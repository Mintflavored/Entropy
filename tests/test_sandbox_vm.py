import pytest
from unittest.mock import MagicMock
from src.viewmodels.SandboxViewModel import SandboxViewModel
import collections

@pytest.fixture
def mock_cfg():
    cfg = MagicMock()
    def mock_get(key, default=None):
        return {"eais_enabled": True, "ai_key": "test"}.get(key, default)
    cfg.get.side_effect = mock_get
    cfg.ai_key = "test"
    return cfg

@pytest.fixture
def mock_ssh():
    return MagicMock()

def test_sandbox_vm_init(mock_ssh, mock_cfg):
    vm = SandboxViewModel(ssh_manager=mock_ssh, config_manager=mock_cfg)
    assert not vm.isRunning
    assert vm.statusText == "Готово к запуску"
    assert vm.progressPercent == 0.0

def test_sandbox_vm_start_optimization_no_eais(mock_ssh):
    cfg = MagicMock()
    cfg.get.return_value = False
    vm = SandboxViewModel(ssh_manager=mock_ssh, config_manager=cfg)
    vm.statusChanged = MagicMock()
    
    vm.startOptimization()
    assert not vm.isRunning
    assert "EAIS отключён" in vm.error
    vm.statusChanged.emit.assert_called_once()

def test_sandbox_vm_start_optimization_no_ssh(mock_cfg):
    vm = SandboxViewModel(ssh_manager=None, config_manager=mock_cfg)
    vm.statusChanged = MagicMock()
    
    vm.startOptimization()
    assert not vm.isRunning
    assert "SSH не подключён" in vm.error

def test_sandbox_vm_start_optimization_success(mock_cfg, mock_ssh):
    vm = SandboxViewModel(ssh_manager=mock_ssh, config_manager=mock_cfg)
    vm.statusChanged = MagicMock()
    
    # Needs to mock QThread start
    with pytest.MonkeyPatch.context() as m:
        m.setattr("src.viewmodels.SandboxViewModel.SandboxWorker.start", MagicMock())
        vm.startOptimization()
        assert vm.isRunning
        assert vm._worker is not None
        assert "Инициализация" in vm.statusText

def test_sandbox_vm_callbacks(mock_cfg, mock_ssh):
    vm = SandboxViewModel(ssh_manager=mock_ssh, config_manager=mock_cfg)
    vm.progressChanged = MagicMock()
    vm.statusChanged = MagicMock()
    vm.resultsChanged = MagicMock()
    
    vm._on_progress(1, 10)
    assert vm.currentExperiment == 1
    assert vm.totalExperiments == 10
    assert vm.progressPercent == 10.0
    vm.progressChanged.emit.assert_called_once()
    
    vm._on_status("Testing")
    assert vm.statusText == "Testing"
    vm.statusChanged.emit.assert_called_once()
    
    vm._is_running = True
    vm._worker = MagicMock() # mock worker to test cleanup
    
    vm._on_finished({
        "score": 90, "baseline_score": 50, "improvement_pct": 80.0,
        "config": {"mtu": 1400}, "ai_reasoning": "Because"
    })
    
    assert not vm.isRunning
    assert vm.bestScore == 90
    assert vm.improvement == 80.0
    assert vm.aiReasoning == "Because"
    assert "1400" in vm.bestConfigJson
    vm.statusChanged.emit.assert_called()
    vm.resultsChanged.emit.assert_called()
    assert vm._worker is None
    
    # Test error callback
    vm._is_running = True
    vm._worker = MagicMock()
    vm._on_error("Failed")
    assert not vm.isRunning
    assert vm.error == "Failed"
    assert vm._worker is None

def test_sandbox_vm_stop(mock_cfg, mock_ssh):
    vm = SandboxViewModel(ssh_manager=mock_ssh, config_manager=mock_cfg)
    vm.statusChanged = MagicMock()
    mock_agent_instance = MagicMock()
    vm._agent = mock_agent_instance
    vm._is_running = True
    vm.stopOptimization()
    
    assert not vm.isRunning
    mock_agent_instance.stop.assert_called_once()
    assert vm._agent is None
    vm.statusChanged.emit.assert_called_once()
