Feature: Telegram Bot Commands
  As a Telegram user
  I want to interact with the debt tracker via bot commands
  So that I can manage shared expenses in group chats

  # Bot command parsing and response formatting tests

  Scenario: Parse order command with description
    Given message text "пицца 3000 @ivan @petya @masha"
    When the message is parsed as order command
    Then parsed description is "пицца"
    And parsed amount is 3000
    And parsed participants are "ivan", "petya", "masha"

  Scenario: Parse order command without description
    Given message text "1500 @ivan @petya"
    When the message is parsed as order command
    Then parsed description is empty
    And parsed amount is 1500
    And parsed participants are "ivan", "petya"

  Scenario: Parse order with explicit payer using payer: marker
    Given message text "пицца 1000 payer:@ivan @petya @masha"
    When the message is parsed as order command
    Then parsed description is "пицца"
    And parsed amount is 1000
    And parsed payer is "ivan"
    And parsed participants are "petya", "masha"

  Scenario: Parse order with explicit payer without space
    Given message text "суши 500 payer:@anna @boris"
    When the message is parsed as order command
    Then parsed payer is "anna"
    And parsed participants are "boris"

  Scenario: Parse order without payer: uses default payer
    Given message text "кофе 300 @ivan @petya"
    When the message is parsed as order command
    Then parsed payer is not specified
    And parsed participants are "ivan", "petya"

  Scenario: Parse payment command
    Given message text "/paid @ivan 1000"
    When the message is parsed as payment command
    Then parsed creditor is "ivan"
    And parsed payment amount is 1000

  Scenario: Parse payment command with username variations
    Given message text "/paid ivan 500"
    When the message is parsed as payment command
    Then parsed creditor is "ivan"
    And parsed payment amount is 500

  Scenario: Format debt list response
    Given user has debt of 1000 to "ivan"
    And user has debt of 500 to "anna"
    When debt list is formatted
    Then response contains "ivan: 1000"
    And response contains "anna: 500"
    And response contains "Итого: 1500"

  Scenario: Format empty debt response
    Given user has no debts
    When debt list is formatted
    Then response is "Долгов нет"

  Scenario: Format order confirmation
    Given order "пицца" for 3000 rubles with 3 participants
    When order confirmation is formatted
    Then response contains "пицца"
    And response contains "3000"
    And response contains "1000" as per person amount

  Scenario: Format payment confirmation
    Given payment of 500 rubles to "ivan"
    And remaining debt is 500 rubles
    When payment confirmation is formatted
    Then response contains "Оплачено: 500"
    And response contains "Остаток: 500"

  Scenario: Format error message for invalid amount
    Given validation error "Сумма должна быть положительной"
    When error is formatted
    Then response contains "Ошибка"
    And response contains "Сумма должна быть положительной"

  Scenario: Handle /start command
    When user sends "/start" command
    Then bot responds with welcome message
    And response contains usage instructions

  Scenario: Handle /help command
    When user sends "/help" command
    Then bot responds with command list
    And response contains "/debts"
    And response contains "/paid"

  Scenario: Handle /debts command
    Given user "petya" has debt of 1000 to "ivan"
    When "petya" sends "/debts" command
    Then bot responds with debt list
    And response contains "ivan: 1000"

  Scenario: Handle /owed command
    Given "petya" owes "ivan" 1000 rubles
    And "masha" owes "ivan" 500 rubles
    When "ivan" sends "/owed" command
    Then bot responds with creditor list
    And response contains "petya: 1000"
    And response contains "masha: 500"
