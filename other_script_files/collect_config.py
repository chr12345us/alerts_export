#!/usr/bin/env python3
"""
Configuration File Collector Script

This script connects to a source device and executes curl commands to collect 
JSON configuration files. It reads connection parameters from config.ini.
"""

import configparser
import requests
import json
import os
import sys
from urllib.parse import urljoin
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('collection.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

class ConfigCollector:
    def __init__(self, config_file='config.ini'):
        """Initialize the collector with configuration."""
        self.config = configparser.ConfigParser()
        self.config.read(config_file)
        
        # Source device settings
        self.source_ip = self.config.get('source_device', 'ip')
        self.source_username = self.config.get('source_device', 'username')
        self.source_password = self.config.get('source_device', 'password')
        self.source_port = self.config.get('source_device', 'port', fallback='9200')
        
        # Settings
        self.output_dir = self.config.get('settings', 'output_dir', fallback='json_files')
        self.timeout = self.config.getint('settings', 'timeout', fallback=30)
        self.verify_ssl = self.config.getboolean('settings', 'verify_ssl', fallback=False)
        
        # Create output directory if it doesn't exist
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Base URL for the source device
        self.base_url = f"http://{self.source_ip}:{self.source_port}"
        
        logging.info(f"Initialized collector for source: {self.source_ip}:{self.source_port}")

    def collect_reports(self):
        """Collect scheduled report definitions."""
        endpoint = "/vrm-scheduled-report-definition-vrm-ty-vrm-scheduled-report-definition/_search"
        query = {
            "query": {
                "match_all": {}
            },
            "size": 9999
        }
        
        output_file = os.path.join(self.output_dir, 'reports.json')
        return self._execute_request(endpoint, query, output_file, 'reports')

    def collect_alerts(self):
        """Collect alert definitions."""
        endpoint = "/rt-alert-def-vrm-ty-rt-alert-def-vrm/_search"
        query = {
            "query": {
                "match_all": {}
            },
            "size": 9999
        }
        
        output_file = os.path.join(self.output_dir, 'alerts.json')
        return self._execute_request(endpoint, query, output_file, 'alerts')

    def _execute_request(self, endpoint, query, output_file, file_type):
        """Execute HTTP request and save response to file."""
        try:
            url = urljoin(self.base_url, endpoint)
            
            # Add pretty parameter to URL
            if '?' in url:
                url += "&pretty"
            else:
                url += "?pretty"
            
            headers = {
                'Content-Type': 'application/json'
            }
            
            # Set up authentication if username and password are provided
            auth = None
            if self.source_username and self.source_password:
                auth = (self.source_username, self.source_password)
            
            logging.info(f"Making request to: {url}")
            
            response = requests.get(
                url,
                headers=headers,
                json=query,
                auth=auth,
                timeout=self.timeout,
                verify=self.verify_ssl
            )
            
            response.raise_for_status()
            
            # Save the response to file
            with open(output_file, 'w', encoding='utf-8') as f:
                if response.headers.get('content-type', '').startswith('application/json'):
                    # Pretty print JSON
                    json.dump(response.json(), f, indent=2, ensure_ascii=False)
                else:
                    # Save as text
                    f.write(response.text)
            
            logging.info(f"Successfully collected {file_type} data to {output_file}")
            return True
            
        except requests.exceptions.RequestException as e:
            logging.error(f"Request failed for {file_type}: {e}")
            return False
        except json.JSONDecodeError as e:
            logging.error(f"Failed to parse JSON response for {file_type}: {e}")
            return False
        except Exception as e:
            logging.error(f"Unexpected error collecting {file_type}: {e}")
            return False

    def collect_all(self):
        """Collect all configuration files."""
        logging.info("Starting configuration collection...")
        
        results = {
            'reports': self.collect_reports(),
            'alerts': self.collect_alerts()
        }
        
        success_count = sum(results.values())
        total_count = len(results)
        
        logging.info(f"Collection completed: {success_count}/{total_count} files collected successfully")
        
        if success_count == total_count:
            logging.info("All files collected successfully!")
        else:
            logging.warning("Some files failed to collect. Check the logs for details.")
        
        return results

def main():
    """Main function to run the collector."""
    try:
        collector = ConfigCollector()
        results = collector.collect_all()
        
        # Print summary
        print("\n" + "="*50)
        print("COLLECTION SUMMARY")
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
            
    except FileNotFoundError:
        logging.error("config.ini file not found. Please create it first.")
        sys.exit(1)
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()