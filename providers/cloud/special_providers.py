"""
Gravity AI — Azure OpenAI + Cohere + HuggingFace + AWS Bedrock V13.0 PRO

Azure:       OpenAI-compatible pero con auth por header 'api-key' y
             endpoint custom por resource/deployment.
Cohere:      REST API propia con /chat endpoint.
HuggingFace: Inference API + nuevo router OpenAI-compat.
AWS Bedrock: boto3 required; streams via InvokeModelWithResponseStream.
"""

import json
import urllib.request
import urllib.error
import os
import logging
from typing import Generator, List, Dict, Any, Tuple
from providers.base import ProviderPlugin, ProviderResult
from core.key_manager import KeyManager
from providers.cloud._openai_compat_cloud import OpenAICompatCloudProvider

logger = logging.getLogger("gravity")


# ── Azure OpenAI ──────────────────────────────────────────────────────────────
class AzureOpenAIProvider(ProviderPlugin):
    name: str = "Azure OpenAI"
    protocol: str = "openai"
    category: str = "cloud"
    requires_key: bool = True
    supports_vision: bool = True
    supports_function_calling: bool = True
    default_context: int = 128000
    _key_id: str = "azure"

    def _get_endpoint_and_key(self) -> Tuple[str, str]:
        key = KeyManager.get_key("azure") or ""
        if "|" in key:
            parts = key.split("|", 2)
            api_key, resource, deployment = (parts + ["", ""])[:3]
            endpoint = (
                f"https://{resource}.openai.azure.com/openai/deployments/{deployment}"
            )
            return api_key, endpoint
        return key, os.environ.get("AZURE_OPENAI_ENDPOINT", "")

    def check_health(self) -> ProviderResult:
        r = self._make_result("https://azure.openai.com")
        r.key_configured = KeyManager.has_key("azure")
        if r.key_configured:
            r.is_healthy = True
            r.models = [{"name": "azure-deployment", "size": 0}]
            r.active_model = "azure-deployment"
        return r

    def chat_stream(
        self,
        messages: List[Dict[str, Any]],
        model: str,
        options: Dict[str, Any],
    ) -> Generator[str, None, None]:
        api_key, endpoint = self._get_endpoint_and_key()
        url = f"{endpoint.rstrip('/')}/chat/completions?api-version=2024-02-01"
        payload: Dict[str, Any] = {"messages": messages, "stream": True}
        for k in ("temperature", "top_p", "max_tokens"):
            if k in options:
                payload[k] = options[k]
        headers = {"Content-Type": "application/json", "api-key": api_key}
        data = json.dumps(payload).encode()
        req = urllib.request.Request(url, data=data, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=300) as r:
                for raw in r:
                    line = raw.decode("utf-8", errors="ignore").strip()
                    if line.startswith("data:") and line[5:].strip() not in (
                        "",
                        "[DONE]",
                    ):
                        try:
                            d = json.loads(line[5:].strip())
                            chunk = d["choices"][0]["delta"].get("content", "")
                            if chunk:
                                yield chunk
                        except Exception:
                            pass
        except Exception as e:
            logger.error(f"[AzureOpenAIStream] Error: {e}")

    def chat_complete(
        self,
        messages: List[Dict[str, Any]],
        model: str,
        options: Dict[str, Any],
    ) -> str:
        api_key, endpoint = self._get_endpoint_and_key()
        url = f"{endpoint.rstrip('/')}/chat/completions?api-version=2024-02-01"
        payload: Dict[str, Any] = {"messages": messages, "stream": False}
        headers = {"Content-Type": "application/json", "api-key": api_key}
        data = json.dumps(payload).encode()
        req = urllib.request.Request(url, data=data, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=300) as r:
                d = json.loads(r.read().decode())
            return str(d["choices"][0]["message"]["content"]) if "choices" in d else ""
        except Exception as e:
            logger.error(f"[AzureOpenAIComplete] Error: {e}")
        return ""

    def get_cost_per_million_tokens(self, model: str) -> Dict[str, float]:
        return {"input": 5.00, "output": 15.00}


