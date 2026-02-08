from __future__ import annotations

import argparse
import asyncio
import getpass
from pathlib import Path
from typing import Callable

from telethon import TelegramClient
from telethon.errors import SessionPasswordNeededError
from telethon.sessions import StringSession

from app.settings import Settings, get_settings
from shared.telegram.errors import TelegramAuthorizationError, TelegramConfigError
from shared.telegram.telethon_client import build_telethon_client_kwargs


def _require_bootstrap_settings(settings: Settings) -> None:
    if not settings.TELEGRAM_ENABLED:
        raise TelegramConfigError("Telegram integration is disabled")
    if settings.TELEGRAM_API_ID is None:
        raise TelegramConfigError("TELEGRAM_API_ID is not configured")
    if not settings.TELEGRAM_API_HASH:
        raise TelegramConfigError("TELEGRAM_API_HASH is not configured")


def _resolve_output_path(settings: Settings, arg_path: str | None) -> Path | None:
    path_value = arg_path or settings.TELEGRAM_SESSION_STRING_PATH
    if not path_value:
        return None
    return Path(path_value).expanduser()


def _write_secret(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value, encoding="utf-8")
    try:
        path.chmod(0o600)
    except OSError:
        # Some filesystems/OS combinations may not support chmod semantics.
        pass


async def bootstrap_telethon_session(
    *,
    settings: Settings,
    phone: str | None = None,
    code: str | None = None,
    password: str | None = None,
    output_path: Path | None = None,
    read_phone: Callable[[str], str] = input,
    read_code: Callable[[str], str] = getpass.getpass,
    read_password: Callable[[str], str] = getpass.getpass,
    print_fn: Callable[[str], None] = print,
) -> str:
    _require_bootstrap_settings(settings)

    client = TelegramClient(
        StringSession(),
        settings.TELEGRAM_API_ID,
        settings.TELEGRAM_API_HASH,
        **build_telethon_client_kwargs(settings),
    )
    await client.connect()
    try:
        if not await client.is_user_authorized():
            phone_value = (phone or read_phone("Telegram phone number (+...): ")).strip()
            if not phone_value:
                raise TelegramConfigError("Phone number is required for Telethon bootstrap")

            await client.send_code_request(phone_value)

            code_value = (code or read_code("Telegram login code: ")).strip()
            if not code_value:
                raise TelegramConfigError("Telegram login code is required for Telethon bootstrap")

            try:
                await client.sign_in(phone=phone_value, code=code_value)
            except SessionPasswordNeededError:
                password_value = (password or read_password("Telegram 2FA password: ")).strip()
                if not password_value:
                    raise TelegramConfigError("Telegram 2FA password is required for Telethon bootstrap")
                await client.sign_in(password=password_value)

        if not await client.is_user_authorized():
            raise TelegramAuthorizationError("Telethon authorization failed")

        session_string = StringSession.save(client.session)
        if not session_string:
            raise TelegramAuthorizationError("Telethon authorization succeeded but session string is empty")

        if output_path is not None:
            _write_secret(output_path, session_string)
            print_fn(f"Telethon session string saved to {output_path}")

        return session_string
    finally:
        await client.disconnect()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="telethon-bootstrap",
        description="Authorize Telethon service account and persist a reusable session string.",
    )
    parser.add_argument("--phone", help="Telegram phone number in +<country><number> format.")
    parser.add_argument("--code", help="Telegram login code (use only in trusted environments).")
    parser.add_argument("--password", help="Telegram 2FA password (use only in trusted environments).")
    parser.add_argument(
        "--session-string-path",
        help=(
            "Path where the generated Telethon session string will be written. "
            "Defaults to TELEGRAM_SESSION_STRING_PATH if configured."
        ),
    )
    parser.add_argument(
        "--print-session-string",
        action="store_true",
        help="Print the generated session string to stdout for manual secret manager updates.",
    )
    args = parser.parse_args(argv)

    settings = get_settings()
    output_path = _resolve_output_path(settings, args.session_string_path)

    if output_path is None and not args.print_session_string:
        print(
            "ERROR: configure TELEGRAM_SESSION_STRING_PATH (or --session-string-path) "
            "or pass --print-session-string."
        )
        return 1

    try:
        session_string = asyncio.run(
            bootstrap_telethon_session(
                settings=settings,
                phone=args.phone,
                code=args.code,
                password=args.password,
                output_path=output_path,
            )
        )
    except (TelegramConfigError, TelegramAuthorizationError) as exc:
        print(f"ERROR: {exc}")
        return 1
    except KeyboardInterrupt:
        print("ERROR: Telethon bootstrap interrupted")
        return 1

    if args.print_session_string:
        print(session_string)

    if output_path is None and not args.print_session_string:
        print("Telethon bootstrap completed.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
