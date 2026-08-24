.PHONY: up down install

up:
	docker-compose up -d

down:
	docker-compose down

install:
	uv sync
