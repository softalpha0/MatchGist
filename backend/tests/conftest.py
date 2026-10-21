import pytest

from app.simulator.engine import generate_match


@pytest.fixture(scope="session")
def match42():
    return generate_match(42)
