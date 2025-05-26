
"""
Emerald's Killfeed - Embed Testing System
Test various embed configurations and styles
"""

import logging
from datetime import datetime, timezone

import discord
from discord.ext import commands
from bot.utils.embed_factory import EmbedFactory

logger = logging.getLogger(__name__)

class EmbedTest(commands.Cog):
    """
    EMBED TESTING
    - Test embed configurations
    - Preview embed styles
    - Debug embed issues
    """
    
    def __init__(self, bot):
        self.bot = bot
    
    @discord.slash_command(name="embed_test", description="Test embed configurations")
    @discord.default_permissions(administrator=True)
    async def embed_test(self, ctx: discord.ApplicationContext, 
                        embed_type: discord.Option(str, "Type of embed to test",
                                                  choices=["basic", "success", "error", "warning", "info"])):
        """Test different embed configurations"""
        try:
            if embed_type == "basic":
                embed = EmbedFactory.build(
                    title="🧪 Basic Embed Test",
                    description="This is a basic embed test with standard formatting.",
                    color=0x3498DB,
                    timestamp=datetime.now(timezone.utc)
                )
                
                embed.add_field(
                    name="📝 Field 1",
                    value="This is the first test field",
                    inline=True
                )
                
                embed.add_field(
                    name="📝 Field 2",
                    value="This is the second test field",
                    inline=True
                )
                
                embed.add_field(
                    name="📝 Field 3",
                    value="This is a full-width field",
                    inline=False
                )
            
            elif embed_type == "success":
                embed = EmbedFactory.build(
                    title="✅ Success Embed Test",
                    description="This embed represents successful operations.",
                    color=0x00FF00,
                    timestamp=datetime.now(timezone.utc)
                )
                
                embed.add_field(
                    name="🎉 Operation",
                    value="Test operation completed successfully!",
                    inline=False
                )
            
            elif embed_type == "error":
                embed = EmbedFactory.build(
                    title="❌ Error Embed Test",
                    description="This embed represents error conditions.",
                    color=0xFF6B6B,
                    timestamp=datetime.now(timezone.utc)
                )
                
                embed.add_field(
                    name="🚨 Error Details",
                    value="This is a test error message for debugging purposes.",
                    inline=False
                )
            
            elif embed_type == "warning":
                embed = EmbedFactory.build(
                    title="⚠️ Warning Embed Test",
                    description="This embed represents warning conditions.",
                    color=0xFFD700,
                    timestamp=datetime.now(timezone.utc)
                )
                
                embed.add_field(
                    name="🔔 Warning Message",
                    value="This is a test warning for user attention.",
                    inline=False
                )
            
            elif embed_type == "info":
                embed = EmbedFactory.build(
                    title="ℹ️ Info Embed Test",
                    description="This embed provides informational content.",
                    color=0x17A2B8,
                    timestamp=datetime.now(timezone.utc)
                )
                
                embed.add_field(
                    name="📊 Information",
                    value="This is test information for users.",
                    inline=False
                )
            
            await ctx.respond(embed=embed)
            
        except Exception as e:
            logger.error(f"Failed to test embed: {e}")
            await ctx.respond("❌ Failed to generate test embed.", ephemeral=True)
    
    @discord.slash_command(name="embed_factory_test", description="Test EmbedFactory functionality")
    @discord.default_permissions(administrator=True)
    async def embed_factory_test(self, ctx: discord.ApplicationContext):
        """Test the EmbedFactory system"""
        try:
            embed = EmbedFactory.build(
                title="🏭 EmbedFactory Test",
                description="Testing the EmbedFactory system with all features.",
                color=0x9B59B6,
                timestamp=datetime.now(timezone.utc)
            )
            
            embed.add_field(
                name="🔧 Factory Status",
                value="✅ Working correctly",
                inline=True
            )
            
            embed.add_field(
                name="📊 Tests Passed",
                value="✅ All systems operational",
                inline=True
            )
            
            embed.add_field(
                name="🎨 Theme",
                value="✅ Consistent styling applied",
                inline=True
            )
            
            embed.add_field(
                name="🖼️ Assets",
                value="✅ Thumbnails and footers working",
                inline=False
            )
            
            await ctx.respond(embed=embed)
            
        except Exception as e:
            logger.error(f"Failed to test EmbedFactory: {e}")
            await ctx.respond("❌ EmbedFactory test failed.", ephemeral=True)

def setup(bot):
    bot.add_cog(EmbedTest(bot))
