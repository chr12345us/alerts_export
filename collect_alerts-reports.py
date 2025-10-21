#!/usr/bin/env python3
"""
Alerts & Reports Configuration Collector Script

This script creates an SSH tunnel to connect to a remote Elasticsearch instance
and collects JSON configuration files through the tunnel.
"""

import configparser
import requests
import json
import os
import sys
import logging
import time
import signal
import atexit
import argparse
import threading
import getpass
from urllib.parse import urljoin
from datetime import datetime
import paramiko
import socket
from select import select

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/collection.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

class SSHTunnelCollector:
    def __init__(self, config_file='config.ini'):
        """Initialize the collector with SSH tunnel configuration."""
        self.config = configparser.ConfigParser()
        
        # Check if config file exists, if not, use interactive input
        if not os.path.exists(config_file):
            logging.warning(f"Configuration file '{config_file}' not found.")
            print(f"\n⚠️  Configuration file '{config_file}' not found.")
            print("Please provide the SSH connection details for the source device:")
            self._setup_interactive_config()
        else:
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
        # Create logs directory if it doesn't exist
        os.makedirs('logs', exist_ok=True)
        
        # SSH tunnel components
        self.ssh_client = None
        self.tunnel_thread = None
        self.tunnel_server = None
        self.tunnel_running = False
        
        # Register cleanup function
        atexit.register(self.cleanup_tunnel)
        
        logging.info(f"Initialized SSH tunnel collector")
        logging.info(f"SSH: {self.ssh_username}@{self.ssh_host}:{self.ssh_port}")
        logging.info(f"Local tunnel port: {self.local_port}")
        logging.info(f"Timestamp: {self.timestamp}")

    def _setup_interactive_config(self):
        """Setup configuration interactively when config.ini doesn't exist."""
        print("\n" + "="*60)
        print("🔧 INTERACTIVE CONFIGURATION SETUP")
        print("="*60)
        
        # Get source device details
        print("\n📥 SOURCE DEVICE (where to collect configurations from):")
        ssh_host = input("SSH Host/IP address: ").strip()
        ssh_username = input("SSH Username: ").strip()
        ssh_password = getpass.getpass("SSH Password: ")
        
        # Optional settings with defaults
        ssh_port_input = input("SSH Port (default: 22): ").strip()
        ssh_port = int(ssh_port_input) if ssh_port_input else 22
        
        local_port_input = input("Local tunnel port (default: 9201): ").strip()
        local_port = int(local_port_input) if local_port_input else 9201
        
        # Create in-memory configuration
        self.config.add_section('source_device')
        self.config.set('source_device', 'ssh_host', ssh_host)
        self.config.set('source_device', 'ssh_username', ssh_username)
        self.config.set('source_device', 'ssh_password', ssh_password)
        self.config.set('source_device', 'ssh_port', str(ssh_port))
        self.config.set('source_device', 'local_port', str(local_port))
        
        # Add default settings section
        self.config.add_section('settings')
        self.config.set('settings', 'output_dir', 'json_files')
        self.config.set('settings', 'timeout', '30')
        self.config.set('settings', 'verify_ssl', 'false')
        
        print(f"\n✅ Configuration complete!")
        print(f"📡 Will connect to: {ssh_username}@{ssh_host}:{ssh_port}")
        print(f"🔗 Local tunnel port: {local_port}")
        print("\n💡 Tip: Create a 'config.ini' file to avoid entering this information each time.")
        print("="*60)

    def create_ssh_tunnel(self):
        """Create SSH tunnel to the remote Elasticsearch instance using paramiko."""
        try:
            logging.info(f"Creating SSH tunnel using paramiko: {self.ssh_username}@{self.ssh_host}:{self.ssh_port}")
            
            # Create SSH client
            self.ssh_client = paramiko.SSHClient()
            self.ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            # Connect to SSH server
            self.ssh_client.connect(
                hostname=self.ssh_host,
                port=self.ssh_port,
                username=self.ssh_username,
                password=self.ssh_password,
                timeout=10
            )
            
            logging.info("SSH connection established successfully")
            
            # Create port forwarding tunnel
            self.tunnel_running = True
            self.tunnel_thread = threading.Thread(
                target=self._tunnel_worker,
                daemon=True
            )
            self.tunnel_thread.start()
            
            # Wait for tunnel to establish
            logging.info("Waiting for SSH tunnel to establish...")
            time.sleep(3)
            
            # Test tunnel connectivity
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
                
        except paramiko.AuthenticationException:
            logging.error("SSH authentication failed. Check username and password.")
            return False
        except paramiko.SSHException as e:
            logging.error(f"SSH connection failed: {e}")
            return False
        except socket.error as e:
            logging.error(f"Network error connecting to SSH server: {e}")
            return False
        except Exception as e:
            logging.error(f"Failed to create SSH tunnel: {e}")
            return False

    def _tunnel_worker(self):
        """Worker thread for handling SSH tunnel port forwarding."""
        try:
            # Create a server socket to listen on local port
            server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server_socket.bind(('localhost', self.local_port))
            server_socket.listen(5)
            self.tunnel_server = server_socket
            
            logging.info(f"Tunnel server listening on localhost:{self.local_port}")
            
            while self.tunnel_running:
                # Accept incoming connections
                try:
                    server_socket.settimeout(1.0)  # Non-blocking accept
                    client_socket, addr = server_socket.accept()
                    
                    # Create tunnel for this connection
                    tunnel_thread = threading.Thread(
                        target=self._handle_tunnel_connection,
                        args=(client_socket,),
                        daemon=True
                    )
                    tunnel_thread.start()
                    
                except socket.timeout:
                    continue  # Check if tunnel_running is still True
                except Exception as e:
                    if self.tunnel_running:
                        logging.error(f"Error accepting tunnel connection: {e}")
                    break
                    
        except Exception as e:
            logging.error(f"Tunnel worker error: {e}")
        finally:
            if self.tunnel_server:
                try:
                    self.tunnel_server.close()
                except:
                    pass

    def _handle_tunnel_connection(self, client_socket):
        """Handle individual tunnel connection."""
        try:
            # Create channel through SSH connection
            transport = self.ssh_client.get_transport()
            channel = transport.open_channel('direct-tcpip', ('localhost', 9200), client_socket.getpeername())
            
            # Forward data between client and channel
            while True:
                ready, _, _ = select([client_socket, channel], [], [], 1.0)
                
                if not ready:
                    continue
                    
                if client_socket in ready:
                    data = client_socket.recv(4096)
                    if not data:
                        break
                    channel.send(data)
                
                if channel in ready:
                    data = channel.recv(4096)
                    if not data:
                        break
                    client_socket.send(data)
                    
        except Exception as e:
            logging.debug(f"Tunnel connection error: {e}")
        finally:
            try:
                client_socket.close()
            except:
                pass
            try:
                channel.close()
            except:
                pass

    def cleanup_tunnel(self):
        """Clean up SSH tunnel components."""
        if self.tunnel_running:
            logging.info("Closing SSH tunnel...")
            self.tunnel_running = False
            
        if self.tunnel_server:
            try:
                self.tunnel_server.close()
            except:
                pass
            self.tunnel_server = None
            
        if self.tunnel_thread and self.tunnel_thread.is_alive():
            try:
                self.tunnel_thread.join(timeout=5)
            except:
                pass
            self.tunnel_thread = None
            
        if self.ssh_client:
            try:
                self.ssh_client.close()
            except:
                pass
            self.ssh_client = None

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
    
    parser = argparse.ArgumentParser(description='Collect alerts & reports configuration files through SSH tunnel')
    parser.add_argument('--config', '-c', default='config.ini', help='Configuration file path')
    
    args = parser.parse_args()
    
    try:
        collector = SSHTunnelCollector(args.config)
        
        # Collect all configurations
        results = collector.collect_all()
        
        # Print summary
        print("\n" + "="*50)
        print("ALERTS & REPORTS COLLECTION SUMMARY")
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
            
    except KeyboardInterrupt:
        logging.info("Operation cancelled by user.")
        print("\n❌ Operation cancelled by user.")
        sys.exit(1)
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()