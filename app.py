#!/usr/bin/env python3

from flask import Flask, render_template, request, jsonify, make_response
import requests
import json
import csv
import io
import re
import os
from urllib3 import disable_warnings
from urllib3.exceptions import InsecureRequestWarning

# Disable SSL warnings since we're using --insecure
disable_warnings(InsecureRequestWarning)

app = Flask(__name__)

def get_fact_category(fact_name):
    """Categorize facts based on their names for filtering"""
    fact_name = fact_name.lower()
    
    if any(term in fact_name for term in ['os::', 'operating', 'kernel', 'distro', 'selinux', 'osfamily']):
        return 'os'
    elif any(term in fact_name for term in ['processor', 'cpu', 'memory::', 'memorysize', 'swap', 'cores', 'threads']):
        return 'hardware'
    elif any(term in fact_name for term in ['networking::', 'ip', 'mac', 'interface', 'dhcp', 'network', 'mtu']):
        return 'network'
    elif any(term in fact_name for term in ['disk', 'partition', 'mountpoint', 'blockdevice', 'filesystem']):
        return 'disk'
    elif any(term in fact_name for term in ['memory::', 'memorysize', 'swap']):
        return 'memory'
    elif any(term in fact_name for term in ['ssh::', 'sshfp', 'sshrsa', 'sshed25519', 'sshecdsa']):
        return 'ssh'
    elif any(term in fact_name for term in ['uptime', 'timezone', 'fqdn', 'hostname', 'uuid', 'virtual', 'manufacturer']):
        return 'system'
    else:
        return 'other'

# Make the function available in templates
app.jinja_env.globals.update(get_fact_category=get_fact_category)

class ForemanAPI:
    def __init__(self, url=None, username=None, password=None):
        self.base_url = url or os.getenv('FOREMAN_URL')
        
        if not self.base_url:
            raise ValueError("Foreman URL must be provided via FOREMAN_URL environment variable")
        username = username or os.getenv('FOREMAN_USERNAME')
        password = password or os.getenv('FOREMAN_PASSWORD')
        
        if not username or not password:
            raise ValueError("Foreman credentials must be provided via FOREMAN_USERNAME and FOREMAN_PASSWORD environment variables")
        
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
            app.logger.error(f"Error querying Foreman API: {e}")
            return None
    
    def get_host(self, hostname):
        """Get specific host details"""
        url = f"{self.base_url}/api/hosts/{hostname}"
        
        try:
            response = self.session.get(url, auth=self.auth)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            app.logger.error(f"Error querying host {hostname}: {e}")
            return None
    
    def get_host_facts(self, hostname):
        """Get specific host facts using the working fact_values endpoint"""
        url = f"{self.base_url}/api/fact_values"
        params = {
            "search": f"host={hostname}",
            "per_page": 1000  # Get all facts for the host
        }
        
        try:
            response = self.session.get(url, auth=self.auth, params=params)
            response.raise_for_status()
            data = response.json()
            
            # Extract facts for this specific host
            if 'results' in data and hostname in data['results']:
                return data['results'][hostname]
            return None
        except requests.exceptions.RequestException as e:
            app.logger.error(f"Error querying facts for host {hostname}: {e}")
            return None

def parse_kernel_version(kernel_str):
    """Parse kernel version string into sortable tuple"""
    if not kernel_str or kernel_str == 'N/A':
        return (0, 0, 0, 0, 0, 0)
    
    # Extract version numbers from kernel string like "4.18.0-553.56.1.el8_10.x86_64"
    # Pattern: major.minor.patch-build.release.subrelease.el_version
    match = re.match(r'(\d+)\.(\d+)\.(\d+)-(\d+)\.(\d+)\.(\d+)', kernel_str)
    if match:
        major, minor, patch, build, release, subrelease = match.groups()
        return (int(major), int(minor), int(patch), int(build), int(release), int(subrelease))
    
    # Fallback: extract major.minor.patch-build.release
    match = re.match(r'(\d+)\.(\d+)\.(\d+)-(\d+)\.(\d+)', kernel_str)
    if match:
        major, minor, patch, build, release = match.groups()
        return (int(major), int(minor), int(patch), int(build), int(release), 0)
    
    # Fallback: extract major.minor.patch-build
    match = re.match(r'(\d+)\.(\d+)\.(\d+)-(\d+)', kernel_str)
    if match:
        major, minor, patch, build = match.groups()
        return (int(major), int(minor), int(patch), int(build), 0, 0)
    
    # Fallback: try to extract just major.minor.patch
    match = re.match(r'(\d+)\.(\d+)\.(\d+)', kernel_str)
    if match:
        major, minor, patch = match.groups()
        return (int(major), int(minor), int(patch), 0, 0, 0)
    
    # If we can't parse it, return 0s so it sorts first
    return (0, 0, 0, 0, 0, 0)

def sort_hosts_by_os_kernel(hosts):
    """Sort hosts by OS first, then by kernel version (oldest first)"""
    def sort_key(host):
        os_name = host.get('os', '') or ''
        kernel = host.get('kernel', '') or ''
        
        # Parse kernel version for proper sorting
        kernel_tuple = parse_kernel_version(kernel)
        
        # Return tuple: (OS name, kernel version tuple)
        # This will sort by OS first, then by kernel version
        return (os_name, kernel_tuple)
    
    return sorted(hosts, key=sort_key)

