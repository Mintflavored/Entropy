import pytest
from unittest.mock import MagicMock, patch
from core.ssh_manager import SSHConnectionManager
import socket

@pytest.fixture
def mock_cfg():
    cfg = MagicMock()
    def mock_get(key):
        return {
            "ip": "1.2.3.4",
            "port": 22,
            "user": "root",
            "key_path": "dummy/path.pem"
        }.get(key)
    cfg.get.side_effect = mock_get
    return cfg

def test_ssh_manager_init(mock_cfg):
    manager = SSHConnectionManager(mock_cfg)
    assert not manager.is_connected()
    assert manager._server_key == "1.2.3.4:22"

@patch("core.ssh_manager.paramiko.SSHClient")
@patch("core.ssh_manager.os.path.exists")
def test_ssh_connect_success(mock_exists, MockSSHClient, mock_cfg):
    mock_exists.return_value = True
    mock_client_instance = MockSSHClient.return_value
    mock_transport = MagicMock()
    mock_client_instance.get_transport.return_value = mock_transport
    
    manager = SSHConnectionManager(mock_cfg)
    result = manager.connect()
    
    assert result is True
    assert manager.is_connected()
    mock_client_instance.connect.assert_called_once()
    mock_transport.set_keepalive.assert_called_with(30)

@patch("core.ssh_manager.paramiko.SSHClient")
@patch("core.ssh_manager.os.path.exists")
def test_ssh_connect_key_not_found(mock_exists, MockSSHClient, mock_cfg):
    mock_exists.return_value = False
    manager = SSHConnectionManager(mock_cfg)
    result = manager.connect()
    assert result is False
    assert not manager.is_connected()

@patch("core.ssh_manager.paramiko.SSHClient")
@patch("core.ssh_manager.os.path.exists")
def test_ssh_connect_error(mock_exists, MockSSHClient, mock_cfg):
    mock_exists.return_value = True
    mock_client_instance = MockSSHClient.return_value
    mock_client_instance.connect.side_effect = Exception("Connection refused")
    manager = SSHConnectionManager(mock_cfg)
    result = manager.connect()
    assert result is False
    assert not manager.is_connected()

def test_ssh_should_reconnect_logic(mock_cfg):
    manager = SSHConnectionManager(mock_cfg)
    assert manager._should_reconnect() is True
    
    manager._connected = True
    manager._client = MagicMock()
    manager._last_server_key = "1.2.3.4:22"
    
    mock_transport = MagicMock()
    mock_transport.is_active.return_value = True
    manager._client.get_transport.return_value = mock_transport
    
    assert manager._should_reconnect() is False
    
    # Change server key
    manager._last_server_key = "different"
    assert manager._should_reconnect() is True

def test_ssh_exec_command_no_client(mock_cfg):
    manager = SSHConnectionManager(mock_cfg)
    manager.connect = MagicMock(return_value=False)
    success, output = manager.exec_command("ls")
    assert not success
    assert output == "Connection failed"

def test_ssh_exec_command_success(mock_cfg):
    manager = SSHConnectionManager(mock_cfg)
    manager.connect = MagicMock(return_value=True)
    manager._client = MagicMock()
    
    mock_stdout = MagicMock()
    mock_stdout.read.return_value = b"success output\n"
    mock_stderr = MagicMock()
    mock_stderr.read.return_value = b""
    manager._client.exec_command.return_value = (None, mock_stdout, mock_stderr)
    
    success, output = manager.exec_command("ls")
    assert success is True
    assert output == "success output"
    
def test_ssh_exec_command_stderr(mock_cfg):
    manager = SSHConnectionManager(mock_cfg)
    manager.connect = MagicMock(return_value=True)
    manager._client = MagicMock()
    
    mock_stdout = MagicMock()
    mock_stdout.read.return_value = b""
    mock_stderr = MagicMock()
    mock_stderr.read.return_value = b"error output\n"
    manager._client.exec_command.return_value = (None, mock_stdout, mock_stderr)
    
    success, output = manager.exec_command("ls")
    assert success is True
    assert output == "error output"

def test_ssh_exec_command_timeout(mock_cfg):
    manager = SSHConnectionManager(mock_cfg)
    manager.connect = MagicMock(return_value=True)
    manager._client = MagicMock()
    manager._client.exec_command.side_effect = socket.timeout("timeout")
    
    success, output = manager.exec_command("ls")
    assert success is False
    assert "Command timed out" in output

def test_ssh_exec_command_exception(mock_cfg):
    manager = SSHConnectionManager(mock_cfg)
    manager.connect = MagicMock(return_value=True)
    manager._client = MagicMock()
    manager._client.exec_command.side_effect = Exception("Channel Error")
    
    success, output = manager.exec_command("ls")
    assert success is False
    assert "Channel Error" in output

def test_ssh_get_sftp(mock_cfg):
    manager = SSHConnectionManager(mock_cfg)
    manager.connect = MagicMock(return_value=True)
    manager._client = MagicMock()
    mock_sftp = MagicMock()
    manager._client.open_sftp.return_value = mock_sftp
    
    sftp = manager.get_sftp()
    assert sftp == mock_sftp
    
    # call again, should return existing and check stat
    mock_sftp.stat.return_value = True
    sftp2 = manager.get_sftp()
    assert sftp2 == mock_sftp
    manager._client.open_sftp.assert_called_once()

def test_ssh_download_file(mock_cfg):
    manager = SSHConnectionManager(mock_cfg)
    mock_sftp = MagicMock()
    manager.get_sftp = MagicMock(return_value=mock_sftp)
    
    result = manager.download_file("remote", "local")
    assert result is True
    mock_sftp.get.assert_called_with("remote", "local")

def test_ssh_download_file_error(mock_cfg):
    manager = SSHConnectionManager(mock_cfg)
    mock_sftp = MagicMock()
    mock_sftp.get.side_effect = Exception("transfer failed")
    manager.get_sftp = MagicMock(return_value=mock_sftp)
    assert manager.download_file("remote", "local") is False

def test_ssh_close(mock_cfg):
    manager = SSHConnectionManager(mock_cfg)
    mock_client = MagicMock()
    mock_sftp = MagicMock()
    manager._client = mock_client
    manager._sftp = mock_sftp
    manager._connected = True
    manager.close()
    mock_sftp.close.assert_called_once()
    mock_client.close.assert_called_once()
    assert manager._client is None
    assert manager._sftp is None
    assert not manager.is_connected()
