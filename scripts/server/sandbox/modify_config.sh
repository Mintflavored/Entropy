#!/bin/bash
# =============================================================================
# Entropy AI Sandbox - Config Modifier
# =============================================================================
# Modifies X-UI/Xray config parameters for AI experiments
# Usage: ./modify_config.sh <parameter> <value>
# =============================================================================

set -e

SANDBOX_DIR="/opt/entropy-sandbox"
SANDBOX_XUI_DIR="${SANDBOX_DIR}/x-ui"
CONFIG_FILE="${SANDBOX_XUI_DIR}/current-experiment.json"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

show_usage() {
    echo "Usage: $0 <parameter> <value>"
    echo ""
    echo "Available parameters:"
    echo "  mtu           - MTU size (1280-1500)"
    echo "  buffer_size   - Buffer size in KB"
    echo "  congestion    - Congestion algorithm (bbr, cubic)"
    echo "  fq_pacing     - BBR FQ Pacing (true/false)"
    echo "  tcp_notsent_lowat - TCP window size in bytes"
    echo "  tcp_fastopen  - TCP Fast Open (0/1/2/3)"
    echo "  tcp_ecn       - TCP ECN (0/1/2)"
    echo "  tcp_slow_start_after_idle - TCP slow start after idle (0/1)"
    echo "  dest          - REALITY destination (domain:port)"
    echo "  short_id      - REALITY short ID"
    echo "  utls          - uTLS fingerprint (chrome, firefox, randomized)"
    echo "  smux          - MUX multiplexing (true/false)"
    echo "  dns_strategy  - DNS Query Strategy (UseIP, UseIPv4)"
    echo ""
    echo "Examples:"
    echo "  $0 mtu 1400"
    echo "  $0 congestion bbr"
    echo "  $0 dest www.microsoft.com:443"
}

if [ $# -lt 2 ]; then
    show_usage
    exit 1
fi

PARAM="$1"
VALUE="$2"

# Validate parameter
case "$PARAM" in
    mtu)
        if [ "$VALUE" -lt 1280 ] || [ "$VALUE" -gt 1500 ]; then
            log_error "MTU must be between 1280 and 1500"
            exit 1
        fi
        # Apply MTU to sandbox interface
        ip netns exec sandbox-net ip link set dev veth-sandbox mtu "$VALUE"
        log_info "MTU set to $VALUE"
        ;;
    
    buffer_size)
        # Modify socket buffer in sysctl (sandbox namespace)
        ip netns exec sandbox-net sysctl -w net.core.rmem_max=$((VALUE * 1024))
        ip netns exec sandbox-net sysctl -w net.core.wmem_max=$((VALUE * 1024))
        log_info "Buffer size set to ${VALUE}KB"
        ;;
    
    congestion)
        if [[ ! "$VALUE" =~ ^(bbr|cubic|reno)$ ]]; then
            log_error "Congestion must be: bbr, cubic, or reno"
            exit 1
        fi
        ip netns exec sandbox-net sysctl -w net.ipv4.tcp_congestion_control="$VALUE"
        log_info "Congestion control set to $VALUE"
        ;;
        
    fq_pacing)
        if [ "$VALUE" == "true" ]; then
            ip netns exec sandbox-net tc qdisc replace dev veth-sandbox root fq pacing
            log_info "FQ pacing enabled"
        else
            ip netns exec sandbox-net tc qdisc replace dev veth-sandbox root pfifo_fast
            log_info "FQ pacing disabled (pfifo_fast applied)"
        fi
        ;;
        
    tcp_notsent_lowat)
        ip netns exec sandbox-net sysctl -w net.ipv4.tcp_notsent_lowat="$VALUE"
        log_info "tcp_notsent_lowat set to $VALUE"
        ;;
        
    tcp_fastopen)
        ip netns exec sandbox-net sysctl -w net.ipv4.tcp_fastopen="$VALUE"
        log_info "tcp_fastopen set to $VALUE"
        ;;
        
    tcp_ecn)
        ip netns exec sandbox-net sysctl -w net.ipv4.tcp_ecn="$VALUE"
        log_info "tcp_ecn set to $VALUE"
        ;;
        
    tcp_slow_start_after_idle)
        ip netns exec sandbox-net sysctl -w net.ipv4.tcp_slow_start_after_idle="$VALUE"
        log_info "tcp_slow_start_after_idle set to $VALUE"
        ;;
    
    dest)
        # Modify REALITY destination in config
        if [ -f "$CONFIG_FILE" ]; then
            # Using jq to modify JSON
            jq --arg dest "$VALUE" \
               '.inbounds[0].streamSettings.realitySettings.dest = $dest' \
               "$CONFIG_FILE" > "${CONFIG_FILE}.tmp" && mv "${CONFIG_FILE}.tmp" "$CONFIG_FILE"
            log_info "REALITY destination set to $VALUE"
        else
            log_error "Config file not found: $CONFIG_FILE"
            exit 1
        fi
        ;;
    
    short_id)
        if [ -f "$CONFIG_FILE" ]; then
            jq --arg sid "$VALUE" \
               '.inbounds[0].streamSettings.realitySettings.shortIds = [$sid]' \
               "$CONFIG_FILE" > "${CONFIG_FILE}.tmp" && mv "${CONFIG_FILE}.tmp" "$CONFIG_FILE"
            log_info "REALITY short_id set to $VALUE"
        fi
        ;;
        
    utls)
        if [ -f "$CONFIG_FILE" ]; then
            jq --arg fp "$VALUE" \
               '.inbounds[0].streamSettings.realitySettings.fingerprint = $fp' \
               "$CONFIG_FILE" > "${CONFIG_FILE}.tmp" && mv "${CONFIG_FILE}.tmp" "$CONFIG_FILE"
            log_info "uTLS fingerprint set to $VALUE"
        fi
        ;;
        
    smux)
        if [ -f "$CONFIG_FILE" ]; then
            if [ "$VALUE" == "true" ]; then
                jq '.inbounds[0].streamSettings.mux.enabled = true' "$CONFIG_FILE" > "${CONFIG_FILE}.tmp"
            else
                jq '.inbounds[0].streamSettings.mux.enabled = false' "$CONFIG_FILE" > "${CONFIG_FILE}.tmp"
            fi
            mv "${CONFIG_FILE}.tmp" "$CONFIG_FILE"
            log_info "S-Mux enabled: $VALUE"
        fi
        ;;
        
    dns_strategy)
        if [ -f "$CONFIG_FILE" ]; then
            jq --arg qstrat "$VALUE" \
               '.dns.queryStrategy = $qstrat' \
               "$CONFIG_FILE" > "${CONFIG_FILE}.tmp" && mv "${CONFIG_FILE}.tmp" "$CONFIG_FILE"
            log_info "DNS queryStrategy set to $VALUE"
        fi
        ;;
    
    *)
        log_error "Unknown parameter: $PARAM"
        show_usage
        exit 1
        ;;
esac

# Log the change
echo "$(date -Iseconds) | $PARAM = $VALUE" >> "${SANDBOX_DIR}/logs/config-changes.log"
