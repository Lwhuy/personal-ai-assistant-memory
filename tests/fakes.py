"""Deterministic fixtures, not a simulated semantic model benchmark."""

import json


class FakeProvider:
    embedding_id = "fixture-vectors-v1"

    def __init__(self):
        self.extractions = {}
        self.messages = []
        self.answer = "A test answer."

    def embed(self, text):
        text = text.casefold()
        if any(word in text for word in ("vietnamese", "decorator", "explanation")):
            return [1.0, 0.0, 0.0, 0.0]
        if any(word in text for word in ("language", "python", "java")):
            return [0.0, 1.0, 0.0, 0.0]
        if any(word in text for word in ("editor", "code")):
            return [0.0, 0.0, 1.0, 0.0]
        return [0.0, 0.0, 0.0, 1.0]

    def chat(self, messages, *, schema=None):
        self.messages.append(messages)
        if schema is not None:
            return json.dumps({"memories": self.extractions.get(messages[-1]["content"], [])})
        return self.answer


def candidate(key, content, quote):
    return {"key": key, "content": content, "memory_type": "semantic", "source_quote": quote}
