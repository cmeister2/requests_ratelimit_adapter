# -*- coding: utf-8 -*-

"""Main module for ratelimiting request adapter."""

from requests.adapters import BaseAdapter, HTTPAdapter
import time
import threading
import logging


log = logging.getLogger(__name__)


# Use monotonic time if available in `time`, otherwise fall back to the default clock.
now = time.monotonic if hasattr(time, 'monotonic') else time.time


class RateLimitException(Exception):
    """Exception raised when too many requests have been made in this period."""

    def __init__(self, time_remaining_s):
        """Construct a RateLimitException.

        Args:
            time_remaining_s (int): The time remaining before the current period ends and new requests can be made.
        """
        self.time_remaining_s = time_remaining_s


class RateLimitAdapter(BaseAdapter):
    """Adapter which rate limits requests."""

    def __init__(self,
                 adapter,
                 calls=15,
                 period=900.0):
        """Construct a RateLimitAdapter.

        Args:
            adapter (BaseAdapter): A request adapter on which all requests will be sent.
            calls (int): The maximum number of requests allowed in `period` seconds.
            period (float): The time period during which requests are totalled. Once one time period expires and another
                begins, the number of admitted requests is reset.
        """
        super(RateLimitAdapter, self).__init__()

        class _ContextAdapter(logging.LoggerAdapter):
            def process(self, msg, kwargs):
                return "[{0}] {1}".format(self.extra["class_name"], msg), kwargs

        self.log = _ContextAdapter(log, {"class_name": self.__class__.__name__})

        self.adapter = adapter
        self.calls = calls
        self.period = period

        # Get a lock to wrap the sending logic.
        self.send_lock = threading.RLock()

        self.period_start = 0
        self.period_end = 0
        self.num_calls = 0

    def send(self, request, stream=False, timeout=None, verify=True, cert=None, proxies=None):
        """Send PreparedRequest object. Returns Response object.

        Args:
            request (PreparedRequest): The `PreparedRequest` being sent.
            stream (bool): (optional) Whether to stream the request content.
            timeout: (optional) How long to wait for the server to send
                data before giving up, as a float, or a `(connect timeout,
                read timeout)` tuple.
            verify: (optional) Either a boolean, in which case it controls whether we verify
                the server's TLS certificate, or a string, in which case it must be a path
                to a CA bundle to use.
            cert: (optional) Any user-provided SSL certificate to be trusted.
            proxies: (optional) The proxies dictionary to apply to the request.

        Returns:
            Response object.

        """
        while True:
            try:
                return self._inner_send(request,
                                        stream=stream,
                                        timeout=timeout,
                                        verify=verify,
                                        cert=cert,
                                        proxies=proxies)
            except RateLimitException as e:
                self.log.debug("Retrying send in %f seconds", e.time_remaining_s)
                time.sleep(e.time_remaining_s)

    def _inner_send(self, request, stream=False, timeout=None, verify=True, cert=None, proxies=None):
        with self.send_lock:
            prestart_time = now()

            # Is this the first event in this period?
            if prestart_time > self.period_end:
                first_event = True
                self.num_calls = 0
            else:
                first_event = False

            # Verify if this request is allowed.
            if self.num_calls < self.calls:
                self.log.debug("Allowing send: %d period calls < %d allowed", self.num_calls, self.calls)
                self.num_calls += 1
                resp = self.adapter.send(request,
                                         stream=stream,
                                         timeout=timeout,
                                         verify=verify,
                                         cert=cert,
                                         proxies=proxies)

                if first_event:
                    # Now that we have a response, start the period.
                    self.period_start = now()
                    self.period_end = self.period_start + self.period
                    self.log.debug("Period starts at %f, ends %f  (prestart %f)",
                                   self.period_start,
                                   self.period_end,
                                   prestart_time)

                # And return the response.
                return resp
            else:
                # Raise an exception to trigger a retry later.
                time_remaining_s = self.period_end - prestart_time
                self.log.debug("Disallowing send: %d period calls >= %d allowed; wait %f seconds",
                               self.num_calls,
                               self.calls,
                               time_remaining_s)
                raise RateLimitException(time_remaining_s)

    def close(self):
        """Clean up adapter specific items."""
        self.adapter.close()


class HTTPRateLimitAdapter(RateLimitAdapter):
    """Adapter which rate limits HTTP requests."""

    def __init__(self,
                 calls=15,
                 period=900.0):
        """Construct an HTTPRateLimitAdapter.

        Args:
            calls (int): The maximum number of requests allowed in `period` seconds.
            period (float): The time period during which requests are totalled. Once one time period expires and another
                begins, the number of admitted requests is reset.
        """
        adapter = HTTPAdapter()
        super(HTTPRateLimitAdapter, self).__init__(adapter, calls, period)
