from datetime import datetime
import discord
from discord.ext import commands
from typing import Optional

from .db.models import get_archive_channel, set_archive_channel

TICK_EMOJI = discord.PartialEmoji(name='✅')


class ArchiveCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name='set-archive')
    @commands.has_guild_permissions(manage_channels=True)
    async def set_pin_channel(self, ctx: commands.Context, *, channel: Optional[discord.TextChannel]):
        """
        Sets the given channel to the 'archive' channel.
        Any pinned messages will get put into it.
        """
        if channel is None:
            channel = ctx.channel

        set_archive_channel(ctx.guild, channel)
        await ctx.message.add_reaction(TICK_EMOJI)
        await ctx.send(f"Archive set. Now pins will show up in {channel.mention}.", delete_after=20)

    @commands.command(name='remove-archive')
    @commands.has_guild_permissions(manage_channels=True)
    async def remove_pin_channel(self, ctx: commands.Context):
        """
        Unsets the pin channel
        """
        set_archive_channel(ctx.guild, None)
        await ctx.message.add_reaction(TICK_EMOJI)
        await ctx.send("Archive forgotten.", delete_after=20)

    @commands.Cog.listener("on_guild_channel_pins_update")
    async def add_pin_to_archive(self, channel: discord.TextChannel, last_pin: Optional[datetime]):
        # Check 1: If the action was an unpin, ignore.
        if last_pin is None:
            return
        # Check 2: If no channel's set, ignore.
        guild = channel.guild
        archive_channel_id = get_archive_channel(guild)
        if archive_channel_id is None:
            print(f"No archive channel set for {guild.name}")
            return
        # Check 3: If the archive channel doesn't exist (been deleted), unset it.
        archive_channel = self.bot.get_channel(archive_channel_id)
        if archive_channel is None:
            print(f"{guild.name}'s archive channel is missing. Unset it.")
            set_archive_channel(guild, None)

        latest_pin: discord.Message = (await channel.pins())[0]
        msg = f"""**Original Poster: {latest_pin.author.mention}**:\n{latest_pin.content}"""
        # Copy and reupload any files
        files = [await attachment.to_file(spoiler=attachment.is_spoiler())
                 for attachment in latest_pin.attachments
                 ]

        await archive_channel.send(msg[:2000], files=files)
