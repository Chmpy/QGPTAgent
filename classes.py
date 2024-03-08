import threading
import time
import sys

class Message:
    def __init__(self, content, role, tool_calls):
        self.content = content
        self.role = role
        self.tool_calls = tool_calls


class Choice:
    def __init__(self, finish_reason, index, message):
        self.finish_reason = finish_reason
        self.index = index
        self.message = Message(**message)


class Usage:
    def __init__(self, completion_tokens, prompt_tokens, total_tokens):
        self.completion_tokens = completion_tokens
        self.prompt_tokens = prompt_tokens
        self.total_tokens = total_tokens


class Result:
    def __init__(self, choices, created, id, model, object, usage):
        self.choices = Choice(**choices[0])
        self.created = created
        self.id = id
        self.model = model
        self.object = object
        self.usage = Usage(**usage)