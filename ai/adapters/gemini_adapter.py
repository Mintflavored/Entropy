import os
import json

class GeminiAdapter:
    def __init__(self, api_key):
        import google.generativeai as genai
        genai.configure(api_key=api_key)
        self.genai = genai

    def generate(self, model, messages, tools=None):
        # Преобразование сообщений для Gemini
        gemini_model = self.genai.GenerativeModel(model)
        
        # Инструменты для Gemini
        gemini_tools = []
        if tools:
            # Упрощенное преобразование
            gemini_tools = tools 

        # Gemini обычно принимает историю чата
        # Для простоты используем одноразовый запрос или простейший цикл
        # В данной реализации просто преобразуем последнее сообщение и системный промпт
        system_instruction = next((m["content"] for m in messages if m["role"] == "system"), None)
        chat_history = []
        for m in messages:
            if m["role"] == "system": continue
            chat_history.append({"role": "user" if m["role"] == "user" else "model", "parts": [m["content"]]})
        
        if system_instruction:
            gemini_model = self.genai.GenerativeModel(model, system_instruction=system_instruction)

        # Gemini Tool implementation is quite different, for now we mock it
        # or use basic generate_content
        response = gemini_model.generate_content(
            messages[-1]["content"],
            tools=gemini_tools if tools else None
        )
        
        class MockMessage:
            def __init__(self, res):
                self.content = res.text if not res.candidates[0].content.parts[0].function_call else ""
                self.tool_calls = []
                # Обработка tool_calls для Gemini
                if res.candidates[0].content.parts[0].function_call:
                    fc = res.candidates[0].content.parts[0].function_call
                    class MockToolCall:
                        def __init__(self, f_call):
                            self.id = "gemini_call" # Gemini doesn't always provide an ID in simple mode
                            self.function = type('obj', (object,), {
                                'name': f_call.name, 
                                'arguments': json.dumps(dict(f_call.args))
                            })()
                    self.tool_calls.append(MockToolCall(fc))
        
        return MockMessage(response)
