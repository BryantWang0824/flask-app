# Makefile for Flask APM Demo Application

.PHONY: help install run dev test docker-build docker-run deploy clean

# Default target
help:
	@echo "Flask APM Demo Application"
	@echo ""
	@echo "Available targets:"
	@echo "  install     - Install dependencies"
	@echo "  run         - Run application in production mode"
	@echo "  dev         - Run application in development mode"
	@echo "  test        - Test all endpoints"
	@echo "  docker-build - Build Docker image"
	@echo "  docker-run  - Run Docker container"
	@echo "  deploy      - Deploy to production (requires sudo)"
	@echo "  clean       - Clean up temporary files"

# Install dependencies
install:
	pip3 install -r requirements.txt

# Run in production mode
run:
	gunicorn -w 2 -b 0.0.0.0:8000 --access-logfile - --error-logfile - app:app

# Run in development mode
dev:
	python3 app.py

# Test all endpoints
test:
	@echo "Testing endpoints..."
	@curl -s http://localhost:8000/health | jq . || echo "Health check failed"
	@curl -s http://localhost:8000/api/fast | jq . || echo "Fast endpoint failed"
	@curl -s http://localhost:8000/api/stats | jq . || echo "Stats endpoint failed"

# Build Docker image
docker-build:
	docker build -t flask-apm-demo .

# Run Docker container
docker-run: docker-build
	docker run -p 8000:8000 -e DD_API_KEY=$(DD_API_KEY) flask-apm-demo

# Deploy to production
deploy:
	sudo ./install-dependencies.sh
	sudo ./deploy.sh

# Clean up
clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	docker system prune -f
