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

### All Features (49 scenarios)

| Feature | Scenarios | Purpose |
|---------|-----------|---------|
| order_creation | 9 | Create orders with validation |
| debt_calculation | 6 | Calculate who owes whom |
| payment_processing | 8 | Record and validate payments |
| debt_query | 7 | Query current debt state |
| persistence | 6 | SQLite data persistence |
| bot_commands | 13 | Telegram message parsing/formatting |

### Security Scenarios

- Negative amount validation
- Zero amount validation
- Overflow protection (>1B rubles)
- Minimum participants check
- Payment exceeds debt protection

## Commit History

| # | Hash | Type | Description |
|---|------|------|-------------|
| 1 | 93a8cdc | docs | Initial project structure and BDD features |
| 2 | 232b907 | feat | MVP domain logic with full test coverage |
| 3 | 26e4e5d | docs | Update development log with MVP completion |
| 4 | 2495483 | feat | SQLite repository with integration tests |
| 5 | febeef9 | feat | Telegram bot with aiogram handlers |
| 6 | e5e39e6 | docs | Update README with bot usage |
| 7 | cf0218e | security | Comprehensive security review |

## Evolution Plan

### MVP (COMPLETE) ✅
- Order creation with equal split
- Debt tracking
- Payment recording
- Basic queries

### Phase E1: SQLite Persistence (COMPLETE) ✅
- SQLite repository implementation
- Data persists across restarts
- Concurrent access safety tested

### Phase E2: Telegram Bot (COMPLETE) ✅
- aiogram handlers for all commands
- Message parsing for orders and payments
- Response formatting with emoji

### Phase E3: Security Review (COMPLETE) ✅
- Threat model documented
- Input validation verified
- SQL injection prevention confirmed
- Abuse cases identified with mitigations

### Remaining Phases
- E4: Payment confirmation flow
- E5: Debt aging (days since order)
- E6: Group isolation by chat_id

## Final Test Count: 49 scenarios

## Lessons Learned

### Session 1 Insights

1. **pytest-bdd language directive**: Using `# language: ru` requires Russian Gherkin keywords (Функция, Сценарий). Simpler to use English keywords with Russian content.

2. **Step definition reuse**: pytest-bdd requires unique step definitions per test file unless using conftest.py fixtures carefully.

3. **Decimal precision**: Using `Decimal(str(float_value))` ensures accurate conversion from float test parameters.

4. **Repository pattern**: InMemoryRepository enables fast isolated tests while SQLite can be swapped in for integration tests.
