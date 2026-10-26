# ADR-001: Feature packages with inward layers

**Status:** accepted

## Context
Polar (`polar/<module>/{endpoints,service,repository,schemas}.py`) and fastapi-best-practices group code by feature. cosmicpython splits `domain / service_layer / adapters / entrypoints`. Flat `models.py` + `crud.py` (full-stack-fastapi-template) stops scaling once a second feature or backend appears.

## Decision
One package per feature (`todo_api/todos/`) with four sub-packages: `domain` (pure dataclasses and rules), `application` (ports + one handler per use case), `infrastructure` (SQLAlchemy, in-memory), `http` (FastAPI router, Pydantic schemas). Cross-cutting HTTP code lives in `todo_api/web`, database/observability plumbing in `todo_api/infrastructure`, pure helpers in `todo_api/shared`. `container.py` builds singletons; `main.py:create_app` wires them.

import-linter enforces it (`[tool.importlinter]` in `pyproject.toml`): `http | infrastructure → application → domain`; domain and application may not import FastAPI, Pydantic, SQLAlchemy, JWT or OpenTelemetry; `shared`, `web` and `infrastructure` may not import a feature. `tests/unit/test_architecture.py` covers what imports cannot: every todo route depends on `current_owner`, and table columns equal the aggregate's fields.

## Consequences
More files than a flat app (ADR-007 explains why use cases stay separate modules). A new feature copies the four folders; a new backend is one class in `infrastructure` plus a branch in `build_container`. If the app ever stays a single CRUD resource with one backend, collapse to `router.py / schemas.py / service.py / repository.py` in one package (rule 2 of the skill).
