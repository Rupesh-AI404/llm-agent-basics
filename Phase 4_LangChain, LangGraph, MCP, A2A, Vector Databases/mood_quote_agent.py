"""Mood-based quote generator agent.

This module provides a lightweight agent that normalizes a user's mood and
returns a matching quote. It is intentionally dependency-free so it runs in any
standard Python environment.
"""

from __future__ import annotations

import re
from typing import Dict, List, Tuple


class MoodQuoteAgent:
    """Generate a quote based on the user's emotional state."""

    MOOD_MAP: Dict[str, List[str]] = {
        "happy": [
            "Happiness is not by chance, but by choice. — William George Jordan",
            "Keep your face always toward the sunshine—and shadows will fall behind you. — Walt Whitman",
            "The best way to cheer yourself is to try to cheer someone else up. — Mark Twain",
        ],
        "sad": [
            "The darkest nights produce the brightest stars. — John Green",
            "Tough times don't last, tough people do. — Robert H. Schuller",
            "Even the saddest hearts can still learn to bloom. — Unknown",
        ],
        "motivated": [
            "Success is the sum of small efforts, repeated day in and day out. — Robert Collier",
            "Don’t watch the clock; do what it does. Keep going. — Sam Levenson",
            "Start where you are. Use what you have. Do what you can. — Arthur Ashe",
        ],
        "calm": [
            "Peace begins with a smile. — Mother Teresa",
            "In the middle of every difficulty lies opportunity. — Albert Einstein",
            "Breathe. Let go. And remind yourself that this very moment is the only one you need. — Oprah Winfrey",
        ],
        "angry": [
            "For every minute you remain angry, you give up sixty seconds of peace of mind. — Ralph Waldo Emerson",
            "Anger is a feeling that tells you something is wrong; it is not a command to act. — Unknown",
            "When angry, count to ten before you speak; if very angry, count to one hundred. — Thomas Jefferson",
        ],
        "romantic": [
            "Love is not about how many days, months, or years you have been together. It is about how much you love each other every single day. — Unknown",
            "The best thing to hold onto in life is each other. — Audrey Hepburn",
            "Love is composed of a single soul inhabiting two bodies. — Aristotle",
        ],
        "stressed": [
            "You do not have to see the whole staircase, just take the first step. — Martin Luther King Jr.",
            "Rest is not a reward; it is a requirement. — Unknown",
            "Take rest; a field that has rested gives a bountiful crop. — Ovid",
        ],
        "confused": [
            "Not all those who wander are lost. — J.R.R. Tolkien",
            "Sometimes the question is the answer. — Unknown",
            "Clarity is the first step to confidence. — Unknown",
        ],
        "neutral": [
            "The future depends on what you do today. — Mahatma Gandhi",
            "A journey of a thousand miles begins with a single step. — Lao Tzu",
            "Your life does not get better by chance, it gets better by change. — Jim Rohn",
        ],
    }

    SYNONYM_MAP: Dict[str, str] = {
        "happy": "happy",
        "joyful": "happy",
        "excited": "happy",
        "cheerful": "happy",
        "sad": "sad",
        "upset": "sad",
        "depressed": "sad",
        "low": "sad",
        "motivated": "motivated",
        "driven": "motivated",
        "determined": "motivated",
        "energized": "motivated",
        "calm": "calm",
        "peaceful": "calm",
        "relaxed": "calm",
        "serene": "calm",
        "angry": "angry",
        "furious": "angry",
        "mad": "angry",
        "irritated": "angry",
        "romantic": "romantic",
        "love": "romantic",
        "in-love": "romantic",
        "stressed": "stressed",
        "anxious": "stressed",
        "tensed": "stressed",
        "worried": "stressed",
        "confused": "confused",
        "uncertain": "confused",
        "lost": "confused",
        "unsure": "confused",
    }

    @staticmethod
    def normalize_mood(mood: str) -> str:
        """Turn raw user input into a supported mood key."""
        if not mood or not str(mood).strip():
            return "neutral"

        cleaned = re.sub(r"[^a-z\s-]", " ", str(mood).lower())
        cleaned = re.sub(r"\s+", " ", cleaned).strip()

        if cleaned in MoodQuoteAgent.SYNONYM_MAP:
            return MoodQuoteAgent.SYNONYM_MAP[cleaned]

        for key, normalized in MoodQuoteAgent.SYNONYM_MAP.items():
            if key in cleaned.split():
                return normalized

        return "neutral"

    def generate_quote(self, mood: str) -> str:
        """Return a quote for the given mood."""
        normalized = self.normalize_mood(mood)
        quotes = self.MOOD_MAP.get(normalized, self.MOOD_MAP["neutral"])

        index = sum(ord(ch) for ch in normalized) % len(quotes)
        return quotes[index]

    def get_quote_payload(self, mood: str) -> Dict[str, str]:
        """Return a structured payload with mood and quote."""
        normalized = self.normalize_mood(mood)
        return {"mood": normalized, "quote": self.generate_quote(mood)}


def generate_quote(mood: str) -> str:
    """Convenience wrapper for quote generation."""
    return MoodQuoteAgent().generate_quote(mood)


def generate_quote_for_mood(mood: str) -> str:
    """Alias used by callers who prefer a more explicit function name."""
    return generate_quote(mood)


def build_quote(mood: str) -> str:
    """Alias for a simple, readable API."""
    return generate_quote(mood)


if __name__ == "__main__":
    agent = MoodQuoteAgent()
    user_mood = input("How are you feeling today? ").strip() or "neutral"
    quote = agent.generate_quote(user_mood)
    print(f"Mood: {agent.normalize_mood(user_mood)}")
    print(f"Quote: {quote}")
