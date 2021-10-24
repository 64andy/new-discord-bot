import discord
from discord.ext import commands
from typing import Dict

import math
import random

from discord.ext.commands.context import Context



class Answers(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot


    @commands.command(name='8ball')
    async def _8ball(self, ctx: commands.Context):
        """Provides a random magic 8ball response to a question."""

        