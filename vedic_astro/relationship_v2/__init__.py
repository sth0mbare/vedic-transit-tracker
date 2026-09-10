"""Independent prospective Jyotish engine; no automatic analysis or scanning."""
from .engine import analyze_v2
from .spec import VERSION

__all__ = ['analyze_v2', 'VERSION']
