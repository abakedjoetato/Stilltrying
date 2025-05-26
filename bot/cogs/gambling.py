"""
Emerald's Killfeed - Gambling System (PHASE 4)
Slot machine and other gambling games
Economy integration with wallet system
"""

import asyncio
import random
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Optional, Any, List

import discord
from discord.ext import commands
from bot.utils.embed_factory import EmbedFactory

logger = logging.getLogger(__name__)

class Gambling(commands.Cog):
    """
    GAMBLING (PREMIUM)
    - Slot machine games
    - Dice rolling
    - Economy integration
    """

    def __init__(self, bot):
        self.bot = bot
        self.gambling_cooldowns: Dict[str, datetime] = {}

        # Slot machine symbols and multipliers
        self.slot_symbols = {
            "🍒": {"weight": 30, "multiplier": 2},
            "🍋": {"weight": 25, "multiplier": 3},
            "🍊": {"weight": 20, "multiplier": 4},
            "🍇": {"weight": 15, "multiplier": 5},
            "🔔": {"weight": 8, "multiplier": 10},
            "💎": {"weight": 2, "multiplier": 50}
        }

    async def check_premium_server(self, guild_id: int) -> bool:
        """Check if guild has premium access for gambling features"""
        guild_doc = await self.bot.db_manager.get_guild(guild_id)
        if not guild_doc:
            return False

        servers = guild_doc.get('servers', [])
        for server_config in servers:
            server_id = server_config.get('server_id', server_config.get('_id', 'default'))
            if await self.bot.db_manager.is_premium_server(guild_id, server_id):
                return True

        return False

    def get_random_slot_symbol(self) -> str:
        """Get random slot symbol based on weights"""
        symbols = list(self.slot_symbols.keys())
        weights = [self.slot_symbols[symbol]["weight"] for symbol in symbols]
        return random.choices(symbols, weights=weights)[0]

    def calculate_slot_winnings(self, reels: List[str], bet: int) -> tuple[int, str]:
        """Calculate slot machine winnings"""
        # Check for three of a kind
        if reels[0] == reels[1] == reels[2]:
            symbol = reels[0]
            multiplier = self.slot_symbols[symbol]["multiplier"]
            winnings = bet * multiplier
            return winnings, f"THREE {symbol}!"

        # Check for two of a kind
        if reels[0] == reels[1] or reels[1] == reels[2] or reels[0] == reels[2]:
            # Find the matching symbol
            if reels[0] == reels[1]:
                symbol = reels[0]
            elif reels[1] == reels[2]:
                symbol = reels[1]
            else:
                symbol = reels[0]

            multiplier = max(1, self.slot_symbols[symbol]["multiplier"] // 3)
            winnings = bet * multiplier
            return winnings, f"TWO {symbol}!"

        return 0, "No match"

    @discord.slash_command(name="slots", description="Play the slot machine")
    async def slots(self, ctx: discord.ApplicationContext, bet: int):
        """Play slot machine gambling game"""
        try:
            guild_id = ctx.guild.id
            discord_id = ctx.user.id
            user_key = f"{guild_id}_{discord_id}_slots"

            # Check premium access
            if not await self.check_premium_server(guild_id):
                embed = EmbedFactory.build(
                    title="🔒 Premium Feature",
                    description="Gambling features require premium subscription!",
                    color=0xFF6B6B
                )
                await ctx.respond(embed=embed, ephemeral=True)
                return

            # Validate bet amount
            if bet <= 0:
                await ctx.respond("❌ Bet must be positive!", ephemeral=True)
                return

            if bet > 1000:
                await ctx.respond("❌ Maximum bet is $1,000!", ephemeral=True)
                return

            # Check cooldown (30 seconds)
            now = datetime.now(timezone.utc)
            if user_key in self.gambling_cooldowns:
                time_remaining = self.gambling_cooldowns[user_key] - now
                if time_remaining.total_seconds() > 0:
                    seconds_left = int(time_remaining.total_seconds())
                    embed = EmbedFactory.build(
                        title="⏱️ Gambling Cooldown",
                        description=f"You must wait **{seconds_left}** seconds before gambling again!",
                        color=0xFFD700
                    )
                    await ctx.respond(embed=embed, ephemeral=True)
                    return

            # Check wallet balance
            wallet = await self.bot.db_manager.get_wallet(guild_id, discord_id)
            if wallet['balance'] < bet:
                await ctx.respond(
                    f"❌ Insufficient funds! You have **${wallet['balance']:,}** but need **${bet:,}**",
                    ephemeral=True
                )
                return

            # Set cooldown
            self.gambling_cooldowns[user_key] = now + timedelta(seconds=30)

            # Deduct bet from wallet
            await self.bot.db_manager.update_wallet(guild_id, discord_id, -bet, "gambling_bet")

            # Spin the reels
            reels = [self.get_random_slot_symbol() for _ in range(3)]

            # Calculate winnings
            winnings, result_text = self.calculate_slot_winnings(reels, bet)

            # Create initial spinning embed
            spinning_embed = discord.Embed(
                title="🎰 Slot Machine",
                description="🎲 🎲 🎲\n\n**Spinning...**",
                color=0xFFD700,
                timestamp=now
            )

            message = await ctx.respond(embed=spinning_embed)

            # Simulate spinning animation
            await asyncio.sleep(2)

            # Create result embed
            if winnings > 0:
                # Add winnings to wallet
                await self.bot.db_manager.update_wallet(guild_id, discord_id, winnings, "gambling_win")

                color = 0x00FF00  # Green for win
                title = "🎰 WINNER!"
                profit = winnings - bet
                description = f"{' '.join(reels)}\n\n**{result_text}**\n\n💰 **Won: ${winnings:,}**\n📈 **Profit: ${profit:,}**"
            else:
                color = 0xFF6B6B  # Red for loss
                title = "🎰 No Luck"
                description = f"{' '.join(reels)}\n\n**{result_text}**\n\n💸 **Lost: ${bet:,}**"

            result_embed = discord.Embed(
                title=title,
                description=description,
                color=color,
                timestamp=now
            )

            # Add current balance
            updated_wallet = await self.bot.db_manager.get_wallet(guild_id, discord_id)
            result_embed.add_field(
                name="💰 Current Balance",
                value=f"${updated_wallet['balance']:,}",
                inline=True
            )

            result_embed.set_footer(text="Powered by Discord.gg/EmeraldServers")

            await message.edit(embed=result_embed)

        except Exception as e:
            logger.error(f"Failed to process slots: {e}")
            await ctx.respond("❌ Slot machine error. Please try again.", ephemeral=True)

    @discord.slash_command(name="dice", description="Roll dice for gambling")
    async def dice(self, ctx: discord.ApplicationContext, bet: int, guess: int):
        """Dice rolling gambling game"""
        try:
            guild_id = ctx.guild.id
            discord_id = ctx.user.id
            user_key = f"{guild_id}_{discord_id}_dice"

            # Check premium access
            if not await self.check_premium_server(guild_id):
                embed = EmbedFactory.build(
                    title="🔒 Premium Feature",
                    description="Gambling features require premium subscription!",
                    color=0xFF6B6B
                )
                await ctx.respond(embed=embed, ephemeral=True)
                return

            # Validate inputs
            if bet <= 0:
                await ctx.respond("❌ Bet must be positive!", ephemeral=True)
                return

            if bet > 500:
                await ctx.respond("❌ Maximum bet for dice is $500!", ephemeral=True)
                return

            if guess < 1 or guess > 6:
                await ctx.respond("❌ Guess must be between 1 and 6!", ephemeral=True)
                return

            # Check cooldown (15 seconds)
            now = datetime.now(timezone.utc)
            if user_key in self.gambling_cooldowns:
                time_remaining = self.gambling_cooldowns[user_key] - now
                if time_remaining.total_seconds() > 0:
                    seconds_left = int(time_remaining.total_seconds())
                    embed = EmbedFactory.build(
                        title="⏱️ Gambling Cooldown",
                        description=f"You must wait **{seconds_left}** seconds before gambling again!",
                        color=0xFFD700
                    )
                    await ctx.respond(embed=embed, ephemeral=True)
                    return

            # Check wallet balance
            wallet = await self.bot.db_manager.get_wallet(guild_id, discord_id)
            if wallet['balance'] < bet:
                await ctx.respond(
                    f"❌ Insufficient funds! You have **${wallet['balance']:,}** but need **${bet:,}**",
                    ephemeral=True
                )
                return

            # Set cooldown
            self.gambling_cooldowns[user_key] = now + timedelta(seconds=15)

            # Deduct bet from wallet
            await self.bot.db_manager.update_wallet(guild_id, discord_id, -bet, "gambling_bet")

            # Roll the dice
            roll = random.randint(1, 6)

            # Determine result
            if roll == guess:
                # Exact match - 5x multiplier
                winnings = bet * 5
                await self.bot.db_manager.update_wallet(guild_id, discord_id, winnings, "gambling_win")

                embed = discord.Embed(
                    title="🎲 PERFECT GUESS!",
                    description=f"🎯 **You guessed: {guess}**\n🎲 **Dice rolled: {roll}**\n\n💰 **Won: ${winnings:,}**\n📈 **Profit: ${winnings - bet:,}**",
                    color=0x00FF00,
                    timestamp=now
                )
            else:
                embed = discord.Embed(
                    title="🎲 Wrong Guess",
                    description=f"🎯 **You guessed: {guess}**\n🎲 **Dice rolled: {roll}**\n\n💸 **Lost: ${bet:,}**",
                    color=0xFF6B6B,
                    timestamp=now
                )

            # Add current balance
            updated_wallet = await self.bot.db_manager.get_wallet(guild_id, discord_id)
            embed.add_field(
                name="💰 Current Balance",
                value=f"${updated_wallet['balance']:,}",
                inline=True
            )

            embed.set_footer(text="Powered by Discord.gg/EmeraldServers")

            await ctx.respond(embed=embed)

        except Exception as e:
            logger.error(f"Failed to process dice: {e}")
            await ctx.respond("❌ Dice game error. Please try again.", ephemeral=True)

def setup(bot):
    bot.add_cog(Gambling(bot))