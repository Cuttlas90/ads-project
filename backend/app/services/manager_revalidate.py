from __future__ import annotations

from app.domain.permissions import ChannelAccessDenied
from app.telegram.permissions import check_user_permissions
from shared.telegram import TelegramClientService


async def revalidate_channel_access(
    *,
    telegram_client: TelegramClientService,
    channel,
    telegram_user_id: int,
    required_rights: set[str],
) -> None:
    channel_ref = channel.telegram_channel_id or channel.username or channel.id

    await telegram_client.connect()
    try:
        client = telegram_client._get_client()
        result = await check_user_permissions(
            client,
            channel_ref,
            telegram_user_id=telegram_user_id,
            required_rights=required_rights,
        )
    finally:
        await telegram_client.disconnect()

    if not result.ok:
        raise ChannelAccessDenied(
            channel_id=channel.id,
            telegram_user_id=telegram_user_id,
            missing_permissions=list(result.missing_permissions),
        )
