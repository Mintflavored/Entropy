import pytest
from unittest.mock import MagicMock
from core.data_loader import DataLoader

def test_data_loader_success():
    mock_ssh = MagicMock()
    mock_ssh.connect.return_value = True
    
    def mock_exec_command(cmd, timeout=None):
        if "Model name" in cmd: return True, "Intel Core"
        if "free -h" in cmd: return True, "16G"
        if "PRETTY_NAME" in cmd: return True, "Ubuntu 22.04"
        if "ps aux" in cmd: return True, "marzban Process"
        if "cat /proc/net/dev" in cmd: return True, "123456"
        if "ping" in cmd: return True, "10.5\n20.1\n"
        if "auth.log" in cmd: return True, "1.1.1.1\n2.2.2.2\n"
        return False, ""
    
    mock_ssh.exec_command.side_effect = mock_exec_command
    mock_ssh.download_file.return_value = True
    
    mock_cfg = MagicMock()
    mock_cfg.get.side_effect = lambda k: "remote.db" if k == "remote_db" else "local.db"
    
    loader = DataLoader(mock_ssh, mock_cfg, skip_discovery=False)
    loader.finished = MagicMock()
    loader.run()
    
    loader.finished.emit.assert_called_once()
    args, _ = loader.finished.emit.call_args
    assert args[0] is True
    assert "Данные обновлены" in args[1]
    
    discovery = args[2]
    assert discovery['cpu_model'] == "Intel Core"
    assert discovery['ram_total'] == "16G"
    assert discovery['os_version'] == "Ubuntu 22.04"
    assert discovery['detected_panels'] == "Marzban"
    
    security = args[3]
    assert security['raw_packets'] == "123456"
    assert security['latencies'] == [10.5, 20.1]
    assert security['ssh_probes'] == ["1.1.1.1", "2.2.2.2"]

def test_data_loader_skip_discovery():
    mock_ssh = MagicMock()
    mock_ssh.connect.return_value = True
    mock_ssh.exec_command.return_value = (True, "empty")
    mock_ssh.download_file.return_value = True
    
    mock_cfg = MagicMock()
    loader = DataLoader(mock_ssh, mock_cfg, skip_discovery=True)
    loader.finished = MagicMock()
    loader.run()
    
    loader.finished.emit.assert_called_once()
    args, _ = loader.finished.emit.call_args
    assert args[0] is True
    assert args[2] == {}  # discovery dict should be empty when skipped

def test_data_loader_ssh_fail():
    mock_ssh = MagicMock()
    mock_ssh.connect.return_value = False
    mock_cfg = MagicMock()
    loader = DataLoader(mock_ssh, mock_cfg)
    loader.finished = MagicMock()
    loader.run()
    loader.finished.emit.assert_called_once()
    args, _ = loader.finished.emit.call_args
    assert args[0] is False
    assert "SSH connection failed" in args[1]

def test_data_loader_sftp_fail():
    mock_ssh = MagicMock()
    mock_ssh.connect.return_value = True
    mock_ssh.exec_command.return_value = (False, "")
    mock_ssh.download_file.return_value = False
    mock_cfg = MagicMock()
    loader = DataLoader(mock_ssh, mock_cfg, skip_discovery=True)
    loader.finished = MagicMock()
    loader.run()
    loader.finished.emit.assert_called_once()
    args, _ = loader.finished.emit.call_args
    assert args[0] is False
    assert "SFTP download failed" in args[1]

def test_data_loader_exception():
    mock_ssh = MagicMock()
    mock_ssh.connect.side_effect = Exception("Test Error")
    mock_cfg = MagicMock()
    loader = DataLoader(mock_ssh, mock_cfg)
    loader.finished = MagicMock()
    loader.run()
    loader.finished.emit.assert_called_once()
    args, _ = loader.finished.emit.call_args
    assert args[0] is False
    assert "DataLoader error: Test Error" in args[1]
