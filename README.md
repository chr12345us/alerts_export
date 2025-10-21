# Elasticsearch Alerts & Reports Export/Import Tools

A comprehensive set of Python scripts for collecting, exporting, and restoring Elasticsearch alert and report configurations between servers using SSH tunneling.

## 🚀 Features

- **Cross-platform SSH tunneling** using Python (no external SSH tools required)
- **Secure remote access** to Elasticsearch instances
- **Flexible collection options** (full format or definitions only)
- **Timestamped exports** for easy tracking
- **Command-line interface** with multiple options
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

1. Copy the example configuration:
   ```bash
   cp config_example.ini config.ini
   ```

2. Edit `config.ini` with your server details:
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

## 📊 Usage

### Collection (Export)

#### Collect All Configurations
```bash
python collect_alerts-reports.py
```

#### Collect Alert Definitions Only
```bash
python collect_alerts-reports.py -as
```

#### Collect Report Definitions Only
```bash
python collect_alerts-reports.py -rs
```

#### Collect Both Definitions
```bash
python collect_alerts-reports.py -as -rs
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

#### Extract Definitions from Existing Files (with full paths)
```bash
python restore_alerts-reports.py -as json_files/alerts_20251021_143900.json
python restore_alerts-reports.py -rs json_files/reports_20251021_143900.json
```

## 📋 Output Files

### Full Format
- `alerts_YYYYMMDD_HHMMSS.json` - Complete Elasticsearch export
- `reports_YYYYMMDD_HHMMSS.json` - Complete Elasticsearch export

### Definitions Only
- `alerts_definitions_YYYYMMDD_HHMMSS.json` - Clean definitions
- `reports_definitions_YYYYMMDD_HHMMSS.json` - Clean definitions

## 🔧 Command Line Options

### Collection Script Options
- `-as, --alerts-source` - Extract alert source definitions only
- `-rs, --reports-source` - Extract report source definitions only
- `--config CONFIG_FILE` - Specify custom config file

### Restore Script Options
- `-a FILENAME, --alerts FILENAME` - Restore alerts from file
- `-r FILENAME, --reports FILENAME` - Restore reports from file
- `-as FILENAME, --alerts-source FILENAME` - Extract alert definitions
- `-rs FILENAME, --reports-source FILENAME` - Extract report definitions
- `--file FILENAME` - Restore from specific file
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