#!/usr/bin/env python3
"""
Local Export Script

This script exports JSON configuration files from the local Elasticsearch instance.
Run this script directly on the source server where Elasticsearch is running.
"""

import requests
import json
import os
import sys
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('export.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

class LocalExporter:
    def __init__(self, base_url='http://localhost:9200', output_dir='json_files'):
        """Initialize the exporter for local Elasticsearch."""
        self.base_url = base_url
        self.output_dir = output_dir
        self.timeout = 30
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Create output directory if it doesn't exist
        os.makedirs(self.output_dir, exist_ok=True)
        
        logging.info(f"Initialized exporter for: {self.base_url}")
        logging.info(f"Output directory: {self.output_dir}")

    def export_reports(self):
        """Export scheduled report definitions."""
        endpoint = "/vrm-scheduled-report-definition-vrm-ty-vrm-scheduled-report-definition/_search"
        query = {
            "query": {
                "match_all": {}
            },
            "size": 9999
        }
        
        output_file = os.path.join(self.output_dir, f'reports_{self.timestamp}.json')
        return self._execute_export(endpoint, query, output_file, 'reports')

    def export_alerts(self):
        """Export alert definitions."""
        endpoint = "/rt-alert-def-vrm-ty-rt-alert-def-vrm/_search"
        query = {
            "query": {
                "match_all": {}
            },
            "size": 9999
        }
        
        output_file = os.path.join(self.output_dir, f'alerts_{self.timestamp}.json')
        return self._execute_export(endpoint, query, output_file, 'alerts')

    def _execute_export(self, endpoint, query, output_file, export_type):
        """Execute HTTP request and save response to file."""
        try:
            url = f"{self.base_url}{endpoint}?pretty"
            
            headers = {
                'Content-Type': 'application/json'
            }
            
            logging.info(f"Exporting {export_type} from: {url}")
            
            response = requests.get(
                url,
                headers=headers,
                json=query,
                timeout=self.timeout
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
            
            # Get count of exported items
            data = response.json()
            count = data.get('hits', {}).get('total', {}).get('value', 0)
            
            logging.info(f"Successfully exported {count} {export_type} items to {output_file}")
            return True
            
        except requests.exceptions.RequestException as e:
            logging.error(f"Request failed for {export_type}: {e}")
            return False
        except json.JSONDecodeError as e:
            logging.error(f"Failed to parse JSON response for {export_type}: {e}")
            return False
        except Exception as e:
            logging.error(f"Unexpected error exporting {export_type}: {e}")
            return False

    def export_all(self):
        """Export all configuration files."""
        logging.info("Starting configuration export...")
        
        results = {
            'reports': self.export_reports(),
            'alerts': self.export_alerts()
        }
        
        success_count = sum(results.values())
        total_count = len(results)
        
        logging.info(f"Export completed: {success_count}/{total_count} exports successful")
        
        if success_count == total_count:
            logging.info("All configurations exported successfully!")
        else:
            logging.warning("Some exports failed. Check the logs for details.")
        
        return results

def main():
    """Main function to run the exporter."""
    try:
        exporter = LocalExporter()
        results = exporter.export_all()
        
        # Print summary
        print("\n" + "="*50)
        print("EXPORT SUMMARY")
        print("="*50)
        for export_type, success in results.items():
            status = "✓ SUCCESS" if success else "✗ FAILED"
            print(f"{export_type.upper()}: {status}")
        print(f"Output directory: {exporter.output_dir}")
        print(f"Timestamp: {exporter.timestamp}")
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