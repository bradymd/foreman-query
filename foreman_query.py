#!/usr/bin/env python3

import requests
import json
import argparse
import sys
import csv
import io
import os
from urllib3 import disable_warnings
from urllib3.exceptions import InsecureRequestWarning

# Disable SSL warnings since we're using --insecure
disable_warnings(InsecureRequestWarning)

class ForemanAPI:
    def __init__(self, url, username, password):
        self.base_url = url
        self.auth = (username, password)
        self.session = requests.Session()
        self.session.verify = False  # Equivalent to curl --insecure
        
    def get_hosts(self, search=None, per_page=1000):
        """Get hosts from Foreman API"""
        url = f"{self.base_url}/api/hosts"
        params = {"per_page": per_page}
        
        if search:
            params["search"] = search
            
        try:
            response = self.session.get(url, auth=self.auth, params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error querying Foreman API: {e}", file=sys.stderr)
            sys.exit(1)
    
    def get_host(self, hostname):
        """Get specific host details"""
        url = f"{self.base_url}/api/hosts/{hostname}"
        
        try:
            response = self.session.get(url, auth=self.auth)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error querying host {hostname}: {e}", file=sys.stderr)
            sys.exit(1)

def format_host_data(hosts_data):
    """Format host data for output"""
    if 'results' in hosts_data:
        # Multiple hosts
        formatted = []
        for host in hosts_data['results']:
            formatted.append({
                'name': host.get('name'),
                'hostgroup': host.get('hostgroup_title'),
                'os': host.get('operatingsystem_name'),
                'kernel': host.get('reported_data', {}).get('kernel_version', 'N/A') if host.get('reported_data') else 'N/A',
                'ip': host.get('ip'),
                'last_report': host.get('last_report'),
                'status': host.get('global_status_label')
            })
        return formatted
    else:
        # Single host
        return {
            'name': hosts_data.get('name'),
            'hostgroup': hosts_data.get('hostgroup_title'),
            'os': hosts_data.get('operatingsystem_name'),
            'kernel': hosts_data.get('reported_data', {}).get('kernel_version', 'N/A') if hosts_data.get('reported_data') else 'N/A',
            'ip': hosts_data.get('ip'),
            'last_report': hosts_data.get('last_report'),
            'status': hosts_data.get('global_status_label')
        }

def output_csv(data):
    """Output data in CSV format"""
    if isinstance(data, list):
        if not data:
            return
        # Multiple hosts
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=['name', 'hostgroup', 'os', 'kernel', 'ip', 'last_report', 'status'])
        writer.writeheader()
        writer.writerows(data)
        print(output.getvalue().strip())
    else:
        # Single host
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=['name', 'hostgroup', 'os', 'kernel', 'ip', 'last_report', 'status'])
        writer.writeheader()
        writer.writerow(data)
        print(output.getvalue().strip())

def main():
    parser = argparse.ArgumentParser(description='Query Foreman hosts')
    parser.add_argument('-a', '--all', action='store_true', help='Show all hosts')
    parser.add_argument('-s', '--search', help='Search for hosts containing term')
    parser.add_argument('-n', '--name', help='Get specific host details')
    parser.add_argument('-g', '--hostgroup', help='Filter by hostgroup')
    parser.add_argument('-e', '--environment', help='Filter by environment')
    parser.add_argument('--csv', action='store_true', help='Output in CSV format instead of JSON')
    parser.add_argument('--url', default=os.getenv('FOREMAN_URL'), 
                       help='Foreman URL (default: from FOREMAN_URL env var)')
    parser.add_argument('--username', default=os.getenv('FOREMAN_USERNAME'), 
                       help='Username (default: from FOREMAN_USERNAME env var)')
    parser.add_argument('--password', default=os.getenv('FOREMAN_PASSWORD'), 
                       help='Password (default: from FOREMAN_PASSWORD env var)')
    
    args = parser.parse_args()
    
    # Validate required parameters
    if not args.url:
        print("Error: Foreman URL required. Set FOREMAN_URL environment variable or use --url", file=sys.stderr)
        sys.exit(1)
    
    if not args.username or not args.password:
        print("Error: Foreman credentials required. Set FOREMAN_USERNAME and FOREMAN_PASSWORD environment variables or use --username and --password", file=sys.stderr)
        sys.exit(1)
    
    # Initialize Foreman API client
    foreman = ForemanAPI(args.url, args.username, args.password)
    
    if args.name:
        # Get specific host
        host_data = foreman.get_host(args.name)
        result = format_host_data(host_data)
    elif args.search:
        # Search hosts
        hosts_data = foreman.get_hosts(search=f"name~{args.search}")
        result = format_host_data(hosts_data)
    elif args.hostgroup:
        # Filter by hostgroup
        hosts_data = foreman.get_hosts()
        filtered_hosts = []
        for host in hosts_data['results']:
            if host.get('hostgroup_title') == args.hostgroup:
                filtered_hosts.append(host)
        hosts_data['results'] = filtered_hosts
        result = format_host_data(hosts_data)
    elif args.environment:
        # Filter by environment
        hosts_data = foreman.get_hosts()
        filtered_hosts = []
        for host in hosts_data['results']:
            if host.get('environment_name') == args.environment:
                filtered_hosts.append(host)
        hosts_data['results'] = filtered_hosts
        result = format_host_data(hosts_data)
    elif args.all:
        # Get all hosts
        hosts_data = foreman.get_hosts()
        result = format_host_data(hosts_data)
    else:
        parser.print_help()
        sys.exit(1)
    
    # Output in requested format
    if args.csv:
        output_csv(result)
    else:
        print(json.dumps(result, indent=2))

if __name__ == '__main__':
    main()
