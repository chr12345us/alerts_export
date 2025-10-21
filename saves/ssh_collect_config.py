#!/usr/bin/env python3
"""
SSH Tunnel Configuration Collector Script

This script creates an SSH tunnel to connect to a remote Elasticsearch instance
and collects JSON configuration files through the tunnel.
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
from urllib.parse import urljoin

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('ssh_collection.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

class SSHTunnelCollector:
    def __init__(self, config_file='config.ini'):
        """Initialize the collector with SSH tunnel configuration."""
        self.config = configparser.ConfigParser()
        self.config.read(config_file)
        
        # SSH tunnel settings
        self.ssh_host = self.config.get('source_device', 'ssh_host')
        self.ssh_port = self.config.getint('source_device', 'ssh_port', fallback=22)
        self.ssh_username = self.config.get('source_device', 'ssh_username')
        self.ssh_password = self.config.get('source_device', 'ssh_password', fallback=None)
        self.local_port = self.config.getint('source_device', 'local_port', fallback=9201)
        
        # Settings
        self.output_dir = self.config.get('settings', 'output_dir', fallback='json_files')
        self.timeout = self.config.getint('settings', 'timeout', fallback=30)
        self.verify_ssl = self.config.getboolean('settings', 'verify_ssl', fallback=False)
        
        # Create timestamp for this collection session
        from datetime import datetime
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Create output directory if it doesn't exist
        os.makedirs(self.output_dir, exist_ok=True)
        
        # SSH tunnel process
        self.tunnel_process = None
        
        # Register cleanup function
        atexit.register(self.cleanup_tunnel)
        
        logging.info(f"Initialized SSH tunnel collector")
        logging.info(f"SSH: {self.ssh_username}@{self.ssh_host}:{self.ssh_port}")
        logging.info(f"Local tunnel port: {self.local_port}")
        logging.info(f"Timestamp: {self.timestamp}")

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
            
            # Log command without password for security
            log_cmd = [c if c != self.ssh_password else '***' for c in ssh_cmd]
            logging.info(f"Creating SSH tunnel: {' '.join(log_cmd)}")
            
            # Start SSH tunnel
            self.tunnel_process = subprocess.Popen(
                ssh_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            # Wait for tunnel to establish
            logging.info("Waiting for SSH tunnel to establish...")
            time.sleep(5)  # Increased wait time
            
            # Check if tunnel is still running
            poll_result = self.tunnel_process.poll()
            if poll_result is not None:
                stdout, stderr = self.tunnel_process.communicate()
                logging.error(f"SSH tunnel process exited with code {poll_result}")
                logging.error(f"SSH stderr: {stderr.decode()}")
                logging.error(f"SSH stdout: {stdout.decode()}")
                return False
            
            logging.info(f"SSH tunnel process is running (PID: {self.tunnel_process.pid})")
            
            # Test tunnel connectivity with more detailed error handling
            try:
                logging.info(f"Testing connection to localhost:{self.local_port}")
                response = requests.get(
                    f'http://localhost:{self.local_port}',
                    timeout=10
                )
                logging.info("SSH tunnel established successfully")
                return True
            except requests.exceptions.ConnectionError as e:
                logging.error(f"SSH tunnel test failed - connection error: {e}")
                # Check if the port is actually listening
                import socket
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                try:
                    result = sock.connect_ex(('localhost', self.local_port))
                    if result == 0:
                        logging.info(f"Port {self.local_port} is listening but Elasticsearch might not be responding")
                    else:
                        logging.error(f"Port {self.local_port} is not listening")
                except Exception as port_test_error:
                    logging.error(f"Port test failed: {port_test_error}")
                finally:
                    sock.close()
                
                self.cleanup_tunnel()
                return False
            except requests.exceptions.Timeout as e:
                logging.error(f"SSH tunnel test failed - timeout: {e}")
                self.cleanup_tunnel()
                return False
            except Exception as e:
                logging.error(f"SSH tunnel test failed - unexpected error: {e}")
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

    def collect_reports(self):
        """Collect scheduled report definitions through SSH tunnel."""
        endpoint = "/vrm-scheduled-report-definition-vrm-ty-vrm-scheduled-report-definition/_search"
        query = {
            "query": {
                "match_all": {}
            },
            "size": 9999
        }
        
        output_file = os.path.join(self.output_dir, f'reports_{self.timestamp}.json')
        return self._execute_request(endpoint, query, output_file, 'reports')

    def collect_alerts(self):
        """Collect alert definitions through SSH tunnel."""
        endpoint = "/rt-alert-def-vrm-ty-rt-alert-def-vrm/_search"
        query = {
            "query": {
                "match_all": {}
            },
            "size": 9999
        }
        
        output_file = os.path.join(self.output_dir, f'alerts_{self.timestamp}.json')
        return self._execute_request(endpoint, query, output_file, 'alerts')

    def _execute_request(self, endpoint, query, output_file, file_type):
        """Execute HTTP request through SSH tunnel and save response to file."""
        try:
            # Use localhost with tunnel port
            url = f"http://localhost:{self.local_port}{endpoint}?pretty"
            
            headers = {
                'Content-Type': 'application/json'
            }
            
            logging.info(f"Making request through tunnel: {url}")
            
            response = requests.get(
                url,
                headers=headers,
                json=query,
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
        """Collect all configuration files through SSH tunnel."""
        logging.info("Starting SSH tunnel configuration collection...")
        
        # Create SSH tunnel first
        if not self.create_ssh_tunnel():
            logging.error("Failed to create SSH tunnel. Aborting collection.")
            return {'reports': False, 'alerts': False}
        
        try:
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
            
        finally:
            # Always cleanup tunnel
            self.cleanup_tunnel()

def signal_handler(signum, frame):
    """Handle interrupt signal to cleanup tunnel."""
    logging.info("Interrupt received, cleaning up...")
    sys.exit(1)

def main():
    """Main function to run the SSH tunnel collector."""
    # Register signal handler for cleanup
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        collector = SSHTunnelCollector()
        results = collector.collect_all()
        
        # Print summary
        print("\n" + "="*50)
        print("SSH TUNNEL COLLECTION SUMMARY")
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