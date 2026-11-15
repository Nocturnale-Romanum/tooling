"""Each check module defines NAME, DESCRIPTION and check(text) -> iterable of (pos, message)."""
from . import asterisk, euouae, ob_cb, repetenda

CHECKS = [ob_cb, euouae, repetenda, asterisk]
