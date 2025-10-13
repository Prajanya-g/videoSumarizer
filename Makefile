# Video Summarizer Makefile

.PHONY: help install dev test clean build deploy

# Default target
help:
	@echo "Video Summarizer - Available Commands:"
	@echo "  install    - Install dependencies"
	@echo "  dev        - Start development server"
	@echo "  test       - Run tests"
	@echo "  seed       - Seed database with sample data"
	@echo "  evaluate   - Run AI feature evaluation"
	@echo "  clean      - Clean up temporary files"
	@echo "  build      - Build Docker image"
	@echo "  deploy     - Deploy with Docker Compose"
	@echo "  logs       - View application logs"
	@echo "  shell      - Open shell in container"

# Install dependencies
install:
	pip install -r requirements.txt
	cd frontend && npm install

# Start development server
dev:
	./venv/bin/python -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000

# Run tests
test:
	pytest -v

# Seed database with sample data
seed:
	python seed_data.py

# Run AI feature evaluation
evaluate:
	python evaluate_ai.py

# Clean up temporary files
clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf build/
	rm -rf dist/
	rm -rf .pytest_cache/
	rm -rf .coverage
	rm -rf htmlcov/

# Build Docker image
build:
	docker build -t video-summarizer .

# Deploy with Docker Compose
deploy:
	docker-compose up -d

# View logs
logs:
	docker-compose logs -f

# Open shell in container
shell:
	docker-compose exec app bash

# Stop services
stop:
	docker-compose down

# Restart services
restart:
	docker-compose restart

# Database operations
db-init:
	./venv/bin/python init_database.py

db-reset:
	docker-compose down -v
	docker-compose up -d db
	sleep 10
	./venv/bin/python init_database.py

# Production deployment
prod-deploy:
	docker-compose -f docker-compose.prod.yml up -d

# Code quality
lint:
	flake8 backend/
	black --check backend/

format:
	black backend/

# Security check
security:
	pip-audit

# Update dependencies
update:
	pip list --outdated
	pip install --upgrade pip
	pip install --upgrade -r requirements.txt