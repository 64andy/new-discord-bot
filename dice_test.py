import re
import random

class PATTERNS:
    MULTIPLE_DIE = r"^(\d*)d(\d+)$"               # Rolling a die multiple times (e.g. '4d6', '2d20', 'd8')
    MULTIPLE_DIE_MOD = r"^(\d*)d(\d+)[\+\-](\d+)$"  # Rolling multiple dice with a modifier (e.g. 'd20-4', '2d20+15', '3d4+2')

class Die:
    n_dice: int             # The number of dice being rolled
    dice_sides: int         # How big is the dice? d20, d6, etc
    modifier: int           # A flat value to add/sub from the roll
    
    def __init__(self, n_dice: str, dice_sides: str, modifier: str | None):
        self.n_dice = int(n_dice or 1)
        self.dice_sides = int(dice_sides)
        self.modifier = 0 if modifier is None else int(modifier)
    
    def __repr__(self):
        val = f"{self.n_dice}d{self.dice_sides}"
        if self.modifier != 0:
            val += f"{self.modifier:+g}"
        return val
    
    def roll(self) -> int:
        total = 0
        for _ in range(self.n_dice):
            total += random.randint(1, self.dice_sides)
        total += self.modifier
        return total

    @staticmethod
    def create(die: str) -> 'Die':
        if die.isdigit():
            return DieJustModifier(die)
        # Dice + Sides + Modifier (e.g. 4d10+3)
        m = re.match(PATTERNS.MULTIPLE_DIE_MOD, die)
        if m != None:
            n_dice, dice_sides, modifier = m.groups()
            return Die(n_dice, dice_sides, modifier)
        
        # Dice + Sides (e.g. 2d4, can also match d5)
        m = re.match(PATTERNS.MULTIPLE_DIE, die)
        if m != None:
            n_dice, dice_sides = m.groups()
            return Die(n_dice, dice_sides, None)
        
        # Doesn't match anything
        raise ValueError(f"Couldn't parse {die!r}")

class DieJustModifier(Die):
    def __init__(self, mod: int):
        super().__init__(0, 0, mod)
    def __repr__(self):
        return repr(self.modifier)
    def roll(self) -> int:
        return self.modifier

class InputDice:
    all_dice: list[Die]     

    @staticmethod
    def create(all_dice: str) -> 'InputDice':
        all_parts = re.split(r"[\+\-]", all_dice)
        me = InputDice()
        me.all_dice = [Die.create(die) for die in all_parts]
        return me
    
    def __repr__(self):
        return repr(self.all_dice)
            
            

x = InputDice.create('2d4+5')
y = InputDice.create('2d4')
z = InputDice.create('d4')
w = InputDice.create('4+4+4+4+4')
print(w, x, y, z)

print(InputDice.create("d20+4+1d4"))