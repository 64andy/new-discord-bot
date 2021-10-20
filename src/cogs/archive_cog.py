import discord
from discord.ext import commands
from typing import Dict

TICK_EMOJI = discord.PartialEmoji(name='✅')


class Archive(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name='set-archive')
    @commands.has_guild_permissions(manage_channels=True)
    async def set_archive_channel(self, ctx: commands.Context, *, channel: discord.TextChannel):
        """
        Sets the given channel to the 'archive' channel.
        Any pinned messages will get put into it.
        """
        self.archive_channels[ctx.guild.id] = channel.id
        await ctx.message.add_reaction(TICK_EMOJI)

    @commands.Cog.listener(name="guild_channel_pins_update")
    async def add_pin_to_archive(self, channel: discord.TextChannel, last_pin):
        if last_pin is None:
            # Pins was removed
            return
        archive_channel = self.archive_channels.get(channel.id)
        if archive_channel is None:
            print(f"No archive channel set for {channel.name}")
            return
        latest_pin: discord.Message = (await channel.pins())[0]
        msg = f"**Original Poster: {latest_pin.author}**:\n{latest_pin.content}"
        await archive_channel.send(msg[:2000])
