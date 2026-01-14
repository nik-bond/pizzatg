"""
Integration tests for Telegram bot handlers.

Tests complete workflows: message -> handler -> service -> response.
Uses direct handler calls to simulate Telegram interactions.
"""
import pytest
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock
from aiogram.types import Message, User, Chat

from src.domain.services import OrderService, DebtService, PaymentService
from src.persistence.memory_repo import InMemoryRepository
from src.bot.handlers import create_router


# Consistent chat ID used across tests
CHAT_ID = 12345


@pytest.fixture
def repository():
    """Create fresh in-memory repository for each test."""
    return InMemoryRepository()


@pytest.fixture
def services(repository):
    """Create service instances with shared repository."""
    order_service = OrderService(repository)
    debt_service = DebtService(repository)
    payment_service = PaymentService(repository)
    return order_service, debt_service, payment_service


@pytest.fixture
def router(services):
    """Create router with test services."""
    order_service, debt_service, payment_service = services
    return create_router(order_service, debt_service, payment_service)


def create_message(text: str, username: str = "testuser") -> Message:
    """
    Create mock Message object for testing.
    
    Args:
        text: Message text content
        username: Username of the sender
        
    Returns:
        Mock Message object with answer() method
    """
    message = MagicMock(spec=Message)
    message.text = text
    message.from_user = User(
        id=12345,
        is_bot=False,
        first_name="Test",
        username=username
    )
    message.chat = Chat(id=CHAT_ID, type="private")
    
    # Track responses
    message.responses = []
    
    async def answer_mock(text, **kwargs):
        message.responses.append(text)
        return MagicMock()
    
    message.answer = AsyncMock(side_effect=answer_mock)
    
    return message


async def call_handler(router, handler_name: str, message: Message):
    """
    Call a specific handler by name from the router.
    
    Args:
        router: The router instance
        handler_name: Name of the handler function (e.g., "handle_start")
        message: The message to process
    """
    # Get message observers
    observers = router.observers["message"]
    
    # Find handlers that match
    for observer in observers.handlers:
        handler_func = observer.callback
        if hasattr(handler_func, "__name__") and handler_func.__name__ == handler_name:
            await handler_func(message)
            return
    
    raise ValueError(f"Handler {handler_name} not found")


@pytest.mark.asyncio
class TestOrderFlow:
    """Test order creation through bot handlers."""
    
    async def test_create_order_with_description(self, router, services):
        """Test complete order creation flow with description."""
        _, debt_service, _ = services
        
        # Simulate user sending order message
        # Note: payer (testuser) is automatically added to participants
        # So participants become: [testuser, ivan, petya, masha] = 4 people
        message = create_message("пицца 3000 @ivan @petya @masha", username="testuser")
        
        await call_handler(router, "handle_text", message)
        
        # Check response was sent
        assert len(message.responses) == 1
        response = message.responses[0]
        
        # Verify confirmation message format
        assert "✅" in response or "Заказ" in response
        assert "3000" in response
        assert "пицца" in response
        
        # Verify debts were created (3000 / 4 people = 750 each)
        ivan_debt = debt_service.get_debt("ivan", "testuser", message.chat.id)
        assert ivan_debt == Decimal("750")

        petya_debt = debt_service.get_debt("petya", "testuser", message.chat.id)
        assert petya_debt == Decimal("750")

        masha_debt = debt_service.get_debt("masha", "testuser", message.chat.id)
        assert masha_debt == Decimal("750")
    
    async def test_create_order_without_description(self, router, services):
        """Test order creation without description."""
        _, debt_service, _ = services
        
        # 1500 split between [testuser, ivan, petya] = 3 people
        message = create_message("1500 @ivan @petya", username="testuser")
        await call_handler(router, "handle_text", message)
        
        # Check confirmation sent
        assert len(message.responses) == 1
        response = message.responses[0]
        assert "1500" in response
        
        # Verify debts (1500 / 3 = 500 each)
        ivan_debt = debt_service.get_debt("ivan", "testuser", message.chat.id)
        assert ivan_debt == Decimal("500")
    
    async def test_order_with_explicit_payer(self, router, services):
        """Test order with payer: marker."""
        _, debt_service, _ = services
        
        message = create_message("пицца 3000 payer:@ivan @petya @masha", username="testuser")
        await call_handler(router, "handle_text", message)
        
        # Ivan is payer, so petya and masha owe ivan
        petya_debt = debt_service.get_debt("petya", "ivan", message.chat.id)
        assert petya_debt == Decimal("1000")

        masha_debt = debt_service.get_debt("masha", "ivan", message.chat.id)
        assert masha_debt == Decimal("1000")

        # Ivan doesn't owe himself
        ivan_debt = debt_service.get_debt("ivan", "ivan", message.chat.id)
        assert ivan_debt == Decimal("0")


