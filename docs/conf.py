"""Sphinx configuration for django-hotels."""

from importlib.metadata import version as pkg_version

project = "django-hotels"
author = "Awais Jibran"
copyright = "2026, Awais Jibran"
release = pkg_version("django-hotels")
version = release

extensions = ["myst_parser"]

source_suffix = {
    ".rst": "restructuredtext",
    ".md": "markdown",
}

html_theme = "furo"
