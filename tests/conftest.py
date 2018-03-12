import tempfile
from pathlib import Path

import pytest


@pytest.fixture
def tempdir():
    with tempfile.TemporaryDirectory() as datadir:
        yield Path(datadir)
