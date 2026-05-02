#!/usr/bin/env python3
"""Extract and initialise translations for all libs and apps.

Commands
--------
extract (default)
    Run ``xgettext`` on each package that has a ``locales/`` directory,
    then merge the result into any existing ``.po`` files with ``msgmerge``.

init --locale <lang> [--package <name>]
    Create the ``locales/<lang>/LC_MESSAGES/`` directory structure and
    initialise a ``.po`` file from the ``.pot`` template using ``msginit``.
    If ``--package`` is omitted, initialises all packages that have a ``.pot``.

Usage::

    # Extract strings and merge into existing .po files
    python tools/extract_translations.py

    # Initialise Swedish for all packages
    python tools/extract_translations.py init --locale sv

    # Initialise Swedish for one package only
    python tools/extract_translations.py init --locale sv --package pytetris-save

Requirements:
    - GNU gettext tools (``xgettext``, ``msginit``, ``msgmerge``) must be on PATH.
    - Run from the repository root with the virtualenv active.
"""

import argparse
import logging
import subprocess
import sys
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Repository layout
# ---------------------------------------------------------------------------

REPO_ROOT = Path(__file__).parent.parent

#: Directories to scan for packages. Each sub-directory that contains a
#: ``locales/`` folder will be processed automatically — no manual registration
#: needed when new libs or apps are added.
SEARCH_DIRS: list[Path] = [
    REPO_ROOT / "libs",
    REPO_ROOT / "apps",
]

