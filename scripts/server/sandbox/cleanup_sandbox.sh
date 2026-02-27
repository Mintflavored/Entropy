#!/bin/bash
# =============================================================================
# Entropy AI Sandbox - Cleanup
# =============================================================================
# Removes sandbox cgroup and network namespace
# =============================================================================

set -e

SANDBOX_NAME="entropy-sandbox"
CGROUP_PATH="/sys/fs/cgroup/${SANDBOX_NAME}"
NETNS_NAME="sandbox-net"
SANDBOX_DIR="/opt/entropy-sandbox"

RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m'

log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }

# Check root
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}[ERROR]${NC} Please run as root"
    exit 1
fi

log_info "Cleaning up AI Sandbox..."

# Kill processes in cgroup
if [ -d "$CGROUP_PATH" ]; then
    if [ -f "${CGROUP_PATH}/cgroup.procs" ]; then
        for pid in $(cat "${CGROUP_PATH}/cgroup.procs" 2>/dev/null); do
            kill -9 "$pid" 2>/dev/null || true
        done
    fi
    rmdir "$CGROUP_PATH" 2>/dev/null || true
    log_info "Removed cgroup"
fi

# Remove network namespace
if ip netns list | grep -q "$NETNS_NAME"; then
    ip netns delete "$NETNS_NAME"
    log_info "Removed network namespace"
fi

# Remove veth interface
ip link delete veth-host 2>/dev/null || true

# Remove NAT rule
iptables -t nat -D POSTROUTING -s 10.200.200.0/24 -j MASQUERADE 2>/dev/null || true

log_info "Sandbox cleanup complete!"
