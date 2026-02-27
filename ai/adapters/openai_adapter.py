import os
import json
from openai import OpenAI

class OpenAIAdapter:
    def __init__(self, api_key, base_url=None):
        params = {"api_key": api_key}
        if base_url:
            params["base_url"] = base_url
        self.client = OpenAI(**params)

    def generate(self, model, messages, tools=None, json_mode=False):
        params = {
            "model": model,
            "messages": messages,
        }
        if tools:
            params["tools"] = tools
            params["tool_choice"] = "auto"
        if json_mode:
            params["response_format"] = {"type": "json_object"}
        
        response = self.client.chat.completions.create(**params)
        return response.choices[0].message
