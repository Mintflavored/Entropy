import pytest
from unittest.mock import MagicMock, patch
import json
from ai.bridge import AIAnalyzer, EAIIWorker

@pytest.fixture
def mock_cfg():
    cfg = MagicMock()
    cfg.ai_key = "test_key"
    def mock_get(key, default=None):
        return {
            "ai_provider": "openai_compatible",
            "ai_model": "test-model",
            "ai_base_url": "http://test",
            "ai_tool_limit": 1,
            "ip": "1.2.3.4",
            "port": 22,
            "user": "root",
            "key_path": "dummy.pem",
            "eaii_key": "eaii_key",
            "eaii_provider": "openai_compatible",
            "eaii_model": "test-eaii",
            "eaii_base_url": "http://eaii",
            "language": "ru"
        }.get(key, default)
    cfg.get.side_effect = mock_get
    return cfg

@patch("ai.adapters.openai_adapter.OpenAIAdapter")
def test_ai_analyzer_no_key(MockAdapter, mock_cfg):
    mock_cfg.ai_key = None
    analyzer = AIAnalyzer(mock_cfg, {}, {})
    analyzer.error_occurred = MagicMock()
    analyzer.run()
    analyzer.error_occurred.emit.assert_called_once()
    assert "API Key не найден" in analyzer.error_occurred.emit.call_args[0][0]

@patch("ai.adapters.openai_adapter.OpenAIAdapter")
def test_ai_analyzer_success_no_tools(MockAdapter, mock_cfg):
    mock_adapter_instance = MockAdapter.return_value
    mock_response = MagicMock()
    mock_response.tool_calls = None
    mock_response.content = "Analysis Result"
    mock_adapter_instance.generate.return_value = mock_response

    analyzer = AIAnalyzer(mock_cfg, {"cpu": 50}, {"os": "linux"})
    analyzer.result_ready = MagicMock()
    analyzer.run()

    analyzer.result_ready.emit.assert_called_once_with("Analysis Result")

@patch("ai.bridge.paramiko.SSHClient")
@patch("ai.adapters.openai_adapter.OpenAIAdapter")
def test_ai_analyzer_with_tools_and_limit(MockAdapter, MockSSH, mock_cfg):
    mock_adapter_instance = MockAdapter.return_value
    
    # First response uses a tool, second response gives final answer
    tool_call = MagicMock()
    tool_call.function.name = "execute_ssh_command"
    tool_call.function.arguments = json.dumps({"command": "ls"})
    tool_call.id = "call_123"
    
    first_response = MagicMock()
    first_response.tool_calls = [tool_call]
    first_response.content = "Checking..."
    
    second_response = MagicMock()
    second_response.tool_calls = None
    second_response.content = "Final Analysis"
    
    mock_adapter_instance.generate.side_effect = [first_response, second_response]
    
    mock_ssh_instance = MockSSH.return_value
    mock_stdout = MagicMock()
    mock_stdout.read.return_value = b"file1\nfile2"
    mock_stderr = MagicMock()
    mock_stderr.read.return_value = b""
    mock_ssh_instance.exec_command.return_value = (None, mock_stdout, mock_stderr)
    
    analyzer = AIAnalyzer(mock_cfg, {}, {})
    analyzer.result_ready = MagicMock()
    analyzer.run()
    
    analyzer.result_ready.emit.assert_called_once_with("Final Analysis")
    mock_ssh_instance.connect.assert_called_once()
    mock_ssh_instance.exec_command.assert_called_once_with("ls", timeout=15)
    mock_ssh_instance.close.assert_called_once()

@patch("ai.adapters.openai_adapter.OpenAIAdapter")
def test_eaii_worker_success(MockAdapter, mock_cfg):
    mock_adapter_instance = MockAdapter.return_value
    mock_response = MagicMock()
    mock_response.content = json.dumps({"score": 85.5, "explanation": "Looks good"})
    mock_adapter_instance.generate.return_value = mock_response

    worker = EAIIWorker(mock_cfg, {"cpu": 10}, {"type": "vpn"})
    worker.analysis_ready = MagicMock()
    worker.run()

    worker.analysis_ready.emit.assert_called_once_with(85.5, "Looks good")

@patch("ai.adapters.openai_adapter.OpenAIAdapter")
def test_eaii_worker_no_key(MockAdapter, mock_cfg):
    mock_cfg.get.side_effect = lambda k, d=None: None if k == "eaii_key" else d
    mock_cfg.ai_key = None
    
    worker = EAIIWorker(mock_cfg, {}, {})
    worker.analysis_ready = MagicMock()
    worker.run()
    
    # Should just return without emitting
    worker.analysis_ready.emit.assert_not_called()

def test_eaii_worker_exception(mock_cfg):
    worker = EAIIWorker(mock_cfg, {}, {})
    worker.error_occurred = MagicMock()
    
    with patch("ai.adapters.openai_adapter.OpenAIAdapter", side_effect=Exception("API Error")):
        worker.run()
        
    worker.error_occurred.emit.assert_called_once_with("API Error")
