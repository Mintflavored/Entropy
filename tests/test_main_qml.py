import pytest
from unittest.mock import MagicMock, patch
import pandas as pd
from src.main_qml import DataBridge

@pytest.fixture
def mock_cfg():
    cfg = MagicMock()
    def mock_get(key, default=None):
        return {
            "ip": "1.2.3.4",
            "sync_interval_ms": 1000,
            "eaii_enabled": True,
            "eaii_interval_min": 1,
            "local_db": "dummy.db"
        }.get(key, default)
    cfg.get.side_effect = mock_get
    return cfg

@pytest.fixture
def mock_vm():
    vm = MagicMock()
    return vm

@pytest.fixture
def mock_ssh():
    ssh = MagicMock()
    return ssh

@patch("src.main_qml.QTimer")
def test_databridge_init(mock_qtimer, mock_cfg, mock_vm, mock_ssh):
    bridge = DataBridge(mock_cfg, mock_vm, mock_ssh)
    
    assert bridge.interval == 1000
    assert not bridge._discovery_done
    
    # Check that signals are connected
    mock_vm.manualScanRequested.connect.assert_called_once()
    assert bridge.timer.timeout.connect.called

@patch("src.main_qml.QTimer")
@patch("src.main_qml.DataLoader")
def test_databridge_start_and_request(MockLoader, mock_qtimer, mock_cfg, mock_vm, mock_ssh):
    bridge = DataBridge(mock_cfg, mock_vm, mock_ssh)
    mock_loader_instance = MockLoader.return_value
    mock_loader_instance.isRunning.return_value = False
    
    bridge.start()
    
    # Check timers started
    bridge.timer.start.assert_any_call(1000)
    bridge._eaii_timer.start.assert_any_call(60000)
    
    # Check exact loader call args
    
    assert bridge._last_server_ip == "1.2.3.4"

@patch("src.main_qml.QTimer")
@patch("src.main_qml.EAIIWorker")
def test_databridge_run_eaii(MockWorker, mock_qtimer, mock_cfg, mock_vm, mock_ssh):
    bridge = DataBridge(mock_cfg, mock_vm, mock_ssh)
    bridge.run_eaii()
    
    # Worker should be instantiated and started
    mock_worker_instance = MockWorker.return_value
    mock_worker_instance.start.assert_called_once()
    mock_vm.set_eaii_analyzing.assert_called_with(True)
    
    # Check callback
    bridge.on_eaii_ready(80.5, "test info")
    mock_vm.update_eaii.assert_called_with(80.5, "test info")

@patch("src.main_qml.QTimer")
@patch("src.main_qml.AIAnalyzer")
def test_databridge_run_interactive(MockAnalyzer, mock_qtimer, mock_cfg, mock_vm, mock_ssh):
    bridge = DataBridge(mock_cfg, mock_vm, mock_ssh)
    bridge.run_interactive_analysis()
    
    mock_analyzer_instance = MockAnalyzer.return_value
    mock_analyzer_instance.start.assert_called_once()
    mock_vm.set_interactive_analyzing.assert_called_with(True)
    
    bridge.on_interactive_ready("success result")
    mock_vm.update_interactive_ready.assert_called_with("success result")
    
    bridge.on_interactive_error("fail error")
    mock_vm.update_interactive_ready.assert_called_with("ERROR: fail error")

@patch("src.main_qml.QTimer")
@patch("src.main_qml.sqlite3.connect")
@patch("src.main_qml.pd.read_sql")
@patch("src.main_qml.SecurityEngine.calculate_pps", return_value=100)
@patch("src.main_qml.SecurityEngine.calculate_jitter", return_value=5.0)
@patch("src.main_qml.SecurityEngine.parse_probes", return_value=["1.1.1.1"])
@patch("src.main_qml.SecurityEngine.calculate_risk", return_value=["LOW", "#0f0", 5.0])
def test_databridge_on_data_ready_success(
    mock_risk, mock_parse_probes, mock_jitter, mock_pps,
    mock_read_sql, mock_connect, mock_qtimer, mock_cfg, mock_vm, mock_ssh
):
    bridge = DataBridge(mock_cfg, mock_vm, mock_ssh)
    bridge.last_raw_packets = "100" # to trigger pps calc
    
    # Mocking DB data
    df_sys = pd.DataFrame([{"cpu": 10.0, "ram": 512.0}])
    df_users = pd.DataFrame([{"email": "test@test.com", "d": 10.0, "u": 5.0}])
    mock_read_sql.side_effect = [df_sys, df_users]
    
    bridge.on_data_ready(
        True, "success", {"os_version": "linux"},
        {"raw_packets": "200", "latencies": [1,2], "ssh_probes": ["1.1.1.1"]}
    )
    
    assert bridge.discovery_data == {"os_version": "linux"}
    assert bridge._discovery_done is True
    assert bridge.last_raw_packets == "200"
    
    mock_pps.assert_called_with("200", "100", 1000)
    mock_vm.update_metrics.assert_called_with(10.0, 512.0, 100, 5.0, ["LOW", "#0f0", 5.0])
    
    users_list_arg = mock_vm.update_users.call_args[0][0]
    assert len(users_list_arg) == 1
    assert users_list_arg[0]["user"] == "test@test.com"
    assert users_list_arg[0]["traffic"] == "15.0 MB"
    
    mock_vm.update_probes.assert_called_with(["1.1.1.1"])
    
    # check that EAII was run automatically since _first_run was True
    assert not bridge._first_run
