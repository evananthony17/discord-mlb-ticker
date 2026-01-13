# Discord Bot Setup Guide

Follow these steps to create and configure your Discord bot.

## Step 1: Create Discord Application

1. Go to the [Discord Developer Portal](https://discord.com/developers/applications)
2. Click **"New Application"**
3. Give it a name (e.g., "MLB Stats Tracker")
4. Click **"Create"**

## Step 2: Create Bot User

1. In your application, click **"Bot"** in the left sidebar
2. Click **"Add Bot"** → **"Yes, do it!"**
3. Under the bot's username, click **"Reset Token"** → **"Yes, do it!"**
4. **Copy the token** and save it somewhere safe (you'll need this for `.env` file)
   - ⚠️ **NEVER share this token publicly or commit it to GitHub!**

## Step 3: Configure Bot Permissions

### Privileged Gateway Intents
Still on the Bot page, scroll down to **"Privileged Gateway Intents"**:
- ✅ Enable **"Server Members Intent"**
- ✅ Enable **"Message Content Intent"**
- Click **"Save Changes"**

### Bot Permissions
1. Click **"OAuth2"** → **"URL Generator"** in the left sidebar
2. Under **"Scopes"**, select:
   - ✅ `bot`
   - ✅ `applications.commands`

3. Under **"Bot Permissions"**, select:
   - ✅ **Send Messages**
   - ✅ **Embed Links**
   - ✅ **Read Message History**
   - ✅ **Use Slash Commands**
   - ✅ **Manage Threads** (if using threads later)

4. Copy the **Generated URL** at the bottom

## Step 4: Invite Bot to Your Server

1. Paste the generated URL into your browser
2. Select the server you want to add the bot to
3. Click **"Authorize"**
4. Complete the CAPTCHA

## Step 5: Create Admin Role in Discord

1. Go to your Discord server
2. Go to **Server Settings** → **Roles**
3. Click **"Create Role"**
4. Name it exactly: `MLB Bot Admin`
   - (Or change `ADMIN_ROLE_NAME` in `config.py` to match your preferred role name)
5. Assign this role to yourself and anyone else who should manage players
6. Click **"Save Changes"**

## Step 6: Get Your Channel ID

1. In Discord, go to **User Settings** → **Advanced**
2. Enable **"Developer Mode"**
3. Right-click the channel where you want the bot to post
4. Click **"Copy ID"**
5. Save this ID for the `.env` file

## Step 7: Configure Environment Variables

1. In the `discord-mlb-ticker` folder, copy `.env.example` to `.env`:
   ```
   cp .env.example .env
   ```

2. Edit `.env` and add your values:
   ```
   DISCORD_BOT_TOKEN=your_actual_bot_token_here
   DISCORD_CHANNEL_ID=your_actual_channel_id_here
   ```

## Step 8: Test Locally (Optional)

Before deploying to Render, you can test locally:

```bash
# Install dependencies
pip install -r requirements.txt

# Run the bot
python bot.py
```

If everything is set up correctly, you should see:
```
[Bot Name] has connected to Discord!
Bot is in 1 server(s)
Synced 3 command(s)
```

## Discord Slash Commands

Once the bot is running, you can use these commands in your server:

- `/add_player <player_name>` - Add a player to track (requires MLB Bot Admin role)
- `/remove_player <player_name>` - Remove a player from tracking (requires MLB Bot Admin role)
- `/list_players` - Show all currently tracked players (anyone can use)

## Troubleshooting

### Bot doesn't respond to commands
- Make sure the bot has the "Use Slash Commands" permission
- Check that slash commands have synced (should see "Synced X command(s)" in console)
- Wait a few minutes - slash commands can take time to register

### "You need the 'MLB Bot Admin' role" error
- Make sure you created the role with the exact name `MLB Bot Admin`
- Make sure the role is assigned to your user
- Check that the role name in `config.py` matches your Discord role

### Bot can't post to channel
- Verify the channel ID is correct in `.env`
- Check that the bot has "Send Messages" and "Embed Links" permissions in that channel
- Make sure the bot is in the server

### "DISCORD_BOT_TOKEN not found" error
- Make sure you created the `.env` file (not `.env.example`)
- Check that the token is on the correct line with no extra spaces
- Verify you copied the entire token

## Next Steps

Once your bot is working locally, you're ready to deploy to Render! See the main [README.md](README.md) for deployment instructions.
