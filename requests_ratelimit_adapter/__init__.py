# -*- coding: utf-8 -*-

"""Top-level package for requests-ratelimit-adapter."""

__author__ = """Max Dymond"""
__email__ = 'cmeister2@gmail.com'
__version__ = '0.2.0'

from .requests_ratelimit_adapter import RateLimitAdapter, HTTPRateLimitAdapter

__all__ = ['RateLimitAdapter', 'HTTPRateLimitAdapter']
