import os
import json

class ClaudeAdapter:
    def __init__(self, api_key):
        import anthropic
        self.client = anthropic.Anthropic(api_key=api_key)

    def generate(self, model, messages, tools=None):
        # Преобразование сообщений из формата OpenAI в Claude
        system_msg = ""
        claude_messages = []
        for m in messages:
            if m["role"] == "system":
                system_msg = m["content"]
            else:
                claude_messages.append(m)
        
        # Инструменты в формате Claude (упрощенно)
        claude_tools = []
        if tools:
            for t in tools:
                f = t["function"]
                claude_tools.append({
                    "name": f["name"],
                    "description": f["description"],
                    "input_schema": f["parameters"]
                })

        response = self.client.messages.create(
            model=model,
            max_tokens=4096,
            system=system_msg,
            messages=claude_messages,
            tools=claude_tools if tools else None
        )
        
        # Возвращаем объект, имитирующий структуру OpenAI Message для совместимости с bridge.py
        class MockMessage:
            def __init__(self, res):
                self.content = res.content[0].text if hasattr(res.content[0], 'text') else ""
                self.tool_calls = []
                # Обработка tool_calls для Claude
                for part in res.content:
                    if part.type == 'tool_use':
                        class MockToolCall:
                            def __init__(self, p):
                                self.id = p.id
                                self.function = type('obj', (object,), {'name': p.name, 'arguments': json.dumps(p.input)})()
                        self.tool_calls.append(MockToolCall(part))
        
        return MockMessage(response)
