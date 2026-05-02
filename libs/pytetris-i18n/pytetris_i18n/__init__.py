"""
pytetris-i18n: Internationalization library for Road Craft.

This library provides functionality for managing translations and localization.
"""

#: Version of the pytetris-i18n package
__version__ = "0.1.0"

# Import main classes for convenient access
from .i18n import I18n

# Explicitly list all public exports
__all__ = [
    # Version
    "__version__",
    # i18n classes
    "I18n",
]
