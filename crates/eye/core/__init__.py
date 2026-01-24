"""Core functionality for Eye"""
from .client import EyeClient
from .session import SessionManager
from .metrics import MetricsCollector

__all__ = ['EyeClient', 'SessionManager', 'MetricsCollector']