#!/bin/bash
# =============================================================================
# Entropy AI Sandbox - cgroups Isolation Setup
# =============================================================================
# Creates an isolated environment for AI VPN experiments
# Limits: CPU 10%, RAM 100MB, separate network namespace
# =============================================================================

set -e

SANDBOX_NAME="entropy-sandbox"
CGROUP_PATH="/sys/fs/cgroup/${SANDBOX_NAME}"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Check root
if [ "$EUID" -ne 0 ]; then
    log_error "Please run as root"
    exit 1
fi

# Check cgroups v2
if [ ! -f /sys/fs/cgroup/cgroup.controllers ]; then
    log_error "cgroups v2 not available. Please enable cgroups v2."
    exit 1
fi

# Install required tools
log_info "Installing required tools (aria2, jq, mtr-tiny)..."
apt-get update -y && apt-get install -y aria2 jq mtr-tiny || log_warn "Failed to install some tools (aria2, jq, mtr-tiny)"

log_info "Setting up AI Sandbox isolation..."

# Create cgroup
if [ ! -d "$CGROUP_PATH" ]; then
    mkdir -p "$CGROUP_PATH"
    log_info "Created cgroup: $CGROUP_PATH"
else
    log_warn "cgroup already exists, reconfiguring..."
fi

# Enable controllers
echo "+cpu +memory +io" > /sys/fs/cgroup/cgroup.subtree_control 2>/dev/null || true

# CPU limit: 10% (100000 = 100%)
echo "10000 100000" > "${CGROUP_PATH}/cpu.max"
log_info "CPU limit set to 10%"

# Memory limit: 100MB
echo "104857600" > "${CGROUP_PATH}/memory.max"
echo "104857600" > "${CGROUP_PATH}/memory.swap.max" 2>/dev/null || true
log_info "Memory limit set to 100MB"

# Create network namespace for isolation
NETNS_NAME="sandbox-net"
if ! ip netns list | grep -q "$NETNS_NAME"; then
    ip netns add "$NETNS_NAME"
    log_info "Created network namespace: $NETNS_NAME"
    
    # Setup loopback in namespace
    ip netns exec "$NETNS_NAME" ip link set lo up
    
    # Create veth pair for internet access
    ip link add veth-sandbox type veth peer name veth-host
    ip link set veth-sandbox netns "$NETNS_NAME"
    
    # Configure host side
    ip addr add 10.200.200.1/24 dev veth-host
    ip link set veth-host up
    
    # Configure sandbox side
    ip netns exec "$NETNS_NAME" ip addr add 10.200.200.2/24 dev veth-sandbox
    ip netns exec "$NETNS_NAME" ip link set veth-sandbox up
    ip netns exec "$NETNS_NAME" ip route add default via 10.200.200.1
    
    # Enable NAT for sandbox internet access
    iptables -t nat -A POSTROUTING -s 10.200.200.0/24 -j MASQUERADE
    echo 1 > /proc/sys/net/ipv4/ip_forward
    
    log_info "Network namespace configured with internet access"
else
    log_warn "Network namespace already exists"
fi

# Create sandbox directory
SANDBOX_DIR="/opt/entropy-sandbox"
mkdir -p "$SANDBOX_DIR"/{config,logs,data}
log_info "Created sandbox directory: $SANDBOX_DIR"

# Save config
cat > "$SANDBOX_DIR/config/sandbox.conf" << EOF
CGROUP_PATH=$CGROUP_PATH
NETNS_NAME=$NETNS_NAME
SANDBOX_DIR=$SANDBOX_DIR
CPU_LIMIT=10
MEMORY_LIMIT_MB=100
CREATED=$(date -Iseconds)
EOF

log_info "Sandbox isolation setup complete!"
echo ""
echo "Usage:"
echo "  Run process in sandbox: ./run_in_sandbox.sh <command>"
echo "  Cleanup:                ./cleanup_sandbox.sh"
