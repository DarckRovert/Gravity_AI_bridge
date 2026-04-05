import pytest

from provider_manager import ProviderManager


@pytest.fixture
def provider_manager():
    return ProviderManager()


def test_provider_initialization(provider_manager):
    assert provider_manager is not None


def test_add_provider(provider_manager):
    provider_manager.add_provider("test_provider")
    assert "test_provider" in provider_manager.providers


def test_remove_provider(provider_manager):
    provider_manager.add_provider("test_provider")
    provider_manager.remove_provider("test_provider")
    assert "test_provider" not in provider_manager.providers


def test_get_providers(provider_manager):
    provider_manager.add_provider("test_provider1")
    provider_manager.add_provider("test_provider2")
    assert set(provider_manager.get_providers()) == {"test_provider1", "test_provider2"}
