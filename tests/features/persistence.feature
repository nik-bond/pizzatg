Feature: Data Persistence
  As a system administrator
  I want data to persist across restarts
  So that users don't lose their debt history

  # Integration tests for SQLite persistence

  Scenario: Orders persist after restart
    Given a fresh SQLite database
    And order "пицца" for 3000 rubles is created with payer "ivan" and participants "ivan", "petya"
    When the repository is reopened
    Then order "пицца" still exists
    And order has amount 3000 rubles

  Scenario: Debts persist after restart
    Given a fresh SQLite database
    And order "пицца" for 2000 rubles is created with payer "ivan" and participants "ivan", "petya"
    And debts are generated from the order
    When the repository is reopened
    Then "petya" still owes "ivan" 1000 rubles

  Scenario: Payments persist after restart
    Given a fresh SQLite database
    And order "пицца" for 2000 rubles is created with payer "ivan" and participants "ivan", "petya"
    And debts are generated from the order
    And "petya" pays "ivan" 500 rubles
    When the repository is reopened
    Then "petya" owes "ivan" 500 rubles

  Scenario: Multiple orders accumulate correctly
    Given a fresh SQLite database
    And order "пицца" for 2000 rubles is created with payer "ivan" and participants "ivan", "petya"
    And debts are generated from the order
    And order "суши" for 1000 rubles is created with payer "ivan" and participants "ivan", "petya"
    And debts are generated from the order
    When the repository is reopened
    Then "petya" still owes "ivan" 1500 rubles

  Scenario: Fully paid debts are removed
    Given a fresh SQLite database
    And order "пицца" for 2000 rubles is created with payer "ivan" and participants "ivan", "petya"
    And debts are generated from the order
    And "petya" pays "ivan" 1000 rubles
    When the repository is reopened
    Then "petya" owes "ivan" 0 rubles

  Scenario: Concurrent access safety
    Given a fresh SQLite database
    And order "пицца" for 3000 rubles is created with payer "ivan" and participants "ivan", "petya", "masha"
    And debts are generated from the order
    When "petya" and "masha" pay simultaneously
    Then both payments are recorded correctly
    And no data corruption occurs
