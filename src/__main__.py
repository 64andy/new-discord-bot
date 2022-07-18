import os
import discord
from dotenv import load_dotenv
from discord.ext import commands

from .cogs import Music, Archive, Oracle
from .cogs.db.models import get_command_prefix, init_database

# alexa play https://www.youtube.com/watch?v=dv1ypynSLzY


async def get_prefix(bot: commands.Bot, message: discord.Message):
    prefix = get_command_prefix(message.guild)
    return commands.when_mentioned_or(prefix)(bot, message)

bot = commands.Bot(
    command_prefix=['alexa', 'navi', 'alexa,', 'navi,'],
    description='[Andy stole this from Github]'
                '(https://gist.github.com/vbe0201/ade9b80f2d3b64643d854938d40a0a2d)',
)
bot.strip_after_prefix = True


@bot.event
async def on_ready():
    print(
        'Logged in as:\n'
        f'Username: {bot.user.name!r}\n'
        f'ID: {bot.user.id}'
    )

if __name__ == "__main__":
    # Load the .env vars
    load_dotenv()

    # Add the cogs
    bot.add_cog(Music(bot))
    bot.add_cog(Archive(bot))
    bot.add_cog(Oracle(bot))
    
    # Load the database
    init_database()

    bot.run(os.environ['TOKEN'])
