# MLB Stats Discord Bot

A Discord bot that tracks live MLB player stats and posts real-time at-bat updates to your Discord server.

## Features

- 🎯 **Live At-Bat Tracking**: Get instant updates when tracked players come to bat
- 📊 **Updated Slash Lines**: See AVG/OBP/SLG after each at-bat
- 🔶 **RISP Indicators**: Automatically highlights at-bats with Runners In Scoring Position
- 📅 **Daily Schedule**: Posts which tracked players have games today
- 🎮 **Role-Based Management**: Control who can add/remove players with Discord roles
- ⚙️ **Dual Configuration**: Manage players via Discord commands or JSON file

## How It Works

1. Add players to track using `/add_player` command
2. Bot monitors MLB Stats API every 5 minutes during games
3. When a tracked player has an at-bat, bot posts:
   - Result (Single, Strikeout, Home Run, etc.)
   - Updated season slash line
   - Game context (score, inning, RISP)
4. When games complete, bot posts a final summary

## Quick Start

### Prerequisites

- Python 3.8 or higher
- A Discord account and server
- A Discord bot token ([Setup Guide](DISCORD_BOT_SETUP.md))

### Local Setup

1. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd discord-mlb-ticker
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment variables**
   ```bash
   cp .env.example .env
   ```

   Edit `.env` and add:
   - Your Discord bot token
   - Your Discord channel ID

   See [DISCORD_BOT_SETUP.md](DISCORD_BOT_SETUP.md) for detailed instructions.

4. **Create the admin role**
   - In Discord: Server Settings → Roles → Create Role
   - Name it: `MLB Bot Admin`
   - Assign to users who should manage players

5. **Run the bot**
   ```bash
   python bot.py
   ```

## Discord Commands

### `/add_player <player_name>`
Add a player to the tracking roster. Requires `MLB Bot Admin` role.

**Example:**
```
/add_player Aaron Judge
```

### `/remove_player <player_name>`
Remove a player from tracking. Requires `MLB Bot Admin` role.

**Example:**
```
/remove_player Aaron Judge
```

### `/list_players`
Display all currently tracked players. Available to everyone.

## Manual Configuration

You can also manage players by editing `players.json` directly:

```json
[
  {
    "id": 592450,
    "name": "Aaron Judge",
    "primaryNumber": "99",
    "team": "New York Yankees",
    "team_id": 147,
    "position": "RF"
  }
]
```

The bot will automatically reload the roster on the next check.

## Deployment to Render

### Step 1: Push to GitHub

1. **Initialize git repository** (if not already done)
   ```bash
   git init
   git add .
   git commit -m "Initial commit - MLB stats bot"
   ```

2. **Create GitHub repository**
   - Go to [GitHub](https://github.com) and create a new repository
   - Name it: `discord-mlb-ticker`
   - Don't initialize with README (you already have one)

3. **Push to GitHub**
   ```bash
   git remote add origin https://github.com/YOUR_USERNAME/discord-mlb-ticker.git
   git branch -M main
   git push -u origin main
   ```

### Step 2: Deploy on Render

1. **Create Render account**
   - Go to [Render.com](https://render.com)
   - Sign up (can use GitHub account)

2. **Create New Web Service**
   - Click **"New +"** → **"Web Service"**
   - Connect your GitHub repository
   - Select `discord-mlb-ticker`

3. **Configure Service**
   - **Name**: `mlb-stats-bot` (or your choice)
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python bot.py`
   - **Instance Type**: `Free`

4. **Set Environment Variables**
   Click **"Advanced"** → **"Add Environment Variable"**

   Add these variables:
   - `DISCORD_BOT_TOKEN` = your bot token
   - `DISCORD_CHANNEL_ID` = your channel ID
   - `PYTHON_VERSION` = `3.11.0` (optional, but recommended)

5. **Deploy**
   - Click **"Create Web Service"**
   - Render will build and deploy your bot
   - Monitor the logs to ensure it connects successfully

### Step 3: Keep Bot Running

Render's free tier may sleep after inactivity. To keep it alive:

1. **Upgrade to paid tier** ($7/month) for 24/7 uptime

   OR

2. **Use a keep-alive service** (external ping service)
   - Note: Free tier has monthly hour limits

## Configuration Options

### `config.py`

- `POLL_INTERVAL_MINUTES`: How often to check for updates (default: 5)
- `ADMIN_ROLE_NAME`: Discord role name for management (default: "MLB Bot Admin")
- `CHANNEL_ID`: Set via environment variable `DISCORD_CHANNEL_ID`

## File Structure

```
discord-mlb-ticker/
├── bot.py                  # Main bot logic and Discord commands
├── mlb_api.py             # MLB Stats API wrapper
├── config.py              # Configuration settings
├── requirements.txt       # Python dependencies
├── players.json           # Tracked players roster (managed by bot)
├── last_atbats.json      # State tracking (auto-generated)
├── .env                   # Environment variables (not committed)
├── .env.example          # Example environment file
├── .gitignore            # Git ignore rules
├── DISCORD_BOT_SETUP.md  # Discord setup instructions
└── README.md             # This file
```

## Data Sources

This bot uses the official [MLB Stats API](https://statsapi.mlb.com/api/v1):
- Free to use
- No API key required
- Real-time game data
- Comprehensive player statistics

## Troubleshooting

### Bot doesn't post updates
- Check that players are added: `/list_players`
- Verify the player has a game today
- Check bot logs for errors
- Ensure channel ID is correct in `.env`

### "Could not find player" error
- Try the full player name: "Aaron Judge" not "Judge"
- Check spelling
- Player must be on an active MLB roster

### Commands not showing up
- Slash commands can take a few minutes to register
- Try `/list_players` to verify bot is responding
- Check bot has "Use Slash Commands" permission

### Bot keeps restarting on Render
- Check Render logs for error messages
- Verify environment variables are set correctly
- Ensure `DISCORD_BOT_TOKEN` is valid

## Future Enhancements

- [ ] Thread-based posting (one thread per player)
- [ ] Player injury/roster status alerts
- [ ] Historical game stats
- [ ] Multi-server support
- [ ] Webhook notifications
- [ ] Custom stat tracking (e.g., home runs only)

## Contributing

Issues and pull requests are welcome! This is a personal project but feel free to fork and customize.

## License

MIT License - feel free to use and modify for your own Discord servers.

## Acknowledgments

- [MLB Stats API](https://statsapi.mlb.com) for providing free, comprehensive baseball data
- [discord.py](https://discordpy.readthedocs.io/) for the Discord bot framework
