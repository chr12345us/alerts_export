#!/usr/bin/env python3
"""
Alert JSON Analyzer Utility

This script analyzes JSON alert files to extract device IPs, recipients, and syslog servers.
Outputs the results to a JSON file called "alert_devices.json".
"""

import json
import argparse
import os
import sys
import re
import logging
from collections import defaultdict
import ipaddress

# Configure logging
def setup_logging():
    """Setup logging configuration."""
    os.makedirs('logs', exist_ok=True)
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('logs/analysis.log'),
            logging.StreamHandler(sys.stdout)
        ]
    )

def extract_device_ips(data):
    """Extract device IPs from filter fields where field='deviceIp' and value contains IP."""
    device_ips = set()
    
    def search_for_device_ips(obj, path=""):
        """Recursively search for deviceIp filter fields."""
        if isinstance(obj, dict):
            # Check if this dict has both 'field' and 'value' keys
            if 'field' in obj and 'value' in obj:
                if obj['field'] == 'deviceIp' and isinstance(obj['value'], str):
                    ip = obj['value'].strip()
                    if is_valid_ip(ip):
                        device_ips.add(ip)
                        logging.debug(f"Found deviceIp filter at {path}: {ip}")
            
            # Recursively search in nested structures
            for key, value in obj.items():
                current_path = f"{path}.{key}" if path else key
                search_for_device_ips(value, current_path)
                
        elif isinstance(obj, list):
            for i, item in enumerate(obj):
                search_for_device_ips(item, f"{path}[{i}]")
    
    search_for_device_ips(data)
    return sorted(list(device_ips))

def extract_recipients(data):
    """Extract recipients from recipients fields."""
    recipients = set()
    
    def search_for_recipients(obj, path=""):
        """Recursively search for recipients fields."""
        if isinstance(obj, dict):
            for key, value in obj.items():
                current_path = f"{path}.{key}" if path else key
                
                # Look specifically for recipients field
                if key.lower() == 'recipients':
                    if isinstance(value, list):
                        for recipient in value:
                            if isinstance(recipient, str):
                                clean_recipient = recipient.strip()
                                if clean_recipient:
                                    recipients.add(clean_recipient)
                                    logging.debug(f"Found recipient at {current_path}: {clean_recipient}")
                    elif isinstance(value, str):
                        clean_recipient = value.strip()
                        if clean_recipient:
                            recipients.add(clean_recipient)
                            logging.debug(f"Found recipient at {current_path}: {clean_recipient}")
                
                # Recursively search in nested structures
                search_for_recipients(value, current_path)
                
        elif isinstance(obj, list):
            for i, item in enumerate(obj):
                search_for_recipients(item, f"{path}[{i}]")
    
    search_for_recipients(data)
    return sorted(list(recipients))

def extract_syslog_servers(data):
    """Extract syslog servers from syslogServers fields."""
    syslog_servers = set()
    
    def search_for_syslog_servers(obj, path=""):
        """Recursively search for syslogServers fields."""
        if isinstance(obj, dict):
            for key, value in obj.items():
                current_path = f"{path}.{key}" if path else key
                
                # Look specifically for syslogServers field
                if key.lower() == 'syslogservers':
                    if isinstance(value, list):
                        for server in value:
                            if isinstance(server, str):
                                clean_server = server.strip()
                                if clean_server:
                                    syslog_servers.add(clean_server)
                                    logging.debug(f"Found syslog server at {current_path}: {clean_server}")
                            elif isinstance(server, dict):
                                # Handle case where syslog server is an object
                                for server_key, server_value in server.items():
                                    if isinstance(server_value, str):
                                        clean_server = server_value.strip()
                                        if clean_server and (is_valid_ip(clean_server) or '.' in clean_server):
                                            syslog_servers.add(clean_server)
                                            logging.debug(f"Found syslog server at {current_path}.{server_key}: {clean_server}")
                    elif isinstance(value, str):
                        clean_server = value.strip()
                        if clean_server:
                            syslog_servers.add(clean_server)
                            logging.debug(f"Found syslog server at {current_path}: {clean_server}")
                
                # Recursively search in nested structures
                search_for_syslog_servers(value, current_path)
                
        elif isinstance(obj, list):
            for i, item in enumerate(obj):
                search_for_syslog_servers(item, f"{path}[{i}]")
    
    search_for_syslog_servers(data)
    return sorted(list(syslog_servers))

