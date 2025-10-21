# SSH Tunnel Configuration Scripts

These scripts use SSH tunneling to securely connect to remote Elasticsearch instances when direct network access is not available.

## Prerequisites

1. **Install sshpass** (for password-based SSH authentication):
```bash
sudo apt-get update
sudo apt-get install sshpass
```

2. **Install Python requirements:**
```bash
pip install -r requirements.txt
```

3. **SSH access** to both source and destination servers

## Configuration

Update `config.ini` with your SSH connection details:

```ini
[source_device]
ip = 192.168.0.185
username = radware
password = radadmin
port = 9200
# SSH tunnel settings
ssh_host = 192.168.0.185
ssh_port = 22
ssh_username = your_ssh_user
ssh_password = your_ssh_password
local_port = 9201

[destination_device]
ip = 192.168.0.186
username = radware
password = radadmin  
port = 9200
# SSH tunnel settings
ssh_host = 192.168.0.186
ssh_port = 22
ssh_username = your_ssh_user
ssh_password = your_ssh_password
local_port = 9202
```

## SSH Tunnel Scripts

### Collection (from source)
```bash
python3 ssh_collect_config.py
```

**What it does:**
1. Creates SSH tunnel: `localhost:9201 → source_server:9200`
2. Connects to Elasticsearch through tunnel
3. Downloads alerts and reports
4. Saves to `json_files/` directory
5. Automatically closes tunnel when done

### Restoration (to destination)
```bash
# Restore all configurations
python3 ssh_restore_config.py

# Restore only alerts
python3 ssh_restore_config.py --alerts

# Restore only reports
python3 ssh_restore_config.py --reports

# Restore from specific file
python3 ssh_restore_config.py --file json_files/alerts.json
```

**What it does:**
1. Creates SSH tunnel: `localhost:9202 → destination_server:9200`
2. Connects to Elasticsearch through tunnel
3. Uploads configuration files
4. Automatically closes tunnel when done

## How SSH Tunneling Works

The scripts create **local port forwarding** tunnels:

```
Your Machine                    Remote Server
┌─────────────────┐            ┌──────────────────┐
│ localhost:9201  │ =========> │ localhost:9200   │
│                 │  SSH Tunnel │ (Elasticsearch)  │
│ Python Script   │            │                  │
└─────────────────┘            └──────────────────┘
```

- **Local port 9201** → **Source server port 9200**
- **Local port 9202** → **Destination server port 9200**

## Security Features

- **Encrypted connection** through SSH
- **Automatic tunnel cleanup** on script exit
- **Signal handling** for graceful shutdown (Ctrl+C)
- **No persistent connections** - tunnel closed after operation

## Troubleshooting

### SSH Connection Issues
```bash
# Test SSH connectivity manually
ssh your_ssh_user@192.168.0.185

# Test with sshpass
sshpass -p 'your_password' ssh your_ssh_user@192.168.0.185
```

### Port Conflicts
If local ports 9201/9202 are in use, change `local_port` in config.ini:
```ini
local_port = 9301  # Use different port
```

### Firewall Issues
Ensure SSH port (22) is open on remote servers:
```bash
# On remote server
sudo ufw allow 22
```

## Log Files

- `ssh_collection.log` - Collection operation logs
- `ssh_restore.log` - Restoration operation logs

Check these files for detailed error information if operations fail.

## Alternative: SSH Key Authentication

For better security, use SSH keys instead of passwords:

1. **Generate SSH key:**
```bash
ssh-keygen -t rsa -b 4096
```

2. **Copy to remote servers:**
```bash
ssh-copy-id your_ssh_user@192.168.0.185
ssh-copy-id your_ssh_user@192.168.0.186
```

3. **Remove password from config.ini:**
```ini
ssh_password = 
# Leave empty for key-based auth
```

## Example Workflow

1. **Configure SSH access** to both servers
2. **Update config.ini** with correct SSH credentials  
3. **Collect from source:**
   ```bash
   python3 ssh_collect_config.py
   ```
4. **Restore to destination:**
   ```bash
   python3 ssh_restore_config.py
   ```

The scripts handle all tunnel management automatically!