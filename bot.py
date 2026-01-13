"""
MLB Stats Discord Bot
Tracks live at-bats for specified MLB players and posts updates to Discord.
"""

import discord
from discord.ext import commands, tasks
import json
import os
from datetime import datetime, timezone
import asyncio
from mlb_api import MLBStatsAPI
from config import (
    POLL_INTERVAL_MINUTES,
    PLAYER_ROSTER_FILE,
    LAST_ATBATS_FILE,
    ADMIN_ROLE_NAME,
    CHANNEL_ID
)

# Bot setup
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
bot = commands.Bot(command_prefix='!', intents=intents)

# MLB API instance
mlb_api = MLBStatsAPI()


def load_json(filepath, default=None):
    """Load JSON file, return default if not exists."""
    if default is None:
        default = {}
    try:
        with open(filepath, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return default


def save_json(filepath, data):
    """Save data to JSON file."""
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2)


def has_admin_role():
    """Check if user has the required admin role."""
    async def predicate(ctx):
        if not ctx.guild:
            await ctx.send("This command must be used in a server.")
            return False

        role = discord.utils.get(ctx.guild.roles, name=ADMIN_ROLE_NAME)
        if role in ctx.author.roles:
            return True

        await ctx.send(f"You need the '{ADMIN_ROLE_NAME}' role to use this command.")
        return False

    return commands.check(predicate)


@bot.event
async def on_ready():
    """Bot startup event."""
    print(f'{bot.user} has connected to Discord!')
    print(f'Bot is in {len(bot.guilds)} server(s)')

    # Sync slash commands
    try:
        synced = await bot.tree.sync()
        print(f'Synced {len(synced)} command(s)')
    except Exception as e:
        print(f'Failed to sync commands: {e}')

    # Start the tracking loop
    if not check_games.is_running():
        check_games.start()

    # Post daily schedule
    await post_daily_schedule()


@bot.tree.command(name="add_player", description="Add a player to track")
async def add_player(interaction: discord.Interaction, player_name: str):
    """Add a player to the tracking roster."""
    # Check role
    role = discord.utils.get(interaction.guild.roles, name=ADMIN_ROLE_NAME)
    if role not in interaction.user.roles:
        await interaction.response.send_message(
            f"You need the '{ADMIN_ROLE_NAME}' role to use this command.",
            ephemeral=True
        )
        return

    # Search for player
    await interaction.response.defer()
    player_info = await mlb_api.search_player(player_name)

    if not player_info:
        await interaction.followup.send(f"Could not find player: {player_name}")
        return

    # Load roster and add player
    roster = load_json(PLAYER_ROSTER_FILE, default=[])

    # Check if already tracked
    if any(p['id'] == player_info['id'] for p in roster):
        await interaction.followup.send(f"{player_info['name']} is already being tracked!")
        return

    roster.append(player_info)
    save_json(PLAYER_ROSTER_FILE, roster)

    await interaction.followup.send(
        f"✅ Now tracking **{player_info['name']}** (#{player_info.get('primaryNumber', 'N/A')}) - {player_info['team']}"
    )


@bot.tree.command(name="remove_player", description="Remove a player from tracking")
async def remove_player(interaction: discord.Interaction, player_name: str):
    """Remove a player from the tracking roster."""
    # Check role
    role = discord.utils.get(interaction.guild.roles, name=ADMIN_ROLE_NAME)
    if role not in interaction.user.roles:
        await interaction.response.send_message(
            f"You need the '{ADMIN_ROLE_NAME}' role to use this command.",
            ephemeral=True
        )
        return

    roster = load_json(PLAYER_ROSTER_FILE, default=[])

    # Find and remove player
    initial_count = len(roster)
    roster = [p for p in roster if player_name.lower() not in p['name'].lower()]

    if len(roster) == initial_count:
        await interaction.response.send_message(f"Player '{player_name}' not found in roster.")
        return

    save_json(PLAYER_ROSTER_FILE, roster)
    await interaction.response.send_message(f"✅ Removed player matching '{player_name}' from tracking.")


@bot.tree.command(name="list_players", description="List all tracked players")
async def list_players(interaction: discord.Interaction):
    """List all players currently being tracked."""
    roster = load_json(PLAYER_ROSTER_FILE, default=[])

    if not roster:
        await interaction.response.send_message("No players are currently being tracked.")
        return

    embed = discord.Embed(
        title="🎯 Tracked Players",
        color=discord.Color.blue(),
        timestamp=datetime.now(timezone.utc)
    )

    for player in roster:
        embed.add_field(
            name=f"{player['name']} (#{player.get('primaryNumber', 'N/A')})",
            value=f"{player['team']} - {player.get('position', 'N/A')}",
            inline=False
        )

    await interaction.response.send_message(embed=embed)


