Feature: Bot integration workflows
    As a Telegram bot user
    I want commands and free-text orders to work end-to-end
    So that I can track shared expenses via chat messages

    Background:
        Given a router with in-memory services
        And chat id 12345

    Scenario: Create order with description
        When user "testuser" sends message "пицца 3000 @ivan @petya @masha"
        Then exactly 1 response is sent
        And response contains one of "✅|Заказ"
        And response contains "3000"
        And response contains "пицца"
        And debt from "ivan" to "testuser" is 750 rubles
        And debt from "petya" to "testuser" is 750 rubles
        And debt from "masha" to "testuser" is 750 rubles

    Scenario: Create order without description
        When user "testuser" sends message "1500 @ivan @petya"
        Then exactly 1 response is sent
        And response contains "1500"
        And debt from "ivan" to "testuser" is 500 rubles

    Scenario: Create order with explicit payer
        When user "testuser" sends message "пицца 3000 payer:@ivan @petya @masha"
        Then debt from "petya" to "ivan" is 1000 rubles
        And debt from "masha" to "ivan" is 1000 rubles
        And debt from "ivan" to "ivan" is 0 rubles

    Scenario: Full debt payment via /paid
        Given an order "пицца" for 3000 rubles paid by "ivan" with participants "ivan,petya,masha"
        When user "petya" sends message "/paid @ivan 1000"
        Then exactly 1 response is sent
        And response contains "1000"
        And response contains "ivan"
        And response contains "0"
        And debt from "petya" to "ivan" is 0 rubles

    Scenario: Partial debt payment via /paid
        Given an order "пицца" for 3000 rubles paid by "ivan" with participants "ivan,petya"
        When user "petya" sends message "/paid @ivan 500"
        Then response contains "500"
        And response contains "1000"
        And debt from "petya" to "ivan" is 1000 rubles

    Scenario: /debts shows consolidated net balance
        Given an order "пицца" for 2000 rubles paid by "ivan" with participants "ivan,petya"
        And an order "кофе" for 600 rubles paid by "petya" with participants "petya,ivan"
        When user "petya" sends message "/debts"
        Then exactly 1 response is sent
        And response contains "700"
        And response contains "ivan"

    Scenario: /owed shows who owes the user
        Given an order "пицца" for 3000 rubles paid by "ivan" with participants "ivan,petya,masha"
        When user "ivan" sends message "/owed"
        Then response contains "petya"
        And response contains "masha"
        And response contains "1000"

    Scenario: /debts shows empty state when no debts
        When user "petya" sends message "/debts"
        Then response contains one of "Долгов нет|Нет долгов|нет"

    Scenario: /start command
        When user "testuser" sends message "/start"
        Then exactly 1 response is sent
        And response contains one of "Привет|бот"

    Scenario: /help command
        When user "testuser" sends message "/help"
        Then response contains one of "/debts|долги"
        And response contains one of "/paid|оплата"

    Scenario: Invalid order amount returns error
        When user "testuser" sends message "пицца 0 @ivan @petya"
        Then response contains one of "❌|Ошибка"
        And response contains one of "положительной|недопустим"

    Scenario: Payment exceeding debt returns error
        Given an order "кофе" for 200 rubles paid by "ivan" with participants "ivan,petya"
        When user "petya" sends message "/paid @ivan 500"
        Then response contains one of "❌|Ошибка"
        And response contains one of "превышает|больше"

    Scenario: Paying non-existent debt returns error
        When user "petya" sends message "/paid @ivan 100"
        Then response contains one of "❌|Ошибка"
        And response contains one of "не найден|нет долга"

    Scenario: Order fails if user has no username
        When user without username sends message "пицца 1000 @ivan @petya"
        Then response contains "username"
