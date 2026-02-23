#!/bin/bash
# =============================================================================
# Entropy AI Sandbox - Run Process in Sandbox
# =============================================================================
# Executes a command inside the isolated sandbox environment
# =============================================================================

set -e

SANDBOX_DIR="/opt/entropy-sandbox"
CONFIG_FILE="$SANDBOX_DIR/config/sandbox.conf"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m'

if [ ! -f "$CONFIG_FILE" ]; then
    echo -e "${RED}[ERROR]${NC} Sandbox not initialized. Run setup_cgroups.sh first."
    exit 1
fi

source "$CONFIG_FILE"

if [ $# -eq 0 ]; then
    echo "Usage: $0 <command> [args...]"
    echo "Example: $0 curl https://google.com"
    exit 1
fi

# Add current process to sandbox cgroup
echo $$ > "${CGROUP_PATH}/cgroup.procs"

# Execute command in network namespace
exec ip netns exec "$NETNS_NAME" "$@"
