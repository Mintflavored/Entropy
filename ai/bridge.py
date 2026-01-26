import json
import logging
import paramiko
from PyQt6.QtCore import QThread, pyqtSignal
from openai import OpenAI

logger = logging.getLogger(__name__)

class AIAnalyzer(QThread):
    """Единый поток для AI анализа с поддержкой Tool Calling."""
    result_ready = pyqtSignal(str)
    error_occurred = pyqtSignal(str)

    def __init__(self, cfg, data_context, server_config):
        super().__init__()
        self.cfg = cfg
        self.data_context = data_context
        self.server_config = server_config

    def run(self):
        ssh = None
        try:
            provider_type = self.cfg.get("ai_provider", "openai_compatible")
            api_key = self.cfg.ai_key
            model_name = self.cfg.get("ai_model", "glm-4.7")
            base_url = self.cfg.get("ai_base_url")

            if not api_key:
                self.error_occurred.emit("API Key не найден. Проверьте настройки или .env")
                return

            # Инициализация адаптера
            if provider_type == "claude":
                from ai.adapters.claude_adapter import ClaudeAdapter
                adapter = ClaudeAdapter(api_key)
            elif provider_type == "gemini":
                from ai.adapters.gemini_adapter import GeminiAdapter
                adapter = GeminiAdapter(api_key)
            else: # openai or compatible
                from ai.adapters.openai_adapter import OpenAIAdapter
                adapter = OpenAIAdapter(api_key, base_url if provider_type == "openai_compatible" else None)
            
            max_calls = self.cfg.get("ai_tool_limit", 5)
            
            tools = [
                {
                    "type": "function",
                    "function": {
                        "name": "execute_ssh_command",
                        "description": "Выполнить диагностическую команду на VPN-сервере через SSH.",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "command": {"type": "string"}
                            },
                            "required": ["command"]
                        }
                    }
                }
            ]

            prompt = f"""
            Ты — Senior DevOps & Security эксперт по VPN-инфраструктуре. 
            У тебя есть доступ к серверу через SSH для глубокой диагностики.
            ТЕБЕ ДОСТУПНО МАКСИМУМ {max_calls} SSH-ЗАПРОСОВ.
            
            ИНФОРМАЦИЯ О СЕРВЕРЕ (Контекст): {json.dumps(self.server_config, ensure_ascii=False)}
            ТЕКУЩИЕ МЕТРИКИ: {json.dumps(self.data_context, ensure_ascii=False)}
            
            ЗАДАЧА: Проанализируй состояние и дай 3 конкретных совета по безопасности или оптимизации.
            Если нужно проверить конфиги или логи за пределами стандартных метрик, используй `execute_ssh_command`.
            """

            messages = [
                {"role": "system", "content": "Ты эксперт-консультант по кибербезопасности VPN."},
                {"role": "user", "content": prompt}
            ]
            
            for i in range(max_calls + 1):
                # Вызов через адаптер
                response_message = adapter.generate(model_name, messages, tools=tools)
                
                if not response_message.tool_calls:
                    self.result_ready.emit(response_message.content)
                    return

                if i >= max_calls:
                    logger.warning("AI исчерпал лимит SSH-запросов")
                    messages.append({"role": "assistant", "content": response_message.content, "tool_calls": response_message.tool_calls})
                    messages.append({
                        "role": "tool",
                        "tool_call_id": response_message.tool_calls[0].id,
                        "name": response_message.tool_calls[0].function.name,
                        "content": f"ОШИБКА: Превышен лимит запросов ({max_calls}). Сформируй финальный отчет.",
                    })
                    continue

                messages.append({"role": "assistant", "content": response_message.content, "tool_calls": response_message.tool_calls})
                
                for tool_call in response_message.tool_calls:
                    if tool_call.function.name == "execute_ssh_command":
                        cmd = json.loads(tool_call.function.arguments).get("command")
                        logger.info(f"AI ({i+1}/{max_calls}) -> {cmd}")
                        
                        try:
                            if not ssh:
                                ssh = paramiko.SSHClient()
                                ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                                ssh.connect(
                                    hostname=self.cfg.get("ip"), port=self.cfg.get("port"), 
                                    username=self.cfg.get("user"), key_filename=self.cfg.get("key_path"), 
                                    timeout=15, banner_timeout=30
                                )
                            _, stdout, stderr = ssh.exec_command(cmd, timeout=15)
                            result = stdout.read().decode() + stderr.read().decode()
                            if not result.strip(): result = "[OK, Empty Output]"
                        except Exception as e:
                            result = f"Ошибка выполнения: {e}"
                        
                        messages.append({
                            "tool_call_id": tool_call.id,
                            "role": "tool",
                            "name": tool_call.function.name,
                            "content": result,
                        })

        except Exception as e:
            self.error_occurred.emit(f"AI Крит. Ошибка: {str(e)}")
        finally:
            if ssh: ssh.close()