@tasks.loop(minutes=POLL_INTERVAL_MINUTES)
async def check_games():
    """Main loop to check for game updates."""
    roster = load_json(PLAYER_ROSTER_FILE, default=[])

    if not roster:
        return

    last_atbats = load_json(LAST_ATBATS_FILE, default={})
    channel = bot.get_channel(CHANNEL_ID)

    if not channel:
        print(f"Warning: Could not find channel with ID {CHANNEL_ID}")
        return

    for player in roster:
        try:
            # Check if player has a game today
            game_data = await mlb_api.get_player_game_today(player['id'])

            if not game_data:
                continue

            # Get latest at-bat
            latest_atbat = await mlb_api.get_latest_atbat(player['id'], game_data)

            if not latest_atbat:
                continue

            # Check if this is a new at-bat
            player_key = str(player['id'])
            last_atbat_id = last_atbats.get(player_key)

            if latest_atbat['id'] != last_atbat_id:
                # New at-bat! Post it
                await post_atbat_update(channel, player, latest_atbat, game_data)

                # Update last seen
                last_atbats[player_key] = latest_atbat['id']
                save_json(LAST_ATBATS_FILE, last_atbats)

                # Check if game is complete
                if game_data.get('gameComplete'):
                    await post_game_summary(channel, player, game_data)

        except Exception as e:
            print(f"Error checking {player['name']}: {e}")


async def post_atbat_update(channel, player, atbat, game_data):
    """Post an at-bat update to Discord."""
    embed = discord.Embed(
        title=f"⚾ {player['name']} - At Bat",
        color=discord.Color.green() if atbat['was_hit'] else discord.Color.red(),
        timestamp=datetime.now(timezone.utc)
    )

    # Result
    embed.add_field(
        name="Result",
        value=f"**{atbat['result']}**",
        inline=False
    )

    # Slash line
    stats = atbat.get('stats', {})
    slash_line = f".{stats.get('avg', '000')} / .{stats.get('obp', '000')} / .{stats.get('slg', '000')}"
    embed.add_field(
        name="Season Slash Line",
        value=slash_line,
        inline=False
    )

    # Game context
    context = f"**{game_data['away_team']} @ {game_data['home_team']}** | "
    context += f"Score: {game_data['away_score']}-{game_data['home_score']} | "
    context += f"{atbat['inning']}"

    if atbat.get('risp'):
        context += " | 🔶 **RISP**"

    embed.add_field(
        name="Game Context",
        value=context,
        inline=False
    )

    embed.set_footer(text=f"{player['team']}")

    await channel.send(embed=embed)


async def post_game_summary(channel, player, game_data):
    """Post a game summary when the game completes."""
    embed = discord.Embed(
        title=f"📊 Game Complete - {player['name']}",
        color=discord.Color.blue(),
        timestamp=datetime.now(timezone.utc)
    )

    stats = game_data.get('player_stats', {})

    embed.add_field(
        name="Final Line",
        value=f"{stats.get('hits', 0)}-for-{stats.get('atbats', 0)}",
        inline=True
    )

    if stats.get('rbi', 0) > 0:
        embed.add_field(name="RBI", value=str(stats['rbi']), inline=True)

    if stats.get('runs', 0) > 0:
        embed.add_field(name="Runs", value=str(stats['runs']), inline=True)

    embed.add_field(
        name="Game Result",
        value=f"**{game_data['away_team']} {game_data['away_score']}, {game_data['home_team']} {game_data['home_score']}**",
        inline=False
    )

    embed.set_footer(text=f"{player['team']}")

    await channel.send(embed=embed)


async def post_daily_schedule():
    """Post the daily schedule of tracked players' games."""
    roster = load_json(PLAYER_ROSTER_FILE, default=[])

    if not roster:
        print("No players to track.")
        return

    channel = bot.get_channel(CHANNEL_ID)
    if not channel:
        print(f"Warning: Could not find channel with ID {CHANNEL_ID}")
        return

    embed = discord.Embed(
        title="📅 Today's Games",
        color=discord.Color.gold(),
        timestamp=datetime.now(timezone.utc)
    )

    games_today = []

    for player in roster:
        try:
            game = await mlb_api.get_player_game_today(player['id'])
            if game:
                games_today.append(f"**{player['name']}**: {game['away_team']} @ {game['home_team']} - {game['game_time']}")
            else:
                games_today.append(f"**{player['name']}**: No game scheduled")
        except Exception as e:
            print(f"Error getting schedule for {player['name']}: {e}")
            games_today.append(f"**{player['name']}**: Error fetching schedule")

    if games_today:
        embed.description = "\n".join(games_today)
    else:
        embed.description = "No tracked players have games today."

    embed.set_footer(text=f"Tracking {len(roster)} player(s)")

    await channel.send(embed=embed)


def main():
    """Main entry point."""
    token = os.getenv('DISCORD_BOT_TOKEN')

    if not token:
        print("Error: DISCORD_BOT_TOKEN not found in environment variables.")
        print("Please set up your .env file with the bot token.")
        return

    bot.run(token)


if __name__ == "__main__":
    main()
