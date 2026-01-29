class TelegramConfigError(RuntimeError):
    """Raised when Telegram integration is disabled or misconfigured."""


class TelegramApiError(RuntimeError):
    """Raised when a Telegram API request fails."""
