import os
import json
from openai import OpenAI

class OpenAIAdapter:
    def __init__(self, api_key, base_url=None):
        params = {"api_key": api_key}
        if base_url:
            params["base_url"] = base_url
        self.client = OpenAI(**params)

    def generate(self, model, messages, tools=None):
        response = self.client.chat.completions.create(
            model=model,
            messages=messages,
            tools=tools,
            tool_choice="auto" if tools else None
        )
        return response.choices[0].message
