import os
from music_cog import Music
from dotenv import load_dotenv
from discord.ext import commands

load_dotenv()


bot = commands.Bot('music.', description='Yet another music bot.')
bot.add_cog(Music(bot))


@bot.event
async def on_ready():
    print(f'Logged in as:\n{bot.user.name}\n{bot.user.id}'

bot.run(os.environ['TOKEN'])