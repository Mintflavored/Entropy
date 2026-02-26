#!/bin/bash
# =============================================================================
# Entropy AI Sandbox - X-UI Instance Creator
# =============================================================================
# Creates a sandbox instance of X-UI for AI experimentation
# Runs on a different port, isolated from production
# =============================================================================

set -e

SANDBOX_DIR="/opt/entropy-sandbox"
XUI_DIR="/usr/local/x-ui"
SANDBOX_XUI_DIR="${SANDBOX_DIR}/x-ui"
SANDBOX_PORT=54322  # Different from production (default 54321)
SANDBOX_PANEL_PORT=2054  # Different from production (default 2053)

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

# Check X-UI exists
if [ ! -d "$XUI_DIR" ]; then
    log_error "X-UI not found at $XUI_DIR"
    exit 1
fi

log_info "Creating X-UI sandbox instance..."

# Create sandbox directory
mkdir -p "$SANDBOX_XUI_DIR"/{bin,db}

# Copy X-UI binary
cp "$XUI_DIR/bin/xray" "$SANDBOX_XUI_DIR/bin/" 2>/dev/null || true
cp "$XUI_DIR/x-ui" "$SANDBOX_XUI_DIR/" 2>/dev/null || true

# Copy database (will be modified by AI)
if [ -f "$XUI_DIR/db/x-ui.db" ]; then
    cp "$XUI_DIR/db/x-ui.db" "$SANDBOX_XUI_DIR/db/x-ui-sandbox.db"
    log_info "Copied X-UI database"
fi

# Create sandbox config
cat > "$SANDBOX_XUI_DIR/config.json" << EOF
{
    "log": {
        "loglevel": "warning",
        "access": "${SANDBOX_DIR}/logs/access.log",
        "error": "${SANDBOX_DIR}/logs/error.log"
    },
    "api": {
        "tag": "api",
        "services": ["StatsService", "LoggerService"]
    },
    "inbounds": [
        {
            "listen": "127.0.0.1",
            "port": 10085,
            "protocol": "dokodemo-door",
            "settings": {
                "address": "127.0.0.1"
            },
            "tag": "api"
        }
    ],
    "routing": {
        "rules": [
            {
                "inboundTag": ["api"],
                "outboundTag": "api",
                "type": "field"
            }
        ]
    },
    "stats": {},
    "policy": {
        "levels": {
            "0": {
                "statsUserUplink": true,
                "statsUserDownlink": true
            }
        },
        "system": {
            "statsInboundUplink": true,
            "statsInboundDownlink": true,
            "statsOutboundUplink": true,
            "statsOutboundDownlink": true
        }
    },
    "dns": {
        "queryStrategy": "UseIP"
    }
}
EOF

# Create systemd service for sandbox (optional, can run manually)
cat > /etc/systemd/system/x-ui-sandbox.service << EOF
[Unit]
Description=X-UI Sandbox Instance (Entropy AI)
After=network.target

[Service]
Type=simple
WorkingDirectory=${SANDBOX_XUI_DIR}
ExecStart=${SANDBOX_XUI_DIR}/x-ui --config ${SANDBOX_XUI_DIR}/config.json
Restart=on-failure
RestartSec=5
LimitNOFILE=1048576

# Resource limits via cgroup
Slice=entropy-sandbox.slice
CPUQuota=10%
MemoryMax=100M

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload

# Create VLESS REALITY config template for testing
cat > "$SANDBOX_XUI_DIR/vless-reality-template.json" << 'EOF'
{
    "inbounds": [
        {
            "port": 8443,
            "protocol": "vless",
            "settings": {
                "clients": [
                    {
                        "id": "sandbox-test-uuid",
                        "flow": "xtls-rprx-vision"
                    }
                ],
                "decryption": "none"
            },
            "streamSettings": {
                "network": "tcp",
                "security": "reality",
                "realitySettings": {
                    "show": false,
                    "dest": "www.google.com:443",
                    "xver": 0,
                    "serverNames": ["www.google.com"],
                    "privateKey": "SANDBOX_PRIVATE_KEY",
                    "shortIds": ["abcd1234"],
                    "fingerprint": "chrome"
                },
                "mux": {
                    "enabled": false,
                    "concurrency": 8
                }
            },
            "sniffing": {
                "enabled": true,
                "destOverride": ["http", "tls"]
            }
        }
    ],
    "outbounds": [
        {
            "protocol": "freedom",
            "tag": "direct"
        }
    ],
    "dns": {
        "queryStrategy": "UseIP",
        "servers": ["1.1.1.1", "8.8.8.8"]
    }
}
EOF

# Save sandbox info
cat > "$SANDBOX_XUI_DIR/sandbox-info.json" << EOF
{
    "type": "x-ui",
    "panel_port": $SANDBOX_PANEL_PORT,
    "vless_port": 8443,
    "created": "$(date -Iseconds)",
    "production_dir": "$XUI_DIR",
    "sandbox_dir": "$SANDBOX_XUI_DIR"
}
EOF

log_info "X-UI sandbox instance created!"
echo ""
echo "Sandbox location: $SANDBOX_XUI_DIR"
echo "Start sandbox:    systemctl start x-ui-sandbox"
echo "Or manually:      ./run_in_sandbox.sh ${SANDBOX_XUI_DIR}/x-ui"
