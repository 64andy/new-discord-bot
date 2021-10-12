import os
import discord
from dotenv import load_dotenv
from discord.ext import commands

from .cogs import Music, Archive

# alexa play https://www.youtube.com/watch?v=dv1ypynSLzY

bot = commands.Bot(
    command_prefix='alexa ',
    description='[Andy stole this from Github]'
                '(https://gist.github.com/vbe0201/ade9b80f2d3b64643d854938d40a0a2d)',
)


@bot.event
async def on_ready():
    print(
        'Logged in as:\n'
        f'Username: {bot.user.name!r}\n'
        f'ID: {bot.user.id}'
    )

if __name__ == "__main__":
    load_dotenv()
    bot.add_cog(Music(bot))
    bot.add_cog(Archive(bot))
    bot.run(os.environ['TOKEN'])
