
"""
Emerald's Killfeed - Player Linking System (PHASE 5)
/link <char>, /alt add/remove, /linked, /unlink
Stored per guild, used by economy, stats, bounties, factions
"""

import asyncio
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any

import discord
from discord.ext import commands
from bot.utils.embed_factory import EmbedFactory
import logging

logger = logging.getLogger(__name__)

logger = logging.getLogger(__name__)

class Linking(commands.Cog):
    """
    LINKING (FREE)
    - /link <char>, /alt add/remove, /linked, /unlink
    - Stored per guild
    - Used by economy, stats, bounties, factions
    """
    
    def __init__(self, bot):
        self.bot = bot
    
    @discord.slash_command(name="link", description="Link your Discord account to a character")
    async def link(self, ctx: discord.ApplicationContext, character: str):
        """Link Discord account to a character name"""
        try:
            guild_id = ctx.guild.id
            discord_id = ctx.user.id
            
            # Validate character name
            character = character.strip()
            if not character:
                await ctx.respond("❌ Character name cannot be empty!", ephemeral=True)
                return
            
            if len(character) > 32:
                await ctx.respond("❌ Character name too long! Maximum 32 characters.", ephemeral=True)
                return
            
            # Check if character is already linked to another user
            existing_link = await self.bot.db_manager.players.find_one({
                "guild_id": guild_id,
                "linked_characters": character
            })
            
            if existing_link and existing_link['discord_id'] != discord_id:
                await ctx.respond(
                    f"❌ Character **{character}** is already linked to another Discord account!",
                    ephemeral=True
                )
                return
            
            # Link the character
            success = await self.bot.db_manager.link_player(guild_id, discord_id, character)
            
            if success:
                # Get updated player data
                player_data = await self.bot.db_manager.get_linked_player(guild_id, discord_id)
                
                embed = EmbedFactory.build(
                    title="🔗 Character Linked",
                    description=f"Successfully linked **{character}** to your Discord account!",
                    color=0x00FF00,
                    timestamp=datetime.now(timezone.utc)
                )
                
                embed.add_field(
                    name="👤 Linked Characters",
                    value="\n".join([f"• {char}" for char in player_data['linked_characters']]),
                    inline=False
                )
                
                embed.add_field(
                    name="⭐ Primary Character",
                    value=player_data['primary_character'],
                    inline=True
                )
                
                embed.set_thumbnail(url="attachment://main.png")
                embed.set_footer(text="Powered by Discord.gg/EmeraldServers")
                
                await ctx.respond(embed=embed)
            else:
                await ctx.respond("❌ Failed to link character. Please try again.", ephemeral=True)
                
        except Exception as e:
            logger.error(f"Failed to link character: {e}")
            await ctx.respond("❌ Failed to link character.", ephemeral=True)
    
    @discord.slash_command(name="alt_add", description="Add an alternate character")
    async def alt_add(self, ctx: discord.ApplicationContext, character: str):
        """Add an alternate character to your account"""
        try:
            guild_id = ctx.guild.id
            discord_id = ctx.user.id
            
            # Check if user has any linked characters
            player_data = await self.bot.db_manager.get_linked_player(guild_id, discord_id)
            if not player_data:
                await ctx.respond(
                    "❌ You must link your main character first using `/link <character>`!",
                    ephemeral=True
                )
                return
            
            # Validate character name
            character = character.strip()
            if not character:
                await ctx.respond("❌ Character name cannot be empty!", ephemeral=True)
                return
            
            if len(character) > 32:
                await ctx.respond("❌ Character name too long! Maximum 32 characters.", ephemeral=True)
                return
            
            # Check if character is already linked
            if character in player_data['linked_characters']:
                await ctx.respond(f"❌ **{character}** is already linked to your account!", ephemeral=True)
                return
            
            # Check if character is linked to another user
            existing_link = await self.bot.db_manager.players.find_one({
                "guild_id": guild_id,
                "linked_characters": character
            })
            
            if existing_link and existing_link['discord_id'] != discord_id:
                await ctx.respond(
                    f"❌ Character **{character}** is already linked to another Discord account!",
                    ephemeral=True
                )
                return
            
            # Add the alternate character
            result = await self.bot.db_manager.players.update_one(
                {"guild_id": guild_id, "discord_id": discord_id},
                {"$addToSet": {"linked_characters": character}}
            )
            
            if result.modified_count > 0:
                # Get updated data
                updated_player = await self.bot.db_manager.get_linked_player(guild_id, discord_id)
                
                embed = EmbedFactory.build(
                    title="➕ Alternate Character Added",
                    description=f"Successfully added **{character}** as an alternate character!",
                    color=0x00FF00,
                    timestamp=datetime.now(timezone.utc)
                )
                
                embed.add_field(
                    name="👤 All Linked Characters",
                    value="\n".join([f"• {char}" for char in updated_player['linked_characters']]),
                    inline=False
                )
                
                embed.set_thumbnail(url="attachment://main.png")
                embed.set_footer(text="Powered by Discord.gg/EmeraldServers")
                
                await ctx.respond(embed=embed)
            else:
                await ctx.respond("❌ Failed to add alternate character.", ephemeral=True)
                
        except Exception as e:
            logger.error(f"Failed to add alt character: {e}")
            await ctx.respond("❌ Failed to add alternate character.", ephemeral=True)
    
    @discord.slash_command(name="alt_remove", description="Remove an alternate character")
    async def alt_remove(self, ctx: discord.ApplicationContext, character: str):
        """Remove an alternate character from your account"""
        try:
            guild_id = ctx.guild.id
            discord_id = ctx.user.id
            
            # Get player data
            player_data = await self.bot.db_manager.get_linked_player(guild_id, discord_id)
            if not player_data:
                await ctx.respond("❌ You don't have any linked characters!", ephemeral=True)
                return
            
            # Validate character name
            character = character.strip()
            if character not in player_data['linked_characters']:
                await ctx.respond(f"❌ **{character}** is not linked to your account!", ephemeral=True)
                return
            
            # Prevent removing primary character if it's the only one
            if len(player_data['linked_characters']) == 1:
                await ctx.respond(
                    "❌ Cannot remove your only character! Use `/unlink` to remove all characters.",
                    ephemeral=True
                )
                return
            
            # Remove the character
            result = await self.bot.db_manager.players.update_one(
                {"guild_id": guild_id, "discord_id": discord_id},
                {"$pull": {"linked_characters": character}}
            )
            
            if result.modified_count > 0:
                # If removed character was primary, set new primary
                if player_data['primary_character'] == character:
                    remaining_chars = [c for c in player_data['linked_characters'] if c != character]
                    await self.bot.db_manager.players.update_one(
                        {"guild_id": guild_id, "discord_id": discord_id},
                        {"$set": {"primary_character": remaining_chars[0]}}
                    )
                
                # Get updated data
                updated_player = await self.bot.db_manager.get_linked_player(guild_id, discord_id)
                
                embed = EmbedFactory.build(
                    title="➖ Alternate Character Removed",
                    description=f"Successfully removed **{character}** from your linked characters!",
                    color=0xFFA500,
                    timestamp=datetime.now(timezone.utc)
                )
                
                if updated_player['linked_characters']:
                    embed.add_field(
                        name="👤 Remaining Characters",
                        value="\n".join([f"• {char}" for char in updated_player['linked_characters']]),
                        inline=False
                    )
                    
                    embed.add_field(
                        name="⭐ Primary Character",
                        value=updated_player['primary_character'],
                        inline=True
                    )
                
                embed.set_thumbnail(url="attachment://main.png")
                embed.set_footer(text="Powered by Discord.gg/EmeraldServers")
                
                await ctx.respond(embed=embed)
            else:
                await ctx.respond("❌ Failed to remove alternate character.", ephemeral=True)
                
        except Exception as e:
            logger.error(f"Failed to remove alt character: {e}")
            await ctx.respond("❌ Failed to remove alternate character.", ephemeral=True)
    
    @discord.slash_command(name="linked", description="View your linked characters")
    async def linked(self, ctx: discord.ApplicationContext, user: discord.Member = None):
        """View linked characters for yourself or another user"""
        try:
            guild_id = ctx.guild.id
            target_user = user or ctx.user
            
            # Get player data
            player_data = await self.bot.db_manager.get_linked_player(guild_id, target_user.id)
            
            if not player_data:
                if target_user == ctx.user:
                    await ctx.respond(
                        "❌ You don't have any linked characters! Use `/link <character>` to get started.",
                        ephemeral=True
                    )
                else:
                    await ctx.respond(
                        f"❌ {target_user.mention} doesn't have any linked characters!",
                        ephemeral=True
                    )
                return
            
            embed = EmbedFactory.build(
                title="🔗 Linked Characters",
                description=f"Character information for {target_user.mention}",
                color=0x3498DB,
                timestamp=datetime.now(timezone.utc)
            )
            
            embed.add_field(
                name="👤 Linked Characters",
                value="\n".join([f"• {char}" for char in player_data['linked_characters']]),
                inline=False
            )
            
            embed.add_field(
                name="⭐ Primary Character",
                value=player_data['primary_character'],
                inline=True
            )
            
            embed.add_field(
                name="📅 Linked Since",
                value=f"<t:{int(player_data['linked_at'].timestamp())}:F>",
                inline=True
            )
            
            embed.set_thumbnail(url="attachment://main.png")
            embed.set_footer(text="Powered by Discord.gg/EmeraldServers")
            
            await ctx.respond(embed=embed)
            
        except Exception as e:
            logger.error(f"Failed to show linked characters: {e}")
            await ctx.respond("❌ Failed to retrieve linked characters.", ephemeral=True)
    
    @discord.slash_command(name="unlink", description="Unlink all your characters")
    async def unlink(self, ctx: discord.ApplicationContext):
        """Unlink all characters from your Discord account"""
        try:
            guild_id = ctx.guild.id
            discord_id = ctx.user.id
            
            # Get player data
            player_data = await self.bot.db_manager.get_linked_player(guild_id, discord_id)
            
            if not player_data:
                await ctx.respond("❌ You don't have any linked characters!", ephemeral=True)
                return
            
            # Create confirmation embed
            characters_list = "\n".join([f"• {char}" for char in player_data['linked_characters']])
            
            embed = EmbedFactory.build(
                title="⚠️ Confirm Unlinking",
                description="Are you sure you want to unlink ALL your characters?",
                color=0xFF6B6B,
                timestamp=datetime.now(timezone.utc)
            )
            
            embed.add_field(
                name="👤 Characters to Unlink",
                value=characters_list,
                inline=False
            )
            
            embed.add_field(
                name="⚠️ Warning",
                value="This will remove all character links and cannot be undone!",
                inline=False
            )
            
            embed.set_footer(text="React with ✅ to confirm or ❌ to cancel")
            
            # Send confirmation message
            message = await ctx.respond(embed=embed)
            
            # Add reactions
            await message.add_reaction("✅")
            await message.add_reaction("❌")
            
            # Wait for reaction
            def check(reaction, user):
                return (user == ctx.user and 
                       str(reaction.emoji) in ["✅", "❌"] and 
                       reaction.message.id == message.id)
            
            try:
                reaction, user = await self.bot.wait_for('reaction_add', timeout=30.0, check=check)
                
                if str(reaction.emoji) == "✅":
                    # Proceed with unlinking
                    result = await self.bot.db_manager.players.delete_one({
                        "guild_id": guild_id,
                        "discord_id": discord_id
                    })
                    
                    if result.deleted_count > 0:
                        success_embed = EmbedFactory.build(
                            title="✅ Characters Unlinked",
                            description="All your characters have been successfully unlinked!",
                            color=0x00FF00,
                            timestamp=datetime.now(timezone.utc)
                        )
                        success_embed.set_footer(text="Powered by Discord.gg/EmeraldServers")
                        
                        await message.edit(embed=success_embed)
                        await message.clear_reactions()
                    else:
                        await message.edit(content="❌ Failed to unlink characters.")
                        await message.clear_reactions()
                else:
                    # Cancelled
                    cancel_embed = EmbedFactory.build(
                        title="❌ Unlinking Cancelled",
                        description="Your characters remain linked.",
                        color=0xFFD700,
                        timestamp=datetime.now(timezone.utc)
                    )
                    cancel_embed.set_footer(text="Powered by Discord.gg/EmeraldServers")
                    
                    await message.edit(embed=cancel_embed)
                    await message.clear_reactions()
                    
            except asyncio.TimeoutError:
                timeout_embed = EmbedFactory.build(
                    title="⏰ Confirmation Timeout",
                    description="Unlinking cancelled due to timeout.",
                    color=0x808080,
                    timestamp=datetime.now(timezone.utc)
                )
                await message.edit(embed=timeout_embed)
                await message.clear_reactions()
                
        except Exception as e:
            logger.error(f"Failed to unlink characters: {e}")
            await ctx.respond("❌ Failed to unlink characters.", ephemeral=True)

def setup(bot):
    bot.add_cog(Linking(bot))
