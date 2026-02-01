import math
import pytest
from core.security_engine import SecurityEngine

def test_smart_risk_low():
    label, color, score = SecurityEngine.calculate_risk(10, 5, 0)
    assert score < 15
    assert label == "LOW"
    assert color == "#00ff00"

def test_smart_risk_high():
    # 500 PPS + 40ms Jitter should be high/critical
    label, color, score = SecurityEngine.calculate_risk(500, 40, 0)
    assert score > 40
    assert label in ["HIGH", "CRITICAL"]

def test_smart_risk_with_brute_force():
    # High brute force should push risk up
    label_no_bf, _, score_no_bf = SecurityEngine.calculate_risk(50, 5, 0)
    label_bf, _, score_bf = SecurityEngine.calculate_risk(50, 5, 10) # 10 attempts
    
    assert score_bf > score_no_bf
    assert score_bf >= score_no_bf + 30 # 30 is the weight for 10 attempts (min(100, 10*10) * 0.3)

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
