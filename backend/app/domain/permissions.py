from __future__ import annotations


class PermissionDenied(RuntimeError):
    def __init__(self, *, context: str, missing_permissions: list[str]) -> None:
        self.context = context
        self.missing_permissions = missing_permissions
        message = (
            f"Permission denied for {context}: missing permissions "
            f"{', '.join(missing_permissions)}"
        )
        super().__init__(message)


class ChannelAccessDenied(RuntimeError):
    def __init__(
        self,
        *,
        channel_id: int,
        telegram_user_id: int,
        missing_permissions: list[str],
    ) -> None:
        self.channel_id = channel_id
        self.telegram_user_id = telegram_user_id
        self.missing_permissions = missing_permissions
        message = (
            "Channel access denied for "
            f"{telegram_user_id} on channel {channel_id}: missing permissions "
            f"{', '.join(missing_permissions)}"
        )
        super().__init__(message)


def ensure_permissions(result, *, context: str) -> None:
    if not getattr(result, "ok", False):
        missing = list(getattr(result, "missing_permissions", []))
        raise PermissionDenied(context=context, missing_permissions=missing)
