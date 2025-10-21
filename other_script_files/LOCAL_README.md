# Local Elasticsearch Configuration Export/Import

These scripts run directly on the source and destination servers where Elasticsearch is running locally.

## Files

- `local_export.py` - Export configurations from local Elasticsearch (run on source server)
- `local_import.py` - Import configurations to local Elasticsearch (run on destination server)

## Usage

### On Source Server (Export)

1. **Copy `local_export.py` to the source server**

2. **Run the export:**
```bash
python3 local_export.py
```

This will create a timestamped directory (e.g., `exported_configs_20251020_192715`) containing:
- `alerts.json` - Alert definitions
- `reports.json` - Report definitions  
- `package_info.json` - Export metadata
- `export.log` - Detailed log

3. **Copy the entire exported directory to the destination server**

### On Destination Server (Import)

1. **Copy `local_import.py` to the destination server**

2. **Copy the exported directory from source server**

3. **Run the import:**
```bash
# Import all configurations
python3 local_import.py exported_configs_20251020_192715

# Import only alerts
python3 local_import.py exported_configs_20251020_192715 --alerts

# Import only reports  
python3 local_import.py exported_configs_20251020_192715 --reports

# Import from specific file
python3 local_import.py . --file exported_configs_20251020_192715/alerts.json
```

## Requirements

- Python 3.x
- requests library: `pip install requests`
- Elasticsearch running locally on port 9200

## Output

- Export creates timestamped directories with all configuration files
- Both scripts generate detailed logs (`export.log`, `import.log`)
- Summary displayed at completion showing success/failure status

## Notes

- Scripts connect to `localhost:9200` by default
- Export creates timestamped directories to avoid overwriting
- Import preserves original document IDs and indexes
- Both scripts include comprehensive error handling and logging