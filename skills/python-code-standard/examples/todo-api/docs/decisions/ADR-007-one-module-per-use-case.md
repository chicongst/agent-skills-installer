# ADR-007: One module per use case, not one service class

**Status:** accepted

## Context
The review council's architect pointed out that Polar uses one `service.py` per feature and that seven `Command` + `Handler` pairs for a todo list read like C#/MediatR. The alternative is one `TodoService(todos, clock)` with seven methods.

## Decision
Keep `application/use_cases/<action>.py` (a frozen command dataclass + a handler with `handle`) in this reference, because:
- it is the layout the other code-standard skills (Node, .NET) teach, so a reader moving between stacks finds the same shape;
- each use case lists exactly the dependencies it needs, and adding one does not grow a shared class;
- the dependency factories in `http/dependencies.py` are one line each.

The shared steps live in `versioned_write.save`, so the write handlers are five lines. Read handlers (`GetTodoHandler`, `ListTodosHandler`) are thin pass-throughs to the port; that is accepted so every action has the same entry shape and a place for future authorisation or caching. The list handler takes the port's `TodoListQuery` directly rather than a duplicate type.

## Consequences
For a small feature, or when the team prefers Polar's style, one `service.py` with a class per aggregate is equally acceptable — the skill's flat layout (rule 2) uses it. Do not mix the two inside one feature.
