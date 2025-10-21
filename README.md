# Elasticsearch Alerts & Reports Export/Import Tools# Configuration File Collector and Restorer



A comprehensive set of Python scripts for collecting, exporting, and restoring Elasticsearch alert and report configurations between servers using SSH tunneling.This project collects JSON configuration files from a source device and restores them to a destination device using REST API calls.



## 🚀 Features## Files Created



- **Cross-platform SSH tunneling** using Python (no external SSH tools required)1. **config.ini** - Configuration file with device connection parameters

- **Secure remote access** to Elasticsearch instances2. **config_example.ini** - Example configuration file with placeholder values

- **Flexible collection options** (full format or definitions only)3. **collect_config.py** - Python script to collect configuration files from source device

- **Timestamped exports** for easy tracking4. **restore_config.py** - Python script to restore configuration files to destination device

- **Command-line interface** with multiple options5. **requirements.txt** - Python dependencies

- **Comprehensive logging** and error handling6. **README.md** - This documentation file

- **Windows, macOS, and Linux support**

## Setup

## 📁 Project Structure

1. **Install Dependencies:**

```   ```bash

alerts_export/   pip install -r requirements.txt

├── ssh_collect_config.py      # Main collection script (SSH tunnel)   ```

├── ssh_restore_config.py      # Main restore script (SSH tunnel)

├── local_export.py           # Local export script (direct access)2. **Configure Connection Parameters:**

├── local_import.py           # Local import script (direct access)   Edit `config.ini` and update the following sections:

├── collect_config.py         # Original collection script (direct network)   

├── restore_config.py         # Original restore script (direct network)   ```ini

├── config_example.ini        # Example configuration file   [source_device]

├── requirements.txt          # Python dependencies   ip = YOUR_SOURCE_IP

├── README.md                # Main documentation   username = YOUR_USERNAME

├── SSH_TUNNEL_README.md      # SSH tunnel specific guide   password = YOUR_PASSWORD

├── LOCAL_README.md           # Local scripts guide   port = 9200

└── json_files/              # Output directory (excluded from git)   

```   [destination_device]

   ip = YOUR_DESTINATION_IP

## 🛠️ Installation   username = YOUR_USERNAME

   password = YOUR_PASSWORD

### Prerequisites   port = 9200

- Python 3.6 or higher   ```

- Network access to source/destination servers via SSH

## Usage

### Install Dependencies

```bash### Collecting Configuration Files

pip install -r requirements.txt

```Run the collection script:



### Configuration```bash

1. Copy the example configuration:python collect_config.py

   ```bash```

   cp config_example.ini config.ini

   ```### Restoring Configuration Files



2. Edit `config.ini` with your server details:**Restore all configurations:**

   ```ini```bash

   [source_device]python restore_config.py

   ssh_host = 192.168.1.100```

   ssh_port = 22

   ssh_username = root**Restore only alerts:**

   ssh_password = your_password```bash

   local_port = 9201python restore_config.py --alerts

```

   [destination_device]

   ssh_host = 192.168.1.200**Restore only reports:**

   ssh_port = 22```bash

   ssh_username = rootpython restore_config.py --reports

   ssh_password = your_password```

   local_port = 9202

   ```**Restore from a specific file:**

```bash

## 📊 Usagepython restore_config.py --file json_files/alerts.json

```

### Collection (Export)

**Use a different config file:**

#### SSH Tunnel Method (Recommended)```bash

```bashpython restore_config.py --config my_config.ini

# Collect all (full format)```

python ssh_collect_config.py

## Output

# Collect alert definitions only

python ssh_collect_config.py -as### Collection

The collection script will:

# Collect report definitions only- Create a `json_files` directory (if it doesn't exist)

python ssh_collect_config.py -rs- Collect and save two files:

  - `json_files/reports.json` - Scheduled report definitions

# Collect both definitions  - `json_files/alerts.json` - Alert definitions

python ssh_collect_config.py -as -rs- Generate a log file `collection.log` with detailed execution information

