from __future__ import annotations

import logging
import time

from app.bot_api import BotApiService
from app.deal_messaging import handle_update
from app.settings import get_settings
from app.db import SessionLocal


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    settings = get_settings()
    bot_api = BotApiService(settings)

    last_update_id: int | None = None

    while True:
        try:
            response = bot_api.get_updates(offset=last_update_id, timeout=30)
        except Exception:
            logging.exception("Failed to fetch updates")
            time.sleep(3)
            continue

        if not isinstance(response, dict) or not response.get("ok"):
            time.sleep(1)
            continue

        updates = response.get("result") or []
        for update in updates:
            update_id = update.get("update_id")
            if update_id is None:
                continue
            if last_update_id is None or update_id >= last_update_id:
                last_update_id = update_id + 1
            with SessionLocal() as session:
                handle_update(update=update, db=session, bot_api=bot_api, settings=settings)

        time.sleep(0.2)


if __name__ == "__main__":
    main()
