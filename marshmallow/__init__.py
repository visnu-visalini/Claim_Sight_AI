"""Minimal marshmallow stub to satisfy imports in ClaimSightAI backend.
Only interfaces used in the project are implemented; full validation is omitted.
"""

from .fields import *
from .validate import *

class ValidationError(Exception):
    """Simple validation error stub returning a messages dict."""
    def __init__(self, messages=None):
        super().__init__("Validation error")
        self.messages = messages or {}

class Schema:
    """Base schema with a naive load implementation that returns the input data.
    Real validation is not performed in this stub.
    """
    def load(self, data):
        return data