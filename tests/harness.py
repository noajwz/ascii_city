"""Import ascii_city with its colours stubbed, so it can be driven headlessly.

init_colors() needs a real terminal, and almost everything in the renderer wants
a colour to write. This stands in for it.

One trap, and it has cost time more than once: **every colour here is the same
number**. A test that counts "cells drawn in X" will match the whole screen
unless it first gives X a value of its own - see how checks.py sets FLASH, HAZE
and the star colours to distinct sentinels before counting them."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import ascii_city as ac

ac.PALETTES = {"near": list(range(1, 13)), "mid": list(range(13, 21)),
               "far": list(range(21, 27)), "dark": list(range(27, 32)),
               "leaf": list(range(32, 37)), "warm": list(range(37, 42)),
               "cold": list(range(42, 47)), "rust": list(range(47, 52)),
               "red": list(range(52, 57))}
ac.NEON = [(100 + i, 200 + i) for i in range(8)]
for _n in ("STAR", "STREET", "HUD", "CURB", "HAZE", "SMOKE", "EMBER",
           "EMBER_HOT", "RAIN", "RAIN_FAR", "BULB", "BULB_DIM", "FLASH",
           "CONCRETE", "GOLD", "GOLD_DIM", "ROU_RED", "ROU_BLACK",
           "ROU_GREEN", "LANE", "GRASS", "BARK", "ROOF"):
    setattr(ac, _n, 1)
ac.curses.A_BOLD = 0
ac.curses.A_REVERSE = 0
