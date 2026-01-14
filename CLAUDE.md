# CLAUDE.md - AI Development Log

This document records how Claude AI was used in developing this project, following BDD-first methodology.

## Development Methodology

### BDD-First Approach

1. **Feature files written BEFORE code** - Scenarios define expected behavior
2. **Step definitions call REAL domain code** - No mocks of business logic
3. **Tests FAIL first** - TDD red-green-refactor cycle
4. **Minimal implementation** - Only enough code to pass tests
5. **Incremental commits** - Each logical step is committed

### Architecture Decisions

| Decision | Rationale |
|----------|-----------|
| Domain-driven design | Business logic independent of infrastructure |
| In-memory repository for tests | Fast, isolated tests without DB setup |
| Decimal for money | Avoid floating-point precision issues |
| Russian feature files | Match user language, clearer requirements |

## AI Collaboration Sessions

### Session 1: Project Setup (2025-01-14)

**Goal:** Establish project structure and MVP feature files

**What Claude did:**
- Analyzed exam requirements from GitHub
- Designed clean architecture (domain/persistence/bot)
- Created 4 BDD feature files with 31 scenarios
- Wrote step definitions that call real domain code
- Set up pytest-bdd configuration

**Key decisions made:**
1. MVP scope limited to: order creation, debt calculation, payments, queries
2. Telegram integration deferred to post-MVP
3. Security validation built into feature scenarios
4. Rounding strategy: 2 decimal places, standard rounding

**Trade-offs:**
- Feature files in Russian (matches domain, but limits international use)
- No confirmation flow in MVP (simpler, but less secure)
- Single group assumed (simpler, multi-group is post-MVP)

## Test Coverage

### MVP Features (31 scenarios)

| Feature | Scenarios | Purpose |
|---------|-----------|---------|
| order_creation | 8 | Create orders with validation |
| debt_calculation | 6 | Calculate who owes whom |
| payment_processing | 8 | Record and validate payments |
| debt_query | 7 | Query current debt state |

### Security Scenarios

- Negative amount validation
- Zero amount validation
- Overflow protection (>1B rubles)
- Minimum participants check
- Payment exceeds debt protection

## Commit History

Will be updated as development progresses.

| Commit | Type | Description |
|--------|------|-------------|
| 1 | docs | Initial project structure and BDD features |

## Evolution Plan

### MVP (Current)
- Order creation with equal split
- Debt tracking
- Payment recording
- Basic queries

### Post-MVP Phases
1. SQLite persistence layer
2. Telegram bot integration
3. Payment confirmation flow
4. Debt aging (days since order)
5. Order history and details
6. Debt optimization (netting)

## Lessons Learned

*Will be updated as project progresses.*
