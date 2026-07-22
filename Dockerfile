FROM python:3.13-slim@sha256:6771159cd4fa5d9bba1258caf0b82e6b73458c694d178ad97c5e925c2d0e1a91
WORKDIR /app
COPY --from=ghcr.io/astral-sh/uv:0.11.31@sha256:ecd4de2f060c64bea0ff8ecb182ddf46ba3fcccdc8a60cfdbaf20d1a047d7437 /uv /uvx /bin/
COPY pyproject.toml uv.lock README.md ./
COPY python ./python
COPY data ./data
RUN uv sync --frozen --no-dev
ENV PATH="/app/.venv/bin:$PATH" PYTHONPATH=/app/python
CMD ["uvicorn", "resolveflow.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
