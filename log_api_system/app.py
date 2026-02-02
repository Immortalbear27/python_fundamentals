import time
import asyncio
import hashlib
from fastapi import FastAPI
from pydantic import BaseModel

from cache import NoopCache, RedisCache
from core import LogAnalyser, PlainTextParser, JSONTextParser

from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor

app = FastAPI()

# Cache wiring (graceful fallback):
try:
    cache = RedisCache()
except Exception:
    cache = NoopCache()

RATE_LIMIT = 100
RATE_WINDOW = 10
RATE_KEY = "ratelimit:log_api:/batch"

MAX_CONCURRENCY = 20 # Tuneable
THREAD_WORKERS = 20

PROC_WORKERS = 4

class ParseRequest(BaseModel):
    mode: str
    line: str

class BatchRequest(BaseModel):
    mode: str
    lines: list[str]

def cpu_heavy(line: str, rounds: int = 20000):
    data = line.encode("utf-8")
    h = b""
    for _ in range(rounds):
        h = hashlib.sha256(data + h).digest()
    return h.hex()

@app.get("/")
def root():
    return {"message": "See /docs for the API UI. Health at /health."}

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/parse")
def parse(req: ParseRequest):
    parser = PlainTextParser() if req.mode == "plain" else JSONTextParser()
    analyser = LogAnalyser(parser = parser, cache = cache, cache_ttl = 60)
    level = analyser.process_line(req.line)
    return {"level": level}

@app.post("/batch")
async def batch(req: BatchRequest):
    # Rate limit the endpoint
    while not cache.allow(RATE_KEY, RATE_LIMIT, RATE_WINDOW):
        await asyncio.sleep(0.05)

    parser = PlainTextParser() if req.mode == 'plain' else JSONTextParser()
    analyser = LogAnalyser(parser = parser, cache = cache, cache_ttl = 60)
   
    sem = asyncio.Semaphore(MAX_CONCURRENCY)

    async def process_one(line):
        async with sem:
            return await asyncio.to_thread(analyser.process_line, line)
        
    levels = await asyncio.gather(*(process_one(line) for line in req.lines))

    counts: dict[str, int] = {}
    for level in levels:
        counts[level] = counts.get(level, 0) + 1

    return {"counts": counts}

@app.post("/batch_threads")
def batch_threads(req: BatchRequest):
    # Rate limit the endpoint:
    while not cache.allow("ratelimit:log_api:/batch_threads", RATE_LIMIT, RATE_WINDOW):
        time.sleep(0.05)

    parser = PlainTextParser() if req.mode == "plain" else JSONTextParser()
    analyser = LogAnalyser(parser = parser, cache = cache, cache_ttl = 60)

    with ThreadPoolExecutor(max_workers = THREAD_WORKERS) as pool:
        levels = list(pool.map(analyser.process_line, req.lines))

    counts: dict[str, int] = {}
    for level in levels:
        counts[level] = counts.get(level, 0) + 1
    
    return {"counts": counts}

@app.post("/cpu_processes")
def cpu_processes(req: BatchRequest):
    while not cache.allow("ratelimit:log_api:/cpu_processes", RATE_LIMIT, RATE_WINDOW):
        time.sleep(0.05)

    with ProcessPoolExecutor(max_workers = PROC_WORKERS) as pool:
        results = list(pool.map(cpu_heavy, req.lines))

    return {"hashes": results[:3], "total": len(results)}