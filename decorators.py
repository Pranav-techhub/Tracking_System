import os
import csv
from functools import wraps
from datetime import datetime

LOG_FILE_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), 'data', 'logs.csv'))

def log_action(message=None):
    """
    Decorator to log function calls to logs.csv with timestamp, function name, and optional message.
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            result = func(*args, **kwargs)

            log_entry = {
                'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'function': func.__name__,
                'message': message or '',
                'args': str(args) if args else '',
                'kwargs': str(kwargs) if kwargs else ''
            }

            file_exists = os.path.isfile(LOG_FILE_PATH)
            with open(LOG_FILE_PATH, mode='a', newline='', encoding='utf-8') as logfile:
                fieldnames = ['timestamp', 'function', 'message', 'args', 'kwargs']
                writer = csv.DictWriter(logfile, fieldnames=fieldnames)
                if not file_exists:
                    writer.writeheader()
                writer.writerow(log_entry)

            return result
        return wrapper
    return decorator