def extract_alert_names(data):
    """Extract alert names from name fields."""
    alert_names = set()
    
    def search_for_names(obj, path=""):
        """Recursively search for name fields in alert sources."""
        if isinstance(obj, dict):
            for key, value in obj.items():
                current_path = f"{path}.{key}" if path else key
                
                # Look for name field in _source sections (alert definitions)
                if key == 'name' and isinstance(value, str) and '_source' in path:
                    clean_name = value.strip()
                    if clean_name:
                        alert_names.add(clean_name)
                        logging.debug(f"Found alert name at {current_path}: {clean_name}")
                
                # Recursively search in nested structures
                search_for_names(value, current_path)
                
        elif isinstance(obj, list):
            for i, item in enumerate(obj):
                search_for_names(item, f"{path}[{i}]")
    
    search_for_names(data)
    return sorted(list(alert_names))

def is_valid_ip(ip_string):
    """Check if a string is a valid IP address."""
    try:
        ipaddress.ip_address(ip_string)
        # Exclude common non-device IPs
        return not ip_string.startswith(('0.', '255.')) and ip_string != '127.0.0.1'
    except ValueError:
        return False

def analyze_json_file(file_path):
    """Analyze a single JSON file for alerts data."""
    logging.info(f"Analyzing file: {file_path}")
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        logging.error(f"Error reading {file_path}: {e}")
        return None
    
    # Extract different types of data
    alert_names = extract_alert_names(data)
    device_ips = extract_device_ips(data)
    recipients = extract_recipients(data)
    syslog_servers = extract_syslog_servers(data)
    
    # Log summaries
    logging.info(f"Found {len(alert_names)} alert names")
    logging.info(f"Found {len(device_ips)} device IPs")
    logging.info(f"Found {len(recipients)} recipients")
    logging.info(f"Found {len(syslog_servers)} syslog servers")
    
    if alert_names:
        logging.info("Alert names summary:")
        for name in alert_names[:10]:  # Show first 10
            logging.info(f"  - {name}")
        if len(alert_names) > 10:
            logging.info(f"  ... and {len(alert_names) - 10} more")
    
    if recipients:
        logging.info("Recipients summary:")
        for recipient in recipients[:10]:  # Show first 10
            logging.info(f"  - {recipient}")
        if len(recipients) > 10:
            logging.info(f"  ... and {len(recipients) - 10} more")
    
    if device_ips:
        logging.info("Device IPs summary:")
        for ip in device_ips[:10]:  # Show first 10
            logging.info(f"  - {ip}")
        if len(device_ips) > 10:
            logging.info(f"  ... and {len(device_ips) - 10} more")
    
    if syslog_servers:
        logging.info("Syslog servers summary:")
        for server in syslog_servers[:10]:  # Show first 10
            logging.info(f"  - {server}")
        if len(syslog_servers) > 10:
            logging.info(f"  ... and {len(syslog_servers) - 10} more")
    
    return {
        'alert_names': alert_names,
        'device_ips': device_ips,
        'recipients': recipients,
        'syslog_servers': syslog_servers
    }

def main():
    """Main function to analyze alert JSON files."""
    parser = argparse.ArgumentParser(description='Analyze JSON alert files to extract device IPs, recipients, and syslog servers')
    parser.add_argument('files', nargs='+', help='JSON files to analyze')
    parser.add_argument('-o', '--output', default='alert_devices.json', 
                       help='Output JSON file (default: alert_devices.json)')
    parser.add_argument('-v', '--verbose', action='store_true', 
                       help='Enable verbose debug logging')
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    logging.info("Starting alert analysis")
    
    # Collect all data from all files
    all_device_ips = set()
    all_recipients = set()
    all_syslog_servers = set()
    all_alert_names = set()
    
    for file_path in args.files:
        if not os.path.exists(file_path):
            logging.error(f"File not found: {file_path}")
            continue
        
        result = analyze_json_file(file_path)
        if result:
            all_alert_names.update(result['alert_names'])
            all_device_ips.update(result['device_ips'])
            all_recipients.update(result['recipients'])
            all_syslog_servers.update(result['syslog_servers'])
    
    # Prepare output data with the three requested sections
    output_data = {
        'deviceIp': sorted(list(all_device_ips)),
        'recipients': sorted(list(all_recipients)),
        'syslogservers': sorted(list(all_syslog_servers))
    }
    
    # Write results to output file
    try:
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2)
        logging.info(f"Results written to {args.output}")
    except Exception as e:
        logging.error(f"Error writing output file: {e}")
        return 1
    
    # Print final summary
    logging.info("=== FINAL SUMMARY ===")
    logging.info(f"Total alert names found: {len(all_alert_names)}")
    logging.info(f"Total device IPs found: {len(all_device_ips)}")
    logging.info(f"Total recipients found: {len(all_recipients)}")
    logging.info(f"Total syslog servers found: {len(all_syslog_servers)}")
    
    return 0

if __name__ == '__main__':
    sys.exit(main())