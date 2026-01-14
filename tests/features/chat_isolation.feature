Feature: Chat isolation
    As a bot user
    I want each Telegram group to have isolated data
    So that debts from different groups don't mix

    Background:
        Given a fresh repository
        And the order service
        And the debt service

    Scenario: Orders in different chats are isolated
        When user "alice" creates order "Lunch" for 300 rubles with participants "alice,bob" in chat 100
        And user "alice" creates order "Dinner" for 600 rubles with participants "alice,charlie" in chat 200
        Then there should be 1 order in chat 100
        And there should be 1 order in chat 200
        And the last order in chat 100 has description "Lunch"
        And the last order in chat 200 has description "Dinner"

    Scenario: Debts in different chats are isolated
        When user "alice" creates order "Lunch" for 300 rubles with participants "alice,bob" in chat 100
        And user "alice" creates order "Dinner" for 600 rubles with participants "alice,charlie" in chat 200
        Then user "bob" owes 150 rubles in chat 100
        And user "bob" owes 0 rubles in chat 200
        And user "charlie" owes 0 rubles in chat 100
        And user "charlie" owes 300 rubles in chat 200

    Scenario: Payments in different chats are isolated
        Given user "alice" creates order "Lunch" for 300 rubles with participants "alice,bob" in chat 100
        And user "alice" creates order "Dinner" for 600 rubles with participants "alice,charlie" in chat 200
        When user "bob" pays "alice" 150 rubles in chat 100
        Then user "bob" owes 0 rubles in chat 100
        And user "charlie" owes 300 rubles in chat 200

    Scenario: Consolidated debts respect chat boundaries
        Given user "alice" creates order "Pizza" for 600 rubles with participants "alice,bob,charlie" in chat 100
        And user "bob" creates order "Coffee" for 300 rubles with participants "alice,bob" in chat 100
        And user "alice" creates order "Dinner" for 900 rubles with participants "alice,bob" in chat 200
        Then user "bob" has net debt 50 rubles to "alice" in chat 100
        And user "bob" has net debt 450 rubles to "alice" in chat 200

    Scenario: Query all debts respects chat isolation
        Given user "alice" creates order "Pizza" for 600 rubles with participants "alice,bob,charlie" in chat 100
        And user "alice" creates order "Dinner" for 600 rubles with participants "alice,bob" in chat 200
        When querying all debts in chat 100
        Then there are 2 debt records
        When querying all debts in chat 200
        Then there are 1 debt records
