"""
MLB Stats API Wrapper
Handles all interactions with the official MLB Stats API.
"""

import aiohttp
import asyncio
from datetime import datetime, timezone
from typing import Optional, Dict, List


class MLBStatsAPI:
    """Wrapper for MLB Stats API endpoints."""

    BASE_URL = "https://statsapi.mlb.com/api/v1"
    BASE_URL_V1_1 = "https://statsapi.mlb.com/api/v1.1"

    def __init__(self):
        self.session = None

    async def _get_session(self):
        """Get or create aiohttp session."""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession()
        return self.session

    async def _request(self, endpoint: str, params: Optional[Dict] = None) -> Dict:
        """Make async request to MLB API."""
        session = await self._get_session()
        url = f"{self.BASE_URL}{endpoint}"

        try:
            async with session.get(url, params=params) as response:
                response.raise_for_status()
                return await response.json()
        except Exception as e:
            print(f"API request failed: {url} - {e}")
            return {}

    async def search_player(self, name: str) -> Optional[Dict]:
        """
        Search for a player by name.
        Returns player info dict or None if not found.
        """
        endpoint = "/sports/1/players"
        params = {
            "season": datetime.now().year,
            "gameType": "R"  # Regular season
        }

        data = await self._request(endpoint, params)
        players = data.get("people", [])

        # Search for matching name
        name_lower = name.lower()
        for player in players:
            player_name = player.get("fullName", "").lower()
            if name_lower in player_name:
                return self._format_player_info(player)

        return None

    def _format_player_info(self, player_data: Dict) -> Dict:
        """Format player data into standard structure."""
        team_info = player_data.get("currentTeam", {})

        return {
            "id": player_data.get("id"),
            "name": player_data.get("fullName"),
            "primaryNumber": player_data.get("primaryNumber"),
            "team": team_info.get("name", "Unknown"),
            "team_id": team_info.get("id"),
            "position": player_data.get("primaryPosition", {}).get("abbreviation", "N/A")
        }

    async def get_player_game_today(self, player_id: int) -> Optional[Dict]:
        """
        Get today's game for a player.
        Returns game data dict or None if no game today.
        """
        today = datetime.now().strftime("%Y-%m-%d")

        # Get player's team
        player_endpoint = f"/people/{player_id}"
        player_data = await self._request(player_endpoint)

        if not player_data.get("people"):
            return None

        team_id = player_data["people"][0].get("currentTeam", {}).get("id")

        if not team_id:
            return None

        # Get today's schedule for the team
        schedule_endpoint = "/schedule"
        params = {
            "teamId": team_id,
            "date": today,
            "sportId": 1,
            "hydrate": "linescore,team"
        }

        schedule_data = await self._request(schedule_endpoint, params)
        dates = schedule_data.get("dates", [])

        if not dates or not dates[0].get("games"):
            return None

        game = dates[0]["games"][0]
        return self._format_game_info(game)

    def _format_game_info(self, game_data: Dict) -> Dict:
        """Format game data into standard structure."""
        linescore = game_data.get("linescore", {})
        teams = game_data.get("teams", {})

        game_time = game_data.get("gameDate", "")
        if game_time:
            try:
                dt = datetime.fromisoformat(game_time.replace("Z", "+00:00"))
                game_time = dt.strftime("%I:%M %p ET")
            except:
                game_time = "TBD"

        return {
            "game_pk": game_data.get("gamePk"),
            "away_team": teams.get("away", {}).get("team", {}).get("name", ""),
            "home_team": teams.get("home", {}).get("team", {}).get("name", ""),
            "away_score": linescore.get("teams", {}).get("away", {}).get("runs", 0),
            "home_score": linescore.get("teams", {}).get("home", {}).get("runs", 0),
            "inning": linescore.get("currentInning", 1),
            "inning_state": linescore.get("inningState", ""),
            "game_time": game_time,
            "gameComplete": game_data.get("status", {}).get("detailedState") == "Final"
        }

    async def get_latest_atbat(self, player_id: int, game_data: Dict) -> Optional[Dict]:
        """
        Get the latest at-bat for a player in the current game.
        Returns at-bat data dict or None if no at-bats yet.
        """
        game_pk = game_data.get("game_pk")

        if not game_pk:
            return None

        # Get live game feed
        feed_endpoint = f"/game/{game_pk}/feed/live"
        feed_data = await self._request(feed_endpoint)

        if not feed_data:
            return None

        # Find all plays involving this player
        all_plays = feed_data.get("liveData", {}).get("plays", {}).get("allPlays", [])
        player_atbats = []

        for play in all_plays:
            # Check if this play involves our player as a batter
            matchup = play.get("matchup", {})
            batter = matchup.get("batter", {})

            if batter.get("id") == player_id:
                result = play.get("result", {})

                # Only count completed at-bats
                if result.get("event") and result.get("description"):
                    player_atbats.append(play)

        if not player_atbats:
            return None

        # Get the latest at-bat
        latest = player_atbats[-1]

        # Get updated player stats
        player_stats = await self._get_player_season_stats(player_id)

        return self._format_atbat(latest, game_data, player_stats)

    def _format_atbat(self, play_data: Dict, game_data: Dict, player_stats: Dict) -> Dict:
        """Format at-bat data into standard structure."""
        result = play_data.get("result", {})
        about = play_data.get("about", {})
        runners = play_data.get("runners", [])

        # Check for RISP
        risp = any(
            runner.get("movement", {}).get("start") in ["2B", "3B"]
            for runner in runners
        )

        # Determine if it was a hit
        event = result.get("event", "")
        hit_events = ["Single", "Double", "Triple", "Home Run"]
        was_hit = event in hit_events

        # Format inning
        inning_num = about.get("inning", 1)
        inning_half = about.get("halfInning", "top")
        inning_str = f"{inning_half.capitalize()} {inning_num}"

        return {
            "id": play_data.get("atBatIndex"),
            "result": event,
            "description": result.get("description", ""),
            "was_hit": was_hit,
            "risp": risp,
            "inning": inning_str,
            "stats": player_stats
        }

    async def _get_player_season_stats(self, player_id: int) -> Dict:
        """Get player's current season batting stats."""
        current_year = datetime.now().year
        stats_endpoint = f"/people/{player_id}/stats"
        params = {
            "stats": "season",
            "season": current_year,
            "group": "hitting"
        }

        data = await self._request(stats_endpoint, params)

        try:
            splits = data.get("stats", [{}])[0].get("splits", [])
            if splits:
                stats = splits[0].get("stat", {})

                # Format averages (remove leading 0)
                avg = str(stats.get("avg", ".000")).lstrip("0") or "0"
                obp = str(stats.get("obp", ".000")).lstrip("0") or "0"
                slg = str(stats.get("slg", ".000")).lstrip("0") or "0"

                return {
                    "avg": avg,
                    "obp": obp,
                    "slg": slg,
                    "hits": stats.get("hits", 0),
                    "atbats": stats.get("atBats", 0),
                    "rbi": stats.get("rbi", 0),
                    "runs": stats.get("runs", 0),
                    "homeRuns": stats.get("homeRuns", 0)
                }
        except (IndexError, KeyError):
            pass

        return {
            "avg": ".000",
            "obp": ".000",
            "slg": ".000",
            "hits": 0,
            "atbats": 0,
            "rbi": 0,
            "runs": 0,
            "homeRuns": 0
        }

    async def get_player_game_stats(self, player_id: int, game_pk: int) -> Dict:
        """Get player's stats for a specific game."""
        feed_endpoint = f"/game/{game_pk}/feed/live"
        feed_data = await self._request(feed_endpoint)

        try:
            box_score = feed_data.get("liveData", {}).get("boxscore", {}).get("teams", {})

            # Search both teams
            for team_side in ["away", "home"]:
                players = box_score.get(team_side, {}).get("players", {})

                for player_key, player_data in players.items():
                    if player_data.get("person", {}).get("id") == player_id:
                        stats = player_data.get("stats", {}).get("batting", {})
                        return {
                            "hits": stats.get("hits", 0),
                            "atbats": stats.get("atBats", 0),
                            "rbi": stats.get("rbi", 0),
                            "runs": stats.get("runs", 0)
                        }
        except Exception as e:
            print(f"Error getting game stats: {e}")

        return {"hits": 0, "atbats": 0, "rbi": 0, "runs": 0}

    async def close(self):
        """Close the aiohttp session."""
        if self.session and not self.session.closed:
            await self.session.close()
