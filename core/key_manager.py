"""
╔══════════════════════════════════════════════════════════════╗
║     GRAVITY AI — KEY MANAGER V7.1                            ║
║     Almacenamiento cifrado de API keys (DPAPI en Windows)   ║
╚══════════════════════════════════════════════════════════════╝

Estrategia de cifrado por plataforma:
  Windows: DPAPI via win32crypt (pywin32) — vinculado al usuario actual
  Fallback (Linux/Mac o sin pywin32): XOR con machine-unique salt
             derivado de hostname + volume serial number

El keystore se guarda en _keystore.bin como bytes cifrados JSON.
NUNCA se guarda ninguna API key en texto plano.
"""

import os
import json
import hashlib
import platform
import subprocess

BASE_DIR      = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KEYSTORE_FILE = os.path.join(BASE_DIR, "_keystore.bin")

# Proveedores cloud conocidos con sus metadatos de display
KNOWN_CLOUD_PROVIDERS = {
    "openai":       {"display": "OpenAI",           "key_prefix": "sk-",   "url": "https://api.openai.com/v1"},
    "anthropic":    {"display": "Anthropic",         "key_prefix": "sk-ant","url": "https://api.anthropic.com"},
    "gemini":       {"display": "Google Gemini",     "key_prefix": "AIza", "url": "https://generativelanguage.googleapis.com"},
    "mistral":      {"display": "Mistral AI",        "key_prefix": "",     "url": "https://api.mistral.ai/v1"},
    "groq":         {"display": "Groq",              "key_prefix": "gsk_", "url": "https://api.groq.com/openai/v1"},
    "deepseek":     {"display": "DeepSeek Cloud",    "key_prefix": "sk-",  "url": "https://api.deepseek.com/v1"},
    "together":     {"display": "Together AI",       "key_prefix": "",     "url": "https://api.together.xyz/v1"},
    "fireworks":    {"display": "Fireworks AI",      "key_prefix": "fw_",  "url": "https://api.fireworks.ai/inference/v1"},
    "cohere":       {"display": "Cohere",            "key_prefix": "",     "url": "https://api.cohere.com/v1"},
    "xai":          {"display": "xAI (Grok)",        "key_prefix": "xai-", "url": "https://api.x.ai/v1"},
    "azure":        {"display": "Azure OpenAI",      "key_prefix": "",     "url": "custom"},
    "bedrock":      {"display": "AWS Bedrock",       "key_prefix": "",     "url": "custom"},
    "huggingface":  {"display": "HuggingFace",       "key_prefix": "hf_",  "url": "https://api-inference.huggingface.co"},
    "perplexity":   {"display": "Perplexity",        "key_prefix": "pplx-","url": "https://api.perplexity.ai"},
    "openrouter":   {"display": "OpenRouter",        "key_prefix": "sk-or-","url": "https://openrouter.ai/api/v1"},
    "deepinfra":    {"display": "DeepInfra",         "key_prefix": "",     "url": "https://api.deepinfra.com/v1/openai"},
}


def _get_machine_salt() -> bytes:
    """Derives a machine-unique salt (NOT a secret; just for key derivation)."""
    parts = [platform.node(), platform.machine(), platform.processor()]
    if platform.system() == "Windows":
        try:
            vol = subprocess.check_output(
                "vol C:", shell=True, stderr=subprocess.DEVNULL
            ).decode(errors="ignore")
            parts.append(vol)
        except Exception:
            pass
    raw = "|".join(parts).encode()
    return hashlib.sha256(raw).digest()


def _xor_cipher(data: bytes, key: bytes) -> bytes:
    """Simple XOR stream cipher. key is cycled."""
    return bytes(b ^ key[i % len(key)] for i, b in enumerate(data))


def _encrypt(plaintext: str) -> bytes:
    """Encrypt a string. Uses DPAPI on Windows, XOR fallback otherwise."""
    raw = plaintext.encode("utf-8")
    if platform.system() == "Windows":
        try:
            import win32crypt
            return win32crypt.CryptProtectData(raw, None, None, None, None, 0)[1]
        except Exception:
            pass
    # Fallback XOR
    salt = _get_machine_salt()
    key  = hashlib.sha256(salt + b"GravityAI_V7.1").digest()
    return b"XOR:" + _xor_cipher(raw, key)


