from typing import Callable, Dict, List
from dataclasses import dataclass
from enum import Enum


class StreamEventType(Enum):
    START = "start"
    CHUNK = "chunk"
    WORD = "word"
    SENTENCE = "sentence"
    TOOL_CALL = "tool_call"
    COMPLETE = "complete"
    ERROR = "error"


@dataclass
class StreamEvent:
    """Event emitted during streaming."""
    type: StreamEventType
    data: any
    timestamp: float


class StreamingHandler:
    """
    Handles streaming responses with multiple callbacks.
    """

    def __init__(self):
        self._callbacks: Dict[StreamEventType, List[Callable]] = {
            event_type: [] for event_type in StreamEventType
        }
        self._buffer = ""
        self._full_response = ""

    def on(self, event_type: StreamEventType, callback: Callable):
        """Register a callback for an event."""
        self._callbacks[event_type].append(callback)
        return self  # Allow chaining

    def _emit(self, event: StreamEvent):
        """Emit an event to all registered callbacks."""
        for callback in self._callbacks[event.type]:
            callback(event)

    def process_chunk(self, chunk: str):
        """Process a raw chunk from LLM."""
        import time

        # Emit chunk event
        self._emit(StreamEvent(StreamEventType.CHUNK, chunk, time.time()))

        # Update buffers
        self._buffer += chunk
        self._full_response += chunk

        # Detect word boundaries
        if ' ' in self._buffer:
            words = self._buffer.split(' ')
            for word in words[:-1]:  # All complete words
                if word.strip():
                    self._emit(StreamEvent(StreamEventType.WORD, word, time.time()))
            self._buffer = words[-1]  # Keep incomplete word

        # Detect sentence boundaries (., !, ?)
        sentence_endings = ['. ', '! ', '? ', '.\n', '!\n', '?\n']
        for ending in sentence_endings:
            if ending in self._buffer:
                sentences = self._buffer.split(ending)
                for sentence in sentences[:-1]:
                    if sentence.strip():
                        self._emit(StreamEvent(StreamEventType.SENTENCE, sentence + ending.strip(), time.time()))
                self._buffer = sentences[-1]

    def complete(self):
        """Signal that streaming is complete."""
        import time

        # Flush remaining buffer
        if self._buffer.strip():
            self._emit(StreamEvent(StreamEventType.WORD, self._buffer, time.time()))
            self._emit(StreamEvent(StreamEventType.SENTENCE, self._buffer, time.time()))

        # Emit complete event
        self._emit(StreamEvent(StreamEventType.COMPLETE, self._full_response, time.time()))

    def error(self, error_msg: str):
        """Signal an error."""
        import time
        self._emit(StreamEvent(StreamEventType.ERROR, error_msg, time.time()))


# ============= DEMO =============
def demo_streaming():
    """Demo the streaming handler."""

    # Create handler
    handler = StreamingHandler()

    # Register callbacks
    def on_start(event):
        print(f"🎬 Stream started")

    def on_word(event):
        print(f"  📝 Word: '{event.data}'")

    def on_sentence(event):
        print(f"  📖 Sentence: '{event.data}'")

    def on_complete(event):
        print(f"\n✅ Complete! Total length: {len(event.data)} chars")

    handler.on(StreamEventType.START, on_start)
    handler.on(StreamEventType.WORD, on_word)
    handler.on(StreamEventType.SENTENCE, on_sentence)
    handler.on(StreamEventType.COMPLETE, on_complete)

    # Simulate streaming chunks
    handler._emit(StreamEvent(StreamEventType.START, None, 0))

    chunks = [
        "The we",
        "ather in Toky",
        "o is 72 degre",
        "es and sunny.",
        " It's a great d",
        "ay to visit!"
    ]

    for chunk in chunks:
        handler.process_chunk(chunk)

    handler.complete()


if __name__ == "__main__":
    demo_streaming()