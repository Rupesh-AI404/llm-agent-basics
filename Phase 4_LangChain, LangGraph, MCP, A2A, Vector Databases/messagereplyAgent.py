"""Simple message replying agent.

Features:
- MessageReplyAgent class with generate_reply(message, context=None)
- Uses OpenAI if OPENAI_API_KEY is set and openai package is available
- Falls back to a small rule-based reply generator
- CLI usage: python messagereplyAgent.py "Hello"
"""

import os
import sys

try:
    import openai
    _HAS_OPENAI = True
except Exception:
    _HAS_OPENAI = False

class MessageReplyAgent:
    """Pluggable message reply agent.

    If OpenAI API key is present and openai is installed, agent will call the LLM.
    Otherwise it uses a lightweight rule-based fallback.
    """

    def __init__(self, model="gpt-3.5-turbo", api_key=None, use_openai=None):
        self.model = model
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        # By default enable OpenAI only when api key is available and package present
        self.use_openai = (use_openai if use_openai is not None else bool(self.api_key)) and _HAS_OPENAI
        if self.use_openai and self.api_key:
            openai.api_key = self.api_key

    def _llm_reply(self, message, context=None):
        system = "You are a helpful assistant that replies concisely."
        messages = [
            {"role": "system", "content": system},
            {"role": "user", "content": (context or "") + "\n\n" + message},
        ]
        resp = openai.ChatCompletion.create(model=self.model, messages=messages, temperature=0.2)
        return resp.choices[0].message.content.strip()

    def _rule_reply(self, message, context=None):
        msg = (message or "").strip()
        if not msg:
            return "No message received."
        low = msg.lower()
        if any(q in low for q in ["?", "who", "what", "when", "where", "why", "how"]):
            return "Thanks for your question — could you provide a little more detail so I can help?"
        if len(msg.split()) < 6:
            return f"Short reply: {msg}"
        # Generic acknowledgment for longer messages
        return f"Received: {msg[:200]}"  # truncate to keep replies concise





if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser(description="Message Replying Agent CLI")
    p.add_argument("--model", default="gpt-3.5-turbo")
    p.add_argument("--use-openai", action="store_true", help="Force using OpenAI (requires openai package and API key)")
    p.add_argument("message", nargs="?", help="Message text; if omitted, read from stdin")
    args = p.parse_args()

    if args.message:
        msg = args.message
    else:
        msg = sys.stdin.read().strip()

    agent = MessageReplyAgent(model=args.model, use_openai=args.use_openai)
    print(agent.generate_reply(msg))
