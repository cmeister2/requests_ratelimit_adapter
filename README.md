# requests-ratelimit-adapter

[![pypi version](https://img.shields.io/pypi/v/requests_ratelimit_adapter.svg)](https://pypi.python.org/pypi/requests_ratelimit_adapter)
[![Travis Status](https://img.shields.io/travis/cmeister2/requests_ratelimit_adapter.svg)](https://travis-ci.org/cmeister2/requests_ratelimit_adapter)
[![Documentation Status](https://readthedocs.org/projects/requests-ratelimit-adapter/badge/?version=latest)](https://requests-ratelimit-adapter.readthedocs.io/en/latest/?badge=latest)

A ratelimiting Session adapter for requests.

- Free software: MIT license
- Documentation: https://requests-ratelimit-adapter.readthedocs.io.

## Example

    >>> from requests_ratelimit_adapter import HTTPRateLimitAdapter
    >>> import requests
    >>> import time

    >>> # Create a rate limiting adapter
    >>> rate_limiter = HTTPRateLimitAdapter(calls=1, period=1)

    >>> s = requests.Session()
    >>> s.mount("https://", rate_limiter)

    >>> # This first request will start the period.
    >>> r = s.get("https://httpbin.org/get")
    >>> r.raise_for_status()
    >>> time1 = time.time()

    >>> # This second request will wait 1 second before executing.
    >>> r2 = s.get("https://httpbin.org/get")
    >>> r2.raise_for_status()
    >>> time2 = time.time()

    >>> # For this example, verify the timestamps are more than a second apart.
    >>> assert time2 >= time1 + 1


## Credits

This package was created with [Cookiecutter](https://github.com/audreyr/cookiecutter) and the [cmeister2/cookiecutter-pypackage](https://github.com/cmeister2/cookiecutter-pypackage) project template.
