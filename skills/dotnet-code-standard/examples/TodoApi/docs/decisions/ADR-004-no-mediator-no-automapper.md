# ADR-004: No MediatR, no AutoMapper

Status: accepted

## Context
MediatR and AutoMapper are now dual-licensed (RPL-1.5 or commercial, licence key required). For seven use cases a mediator adds indirection without adding behaviour.

## Decision
Each use case is a sealed handler class registered in `AddApplication()` and injected directly into its endpoint. Mapping is a static `From(...)` method on each response record.

## Consequences
Cross-cutting behaviour (validation, logging, transactions) is written explicitly or as endpoint filters. If a pipeline is ever needed, use the MIT `Mediator` source generator.
