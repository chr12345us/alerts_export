# Utilities

This folder contains utility scripts for analyzing and processing alerts and reports data.

## analyze_alerts.py

Analyzes JSON alert files to extract device IPs and email addresses.

### Usage

```bash
# Basic analysis
python utilities/analyze_alerts.py -a json_files/alerts_20251021_143900.json

# Verbose analysis with structure information
python utilities/analyze_alerts.py -a json_files/alerts_20251021_143900.json -v

# Custom output file
python utilities/analyze_alerts.py -a json_files/alerts_20251021_143900.json -o my_analysis.json
```

### Features

- **Device IP Extraction**: Finds all IP addresses from alert configurations
- **Email Address Extraction**: Finds all email addresses used in notifications
- **Structure Analysis**: Provides insights into alert data structure (with -v flag)
- **JSON Output**: Results saved to `alert_devices.json` by default

### Output Format

```json
{
  "analysis_timestamp": "2025-10-21T14:39:00.123456",
  "source_file": "json_files/alerts_20251021_143900.json",
  "device_ips": {
    "count": 5,
    "addresses": ["192.168.1.10", "192.168.1.20", "10.0.1.5"]
  },
  "email_addresses": {
    "count": 3,
    "addresses": ["admin@company.com", "alerts@company.com"]
  },
  "structure_analysis": {
    "total_alerts": 25,
    "alert_types": ["cpu_alert", "memory_alert"],
    "fields_with_ips": ["_source.target_ip", "_source.device.ip"],
    "fields_with_emails": ["_source.notification.email"]
  }
}
```

### Command Line Options

- `-a, --alerts`: Path to the alerts JSON file to analyze (required)
- `-o, --output`: Output JSON file name (default: alert_devices.json)
- `-v, --verbose`: Show detailed analysis information including structure analysis