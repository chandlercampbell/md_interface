#!/bin/bash

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Define the virtual environment directory name
VENV_NAME="venv"
VENV_PATH="$SCRIPT_DIR/$VENV_NAME"

# Check if virtual environment already exists
if [ ! -d "$VENV_PATH" ]; then
    echo -e "\033[32mCreating virtual environment...\033[0m"
    python3 -m venv "$VENV_NAME"
    
    if [ $? -ne 0 ]; then
        echo -e "\033[31mError: Failed to create virtual environment. Make sure Python is installed and accessible.\033[0m" >&2
        exit 1
    fi
else
    echo -e "\033[33mVirtual environment already exists.\033[0m"
fi

# Activate the virtual environment
echo -e "\033[32mActivating virtual environment...\033[0m"
ACTIVATE_SCRIPT="$VENV_PATH/bin/activate"

if [ -f "$ACTIVATE_SCRIPT" ]; then
    source "$ACTIVATE_SCRIPT"
else
    echo -e "\033[31mError: Failed to find activation script at $ACTIVATE_SCRIPT\033[0m" >&2
    exit 1
fi

# Install requirements and run main script
pip3 install -r requirements.txt
python3 main.py