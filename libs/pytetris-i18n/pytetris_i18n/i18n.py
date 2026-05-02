"""Internationalisation support for pytetris packages.

Each package that has translatable strings creates a single :class:`I18n`
instance at import time, pointing at its own ``locales/`` directory:

.. code-block:: python

    # pytetris_save/__init__.py
    import pathlib
    from pytetris_i18n.i18n import I18n

    _i18n = I18n(
        domain="pytetris_save",
        locales_dir=pathlib.Path(__file__).parent.parent / "locales",
    )

Modules within the package then import and use the aliases directly:

.. code-block:: python

    # pytetris_save/save_manager.py
    from pytetris_save import _, _n

    def describe_backups(count: int) -> str:
        return _i18n.ngettext("One backup found.",
                              "{n} backups found.",
                              count).format(n=count)
"""

import gettext
import logging
import pathlib
from gettext import NullTranslations

log = logging.getLogger(__name__)


class I18n:
    """Gettext wrapper for a single pytetris package.

    Loads translations from the package's own ``locales/`` directory.
    Falls back to returning the original string if the locale or ``.mo``
    file is not found, and logs a ``WARNING`` via :mod:`logging` so the
    missing translation is visible without crashing the app.

    :param domain: Gettext domain, typically the package name
        (e.g. ``pytetris_save``).
    :param locales_dir: Absolute path to the package's ``locales/``
        directory.
    :param locale: BCP 47 locale code to load (e.g. ``sv``, ``en``).
        Defaults to ``None``, which lets :mod:`gettext` resolve the
        locale from the environment (``LANGUAGE``, ``LC_ALL``, etc.).
    """

    def __init__(
        self,
        domain: str,
        locales_dir: pathlib.Path,
        locale: str | None = None,
    ) -> None:
        self._domain = domain
        self._locales_dir = locales_dir
        self._translation = self._load(domain, locales_dir, locale)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def gettext(self, message: str) -> str:
        """Return the translation of *message* for the active locale.

        Falls back to *message* itself if no translation is available.

        :param message: The source string to translate.
        :return: Translated string, or *message* if no translation exists.
        """
        return str(self._translation.gettext(message))

    def ngettext(self, singular: str, plural: str, n: int) -> str:
        """Return the singular or plural translation depending on *n*.

        Falls back to *singular* when ``n == 1`` and *plural* otherwise
        if no translation is available.

        :param singular: Singular form of the source string.
        :param plural: Plural form of the source string.
        :param n: The count that determines which form to use.
        :return: Translated string for the appropriate plural form.
        """
        return str(self._translation.ngettext(singular, plural, n))

    def set_locale(self, locale: str) -> None:
        """Switch the active locale at runtime.

        Falls back silently if the new locale is not available.

        :param locale: BCP 47 locale code to switch to (e.g. ``sv``).
        """
        self._translation = self._load(self._domain, self._locales_dir, locale)

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    @staticmethod
    def _load(
        domain: str,
        locales_dir: pathlib.Path,
        locale: str | None,
    ) -> NullTranslations:
        """Load a :class:`gettext.GNUTranslations` for the given locale.

        Returns a :class:`gettext.NullTranslations` (pass-through) if the
        ``.mo`` file cannot be found, so callers always receive a valid
        translation object.

        :param domain: Gettext domain name.
        :param locales_dir: Path to the ``locales/`` directory.
        :param locale: Locale code, or ``None`` to use the environment.
        :return: A translations object, never ``None``.
        """
        languages: list[str] | None = [locale] if locale else None
        try:
            return gettext.translation(
                domain=domain,
                localedir=locales_dir,
                languages=languages,
                #fallback=True,
            )
        except FileNotFoundError:
            log.warning(
                "No translation file found for domain '%s' in %s (locale: %s). "
                "Falling back to original strings.",
                domain,
                locales_dir,
                locale if locale else "environment",
            )
            return gettext.NullTranslations()
