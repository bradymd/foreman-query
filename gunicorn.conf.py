bind = "0.0.0.0:8087"
workers = 4
certfile='/etc/pki/tls/certs/certiffy.ca-bundle'
keyfile='/etc/pki/tls/private/certiffy.key'
loglevel = 'WARNING'
accesslog='/var/log/gunicorn/foreman-query-access.log'
errorlog='/var/log/gunicorn/foreman-query-error.log'
timeout = 240000
#check_config=True
reload=True
spew=False
reuse_port=True
cert_reqs = 1
proxy_allow_ips = '*'
# Put the output into error.log
capture_output=True
