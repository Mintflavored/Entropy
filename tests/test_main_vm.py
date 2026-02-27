import pytest
from unittest.mock import MagicMock
from src.viewmodels.MainViewModel import MainViewModel

@pytest.fixture
def mock_cfg():
    cfg = MagicMock()
    cfg.get.return_value = "default"
    cfg.ai_key = "key"
    cfg.secrets = {}
    cfg.settings = {}
    return cfg

@pytest.fixture
def mock_loader():
    return MagicMock()

@pytest.fixture
def mock_sec_engine():
    return MagicMock()

def test_main_vm_init(mock_loader, mock_sec_engine, mock_cfg):
    vm = MainViewModel(mock_loader, mock_sec_engine, mock_cfg)
    assert vm.cpu == 0.0
    assert vm.aiRiskScore == 0.0
    assert not vm.isEaiiAnalyzing

def test_main_vm_update_metrics(mock_loader, mock_sec_engine, mock_cfg):
    vm = MainViewModel(mock_loader, mock_sec_engine, mock_cfg)
    vm.cpuChanged = MagicMock()
    vm.ramChanged = MagicMock()
    vm.riskChanged = MagicMock()
    
    # Need to simulate sending a list to risk_data
    risk_data = ["HIGH", "#ff0000", 90.0]
    vm.update_metrics(cpu=50.5, ram=1024.0, pps=5000, jitter=10.0, risk_data=risk_data)
    
    assert vm.cpu == 50.5
    assert vm.ram == 1024.0
    assert vm.pps == 5000
    assert vm.jitter == 10.0
    assert vm.riskLabel == "HIGH"
    assert vm.riskColor == "#ff0000"
    assert vm.riskScore == 90.0
    
    # Histroy length was 60 max, populated with 0.0 initially, now it should append and pop
    assert vm.cpuHistory[-1] == 50.5
    assert len(vm.cpuHistory) == 60
    
    vm.cpuChanged.emit.assert_called_once()
    vm.riskChanged.emit.assert_called_once()

def test_main_vm_ai_updates(mock_loader, mock_sec_engine, mock_cfg):
    vm = MainViewModel(mock_loader, mock_sec_engine, mock_cfg)
    
    # Eaii testing
    vm.eaiiChanged = MagicMock()
    vm.set_eaii_analyzing(True)
    assert vm.isEaiiAnalyzing
    vm.eaiiChanged.emit.assert_called_once()
    
    vm.update_eaii(score=80.0, explanation="Looks OK")
    assert vm.aiRiskScore == 80.0
    assert vm.aiExplanation == "Looks OK"
    assert not vm.isEaiiAnalyzing
    assert vm.eaiiChanged.emit.call_count == 2
    
    # Interactive testing
    vm.interactiveChanged = MagicMock()
    vm.set_interactive_analyzing(True)
    assert vm.isInteractiveAnalyzing
    vm.interactiveChanged.emit.assert_called_once()
    
    vm.update_interactive_ready("Ready to rock")
    assert vm.aiInteractiveResult == "Ready to rock"
    assert not vm.isInteractiveAnalyzing

def test_main_vm_apply_settings(mock_loader, mock_sec_engine, mock_cfg):
    with pytest.MonkeyPatch.context() as m:
        import core.localization
        m.setattr(core.localization.L, "set_language", MagicMock())
        vm = MainViewModel(mock_loader, mock_sec_engine, mock_cfg)
        vm.settingsChanged = MagicMock()
        
        vm.applySettings(
            eaii_enabled=False, interval=5000, eaii_interval=10, lang="en",
            eaii_provider="test", eaii_model="testm", eaii_url="testu", eaii_key="key",
            ai_provider="test2", ai_model="testm2", ai_url="testu2", ai_key="key2",
            vps_ip="192", vps_port="222", vps_user="admin", ssh_key="/k.pem", eais_enabled=True
        )
        
        mock_cfg.set.assert_any_call("ip", "192")
        mock_cfg.set.assert_any_call("port", 222)
        mock_cfg.set.assert_any_call("eaii_enabled", False)
        
        vm.settingsChanged.emit.assert_called_once()
        mock_cfg.save.assert_called_once()
