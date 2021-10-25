import discord
from discord.ext import commands
from typing import Dict

import math
import random

from discord.ext.commands.context import Context



class Oracle(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot


    @commands.command(name='8ball', aliases=['🎱'])
    async def _8ball(self, ctx: commands.Context, question=None):
        """Provides a random magic 8ball response to a question."""
        answers=[
            'It is certain.',
            'It is decidedly so.',
            'Without a doubt.',
            'Yes definitely.',
            'You may rely on it.',
            'As I see it, yes.',
            'Most likely.',
            'Outlook good.',
            'Yes.',
            'Signs point to yes.',
            'Reply hazy, try again.',
            'Ask again later.',
            'Better not tell you now.',
            'Cannot predict now.',
            'Concentrate and ask again.',
            'Don\'t count on it.',
            'My reply is no.',
            'My sources say no.',
            'Outlook not so good.',
            'Very doubtful.']

        snark = [
            'Did you hear something?',
            'You forgot the question.',
            'Try adding a question next time.',
            'Try again, dipshit.']

        if question == None:
            await ctx.send(random.choice(snark))
        else: 
            await ctx.send(f'🎱 {random.choice(answers)}')

    @commands.command(name="coinflip", aliases=["coin","flip"])
    async def _coinflip(self, ctx: commands.Context):
        """Flips a coin, and observes the outcome."""
        sides=['Heads.','Tails.']

        await ctx.send(f':coin: {random.choice(sides)}')