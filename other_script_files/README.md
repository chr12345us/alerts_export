# Configuration File Collector and Restorer

This project collects JSON configuration files from a source device and restores them to a destination device using REST API calls.

## Files Created

1. **config.ini** - Configuration file with device connection parameters
2. **config_example.ini** - Example configuration file with placeholder values
3. **collect_config.py** - Python script to collect configuration files from source device
4. **restore_config.py** - Python script to restore configuration files to destination device
5. **requirements.txt** - Python dependencies
6. **README.md** - This documentation file

## Setup

1. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure Connection Parameters:**
   Edit `config.ini` and update the following sections:
   
   ```ini
   [source_device]
   ip = YOUR_SOURCE_IP
   username = YOUR_USERNAME
   password = YOUR_PASSWORD
   port = 9200
   
   [destination_device]
   ip = YOUR_DESTINATION_IP
   username = YOUR_USERNAME
   password = YOUR_PASSWORD
   port = 9200
   ```

## Usage

### Collecting Configuration Files

Run the collection script:

```bash
python collect_config.py
```

### Restoring Configuration Files

**Restore all configurations:**
```bash
python restore_config.py
```

**Restore only alerts:**
```bash
python restore_config.py --alerts
```

**Restore only reports:**
```bash
python restore_config.py --reports
```

**Restore from a specific file:**
```bash
python restore_config.py --file json_files/alerts.json
```

**Use a different config file:**
```bash
python restore_config.py --config my_config.ini
```

## Output

### Collection
The collection script will:
- Create a `json_files` directory (if it doesn't exist)
- Collect and save two files:
  - `json_files/reports.json` - Scheduled report definitions
  - `json_files/alerts.json` - Alert definitions
- Generate a log file `collection.log` with detailed execution information
- Display a summary of the collection results

### Restoration
The restoration script will:
- Read the collected JSON files from the `json_files` directory
- Connect to the destination device specified in config.ini
- Restore each configuration item using PUT requests to the appropriate endpoints
- Generate a log file `restore.log` with detailed execution information
- Display a summary of the restoration results

## Configuration Options

The `config.ini` file supports the following settings:

### Source Device
- `ip` - IP address of the source device
- `username` - Username for authentication
- `password` - Password for authentication
- `port` - Port number (default: 9200)

### Destination Device
- `ip` - IP address of the destination device
- `username` - Username for destination authentication
- `password` - Password for destination authentication
- `port` - Port number for destination (default: 9200)

### Settings
- `output_dir` - Directory to save collected files (default: json_files)
- `timeout` - Request timeout in seconds (default: 30)
- `verify_ssl` - Whether to verify SSL certificates (default: false)

## Error Handling

The script includes comprehensive error handling and logging:
- Connection timeouts
- Authentication failures
- JSON parsing errors
- File system errors
- Network connectivity issues

Check the `collection.log` file for detailed error information if collection fails.

## Security Notes

- Store passwords securely and consider using environment variables for sensitive data
- The script supports both HTTP and HTTPS connections
- SSL certificate verification can be enabled in the configuration

## Troubleshooting

1. **Connection refused**: Check if the source device is accessible and the port is correct
2. **Authentication failed**: Verify username and password in config.ini
3. **Timeout errors**: Increase the timeout value in the settings section
4. **JSON parsing errors**: Check if the API endpoints are returning valid JSON data