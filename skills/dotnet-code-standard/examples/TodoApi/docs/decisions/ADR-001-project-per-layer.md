# ADR-001: One project per layer

Status: accepted

## Context
Use separate projects when at least two of these hold: a state machine or cross-field invariants, more than one storage backend, more than one entry point (API + worker), or a team larger than two. This API has a status lifecycle with idempotent transitions, ownership, versioning and two storage backends. Folder-only layering in one project is enforced only by discipline.

## Decision
Four projects: `Todo.Domain` → `Todo.Application` → `Todo.Infrastructure` → `Todo.Api`. Project references make illegal dependencies a compile error; `tests/Todo.UnitTests/Architecture` guards the rules project references cannot express (no EF Core or ASP.NET Core in Application).

## Consequences
More projects to navigate. A service with no domain logic (a thin proxy, a CRUD admin tool) should use a single Api project with feature folders instead.
