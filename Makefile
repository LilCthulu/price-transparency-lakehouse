.PHONY: up down ingest stage normalize build export test lint

up:
	docker compose -f airflow/docker-compose.yaml up -d

down:
	docker compose -f airflow/docker-compose.yaml down

ingest:
	python -m pipeline.ingest --source-id $(SOURCE_ID)

stage:
	python -m pipeline.stage --source-id $(SOURCE_ID)

normalize:
	python -m pipeline.load_silver --source-id $(SOURCE_ID)

build:
	cd dbt && dbt build

export:
	python -m pipeline.export

test:
	pytest

lint:
	ruff check .
