"""Tests for :class:`pytetris_i18n.i18n.I18n`."""

import gettext
import pathlib
from unittest.mock import MagicMock, patch

import pytest

from pytetris_i18n.i18n import I18n

DOMAIN = "pytetris_test"
LOCALES_DIR = pathlib.Path("/fake/locales")


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def null_i18n() -> I18n:
    """An I18n instance that always falls back (no .mo file present)."""
    return I18n(domain=DOMAIN, locales_dir=LOCALES_DIR)


@pytest.fixture()
def loaded_i18n() -> I18n:
    """An I18n instance backed by a mock GNUTranslations object."""
    mock_translation = MagicMock(spec=gettext.GNUTranslations)
    mock_translation.gettext.side_effect = lambda m: f"[translated] {m}"
    mock_translation.ngettext.side_effect = lambda s, p, n: (
        f"[translated] {s}" if n == 1 else f"[translated] {p}"
    )

    with patch("gettext.translation", return_value=mock_translation):
        instance = I18n(domain=DOMAIN, locales_dir=LOCALES_DIR, locale="sv")

    return instance


# ---------------------------------------------------------------------------
# Fallback behaviour (missing .mo file)
# ---------------------------------------------------------------------------


class TestFallback:
    def test_gettext_returns_original_string(self, null_i18n: I18n) -> None:
        assert null_i18n.gettext("Hello") == "Hello"

    def test_missing_mo_logs_warning(self, caplog: pytest.LogCaptureFixture) -> None:
        import logging

        with caplog.at_level(logging.WARNING, logger="pytetris_i18n.i18n"):
            I18n(domain=DOMAIN, locales_dir=LOCALES_DIR)
        assert "No translation file found" in caplog.text

    def test_ngettext_returns_singular_when_n_is_one(self, null_i18n: I18n) -> None:
        assert null_i18n.ngettext("One item", "{n} items", 1) == "One item"

    def test_ngettext_returns_plural_when_n_is_not_one(self, null_i18n: I18n) -> None:
        assert null_i18n.ngettext("One item", "{n} items", 3) == "{n} items"

    def test_ngettext_returns_plural_when_n_is_zero(self, null_i18n: I18n) -> None:
        assert null_i18n.ngettext("One item", "{n} items", 0) == "{n} items"


# ---------------------------------------------------------------------------
# Loaded translations
# ---------------------------------------------------------------------------


class TestLoaded:
    def test_gettext_returns_translation(self, loaded_i18n: I18n) -> None:
        assert loaded_i18n.gettext("Hello") == "[translated] Hello"

    def test_ngettext_returns_singular_translation(self, loaded_i18n: I18n) -> None:
        result = loaded_i18n.ngettext("One item", "{n} items", 1)
        assert result == "[translated] One item"

    def test_ngettext_returns_plural_translation(self, loaded_i18n: I18n) -> None:
        result = loaded_i18n.ngettext("One item", "{n} items", 5)
        assert result == "[translated] {n} items"


# ---------------------------------------------------------------------------
# set_locale
# ---------------------------------------------------------------------------


class TestSetLocale:
    def test_set_locale_switches_translation(self) -> None:
        mock_sv = MagicMock(spec=gettext.GNUTranslations)
        mock_sv.gettext.return_value = "Hej"

        mock_en = MagicMock(spec=gettext.GNUTranslations)
        mock_en.gettext.return_value = "Hello"

        with patch("gettext.translation", return_value=mock_sv):
            instance = I18n(domain=DOMAIN, locales_dir=LOCALES_DIR, locale="sv")

        assert instance.gettext("greeting") == "Hej"

        with patch("gettext.translation", return_value=mock_en):
            instance.set_locale("en")

        assert instance.gettext("greeting") == "Hello"

    def test_set_locale_falls_back_silently_when_locale_missing(self) -> None:
        with patch("gettext.translation", return_value=gettext.NullTranslations()):
            instance = I18n(domain=DOMAIN, locales_dir=LOCALES_DIR, locale="sv")

        with patch("gettext.translation", side_effect=FileNotFoundError):
            instance.set_locale("xx")  # non-existent locale

        # Should fall back to NullTranslations, returning the original string
        assert instance.gettext("Hello") == "Hello"
