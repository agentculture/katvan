"""katvan — maintain sibling-repo docs under one roof on the culture.dev site."""

from importlib.metadata import PackageNotFoundError
from importlib.metadata import version as _v

try:
    __version__ = _v("katvan")
except PackageNotFoundError:  # editable install without metadata
    __version__ = "0.0.0+local"

__all__ = ["__version__"]
