from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
import time

# Metrics definitions
REQUESTS_TOTAL = Counter(
    "gravity_requests_total", 
    "Total requests to bridge", 
    ["method", "endpoint", "provider", "model"]
)

TOKENS_TOTAL = Counter(
    "gravity_tokens_total", 
    "Total tokens processed", 
    ["type", "provider", "model"]
)

REQUEST_LATENCY = Histogram(
    "gravity_request_duration_seconds", 
    "Latency of requests in seconds", 
    ["provider", "model"],
    buckets=(0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0, float("inf"))
)

ERRORS_TOTAL = Counter(
    "gravity_errors_total", 
    "Total errors encountered", 
    ["type", "provider"]
)

def record_request(provider: str, model: str, method: str = "POST", endpoint: str = "/v1/chat/completions"):
    REQUESTS_TOTAL.labels(method=method, endpoint=endpoint, provider=provider, model=model).inc()

def record_tokens(type: str, provider: str, model: str, count: int):
    """type: 'input' or 'output'"""
    TOKENS_TOTAL.labels(type=type, provider=provider, model=model).inc(count)

def record_latency(provider: str, model: str, seconds: float):
    REQUEST_LATENCY.labels(provider=provider, model=model).observe(seconds)

def record_error(type: str, provider: str = "bridge"):
    ERRORS_TOTAL.labels(type=type, provider=provider).inc()

def get_metrics_data():
    """Returns data in Prometheus format."""
    return generate_latest(), CONTENT_TYPE_LATEST
