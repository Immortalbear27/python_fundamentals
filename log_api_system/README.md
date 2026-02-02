# FastAPI Log Analysis Service  
Redis · Concurrency · Docker

This project is a small backend service written in Python that analyses log data.  
It is designed as a **learning and demonstration project**, showing how modern backend systems are structured, scaled, and deployed.

The service:
- Accepts log data via a REST API
- Extracts useful information from logs
- Uses Redis for caching and rate limiting
- Demonstrates multiple concurrency models (async, threads, processes)
- Runs locally or inside Docker

No prior knowledge of FastAPI, Redis, or concurrency is required to understand this document.

---

## What problem does this project solve?

Most software systems generate **logs** — text records that describe what the system is doing.  
Examples include:
- ```2026-01-30 12:01:05 INFO User logged in```
- ```2026-01-30 12:01:06 ERROR Database timeout```


A common backend task is to:
- Read log data
- Extract key information (e.g. log level)
- Aggregate results efficiently
- Handle many requests without overloading the system

This project demonstrates **how such a system can be built**, using realistic backend techniques.

---

## High-level overview

The application is a **web API** built with FastAPI. Clients send log data, and the API returns structured results.

Internally, the project is organised into clear layers:

- **API layer** – handles HTTP requests and responses
- **Core logic layer** – parses and analyses log data
- **Infrastructure layer** – caching and rate limiting via Redis

Each layer has a single responsibility, making the system easier to understand and extend.

---

## Supported log formats

### Plain text logs
Expected format:
- ```YYYY-MM-DD HH:MM:SS LEVEL message```

### JSON Logs (JSON lines)
One JSON object per line.  
Example:
- ```{"ts":"2026-01-30T12:01:05","level":"INFO","msg":"User logged in"}```

The client specifies which format it is sending when making a request.

## API Endpoints
Once the application is running, interactive documentation is available at:
- ```http://127.0.0.1:8000/docs```

### GET ```/health```
Performs a simple health check, flagging the status of the service.
- Example representation: ```{"status": "ok"}```

### POST ```/parse```
Parses a single log line and returns the detected log level.  
Request example:
```
{
    "mode": "plain",
    "line": "2026-01-30 12:01:05 INFO User logged in"
}
```

Response to example:
```
{
    "level": "INFO"
}
```

### POST ```/batch```
Processes multiple log lines asynchronously.  
This endpoint uses:
- ```asyncio```
- Bounded concurrency
- Background threads to avoid blocking the event loop

Request Example:
```
{
  "mode": "plain",
  "lines": [
    "2026-01-30 12:01:05 INFO User logged in",
    "2026-01-30 12:01:06 ERROR Database timeout",
    "2026-01-30 12:01:07 WARNING Disk almost full"
  ]
}
```

Response to example:
```
{
  "counts": {
    "INFO": 1,
    "ERROR": 1,
    "WARNING": 1
  }
}
```

### POST ```/batch_threads```
Processes multiple log lines using explicit multithreading.  
This endpoint demonstrates:
- ```ThreadPoolExecutor```
- Parallel execution for I/O-bound workloads
The request and response format are identical to /batch.

### POST ```/cpu_processes```
Demonstrates multiprocessing for CPU-bound workloads.  
This endpoint performs intentionally expensive hashing work and uses:
- ```ProcessPoolExecutor```
- Multiple CPU cores

It exists to demonstrate when processes are preferable to threads.

## Concurrency models used in this project:
This project intentionally includes three different concurrency approaches, because each is appropriate in different situations.

### Async ```/batch```
Best suited for:
- I/O-bound work (network calls, Redis access)
- Handling many concurrent requests efficiently

Uses:
- ```async def```
- ```asyncio.Semaphore```
- ```asyncio.to_thread```

### Multithreading ```/batch_threads```
Best suited for:
- I/O-bound work
- Existing synchronous code
- Simpler mental model than async

Uses:
- ```ThreadPoolExecutor```

### Multiprocessing ```/cpu_processes```
Best suited for:
- CPU-bound work
- Heavy computation

Uses:
- ```ProcessPoolExecutor```
- Multiple CPU cores
- Avoids Python's Global Interpreter Lock (GIL)

### Redis Usage
Redis is used for two distinct purposes:

### Caching
When a log line is processed:
- The line is hashed
- The parsed result is stored in Redis
- A time-to-live (TTL) is applied

This avoids re-processing identical log lines  
Redis commands used:
- ```GET```
- ```SETEX```

### Rate Limiting
Each endpoint is protected by a distributed rate limiter.  
Implementation:
- ```INCR``` counts requests
- ```EXPIRE``` defines a time window

This prevents the service from being overloaded.  
If Redis is unavailable:
- The application falls back to a no-op cache
- The service continues running (Graceful Degradation)

## Project Structure:
```
log_api_system
├── app.py          # FastAPI app and endpoints
├── core.py         # Parsing and analysis logic
├── cache.py        # Redis cache and rate limiting
├── Dockerfile      # Container configuration
├── requirements.txt
└── README.md
```
Where:
- ```app.py``` defines the API and concurrency behaviour
- ```core.py``` contains all log parsing and analysis logic
- ```cache.py``` encapsulates Redis access and rate limiting

## Running Locally (Without Docker)
Install dependencies:
- ```pip install -r requirements.txt```

Run the server:
- ```python -m uvicorn app:app --reload```

Open:
- ```http://127.0.0.1:8000/docs```

## Running Redis locally (Optional)
The application works without Redis, but caching and rate limiting are disabled.  
To run Redis with Docker:
- ```docker run -p 6379:6379 redis:7-alpine```

## Running with Docker:
Build the image:
- ```docker build -t log-api .```

Run the container:
- ```docker run --rm -p 8000:8000 log-api```

Then visit:
- ```http://127.0.0.1:8000/docs```

## Purpose of this Project:
This project was built to recap various important Python concepts, such as:
- Modern Python backend patterns
- Practise REST API design
- Understand concurrency trade-offs
- Work with Redis realistically
- Deploy applications using Docker

## Summary:
This repository demonstrates how a backed service can:
- Accpet structured input
- Process data efficiently
- Scale using appropriate concurrency models
- Protect itself using caching and rate limiting
- Be packaged and deployed using Docker
