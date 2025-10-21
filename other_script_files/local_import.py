#!/usr/bin/env python3
"""
Local Import Script

This script imports JSON configuration files to the local Elasticsearch instance.
Run this script directly on the destination server where Elasticsearch is running.
"""

import json
import requests
import sys
import os
import logging
import argparse
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('import.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

class LocalImporter:
    def __init__(self, base_url='http://localhost:9200'):
        """Initialize the importer for local Elasticsearch."""
        self.base_url = base_url
        self.timeout = 30
        
        logging.info(f"Initialized importer for: {self.base_url}")

    def import_from_file(self, json_file_path):
        """Import configuration from a single JSON file."""
        try:
            if not os.path.exists(json_file_path):
                logging.error(f"File not found: {json_file_path}")
                return False

            logging.info(f"Importing from: {json_file_path}")

            with open(json_file_path, 'r', encoding='utf-8') as file:
                json_data = json.load(file)

            # Check if this is an Elasticsearch response format
            if 'hits' not in json_data:
                logging.error(f"Invalid JSON format in {json_file_path}: missing 'hits' field")
                return False

            hits = json_data.get('hits', {}).get('hits', [])
            
            if not hits:
                logging.warning(f"No data to import in {json_file_path}")
                return True

            logging.info(f"Importing {len(hits)} items from {json_file_path}")
            
            success_count = 0
            failure_count = 0

            for item in hits:
                if self._import_single_item(item):
                    success_count += 1
                else:
                    failure_count += 1

            logging.info(f"Import from {json_file_path} completed: {success_count} success, {failure_count} failures")
            return failure_count == 0

        except json.JSONDecodeError as e:
            logging.error(f"Failed to parse JSON in {json_file_path}: {e}")
            return False
        except Exception as e:
            logging.error(f"Unexpected error importing from {json_file_path}: {e}")
            return False

    def _import_single_item(self, item):
        """Import a single configuration item."""
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

            # Make the PUT request to import the document
            response = requests.put(
                url,
                json=source,
                headers=headers,
                timeout=self.timeout
            )

            response.raise_for_status()
            
            result = response.json()
            action = result.get('result', 'unknown')
            logging.debug(f"Imported item {doc_id}: {action}")
            
            return True

        except requests.exceptions.RequestException as e:
            logging.error(f"Request failed for item {doc_id}: {e}")
            return False
        except Exception as e:
            logging.error(f"Unexpected error importing item {doc_id}: {e}")
            return False

    def import_alerts(self, import_dir):
        """Import alert definitions."""
        alerts_file = os.path.join(import_dir, 'alerts.json')
        logging.info("Starting alerts import...")
        return self.import_from_file(alerts_file)

    def import_reports(self, import_dir):
        """Import report definitions."""
        reports_file = os.path.join(import_dir, 'reports.json')
        logging.info("Starting reports import...")
        return self.import_from_file(reports_file)

    def import_all(self, import_dir):
        """Import all configuration files from directory."""
        logging.info(f"Starting full configuration import from: {import_dir}")
        
        if not os.path.exists(import_dir):
            logging.error(f"Import directory not found: {import_dir}")
            return False
        
        results = {
            'alerts': self.import_alerts(import_dir),
            'reports': self.import_reports(import_dir)
        }
        
        success_count = sum(results.values())
        total_count = len(results)
        
        logging.info(f"Import completed: {success_count}/{total_count} file types imported successfully")
        
        if success_count == total_count:
            logging.info("All configurations imported successfully!")
        else:
            logging.warning("Some configurations failed to import. Check the logs for details.")
        
        return results

def main():
    """Main function to run the importer."""
    parser = argparse.ArgumentParser(description='Import configuration files to local Elasticsearch')
    parser.add_argument('import_dir', help='Directory containing exported configuration files')
    parser.add_argument('--file', '-f', help='Import from a specific JSON file')
    parser.add_argument('--alerts', action='store_true', help='Import only alerts')
    parser.add_argument('--reports', action='store_true', help='Import only reports')
    
    args = parser.parse_args()
    
    try:
        importer = LocalImporter()
        
        results = {}
        
        if args.file:
            # Import from specific file
            filename = os.path.basename(args.file)
            results[filename] = importer.import_from_file(args.file)
        elif args.alerts:
            # Import only alerts
            results['alerts'] = importer.import_alerts(args.import_dir)
        elif args.reports:
            # Import only reports
            results['reports'] = importer.import_reports(args.import_dir)
        else:
            # Import all configurations
            results = importer.import_all(args.import_dir)
        
        # Print summary
        print("\n" + "="*50)
        print("IMPORT SUMMARY")
        print("="*50)
        for import_type, success in results.items():
            status = "✓ SUCCESS" if success else "✗ FAILED"
            print(f"{import_type.upper()}: {status}")
        print("="*50)
        
        # Exit with appropriate code
        if all(results.values()):
            sys.exit(0)
        else:
            sys.exit(1)
            
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()