#: Translation function names to extract. Extend this if your pytetris-i18n
#: wrapper exposes additional aliases (e.g. ``_n`` for plurals).
KEYWORDS: list[str] = [
    "_",
    "_n:1,2",
    "_i18n.gettext",
    "_i18n.gettext:1,2",
    # "i18n.t",
    # "i18n.n:1,2",
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def run(
    args: list[str], *, stdin: str | None = None
) -> subprocess.CompletedProcess[str]:
    """Run a subprocess and log its output.

    :param args: Command and arguments to run.
    :param stdin: Optional string to pass to the process on stdin.
    :return: Completed process result.
    :raises SystemExit: If the process exits with a non-zero return code.
    """
    log.debug("Running: %s", " ".join(args))
    result = subprocess.run(
        args,
        input=stdin,
        capture_output=True,
        text=True,
    )
    if result.stdout:
        log.debug(result.stdout.strip())
    if result.stderr:
        log.warning(result.stderr.strip())
    if result.returncode != 0:
        log.error("Command failed: %s", " ".join(args))
        sys.exit(result.returncode)
    return result


def find_packages(
    name_filter: str | None = None, lang_filter: str | None = None
) -> list[Path]:
    """Find all packages that have a ``locales/`` directory.

    :param name_filter: If provided, only return the package with this name.
    :param lang_filter: If provided, only return the package with this language.
    :return: Sorted list of package root paths.
    """
    packages: list[Path] = []
    for search_dir in SEARCH_DIRS:
        if not search_dir.is_dir():
            log.warning("Search directory does not exist, skipping: %s", search_dir)
            continue
        for candidate in sorted(search_dir.iterdir()):
            if not candidate.is_dir():
                continue
            if name_filter and candidate.name != name_filter:
                continue
            if not (candidate / "locales").is_dir():
                continue
            if (
                lang_filter
                and not (candidate / "locales" / lang_filter / "LC_MESSAGES").is_dir()
            ):
                continue
            packages.append(candidate)

    if name_filter and not packages:
        log.error(
            "Package '%s' not found or has no locales/ directory.",
            name_filter,
        )
        sys.exit(1)
    if lang_filter and not packages:
        log.error(
            "Locale '%s' not found or does not exist in locales/ directory.",
            lang_filter,
        )
        sys.exit(1)

    return packages


def find_python_files(package_root: Path) -> list[Path]:
    """Find all ``.py`` files within a package, excluding tests.

    :param package_root: Root directory of the package.
    :return: Sorted list of Python source file paths.
    """
    return sorted(
        p
        for p in package_root.rglob("*.py")
        if "tests" not in p.parts and "__pycache__" not in p.parts
    )


def get_domain(package_root: Path) -> str | None:
    """Derive the gettext domain name from the Python package directory.

    :param package_root: Root directory of the package.
    :return: Domain name, or ``None`` if no Python package was found.
    """
    python_packages = [
        d for d in package_root.iterdir() if d.is_dir() and (d / "__init__.py").exists()
    ]
    if not python_packages:
        return None
    return python_packages[0].name


# ---------------------------------------------------------------------------
# extract command
# ---------------------------------------------------------------------------


def extract(package_root: Path) -> None:
    """Extract translatable strings from a single package.

    Writes a ``.pot`` file to ``<package_root>/locales/<domain>.pot``.
    Skips gracefully if no translatable strings are found.

    :param package_root: Root directory of the package.
    """
    domain = get_domain(package_root)
    if not domain:
        log.warning("No Python package found in %s, skipping.", package_root)
        return

    locales_dir = package_root / "locales"
    pot_file = locales_dir / f"{domain}.pot"
    locales_dir.mkdir(exist_ok=True)

    py_files = find_python_files(package_root)
    if not py_files:
        log.info("No Python files found in %s, skipping.", package_root)
        return

    log.info("Extracting: %s -> %s", package_root.name, pot_file.relative_to(REPO_ROOT))

    # xgettext requires --keyword=VALUE format (not --keyword VALUE) since 0.26
    keyword_args: list[str] = [f"--keyword={kw}" for kw in KEYWORDS]
    file_list = "\n".join(str(f) for f in py_files)

    run(
        [
            "xgettext",
            "--language=Python",
            *keyword_args,
            f"--output={pot_file}",
            "--from-code=UTF-8",
            "--add-comments=i18n",
            "--files-from=-",
        ],
        stdin=file_list,
    )

    if not pot_file.exists():
        log.info(
            "No translatable strings found in %s — nothing to merge.", package_root.name
        )


def merge(package_root: Path) -> None:
    """Merge an updated ``.pot`` into all existing ``.po`` files.

    :param package_root: Root directory of the package.
    """
    locales_dir = package_root / "locales"
    pot_files = list(locales_dir.glob("*.pot"))
    if not pot_files:
        return

    pot_file = pot_files[0]
    po_files = list(locales_dir.rglob("*.po"))

    if not po_files:
        log.info(
            "No .po files found for %s — run `init --locale <lang>` to create one.",
            package_root.name,
        )
        return

    for po_file in sorted(po_files):
        log.info("Merging: %s <- %s", po_file.relative_to(REPO_ROOT), pot_file.name)
        run(
            [
                "msgmerge",
                "--update",
                "--backup=none",
                str(po_file),
                str(pot_file),
            ]
        )


def cmd_extract(args: argparse.Namespace) -> None:
    """Entry point for the ``extract`` command.

    :param args: Parsed command-line arguments.
    """
    packages = find_packages(name_filter=args.package)
    if not packages:
        log.error(
            "No packages with a locales/ directory found under: %s",
            ", ".join(str(d) for d in SEARCH_DIRS),
        )
        sys.exit(1)

    log.info(
        "Found %d package(s): %s",
        len(packages),
        ", ".join(p.name for p in packages),
    )

    for package in packages:
        extract(package)
        merge(package)

    log.info("Done.")


# ---------------------------------------------------------------------------
# init command
# ---------------------------------------------------------------------------


def init_locale(package_root: Path, locale: str) -> None:
    """Initialise a new ``.po`` file for a locale in a single package.

    Creates ``locales/<locale>/LC_MESSAGES/`` if it does not exist, then
    runs ``msginit`` to produce the ``.po`` file from the ``.pot`` template.

    Skips if no ``.pot`` file exists (run ``extract`` first).
    Skips if the ``.po`` file already exists to avoid overwriting translations.

    :param package_root: Root directory of the package.
    :param locale: Locale code, e.g. ``sv``, ``en``, ``de``.
    """
    domain = get_domain(package_root)
    if not domain:
        log.warning("No Python package found in %s, skipping.", package_root)
        return

    locales_dir = package_root / "locales"
    pot_file = locales_dir / f"{domain}.pot"

    if not pot_file.exists():
        log.warning(
            "No .pot file found for %s — run extract first.",
            package_root.name,
        )
        return

    lc_messages_dir = locales_dir / locale / "LC_MESSAGES"
    po_file = lc_messages_dir / f"{domain}.po"

    if po_file.exists():
        log.info(
            "Already exists, skipping: %s (use msgmerge to update it)",
            po_file.relative_to(REPO_ROOT),
        )
        return

    log.info("Initialising: %s", po_file.relative_to(REPO_ROOT))
    lc_messages_dir.mkdir(parents=True, exist_ok=True)

    run(
        [
            "msginit",
            f"--input={pot_file}",
            f"--output={po_file}",
            f"--locale={locale}",
            "--no-translator",  # skip interactive prompt for translator name/email
        ]
    )


def cmd_init(args: argparse.Namespace) -> None:
    """Entry point for the ``init`` command.

    :param args: Parsed command-line arguments.
    """
    packages = find_packages(name_filter=args.package)
    if not packages:
        log.error("No matching packages found.")
        sys.exit(1)

    for package in packages:
        init_locale(package, args.locale)

    log.info("Done.")


# ---------------------------------------------------------------------------
# build command
# ---------------------------------------------------------------------------


def build_locale(package_root: Path, locale: str) -> None:
    """Build a new ``.mo`` file for a locale in a single package.

    Creates ``locales/<locale>/LC_MESSAGES/`` if it does not exist, then
    runs ``msgfmt`` to produce the ``.mo`` file from the ``.po`` template.

    Skips if no ``.po`` file exists (run ``init`` first).
    Skips if the ``.mo`` file already exists to avoid overwriting translations.

    :param package_root: Root directory of the package.
    :param locale: Locale code, e.g. ``sv``, ``en``, ``de``.
    """
    domain = get_domain(package_root)
    if not domain:
        log.warning("No Python package found in %s, skipping.", package_root)
        return

    lc_messages_dir = package_root / "locales" / locale / "LC_MESSAGES"
    po_file = lc_messages_dir / f"{domain}.po"
    mo_file = lc_messages_dir / f"{domain}.mo"

    if not po_file.exists():
        log.warning(
            "No .po file found for %s — run init first.",
            package_root.name,
        )
        return

    # if mo_file.exists():
    #    log.info(
    #        "Already exists, skipping: %s (use msgmerge to update it)",
    #        mo_file.relative_to(REPO_ROOT),
    #    )
    #    return

    run(
        [
            "msgfmt",
            f"--output-file={mo_file}",
            f"{po_file}",
        ]
    )


def cmd_build(args: argparse.Namespace) -> None:
    """Entry point for the ``build`` command.

    :param args: Parsed command-line arguments.
    """
    packages = find_packages(name_filter=args.package, lang_filter=args.locale)
    if not packages:
        log.error("No matching packages found.")
        sys.exit(1)

    for package in packages:
        build_locale(package, args.locale)

    log.info("Done.")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    """Build the argument parser.

    :return: Configured argument parser.
    """
    parser = argparse.ArgumentParser(
        description="Manage translations for the pytetris monorepo.",
    )
    subparsers = parser.add_subparsers(dest="command")

    # extract (default)
    extract_parser = subparsers.add_parser(
        "extract",
        help="Extract strings and merge into existing .po files (default).",
    )
    extract_parser.add_argument(
        "--package",
        default=None,
        metavar="NAME",
        help="Package name to extract (e.g. pytetris-save). Defaults to all packages.",
    )

    # init
    init_parser = subparsers.add_parser(
        "init",
        help="Initialise a new .po file for a locale.",
    )
    init_parser.add_argument(
        "--locale",
        required=True,
        metavar="LANG",
        help="Locale code to initialise, e.g. sv, sv_SE, en, en_GB, de, de_DE.",
    )
    init_parser.add_argument(
        "--package",
        default=None,
        metavar="NAME",
        help="Package name to initialise (e.g. pytetris-save). Defaults to all packages.",
    )

    # build
    build_parser = subparsers.add_parser(
        "build",
        help="Build translation files.",
    )
    build_parser.add_argument(
        "--locale",
        required=True,
        metavar="LANG",
        help="Locale code to build, e.g. sv, sv_SE, en, en_GB, de, de_DE.",
    )
    build_parser.add_argument(
        "--package",
        default=None,
        metavar="NAME",
        help="Package name to build (e.g. pytetris-save). Defaults to all packages.",
    )

    return parser


def main() -> None:
    """Parse arguments and dispatch to the appropriate command."""
    parser = build_parser()
    args = parser.parse_args()

    match args.command:
        case "init":
            cmd_init(args)
        case "extract":
            cmd_extract(args)
        case "build":
            cmd_build(args)
        case _:
            parser.print_help()
            sys.exit(1)


if __name__ == "__main__":
    main()