def format_host_data(hosts_data, sort_by_os_kernel=True):
    """Format host data for output"""
    if hosts_data is None:
        return []
        
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
        
        # Sort by OS and kernel version by default
        if sort_by_os_kernel:
            formatted = sort_hosts_by_os_kernel(formatted)
            
        return formatted
    else:
        # Single host
        return [{
            'name': hosts_data.get('name'),
            'hostgroup': hosts_data.get('hostgroup_title'),
            'os': hosts_data.get('operatingsystem_name'),
            'kernel': hosts_data.get('reported_data', {}).get('kernel_version', 'N/A') if hosts_data.get('reported_data') else 'N/A',
            'ip': hosts_data.get('ip'),
            'last_report': hosts_data.get('last_report'),
            'status': hosts_data.get('global_status_label')
        }]

# Initialize Foreman API client
foreman = ForemanAPI()

@app.route('/')
def index():
    """Main page showing all hosts"""
    sort_by = request.args.get('sort', 'os_kernel')  # Default to OS+kernel sort
    hosts_data = foreman.get_hosts()
    
    if sort_by == 'name':
        hosts = format_host_data(hosts_data, sort_by_os_kernel=False)
        hosts.sort(key=lambda x: x.get('name', ''))
    elif sort_by == 'hostgroup':
        hosts = format_host_data(hosts_data, sort_by_os_kernel=False)
        hosts.sort(key=lambda x: (x.get('hostgroup', '') or '', x.get('name', '')))
    else:  # os_kernel (default)
        hosts = format_host_data(hosts_data, sort_by_os_kernel=True)
    
    return render_template('index.html', hosts=hosts, current_sort=sort_by)

@app.route('/search')
def search():
    """Search hosts"""
    search_term = request.args.get('q', '')
    sort_by = request.args.get('sort', 'os_kernel')
    
    if search_term:
        hosts_data = foreman.get_hosts(search=f"name~{search_term}")
        
        if sort_by == 'name':
            hosts = format_host_data(hosts_data, sort_by_os_kernel=False)
            hosts.sort(key=lambda x: x.get('name', ''))
        elif sort_by == 'hostgroup':
            hosts = format_host_data(hosts_data, sort_by_os_kernel=False)
            hosts.sort(key=lambda x: (x.get('hostgroup', '') or '', x.get('name', '')))
        else:  # os_kernel (default)
            hosts = format_host_data(hosts_data, sort_by_os_kernel=True)
    else:
        hosts = []
    return render_template('index.html', hosts=hosts, search_term=search_term, current_sort=sort_by)

@app.route('/hostgroup/<hostgroup>')
def filter_hostgroup(hostgroup):
    """Filter hosts by hostgroup"""
    hosts_data = foreman.get_hosts()
    if hosts_data:
        filtered_hosts = []
        for host in hosts_data['results']:
            if host.get('hostgroup_title') == hostgroup:
                filtered_hosts.append(host)
        hosts_data['results'] = filtered_hosts
        hosts = format_host_data(hosts_data)
    else:
        hosts = []
    return render_template('index.html', hosts=hosts, filter_type='hostgroup', filter_value=hostgroup)

@app.route('/host/<hostname>')
def host_details(hostname):
    """Get specific host details"""
    host_data = foreman.get_host(hostname)
    facts_data = None
    
    if host_data:
        # Try to get facts data using the suggested endpoint
        facts_data = foreman.get_host_facts(hostname)
        return render_template('host_detail.html', host=host_data, facts=facts_data)
    else:
        return render_template('host_detail.html', host=None, facts=None)

@app.route('/api/hosts')
def api_hosts():
    """API endpoint for all hosts"""
    hosts_data = foreman.get_hosts()
    hosts = format_host_data(hosts_data)
    return jsonify(hosts)

@app.route('/api/search')
def api_search():
    """API endpoint for search"""
    search_term = request.args.get('q', '')
    if search_term:
        hosts_data = foreman.get_hosts(search=f"name~{search_term}")
        hosts = format_host_data(hosts_data)
    else:
        hosts = []
    return jsonify(hosts)

@app.route('/export/csv')
def export_csv():
    """Export hosts to CSV"""
    search_term = request.args.get('q', '')
    hostgroup = request.args.get('hostgroup', '')
    
    if search_term:
        hosts_data = foreman.get_hosts(search=f"name~{search_term}")
    elif hostgroup:
        hosts_data = foreman.get_hosts()
        if hosts_data:
            filtered_hosts = []
            for host in hosts_data['results']:
                if host.get('hostgroup_title') == hostgroup:
                    filtered_hosts.append(host)
            hosts_data['results'] = filtered_hosts
    else:
        hosts_data = foreman.get_hosts()
    
    hosts = format_host_data(hosts_data)
    
    # Create CSV
    output = io.StringIO()
    if hosts:
        writer = csv.DictWriter(output, fieldnames=['name', 'hostgroup', 'os', 'kernel', 'ip', 'last_report', 'status'])
        writer.writeheader()
        writer.writerows(hosts)
    
    # Create response
    response = make_response(output.getvalue())
    response.headers["Content-Disposition"] = "attachment; filename=foreman_hosts.csv"
    response.headers["Content-type"] = "text/csv"
    
    return response

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8087, debug=True)