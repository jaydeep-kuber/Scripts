#!/bin/bash

# --- Configuration ---
CONFIG_FILE="config.json" # Name of your config file in the same directory as the script
MUTTRC_FILE="$HOME/.muttrc"


# --- checking existing file ---
if [[ -f "$MUTTRC_FILE" ]] ; then
  echo "You have an existing .muttrc file at: $MUTTRC_FILE"
  read -p "Do you want to override this file? [Y/n]: " -n 1 -r
  echo # Move to a new line after the input
  if [[ ! "$REPLY" =~ ^[Yy]$ ]]; then
      echo "Aborting: File will not be overridden."
      exit 0 # Exit gracefully if user chooses not to override
  fi
fi

# --- Functions ---
# Function to display an error message and exit
error_exit() {
    echo "ERROR: $1" >&2
    exit 1
}

# Function to get a value from JSON using jq
get_json_value() {
    local key="$1"
    local value=$(jq -r "$key" "$CONFIG_FILE")
    echo "$value"
}

# Function to validate and retrieve a required configuration value
get_required_config() {
    local key_path="$1"
    local description="$2"
    local value=$(get_json_value "$key_path")

    if [[ -z "$value" || "$value" == "null" ]]; then
        error_exit "Missing or empty configuration for '$description' (JSON path: $key_path). Please check your '$CONFIG_FILE'."
    fi
    echo "$value"
}

# --- Main Script Logic ---

echo "Starting .muttrc generation script..."

# 1. Check for jq installation
if ! command -v jq &> /dev/null; then
    error_exit "jq is not installed. Please install it to parse JSON.
    On Debian/Ubuntu: sudo apt-get install jq
    On Fedora: sudo dnf install jq
    On macOS: brew install jq"
fi

# 2. Check if config.json exists
if [[ ! -f "$CONFIG_FILE" ]]; then
    error_exit "Configuration file '$CONFIG_FILE' not found in the current directory ($(pwd))."
fi

echo "Reading configuration from '$CONFIG_FILE'..."

# 3. Retrieve required values from config.json
# Using get_required_config to ensure values are present
SMTP_HOST=$(get_required_config ".email_config.smtp_host" "SMTP Host")
SMTP_PORT=$(get_required_config ".email_config.smtp_port" "SMTP Port")
SMTP_USER=$(get_required_config ".email_config.smtp_user" "SMTP User")
SMTP_PASS=$(get_required_config ".email_config.smtp_pass" "SMTP Password")
FROM_EMAIL=$(get_required_config ".email_config.from_email" "From Email Address")
REAL_NAME=$(get_required_config ".email_config.real_name" "Real Name")

echo "All required email configuration values retrieved successfully."

# 4. Generate .muttrc content
# Using a HEREDOC for cleaner multi-line string creation
cat << EOF > "$MUTTRC_FILE"
# --- Mutt Configuration Generated by Deployment Script ---
# Generated on: $(date)

# Account settings
set from = "$FROM_EMAIL"
set realname = "$REAL_NAME"

# SMTP settings for sending mail
set smtp_url = "smtp://$SMTP_USER@$SMTP_HOST:$SMTP_PORT/"
set smtp_pass = "$SMTP_PASS"
# set ssl_starttls = yes
# set ssl_force_tls = yes

# Other common settings (you can customize these further)
# set folder = "~/mail"
# set header_cache = "~/.mutt/cache/headers"
# set message_cache = "~/.mutt/cache/bodies"
# set certificate_file = "~/.mutt/certificates"

# PGP/GPG settings (example, adjust if needed)
# set pgp_decode_command = "gpg --status-fd=2 %f"
# set pgp_verify_command = "gpg --status-fd=2 --verify %s %f"
# set pgp_decrypt_command = "gpg --status-fd=2 %f"
# set pgp_sign_command = "gpg --status-fd=2 --clearsign %f"
# set pgp_encrypt_only_command = "gpg --status-fd=2 -e -r %r -- %f"
# set pgp_encrypt_sign_command = "gpg --status-fd=2 --encrypt --sign -r %r -- %f"
# set pgp_import_command = "gpg --status-fd=2 --import %f"
# set pgp_export_command = "gpg --status-fd=2 --export %f"
# set pgp_verify_key_command = "gpg --status-fd=2 --fingerprint %r"
# set pgp_list_pubring_command = "gpg --status-fd=2 --list-keys %r"
# set pgp_list_secring_command = "gpg --status-fd=2 --list-secret-keys %r"
EOF

# 5. Set permissions for .muttrc
# It's crucial to set secure permissions for files containing passwords
chmod 600 "$MUTTRC_FILE"

echo "Successfully created/updated '$MUTTRC_FILE' with the following content:"
# cat "$MUTTRC_FILE"
echo "---------------------------------------------------------------------"
echo "Please ensure you have 'mutt' installed and configured correctly."
echo "---------------------------------------------------------------------"
echo "....script finished...."
