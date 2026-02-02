FROM python:3.11-slim

WORKDIR /app

# Install dependencies first for better layer caching:
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code:
COPY . .

# Expose the API port:
EXPOSE 8000

# Run the server:
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
