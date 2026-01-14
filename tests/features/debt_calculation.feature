Feature: Debt Calculation
  As a expense tracking system
  I need to correctly calculate who owes whom
  So that participants know their obligations

  # MVP: debts are created from participants to payer

  Scenario: Debts created after order
    Given user "ivan" is the payer
    And order "пицца" for 3000 rubles is created with participants "ivan", "petya", "masha"
    Then "petya" owes "ivan" 1000 rubles
    And "masha" owes "ivan" 1000 rubles
    And "ivan" owes nothing

  Scenario: Payer does not owe themselves
    Given user "ivan" is the payer
    And order "пицца" for 2000 rubles is created with participants "ivan", "petya"
    Then "ivan" has no debt to "ivan"
    And "petya" owes "ivan" 1000 rubles

  Scenario: Debts accumulate from multiple orders
    Given user "ivan" is the payer
    And order "пицца" for 2000 rubles is created with participants "ivan", "petya"
    And order "напитки" for 1000 rubles is created with participants "ivan", "petya"
    Then "petya" owes "ivan" 1500 rubles

  Scenario: Mutual debts tracked separately
    Given order "пицца" for 2000 rubles is created with payer "ivan" and participants "ivan", "petya"
    And order "суши" for 2000 rubles is created with payer "petya" and participants "ivan", "petya"
    Then "petya" owes "ivan" 1000 rubles
    And "ivan" owes "petya" 1000 rubles

  Scenario: Net balance equals zero
    Given order "пицца" for 2000 rubles is created with payer "ivan" and participants "ivan", "petya"
    And order "суши" for 2000 rubles is created with payer "petya" and participants "ivan", "petya"
    When net balance is requested between "ivan" and "petya"
    Then net balance is 0 rubles

  Scenario: Net balance with unequal debts
    Given order "пицца" for 3000 rubles is created with payer "ivan" and participants "ivan", "petya"
    And order "суши" for 1000 rubles is created with payer "petya" and participants "ivan", "petya"
    When net balance is requested between "ivan" and "petya"
    Then "petya" owes "ivan" net 1000 rubles

  Scenario: Consolidated debts show net balance with breakdown
    Given order "десерт" for 800 rubles is created with payer "ivan" and participants "ivan", "petya"
    And order "кофе" for 400 rubles is created with payer "petya" and participants "ivan", "petya"
    When consolidated debts are requested for "petya"
    Then consolidated result shows "ivan" with net "i_owe" of 200 rubles
    And breakdown shows I owe 400 for "десерт"
    And breakdown shows they owe 200 for "кофе"
