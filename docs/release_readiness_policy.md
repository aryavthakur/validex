# Release Readiness Policy

Validex 0.1.0 is designated **Research preview**.

Mandatory blockers:

- Backend tests, frontend tests, Ruff, mypy, benchmark, static parity, frontend build, wheel build, sdist build, installed-wheel smoke, or sdist-built-wheel smoke fail.
- Runtime dependency audit reports an unapproved vulnerability.
- npm audit reports unresolved production or release-relevant advisories.
- Required validation data is missing or has a checksum mismatch.
- Release artifacts contain forbidden files, private/pilot data, credentials, developer paths, stale static assets, source maps, or frontend development artifacts.
- Documentation or active frontend copy claims scientific validation beyond repository evidence.

Warnings:

- Independent external validation is incomplete.
- A development-only advisory has a documented, time-limited exception.
- Repeated build comparison differs only in expected archive metadata.

Informational checks:

- Bundle-size observations.
- Non-Linux operating systems not covered by CI.

External-validation incompleteness is not a scientific pass. It is an explicit limitation that keeps the product in research-preview status.
