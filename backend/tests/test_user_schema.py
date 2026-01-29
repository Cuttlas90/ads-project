from shared.db.base import SQLModel


def test_users_table_schema() -> None:
    table = SQLModel.metadata.tables["users"]

    assert "telegram_user_id" in table.c
    assert "last_login_at" in table.c

    telegram_col = table.c.telegram_user_id
    assert telegram_col.unique is True
    assert telegram_col.index is True or any(telegram_col in index.columns for index in table.indexes)
