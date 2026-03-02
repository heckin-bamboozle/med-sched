FROM python:3.11-slim

WORKDIR /code

# Install system dependencies for psycopg2
RUN apt-get update && apt-get install -y gcc libpq-dev && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY ./app ./app

# Create directory for static files if needed
RUN mkdir -p /code/app/static

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
