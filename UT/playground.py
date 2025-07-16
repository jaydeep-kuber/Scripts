# import subprocess
#
# def send_email_with_mutt(to, subject, body, attachment=None):
#     # Construct command
#     cmd = f'echo "{body}" | mutt -s "{subject}" {to}'
#
#     if attachment:
#         cmd += f' -a "{attachment}" --'
#
#     try:
#         # Execute the command using shell
#         subprocess.run(cmd, shell=True, check=True)
#         print("Email sent successfully!")
#     except subprocess.CalledProcessError as e:
#         print("Failed to send email:", e)
#
# # Example usage
# send_email_with_mutt(
#     to="recipient@example.com",
#     subject="Test Email from Python via mutt",
#     body="This is a test email sent from a Python script using mutt.",
#     attachment="/path/to/file.pdf"  # Optional, can be None
# )

import sys
import json
import  os

# def config_loader(path):
#     """
#     Loads configuration from a JSON file.
#     Populates global variables REGION, TOPIC_ARN, LOG_FILES.
#     """
#     if not path.endswith(".json"):
#         sys.exit("Error: Please provide a .json configuration file.")
#     if not os.path.exists(path):
#         sys.exit(f"Error: Configuration file not found at '{path}'.")
#
#     try:
#         with open(path, 'r') as f:
#             configs = json.load(f)
#
#         global LOG_FILES, COOLDOWN,EMAIL_SENDER,EMAIL_APP_PASS,EMAIL_RECIPIENTS, SMTP_HOST, SMTP_PORT
#         LOG_FILES = configs.get('log_files', [])
#         COOLDOWN = configs.get('cooldown_seconds', 60) # Use default if not provided
#
#         email_configs = configs.get('email_config')
#         print(email_configs['smtp_host'])
#         EMAIL_SENDER = configs.get('EMAIL_SENDER')
#         EMAIL_APP_PASS = configs.get('EMAIL_APP_PASS')
#         EMAIL_RECIPIENTS = configs.get('EMAIL_RECIPIENTS', [])
#
#         if not EMAIL_SENDER or not EMAIL_APP_PASS or not LOG_FILES:
#             sys.exit("Error: Missing SMTP configs, or 'LOG_FILES' in config.json.")
#         if not isinstance(LOG_FILES, list) or not all(isinstance(f, str) for f in LOG_FILES):
#             sys.exit("Error: 'LOG_FILES' must be a list of strings in config.json.")
#     except json.JSONDecodeError:
#         sys.exit(f"Error: Invalid JSON in configuration file '{path}'.")
#     except Exception as e:
#         sys.exit(f"Error loading configuration: {e}")
#
#     return True
#
# if __name__ == "__main__":
#     confpath="config.json"
#     config_loader(confpath)
