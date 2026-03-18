# Architecture Template

## Problem Statement
[What we're building and why. Include non-goals.]

## Architecture Overview
**Pattern**: [Monolith / Microservices / Serverless / Hybrid]
**Communication**: [REST / Events / gRPC / Mixed]
**Data Strategy**: [Shared DB / DB per service / Event Sourcing]

## Component Design
### [Component Name]
- **Responsibility**: [Single purpose]
- **Data owned**: [Authoritative data]
- **APIs exposed**: [Endpoints/events]
- **Dependencies**: [What it calls]

## Data Flow
[Primary data flow diagram]

## Failure Modes
| Failure | Impact | Mitigation | Recovery |
|---------|--------|------------|----------|
| | | | |

## Tradeoffs
| Decision | Benefit | Cost | Alternative |
|----------|---------|------|-------------|
| | | | |

## Rollout Strategy
1. Phase 1: [What ships first]
2. Rollback plan: [How to undo]