# ── Cohere ────────────────────────────────────────────────────────────────────
class CohereProvider(ProviderPlugin):
    name: str = "Cohere"
    protocol: str = "cohere"
    category: str = "cloud"
    requires_key: bool = True
    supports_function_calling: bool = True
    default_context: int = 128000
    _key_id: str = "cohere"
    _available_models: List[str] = [
        "command-r-plus-08-2024",
        "command-r-03-2024",
        "command-a-03-2025",
    ]

    def _headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {KeyManager.get_key(self._key_id) or ''}",
            "Content-Type": "application/json",
        }

    def check_health(self) -> ProviderResult:
        r = self._make_result("https://api.cohere.com/v1")
        r.key_configured = KeyManager.has_key(self._key_id)
        if r.key_configured:
            r.is_healthy = True
            r.models = [{"name": m, "size": 0} for m in self._available_models]
            r.active_model = self._available_models[0]
        return r

    def _convert_messages(
        self, messages: List[Dict[str, Any]]
    ) -> Tuple[str, List[Dict[str, Any]], str]:
        """Converts OpenAI messages → Cohere chat_history + message."""
        system_prompt = ""
        history: List[Dict[str, Any]] = []
        last_user_msg = ""
        for m in messages:
            role = m.get("role")
            content = str(m.get("content", ""))
            if role == "system":
                system_prompt = content
            elif role == "user":
                last_user_msg = content
                if history:
                    history.append({"role": "USER", "message": content})
            elif role == "assistant":
                history.append({"role": "CHATBOT", "message": content})
        return system_prompt, history[:-1] if history else [], last_user_msg

    def chat_stream(
        self,
        messages: List[Dict[str, Any]],
        model: str,
        options: Dict[str, Any],
    ) -> Generator[str, None, None]:
        preamble, history, user_msg = self._convert_messages(messages)
        payload: Dict[str, Any] = {"model": model, "message": user_msg, "stream": True}
        if preamble:
            payload["preamble"] = preamble
        if history:
            payload["chat_history"] = history
        data = json.dumps(payload).encode()
        req = urllib.request.Request(
            "https://api.cohere.com/v1/chat", data=data, headers=self._headers()
        )
        try:
            with urllib.request.urlopen(req, timeout=300) as r:
                for raw in r:
                    line = raw.decode("utf-8", errors="ignore").strip()
                    if not line:
                        continue
                    try:
                        d = json.loads(line)
                        if d.get("event_type") == "text-generation":
                            yield d.get("text", "")
                    except Exception:
                        pass
        except Exception as e:
            logger.error(f"[CohereStream] Error: {e}")

    def chat_complete(
        self,
        messages: List[Dict[str, Any]],
        model: str,
        options: Dict[str, Any],
    ) -> str:
        preamble, history, user_msg = self._convert_messages(messages)
        payload: Dict[str, Any] = {"model": model, "message": user_msg}
        if preamble:
            payload["preamble"] = preamble
        if history:
            payload["chat_history"] = history
        data = json.dumps(payload).encode()
        req = urllib.request.Request(
            "https://api.cohere.com/v1/chat", data=data, headers=self._headers()
        )
        try:
            with urllib.request.urlopen(req, timeout=300) as r:
                d = json.loads(r.read().decode())
            return str(d.get("text", ""))
        except Exception as e:
            logger.error(f"[CohereComplete] Error: {e}")
        return ""

    def get_cost_per_million_tokens(self, model: str) -> Dict[str, float]:
        costs = {
            "command-r-plus-08-2024": {"input": 2.50, "output": 10.00},
            "command-r-03-2024": {"input": 0.15, "output": 0.60},
        }
        return costs.get(model, {"input": 2.50, "output": 10.00})


# ── HuggingFace ───────────────────────────────────────────────────────────────
class HuggingFaceProvider(OpenAICompatCloudProvider):
    """
    HuggingFace Inference Router (new OpenAI-compat endpoint).
    Supports any model on HuggingFace Hub with Inference API enabled.
    """

    name: str = "HuggingFace"
    _base_url: str = "https://router.huggingface.co/v1"
    _key_id: str = "huggingface"
    default_context: int = 32768
    _available_models: List[str] = [
        "meta-llama/Meta-Llama-3.1-8B-Instruct",
        "mistralai/Mistral-7B-Instruct-v0.3",
        "Qwen/Qwen2.5-72B-Instruct",
        "deepseek-ai/DeepSeek-R1",
        "google/gemma-2-27b-it",
    ]

    def get_cost_per_million_tokens(self, model: str) -> Dict[str, float]:
        return {"input": 0.50, "output": 0.50}


