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
import time
from collections import deque
from collections.abc import Callable
from typing import Any, Literal

from pydantic import Field

from resolveflow.domain.base import FrozenModel
from resolveflow.domain.hashing import checksum

Endpoint = Literal["chat", "embed", "rerank"]

# Cohere trial key ceilings, as stated in the task brief.
DEFAULT_RATE_LIMITS: dict[Endpoint, int] = {"chat": 20, "embed": 5, "rerank": 10}
DEFAULT_MAX_CALLS = 400
RATE_WINDOW_SECONDS = 60.0
# Leave headroom so a clock skew between us and the provider does not trip a 429.
RATE_SAFETY_SECONDS = 1.5


class BudgetExceeded(RuntimeError):
    """Raised when a call would push the run past its hard call cap."""


class ProviderCallRecord(FrozenModel):
    sequence: int = Field(ge=1)
    endpoint: Endpoint
    model: str
    scenario_id: str | None
    build_id: str | None
    attempt: int = Field(ge=1)
    retry_of_sequence: int | None = None
    status: Literal["ok", "rate_limited", "error"]
    request_hash: str
    response_hash: str | None
    input_tokens: int = Field(default=0, ge=0)
    output_tokens: int = Field(default=0, ge=0)
    duration_ms: float = Field(ge=0.0)
    throttle_sleep_ms: float = Field(default=0.0, ge=0.0)
    error_code: str | None = None


class BudgetLedger(FrozenModel):
    schema_version: Literal["1.0"] = "1.0"
    max_calls: int
    total_calls: int
    calls_by_endpoint: dict[str, int]
    retry_calls: int
    input_tokens: int
    output_tokens: int
    provider_call_ms: float
    throttle_sleep_ms: float
    records: tuple[ProviderCallRecord, ...]

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
        clock: Callable[[], float] = time.monotonic,
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
            f"provider_ms={ledger.provider_call_ms:.0f}"
        )

    # -- throttling ----------------------------------------------------------

    def _throttle(self, endpoint: Endpoint) -> float:
        limit = self._rate_limits.get(endpoint)
        if not limit:
            return 0.0
        window = self._windows[endpoint]
        slept = 0.0
        while True:
            now = self._clock()
            while window and now - window[0] >= RATE_WINDOW_SECONDS:
                window.popleft()
            if len(window) < limit:
                window.append(now)
                return slept
            wait = RATE_WINDOW_SECONDS - (now - window[0]) + RATE_SAFETY_SECONDS
            self._sleep(wait)
            slept += wait

    def _reserve(self) -> None:
        if self.total_calls >= self._max_calls:
            raise BudgetExceeded(
                f"provider call budget exhausted: {self.total_calls}/{self._max_calls}"
            )

    # -- dispatch ------------------------------------------------------------

    def _invoke(self, endpoint: Endpoint, kwargs: dict[str, Any]) -> Any:
        model = str(kwargs.get("model", "unknown"))
        request_hash = checksum(json.loads(json.dumps(kwargs, default=str, sort_keys=True)))
        method = getattr(self._client, endpoint)
        first_sequence: int | None = None
        last_error: BaseException | None = None

        for attempt in range(1, self._max_attempts + 1):
            self._reserve()
            slept = self._throttle(endpoint)
            self._throttle_sleep_ms += slept * 1000.0
            started = self._clock()
            try:
                response = method(**kwargs)
            except Exception as exc:  # noqa: BLE001 - normalized into a record below
                duration_ms = (self._clock() - started) * 1000.0
                rate_limited = _is_rate_limited(exc)
                record = self._record(
                    endpoint=endpoint,
                    model=model,
                    attempt=attempt,
                    retry_of=first_sequence,
                    status="rate_limited" if rate_limited else "error",
                    request_hash=request_hash,
                    response_hash=None,
                    input_tokens=0,
                    output_tokens=0,
                    duration_ms=duration_ms,
                    throttle_sleep_ms=slept * 1000.0,
                    error_code=type(exc).__name__,
                )
                first_sequence = first_sequence or record.sequence
                last_error = exc
                if not rate_limited or attempt == self._max_attempts:
                    raise
                # Retries are real calls against the trial key and are counted as such.
                self._sleep(self._backoff_base * (2 ** (attempt - 1)))
                continue

            duration_ms = (self._clock() - started) * 1000.0
            usage_in, usage_out = _extract_usage(response)
            self._record(
                endpoint=endpoint,
                model=model,
                attempt=attempt,
                retry_of=first_sequence,
                status="ok",
                request_hash=request_hash,
                response_hash=checksum(_response_fingerprint(response)),
                input_tokens=usage_in,
                output_tokens=usage_out,
                duration_ms=duration_ms,
                throttle_sleep_ms=slept * 1000.0,
                error_code=None,
            )
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
        vectors = getattr(response.embeddings, "float", None) or []
        return {"embedding_count": len(vectors), "dimension": len(vectors[0]) if vectors else 0}
    return {"repr": type(response).__name__}


def _extract_usage(response: Any) -> tuple[int, int]:
    usage = getattr(response, "usage", None)
    if usage is None:
        return 0, 0
    data: Any = usage
    if hasattr(usage, "model_dump"):
        data = usage.model_dump(mode="json")
    if not isinstance(data, dict):
        return 0, 0
    tokens = data.get("tokens")
    if isinstance(tokens, dict):
        return (
            int(tokens.get("input_tokens") or 0),
            int(tokens.get("output_tokens") or 0),
        )
    billed = data.get("billed_units")
    if isinstance(billed, dict):
        return (
            int(billed.get("input_tokens") or 0),
            int(billed.get("output_tokens") or 0),
        )
    return 0, 0
