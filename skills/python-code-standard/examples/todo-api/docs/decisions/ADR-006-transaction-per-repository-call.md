# ADR-006: One transaction per repository call

**Status:** accepted

## Context
Polar opens one session per request and commits in middleware. That is the right default when a use case writes several aggregates that must commit together.

## Decision
Here every use case performs at most one write, and that write is guarded by `version` in its `WHERE` clause. `SqlTodoRepository` therefore opens a short `async with sessions.begin()` per method; the read in `versioned_write.save` and the guarded write need not share a transaction. The engine has pool, connect and command timeouts; `expire_on_commit=False`.

## Consequences
No session object leaks into handlers or the router. When a use case must write two aggregates atomically, introduce a `UnitOfWork` port (`async with uow: … await uow.commit()`) and pass the session to repositories created inside it; do not add commits to the router.
