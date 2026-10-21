FROM ghcr.io/astral-sh/uv:alpine
LABEL authors="techttgames"

WORKDIR /app

RUN adduser -S -u 1001 appuser && chown appuser .

COPY --chown=appuser pyproject.toml uv.lock ./

RUN uv sync --frozen --no-dev --no-install-project --python 3.14

COPY --chown=appuser kumo_bot /app/kumo_bot/

USER appuser

CMD ["uv", "run", "python", "-m", "kumo_bot"]