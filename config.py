"""
Configuration file for MLB Stats Discord Bot
"""

import os

# Bot Settings
POLL_INTERVAL_MINUTES = 5  # How often to check for new at-bats during games
ADMIN_ROLE_NAME = "MLB Bot Admin"  # Discord role name that can manage players

# Channel Configuration
# IMPORTANT: Replace this with your actual Discord channel ID
# Right-click a channel in Discord (with Developer Mode enabled) and click "Copy ID"
CHANNEL_ID = int(os.getenv('DISCORD_CHANNEL_ID', '0'))  # Set in .env file

# File Paths
PLAYER_ROSTER_FILE = "players.json"  # Stores list of tracked players
LAST_ATBATS_FILE = "last_atbats.json"  # Tracks last seen at-bat IDs

# MLB API Settings
MLB_API_BASE_URL = "https://statsapi.mlb.com/api/v1"

# Time Settings
TIMEZONE = "America/New_York"  # ET for MLB games
