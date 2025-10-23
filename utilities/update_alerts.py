#!/usr/bin/env python3
"""
Alert JSON Update Utility

This script uses alert_devices.json as input to update alert configuration files.
It replaces device IPs, recipients, and syslog servers based on the extracted data.
"""

import json
import argparse
import os
import sys
import logging
from copy import deepcopy

# Configure logging
def setup_logging():
    """Setup logging configuration."""
    os.makedirs('logs', exist_ok=True)
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('logs/update_alerts.log'),
            logging.StreamHandler(sys.stdout)
        ]
    )

def load_input_data(input_file):
    """Load the alert_devices.json input file."""
    logging.info(f"Loading input data from: {input_file}")
    
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Validate required sections
        if 'deviceIp' not in data:
            logging.error("Missing required 'deviceIp' section in input file")
            return None
        
        if 'recipients' not in data:
            logging.error("Missing required 'recipients' section in input file")
            return None
        
        # Log what we found
        logging.info(f"Found {len(data['deviceIp'])} device IPs")
        logging.info(f"Found {len(data['recipients'])} recipients")
        
        if 'syslogservers' in data:
            logging.info(f"Found {len(data['syslogservers'])} syslog servers")
        else:
            logging.info("No syslog servers section found - will remove from output")
        
        if 'alert_names' in data:
            logging.info(f"Found {len(data['alert_names'])} alert names for filtering")
        else:
            logging.info("No alert names section found - no filtering will be applied")
        
        return data
        
    except Exception as e:
        logging.error(f"Error loading input file: {e}")
        return None

def update_device_ip_filters(obj, device_ips, path="", ip_index_counter=None):
    """Recursively update deviceIp filter values."""
    if ip_index_counter is None:
        ip_index_counter = {'index': 0}
    
    updated_count = 0
    
    if isinstance(obj, dict):
        # Check if this is a deviceIp filter
        if 'field' in obj and 'value' in obj and obj['field'] == 'deviceIp':
            old_value = obj['value']
            # Cycle through available device IPs
            if device_ips:
                new_ip = device_ips[ip_index_counter['index'] % len(device_ips)]
                obj['value'] = new_ip
                logging.debug(f"Updated deviceIp filter at {path}: {old_value} -> {new_ip}")
                ip_index_counter['index'] += 1
                updated_count += 1
        
        # Recursively process nested objects
        for key, value in obj.items():
            current_path = f"{path}.{key}" if path else key
            updated_count += update_device_ip_filters(value, device_ips, current_path, ip_index_counter)
    
    elif isinstance(obj, list):
        for i, item in enumerate(obj):
            updated_count += update_device_ip_filters(item, device_ips, f"{path}[{i}]", ip_index_counter)
    
    return updated_count

def create_device_ip_filters(device_ips):
    """Create new deviceIp filter structures for multiple IPs."""
    if not device_ips:
        return []
    
    # Create OR filter with multiple deviceIp filters
    device_filters = []
    for ip in device_ips:
        device_filter = {
            "type": "andFilter",
            "inverseFilter": False,
            "filters": [
                {
                    "type": "termFilter",
                    "inverseFilter": False,
                    "field": "deviceIp",
                    "value": ip
                }
            ]
        }
        device_filters.append(device_filter)
    
    if len(device_filters) == 1:
        return device_filters[0]
    else:
        return {
            "type": "orFilter",
            "inverseFilter": False,
            "filters": device_filters
        }

def update_recipients(obj, recipients, path=""):
    """Recursively update recipients sections."""
    updated_count = 0
    
    if isinstance(obj, dict):
        for key, value in obj.items():
            current_path = f"{path}.{key}" if path else key
            
            if key == 'recipients' and isinstance(value, list):
                # Replace recipients
                old_recipients = value.copy()
                obj[key] = recipients.copy()
                logging.debug(f"Updated recipients at {current_path}: {len(old_recipients)} -> {len(recipients)} recipients")
                updated_count += 1
            else:
                # Recursively process nested objects
                updated_count += update_recipients(value, recipients, current_path)
    
    elif isinstance(obj, list):
        for i, item in enumerate(obj):
            updated_count += update_recipients(item, recipients, f"{path}[{i}]")
    
    return updated_count

def update_syslog_servers(obj, syslog_servers, path=""):
    """Recursively update or remove syslogServers sections."""
    updated_count = 0
    
    if isinstance(obj, dict):
        for key, value in obj.items():
            current_path = f"{path}.{key}" if path else key
            
            if key == 'syslogServers':
                if syslog_servers:
                    # Update syslog servers
                    new_servers = []
                    for i, server in enumerate(syslog_servers):
                        server_obj = {
                            "host": server,
                            "port": 514,
                            "facility": "LOG_AUDIT",
                            "serverId": f"updated-server-{i+1}"
                        }
                        new_servers.append(server_obj)
                    
                    old_count = len(value) if isinstance(value, list) else 0
                    obj[key] = new_servers
                    logging.debug(f"Updated syslogServers at {current_path}: {old_count} -> {len(new_servers)} servers")
                    updated_count += 1
                else:
                    # Remove syslog servers section
                    obj[key] = []
                    logging.debug(f"Removed syslogServers at {current_path}")
                    updated_count += 1
            else:
                # Recursively process nested objects
                updated_count += update_syslog_servers(value, syslog_servers, current_path)
    
    elif isinstance(obj, list):
        for i, item in enumerate(obj):
            updated_count += update_syslog_servers(item, syslog_servers, f"{path}[{i}]")
    
    return updated_count

