import os
import re
import sys
import time
import queue
import json
import logging
import threading
import subprocess
from typing import AnyStr

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from logging.config import dictConfig

# --- Global Configuration (Loaded from config.json) ---
# These will be populated by config_loader
LOG_FILES = []
COOLDOWN = 120 # Default cooldown in seconds to prevent excessive notifications
EMAIL_SENDER = ""
EMAIL_APP_PASS = ""
EMAIL_RECIPIENTS = ""
# --- Regex Patterns ---
# Timestamp pattern for lines that start with a date and time
TIMESTAMP_RE = re.compile(r'^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d{3}')
# Specific pattern for lines that explicitly indicate an ERROR with a timestamp
TIMESTAMP_ERROR_RE = re.compile(r'^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d{3}.*ERROR', re.IGNORECASE)
# General log pattern for error keywords (used if TIMESTAMP_ERROR_RE isn't specific enough)
LOG_PATTERN = re.compile(r'error|exception|traceback|fatal|fail(ed)?|panic|crash|unhandled', re.IGNORECASE)

# --- Logging Setup ---
def setup_logging():
    """
    Sets up the logging configuration from 'logging_conf.json'.
    Ensures log directories exist before applying the configuration.
    """
    try:
        with open('logging_conf.json', 'r') as f:
            log_conf = json.load(f)

        # Auto configure logging directory
        for handler_name, handler_config in log_conf.get('handlers', {}).items():
            if handler_config.get('class') == 'logging.handlers.FileHandler':
                log_file = handler_config.get('filename')
                if log_file:
                    os.makedirs(os.path.dirname(log_file), exist_ok=True)
        # Apply logging configuration
        dictConfig(log_conf)
        # Return the main logger instance
        return logging.getLogger("script")
    except FileNotFoundError:
        print("Error: logging_conf.json not found. Please create it.")
        sys.exit(1)
    except json.JSONDecodeError:
        print("Error: Invalid JSON in logging_conf.json.")
        sys.exit(1)
    except Exception as e:
        print(f"Error setting up logging: {e}")
        sys.exit(1)

