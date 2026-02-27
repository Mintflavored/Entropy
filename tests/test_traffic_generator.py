import pytest
from unittest.mock import MagicMock
from ai.traffic_generator import RemoteTrafficGenerator, trimmed_mean, TrafficTestResult

def test_trimmed_mean():
    assert trimmed_mean([1, 2, 3, 4, 100], trim_pct=0.2) == pytest.approx(3.0)  # removes 1 and 100
    assert trimmed_mean([], trim_pct=0.2) == 0.0
    assert trimmed_mean([5], trim_pct=0.2) == 5.0
    assert trimmed_mean([5, 10], trim_pct=0.2) == 7.5

@pytest.fixture
def mock_ssh():
    ssh = MagicMock()
    return ssh

@pytest.fixture
def generator(mock_ssh):
    return RemoteTrafficGenerator(mock_ssh)

def test_connection_timing(generator, mock_ssh):
    def mock_exec(cmd, *args, **kwargs):
        if cmd.startswith("ping"):
            return (True, "1 packets transmitted, 1 received, 0% packet loss, time 0ms\nrtt min/avg/max/mdev = 10.000/10.000/10.000/0.000 ms")
        return (True, "0.100|0.200|0.300")
        
    mock_ssh.exec_command.side_effect = mock_exec
    
    res = generator.test_connection_timing()
    assert res["latency"].success
    assert res["latency"].value == 300.0  # ms
    assert res["tcp_handshake"].value == 100.0
    assert res["tls_handshake"].value == 200.0

def test_connection_timing_fail(generator, mock_ssh):
    def mock_exec_fail(cmd, *args, **kwargs):
        if cmd.startswith("ping"):
            return (True, "1 packets transmitted, 1 received, 0% packet loss, time 0ms")
        return (False, "")
        
    mock_ssh.exec_command.side_effect = mock_exec_fail
    
    res = generator.test_connection_timing()
    assert not res["latency"].success

def test_dns(generator, mock_ssh):
    mock_ssh.exec_command.return_value = (True, "Query time: 15 msec")
    res = generator.test_dns()
    assert res.success
    assert res.value == 15.0

def test_dns_fail(generator, mock_ssh):
    mock_ssh.exec_command.return_value = (True, "Timeout no answer")
    res = generator.test_dns()
    assert not res.success

def test_jitter(generator, mock_ssh):
    mock_ssh.exec_command.return_value = (True, "time=10.0\ntime=20.0\ntime=10.0\ntime=20.0")
    res = generator.test_jitter()
    assert res.success
    # avg = 15, abs: 5, 5, 5, 5, sum 20, avg jitter 5
    assert res.value == 5.0

def test_packet_loss(generator, mock_ssh):
    mock_ssh.exec_command.return_value = (True, "15% packet loss")
    res = generator.test_packet_loss()
    assert res.success
    assert res.value == 15.0

def test_download_and_stability_aria2c(generator, mock_ssh):
    # Output simulates aria2c parsing
    mock_ssh.exec_command.return_value = (True, "DL:1.0MiB\nDL:2.0MiB")
    res = generator.test_download_and_stability()
    assert res["download"].success
    # 1.0 MiB = 8 Mbps, 2.0 MiB = 16 Mbps
    # average of 8, 16 -> trimmed_mean -> 12 Mbps
    assert res["download"].value > 0
    assert res["stability"].success

def test_download_and_stability_wget_fallback(generator, mock_ssh):
    mock_ssh.exec_command.side_effect = [
        (False, ""),  # aria fails
        (True, "100%[=====================>] 10MB  (5.0 MB/s)  in 2s") # wget success
    ]
    res = generator.test_download_and_stability()
    assert res["download"].success
    # 5.0 MB/s = 40 Mbps
    assert res["download"].value == 40.0
    assert not res["stability"].success # False but contains metric (or 0)

def test_upload_speed(generator, mock_ssh):
    mock_ssh.exec_command.return_value = (True, "1250000") # 1.25 MB/s
    res = generator.test_upload_speed()
    assert res.success
    assert res.value == 10.0 # (1250000 * 8) / 1000000

def test_load_telemetry(generator, mock_ssh):
    # idle -> load
    mock_ssh.exec_command.side_effect = [
        (True, "time=10.0\ntime=10.0"), # idle
        (True, "time=50.0\ntime=50.0\nretrans:0/5\nretrans:2\nbacklog 1000b 12p")  # load
    ]
    res = generator.test_load_telemetry()
    assert res["bufferbloat"].success
    assert res["bufferbloat"].value == 40.0 # 50 - 10
    assert res["tcp_retrans"].success
    assert res["tcp_retrans"].value == 7.0 # 5 + 2
    assert res["tc_backlog"].success
    assert res["tc_backlog"].value == 12.0

def test_mtr(generator, mock_ssh):
    mock_ssh.exec_command.return_value = (True, "HOST: node\n  1.|-- 10.0.0.1  0.0%  10  200.5\n  2.|-- 10.0.0.2  0.0%  10  10.0\n")
    res = generator.test_mtr()
    assert res.success
    assert res.value == 1.0 # 200.5 > 150.0 gets anomalous

def test_xray_stats(generator, mock_ssh):
    mock_ssh.exec_command.return_value = (True, '{"stat": [{"name": "inbound>>>api>>>drop", "value": "5"}, {"name": "outbound>>>app>>>error", "value": "2"}]}')
    res = generator.test_xray_stats()
    assert res.success
    assert res.value == 7.0

def test_run_full_test(generator):
    generator.test_connection_timing = MagicMock(return_value={"latency": TrafficTestResult("l", True, 10.0, "ms", 0)})
    generator.test_dns = MagicMock(return_value=TrafficTestResult("d", True, 5.0, "ms", 0))
    generator.test_jitter = MagicMock(return_value=TrafficTestResult("j", True, 1.0, "ms", 0))
    generator.test_packet_loss = MagicMock(return_value=TrafficTestResult("p", True, 0.0, "%", 0))
    generator.test_download_and_stability = MagicMock(return_value={"download": TrafficTestResult("dl", True, 100, "Mbps", 0), "stability": TrafficTestResult("s", True, 0, "%cv", 0)})
    generator.test_upload_speed = MagicMock(return_value=TrafficTestResult("up", True, 50, "Mbps", 0))
    generator.test_load_telemetry = MagicMock(return_value={
        "bufferbloat": TrafficTestResult("b", True, 5.0, "ms", 0),
        "tcp_retrans": TrafficTestResult("tr", True, 0.0, "packets", 0),
        "tc_backlog": TrafficTestResult("tb", True, 2.0, "packets", 0)
    })
    generator.test_mtr = MagicMock(return_value=TrafficTestResult("mtr", True, 0.0, "bool", 0))
    generator.test_xray_stats = MagicMock(return_value=TrafficTestResult("xs", True, 0.0, "count", 0))
    generator.ssh.exec_command.return_value = (True, "1 packets transmitted, 1 received, 0% packet loss")
    
    results = generator.run_full_test()
    summary = generator.get_summary(results)
    
    assert summary["latency_ms"] == 10.0
    assert summary["dns_ms"] == 5.0
    assert summary["download_mbps"] == 100.0
    assert summary["upload_mbps"] == 50.0
    assert summary["tc_backlog"] == 2.0
