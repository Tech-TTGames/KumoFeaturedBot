FROM python:3.13-alpine AS build-stage

WORKDIR /code

RUN pip install --no-cache-dir poetry poetry-plugin-export

COPY poetry.lock pyproject.toml ./

RUN poetry export -f requirements.txt --output requirements.txt --without-hashes --without dev

FROM python:3.13-alpine
LABEL authors="techttgames"

WORKDIR /app

RUN adduser -S -u 1001 appuser && chown appuser .

COPY --from=build-stage /code/requirements.txt .

RUN pip install --no-cache-dir --no-deps -r requirements.txt

COPY --chown=appuser kumo_bot /app/kumo_bot/

USER appuser

CMD ["python", "-m", "kumo_bot"]