```- Display a summary of the collection results



#### Local Method (when running on Elasticsearch server)### Restoration

```bashThe restoration script will:

python local_export.py- Read the collected JSON files from the `json_files` directory

```- Connect to the destination device specified in config.ini

- Restore each configuration item using PUT requests to the appropriate endpoints

### Restoration (Import)- Generate a log file `restore.log` with detailed execution information

- Display a summary of the restoration results

#### SSH Tunnel Method (Recommended)

```bash## Configuration Options

# Restore all (default filenames)

python ssh_restore_config.pyThe `config.ini` file supports the following settings:



# Restore specific files### Source Device

python ssh_restore_config.py -a alerts_20251021_143900.json -r reports_20251021_143900.json- `ip` - IP address of the source device

- `username` - Username for authentication

# Restore only alerts- `password` - Password for authentication

python ssh_restore_config.py -a alerts_20251021_143900.json- `port` - Port number (default: 9200)



# Extract definitions from existing files### Destination Device

python ssh_restore_config.py -as alerts_20251021_143900.json- `ip` - IP address of the destination device

```- `username` - Username for destination authentication

- `password` - Password for destination authentication

#### Local Method (when running on Elasticsearch server)- `port` - Port number for destination (default: 9200)

```bash

python local_import.py exported_configs_20251021_143900### Settings

```- `output_dir` - Directory to save collected files (default: json_files)

- `timeout` - Request timeout in seconds (default: 30)

## 📋 Output Files- `verify_ssl` - Whether to verify SSL certificates (default: false)



### Full Format## Error Handling

- `alerts_YYYYMMDD_HHMMSS.json` - Complete Elasticsearch export

- `reports_YYYYMMDD_HHMMSS.json` - Complete Elasticsearch exportThe script includes comprehensive error handling and logging:

- Connection timeouts

### Definitions Only- Authentication failures

- `alerts_definitions_YYYYMMDD_HHMMSS.json` - Clean definitions- JSON parsing errors

- `reports_definitions_YYYYMMDD_HHMMSS.json` - Clean definitions- File system errors

- Network connectivity issues

## 🔧 Command Line Options

Check the `collection.log` file for detailed error information if collection fails.

### Collection Script Options

- `-as, --alerts-source` - Extract alert source definitions only## Security Notes

- `-rs, --reports-source` - Extract report source definitions only

- `--config CONFIG_FILE` - Specify custom config file- Store passwords securely and consider using environment variables for sensitive data

- The script supports both HTTP and HTTPS connections

### Restore Script Options- SSL certificate verification can be enabled in the configuration

- `-a FILENAME, --alerts FILENAME` - Restore alerts from file

- `-r FILENAME, --reports FILENAME` - Restore reports from file## Troubleshooting

- `-as FILENAME, --alerts-source FILENAME` - Extract alert definitions

- `-rs FILENAME, --reports-source FILENAME` - Extract report definitions1. **Connection refused**: Check if the source device is accessible and the port is correct

- `--file FILENAME` - Restore from specific file2. **Authentication failed**: Verify username and password in config.ini

- `--config CONFIG_FILE` - Specify custom config file3. **Timeout errors**: Increase the timeout value in the settings section

4. **JSON parsing errors**: Check if the API endpoints are returning valid JSON data
## 🔒 Security Features

- **SSH encryption** for all remote connections
- **Automatic host key acceptance** for ease of use
- **Password-based authentication** (SSH key support available)
- **Local tunnel cleanup** on script exit
- **Sensitive data exclusion** from git repository

## 📝 Logging

All scripts generate detailed logs:
- `ssh_collection.log` - Collection operations
- `ssh_restore.log` - Restore operations
- `export.log` - Local export operations
- `import.log` - Local import operations

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

## 🔄 Version History

- **v1.0** - Initial release with basic collection/restore
- **v1.1** - Added SSH tunnel support
- **v1.2** - Added definitions extraction
- **v1.3** - Cross-platform paramiko implementation