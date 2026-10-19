"""
Rate limiting and request validation utilities for KisanMitra AI Backend.
"""

import time
import logging
from collections import defaultdict
from threading import Lock
from functools import wraps
from flask import request, jsonify

logger = logging.getLogger(__name__)


class SimpleRateLimiter:
    """
    Thread-safe in-memory sliding window rate limiter per client IP.
    Default: 20 requests per minute.
    """
    def __init__(self, max_requests: int = 20, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests = defaultdict(list)
        self.lock = Lock()

    def get_client_ip(self) -> str:
        # Respect X-Forwarded-For if behind a proxy
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        return request.remote_addr or "127.0.0.1"

    def is_allowed(self, client_ip: str) -> bool:
        now = time.time()
        with self.lock:
            timestamps = [t for t in self.requests[client_ip] if now - t < self.window_seconds]
            if len(timestamps) >= self.max_requests:
                self.requests[client_ip] = timestamps
                return False
            timestamps.append(now)
            self.requests[client_ip] = timestamps
            return True


ai_limiter = SimpleRateLimiter(max_requests=20, window_seconds=60)


def rate_limit_ai(f):
    """Decorator to apply ~20 req/min rate limiting on AI endpoints."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        client_ip = ai_limiter.get_client_ip()
        if not ai_limiter.is_allowed(client_ip):
            logger.warning(f"Rate limit exceeded for client IP: {client_ip}")
            return jsonify({
                "error": "Rate limit exceeded. Maximum 20 requests per minute allowed. Please try again shortly. / अनुरोध दर सीमा समाप्त। अधिकतम 20 अनुरोध प्रति मिनट मान्य हैं।"
            }), 429
        return f(*args, **kwargs)
    return decorated_function


def sanitize_language(lang: any) -> str:
    """Validates language to be 'en' or 'hi' (default: 'hi')."""
    if str(lang).strip().lower() == "en":
        return "en"
    return "hi"
