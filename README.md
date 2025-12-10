# KumoFeaturedBot

Tech's random bot for Kumo Desu discord server.

## Setup Instructions

1. Install poetry (`curl -sSL https://install.python-poetry.org | python3 -`)
2. Install dependencies (`poetry install`)
3. Setup your files (`config.json`, `secret.json`)
4. Run the program! (`poetry run python -m kumo_bot`)

### Setup (Docker)

1. Prep your `secret.json`! (and at least touch `config.json`.)
2. Run the container!
    ```shell
   docker run -d \
       --name kumo \
       --restart unless-stopped \
       -v "$(pwd)/secret.json:/code/secret.json" \
       -v "$(pwd)/config.json:/code/config.json" \
       techttgames/kumofeaturedbot
    ```