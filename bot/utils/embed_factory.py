"""
Emerald's Killfeed - Embed Factory
Consistent embed creation across all bot functions
"""

import discord
from datetime import datetime, timezone
from typing import Optional

class EmbedFactory:
    """Factory class for creating consistent Discord embeds"""

    # Default colors for different embed types
    COLORS = {
        'success': 0x00FF00,
        'error': 0xFF6B6B,
        'warning': 0xFFD700,
        'info': 0x3498DB,
        'premium': 0xFFD700,
        'default': 0x3498DB
    }

    @staticmethod
    def build(title: str, description: str = None, color: int = None, 
             timestamp: datetime = None, **kwargs) -> discord.Embed:
        """
        Build a standard embed with consistent formatting

        Args:
            title: Embed title
            description: Embed description
            color: Embed color (hex)
            timestamp: Embed timestamp
            **kwargs: Additional embed properties

        Returns:
            discord.Embed: Configured embed
        """
        # Use default color if none provided
        if color is None:
            color = EmbedFactory.COLORS['default']

        # Create embed
        embed = discord.Embed(
            title=title,
            description=description,
            color=color,
            timestamp=timestamp or datetime.now(timezone.utc)
        )

        # Set footer if not provided
        if 'footer' not in kwargs:
            embed.set_footer(text="Powered by Discord.gg/EmeraldServers")

        # Set thumbnail if available
        if 'thumbnail' not in kwargs:
            embed.set_thumbnail(url="attachment://main.png")

        return embed

    @staticmethod
    def success(title: str, description: str = None, **kwargs) -> discord.Embed:
        """Create a success embed"""
        return EmbedFactory.build(
            title=title,
            description=description,
            color=EmbedFactory.COLORS['success'],
            **kwargs
        )

    @staticmethod
    def error(title: str, description: str = None, **kwargs) -> discord.Embed:
        """Create an error embed"""
        return EmbedFactory.build(
            title=title,
            description=description,
            color=EmbedFactory.COLORS['error'],
            **kwargs
        )

    @staticmethod
    def warning(title: str, description: str = None, **kwargs) -> discord.Embed:
        """Create a warning embed"""
        return EmbedFactory.build(
            title=title,
            description=description,
            color=EmbedFactory.COLORS['warning'],
            **kwargs
        )

    @staticmethod
    def info(title: str, description: str = None, **kwargs) -> discord.Embed:
        """Create an info embed"""
        return EmbedFactory.build(
            title=title,
            description=description,
            color=EmbedFactory.COLORS['info'],
            **kwargs
        )

    @staticmethod
    def premium(title: str, description: str = None, **kwargs) -> discord.Embed:
        """Create a premium-themed embed"""
        return EmbedFactory.build(
            title=title,
            description=description,
            color=EmbedFactory.COLORS['premium'],
            **kwargs
        )