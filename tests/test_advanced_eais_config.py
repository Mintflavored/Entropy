import pytest
from unittest.mock import MagicMock
from ai.sandbox_agent import EAISAgent

@pytest.fixture
def mock_ssh():
    ssh = MagicMock()
    ssh.exec_command.return_value = (True, "")
    return ssh

@pytest.fixture
def agent(mock_ssh):
    cfg = MagicMock()
    return EAISAgent(mock_ssh, cfg)

def test_apply_advanced_config(agent, mock_ssh):
    """
    Test that the agent properly formats the ssh command for new parameters
    """
    advanced_config = {
        "fq_pacing": "true",
        "tcp_notsent_lowat": 131072,
        "tcp_fastopen": 3,
        "tcp_ecn": 1,
        "tcp_slow_start_after_idle": 0,
        "utls": "randomized",
        "smux": "true",
        "dns_strategy": "UseIPv4"
    }
    
    success = agent.apply_config(advanced_config)
    assert success is True
    
    # Check that modify_config.sh was called for each parameter
    calls = mock_ssh.exec_command.call_args_list
    assert len(calls) == 8
    
    commands_executed = [call[0][0] for call in calls]
    
    assert any("modify_config.sh fq_pacing true" in cmd for cmd in commands_executed)
    assert any("modify_config.sh tcp_notsent_lowat 131072" in cmd for cmd in commands_executed)
    assert any("modify_config.sh tcp_fastopen 3" in cmd for cmd in commands_executed)
    assert any("modify_config.sh tcp_ecn 1" in cmd for cmd in commands_executed)
    assert any("modify_config.sh tcp_slow_start_after_idle 0" in cmd for cmd in commands_executed)
    assert any("modify_config.sh utls randomized" in cmd for cmd in commands_executed)
    assert any("modify_config.sh smux true" in cmd for cmd in commands_executed)
    assert any("modify_config.sh dns_strategy UseIPv4" in cmd for cmd in commands_executed)

def test_apply_advanced_config_failure(agent, mock_ssh):
    """
    Test that if one parameter fails, the process handles it by returning False
    """
    advanced_config = {
        "smux": "true",
        "fq_pacing": "true"
    }
    
    # First command fails, second succeeds
    mock_ssh.exec_command.side_effect = [(False, "Permission denied"), (True, "")]
    
    success = agent.apply_config(advanced_config)
    assert success is False
    
    # execution should stop at the first failure
    assert mock_ssh.exec_command.call_count == 1
