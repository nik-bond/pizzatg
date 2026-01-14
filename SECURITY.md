# Security Review

This document describes the security model, threat analysis, and protective measures implemented in the Food Debt Tracker bot.

## Table of Contents

1. [Threat Model](#threat-model)
2. [Input Validation](#input-validation)
3. [SQL Injection Prevention](#sql-injection-prevention)
4. [Authentication & Authorization](#authentication--authorization)
5. [Data Integrity](#data-integrity)
6. [Abuse Cases](#abuse-cases)
7. [Known Limitations](#known-limitations)
8. [Security Checklist](#security-checklist)

---

## Threat Model

### Assets

| Asset | Sensitivity | Description |
|-------|-------------|-------------|
| Debt records | Medium | Who owes whom and how much |
| Payment history | Medium | Record of payments made |
| User identities | Low | Telegram usernames |
| Bot token | **Critical** | Access to Telegram Bot API |

### Threat Actors

| Actor | Motivation | Capability |
|-------|------------|------------|
| Malicious user | Financial gain, harassment | Can send arbitrary messages |
| Group member | Reduce own debt unfairly | Legitimate access to bot |
| External attacker | Data theft, bot takeover | Network access |

### Attack Surface

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  Telegram API   │────▶│   Bot Server    │────▶│   SQLite DB     │
│  (untrusted     │     │  (parsers,      │     │  (persistent    │
│   input)        │     │   handlers)     │     │   storage)      │
└─────────────────┘     └─────────────────┘     └─────────────────┘
        │                       │                       │
   User messages          Business logic          Parameterized
   (attack vector)        (validation)            queries only
```

---

## Input Validation

### Amount Validation

**Location:** `src/domain/services.py` → `OrderService._validate_amount()`

| Rule | Implementation | Reason |
|------|---------------|--------|
| Positive only | `amount > 0` | Prevent negative debt creation |
| Upper limit | `amount <= 1,000,000,000` | Prevent overflow attacks |
| Numeric type | `Decimal` parsing | Prevent type confusion |

```python
def _validate_amount(self, amount: Decimal) -> None:
    if amount <= Decimal('0'):
        raise ValidationError("Сумма должна быть положительной")
    if amount > MAX_AMOUNT:  # 1 billion
        raise ValidationError("Сумма превышает допустимый лимит")
```

### Participant Validation

**Location:** `src/domain/services.py` → `OrderService._validate_participants()`

| Rule | Implementation | Reason |
|------|---------------|--------|
| Minimum 2 | `len(participants) >= 2` | Single person can't split |
| Non-empty names | Implicit via parser | Prevent empty usernames |

### Payment Validation

**Location:** `src/domain/services.py` → `PaymentService.record_payment()`

| Rule | Implementation | Reason |
|------|---------------|--------|
| Positive amount | `amount > 0` | Prevent negative payments |
| Not exceeding debt | `amount <= debt.amount` | Prevent overpayment/reverse debt |
| Debt must exist | Check before reduce | Prevent phantom payments |

```python
def record_payment(self, debtor, creditor, amount):
    if amount <= Decimal('0'):
        raise ValidationError("Сумма платежа должна быть положительной")
    # ... debt existence check
    if amount > debt.amount:
        raise PaymentExceedsDebtError("Сумма платежа превышает долг")
```

### Message Parsing

**Location:** `src/bot/parsers.py`

| Input | Validation | Sanitization |
|-------|------------|--------------|
| Username | Regex `@?(\w+)` | Strip `@` prefix |
| Amount | Regex `\b(\d+)\b` | Convert to Decimal |
| Description | Everything before amount | No HTML/script injection risk |

---

## SQL Injection Prevention

### Parameterized Queries Only

**All database queries use parameterized statements.** No string concatenation or formatting is used for SQL.

**Example (SAFE):**
```python
# src/persistence/sqlite_repo.py
conn.execute(
    "SELECT * FROM debts WHERE debtor = ? AND creditor = ?",
    (debtor, creditor)  # Parameters passed separately
)
```

**Never used (UNSAFE):**
```python
# This pattern is NOT in the codebase
conn.execute(f"SELECT * FROM debts WHERE debtor = '{debtor}'")  # VULNERABLE
```

### Query Audit

| File | Method | Query Type | Safe |
|------|--------|------------|------|
| sqlite_repo.py | save_order | INSERT OR REPLACE | ✅ Parameterized |
| sqlite_repo.py | get_order | SELECT | ✅ Parameterized |
| sqlite_repo.py | save_debt | INSERT OR REPLACE | ✅ Parameterized |
| sqlite_repo.py | get_debt | SELECT | ✅ Parameterized |
| sqlite_repo.py | delete_debt | DELETE | ✅ Parameterized |
| sqlite_repo.py | save_payment | INSERT | ✅ Parameterized |

### Schema Safety

- Foreign key constraints enabled (`PRAGMA foreign_keys = ON`)
- Primary keys prevent duplicate entries
- Indexes for performance, not security

---

## Authentication & Authorization

### Current Model (MVP)

| Aspect | Implementation | Security Level |
|--------|---------------|----------------|
| User identity | Telegram username | **Weak** - can be changed |
| Authorization | None - all users equal | **Minimal** |
| Group isolation | Not implemented | **None** |

### Trust Assumptions

1. **Telegram username is identity** - Users are identified solely by username
2. **No verification of payments** - Self-reported (honor system)
3. **No admin roles** - Any user can create orders affecting others

### Recommendations for Production

```
Priority 1: Use Telegram user_id instead of username (immutable)
Priority 2: Add payment confirmation by creditor
Priority 3: Implement group isolation (chat_id scoping)
Priority 4: Add admin role for dispute resolution
```

---

## Data Integrity

### Transaction Safety

**Location:** `src/persistence/sqlite_repo.py` → `_transaction()`

```python
@contextmanager
def _transaction(self):
    conn = self._get_connection()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()  # Automatic rollback on error
        raise
    finally:
        conn.close()
```

### Debt Consistency

| Operation | Integrity Check |
|-----------|-----------------|
| Create debt | Accumulates with existing debt |
| Reduce debt | Cannot go below zero |
| Delete debt | Only when fully paid (amount = 0) |
| Payment | Atomic with debt reduction |

### Concurrent Access

- SQLite serializes writes automatically
- Tested with `ThreadPoolExecutor` (see `test_concurrent_access_safety`)
- No race conditions in debt updates

---

## Abuse Cases

### 1. Fake Order Creation

**Attack:** User creates order with inflated amount or fake participants.

**Current mitigation:** None - relies on social trust.

**Recommended mitigation:**
```
- Require order confirmation from all participants
- Allow order cancellation within time window
- Implement dispute mechanism
```

### 2. Payment Fraud

**Attack:** User claims payment without actually paying.

**Current mitigation:** None - honor system.

**Recommended mitigation:**
```
- Require creditor confirmation of payment receipt
- Integrate with payment systems (future)
- Add payment dispute mechanism
```

### 3. Username Spoofing

**Attack:** Change Telegram username to match another user.

**Current mitigation:** None.

**Recommended mitigation:**
```
- Use Telegram user_id (immutable) instead of username
- This is a CRITICAL fix for production
```

### 4. Denial of Service

**Attack:** Flood bot with messages.

**Current mitigation:** Telegram rate limits.

**Recommended mitigation:**
```
- Add per-user rate limiting
- Implement cooldown on order creation
- Add maximum participants per order
```

### 5. Large Amount Attack

**Attack:** Create order with maximum amount to confuse users.

**Current mitigation:** 1 billion ruble limit.

**Recommended mitigation:**
```
- Add confirmation for large amounts (>10,000)
- Group-specific limits configurable by admin
```

### 6. Negative Debt Manipulation

**Attack:** Try to create negative debts through edge cases.

**Current mitigation:** ✅ Fully implemented
- Amount must be positive
- Payment cannot exceed debt
- Overpayment rejected

---

## Known Limitations

### Security Limitations

| Limitation | Risk | Mitigation Path |
|------------|------|-----------------|
| Username-based identity | Impersonation | Use user_id |
| No payment confirmation | Fraud | Add creditor confirmation |
| No group isolation | Data leakage | Scope by chat_id |
| Honor system | False claims | Confirmation workflow |

### Technical Limitations

| Limitation | Impact | Mitigation Path |
|------------|--------|-----------------|
| SQLite single-writer | Scale limit | PostgreSQL for production |
| No backup mechanism | Data loss risk | Add backup/export |
| Plain text storage | Privacy | Encrypt sensitive data |

---

## Security Checklist

### Implemented ✅

- [x] Input validation for amounts (positive, bounded)
- [x] Input validation for participants (minimum 2)
- [x] Payment validation (positive, not exceeding debt)
- [x] SQL injection prevention (parameterized queries)
- [x] Transaction rollback on error
- [x] Concurrent access safety
- [x] Error messages don't leak internals

### Not Yet Implemented ⚠️

- [ ] User identity by user_id (not username)
- [ ] Payment confirmation by creditor
- [ ] Group isolation (chat_id scoping)
- [ ] Rate limiting
- [ ] Large amount confirmation
- [ ] Audit logging
- [ ] Data encryption at rest

### Recommended Before Production 🚨

1. **CRITICAL:** Switch from username to user_id
2. **HIGH:** Add payment confirmation flow
3. **HIGH:** Implement group isolation
4. **MEDIUM:** Add rate limiting
5. **MEDIUM:** Add audit logging

---

## Reporting Security Issues

If you discover a security vulnerability, please report it by:

1. **Do not** create a public GitHub issue
2. Contact the maintainers directly
3. Allow reasonable time for fix before disclosure

---

*Last updated: 2025-01-14*
*Review status: Initial security assessment complete*
