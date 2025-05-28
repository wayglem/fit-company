# FIT

The fit monolith is a blazing fast, cutting edge AI fitness coach

## TEAM: Timofey Karpeev, Aleksei Shmakov, Aleksandr Blokhin

## Getting Started

Start the database with docker compose

```bash
docker compose up -d
```

Run the projet

```bash
uv sync
./main.py
# works for me
#uv run main.py
```

## Usage

You can install Bruno to play with the API https://www.usebruno.com/

It's a free developer friendly replacement for Postman. Then open the collection called bruno in this repository.

## Tests

```bash
python -m pytest tests/ -v
# works for me
#uv run -m pytest tests/ -v
```
