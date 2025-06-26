#!/bin/bash

set -e

SSH_DIR="$HOME/.ssh"
DOC_DIR="$HOME/Documents"
PASSPRASE="${2:-}"
KEY_NAME="${1:-}" # taking $1 as filename arg
KEY_FILE="~/.ssh/$KEY_NAME" #set file path

echo "checking required prereqsists..."
echo "$SSH_DIR , $DOC_DIR "

#checking for .ssh dir
if [ -d "$SSH_DIR" ]; then
  echo ".ssh does exists"
else
  echo "missing .shh creating..."
  mkdir -p "$SSH_DIR"
fi

# checking file is there  or not
if [ -f "$KEY_FILE" ] || [ -f "~/.ssh/id_rsa"]; then
  echo "This named or id_rsa file is exists..."
else
  echo "generating a new SSH key file..."

  if [ -n "$PASSPRASE" ]; then
       echo "do not forget the passphrase ;)"
       ssh-keygen -t rsa -b 4096 -C "$(whoami)@$(hostname)" -f "$KEY_FILE" -N "$PASSPRASE"
  else
       echo "you have not passed passphrase,"
       echo "use this script like, $0 <new-key-file-name> <passphrase>"
       exit 1
  fi
fi

#checking for doc
if [ -d "$DOC_DIR" ]; then
  echo "Document dir exists, there your final .pub key will copied automentic..."
else
  echo "missing Document dir creating one... "
  mkdir -p "DOC_DIR"
fi
echo "copy public key to $DOC_DIR for sharing, you need to give this key to server admin."
cp "$KEY_FILE.pub" "$DOC_DIR/$KEY_FILE.pub"


# permission time
# echo "giving 700 permission to .ssh..."
# chmod 777 "$SSH_DIR"
