Feature: Payment Processing
  As a debtor
  I want to record debt payments
  So that my debt is reduced

  # MVP: simple payments reduce debt

  Background:
    Given order "пицца" for 3000 rubles is created with payer "ivan" and participants "ivan", "petya", "masha"
    # petya owes ivan 1000, masha owes ivan 1000

  Scenario: Full debt payment
    Given "petya" owes "ivan" 1000 rubles
    When "petya" pays "ivan" 1000 rubles
    Then payment is recorded successfully
    And "petya" owes "ivan" 0 rubles

  Scenario: Partial debt payment
    Given "petya" owes "ivan" 1000 rubles
    When "petya" pays "ivan" 400 rubles
    Then payment is recorded successfully
    And "petya" owes "ivan" 600 rubles

  Scenario: Multiple partial payments
    Given "petya" owes "ivan" 1000 rubles
    When "petya" pays "ivan" 300 rubles
    And "petya" pays "ivan" 300 rubles
    Then "petya" owes "ivan" 400 rubles

  Scenario: Error on overpayment
    Given "petya" owes "ivan" 1000 rubles
    When "petya" tries to pay "ivan" 1500 rubles
    Then error "Сумма платежа превышает долг" occurs
    And debt of "petya" to "ivan" remains 1000 rubles

  Scenario: Error on negative payment
    Given "petya" owes "ivan" 1000 rubles
    When "petya" tries to pay "ivan" -100 rubles
    Then error "Сумма платежа должна быть положительной" occurs
    And debt of "petya" to "ivan" remains 1000 rubles

  Scenario: Error on zero payment
    Given "petya" owes "ivan" 1000 rubles
    When "petya" tries to pay "ivan" 0 rubles
    Then error "Сумма платежа должна быть положительной" occurs
    And debt of "petya" to "ivan" remains 1000 rubles

  Scenario: Error on non-existent debt
    Given "masha" does not owe "petya" anything
    When "masha" tries to pay "petya" 500 rubles
    Then error "Долг не найден" occurs

  Scenario: Payment does not affect other debts
    Given "petya" owes "ivan" 1000 rubles
    And "masha" owes "ivan" 1000 rubles
    When "petya" pays "ivan" 1000 rubles
    Then "petya" owes "ivan" 0 rubles
    And "masha" owes "ivan" 1000 rubles