@pytest.mark.asyncio
class TestPaymentFlow:
    """Test payment processing through bot handlers."""
    
    async def test_full_payment(self, router, services):
        """Test full debt payment."""
        order_service, debt_service, _ = services
        
        # Setup: create order first
        order = order_service.create_order(
            "пицца", Decimal("3000"), "ivan", ["ivan", "petya", "masha"], chat_id=CHAT_ID
        )
        debt_service.create_debts_from_order(order)
        
        # Petya pays full debt
        message = create_message("/paid @ivan 1000", username="petya")
        await call_handler(router, "handle_paid", message)
        
        # Check confirmation
        assert len(message.responses) == 1
        response = message.responses[0]
        assert "1000" in response
        assert "ivan" in response
        assert "0" in response  # Remaining debt is 0
        
        # Verify debt cleared
        remaining_debt = debt_service.get_debt("petya", "ivan", message.chat.id)
        assert remaining_debt == Decimal("0")
    
    async def test_partial_payment(self, router, services):
        """Test partial debt payment."""
        order_service, debt_service, _ = services
        
        # Setup: create order
        order = order_service.create_order(
            "пицца", Decimal("3000"), "ivan", ["ivan", "petya"], chat_id=CHAT_ID
        )
        debt_service.create_debts_from_order(order)
        
        # Petya pays 500 of 1500 debt
        message = create_message("/paid @ivan 500", username="petya")
        await call_handler(router, "handle_paid", message)
        
        # Check response shows remaining debt
        response = message.responses[0]
        assert "500" in response  # Payment amount
        assert "1000" in response  # Remaining debt
        
        # Verify debt reduced
        remaining_debt = debt_service.get_debt("petya", "ivan", message.chat.id)
        assert remaining_debt == Decimal("1000")


@pytest.mark.asyncio
class TestQueryCommands:
    """Test debt query commands."""
    
    async def test_debts_command_shows_consolidated(self, router, services):
        """Test /debts command shows net balance."""
        order_service, debt_service, _ = services
        
        # Setup: petya owes ivan 1000, ivan owes petya 300
        order1 = order_service.create_order(
            "пицца", Decimal("2000"), "ivan", ["ivan", "petya"], chat_id=CHAT_ID
        )
        debt_service.create_debts_from_order(order1)
        
        order2 = order_service.create_order(
            "кофе", Decimal("600"), "petya", ["petya", "ivan"], chat_id=CHAT_ID
        )
        debt_service.create_debts_from_order(order2)
        
        # Petya checks debts
        message = create_message("/debts", username="petya")
        await call_handler(router, "handle_debts", message)
        
        # Check response shows net debt (1000 - 300 = 700)
        assert len(message.responses) == 1
        response = message.responses[0]
        assert "700" in response
        assert "ivan" in response
    
    async def test_owed_command_shows_creditors(self, router, services):
        """Test /owed command shows who owes user."""
        order_service, debt_service, _ = services
        
        # Setup: petya and masha owe ivan
        order = order_service.create_order(
            "пицца", Decimal("3000"), "ivan", ["ivan", "petya", "masha"], chat_id=CHAT_ID
        )
        debt_service.create_debts_from_order(order)
        
        # Ivan checks who owes him
        message = create_message("/owed", username="ivan")
        await call_handler(router, "handle_owed", message)
        
        # Check response lists debtors
        response = message.responses[0]
        assert "petya" in response
        assert "masha" in response
        assert "1000" in response
    
    async def test_debts_command_no_debts(self, router, services):
        """Test /debts when user has no debts."""
        message = create_message("/debts", username="petya")
        await call_handler(router, "handle_debts", message)
        
        response = message.responses[0]
        assert "Долгов нет" in response or "нет" in response.lower()


@pytest.mark.asyncio
class TestCommandHandlers:
    """Test command handlers."""
    
    async def test_start_command(self, router):
        """Test /start command."""
        message = create_message("/start", username="testuser")
        await call_handler(router, "handle_start", message)
        
        # Check welcome message
        assert len(message.responses) == 1
        response = message.responses[0]
        assert "Привет" in response or "бот" in response.lower()
    
    async def test_help_command(self, router):
        """Test /help command."""
        message = create_message("/help", username="testuser")
        await call_handler(router, "handle_help", message)
        
        # Check help includes command list
        response = message.responses[0]
        assert "/debts" in response or "долги" in response
        assert "/paid" in response or "оплата" in response


@pytest.mark.asyncio
class TestErrorHandling:
    """Test error handling in bot handlers."""
    
    async def test_invalid_order_amount(self, router):
        """Test error on invalid order amount."""
        # Use zero amount which is validated by the domain service
        message = create_message("пицца 0 @ivan @petya", username="testuser")
        await call_handler(router, "handle_text", message)
        
        # Check error message
        response = message.responses[0]
        assert "❌" in response or "Ошибка" in response
        assert "положительной" in response or "недопустим" in response.lower()
    
    async def test_payment_exceeds_debt(self, router, services):
        """Test error when payment exceeds debt."""
        order_service, debt_service, _ = services
        
        # Setup: small debt
        order = order_service.create_order(
            "кофе", Decimal("200"), "ivan", ["ivan", "petya"], chat_id=CHAT_ID
        )
        debt_service.create_debts_from_order(order)
        
        # Try to pay more than owed
        message = create_message("/paid @ivan 500", username="petya")
        await call_handler(router, "handle_paid", message)
        
        # Check error message
        response = message.responses[0]
        assert "❌" in response or "Ошибка" in response
        assert "превышает" in response or "больше" in response
    
    async def test_payment_no_debt(self, router):
        """Test error when trying to pay non-existent debt."""
        message = create_message("/paid @ivan 100", username="petya")
        await call_handler(router, "handle_paid", message)
        
        # Check error message
        response = message.responses[0]
        assert "❌" in response or "Ошибка" in response
        assert "не найден" in response or "нет долга" in response
    
    async def test_order_with_no_username(self, router):
        """Test error when user has no username."""
        message = create_message("пицца 1000 @ivan @petya", username=None)
        await call_handler(router, "handle_text", message)
        
        # Check error about missing username
        response = message.responses[0]
        assert "username" in response.lower()
