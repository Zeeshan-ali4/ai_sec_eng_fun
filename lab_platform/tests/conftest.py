from unittest.mock import Mock
import pytest
from lab_platform.app import create_app


@pytest.fixture
def model():
    client = Mock()
    client.chat.return_value = 'A fictional catalogue answer.'
    client.health.return_value = dict(available=True, model_ready=True, model='llama3.1:8b', digest='test-digest')
    return client


@pytest.fixture
def app(model):
    return create_app({'TESTING': True}, client=model)
