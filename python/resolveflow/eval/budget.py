"""Hard-capped, throttled, fully accounted Cohere client.

Every provider call in an evaluation run goes through this wrapper. It exists so
that three claims can be made without hand-waving:

* the run consumed exactly N provider calls, because a counter incremented once
  per HTTP attempt (retries included);
* the run stayed inside the trial key's per-minute ceilings, because it slept;
* the run aborted rather than silently overspending, because a hard cap raises.

The recorded call log stores hashes and token counts, never request or response
bodies, and never the API key.
"""

from __future__ import annotations

import json
import math
import time
from collections import deque
from collections.abc import Callable
from typing import Any, Literal

from pydantic import Field, model_validator

from resolveflow.domain.base import FrozenModel
from resolveflow.domain.hashing import checksum

Endpoint = Literal["chat", "embed", "rerank"]

# Cohere trial key ceilings, as stated in the task brief.
DEFAULT_RATE_LIMITS: dict[Endpoint, int] = {"chat": 20, "embed": 5, "rerank": 10}
# The SDK retries 429/408/409/5xx internally, by default twice, and those
# retries are real HTTP requests against the monthly key quota that this
# wrapper never sees. That would make the ledger's central claim -- "the run
# consumed exactly N provider calls, because a counter incremented once per
# HTTP attempt" -- false, and would let a rate-limited burst spend 3x the
# counted budget. Retries are handled here instead, where they are counted.
SDK_MAX_RETRIES = 0

DEFAULT_MAX_CALLS = 400
RATE_WINDOW_SECONDS = 60.0
# Leave headroom so a clock skew between us and the provider does not trip a 429.
RATE_SAFETY_SECONDS = 1.5
# A window needs at most a couple of drains; more means the clock is not moving.
MAX_THROTTLE_WAITS = 8


class BudgetExceeded(RuntimeError):
    """Raised when a call would push the run past its hard call cap."""


class ProviderCallRecord(FrozenModel):
    sequence: int = Field(ge=1)
    endpoint: Endpoint
    model: str = Field(min_length=1)
    scenario_id: str | None
    build_id: str | None
    attempt: int = Field(ge=1)
    retry_of_sequence: int | None = None
    status: Literal["ok", "rate_limited", "gateway_error", "error"]
    request_hash: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    response_hash: str | None = Field(default=None, pattern=r"^sha256:[0-9a-f]{64}$")
    input_tokens: int = Field(default=0, ge=0)
    output_tokens: int = Field(default=0, ge=0)
    search_units: int = Field(default=0, ge=0)
    duration_ms: float = Field(ge=0.0)
    throttle_sleep_ms: float = Field(default=0.0, ge=0.0)
    error_code: str | None = None


class BudgetLedger(FrozenModel):
    schema_version: Literal["1.0"] = "1.0"
    max_calls: int = Field(ge=1)
    total_calls: int = Field(ge=0)
    calls_by_endpoint: dict[str, int]
    retry_calls: int = Field(ge=0)
    input_tokens: int = Field(ge=0)
    output_tokens: int = Field(ge=0)
    search_units: int = Field(default=0, ge=0)
    provider_call_ms: float = Field(ge=0.0)
    throttle_sleep_ms: float = Field(ge=0.0)
    records: tuple[ProviderCallRecord, ...]

    @model_validator(mode="after")
    def stays_within_hard_cap(self) -> BudgetLedger:
        if self.total_calls > self.max_calls:
            raise ValueError("provider ledger exceeds its hard call cap")
        return self

    @property
    def total_tokens(self) -> int:
        return self.input_tokens + self.output_tokens


def _is_rate_limited(exc: BaseException) -> bool:
    name = type(exc).__name__.lower()
    if "toomanyrequests" in name or "ratelimit" in name:
        return True
    status = getattr(exc, "status_code", None)
    if status == 429:
        return True
    return "429" in str(exc) or "rate limit" in str(exc).lower()


# Transient server-side failures. Cohere's gateway can return a 502/503/504 or
# time a request out under load; these are not the caller's fault and are the
# textbook case for a bounded, counted retry. A live run that aborts on the first
# one wastes every call it already spent, which is what happened on a Rerank v4
# 504 after 33 successful calls. Retried the same way as a 429 -- with backoff,
# and each attempt counted against the budget so the ledger stays honest.
_GATEWAY_STATUS = frozenset({500, 502, 503, 504})


