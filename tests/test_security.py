import math
import pytest
from core.security_engine import SecurityEngine

def test_pps_calculation():
    # 1000 packets in 10s = 100 pps
    pps = SecurityEngine.calculate_pps(2000, 1000, 10000)
    assert pps == 100.0

def test_jitter_calculation():
    latencies = [10, 20, 10, 20]
    jitter = SecurityEngine.calculate_jitter(latencies)
    assert jitter > 0
    # Standard deviation of [10, 20, 10, 20] is 5.0
    assert jitter == 5.0

def test_parse_probes():
    probes = SecurityEngine.parse_probes(["1.1.1.1", "2.2.2.2", "1.1.1.1"])
    assert len(probes) == 2
    # Check that counts are accumulated
    ip_map = {p["ip"]: p["attempts"] for p in probes}
    assert ip_map["1.1.1.1"] == 2
    assert ip_map["2.2.2.2"] == 1

def test_parse_probes_empty():
    assert SecurityEngine.parse_probes([]) == []
    assert SecurityEngine.parse_probes(None) == []

def test_pps_negative_delta():
    """Negative delta (interface reset) should return 0."""
    pps = SecurityEngine.calculate_pps(100, 200, 10000)
    assert pps == 0

def test_jitter_single_value():
    """Less than 2 latencies → jitter 0."""
    assert SecurityEngine.calculate_jitter([10]) == 0.0
    assert SecurityEngine.calculate_jitter([]) == 0.0
