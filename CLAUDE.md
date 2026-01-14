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

## Development Evolution

### MVP (COMPLETE) ✅
**Goal:** Core functionality for shared expense tracking

**Implementation:**
- Order creation with equal split
- Debt calculation with netting
- Payment recording
- Basic debt queries
- 31 BDD scenarios in 4 feature files

**Key decisions:**
- MVP scope limited to single group
- No confirmation flow (simpler implementation)
- 2 decimal places, standard rounding

### Phase E1: SQLite Persistence (COMPLETE) ✅
**Goal:** Data persistence across restarts

**Implementation:**
- SQLite repository implementation
- Transaction management with ACID guarantees
- Database migrations for schema updates
- Concurrent access safety

**Key insights:**
- Repository pattern enables easy swapping between in-memory and SQLite
- Migrations can be handled inline during initialization

### Phase E2: Telegram Bot (COMPLETE) ✅
**Goal:** User interface via Telegram

**Implementation:**
- aiogram handlers for all commands
- Message parsing for orders and payments
- Response formatting with emoji
- Explicit payer syntax: `payer:@username`

**Key decisions:**
- First mentioned user defaults to payer
- Parser extracts absolute values from negative inputs

### Phase E3: Security & Testing (COMPLETE) ✅
**Goal:** Production readiness

**Implementation:**
- 14 end-to-end handler scenarios (now in BDD) — total: 86 tests (72 BDD scenarios + integration coverage)
- Secure token storage with python-dotenv
- Input validation for all user inputs
- SQL injection prevention

**Key insights:**
- Direct handler testing more reliable than full dispatcher
- Router observers require `.handlers` attribute access
- GitHub secret scanning detected session IDs in .specstory files

### Phase E4: Feature Enhancements (COMPLETE) ✅
**Goal:** Improved UX and order management

**Implementation:**
- `/delete` command to remove orders by creator
- Order tracking with `created_by` field
- Database migration for new column
- Improved help message clarity
- Netted debt display in `/owed` command

**Key insights:**
- Tracking creator vs payer enables better deletion control
- Netting debts significantly improves readability
- Consolidated debt views reduce confusion

### Remaining Phases
- E5: Payment confirmation flow
- E6: Debt aging (days since order)

## Test Coverage

### All Features (86 tests; 72 BDD scenarios + supporting coverage)

| Feature | Scenarios | Purpose |
|---------|-----------|---------|
| order_creation | 9 | Create orders with validation |
| debt_calculation | 7 | Calculate who owes whom (including netting) |
| payment_processing | 8 | Record and validate payments |
| debt_query | 7 | Query current debt state |
| persistence | 6 | SQLite data persistence |
| bot_commands | 16 | Telegram message parsing/formatting |
| chat_isolation | 5 | Validate per-chat data segregation |
| **bot_integration** | **14** | **End-to-end handler workflows (BDD)** |

**Bot Integration Scenarios** (BDD):
- Order flow (3): with/without description, explicit payer
- Payment flow (2): full and partial payments
- Query commands (3): /debts, /owed, no debts case
- Command handlers (2): /start, /help
- Error handling (4): invalid input, payment errors, missing username

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
| 8 | ffa84dd | feat | Track debt descriptions |
| 9 | b9e1c28 | feat | Add explicit payer syntax (payer:@username) |
| 10 | d9537cb | feat | Automatic debt netting with breakdown |
| 11 | 7e2f4a3 | test | Bot integration tests (67 tests passing) |
| 12 | 9d8b6f5 | security | Remove .specstory files, add .env for bot token |
| 13 | ca22e0b | fix | Update help formatting and /owed netting display |
| 14 | ed62725 | feat | Add /delete command to remove orders by creator |
| 15 | CURRENT | feat | Chat isolation + BDD bot integration + SQLite migration guard + pip-audit clean |

## Phase E7 - Chat Isolation (COMPLETE) ✅

**Goal:** Allow bot to work in multiple Telegram groups simultaneously

**Status:** All 86 tests passing (BDD scenarios converted for bot integration); bot manually tested; pip-audit clean

**Changes made:**
- Added `chat_id` field to Order, Debt, Payment models (default 0 for backwards compatibility)
- Database migrations: added chat_id columns with indexes to orders, debts, payments tables; guard ensures columns exist before index creation on older DBs
- Changed debt primary key to (debtor, creditor, chat_id) to allow same users in different groups
- Updated InMemoryRepository and SQLiteRepository to filter by chat_id
- Modified all service methods (20+ methods) to accept and filter by chat_id parameter
- Updated all bot handlers to extract message.chat.id and pass to services
- Converted bot integration tests to BDD (.feature + steps); removed legacy integration test file
- Fixed sqlite3.Row access issues (Row doesn't have .get() method)
- Security: ran `pip-audit` (2.10.0) — no known vulnerabilities

## Lessons Learned

**pytest-bdd language directive**: Using `# language: ru` requires Russian Gherkin keywords. Simpler to use English keywords with Russian content.

**Repository pattern**: InMemoryRepository enables fast isolated tests while SQLite can be swapped in for production.

**Decimal precision**: Using `Decimal(str(float_value))` ensures accurate conversion from float test parameters.

**Router testing**: Direct handler calls with mock Messages more reliable than full dispatcher testing.

**sqlite3.Row access**: Row objects don't have .get() method. Use `row['key'] if 'key' in row.keys() else default` instead of `row.get('key', default)`.
