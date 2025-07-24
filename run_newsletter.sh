#!/bin/bash
# AgentNews automation script for cron jobs
# This script ensures the correct environment is activated before running

# Change to the script directory
cd "$(dirname "$0")"

# Load environment variables from .env file if it exists
if [ -f .env ]; then
    export $(cat .env | xargs)
fi

# Activate conda environment if needed
# source ~/anaconda3/etc/profile.d/conda.sh
# conda activate agentnews

# Run the newsletter
python agent_news.py

# Optional: Send status email if newsletter fails
if [ $? -ne 0 ]; then
    echo "AgentNews failed at $(date)" >> agent_news_errors.log
fi
