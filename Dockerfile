FROM python:3.13-slim-trixie
LABEL authors="techttgames"

RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

RUN curl -sSL https://install.python-poetry.org | python3 -

WORKDIR /code

ENV PATH="/root/.local/bin:$PATH"

COPY poetry.lock pyproject.toml /code/

RUN poetry config virtualenvs.create false && poetry install --no-interaction --no-ansi --no-root

COPY kumo_bot /code/kumo_bot/

CMD ["python", "-m", "kumo_bot"]