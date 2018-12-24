#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for `requests_ratelimit_adapter` package."""

from requests_ratelimit_adapter import RateLimitAdapter
from requests.adapters import HTTPAdapter
import requests
import time


def ensure_gap(timestamps, gap_ms):
    if len(timestamps) < 2:
        return

    for ii in range(len(timestamps) - 1):
        measured_gap_ms = (timestamps[ii + 1] - timestamps[ii]) * 1000

        print("Comparing: {0} - {1} = {2} ms vs {3} ms"
              .format(timestamps[ii], timestamps[ii + 1], measured_gap_ms, gap_ms))

        assert measured_gap_ms >= gap_ms


def test_adapter():
    # Create an HTTP adapter.
    http = HTTPAdapter()

    # Create a rate limiting adapter
    rate_limiter = RateLimitAdapter(adapter=http, calls=1, period=1)

    s = requests.Session()
    s.mount("https://", rate_limiter)
    s.mount("http://", rate_limiter)

    def timestamp_for_url_get(url):
        r = s.get(url)
        r.raise_for_status()
        return time.time()

    # Try and get https://httpbin.org/get more than once per second
    results = [timestamp_for_url_get("https://httpbin.org/get") for _i in range(3)]

    # Ensure the gap between requests is at least 1000 ms
    ensure_gap(results, 1000)