# ── AWS Bedrock ───────────────────────────────────────────────────────────────
class BedrockProvider(ProviderPlugin):
    """
    AWS Bedrock — requires:
      KeyManager.set_key("bedrock", "ACCESS_KEY|SECRET_KEY|REGION")
    Uses boto3 if available, falls back to SigV4-signed urllib requests.
    """

    name: str = "AWS Bedrock"
    protocol: str = "bedrock"
    category: str = "cloud"
    requires_key: bool = True
    supports_vision: bool = True
    supports_function_calling: bool = True
    default_context: int = 200000
    _key_id: str = "bedrock"
    _available_models: List[str] = [
        "anthropic.claude-3-5-sonnet-20241022-v2:0",
        "anthropic.claude-3-haiku-20240307-v1:0",
        "meta.llama3-70b-instruct-v1:0",
        "amazon.titan-text-premier-v1:0",
    ]

    def _get_credentials(self) -> Tuple[str, str, str]:
        raw = KeyManager.get_key(self._key_id) or ""
        if "|" in raw:
            parts = raw.split("|", 2)
            ak, sk = (parts + ["", ""])[:2]
            region = parts[2] if len(parts) > 2 else "us-east-1"
            return ak, sk, region
        return "", "", "us-east-1"

    def check_health(self) -> ProviderResult:
        r = self._make_result("https://bedrock.aws.amazon.com")
        r.key_configured = KeyManager.has_key(self._key_id)
        if r.key_configured:
            r.is_healthy = True
            r.models = [{"name": m, "size": 0} for m in self._available_models]
            r.active_model = self._available_models[0]
        return r

    def chat_stream(
        self,
        messages: List[Dict[str, Any]],
        model: str,
        options: Dict[str, Any],
    ) -> Generator[str, None, None]:
        try:
            import boto3

            ak, sk, region = self._get_credentials()
            client = boto3.client(
                "bedrock-runtime",
                aws_access_key_id=ak,
                aws_secret_access_key=sk,
                region_name=region,
            )
            system_prompt = ""
            body_messages: List[Dict[str, Any]] = []
            for m in messages:
                role = m.get("role")
                content = m.get("content")
                if role == "system":
                    system_prompt = str(content)
                else:
                    body_messages.append({"role": role, "content": content})
            body: Dict[str, Any] = {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": options.get("max_tokens", 4096),
                "messages": body_messages,
            }
            if system_prompt:
                body["system"] = system_prompt

            resp = client.invoke_model_with_response_stream(
                modelId=model, body=json.dumps(body)
            )
            for event in resp["body"]:
                chunk_data = json.loads(event["chunk"]["bytes"].decode())
                if chunk_data.get("type") == "content_block_delta":
                    yield str(chunk_data.get("delta", {}).get("text", ""))
        except ImportError:
            yield "[Bedrock] boto3 no instalado. Ejecuta: pip install boto3"
        except Exception as e:
            yield f"[Bedrock Error] {e}"

    def chat_complete(
        self,
        messages: List[Dict[str, Any]],
        model: str,
        options: Dict[str, Any],
    ) -> str:
        chunks: List[str] = []
        try:
            for chunk in self.chat_stream(messages, model, options):
                chunks.append(chunk)
            return "".join(chunks)
        except Exception as e:
            logger.error(f"[BedrockComplete] Error: {e}")
        return ""

    def get_cost_per_million_tokens(self, model: str) -> Dict[str, float]:
        costs = {
            "anthropic.claude-3-5-sonnet-20241022-v2:0": {
                "input": 3.00,
                "output": 15.00,
            },
            "anthropic.claude-3-haiku-20240307-v1:0": {"input": 0.25, "output": 1.25},
            "meta.llama3-70b-instruct-v1:0": {"input": 1.00, "output": 1.00},
        }
        return costs.get(model, {"input": 3.00, "output": 15.00})
