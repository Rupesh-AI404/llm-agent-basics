"""Simple message replying agent.

Features:
- MessageReplyAgent with reply(message, context=None)
- Uses OpenAI Chat Completions when an API key is available
- Falls back to a small rule-based reply generator
- CLI usage: python messagereplyAgent.py "Hello"
"""

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from typing import Iterable, List, Optional


class MessageReplyAgent:
    """Reply to incoming messages with optional LLM support."""

    def __init__(self, model: str = "gpt-4o-mini", api_key: Optional[str] = None, use_openai: Optional[bool] = None):
        self.model = model
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        self.use_openai = bool(self.api_key) if use_openai is None else bool(use_openai and self.api_key)
        self.system_prompt = "You are a helpful assistant that replies naturally and concisely."

    def _build_messages(self, message: str, context: Optional[str] = None, history: Optional[Iterable[dict]] = None) -> List[dict]:
        messages = [{"role": "system", "content": self.system_prompt}]
        if context:
            messages.append({"role": "system", "content": context})
        if history:
            for item in history:
                role = item.get("role")
                content = item.get("content")
                if role in {"system", "user", "assistant"} and content:
                    messages.append({"role": role, "content": content})
        messages.append({"role": "user", "content": message})
        return messages

    def _llm_reply(self, message: str, context: Optional[str] = None, history: Optional[Iterable[dict]] = None) -> str:
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY is not set")

        payload = {
            "model": self.model,
            "messages": self._build_messages(message, context, history),
            "temperature": 0.2,
            "max_tokens": 150,
            "context": context,
        }
        request = urllib.request.Request(
            "https://api.openai.com/v1/chat/completions",
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "Accept": "application/json",
                "grant_type": "client_credentials",
                "cache-control": "no-cache",
            },
            method="POST",
        )

        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                data = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"OpenAI request failed: {exc.code} {exc.reason}: {detail}") from exc

        return data["choices"][0]["message"]["content"].strip()

    def _rule_reply(self, message: str, context: Optional[str] = None) -> str:
        msg = (message or "").strip()
        if not msg:
            return "No message received."

        low = msg.lower()
        if any(word in low for word in ["help", "assist", "support"]):
            return "Sure - tell me what you need help with."
        if "?" in msg or any(q in low for q in ["who", "what", "when", "where", "why", "how"]):
            return "Thanks for the question. Can you share a bit more detail?"
        if len(msg.split()) <= 6:
            return f"Got it: {msg}"
        if len(msg.split()) > 40:
            return "Thanks for the detailed message. I will reply shortly."
        if len(msg.split()) > 30:
            return "Thanks for the detailed message. I will reply longly."
        if context:
            return f"Understood. Context noted: {context[:120]}"
        if len(msg.split()) > 20:
            return "Thanks for the detailed message. I will reply longly."
        return f"Received: {msg[:200]}"

    def reply(self, message: str, context: Optional[str] = None, history: Optional[Iterable[dict]] = None) -> str:
        """Return a reply for the given message."""
        if self.use_openai:
            try:
                return self._llm_reply(message, context, history)
            except Exception:
                return self._rule_reply(message, context)
        return self._rule_reply(message, context)

    def generate_reply(self, message: str, context: Optional[str] = None, history: Optional[Iterable[dict]] = None) -> str:
        return self.reply(message, context=context, history=history)


def _read_message_from_stdin() -> str:
    if sys.stdin.isatty():
        return ""
    return sys.stdin.read().strip()


def main() -> int:
    parser = argparse.ArgumentParser(description="Message replying agent")
    parser.add_argument("message", nargs="?", help="Message text. If omitted, read from stdin.")
    parser.add_argument("--context", default=None, help="Optional context to include in the reply")
    parser.add_argument("--model", default="gpt-4o-mini", help="OpenAI model to use when API access is available")
    parser.add_argument("--no-openai", action="store_true", help="Force the rule-based fallback")
    parser.add_argument("-v", "--version", action="version", version="%(prog)s 1.0")
    args = parser.parse_args()

    message = args.message or _read_message_from_stdin()
    if not message:
        parser.error("No message provided")

    agent = MessageReplyAgent(model=args.model, use_openai=not args.no_openai)
    print(agent.reply(message, context=args.context))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
