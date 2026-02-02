import json
from abc import ABC, abstractmethod
from collections import defaultdict
from cache import line_cache_key

class BaseParser(ABC):
    @abstractmethod
    def parse_level(self, line: str):
        raise NotImplementedError


class PlainTextParser(BaseParser):
    def parse_level(self, line: str):
        parts = line.strip().split()
        level = parts[2]
        if level in {"INFO", "WARNING", "ERROR"}:
            return level


class JSONTextParser(BaseParser): 
    def parse_level(self, line: str):
        obj = json.loads(line)
        level = obj.get("level")
        if level in {"INFO", "WARNING", "ERROR"}:
            return level


class LogAnalyser:
    def __init__(self, parser: BaseParser, cache, cache_ttl=60):
        self.parser = parser
        self.cache = cache
        self.cache_ttl = cache_ttl
        self.counts = defaultdict(int)

    def process_line(self, line: str):
        key = None
        if self.cache is not None:
            key = line_cache_key(line)
            cached = self.cache.get(key)
            if cached is not None:
                return cached

        level = self.parser.parse_level(line)

        if key is not None:
            self.cache.set(key, level, self.cache_ttl)

        return level

    def process_lines(self, lines):
        for line in lines:
            level = self.process_line(line)
            self.counts[level] += 1
        return dict(self.counts)
