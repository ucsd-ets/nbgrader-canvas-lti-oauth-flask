import os
import tempfile

import pytest

import nbgrader_to_canvas


@pytest.fixture
def client():
    with nbgrader_to_canvas.app.test_client() as client:
        yield client

