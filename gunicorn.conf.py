# Gunicorn configuration file
bind = "0.0.0.0:5000"
workers = 1
worker_class = "sync"
timeout = 300
keepalive = 2
max_requests = 1000
max_requests_jitter = 50
preload_app = True
reload = True

# Large file upload settings
limit_request_line = 0
limit_request_field_size = 0