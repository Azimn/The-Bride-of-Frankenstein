from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol
import json
import os
import urllib.request

from .types import RenderedResponse, SubjectiveFrame


class Renderer(Protocol):
    renderer_id: str
    def render(self, frame: SubjectiveFrame, *, user_text: str = "") -> RenderedResponse: ...


class DeterministicRenderer:
    renderer_id = "deterministic-v1"

    def render(self, frame: SubjectiveFrame, *, user_text: str = "") -> RenderedResponse:
        memory = frame.recalled_memories[0] if frame.recalled_memories else ""
        if frame.selected_move == "withdraw":
            text = "I do not want to push this further right now."
        elif frame.selected_move == "clarify":
            text = "I want to make sure I understand what you mean before I commit to an answer."
        elif frame.selected_move == "repair":
            text = "I think there is something here that needs repair, and I would rather address it directly."
        elif frame.selected_move == "commit":
            text = "Yes. I am willing to take that on, and I want to keep track of it properly."
        else:
            text = "I am here and paying attention."
            if memory:
                text += f" This connects with something I remember: {memory}"
        return RenderedResponse(text=text, renderer_id=self.renderer_id, raw={"mode": "deterministic"})


@dataclass
class OllamaRenderer:
    model: str
    base_url: str = "http://127.0.0.1:11434"
    timeout: float = 90.0
    renderer_id: str = "ollama"

    def render(self, frame: SubjectiveFrame, *, user_text: str = "") -> RenderedResponse:
        system = (
            "You are the language renderer for one persistent character. The structured subjective frame is authoritative about what the character may know and feel. "
            "Do not invent memories, commitments, world facts, hidden numerical state, or tool results. Express the selected social move naturally in first person."
        )
        prompt = json.dumps({"frame": frame.as_prompt_dict(), "current_message": user_text}, ensure_ascii=False)
        body = json.dumps({"model": self.model, "stream": False, "messages": [{"role": "system", "content": system}, {"role": "user", "content": prompt}]}).encode("utf-8")
        req = urllib.request.Request(self.base_url.rstrip("/") + "/api/chat", data=body, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=self.timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        text = str(data.get("message", {}).get("content", "")).strip()
        out = RenderedResponse(text=text, renderer_id=f"ollama:{self.model}", raw={"done_reason": data.get("done_reason")})
        out.validate()
        return out


@dataclass
class OpenAICompatibleRenderer:
    model: str
    base_url: str
    api_key_env: str = "FRANKENSTEIN_API_KEY"
    timeout: float = 90.0
    renderer_id: str = "openai-compatible"

    def render(self, frame: SubjectiveFrame, *, user_text: str = "") -> RenderedResponse:
        key = os.environ.get(self.api_key_env, "")
        messages = [
            {"role": "system", "content": "Render the supplied subjective character state without inventing facts or hidden state."},
            {"role": "user", "content": json.dumps({"frame": frame.as_prompt_dict(), "current_message": user_text}, ensure_ascii=False)},
        ]
        body = json.dumps({"model": self.model, "messages": messages, "temperature": 0.7}).encode("utf-8")
        headers = {"Content-Type": "application/json"}
        if key:
            headers["Authorization"] = f"Bearer {key}"
        req = urllib.request.Request(self.base_url.rstrip("/") + "/chat/completions", data=body, headers=headers)
        with urllib.request.urlopen(req, timeout=self.timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        text = str(data["choices"][0]["message"]["content"]).strip()
        out = RenderedResponse(text=text, renderer_id=f"openai-compatible:{self.model}", raw={"finish_reason": data["choices"][0].get("finish_reason")})
        out.validate()
        return out