# --- Log Monitoring Class ---
class LogMonitor:
    """
    Manages the state and logic for monitoring log files,
    detecting errors, and sending notifications.
    """
    def __init__(self, logger):
        self.logger = logger
        # A dictionary to remember the last position (offset),
        # current error buffer, and collection state for each log file.
        self.file_states = {} # {filepath: {'offset': int, 'buffer': [], 'collecting': bool, 'last_error_time': float}}
        self.error_queue = queue.Queue()
        self.last_sent_time = 0 # Timestamp of the last SNS notification sent
        self.cooldown_active = False # Flag to indicate if cooldown is currently active
        self.cooldown_timer = None # Thread for cooldown

        # Start the error processing thread
        self.error_processor_thread = threading.Thread(target=self._process_error_queue_loop, daemon=True)
        self.error_processor_thread.start()
        self.logger.info("Error processing thread started.")

    def _send_smtp_notification(self, message):
        """
        Sends an email notification using SMTP.
        This function is a placeholder for actual email sending logic.
        """
            # if self.cooldown_active:
            #     return
        subject = "Logwatcher Alert: Error Detected"
        to = ','.join(EMAIL_RECIPIENTS)  # Join multiple recipients with commas
        
        # Construct command
        cmd = f'echo "{message}" | mutt -s "{subject}" {to}'

        # if attachment:
        #     cmd += f' -a "{attachment}" --'

        try:
            # Execute the command using shell
            result = subprocess.run(cmd, shell=True, check=True)
            
            self.logger.info(f"Email notification sent...")
            # Log mutt's output for debugging if needed
            if result.stdout:
                self.logger.debug(f"mutt stdout: {result.stdout.decode().strip()}")
            if result.stderr:
                self.logger.error(f"mutt stderr: {result.stderr.decode().strip()}")

            # --- Cooldown Activation ---
            self.last_sent_time = time.time()
            self.cooldown_active = True
            # Assuming COOLDOWN is a global variable and _reset_cooldown is a method of this class
            self.cooldown_timer = threading.Timer(COOLDOWN, self._reset_cooldown)
            self.cooldown_timer.start()

        # --- Error Handling ---
        except subprocess.CalledProcessError as e:
            # This catches errors where the mutt command itself failed (e.g., bad arguments, mutt not found, mutt couldn't send)
            self.logger.error(f"Error sending email via mutt (exit code {e.returncode}): {e.stderr.decode().strip()}")
        except FileNotFoundError:
            # This specifically catches if the 'mutt' executable is not found in the system's PATH
            self.logger.error("Error: 'mutt' command not found. Please ensure mutt is installed and in your system's PATH.")
        except Exception as e:
            # Catch any other unexpected errors during the process
            self.logger.error(f"An unexpected error occurred during email notification with mutt: {e}")


    def _reset_cooldown(self):
        """Resets the cooldown flag after the specified interval."""
        self.cooldown_active = False
        self.logger.info("SNS notification cooldown reset.")

    def _process_error_queue_loop(self):
        """
        This function runs in a separate thread.
        It continuously processes the error queue and sends messages to SNS.
        """
        while True:
            try:
                # Get a message from the queue with a timeout to allow the thread to be stopped
                error_message = self.error_queue.get(timeout=1)
                self.logger.info(f"Processing error from queue (Q size: {self.error_queue.qsize()}): {error_message[:20]}...")
                self._send_smtp_notification(error_message)
                self.error_queue.task_done() # Mark the task as done
            except queue.Empty:
                # No items in queue, continue loop
                pass
            except Exception as e:
                self.logger.error(f"Error in error processing thread: {e}")
            time.sleep(0.5) # Small sleep to prevent busy-waiting

    def read_new_lines(self, filepath):
        """
        Reads new lines from the log file, handles multi-line error aggregation,
        and puts complete error messages into the error queue.
        """
        self.logger.debug(f"Checking for new lines in: {filepath}")

        if filepath not in self.file_states:
            # Initialize state for a new file
            self.file_states[filepath] = {
                'offset': os.path.getsize(filepath),
                'buffer': [],
                'collecting': False
            }
            self.logger.info(f"Initialized monitoring for {filepath} at offset {self.file_states[filepath]['offset']}")
            return # First run, skip existing lines

        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                f.seek(self.file_states[filepath]['offset'])
                new_lines = f.readlines()
                self.file_states[filepath]['offset'] = f.tell() # Update offset for next read

            if not new_lines:
                self.logger.debug(f"No new lines in {filepath}")
                return

            self.logger.debug(f"Read {len(new_lines)} new lines from {filepath}")

            for line in new_lines:
                line = line.strip()
                if not line: # Skip empty lines
                    continue

                is_timestamped = TIMESTAMP_RE.search(line)
                is_error_line = LOG_PATTERN.search(line) # Checks for 'error' keywords

                if is_timestamped and is_error_line:
                    # This line is a new error, potentially ending a previous one
                    if self.file_states[filepath]['collecting']:
                        # Finish previous error block and enqueue it
                        self._enqueue_error_block(filepath)

                    # Start a new error block
                    self.file_states[filepath]['buffer'] = [line]
                    self.file_states[filepath]['collecting'] = True
                    self.logger.debug(f"Started collecting new error block: {line[:80]}...")
                elif is_timestamped and not is_error_line:
                    # This line has a timestamp but is not an error,
                    # potentially ending an ongoing error block
                    if self.file_states[filepath]['collecting']:
                        # Finish previous error block and enqueue it
                        self._enqueue_error_block(filepath)
                    self.file_states[filepath]['collecting'] = False
                    self.file_states[filepath]['buffer'] = [] # Clear buffer
                    self.logger.debug(f"Timestamped non-error line, stopped collecting: {line[:20]}...")
                elif not is_timestamped:
                    # This line has no timestamp, so it's likely a continuation of a previous log entry
                    if self.file_states[filepath]['collecting']:
                        # Append to the current error buffer
                        self.file_states[filepath]['buffer'].append(line)
                        self.logger.debug(f"Appended to error buffer: {line[:20]}...")
                    else:
                        # Ignore lines without timestamp and not part of an active error collection
                        self.logger.debug(f"Ignored non-timestamped line (not collecting): {line[:20]}...")

            # After processing all new_lines, if still collecting, enqueue the final block
            if self.file_states[filepath]['collecting'] and self.file_states[filepath]['buffer']:
                self._enqueue_error_block(filepath, force_enqueue=True) # Ensure it's enqueued even if no new timestamped line follows

        except FileNotFoundError:
            self.logger.error(f"Error: Log file not found at {filepath}. Please check the path.")
        except Exception as e:
            self.logger.error(f"An unexpected error occurred during log monitoring of {filepath}: {e}")

    def _enqueue_error_block(self, filepath, force_enqueue=False):
        """
        Enqueues the current error buffer if collecting is active.
        Resets the buffer and collecting state.
        """
        if self.file_states[filepath]['collecting'] and self.file_states[filepath]['buffer']:
            full_error_message = "\n".join(self.file_states[filepath]['buffer'])
            self.error_queue.put(full_error_message)
            self.logger.info(f"Enqueued error block (length {len(full_error_message)}): {full_error_message[:50]}...")
            # Reset buffer and collecting state after enqueueing
            self.file_states[filepath]['buffer'] = []
            self.file_states[filepath]['collecting'] = False
        elif force_enqueue and self.file_states[filepath]['buffer']:
             full_error_message = "\n".join(self.file_states[filepath]['buffer'])
             self.error_queue.put(full_error_message)
             self.logger.info(f"Forced enqueue of error block (length {len(full_error_message)}): {full_error_message[:200]}...")
             self.file_states[filepath]['buffer'] = []
             self.file_states[filepath]['collecting'] = False


