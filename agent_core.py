import os
import yaml
import datetime
import subprocess

def get_os_context():
    try:
        return f"OS: {os.uname().sysname}, Release: {os.uname().release}, Arch: {os.uname().machine}"
    except OSError:
        return "OS Context unavailable"

def load_config():
    try:
        with open("Config.yaml", "r") as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        print("Warning: Config.yaml not found")
        return None
    except yaml.YAMLError as e:
        print(f"Warning: Error parsing Config.yaml: {e}")
        return None

def update_log(message):
    log_file = "session.log"
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    import fcntl
    with open(log_file, "a+") as f:
        fcntl.flock(f, fcntl.LOCK_EX)
        try:
            f.write(f"[{timestamp}] {message}\n")
        finally:
            fcntl.flock(f, fcntl.LOCK_UN)
    with open(log_file, "r+") as f:
        fcntl.flock(f, fcntl.LOCK_EX)
        try:
            lines = f.readlines()
            if len(lines) > 100:
                f.seek(0)
                f.truncate()
                f.writelines(lines[-100:])
        finally:
            fcntl.flock(f, fcntl.LOCK_UN)

def autonomous_loop():
    config = load_config()
    context = get_os_context()
    update_log(f"Context acquired: {context}")
    if config and 'model_settings' in config:
        print(f"Autonomous loop initialized. Provider: {config['model_settings']['provider']}")
    else:
        print("Autonomous loop initialized. Provider: Unknown (config not loaded)")

if __name__ == "__main__":
    autonomous_loop()
