#!/bin/bash

# Script to initialize project directory structure
# Usage: ./init_project.sh <project_name>

set -e

# Get project name
PROJECT_NAME=$1
if [ -z "$PROJECT_NAME" ]; then
    echo "Please provide a project name."
    echo "Usage: $0 <project_name>"
    exit 1
fi

# Base path
BASE_DIR="/home/$USER/work/domination/$PROJECT_NAME"

echo "📁 Creating project at: $BASE_DIR"

# Define structure
DIRS=(
    "$BASE_DIR/frontend/src/components"
    "$BASE_DIR/frontend/src/pages"
    "$BASE_DIR/frontend/src/services"
    "$BASE_DIR/frontend/public"
    "$BASE_DIR/backend/app/api"
    "$BASE_DIR/backend/app/models"
    "$BASE_DIR/backend/app/services"
    "$BASE_DIR/backend/app/auth"
    "$BASE_DIR/backend/app/utils"
    "$BASE_DIR/jenkins/jobs"
    "$BASE_DIR/jenkins/pipeline_templates"
    "$BASE_DIR/keycloak"
    "$BASE_DIR/nginx"
    "$BASE_DIR/postgres"
)

# Create directories
for DIR in "${DIRS[@]}"; do
    mkdir -p "$DIR"
    echo "✅ Created $DIR"
done

# Create placeholder files
touch "$BASE_DIR/.env"
touch "$BASE_DIR/docker-compose.yml"
touch "$BASE_DIR/README.md"
touch "$BASE_DIR/keycloak/realm-export.json"
touch "$BASE_DIR/nginx/default.conf"

echo "✅ Project directory structure ready."
