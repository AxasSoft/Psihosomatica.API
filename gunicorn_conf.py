
import multiprocessing
import os

workers_per_core_str = os.getenv("WORKERS_PER_CORE", "2")

host = os.getenv("HOST", "0.0.0.0")
port = os.getenv("PORT", "80")
bind_env = os.getenv("BIND", None)
use_loglevel = os.getenv("LOG_LEVEL", "info")
if bind_env:
    use_bind = bind_env
else:
    use_bind = f"{host}:{port}"

cores = multiprocessing.cpu_count()
workers_per_core = float(workers_per_core_str)
default_web_concurrency = (workers_per_core * cores) - 1
web_concurrency = max(int(default_web_concurrency), 2)

accesslog_var = os.getenv("ACCESS_LOG", "-")
errorlog_var = os.getenv("ERROR_LOG", "-")
graceful_timeout_str = os.getenv("GRACEFUL_TIMEOUT", "60")
timeout_str = os.getenv("TIMEOUT", "60")
keepalive_str = os.getenv("KEEP_ALIVE", "5")

# Gunicorn config variables
loglevel = use_loglevel
workers = web_concurrency
bind = use_bind
errorlog = errorlog_var
worker_tmp_dir = "/dev/shm"
accesslog = accesslog_var
graceful_timeout = int(graceful_timeout_str)
timeout = int(timeout_str)
keepalive = int(keepalive_str)

# For debugging and testing
log_data = {
    "loglevel": loglevel,
    "workers": workers,
    "bind": bind,
    "graceful_timeout": graceful_timeout,
    "timeout": timeout,
    "keepalive": keepalive,
    "errorlog": errorlog,
    "accesslog": accesslog,
    # Additional, non-gunicorn variables
    "workers_per_core": workers_per_core,
    "host": host,
    "port": port,
}

#HOOKS
def on_starting(server):
    server.log.info("Gunicorn starting")
    server.log.info(f"Workers: {workers}")
    server.log.info(f"Bind: {bind}")

def when_ready(server):
    server.log.info("Gunicorn ready")
    server.log.info(f"Config: {log_data}")

