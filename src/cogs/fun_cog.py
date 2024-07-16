import discord
from discord.ext import commands
from typing import List, Optional

import random

class OracleCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name='8ball', aliases=['🎱'])
    async def _8ball(self, ctx: commands.Context, question: Optional[str]):
        """Provides a random magic 8ball response to a question."""
        answers = [
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
            'You forgot the question.',
            'Try adding a question next time.',
            'Cat got your tongue? Speak your question.']

        if question == None:
            answer = random.choice(snark + " (Format: `alexa 8ball `__**`question goes here`**__)")
        else:
            # Unique so the same person asking the same question gets the same answer
            # (within the same session, PYTHONHASHSEED is random on each start-up)
            index = hash(ctx.message.content) + ctx.message.author.id
            index %= len(answers)
            answer = answers[index]
        await ctx.send(f'🎱 {answer}')

    @commands.command(name="coinflip", aliases=["coin", "flip"])
    async def _coinflip(self, ctx: commands.Context):
        """Flips a coin, and observes the outcome."""
        sides = ['Heads.', 'Tails.']

        await ctx.send(f':coin: {random.choice(sides)}')

    @commands.command(name="choose", aliases=["decide", "pick"])
    async def _choose(self, ctx: commands.Context, *, options: Optional[str]):
        """Randomly selects from a user-generated list of options."""
        FORMAT = " (Format: `alexa choose `__**`choices, separated, by, commas`**__)"
        if options is None:
            selection = None
        else:
            # Ignore all the empty options
            selection = random.choice([value.strip()
                                       for value in options.split(',')
                                       if len(value) == 0 or value.isspace()])

        snark = [
            'Gee, quite the selection there.',
            'Did you forget something?',
            'Not much to really choose from.',
            'Try again, and actually list some stuff this time.'
        ]

        forcedsnark = [
            'Last time I had this many options there was a gun to my head.',
            'Is that my only choice? Ok, {option}',
            'What happens if I don\'t?',
            'Out of all the options, I guess I\'d have to go with {option}.',
            '"{option}"? Is that my only option?',
            'You\'re supposed to give me a comma-separated list.'
        ]

        if selection == None:
            msg = random.choice(snark) + FORMAT
        elif len(options.split(',')) == 1:
            msg = random.choice(forcedsnark).format(option=selection) + FORMAT
        else:
            msg = selection
        await ctx.send(msg)

    @commands.command(name="d20")
    async def _d20(self, ctx: commands.Context):
        """Rolls a single D20"""
        dice = [20]
        return await self._roll_given_dice(ctx, dice)

    @commands.command(name="roll")
    async def _roll(self, ctx: commands.Context, *, dice_to_roll: Optional[str]):
        """
        Rolls the given number of plus-separated dice.
        (e.g. `roll 6+6+20` rolls two 6-sided dice & one 20-sided).
        If no dice are given, it defaults to one 6-sided.
        """
        snark = [
            'Oh, right, let me just roll an infinitely small point for you.',
            'Are you that desperate for a max roll?',
            'If you can\'t _not_ hit a crit, is it even a crit?',
            'Why would you bother trying?',
            'This is pointless, this die is pointless.',
            'I\'m just gonna say you missed.',
            'Why don\'t you roll for some _bitches?_',
            'Try rolling an actual range for once.'
        ]

        invertsnark = [
            'You can\'t roll a negative sided die, just invert it in your head!',
            'Stop trying to roll negative numbers!',
            'Inverted dice aren\'t real!',
            '"Hmm, yes, today I think I\'ll roll negative numbers" words thought up by the utterly deranged.'
        ]

        stringsnark = [
            'What am I supposed to be rolling here?',
            'An integer genius, whole numbers only.',
            'I only work in numbers'
        ]

        dice: List[int] = []
        # If no string is given, default to a D6
        if dice_to_roll is None:
            dice = [6]
            return await self._roll_given_dice(ctx, dice)
        # Otherwise it's '+' separated list of numbers
        for num in dice_to_roll.split('+'):
            try:
                num = int(num)
            except ValueError:
                # Can't parse as int ('cheese' isn't a number)
                return await ctx.send(random.choice(stringsnark))
            if num < 0:
                # Can't roll a negative-sided dice
                return await ctx.send(random.choice(invertsnark))
            if num == 0 or num == 1:
                # No such thing as a 0-sided/1-sided dice
                return await ctx.send(random.choice(snark))
            else:
                dice.append(num)
        # Special case: A single 2-sided dice is a coin
        if dice == [2]:
            return await ctx.invoke(self._coinflip)

        return await self._roll_given_dice(ctx, dice)

    async def _roll_given_dice(self, ctx: commands.Context, dice: List[int]):
        """
        Handles the rolling of dice & the result messages to send
        """
        # Roll each dice
        dice_results = [random.randint(1, num) for num in dice]
        if len(dice_results) == 1:
            # '<dice> 14'
            msg = f":game_die: {dice_results[0]}"
        else:
            # "<dice>1<dice>2<dice>3<dice>4 = 10.
            #  4 dice, 10.00 avg"
            n_dice, total = len(dice_results), sum(dice_results)
            avg = total / n_dice
            results_string = ' + '.join(
                f":game_die:{res}" for res in dice_results)
            msg = (f"{results_string} = {total}.\n"
                   f"{n_dice} dice, {avg:.2f} average")
        await ctx.send(msg)

    @commands.command(name="gay")
    async def _gay(self, ctx: commands.Context):
        """gay"""

        embed = discord.Embed(title="BORN TO CRY", url="https://64andy.neocities.org/",
                              description="WORLD IS A FEAR", color=0xdeadff)
        embed.set_author(name="[DL] Locked", url="https://twitter.com/locked_dream",
                         icon_url="https://circle-strafe-2001.neocities.org/misakool.png")
        embed.set_thumbnail(
            url="https://circle-strafe-2001.neocities.org/spacecool.gif")
        embed.add_field(name="恶魔 Kill Em All 2012",
                        value="I am gamer girl", inline=False)
        embed.set_footer(text="27,453,665 AUTOMATA RUNS")
        await ctx.send(embed=embed)

    @commands.command(name="about")
    async def _about(self, ctx: commands.Context):
        """Defines the primary purpose of this bot."""

        msg = "https://cdn.discordapp.com/attachments/295826646748102657/950218645273989190/FNLjoAsVgAYA0pN.png"
        await ctx.send(msg)
