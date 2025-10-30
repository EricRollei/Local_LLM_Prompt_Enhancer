"""
LLM Backend handlers for LM Studio, Ollama, and Qwen3-VL
Handles API communication with local LLM servers and local models
"""

import requests
import json
import base64
from typing import Dict, Optional, List, Any


class LLMBackend:
    """Handles communication with local LLM backends"""
    
    def __init__(self, backend_type: str, endpoint: str, model_name: str, temperature: float = 0.7):
        self.backend_type = backend_type.lower()
        self.endpoint = endpoint.rstrip('/')
        self.temperature = temperature
        
        # Auto-detect model if not provided
        if model_name is None:
            self.model_name = self._auto_detect_model()
        else:
            self.model_name = model_name
            
        self._capabilities = self._infer_capabilities()
        self._capability_notes: Dict[str, Any] = {}
        self._probe_backend_capabilities()
    
    def _auto_detect_model(self) -> Optional[str]:
        """Auto-detect the currently loaded model from LM Studio or Ollama"""
        try:
            if self.backend_type == "lm_studio":
                # Query LM Studio for loaded models
                url = f"{self.endpoint}/models"
                response = requests.get(url, timeout=5)
                response.raise_for_status()
                data = response.json()
                
                models = data.get("data", [])
                if models and len(models) > 0:
                    # Get the first model (usually the loaded one)
                    detected = models[0].get("id") or models[0].get("model")
                    print(f"[LLM Backend] Auto-detected LM Studio model: {detected}")
                    return detected
                    
            elif self.backend_type == "ollama":
                # Query Ollama for loaded models
                url = f"{self.endpoint.replace('/v1', '')}/api/tags"
                response = requests.get(url, timeout=5)
                response.raise_for_status()
                data = response.json()
                
                models = data.get("models", [])
                if models and len(models) > 0:
                    # Get the first model
                    detected = models[0].get("name")
                    print(f"[LLM Backend] Auto-detected Ollama model: {detected}")
                    return detected
                    
            print(f"[LLM Backend] Could not auto-detect model for {self.backend_type}, will use 'default'")
            return "default"
            
        except Exception as e:
            print(f"[LLM Backend] Auto-detection failed: {e}, using 'default'")
            return "default"

    def _infer_capabilities(self) -> Dict[str, bool]:
        """Best-effort capability inference based on backend and model naming."""

        capabilities = {
            "vision": False
        }

        name = (self.model_name or "").lower()

        if any(tag in name for tag in ["vision", "vl", "mm", "multimodal", "clip", "siglip", "diffusion"]):
            capabilities["vision"] = True

        # Ollama advertises multimodal support via specific endpoints; currently text-only.
        # LM Studio serves OpenAI-compatible models; treat as text unless name hints otherwise.
        if self.backend_type == "ollama" and "vision" in name:
            capabilities["vision"] = True

        return capabilities

    def _probe_backend_capabilities(self) -> None:
        """Query backend metadata for more precise capability detection."""

        if self.backend_type != "lm_studio":
            return

        try:
            url = f"{self.endpoint}/models"
            response = requests.get(url, timeout=6)
            response.raise_for_status()
            payload = response.json()
        except Exception as exc:
            self._capability_notes.setdefault("probe_errors", []).append(str(exc))
            return

        models = payload.get("data")
        if not isinstance(models, list):
            return

        normalized = (self.model_name or "").lower()
        candidate: Optional[Dict[str, Any]] = None
        fallback: List[Dict[str, Any]] = []

        for entry in models:
            if not isinstance(entry, dict):
                continue
            identifier = str(entry.get("id") or entry.get("model") or entry.get("name") or "").lower()
            if identifier == normalized:
                candidate = entry
                break
            fallback.append(entry)

        if candidate is None and normalized:
            for entry in fallback:
                identifier = str(entry.get("id") or entry.get("model") or entry.get("name") or "")
                if normalized in identifier.lower():
                    candidate = entry
                    break

        if candidate is None:
            return

        if self._candidate_supports_vision(candidate):
            self._capabilities["vision"] = True
            matched_id = candidate.get("id") or candidate.get("model") or candidate.get("name")
            if matched_id:
                self._capability_notes["vision_probe_match"] = matched_id
            self._capability_notes["vision_source"] = "lm_studio_probe"

    def _candidate_supports_vision(self, candidate: Dict[str, Any]) -> bool:
        """Inspect LM Studio model metadata for any vision/multimodal signals."""

        indicators = {"vision", "image", "multimodal", "multi-modal", "visual", "vl", "mm"}

        def check_value(value: Any) -> bool:
            if isinstance(value, bool):
                return value
            if isinstance(value, str):
                lowered = value.lower()
                return any(token in lowered for token in indicators)
            if isinstance(value, list):
                return any(check_value(item) for item in value)
            if isinstance(value, dict):
                return any(check_value(val) for val in value.values())
            return False

        direct_flags = [
            "vision",
            "supportsVision",
            "supports_vision",
            "supports_images",
            "supportsImages",
            "has_image_input",
            "hasImageInput",
            "multimodal"
        ]

        for flag in direct_flags:
            if flag in candidate and check_value(candidate.get(flag)):
                return True

        fields = [
            "modalities",
            "capabilities",
            "abilities",
            "tags",
            "features",
            "metadata",
            "io",
            "input_modalities",
            "output_modalities",
            "mode"
        ]

        for field in fields:
            if field in candidate and check_value(candidate.get(field)):
                return True

        return False

    def supports_images(self) -> bool:
        """Return True if the backend/model combination is expected to handle image context."""

        return bool(self._capabilities.get("vision"))

    def caption_image(
        self,
        image_bytes: bytes,
        label: str,
        prompt: Optional[str] = None,
        max_tokens: int = 320
    ) -> Dict:
        """Attempt to obtain a detailed caption from the backend for the provided image."""

        detail_prompt = prompt or (
            "Describe this reference image in exhaustive detail, covering subjects, setting, lighting, colors, mood, and notable elements."
        )

        log_entry = {
            "mode": "vision_caption",
            "label": label,
            "backend": self.backend_type,
            "model": self.model_name,
            "prompt": detail_prompt,
            "success": False,
            "raw_response": None,
            "error": None,
            "attempted": False
        }

        if not self.supports_images():
            log_entry["error"] = "Model does not support image inputs."
            return {
                "success": False,
                "caption": "",
                "error": "Model does not support image inputs.",
                "raw_response": "",
                "log_entry": log_entry
            }

        try:
            if self.backend_type == "lm_studio":
                result = self._caption_lm_studio(image_bytes, detail_prompt, max_tokens)
            elif self.backend_type == "ollama":
                result = self._caption_ollama(image_bytes, detail_prompt, max_tokens)
            else:
                raise ValueError(f"Unsupported backend for vision captioning: {self.backend_type}")

            log_entry["attempted"] = True
            log_entry["raw_response"] = result.get("response")
            log_entry["error"] = result.get("error")
            log_entry["success"] = result.get("success", False)

            if result.get("success") and result.get("response"):
                caption_text = result.get("response", "").strip()
                return {
                    "success": True,
                    "caption": caption_text,
                    "error": None,
                    "raw_response": result.get("response"),
                    "log_entry": log_entry
                }

            return {
                "success": False,
                "caption": "",
                "error": result.get("error") or "Vision caption failed",
                "raw_response": result.get("response", ""),
                "log_entry": log_entry
            }
        except Exception as exc:
            log_entry["attempted"] = True
            log_entry["error"] = str(exc)
            return {
                "success": False,
                "caption": "",
                "error": str(exc),
                "raw_response": "",
                "log_entry": log_entry
            }
        
    def send_prompt(self, system_prompt: str, user_prompt: str, max_tokens: int = 2000) -> Dict:
        """
        Send prompt to LLM and get response
        
        Args:
            system_prompt: System instructions
            user_prompt: User's prompt to expand
            max_tokens: Maximum tokens in response
            
        Returns:
            Dict with 'success', 'response', and 'error' keys
        """
        try:
            if self.backend_type == "lm_studio":
                return self._call_lm_studio(system_prompt, user_prompt, max_tokens)
            elif self.backend_type == "ollama":
                return self._call_ollama(system_prompt, user_prompt, max_tokens)
            elif self.backend_type == "qwen3_vl":
                return self._call_qwen3_vl(system_prompt, user_prompt, max_tokens)
            else:
                return {
                    "success": False,
                    "response": "",
                    "error": f"Unknown backend type: {self.backend_type}"
                }
        except Exception as e:
            return {
                "success": False,
                "response": "",
                "error": f"LLM Backend Error: {str(e)}"
            }
    
    def _call_lm_studio(self, system_prompt: str, user_prompt: str, max_tokens: int) -> Dict:
        """Call LM Studio API (OpenAI-compatible)"""
        url = f"{self.endpoint}/chat/completions"
        
        payload = {
            "model": self.model_name,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": self.temperature,
            "max_tokens": max_tokens,
            "stream": False
        }
        
        headers = {
            "Content-Type": "application/json"
        }
        
        try:
            response = requests.post(url, json=payload, headers=headers, timeout=120)
            response.raise_for_status()
            
            data = response.json()
            
            # Debug logging
            print(f"[LLM Backend] LM Studio response keys: {list(data.keys())}")
            
            # Check if response has expected structure
            if 'choices' not in data:
                error_msg = data.get('error', {})
                if isinstance(error_msg, dict):
                    error_text = error_msg.get('message', str(error_msg))
                else:
                    error_text = str(error_msg) if error_msg else "Unknown error - response missing 'choices' field"
                print(f"[LLM Backend] LM Studio error response: {data}")
                return {
                    "success": False,
                    "response": "",
                    "error": f"LM Studio API Error: {error_text}"
                }
            
            if not data['choices'] or len(data['choices']) == 0:
                return {
                    "success": False,
                    "response": "",
                    "error": "LM Studio returned empty choices array"
                }
            
            content = data['choices'][0]['message']['content']
            
            return {
                "success": True,
                "response": content.strip(),
                "error": None
            }
        except requests.exceptions.Timeout:
            return {
                "success": False,
                "response": "",
                "error": "Request timed out. LLM took too long to respond."
            }
        except requests.exceptions.ConnectionError:
            return {
                "success": False,
                "response": "",
                "error": f"Cannot connect to LM Studio at {self.endpoint}. Is it running?"
            }
        except KeyError as e:
            return {
                "success": False,
                "response": "",
                "error": f"LM Studio returned unexpected response structure (missing {str(e)})"
            }
        except Exception as e:
            return {
                "success": False,
                "response": "",
                "error": f"LM Studio Error: {str(e)}"
            }

    def _caption_lm_studio(self, image_bytes: bytes, prompt: str, max_tokens: int) -> Dict:
        """Call LM Studio for multimodal captioning."""

        url = f"{self.endpoint}/chat/completions"
        image_b64 = base64.b64encode(image_bytes).decode("utf-8")

        payload = {
            "model": self.model_name,
            "messages": [
                {
                    "role": "system",
                    "content": [
                        {
                            "type": "text",
                            "text": "You are an expert visual captioner who writes rich, precise descriptions."
                        }
                    ]
                },
                {
                    "role": "user",
                    "content": [
                        {"type": "input_text", "text": prompt},
                        {
                            "type": "input_image",
                            "image": {
                                "b64": image_b64,
                                "mime_type": "image/png"
                            }
                        }
                    ]
                }
            ],
            "temperature": self.temperature,
            "max_tokens": max_tokens,
            "stream": False
        }

        headers = {
            "Content-Type": "application/json"
        }

        try:
            response = requests.post(url, json=payload, headers=headers, timeout=120)
            response.raise_for_status()

            data = response.json()
            
            # Check if response has expected structure
            if 'choices' not in data:
                error_msg = data.get('error', {})
                if isinstance(error_msg, dict):
                    error_text = error_msg.get('message', str(error_msg))
                else:
                    error_text = str(error_msg) if error_msg else "Unknown error - response missing 'choices' field"
                return {
                    "success": False,
                    "response": "",
                    "error": f"LM Studio vision API error: {error_text}"
                }
            
            if not data['choices'] or len(data['choices']) == 0:
                return {
                    "success": False,
                    "response": "",
                    "error": "LM Studio returned empty choices array for vision request"
                }
            
            content = data['choices'][0]['message']['content']

            return {
                "success": True,
                "response": content.strip(),
                "error": None
            }
        except requests.exceptions.Timeout:
            return {
                "success": False,
                "response": "",
                "error": "Vision caption request timed out."
            }
        except requests.exceptions.ConnectionError:
            return {
                "success": False,
                "response": "",
                "error": f"Cannot connect to LM Studio at {self.endpoint}."
            }
        except KeyError as e:
            return {
                "success": False,
                "response": "",
                "error": f"LM Studio vision response missing field: {str(e)}"
            }
        except Exception as e:
            return {
                "success": False,
                "response": "",
                "error": f"LM Studio vision error: {str(e)}"
            }
    
    def _call_ollama(self, system_prompt: str, user_prompt: str, max_tokens: int) -> Dict:
        """Call Ollama API"""
        url = f"{self.endpoint}/api/generate"
        
        # Combine system and user prompts for Ollama
        full_prompt = f"{system_prompt}\n\n{user_prompt}"
        
        payload = {
            "model": self.model_name,
            "prompt": full_prompt,
            "stream": False,
            "options": {
                "temperature": self.temperature,
                "num_predict": max_tokens
            }
        }
        
        try:
            response = requests.post(url, json=payload, timeout=120)
            response.raise_for_status()
            
            data = response.json()
            content = data.get('response', '')
            
            return {
                "success": True,
                "response": content.strip(),
                "error": None
            }
        except requests.exceptions.Timeout:
            return {
                "success": False,
                "response": "",
                "error": "Request timed out. LLM took too long to respond."
            }
        except requests.exceptions.ConnectionError:
            return {
                "success": False,
                "response": "",
                "error": f"Cannot connect to Ollama at {self.endpoint}. Is it running?"
            }
        except Exception as e:
            return {
                "success": False,
                "response": "",
                "error": f"Ollama Error: {str(e)}"
            }

    def _caption_ollama(self, image_bytes: bytes, prompt: str, max_tokens: int) -> Dict:
        """Call Ollama for multimodal captioning."""

        url = f"{self.endpoint}/api/generate"
        image_b64 = base64.b64encode(image_bytes).decode("utf-8")

        payload = {
            "model": self.model_name,
            "prompt": prompt,
            "images": [image_b64],
            "stream": False,
            "options": {
                "temperature": self.temperature,
                "num_predict": max_tokens
            }
        }

        try:
            response = requests.post(url, json=payload, timeout=120)
            response.raise_for_status()

            data = response.json()
            content = data.get('response', '')

            return {
                "success": True,
                "response": content.strip(),
                "error": None
            }
        except requests.exceptions.Timeout:
            return {
                "success": False,
                "response": "",
                "error": "Vision caption request timed out."
            }
        except requests.exceptions.ConnectionError:
            return {
                "success": False,
                "response": "",
                "error": f"Cannot connect to Ollama at {self.endpoint}."
            }
        except Exception as e:
            return {
                "success": False,
                "response": "",
                "error": f"Ollama vision error: {str(e)}"
            }
    
    def _call_qwen3_vl(self, system_prompt: str, user_prompt: str, max_tokens: int) -> Dict:
        """Call local Qwen3-VL model for text generation (no image)"""
        try:
            from .qwen3_vl_backend import generate_text_with_qwen3_vl
            import folder_paths
            from pathlib import Path
            
            # Determine model spec to use
            # Check api_endpoint first - if it's custom (not default LM Studio URL), use it as model path
            if self.endpoint and self.endpoint != "http://localhost:1234/v1":
                # User specified custom path in api_endpoint field
                model_spec = self.endpoint if self.endpoint.startswith("local:") else f"local:{self.endpoint}"
                print(f"[Qwen3-VL Backend] Using custom model from api_endpoint: {model_spec}")
            else:
                # Auto-detect local model in VLM directory
                vlm_dir = Path(folder_paths.models_dir) / "VLM" / "Qwen3-VL-4B-Instruct"
                if vlm_dir.exists():
                    model_spec = f"local:{str(vlm_dir)}"
                    print(f"[Qwen3-VL Backend] Auto-detected local model: {vlm_dir}")
                else:
                    # Try other common Qwen model names in VLM directory
                    vlm_base = Path(folder_paths.models_dir) / "VLM"
                    qwen_models = list(vlm_base.glob("Qwen*-VL-*")) if vlm_base.exists() else []
                    if qwen_models:
                        model_spec = f"local:{str(qwen_models[0])}"
                        print(f"[Qwen3-VL Backend] Auto-detected local model: {qwen_models[0]}")
                    else:
                        # Fall back to default (will try to download)
                        model_spec = None
                        print("[Qwen3-VL Backend] No local Qwen3-VL model found, will attempt download")
            
            # Combine system and user prompts for text generation
            full_prompt = f"{system_prompt}\n\n{user_prompt}"
            
            # Call Qwen3-VL for pure text generation (no image)
            result = generate_text_with_qwen3_vl(
                prompt=full_prompt,
                model_spec=model_spec,
                max_new_tokens=max_tokens,
                temperature=self.temperature
            )
            
            if result.get("success"):
                return {
                    "success": True,
                    "response": result.get("response", ""),
                    "error": None
                }
            else:
                return {
                    "success": False,
                    "response": "",
                    "error": f"Qwen3-VL error: {result.get('error', 'Unknown error')}"
                }
                
        except ImportError:
            return {
                "success": False,
                "response": "",
                "error": "Qwen3-VL backend not available. Install transformers and torch."
            }
        except Exception as e:
            return {
                "success": False,
                "response": "",
                "error": f"Qwen3-VL Error: {str(e)}"
            }
    
    def test_connection(self) -> Dict:
        """Test if LLM backend is accessible"""
        try:
            if self.backend_type == "lm_studio":
                url = f"{self.endpoint}/models"
                response = requests.get(url, timeout=5)
                response.raise_for_status()
                return {"success": True, "message": "LM Studio connected"}
            elif self.backend_type == "ollama":
                url = f"{self.endpoint}/api/tags"
                response = requests.get(url, timeout=5)
                response.raise_for_status()
                return {"success": True, "message": "Ollama connected"}
            elif self.backend_type == "qwen3_vl":
                # Test Qwen3-VL by checking if we can import it
                try:
                    from .qwen3_vl_backend import caption_with_qwen3_vl
                    return {"success": True, "message": "Qwen3-VL backend available (local model)"}
                except ImportError as e:
                    return {"success": False, "message": f"Qwen3-VL dependencies not installed: {str(e)}"}
        except Exception as e:
            return {"success": False, "message": f"Connection failed: {str(e)}"}
        return {"success": False, "message": f"Unknown backend type: {self.backend_type}"}
