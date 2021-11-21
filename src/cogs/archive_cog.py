import discord
from discord.ext import commands

from .db.models import get_archive_channel, set_archive_channel, forget_archive_channel

TICK_EMOJI = discord.PartialEmoji(name='✅')


class Archive(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name='set-archive')
    @commands.has_guild_permissions(manage_channels=True)
    async def set_pin_channel(self, ctx: commands.Context, *, channel: discord.TextChannel):
        """
        Sets the given channel to the 'archive' channel.
        Any pinned messages will get put into it.
        """
        set_archive_channel(ctx.guild, channel.id)
        await ctx.message.add_reaction(TICK_EMOJI)
    
    @commands.command(name='remove-archive')
    @commands.has_guild_permissions(manage_channels=True)
    async def remove_pin_channel(self, ctx: commands.Context, *, channel: discord.TextChannel):
        """
        Unsets the pin channel
        """
        forget_archive_channel(ctx.guild)
        await ctx.message.add_reaction(TICK_EMOJI)

    @commands.Cog.listener(name="guild_channel_pins_update")
    async def add_pin_to_archive(self, channel: discord.TextChannel, last_pin):
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
            forget_archive_channel(guild)
        
        latest_pin: discord.Message = (await channel.pins())[0]
        msg = f"""**Original Poster: {latest_pin.author.mention}**:\n{latest_pin.content}"""
        # Copy and reupload any files
        files = [attachment.to_file(spoilers=attachment.is_spoiler())
                    for attachment in latest_pin.attachments
                ]
        
        await archive_channel.send(msg[:2000], files=files)
