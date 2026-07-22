FROM python:3.13-slim
WORKDIR /app
COPY --from=ghcr.io/astral-sh/uv:0.11.31 /uv /uvx /bin/
COPY pyproject.toml uv.lock README.md ./
COPY python ./python
RUN uv sync --frozen --no-dev
ENV PATH="/app/.venv/bin:$PATH" PYTHONPATH=/app/python
CMD ["uvicorn", "resolveflow.api.main:app", "--host", "0.0.0.0", "--port", "8000"]