def _is_transient_gateway(exc: BaseException) -> bool:
    status = getattr(exc, "status_code", None)
    if status in _GATEWAY_STATUS:
        return True
    name = type(exc).__name__.lower()
    if "timeout" in name or "serviceunavailable" in name or "badgateway" in name:
        return True
    text = str(exc).lower()
    return any(code in text for code in ("502", "503", "504")) or "gateway timeout" in text


def _is_retryable(exc: BaseException) -> bool:
    return _is_rate_limited(exc) or _is_transient_gateway(exc)


class BudgetedCohereClient:
    """Counts, throttles, retries, and caps every Cohere call."""

    def __init__(
        self,
        client: Any,
        *,
        max_calls: int = DEFAULT_MAX_CALLS,
        rate_limits: dict[Endpoint, int] | None = None,
        max_attempts: int = 4,
        backoff_base_seconds: float = 5.0,
        sleep: Callable[[float], None] = time.sleep,
        clock: Callable[[], float] = time.perf_counter,
        on_call: Callable[[ProviderCallRecord], None] | None = None,
    ) -> None:
        self._client = client
        self._max_calls = max_calls
        self._rate_limits = dict(rate_limits or DEFAULT_RATE_LIMITS)
        self._max_attempts = max_attempts
        self._backoff_base = backoff_base_seconds
        self._sleep = sleep
        self._clock = clock
        self._on_call = on_call
        self._records: list[ProviderCallRecord] = []
        self._windows: dict[Endpoint, deque[float]] = {
            endpoint: deque() for endpoint in self._rate_limits
        }
        self._throttle_sleep_ms = 0.0
        self.scenario_id: str | None = None
        self.build_id: str | None = None

    # -- accounting ----------------------------------------------------------

    @property
    def total_calls(self) -> int:
        return len(self._records)

    def calls_by_endpoint(self) -> dict[str, int]:
        counts: dict[str, int] = {}
        for record in self._records:
            counts[record.endpoint] = counts.get(record.endpoint, 0) + 1
        return dict(sorted(counts.items()))

    def ledger(self) -> BudgetLedger:
        return BudgetLedger(
            max_calls=self._max_calls,
            total_calls=self.total_calls,
            calls_by_endpoint=self.calls_by_endpoint(),
            retry_calls=sum(1 for item in self._records if item.retry_of_sequence is not None),
            input_tokens=sum(item.input_tokens for item in self._records),
            output_tokens=sum(item.output_tokens for item in self._records),
            search_units=sum(item.search_units for item in self._records),
            provider_call_ms=round(sum(item.duration_ms for item in self._records), 3),
            throttle_sleep_ms=round(self._throttle_sleep_ms, 3),
            records=tuple(self._records),
        )

    def summary_line(self) -> str:
        ledger = self.ledger()
        parts = ", ".join(f"{key}={value}" for key, value in ledger.calls_by_endpoint.items())
        return (
            f"[budget] total={ledger.total_calls}/{self._max_calls} ({parts}) "
            f"retries={ledger.retry_calls} "
            f"tokens_in={ledger.input_tokens} tokens_out={ledger.output_tokens} "
            f"search_units={ledger.search_units} "
            f"provider_ms={ledger.provider_call_ms:.0f}"
        )

    # -- throttling ----------------------------------------------------------

    def _throttle(self, endpoint: Endpoint, *, deadline: float | None = None) -> float:
        limit = self._rate_limits.get(endpoint)
        if not limit:
            self._require_time_remaining(deadline)
            return 0.0
        window = self._windows[endpoint]
        slept = 0.0
        # Bounded: if the injected sleep does not advance the injected clock (as in
        # a test harness), an unbounded loop would spin forever instead of failing.
        for _ in range(MAX_THROTTLE_WAITS):
            self._require_time_remaining(deadline)
            now = self._clock()
            while window and now - window[0] >= RATE_WINDOW_SECONDS:
                window.popleft()
            if len(window) < limit:
                window.append(now)
                return slept
            wait = RATE_WINDOW_SECONDS - (now - window[0]) + RATE_SAFETY_SECONDS
            remaining = self._remaining(deadline)
            if remaining is not None and wait + 1.0 >= remaining:
                raise TimeoutError("provider deadline exhausted before rate-limit wait")
            self._sleep(wait)
            slept += wait
        raise RuntimeError(
            f"rate-limit window for {endpoint} did not drain after "
            f"{MAX_THROTTLE_WAITS} waits; the clock is not advancing"
        )

    def _reserve(self) -> None:
        if self.total_calls >= self._max_calls:
            raise BudgetExceeded(
                f"provider call budget exhausted: {self.total_calls}/{self._max_calls}"
            )

    def _remaining(self, deadline: float | None) -> float | None:
        return None if deadline is None else deadline - self._clock()

    def _require_time_remaining(self, deadline: float | None) -> None:
        remaining = self._remaining(deadline)
        if remaining is not None and remaining < 1.0:
            # Cohere SDK 7 accepts whole-second request timeouts. Do not start an
            # attempt whose minimum representable timeout exceeds the run budget.
            raise TimeoutError("provider deadline exhausted before request")

    def _attempt_kwargs(self, kwargs: dict[str, Any], *, deadline: float | None) -> dict[str, Any]:
        if deadline is None:
            return kwargs
        remaining = self._remaining(deadline)
        if remaining is None or remaining < 1.0:
            raise TimeoutError("provider deadline exhausted before request")
        attempt = dict(kwargs)
        request_options = dict(attempt.get("request_options") or {})
        request_options["timeout_in_seconds"] = int(remaining)
        request_options["max_retries"] = 0
        attempt["request_options"] = request_options
        return attempt

    # -- dispatch ------------------------------------------------------------

    def _invoke(self, endpoint: Endpoint, kwargs: dict[str, Any]) -> Any:
        model = str(kwargs.get("model", "unknown"))
        request_hash = checksum(json.loads(json.dumps(kwargs, default=str, sort_keys=True)))
        method = getattr(self._client, endpoint)
        first_sequence: int | None = None
        last_error: BaseException | None = None
        raw_request_options = kwargs.get("request_options")
        timeout_seconds = (
            raw_request_options.get("timeout_in_seconds")
            if isinstance(raw_request_options, dict)
            else None
        )
        deadline = (
            self._clock() + float(timeout_seconds)
            if isinstance(timeout_seconds, int | float) and timeout_seconds > 0
            else None
        )

        for attempt in range(1, self._max_attempts + 1):
            self._reserve()
            slept = self._throttle(endpoint, deadline=deadline)
            self._throttle_sleep_ms += slept * 1000.0
            attempt_kwargs = self._attempt_kwargs(kwargs, deadline=deadline)
            started = self._clock()
            try:
                response = method(**attempt_kwargs)
                usage_in, usage_out, search_units = _extract_usage(response, endpoint=endpoint)
                response_hash = checksum(_response_fingerprint(response))
            except Exception as exc:  # noqa: BLE001 - normalized into a record below
                duration_ms = (self._clock() - started) * 1000.0
                rate_limited = _is_rate_limited(exc)
                retryable = _is_retryable(exc)
                if rate_limited:
                    status = "rate_limited"
                elif retryable:
                    status = "gateway_error"
                else:
                    status = "error"
                record = self._record(
                    endpoint=endpoint,
                    model=model,
                    attempt=attempt,
                    retry_of=first_sequence,
                    status=status,
                    request_hash=request_hash,
                    response_hash=None,
                    input_tokens=0,
                    output_tokens=0,
                    search_units=0,
                    duration_ms=duration_ms,
                    throttle_sleep_ms=slept * 1000.0,
                    error_code=type(exc).__name__,
                )
                first_sequence = first_sequence or record.sequence
                last_error = exc
                if not retryable or attempt == self._max_attempts:
                    raise
                # Retries are real calls against the trial key and are counted as such.
                backoff = self._backoff_base * (2 ** (attempt - 1))
                remaining = self._remaining(deadline)
                if remaining is not None and backoff + 1.0 >= remaining:
                    raise TimeoutError("provider deadline exhausted before retry") from exc
                self._sleep(backoff)
                continue

            duration_ms = (self._clock() - started) * 1000.0
            self._record(
                endpoint=endpoint,
                model=model,
                attempt=attempt,
                retry_of=first_sequence,
                status="ok",
                request_hash=request_hash,
                response_hash=response_hash,
                input_tokens=usage_in,
                output_tokens=usage_out,
                search_units=search_units,
                duration_ms=duration_ms,
                throttle_sleep_ms=slept * 1000.0,
                error_code=None,
            )
            remaining = self._remaining(deadline)
            if remaining is not None and remaining <= 0:
                raise TimeoutError("provider deadline exhausted after request")
            return response

        raise last_error if last_error else RuntimeError("unreachable retry exit")

    def _record(self, **fields: Any) -> ProviderCallRecord:
        record = ProviderCallRecord(
            sequence=len(self._records) + 1,
            scenario_id=self.scenario_id,
            build_id=self.build_id,
            retry_of_sequence=fields.pop("retry_of"),
            **fields,
        )
        self._records.append(record)
        if self._on_call is not None:
            self._on_call(record)
        return record

    # -- Cohere client surface used by the adapters --------------------------

    def chat(self, **kwargs: Any) -> Any:
        return self._invoke("chat", kwargs)

    def embed(self, **kwargs: Any) -> Any:
        return self._invoke("embed", kwargs)

    def rerank(self, **kwargs: Any) -> Any:
        return self._invoke("rerank", kwargs)


