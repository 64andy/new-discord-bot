import asyncio
import os
import discord
from dotenv import load_dotenv
from discord.ext import commands

from .cogs import MusicCog, ArchiveCog, OracleCog
from .cogs.db.models import get_command_prefix, init_database

# alexa play https://www.youtube.com/watch?v=dv1ypynSLzY


async def get_prefix(bot: commands.Bot, message: discord.Message):
    prefix = get_command_prefix(message.guild)
    return commands.when_mentioned_or(prefix)(bot, message)

intents = discord.Intents.default()
intents.message_content = True

class MyBot(commands.Bot):
    async def setup_hook(self):
        await self.tree.sync()

bot = MyBot(
    intents=intents,
    command_prefix=['alexa', 'navi', 'alexa,', 'navi,'],
    description='Personal Discord Music Bot that can also play local music. Forked from '
                'https://gist.github.com/vbe0201/ade9b80f2d3b64643d854938d40a0a2d',
)
bot.strip_after_prefix = True


@bot.event
async def on_ready():
    print(
        'Logged in as:\n'
        f'Username: {bot.user.name!r}\n'
        f'ID: {bot.user.id}'
    )

async def add_all_cogs(bot):
    """Discord.py 2.0 makes adding cogs an async operation"""
    await bot.add_cog(MusicCog(bot, music_folder=os.environ.get("LOCAL_MUSIC_FOLDER")))
    await bot.add_cog(ArchiveCog(bot))
    await bot.add_cog(OracleCog(bot))


if __name__ == "__main__":
    # Load the .env vars
    load_dotenv()

    # Add the cogs
    asyncio.run(add_all_cogs(bot))
    # Load the database
    init_database()
    
    try:
        token = os.environ['TOKEN']
    except KeyError:
        raise KeyError("Environment variable 'TOKEN' is not set. Have you created a .env file?")
    bot.run(token)
