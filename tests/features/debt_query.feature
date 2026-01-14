Feature: Debt Query
  As a user
  I want to see current debt status
  So that I know who owes whom

  # MVP: basic debt queries

  Scenario: Query my debts
    Given order "пицца" for 3000 rubles is created with payer "ivan" and participants "ivan", "petya", "masha"
    And order "суши" for 2000 rubles is created with payer "anna" and participants "anna", "petya"
    When "petya" queries their debts
    Then result contains debt of 1000 rubles to "ivan"
    And result contains debt of 1000 rubles to "anna"
    And total debt is 2000 rubles

  Scenario: Query who owes me
    Given order "пицца" for 3000 rubles is created with payer "ivan" and participants "ivan", "petya", "masha"
    When "ivan" queries who owes them
    Then result contains debt from "petya" of 1000 rubles
    And result contains debt from "masha" of 1000 rubles
    And total owed is 2000 rubles

  Scenario: No debts
    Given user "newuser" exists
    And "newuser" has no orders
    When "newuser" queries their debts
    Then result is empty
    And message is "Долгов нет"

  Scenario: Nobody owes me
    Given user "newuser" exists
    And "newuser" has no orders
    When "newuser" queries who owes them
    Then result is empty
    And message is "Вам никто не должен"

  Scenario: Debts after partial payment
    Given order "пицца" for 2000 rubles is created with payer "ivan" and participants "ivan", "petya"
    And "petya" paid "ivan" 500 rubles
    When "petya" queries their debts
    Then result contains debt of 500 rubles to "ivan"

  Scenario: Debts fully paid
    Given order "пицца" for 2000 rubles is created with payer "ivan" and participants "ivan", "petya"
    And "petya" paid "ivan" 1000 rubles
    When "petya" queries their debts
    Then result is empty
    And message is "Долгов нет"

  Scenario: Query all group debts
    Given order "пицца" for 3000 rubles is created with payer "ivan" and participants "ivan", "petya", "masha"
    When all group debts are queried
    Then result contains group debt from "petya" to "ivan" of 1000 rubles
    And result contains group debt from "masha" to "ivan" of 1000 rubles
