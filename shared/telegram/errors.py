class TelegramConfigError(RuntimeError):
    """Raised when Telegram integration is disabled or misconfigured."""


class TelegramApiError(RuntimeError):
    """Raised when a Telegram API request fails."""


class TelegramAuthorizationError(RuntimeError):
    """Raised when a Telegram client is connected but not authorized."""