# --- Watchdog Handler ---
class LogChangeHandler(FileSystemEventHandler):
    """
    Custom event handler for watchdog to react to file modifications.
    """
    def __init__(self, log_monitor):
        super().__init__()
        self.log_monitor = log_monitor

    def on_modified(self, event):
        """
        Called when a file or directory is modified.
        Triggers reading of new lines if it's a log file.
        """
        # Ensure it's a file and ends with .log
        if not event.is_directory and event.src_path.endswith(".log"): #type: ignore
            self.log_monitor.read_new_lines(event.src_path)
        # Added handling for created files, especially important for log rotation
    def on_created(self, event):
        """
        Called when a file or directory is created.
        Important for detecting new log files after rotation.
        """
        if not event.is_directory and event.src_path.endswith(".log"): #type: ignore
            self.log_monitor.logger.info(f"New log file created: {event.src_path}. Initializing monitoring.")
            # Re-initialize the file state for the new file, starting from offset 0
            self.log_monitor.file_states[event.src_path] = {
                'offset': 0, # Start from the beginning for a new file
                'buffer': [],
                'collecting': False
            }
            self.log_monitor.read_new_lines(event.src_path) # Read any initial content

    def on_moved(self, event):
        """
        Called when a file or directory is moved/renamed.
        Important for detecting log file rotations (e.g., app.log -> app.log.1).
        """
        if not event.is_directory and event.src_path.endswith(".log"): #type: ignore
            self.log_monitor.logger.info(f"Log file moved/rotated: {event.src_path} -> {event.dest_path}")
            # Remove old file from monitoring state
            if event.src_path in self.log_monitor.file_states:
                del self.log_monitor.file_states[event.src_path]
                self.log_monitor.logger.info(f"Stopped monitoring old file: {event.src_path}")
            # The new file (original name, now empty or new content) will trigger on_created or on_modified
            # if it's recreated or written to.
            # If the destination path is a new log file to be monitored, add it.
            if event.dest_path.endswith(".log") and event.dest_path not in self.log_monitor.file_states: #type: ignore
                self.log_monitor.logger.info(f"Starting monitoring for new log file at destination: {event.dest_path}")
                self.log_monitor.file_states[event.dest_path] = {
                    'offset': os.path.getsize(event.dest_path),
                    'buffer': [],
                    'collecting': False
                }


