from __future__ import annotations


class ChannelNotFound(RuntimeError):
    def __init__(self, channel_id: int) -> None:
        super().__init__(f"Channel {channel_id} not found")
        self.channel_id = channel_id


class ChannelAccessDenied(RuntimeError):
    def __init__(self, channel_id: int, user_id: int | None) -> None:
        super().__init__(f"User {user_id} is not authorized to verify channel {channel_id}")
        self.channel_id = channel_id
        self.user_id = user_id


class ChannelBotPermissionDenied(RuntimeError):
    def __init__(self, channel_id: int, missing_permissions: list[str]) -> None:
        super().__init__(
            f"Bot lacks required permissions for channel {channel_id}: {', '.join(missing_permissions)}"
        )
        self.channel_id = channel_id
        self.missing_permissions = missing_permissions


class ChannelVerificationError(RuntimeError):
    def __init__(self, message: str, *, channel_id: int | None = None) -> None:
        super().__init__(message)
        self.channel_id = channel_id
