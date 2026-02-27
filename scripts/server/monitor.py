import sqlite3
import psutil
import time
import os
import subprocess
import json

# Configuration
DB_NAME = "/root/monitoring/monitor_stats.db"
MAX_DB_SIZE_MB = 500
XRAY_PATH = "/usr/local/x-ui/bin/xray-linux-amd64" # Default X-UI/Xray path
UPDATE_INTERVAL = 30 # Seconds

def init_db():
    os.makedirs(os.path.dirname(DB_NAME), exist_ok=True)
    conn = sqlite3.connect(DB_NAME)
    curr = conn.cursor()
    # System metrics table
    curr.execute('''CREATE TABLE IF NOT EXISTS system_stats
                 (timestamp DATETIME DEFAULT (datetime('now','localtime')),
                  cpu REAL, ram REAL, net_down REAL, net_up REAL)''')
    # User traffic stats table
    curr.execute('''CREATE TABLE IF NOT EXISTS user_stats
                 (timestamp DATETIME DEFAULT (datetime('now','localtime')),
                  email TEXT, down INTEGER, up INTEGER)''')
    conn.commit()
    conn.close()

def get_xray_stats():
    try:
        # Querying Xray API directly
        cmd = f"{XRAY_PATH} api statsquery --server=127.0.0.1:62789"
        result = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT).decode()
        return json.loads(result)
    except Exception as e:
        print(f"Xray statistics unavailable: {e}")
        return None

def cleanup_db():
    """Deletes old data when DB size exceeds 500MB"""
    if os.path.exists(DB_NAME) and os.path.getsize(DB_NAME) > MAX_DB_SIZE_MB * 1024 * 1024:
        conn = sqlite3.connect(DB_NAME)
        curr = conn.cursor()
        curr.execute("DELETE FROM system_stats WHERE rowid IN (SELECT rowid FROM system_stats LIMIT 500)")
        curr.execute("DELETE FROM user_stats WHERE rowid IN (SELECT rowid FROM user_stats LIMIT 500)")
        conn.commit()
        conn.close()

def collect():
    conn = sqlite3.connect(DB_NAME)
    curr = conn.cursor()

    # System data
    cpu = psutil.cpu_percent()
    ram = psutil.virtual_memory().percent
    net = psutil.net_io_counters()

    curr.execute("INSERT INTO system_stats (cpu, ram, net_down, net_up) VALUES (?, ?, ?, ?)",
                 (cpu, ram, net.bytes_recv, net.bytes_sent))

    # Xray data
    xstats = get_xray_stats()
    if xstats and isinstance(xstats.get('stat'), list):
        for entry in xstats['stat']:
            name = entry.get('name', '')
            val = entry.get('value', 0)

            parts = name.split('>>>')
            if len(parts) >= 4 and parts[0] == 'user':
                email = parts[1]
                type_t = parts[3]

                if type_t == 'downlink':
                    curr.execute("INSERT INTO user_stats (email, down, up) VALUES (?, ?, 0)", (email, val))
                elif type_t == 'uplink':
                    curr.execute("INSERT INTO user_stats (email, down, up) VALUES (?, 0, ?)", (email, val))

    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
    print(f"Monitoring started. Interval: {UPDATE_INTERVAL}s. DB: {DB_NAME}")
    while True:
        try:
            collect()
            cleanup_db()
        except Exception as e:
            print(f"Collection error: {e}")
        time.sleep(UPDATE_INTERVAL)