# --- Setup Watchdog Observer ---
def start_monitoring(log_monitor_instance):
    """
    Initializes and starts the watchdog observer to monitor specified log files.
    """
    observer = Observer()
    handler = LogChangeHandler(log_monitor_instance)
    log_monitor_instance.logger.info("Starting log file monitoring...")

    # Ensure directories of log files exist and schedule monitoring
    for file_path in LOG_FILES:
        log_dir = os.path.dirname(file_path)
        if not os.path.exists(log_dir):
            log_monitor_instance.logger.warning(f"Directory for log file not found: {log_dir}. skipping it...")
            continue        
        # Create the log file if it doesn't exist, so watchdog can monitor it
        if not os.path.exists(file_path):
            log_monitor_instance.logger.info(f"Log file not found: {file_path}. skipping it...")
            continue
        
        # Initialize file state for existing files (or newly created empty ones)
        # This is crucial for the first read to skip old content
        log_monitor_instance.file_states[file_path] = {
            'offset': os.path.getsize(file_path),
            'buffer': [],
            'collecting': False
        }
        observer.schedule(handler, path=os.path.dirname(file_path) or '.', recursive=False)
        log_monitor_instance.logger.info(f"Monitoring directory: {os.path.dirname(file_path) or '.'} for file: {file_path}")

    observer.start()
    log_monitor_instance.logger.info("Watchdog observer started.")
    try:
        while True:
            time.sleep(1) # Keep main thread alive
    except KeyboardInterrupt:
        log_monitor_instance.logger.info("Monitoring interrupted by user. Stopping observer.")
        observer.stop()
    observer.join()
    log_monitor_instance.logger.info("Watchdog observer stopped.")


def config_loader(path):
    """
    Loads configuration from a JSON file.
    Populates global variables REGION, TOPIC_ARN, LOG_FILES.
    """
    logger.info(f"Loading configuration from: {path}")
    if not path.endswith(".json"):
        sys.exit("Error: Please provide a .json configuration file.")
    if not os.path.exists(path):
        sys.exit(f"Error: Configuration file not found at '{path}'.")

    try:
        with open(path, 'r') as f:
            configs = json.load(f)

        global LOG_FILES, COOLDOWN,EMAIL_SENDER,EMAIL_APP_PASS,EMAIL_RECIPIENTS
        LOG_FILES = configs.get('log_files', [])
        COOLDOWN = configs.get('cooldown_seconds', 60) # Use default if not provided
        if not isinstance(COOLDOWN, int) or COOLDOWN <= 0:
            sys.exit("Error: 'cooldown_seconds' must be a positive integer in config.json.")
        else:
            logger.info(f"Cooldown set to {COOLDOWN} seconds.")

        email_configs = configs.get('email_config')
        if not email_configs or not isinstance(email_configs, dict):
            sys.exit("Error: 'email_config' section is missing in config.json.")

        EMAIL_SENDER = email_configs['smtp_user']
        EMAIL_APP_PASS = email_configs['smtp_pass']
        EMAIL_RECIPIENTS = configs.get('email_recipients', [])

        if not EMAIL_SENDER or not EMAIL_APP_PASS or not LOG_FILES:
            sys.exit("Error: Missing SMTP configs, or 'LOG_FILES' in config.json.")
        if not isinstance(LOG_FILES, list) or not all(isinstance(f, str) for f in LOG_FILES):
            sys.exit("Error: 'LOG_FILES' must be a list of strings in config.json.")

        return True
    except json.JSONDecodeError:
        sys.exit(f"Error: Invalid JSON in configuration file '{path}'.")
    except Exception as e:
        sys.exit(f"Error loading configuration: {e}")

if __name__ == "__main__":
    # Setup logging first
    logger = setup_logging()

    # Check if config file path is provided as a command-line argument
    if len(sys.argv) < 2:
        logger.error("Usage: python your_script_name.py <config_file.json>")
        sys.exit(1)
    config_path = sys.argv[1]
    logger.info(f"Using configuration from: {config_path}")

    # Load configuration
    if config_loader(config_path):
        logger.info("Configuration loaded successfully.")
       
        # Initialize LogMonitor instance
        log_monitor = LogMonitor(logger)

        # Start monitoring
        start_monitoring(log_monitor)
    else:
        logger.error("Failed to load configuration. Exiting.")
        sys.exit(1)