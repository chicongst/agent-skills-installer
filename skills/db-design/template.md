# Database Design: [System / feature]

**Engine**: [e.g. PostgreSQL 17] · **Scope**: [new schema / change to existing schema / review]

## Findings
- [🔴/🟠/🟡/💭] **[table.column or DDL line]** — [defect] → [corrected DDL]

## Assumptions
- [Assumption not stated in the input — confirm with user]

## Domain Model
- [Entity] 1:N [Entity] — [ownership / lifecycle note]

## Schema
### [table]
| Column | Type | Constraints | Notes |
|---|---|---|---|
| [col] | [type] | [PK / FK → / NOT NULL / CHECK / UNIQUE] | [why] |

**Table constraints**: [composite UNIQUE / FK / CHECK / EXCLUDE]

## DDL
```sql
[Complete, runnable DDL: tables, indexes, policies]
```

## Indexes
| Index | Definition | Serves | Notes |
|---|---|---|---|
| [name] | [(cols) / WHERE / INCLUDE] | [Q# or FK] | [trade-off] |

## Query Patterns
### Q1 — [purpose]
```sql
[query with explicit columns and $n parameters]
```
**Plan**: [verified — plan node seen, engine, data size] or [unverified — expected plan]

## Data Integrity
| Business rule | Enforced by |
|---|---|
| [rule] | [constraint / policy / application — why] |

## Migration Strategy
[New schema: how it is created. Change: expand/contract steps. Rollout details → `migration-safety`.]

## Trade-offs & Open Questions
- **[Decision]** — [alternative considered, why rejected, what would change it]
- [Open question for the user]
