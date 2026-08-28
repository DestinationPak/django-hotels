# Changelog

All notable changes to this project are documented here. Format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

### Removed
- `Hotel.city` (a free-text `CharField`) - superseded by `Hotel.location`, a
  swappable FK.

### Changed
- `HotelListSerializer`/`HotelDetailSerializer` now return a nested
  `location` object (`name`/`slug`/`lat`/`lng`) instead of the removed
  `city` string field.
- The public `?city=` filter on `/hotels/` now does a case-insensitive
  match against `location.name` instead of an exact match on the removed
  `city` field.

### Fixed
- CI's `Unit Tests` workflow now actually runs `pytest` - its last step was a
  copy-paste of the `Quality` workflow's lint command, so no test in the
  suite ever ran on pull requests.
- `setup.py`/`setup.cfg` no longer duplicate (and drift from) each other's
  package metadata; `setup.cfg` is now the single source of truth.
- Published `install_requires` now actually matches the code's imports:
  adds `swapper` and `drf-spectacular` (both imported by the app but
  missing from `0.1.0`'s metadata), drops `mysqlclient` and `setuptools`
  (neither is imported by this package - a consuming project's own DB
  driver choice shouldn't be forced on it).
- `packages = find:` no longer sweeps the dev-only `django-hotels` project
  shell and local `settings` package into the built wheel/sdist alongside
  the real `django_hotels` app.
- `LICENSE` no longer attributes the project to "The Python Packaging
  Authority" (leftover cookiecutter boilerplate).

### Changed
- Local dev/test settings (`settings/test.py`) now default to an in-memory
  SQLite database instead of requiring a running MySQL server - nothing in
  this package's models/migrations is MySQL-specific. `settings/common.py`
  (Docker/local-server dev) is unaffected and still targets MySQL.
- CI now runs the suite across a Python 3.11/3.12/3.13 x Django 4.2/5.2
  matrix instead of a single pinned combination.
- `django-filter` is capped at `<25.2` (25.2 dropped Django 4.2 support) so
  the declared `Django>=4.2,<6.0` support range is one that's actually
  installable and tested, not just asserted.

## [0.1.0]
Initial release: hotels/room-types/availability/booking models, a public
read-only catalog API, guest booking create/lookup, and a swappable
`Location` model.
