import pytest

from app.db.session import engine


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


@pytest.fixture(autouse=True)
async def dispose_engine_after_test():
    yield
    await engine.dispose()
