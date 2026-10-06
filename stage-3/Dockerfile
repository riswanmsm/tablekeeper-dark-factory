FROM python:3.11-slim

WORKDIR /app

# Pre-install dependencies during build time
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source and test suite
COPY . .

# Execute verification gate during build: container will only build if all concurrency tests pass
RUN pytest tests/test_concurrency.py -v

EXPOSE 8080
ENV PORT=8080

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8080"]