def filter_alerts_by_names(obj, alert_names, path=""):
    """Filter alerts based on the alert_names list, keeping only matching alerts."""
    if not alert_names:
        logging.info("No alert names provided - keeping all alerts")
        return obj, 0
    
    filtered_count = 0
    
    if isinstance(obj, dict):
        # Check if this object contains alert data with hits/hits array
        if 'hits' in obj and isinstance(obj['hits'], dict) and 'hits' in obj['hits']:
            hits_array = obj['hits']['hits']
            if isinstance(hits_array, list):
                original_count = len(hits_array)
                filtered_hits = []
                
                for hit in hits_array:
                    if isinstance(hit, dict) and '_source' in hit:
                        source = hit['_source']
                        if isinstance(source, dict) and 'name' in source:
                            alert_name = source['name']
                            if alert_name in alert_names:
                                filtered_hits.append(hit)
                                logging.debug(f"Keeping alert: {alert_name}")
                            else:
                                logging.debug(f"Filtering out alert: {alert_name}")
                                filtered_count += 1
                        else:
                            # Keep hits without name field
                            filtered_hits.append(hit)
                    else:
                        # Keep hits without _source field
                        filtered_hits.append(hit)
                
                obj['hits']['hits'] = filtered_hits
                obj['hits']['total'] = len(filtered_hits)
                
                logging.info(f"Filtered alerts at {path}: {original_count} -> {len(filtered_hits)} alerts (removed {filtered_count})")
                return obj, filtered_count
        
        # Recursively process nested objects
        for key, value in obj.items():
            current_path = f"{path}.{key}" if path else key
            obj[key], nested_filtered = filter_alerts_by_names(value, alert_names, current_path)
            filtered_count += nested_filtered
    
    elif isinstance(obj, list):
        for i, item in enumerate(obj):
            obj[i], nested_filtered = filter_alerts_by_names(item, alert_names, f"{path}[{i}]")
            filtered_count += nested_filtered
    
    return obj, filtered_count

def update_alert_file(alert_file, input_data, output_file):
    """Update an alert file with data from input_data."""
    logging.info(f"Processing alert file: {alert_file}")
    
    try:
        # Load alert file
        with open(alert_file, 'r', encoding='utf-8') as f:
            alert_data = json.load(f)
        
        # Make a deep copy to avoid modifying original
        updated_data = deepcopy(alert_data)
        
        # Filter alerts by names if alert_names section exists
        filtered_count = 0
        if 'alert_names' in input_data and input_data['alert_names']:
            updated_data, filtered_count = filter_alerts_by_names(
                updated_data, 
                input_data['alert_names']
            )
        
        # Update device IP filters
        device_ip_updates = update_device_ip_filters(
            updated_data, 
            input_data['deviceIp']
        )
        
        # Update recipients
        recipient_updates = update_recipients(
            updated_data, 
            input_data['recipients']
        )
        
        # Update or remove syslog servers
        syslog_updates = update_syslog_servers(
            updated_data, 
            input_data.get('syslogservers', [])
        )
        
        # Write updated file
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(updated_data, f, indent=2)
        
        logging.info(f"Updated alert file saved to: {output_file}")
        logging.info(f"Updates made - Filtered alerts: {filtered_count}, Device IPs: {device_ip_updates}, Recipients: {recipient_updates}, Syslog: {syslog_updates}")
        
        return True
        
    except Exception as e:
        logging.error(f"Error processing alert file: {e}")
        return False

def main():
    """Main function to update alert files."""
    parser = argparse.ArgumentParser(description='Update alert JSON files using alert_devices.json data')
    parser.add_argument('-i', '--input', default='json_files/alert_devices.json',
                       help='Input JSON file with device IPs, recipients, and syslog servers (default: json_files/alert_devices.json)')
    parser.add_argument('-a', '--alert', required=True,
                       help='Alert JSON file to update')
    parser.add_argument('-o', '--output', required=True,
                       help='Output JSON file name (will be saved to json_files/ folder)')
    parser.add_argument('-v', '--verbose', action='store_true',
                       help='Enable verbose debug logging')
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    logging.info("Starting alert file update process")
    
    # Check if input files exist
    if not os.path.exists(args.input):
        logging.error(f"Input file not found: {args.input}")
        return 1
    
    if not os.path.exists(args.alert):
        logging.error(f"Alert file not found: {args.alert}")
        return 1
    
    # Ensure output goes to json_files folder
    if not args.output.startswith('json_files/'):
        output_file = os.path.join('json_files', args.output)
    else:
        output_file = args.output
    
    # Create json_files directory if it doesn't exist
    os.makedirs('json_files', exist_ok=True)
    
    # Load input data
    input_data = load_input_data(args.input)
    if not input_data:
        return 1
    
    # Update alert file
    success = update_alert_file(args.alert, input_data, output_file)
    
    if success:
        logging.info("Alert file update completed successfully")
        return 0
    else:
        logging.error("Alert file update failed")
        return 1

if __name__ == '__main__':
    sys.exit(main())