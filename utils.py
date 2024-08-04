import time
import logging
from functools import wraps

def retry_with_timeout(max_retries=3, delay=2, timeout=10):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            retries = 0
            while retries < max_retries:
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    logging.warning(f"Attempt {retries + 1} failed: {str(e)}")
                    retries += 1
                    if retries < max_retries:
                        time.sleep(delay)
            logging.error(f"Function {func.__name__} failed after {max_retries} attempts")
            raise Exception(f"Failed to execute {func.__name__} after {max_retries} attempts")
        return wrapper
    return decorator