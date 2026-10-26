# ADR-001: Flat feature package with in-memory storage behind a port

**Status:** accepted

## Context
The service has one resource (todos), one entry point (the HTTP API) and, for now, one storage backend (in memory). The brief asks that storage be easy to swap for a real database later.

## Decision
One package `taskboard/todos/` with `domain.py`, `ports.py`, `service.py` (one `TodoService` class, Polar's style), `repository.py`, `schemas.py`, `dependencies.py`, `router.py`. The service depends on the `TodoRepository` Protocol only; `container.py` is the only module that imports the in-memory adapter. import-linter enforces the layer order and that the service never imports the adapter.

## Consequences
Swapping to PostgreSQL is one adapter, one settings variant, one container branch and one test fixture param; the service, router and contract tests do not change. If a second backend or entry point actually ships, move to the layered layout.
