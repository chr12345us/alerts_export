#!/usr/bin/env python3
"""
Configuration Restore Script

This script restores JSON configuration files to a destination device.
It reads connection parameters from config.ini and processes the collected JSON files.
"""

import configparser
import requests
import json
import os
import sys
import logging
from urllib.parse import urljoin
import argparse

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('restore.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

class ConfigRestorer:
    def __init__(self, config_file='config.ini'):
        """Initialize the restorer with configuration."""
        self.config = configparser.ConfigParser()
        self.config.read(config_file)
        
        # Destination device settings
        self.dest_ip = self.config.get('destination_device', 'ip')
        self.dest_username = self.config.get('destination_device', 'username')
        self.dest_password = self.config.get('destination_device', 'password')
        self.dest_port = self.config.get('destination_device', 'port', fallback='9200')
        
        # Settings
        self.input_dir = self.config.get('settings', 'output_dir', fallback='json_files')
        self.timeout = self.config.getint('settings', 'timeout', fallback=30)
        self.verify_ssl = self.config.getboolean('settings', 'verify_ssl', fallback=False)
        
        # Base URL for the destination device
        self.base_url = f"http://{self.dest_ip}:{self.dest_port}"
        
        logging.info(f"Initialized restorer for destination: {self.dest_ip}:{self.dest_port}")

    def restore_from_file(self, json_file_path):
        """Restore configuration from a single JSON file."""
        try:
            if not os.path.exists(json_file_path):
                logging.error(f"File not found: {json_file_path}")
                return False

            with open(json_file_path, 'r', encoding='utf-8') as file:
                json_data = json.load(file)

            # Check if this is an Elasticsearch response format
            if 'hits' not in json_data:
                logging.error(f"Invalid JSON format in {json_file_path}: missing 'hits' field")
                return False

            hits = json_data.get('hits', {}).get('hits', [])
            
            if not hits:
                logging.warning(f"No data to restore in {json_file_path}")
                return True

            logging.info(f"Restoring {len(hits)} items from {json_file_path}")
            
            success_count = 0
            failure_count = 0

            for item in hits:
                if self._restore_single_item(item):
                    success_count += 1
                else:
                    failure_count += 1

            logging.info(f"Restore from {json_file_path} completed: {success_count} success, {failure_count} failures")
            return failure_count == 0

        except json.JSONDecodeError as e:
            logging.error(f"Failed to parse JSON in {json_file_path}: {e}")
            return False
        except Exception as e:
            logging.error(f"Unexpected error restoring from {json_file_path}: {e}")
            return False

    def _restore_single_item(self, item):
        """Restore a single configuration item."""
        try:
            # Extract the necessary fields from the Elasticsearch document
            index = item.get('_index')
            doc_id = item.get('_id')
            source = item.get('_source')

            if not all([index, doc_id, source]):
                logging.error(f"Missing required fields in item: {item}")
                return False

            # Construct the URL for the PUT request
            url = f"{self.base_url}/{index}/_doc/{doc_id}"
            
            headers = {
                'Content-Type': 'application/json'
            }

            # Set up authentication if username and password are provided
            auth = None
            if self.dest_username and self.dest_password:
                auth = (self.dest_username, self.dest_password)

            # Make the PUT request to restore the document
            response = requests.put(
                url,
                json=source,
                headers=headers,
                auth=auth,
                timeout=self.timeout,
                verify=self.verify_ssl
            )

            response.raise_for_status()
            
            result = response.json()
            logging.debug(f"Restored item {doc_id}: {result}")
            
            return True

        except requests.exceptions.RequestException as e:
            logging.error(f"Request failed for item {doc_id}: {e}")
            return False
        except Exception as e:
            logging.error(f"Unexpected error restoring item {doc_id}: {e}")
            return False

    def restore_alerts(self):
        """Restore alert definitions."""
        alerts_file = os.path.join(self.input_dir, 'alerts.json')
        logging.info("Starting alerts restoration...")
        return self.restore_from_file(alerts_file)

    def restore_reports(self):
        """Restore report definitions."""
        reports_file = os.path.join(self.input_dir, 'reports.json')
        logging.info("Starting reports restoration...")
        return self.restore_from_file(reports_file)

    def restore_all(self):
        """Restore all configuration files."""
        logging.info("Starting full configuration restoration...")
        
        results = {
            'alerts': self.restore_alerts(),
            'reports': self.restore_reports()
        }
        
        success_count = sum(results.values())
        total_count = len(results)
        
        logging.info(f"Restoration completed: {success_count}/{total_count} file types restored successfully")
        
        if success_count == total_count:
            logging.info("All configurations restored successfully!")
        else:
            logging.warning("Some configurations failed to restore. Check the logs for details.")
        
        return results

def main():
    """Main function to run the restorer."""
    parser = argparse.ArgumentParser(description='Restore configuration files to destination device')
    parser.add_argument('--file', '-f', help='Restore from a specific JSON file')
    parser.add_argument('--alerts', action='store_true', help='Restore only alerts')
    parser.add_argument('--reports', action='store_true', help='Restore only reports')
    parser.add_argument('--config', '-c', default='config.ini', help='Configuration file path')
    
    args = parser.parse_args()
    
    try:
        restorer = ConfigRestorer(args.config)
        
        results = {}
        
        if args.file:
            # Restore from specific file
            filename = os.path.basename(args.file)
            results[filename] = restorer.restore_from_file(args.file)
        elif args.alerts:
            # Restore only alerts
            results['alerts'] = restorer.restore_alerts()
        elif args.reports:
            # Restore only reports
            results['reports'] = restorer.restore_reports()
        else:
            # Restore all configurations
            results = restorer.restore_all()
        
        # Print summary
        print("\n" + "="*50)
        print("RESTORATION SUMMARY")
        print("="*50)
        for file_type, success in results.items():
            status = "✓ SUCCESS" if success else "✗ FAILED"
            print(f"{file_type.upper()}: {status}")
        print("="*50)
        
        # Exit with appropriate code
        if all(results.values()):
            sys.exit(0)
        else:
            sys.exit(1)
            
    except FileNotFoundError as e:
        logging.error(f"Configuration file not found: {e}")
        sys.exit(1)
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()