import os
import pytest
import aiosqlite
from database import init_db, get_db, create_or_get_user, get_user, update_user_balance, get_global_rank, get_top_richest

@pytest.fixture(autouse=True)
def cleanup_dbs():
    # Remove any possible leftover test databases
    for db_file in ["test_bot_database.db", "test_bot_database_users.db"]:
        if os.path.exists(db_file):
            try:
                os.remove(db_file)
            except Exception:
                pass
    yield
    for db_file in ["test_bot_database.db", "test_bot_database_users.db"]:
        if os.path.exists(db_file):
            try:
                os.remove(db_file)
            except Exception:
                pass

@pytest.mark.asyncio
async def test_database_initialization(monkeypatch):
    monkeypatch.setenv("DATABASE_PATH", "test_bot_database.db")
    await init_db()

    async with get_db() as db:
        # Verify users table existence and pre-populated waifus
        async with db.execute("SELECT COUNT(*) as cnt FROM waifus") as cursor:
            row = await cursor.fetchone()
            assert row["cnt"] >= 10

@pytest.mark.asyncio
async def test_user_creation_and_balance_ops(monkeypatch):
    monkeypatch.setenv("DATABASE_PATH", "test_bot_database_users.db")
    await init_db()

    # Test creation
    user = await create_or_get_user(112233, "tester_joe", "Joe")
    assert user["id"] == 112233
    assert user["username"] == "tester_joe"
    assert user["coins"] == 1000

    # Update balance
    await update_user_balance(112233, coins_delta=500, gems_delta=5, xp_delta=100)
    user_updated = await get_user(112233)
    assert user_updated["coins"] == 1500
    assert user_updated["gems"] == 15
    assert user_updated["xp"] == 100

    # Test Ranking
    await create_or_get_user(445566, "tester_rich", "Richie")
    await update_user_balance(445566, coins_delta=10000) # Give 10000 additional coins

    rank_rich = await get_global_rank(445566)
    rank_joe = await get_global_rank(112233)

    assert rank_rich < rank_joe

    # Test top richest limit
    top_richest = await get_top_richest(5)
    assert len(top_richest) >= 2
    assert top_richest[0]["id"] == 445566

    # Clean up
    if os.path.exists("test_bot_database_users.db"):
        os.remove("test_bot_database_users.db")
