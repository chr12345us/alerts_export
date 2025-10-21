# Elasticsearch Alerts & Reports Export/Import Tools

A comprehensive set of Python scripts for collecting, exporting, and restoring Elasticsearch alert and report configurations between servers using SSH tunneling.

## 🚀 Features

- **Cross-platform SSH tunneling** using Python (no external SSH tools required)
- **Interactive configuration** when config.ini doesn't exist
- **Secure remote access** to Elasticsearch instances
- **Timestamped exports** for easy tracking
- **Command-line interface** with multiple options
- **Full path support** for input files
- **Comprehensive logging** and error handling
- **Windows, macOS, and Linux support**

## 📁 Project Structure

```
alerts_export/
├── collect_alerts-reports.py    # Main collection script
├── restore_alerts-reports.py    # Main restore script
├── config_example.ini           # Example configuration file
├── requirements.txt             # Python dependencies
├── README.md                   # Documentation
├── logs/                       # Log files directory
└── json_files/                 # Output directory (excluded from git)
```

## 🛠️ Installation

### Prerequisites
- Python 3.6 or higher
- Network access to source/destination servers via SSH

### Install Dependencies

```bash
pip install -r requirements.txt
```

### Configuration

1. **Option 1: Create configuration file (recommended for repeated use)**
   ```bash
   cp config_example.ini config.ini
   ```
   
   Edit `config.ini` with your server details:
   ```ini
   [source_device]
   ssh_host = 192.168.1.100
   ssh_port = 22
   ssh_username = root
   ssh_password = your_password
   local_port = 9201

   [destination_device]
   ssh_host = 192.168.1.200
   ssh_port = 22
   ssh_username = root
   ssh_password = your_password
   local_port = 9202
   ```

2. **Option 2: Interactive configuration (when config.ini doesn't exist)**
   
   If no `config.ini` file exists, both scripts will automatically prompt you for connection details:
   ```bash
   # Just run the script - it will ask for details interactively
   python collect_alerts-reports.py
   ```
   
   The script will prompt for:
   - SSH Host/IP address
   - SSH Username
   - SSH Password (hidden input)
   - SSH Port (optional, default: 22)
   - Local tunnel port (optional, default: 9201 for collection, 9202 for restore)

## 📊 Usage

### Quick Start (Interactive Mode)

If you don't have a config file, just run the script and it will guide you:

```bash
# Collection - will prompt for source device details
python collect_alerts-reports.py

# Restoration - will prompt for destination device details  
python restore_alerts-reports.py
```

**Interactive prompt example:**
```
⚠️  Configuration file 'config.ini' not found.
Please provide the SSH connection details for the source device:

============================================================
🔧 INTERACTIVE CONFIGURATION SETUP
============================================================

📥 SOURCE DEVICE (where to collect configurations from):
SSH Host/IP address: 192.168.1.100
SSH Username: root
SSH Password: [hidden]
SSH Port (default: 22): 
Local tunnel port (default: 9201): 

✅ Configuration complete!
📡 Will connect to: root@192.168.1.100:22
🔗 Local tunnel port: 9201

💡 Tip: Create a 'config.ini' file to avoid entering this information each time.
============================================================
```

### Collection (Export)

#### Collect All Configurations
```bash
python collect_alerts-reports.py
```

### Restoration (Import)

#### Restore All Configurations
```bash
python restore_alerts-reports.py
```

#### Restore Specific Files (with full paths)
```bash
python restore_alerts-reports.py -a json_files/alerts_20251021_143900.json -r json_files/reports_20251021_143900.json
```

#### Restore Only Alerts (with full path)
```bash
python restore_alerts-reports.py -a json_files/alerts_20251021_143900.json
```

#### Restore Only Reports (with full path)
```bash
python restore_alerts-reports.py -r json_files/reports_20251021_143900.json
```

## 📋 Output Files

- `alerts_YYYYMMDD_HHMMSS.json` - Complete Elasticsearch export for alerts
- `reports_YYYYMMDD_HHMMSS.json` - Complete Elasticsearch export for reports

## 🔧 Command Line Options

### Collection Script Options
- `--config CONFIG_FILE` - Specify custom config file

### Restore Script Options
- `-a FILENAME, --alerts FILENAME` - Restore alerts from file (supports full paths)
- `-r FILENAME, --reports FILENAME` - Restore reports from file (supports full paths)
- `--file FILENAME` - Restore from specific file (full path)
- `--config CONFIG_FILE` - Specify custom config file

## 🔒 Security Features

- **SSH encryption** for all remote connections
- **Automatic host key acceptance** for ease of use
- **Password-based authentication** (SSH key support available)
- **Local tunnel cleanup** on script exit
- **Sensitive data exclusion** from git repository

## 📝 Logging

All scripts generate detailed logs in the `logs/` directory:
- `logs/collection.log` - Collection operations
- `logs/restore.log` - Restore operations

## Configuration Options

The `config.ini` file supports the following settings:

### Source Device
- `ssh_host` - IP address of the source device
- `ssh_username` - Username for SSH authentication
- `ssh_password` - Password for SSH authentication
- `ssh_port` - SSH port number (default: 22)
- `local_port` - Local port for tunnel (default: 9201)

### Destination Device
- `ssh_host` - IP address of the destination device
- `ssh_username` - Username for SSH authentication
- `ssh_password` - Password for SSH authentication
- `ssh_port` - SSH port number (default: 22)
- `local_port` - Local port for tunnel (default: 9202)

### Settings
- `output_dir` - Directory to save collected files (default: json_files)
- `timeout` - Request timeout in seconds (default: 30)
- `verify_ssl` - Whether to verify SSL certificates (default: false)

## Error Handling

The scripts include comprehensive error handling and logging:
- Connection timeouts
- Authentication failures
- JSON parsing errors
- File system errors
- Network connectivity issues

Check the log files in the `logs/` directory for detailed error information if operations fail.

## 🚨 Troubleshooting

### Common Issues

1. **Connection refused**: Check if SSH service is running on target server
2. **Authentication failed**: Verify SSH username and password
3. **Port conflicts**: Change `local_port` in config.ini if ports are in use
4. **Firewall blocking**: Ensure SSH port (22) is open

### Debug Steps
```bash
# Test SSH connectivity
ssh root@192.168.1.100

# Check if Elasticsearch is running
curl http://localhost:9200

# Verify Python dependencies
pip list | grep -E "(requests|paramiko)"
```

## Security Notes

- Store passwords securely and consider using environment variables for sensitive data
- The scripts support both HTTP and HTTPS connections
- SSL certificate verification can be enabled in the configuration

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 📧 Support

For issues and questions:
1. Check the troubleshooting section
2. Review log files for detailed error information
3. Create an issue in the repository