def _response_fingerprint(response: Any) -> Any:
    """A content fingerprint that never carries hidden reasoning or credentials."""
    for attribute in ("id", "response_id"):
        value = getattr(response, attribute, None)
        if value:
            return {"id": str(value)}
    if hasattr(response, "results"):
        return {
            "results": [
                {
                    "index": int(getattr(item, "index", -1)),
                    "score": round(float(getattr(item, "relevance_score", 0.0)), 12),
                }
                for item in response.results
            ]
        }
    if hasattr(response, "embeddings"):
        # Cohere SDK 7 exposes the wire field ``float`` as ``float_`` on its
        # Python model because ``float`` is a builtin. Keep the wire-name
        # fallback for lightweight fixtures and older/future SDK shapes.
        vectors = getattr(response.embeddings, "float_", None)
        if vectors is None:
            vectors = getattr(response.embeddings, "float", None)
        if vectors is None and isinstance(response.embeddings, dict):
            vectors = response.embeddings.get("float")
            if vectors is None:
                vectors = response.embeddings.get("float_")
        vectors = vectors or []
        return {"embedding_count": len(vectors), "dimension": len(vectors[0]) if vectors else 0}
    return {"repr": type(response).__name__}


def _extract_usage(response: Any, *, endpoint: Endpoint) -> tuple[int, int, int]:
    usage = getattr(response, "usage", None)
    usage_data: Any = None
    if usage is None:
        if endpoint == "chat":
            raise ValueError("provider response omitted required token usage")
    else:
        usage_data = usage
        if hasattr(usage, "model_dump"):
            usage_data = usage.model_dump(mode="json")
    if usage_data is not None and not isinstance(usage_data, dict):
        if endpoint == "chat":
            raise ValueError("provider response carried malformed token usage")
        usage_data = None

    def counts(block: Any) -> tuple[int, int] | None:
        if not isinstance(block, dict):
            return None
        input_value = block.get("input_tokens")
        output_value = block.get("output_tokens")
        if (
            isinstance(input_value, bool)
            or not isinstance(input_value, int | float)
            or isinstance(output_value, bool)
            or not isinstance(output_value, int | float)
            or not math.isfinite(float(input_value))
            or not math.isfinite(float(output_value))
            or input_value < 0
            or output_value < 0
            or not float(input_value).is_integer()
            or not float(output_value).is_integer()
        ):
            return None
        return int(input_value), int(output_value)

    if endpoint == "chat" and isinstance(usage_data, dict):
        tokens = usage_data.get("tokens")
        parsed = counts(tokens)
        if parsed is not None:
            return (*parsed, 0)
        billed = usage_data.get("billed_units")
        parsed = counts(billed)
        if parsed is not None:
            return (*parsed, 0)
    if endpoint == "chat":
        raise ValueError("provider response omitted complete token usage")

    meta: Any = getattr(response, "meta", None)
    if meta is not None and hasattr(meta, "model_dump"):
        meta = meta.model_dump(mode="json")
    billed = meta.get("billed_units") if isinstance(meta, dict) else None
    if not isinstance(billed, dict):
        raise ValueError(f"provider {endpoint} response omitted required billed usage")

    def exact_nonnegative(name: str) -> int:
        if name not in billed:
            raise ValueError(f"provider {endpoint} response omitted required {name}")
        value = billed[name]
        if (
            isinstance(value, bool)
            or not isinstance(value, int | float)
            or not math.isfinite(float(value))
            or value < 0
            or not float(value).is_integer()
        ):
            raise ValueError(f"provider response carried invalid {name}")
        return int(value)

    if endpoint == "embed":
        return exact_nonnegative("input_tokens"), 0, 0
    return 0, 0, exact_nonnegative("search_units")
