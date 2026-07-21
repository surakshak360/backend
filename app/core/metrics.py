from typing import Dict
from prometheus_client import Counter, Histogram, Gauge, CollectorRegistry

registry = CollectorRegistry()

http_requests_total = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "path", "status"],
    registry=registry,
)

http_request_duration_seconds = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "path"],
    registry=registry,
)

ml_inference_duration_seconds = Histogram(
    "ml_inference_duration_seconds",
    "ML service inference duration in seconds",
    ["service", "endpoint"],
    registry=registry,
)

ml_inference_errors_total = Counter(
    "ml_inference_errors_total",
    "Total ML service inference errors",
    ["service", "error_type"],
    registry=registry,
)

active_cases_gauge = Gauge(
    "active_cases",
    "Number of active cases by status and type",
    ["status", "type"],
    registry=registry,
)

websocket_connections_gauge = Gauge(
    "websocket_connections",
    "Number of active websocket connections",
    registry=registry,
)


def track_case_counts(counts: Dict[str, Dict[str, int]]):
    """Update case gauge. counts: {status: {type: count}}"""
    active_cases_gauge.clear()
    for status, type_counts in counts.items():
        for case_type, count in type_counts.items():
            active_cases_gauge.labels(status=status, type=case_type).set(count)


def update_websocket_count(count: int):
    websocket_connections_gauge.set(count)
