from fastapi import APIRouter

from app.settings import get_settings

router = APIRouter()


@router.get("/health")
def health() -> dict:
    settings = get_settings()

    def _build_check(required: dict[str, object]) -> dict[str, object]:
        missing = [name for name, value in required.items() if value in (None, "")]
        return {"ready": len(missing) == 0, "missing": missing}

    backend_check = _build_check(
        {
            "DATABASE_URL": settings.DATABASE_URL,
        }
    )

    telegram_required = {}
    if settings.TELEGRAM_ENABLED:
        telegram_required = {
            "TELEGRAM_BOT_TOKEN": settings.TELEGRAM_BOT_TOKEN,
            "TELEGRAM_API_ID": settings.TELEGRAM_API_ID,
            "TELEGRAM_API_HASH": settings.TELEGRAM_API_HASH,
        }
    telegram_check = _build_check(telegram_required)

    ton_required = {}
    if settings.TON_ENABLED:
        ton_required = {
            "TON_HOT_WALLET_MNEMONIC": settings.TON_HOT_WALLET_MNEMONIC,
            "TONCENTER_API": settings.TONCENTER_API,
            "TON_FEE_PERCENT": settings.TON_FEE_PERCENT,
            "TONCONNECT_MANIFEST_URL": settings.TONCONNECT_MANIFEST_URL,
        }
    ton_check = _build_check(ton_required)

    worker_required = {
        "CELERY_BROKER_URL": settings.CELERY_BROKER_URL,
        "CELERY_RESULT_BACKEND": settings.CELERY_RESULT_BACKEND,
    }
    workers_check = _build_check(worker_required)

    checks = {
        "backend": backend_check,
        "ton": ton_check,
        "telegram": telegram_check,
        "workers": workers_check,
    }
    status = "ok" if all(check["ready"] for check in checks.values()) else "degraded"
    return {"status": status, "checks": checks}