def _decrypt(ciphertext: bytes) -> str:
    """Decrypt bytes back to string."""
    if ciphertext.startswith(b"XOR:"):
        salt = _get_machine_salt()
        key  = hashlib.sha256(salt + b"GravityAI_V7.1").digest()
        return _xor_cipher(ciphertext[4:], key).decode("utf-8")
    if platform.system() == "Windows":
        try:
            import win32crypt
            _, decrypted = win32crypt.CryptUnprotectData(ciphertext, None, None, None, 0)
            return decrypted.decode("utf-8")
        except Exception:
            pass
    raise ValueError("Cannot decrypt: platform mismatch or corrupted keystore")


def _load_store() -> dict:
    """Loads and decrypts the keystore. Returns {} if it doesn't exist."""
    if not os.path.exists(KEYSTORE_FILE):
        return {}
    try:
        with open(KEYSTORE_FILE, "rb") as f:
            encrypted_json = f.read()
        plaintext = _decrypt(encrypted_json)
        return json.loads(plaintext)
    except Exception:
        return {}


def _save_store(store: dict) -> None:
    """Encrypts and saves the keystore."""
    plaintext = json.dumps(store, ensure_ascii=False)
    encrypted = _encrypt(plaintext)
    with open(KEYSTORE_FILE, "wb") as f:
        f.write(encrypted)


class KeyManager:
    """
    Secure API key storage with DPAPI (Windows) or XOR fallback.

    All methods are classmethods for ergonomic usage:
        KeyManager.set_key("openai", "sk-...")
        key = KeyManager.get_key("openai")
    """

    @classmethod
    def set_key(cls, provider: str, api_key: str) -> None:
        """Stores an API key for a provider (encrypted)."""
        store = _load_store()
        store[provider.lower().strip()] = api_key.strip()
        _save_store(store)

    @classmethod
    def get_key(cls, provider: str) -> str | None:
        """Returns the API key for a provider, or None if not configured."""
        store = _load_store()
        return store.get(provider.lower().strip())

    @classmethod
    def has_key(cls, provider: str) -> bool:
        """Returns True if an API key is configured for this provider."""
        return cls.get_key(provider) is not None

    @classmethod
    def delete_key(cls, provider: str) -> bool:
        """Deletes the API key for a provider. Returns True if it existed."""
        store = _load_store()
        key   = provider.lower().strip()
        if key in store:
            del store[key]
            _save_store(store)
            return True
        return False

    @classmethod
    def rotate_key(cls, provider: str, new_key: str) -> None:
        """Alias for set_key: replaces existing key."""
        cls.set_key(provider, new_key)

    @classmethod
    def list_configured(cls) -> list[str]:
        """Returns list of provider names that have a configured key."""
        return list(_load_store().keys())

    @classmethod
    def mask(cls, provider: str) -> str:
        """Returns a masked representation of the key (first 4 + ... + last 3 chars)."""
        key = cls.get_key(provider)
        if not key:
            return "[no configurada]"
        if len(key) <= 10:
            return "*" * len(key)
        return f"{key[:5]}...{key[-3:]}"

    @classmethod
    def get_provider_info(cls, provider: str) -> dict | None:
        """Returns metadata dict for a known cloud provider."""
        return KNOWN_CLOUD_PROVIDERS.get(provider.lower())

    @classmethod
    def list_all_known(cls) -> dict:
        """Returns all known cloud providers with their key status."""
        result = {}
        for pid, meta in KNOWN_CLOUD_PROVIDERS.items():
            result[pid] = {
                **meta,
                "has_key":   cls.has_key(pid),
                "key_masked": cls.mask(pid) if cls.has_key(pid) else None,
            }
        return result

    @classmethod
    def clear_all(cls) -> int:
        """Deletes ALL stored keys. Returns number of keys deleted."""
        store = _load_store()
        count = len(store)
        _save_store({})
        return count


if __name__ == "__main__":
    print("KeyManager V7.1 — Test\n")
    KeyManager.set_key("test_provider", "sk-test-123456789")
    assert KeyManager.has_key("test_provider")
    assert KeyManager.get_key("test_provider") == "sk-test-123456789"
    print(f"  Mask: {KeyManager.mask('test_provider')}")
    KeyManager.delete_key("test_provider")
    assert not KeyManager.has_key("test_provider")
    print("  All tests passed.")
    print("\nKnown providers:")
    for pid, info in KeyManager.list_all_known().items():
        status = "✅ Configurada" if info["has_key"] else "🔴 Sin key"
        print(f"  {pid:<14} {info['display']:<20} {status}")
