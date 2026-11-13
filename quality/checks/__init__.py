"""Each check module defines NAME, DESCRIPTION and check(text) -> iterable of (pos, message)."""
from . import ob_cb

CHECKS = [ob_cb]
