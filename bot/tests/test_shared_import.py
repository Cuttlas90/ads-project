from shared.db.models.users import User
from shared.db.session import get_db


def test_bot_can_import_shared_db() -> None:
    assert User.__tablename__ == "users"
    assert callable(get_db)
