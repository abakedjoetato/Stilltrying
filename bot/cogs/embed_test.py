"""
Emerald's Killfeed - Embed Testing (PHASE 1)
Test all embed types and verify EmbedFactory functionality
"""

import logging
from datetime import datetime, timezone
from typing import Optional

import discord
from discord.ext import commands
from bot.utils.embed_factory import EmbedFactory

logger = logging.getLogger(__name__)

class EmbedTest(commands.Cog):
    """
    EMBED TESTING (ADMIN)
    - Test all embed types
    - Verify EmbedFactory functionality
    """

    def __init__(self, bot):
        self.bot = bot

    @discord.slash_command(name="test_embed", description="Test embed functionality (Admin)")
    @discord.default_permissions(administrator=True)
    async def test_embed(self, ctx: discord.ApplicationContext, 
                        embed_type: discord.Option(str, "Type of embed to test", 
                                                  choices=["killfeed", "bounty", "faction", "leaderboard", "economy", "gambling"])):
        """Test different embed types"""
        try:
            test_data = self._get_test_data(embed_type)

            embed = EmbedFactory.build(
                embed_type=embed_type,
                **test_data
            )

            if isinstance(embed, tuple):
                embed_obj, file_obj = embed
                if file_obj:
                    await ctx.respond(embed=embed_obj, file=file_obj)
                else:
                    await ctx.respond(embed=embed_obj)
            else:
                await ctx.respond(embed=embed)

        except Exception as e:
            logger.error(f"Failed to test embed: {e}")
            await ctx.respond(f"❌ Failed to test {embed_type} embed: {str(e)}", ephemeral=True)

    def _get_test_data(self, embed_type: str) -> dict:
        """Get test data for different embed types"""
        base_time = datetime.now(timezone.utc)

        test_data_map = {
            "killfeed": {
                "title": "🔫 Test Kill",
                "description": "Test killfeed embed",
                "data": {
                    "killer": "TestKiller",
                    "victim": "TestVictim",
                    "weapon": "AK-74",
                    "distance": "125m",
                    "server_name": "Test Server",
                    "thumbnail_url": "attachment://main.png"
                }
            },
            "bounty": {
                "title": "💰 Test Bounty",
                "description": "Test bounty embed",
                "data": {
                    "target": "TestTarget",
                    "amount": 5000,
                    "issuer": "TestIssuer",
                    "reason": "Test bounty",
                    "thumbnail_url": "attachment://main.png"
                }
            },
            "faction": {
                "title": "⚔️ Test Faction",
                "description": "Test faction embed",
                "data": {
                    "faction_name": "Test Faction",
                    "member_count": 25,
                    "leader": "TestLeader",
                    "thumbnail_url": "attachment://main.png"
                }
            },
            "leaderboard": {
                "title": "🏆 Test Leaderboard",
                "description": "Test leaderboard embed",
                "data": {
                    "leaderboard_type": "kills",
                    "entries": [
                        {"rank": 1, "player": "Player1", "value": 150},
                        {"rank": 2, "player": "Player2", "value": 125},
                        {"rank": 3, "player": "Player3", "value": 100}
                    ],
                    "thumbnail_url": "attachment://main.png"
                }
            },
            "economy": {
                "title": "💰 Test Economy",
                "description": "Test economy embed",
                "data": {
                    "player": "TestPlayer",
                    "balance": 10000,
                    "earnings": 500,
                    "thumbnail_url": "attachment://main.png"
                }
            },
            "gambling": {
                "title": "🎰 Test Gambling",
                "description": "Test gambling embed",
                "data": {
                    "game_type": "slots",
                    "bet": 100,
                    "result": "win",
                    "winnings": 500,
                    "thumbnail_url": "attachment://main.png"
                }
            }
        }

        return test_data_map.get(embed_type, {
            "title": "🧪 Test Embed",
            "description": "Generic test embed",
            "data": {"thumbnail_url": "attachment://main.png"}
        })

    @discord.slash_command(name="test_all_embeds", description="Test all embed types (Admin)")
    @discord.default_permissions(administrator=True)
    async def test_all_embeds(self, ctx: discord.ApplicationContext):
        """Test all embed types"""
        try:
            await ctx.defer()

            embed_types = ["killfeed", "bounty", "faction", "leaderboard", "economy", "gambling"]

            for embed_type in embed_types:
                try:
                    test_data = self._get_test_data(embed_type)

                    embed = EmbedFactory.build(
                        embed_type=embed_type,
                        **test_data
                    )

                    if isinstance(embed, tuple):
                        embed_obj, file_obj = embed
                        if file_obj:
                            await ctx.followup.send(embed=embed_obj, file=file_obj)
                        else:
                            await ctx.followup.send(embed=embed_obj)
                    else:
                        await ctx.followup.send(embed=embed)

                except Exception as e:
                    logger.error(f"Failed to test {embed_type} embed: {e}")
                    await ctx.followup.send(f"❌ Failed to test {embed_type} embed")

            await ctx.followup.send("✅ All embed tests completed!")

        except Exception as e:
            logger.error(f"Failed to test all embeds: {e}")
            await ctx.respond("❌ Failed to test embeds.", ephemeral=True)

def setup(bot):
    bot.add_cog(EmbedTest(bot))