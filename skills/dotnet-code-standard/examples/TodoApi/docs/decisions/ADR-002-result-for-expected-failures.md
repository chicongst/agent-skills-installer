# ADR-002: Result<T> for expected failures, exceptions for bugs

Status: accepted

## Context
Not found, validation and version conflicts happen on every busy day. Throwing for them hides control flow and costs a stack trace each time.

## Decision
Domain and application code return `Result<T>` carrying a `DomainError(Kind, Code, Message, Field, Details)`. The API maps `ErrorKind` to an HTTP status in `Http/Problems.cs` and always answers with RFC 9457 ProblemDetails. Exceptions are reserved for programmer errors and infrastructure faults; `GlobalExceptionHandler` turns them into a 500 ProblemDetails and logs them.

## Consequences
Handlers must check `IsSuccess`. No third-party Result library: the type is 40 lines and has no licence risk.
