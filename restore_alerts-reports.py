#!/usr/bin/env python3
"""
Alerts & Reports Configuration Restore Script

This script creates an SSH tunnel to connect to a remote Elasticsearch instance
and restores JSON configuration files through the tunnel.
"""

import configparser
import requests
import json
import os
import sys
import logging
import subprocess
import time
import signal
import atexit
import argparse
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/restore.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

class SSHTunnelRestorer:
    def __init__(self, config_file='config.ini'):
        """Initialize the restorer with SSH tunnel configuration."""
        self.config = configparser.ConfigParser()
        self.config.read(config_file)
        
        # SSH tunnel settings
        self.ssh_host = self.config.get('destination_device', 'ssh_host')
        self.ssh_port = self.config.getint('destination_device', 'ssh_port', fallback=22)
        self.ssh_username = self.config.get('destination_device', 'ssh_username')
        self.ssh_password = self.config.get('destination_device', 'ssh_password', fallback=None)
        self.local_port = self.config.getint('destination_device', 'local_port', fallback=9202)
        
        # Settings
        self.input_dir = self.config.get('settings', 'output_dir', fallback='json_files')
        self.timeout = self.config.getint('settings', 'timeout', fallback=30)
        self.verify_ssl = self.config.getboolean('settings', 'verify_ssl', fallback=False)
        
        # SSH tunnel process
        self.tunnel_process = None
        
        # Create logs directory if it doesn't exist
        os.makedirs('logs', exist_ok=True)
        
        # Register cleanup function
        atexit.register(self.cleanup_tunnel)
        
        logging.info(f"Initialized SSH tunnel restorer")
        logging.info(f"SSH: {self.ssh_username}@{self.ssh_host}:{self.ssh_port}")
        logging.info(f"Local tunnel port: {self.local_port}")

    def create_ssh_tunnel(self):
        """Create SSH tunnel to the remote Elasticsearch instance."""
        try:
            # Build SSH command
            ssh_cmd = [
                'ssh',
                '-N',  # Do not execute remote command
                '-L', f'{self.local_port}:localhost:9200',  # Local port forwarding to Elasticsearch
                '-p', str(self.ssh_port),
                f'{self.ssh_username}@{self.ssh_host}',
                '-o', 'StrictHostKeyChecking=no',
                '-o', 'UserKnownHostsFile=/dev/null',
                '-o', 'LogLevel=ERROR'
            ]
            
            # If password is provided, use sshpass
            if self.ssh_password:
                ssh_cmd = ['sshpass', '-p', self.ssh_password] + ssh_cmd
            
            logging.info(f"Creating SSH tunnel: {' '.join([c for c in ssh_cmd if c != self.ssh_password])}")
            
            # Start SSH tunnel
            self.tunnel_process = subprocess.Popen(
                ssh_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            # Wait for tunnel to establish
            time.sleep(3)
            
            # Check if tunnel is still running
            if self.tunnel_process.poll() is not None:
                stdout, stderr = self.tunnel_process.communicate()
                logging.error(f"SSH tunnel failed to start: {stderr.decode()}")
                return False
            
            # Test tunnel connectivity
            try:
                response = requests.get(
                    f'http://localhost:{self.local_port}',
                    timeout=5
                )
                logging.info("SSH tunnel established successfully")
                return True
            except requests.exceptions.RequestException as e:
                logging.error(f"SSH tunnel test failed: {e}")
                self.cleanup_tunnel()
                return False
                
        except FileNotFoundError as e:
            if 'sshpass' in str(e):
                logging.error("sshpass not found. Install with: sudo apt-get install sshpass")
            else:
                logging.error(f"SSH command not found: {e}")
            return False
        except Exception as e:
            logging.error(f"Failed to create SSH tunnel: {e}")
            return False

    def cleanup_tunnel(self):
        """Clean up SSH tunnel process."""
        if self.tunnel_process and self.tunnel_process.poll() is None:
            logging.info("Closing SSH tunnel...")
            self.tunnel_process.terminate()
            try:
                self.tunnel_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.tunnel_process.kill()
            self.tunnel_process = None

    def restore_from_file(self, json_file_path):
        """Restore configuration from a single JSON file through SSH tunnel."""
        try:
            if not os.path.exists(json_file_path):
                logging.error(f"File not found: {json_file_path}")
                return False

            logging.info(f"Restoring from: {json_file_path}")

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
        """Restore a single configuration item through SSH tunnel."""
        try:
            # Extract the necessary fields from the Elasticsearch document
            index = item.get('_index')
            doc_id = item.get('_id')
            source = item.get('_source')

            if not all([index, doc_id, source]):
                logging.error(f"Missing required fields in item: {item}")
                return False

            # Construct the URL for the PUT request (through tunnel)
            url = f"http://localhost:{self.local_port}/{index}/_doc/{doc_id}"
            
            headers = {
                'Content-Type': 'application/json'
            }

            # Make the PUT request to restore the document (no auth needed for localhost)
            response = requests.put(
                url,
                json=source,
                headers=headers,
                timeout=self.timeout,
                verify=self.verify_ssl
            )

            response.raise_for_status()
            
            result = response.json()
            action = result.get('result', 'unknown')
            logging.debug(f"Restored item {doc_id}: {action}")
            
            return True

        except requests.exceptions.RequestException as e:
            logging.error(f"Request failed for item {doc_id}: {e}")
            return False
        except Exception as e:
            logging.error(f"Unexpected error restoring item {doc_id}: {e}")
            return False

    def restore_alerts(self, alerts_filename=None):
        """Restore alert definitions through SSH tunnel."""
        if alerts_filename is None:
            alerts_filename = 'alerts.json'
        
        # If filename contains path separators, use as-is, otherwise join with input_dir
        if os.path.sep in alerts_filename or '/' in alerts_filename:
            alerts_file = alerts_filename
        else:
            alerts_file = os.path.join(self.input_dir, alerts_filename)
            
        logging.info(f"Starting alerts restoration from: {alerts_file}")
        return self.restore_from_file(alerts_file)

    def restore_reports(self, reports_filename=None):
        """Restore report definitions through SSH tunnel."""
        if reports_filename is None:
            reports_filename = 'reports.json'
        
        # If filename contains path separators, use as-is, otherwise join with input_dir
        if os.path.sep in reports_filename or '/' in reports_filename:
            reports_file = reports_filename
        else:
            reports_file = os.path.join(self.input_dir, reports_filename)
            
        logging.info(f"Starting reports restoration from: {reports_file}")
        return self.restore_from_file(reports_file)

    def extract_definitions_only(self, json_file_path, output_file_path):
        """Extract only the _source definitions from a JSON file and save to a new file."""
        try:
            if not os.path.exists(json_file_path):
                logging.error(f"File not found: {json_file_path}")
                return False

            logging.info(f"Extracting definitions from: {json_file_path}")

            with open(json_file_path, 'r', encoding='utf-8') as file:
                json_data = json.load(file)

            # Check if this is an Elasticsearch response format
            if 'hits' not in json_data:
                logging.error(f"Invalid JSON format in {json_file_path}: missing 'hits' field")
                return False

            hits = json_data.get('hits', {}).get('hits', [])
            
            if not hits:
                logging.warning(f"No data to extract in {json_file_path}")
                return True

            # Extract only the _source definitions
            definitions = []
            for item in hits:
                source = item.get('_source')
                if source:
                    definitions.append(source)

            # Save the definitions to the output file
            with open(output_file_path, 'w', encoding='utf-8') as output_file:
                json.dump({
                    "definitions": definitions,
                    "count": len(definitions),
                    "extracted_from": os.path.basename(json_file_path)
                }, output_file, indent=2, ensure_ascii=False)

            logging.info(f"Successfully extracted {len(definitions)} definitions to {output_file_path}")
            return True

        except json.JSONDecodeError as e:
            logging.error(f"Failed to parse JSON in {json_file_path}: {e}")
            return False
        except Exception as e:
            logging.error(f"Unexpected error extracting definitions from {json_file_path}: {e}")
            return False

    def restore_all(self, alerts_filename=None, reports_filename=None):
        """Restore all configuration files through SSH tunnel."""
        logging.info("Starting SSH tunnel configuration restoration...")
        
        # Create SSH tunnel first
        if not self.create_ssh_tunnel():
            logging.error("Failed to create SSH tunnel. Aborting restoration.")
            return {'reports': False, 'alerts': False}
        
        try:
            results = {
                'alerts': self.restore_alerts(alerts_filename),
                'reports': self.restore_reports(reports_filename)
            }
            
            success_count = sum(results.values())
            total_count = len(results)
            
            logging.info(f"Restoration completed: {success_count}/{total_count} file types restored successfully")
            
            if success_count == total_count:
                logging.info("All configurations restored successfully!")
            else:
                logging.warning("Some configurations failed to restore. Check the logs for details.")
            
            return results
            
        finally:
            # Always cleanup tunnel
            self.cleanup_tunnel()

def signal_handler(signum, frame):
    """Handle interrupt signal to cleanup tunnel."""
    logging.info("Interrupt received, cleaning up...")
    sys.exit(1)

def main():
    """Main function to run the SSH tunnel restorer."""
    # Register signal handler for cleanup
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    parser = argparse.ArgumentParser(description='Restore alerts & reports configuration files through SSH tunnel')
    parser.add_argument('--file', '-f', help='Restore from a specific JSON file (full path)')
    parser.add_argument('-a', '--alerts', nargs='?', const='alerts.json', 
                       help='Restore alerts. Specify filename or full path (default: alerts.json)')
    parser.add_argument('-r', '--reports', nargs='?', const='reports.json',
                       help='Restore reports. Specify filename or full path (default: reports.json)')
    parser.add_argument('-as', '--alerts-source', nargs='?', const='alerts.json',
                       help='Extract alert source definitions only. Specify input filename or full path (default: alerts.json)')
    parser.add_argument('-rs', '--reports-source', nargs='?', const='reports.json',
                       help='Extract report source definitions only. Specify input filename or full path (default: reports.json)')
    parser.add_argument('--config', '-c', default='config.ini', help='Configuration file path')
    
    args = parser.parse_args()
    
    try:
        restorer = SSHTunnelRestorer(args.config)
        
        results = {}
        
        if args.file:
            # Create tunnel and restore from specific file
            if not restorer.create_ssh_tunnel():
                logging.error("Failed to create SSH tunnel. Aborting.")
                sys.exit(1)
            try:
                filename = os.path.basename(args.file)
                results[filename] = restorer.restore_from_file(args.file)
            finally:
                restorer.cleanup_tunnel()
        elif args.alerts_source:
            # Extract alert source definitions only (no tunnel needed)
            # If filename contains path separators, use as-is, otherwise join with input_dir
            if os.path.sep in args.alerts_source or '/' in args.alerts_source:
                input_file = args.alerts_source
            else:
                input_file = os.path.join(restorer.input_dir, args.alerts_source)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = os.path.join(restorer.input_dir, f'alerts_definitions_{timestamp}.json')
            results['alerts_extract'] = restorer.extract_definitions_only(input_file, output_file)
        elif args.reports_source:
            # Extract report source definitions only (no tunnel needed)
            # If filename contains path separators, use as-is, otherwise join with input_dir
            if os.path.sep in args.reports_source or '/' in args.reports_source:
                input_file = args.reports_source
            else:
                input_file = os.path.join(restorer.input_dir, args.reports_source)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = os.path.join(restorer.input_dir, f'reports_definitions_{timestamp}.json')
            results['reports_extract'] = restorer.extract_definitions_only(input_file, output_file)
        elif args.alerts and args.reports:
            # Restore both alerts and reports with specified filenames
            results = restorer.restore_all(args.alerts, args.reports)
        elif args.alerts:
            # Create tunnel and restore only alerts
            if not restorer.create_ssh_tunnel():
                logging.error("Failed to create SSH tunnel. Aborting.")
                sys.exit(1)
            try:
                results['alerts'] = restorer.restore_alerts(args.alerts)
            finally:
                restorer.cleanup_tunnel()
        elif args.reports:
            # Create tunnel and restore only reports
            if not restorer.create_ssh_tunnel():
                logging.error("Failed to create SSH tunnel. Aborting.")
                sys.exit(1)
            try:
                results['reports'] = restorer.restore_reports(args.reports)
            finally:
                restorer.cleanup_tunnel()
        else:
            # Restore all configurations with default filenames
            results = restorer.restore_all()
        
        # Print summary
        print("\n" + "="*50)
        print("ALERTS & REPORTS RESTORATION SUMMARY")
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