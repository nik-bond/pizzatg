Feature: Order Creation
  As a participant in a shared order
  I want to record an expense with amount and participants
  So that the system can calculate who owes whom

  # MVP: basic order creation with equal split

  Scenario: Create order with three participants
    Given user "ivan" is the payer
    When order "пицца" is created for 3000 rubles
    And participants are "ivan", "petya", "masha"
    Then order is successfully created
    And per person amount is 1000.00 rubles

  Scenario: Create order with two participants
    Given user "anna" is the payer
    When order "суши" is created for 2000 rubles
    And participants are "anna", "boris"
    Then order is successfully created
    And per person amount is 1000.00 rubles

  Scenario: Create order with indivisible amount
    Given user "ivan" is the payer
    When order "кофе" is created for 100 rubles
    And participants are "ivan", "petya", "masha"
    Then order is successfully created
    And per person amount is 33.33 rubles

  Scenario Outline: Error on invalid amount
    Given user "ivan" is the payer
    When order "еда" is created for <amount> rubles
    And participants are "ivan", "petya"
    Then error "<message>" occurs
    And order is not created

    Examples:
      | amount | message                           |
      | 0      | Сумма должна быть положительной   |
      | -100   | Сумма должна быть положительной   |

  Scenario: Error on amount too large
    Given user "ivan" is the payer
    When order "яхта" is created for 1000000001 rubles
    And participants are "ivan", "petya"
    Then error "Сумма превышает допустимый лимит" occurs
    And order is not created

  Scenario: Error on empty participants
    Given user "ivan" is the payer
    When order "пицца" is created for 1000 rubles
    And participants list is empty
    Then error "Требуется минимум два участника" occurs
    And order is not created

  Scenario: Error on single participant
    Given user "ivan" is the payer
    When order "пицца" is created for 1000 rubles
    And participants are "ivan"
    Then error "Требуется минимум два участника" occurs
    And order is not created

  Scenario: Payer automatically included in participants
    Given user "ivan" is the payer
    When order "пицца" is created for 2000 rubles
    And participants are "petya", "masha"
    Then order is successfully created
    And "ivan" is included in participants
    And per person amount is 666.67 rubles
