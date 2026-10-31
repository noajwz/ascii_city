#!/usr/bin/env python3
"""
ascii_city.py - an endless, procedurally generated ASCII city, seen two ways.

    skyline   the city from outside: parallax layers sliding past as you walk
    street    the city from inside, in the rain: turn where you like, follow the
              neon or take the dark alley, and see whether you find your way out

Controls:
    tab / v                     switch view
    space                       wander on its own
    q                           quit

    skyline   left / right    or  h / l   walk           H / L   run
    street    up / down       or  w / s   walk           W / S   run
              left / right    or  a / d   turn
              , / .                       sidestep

No dependencies on Linux/macOS (curses ships with Python).
On Windows:  pip install windows-curses
"""

import curses
import math
import random
import re
import time
import unicodedata

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

FPS = 30
KEY_GRACE = 0.15       # how long a keypress keeps you moving (smooths key repeat)
RUN_MULTIPLIER = 3.0
BIG = 1 << 30          # added before int() so truncation floors negatives too

# --- skyline view ---
CHUNK_W = 200          # how many "world columns" one generated chunk covers
WALK_SPEED = 20.0      # world columns per second

# Each layer is one depth plane of the city.
# parallax: 0.0 = infinitely far away (never moves), 1.0 = right next to you.
# h and w are (min, max); h is a fraction of the available screen height.
# dens is how many of a facade's windows are lit. Falling away with distance is
# most of what separates the layers: the far bank is a dim shape, the near one
# is a lit building. gap widens as it comes forward so the near layer is a row
# of towers with sky between them rather than a wall across the bottom.
LAYERS = [
    dict(parallax=0.20, h=(0.22, 0.48), w=(4, 10), gap=(2, 6),
         dens=(0.06, 0.22), palette="far"),
    dict(parallax=0.45, h=(0.30, 0.66), w=(6, 15), gap=(3, 8),
         dens=(0.20, 0.50), palette="mid"),
    dict(parallax=1.00, h=(0.28, 0.76), w=(8, 20), gap=(5, 15),
         dens=(0.38, 0.80), palette="near"),
]

# --- street view ---
# The city is a grid of cells; a cell is either open (street, alley, courtyard)
# or one building. World x and z run along the grid, y is up from the road.
CELL = 5.0             # world size of one grid cell, and so one building's front
XP = 9                 # cells from one avenue to the next
ZP = 9                 # ... and from one cross street to the next
EYE_Y = 3.2            # how high off the road you are looking from
BODY = 1.15            # how close to a wall you can get
NEAR_Z = 0.6
MAX_VIEW = 130.0       # how far a wall ray is followed
GROUND_FAR = 80.0
PLANE = 0.9            # half-width of the camera plane: about 84 degrees across
FLOOR_H = 2.4          # world height of one storey
BAY_W = 1.6            # world width of one window bay
PAVE = 1.7             # pavement width, measured in from a facade
WALK = 14.0            # world units per second
TURN = 1.9             # radians per second
SIDESTEP = 8.0

SIGN_CLEAR = 4.2       # a projecting sign must clear anyone walking under it
SIGN_STEP = 1.15       # world height of one stacked letter
SIGN_OUT = 0.95        # how far a sign hangs off the wall, to its middle
SIGN_HALF = 0.55       # and half its depth, out and back from that

SMOKE_CYCLE = 7.0      # seconds between drags
DRAG_LEN = 1.2         # how long a drag lasts

# --- rain ---
RAIN_LATTICE = 1.35    # world spacing of the drop lattice
RAIN_REACH = 13        # lattice cells around you that can hold a drop
RAIN_TOP = 17.0        # how high above the road a drop starts
RAIN_SPEED = 24.0      # world units per second
RAIN_STREAK = 0.028    # seconds of fall drawn as one streak

# --- lightning ---
# A storm is a weather in its own right, not something that happens to a
# downpour. It is the rarest of them by some way - a few percent of the time -
# and while one is overhead it is violent: it brings its own rain and the
# strikes come every couple of seconds.
STORM_SLOT = 210.0     # seconds per slot in which a storm might blow up
STORM_ODDS = 6         # and only one slot in this many has one
STORM_SHORT = 35.0     # how long the briefest storm lasts
STORM_LONG = 80.0      # and the longest

# --- snow ---
# Rarer than a storm. When it comes it is the whole sky's weather - no rain,
# the streets dry, the stars gone - and it settles: the pavements, the roads,
# every roofline and the trees go white while it falls, and it takes a few
# minutes to melt once it has stopped.
SNOW_SLOT = 300.0      # seconds per slot in which it might snow
SNOW_ODDS = 24         # one slot in this many: rarer than a storm
SNOW_SHORT = 120.0
SNOW_LONG = 280.0
SNOW_SETTLE = 90.0     # seconds of snowfall to cover everything
SNOW_MELT = 240.0      # and to be gone again afterwards
SNOW_SPEED = 1.6       # how fast a flake falls, world units a second
STRIKE_EVERY = 2.8     # seconds between strikes once one is overhead

# --- the club, and the casino across town ---
CLUB_ODDS = 1200       # one building in this many is one, and it is unmarked
CLUB_BPM = 134.0
# Every so often the door swings open, light pours out across the street,
# and the front of the queue goes in. The rest shuffle up.
CLUB_DOOR = 12.0       # seconds between one opening and the next
CLUB_OPEN = 1.8        # and how long it stands open
CLUB_QUEUE = 5         # people waiting
CLUB_GAP = 0.85        # world units between them in the line
# Closing time, the last stretch of every night but the strange one: the
# music stops, the house lights come up, the door stands open and they all
# come out and go home.
CLOSE_LEN = 75.0       # seconds of it, at the end of the night
LEAVE_GAP = 0.9        # seconds between one coming out and the next
LEAVE_FOR = 50.0       # and how long they keep coming
LEAVE_PACE = 1.15      # units a second, walking off down the street
BASS_REACH = 2         # cells round a club whose windows rattle on the kick

# --- the woods, and the rig in them ---
# Not a park. The parks are the small green squares the city has everywhere;
# the woods are one great dark block of trees a few districts across, with
# trails through it, a hollow in the middle, and no streets, lights or
# buildings in it at all. One per WOODS_TILE cells each way, so from anywhere
# the nearest is a long walk - and once a night, somebody carries a sound
# system into the hollow and does not ask anyone.
WOODS_TILE = 480       # cells from one woods to the next
# The landmark: one skyscraper a whole city block wide in every LANDMARK_TILE
# square of city, an Art Deco wedding cake - a broad base, the tower set back
# from it, a spire over that - and a techno party on the roof you can walk
# about in.
LANDMARK_TILE = 240    # cells between one and the next, each way
LANDMARK_MAX = 7       # the most cells across it is, each way
LANDMARK_BASE = 34.0   # the base's height, round the edge
LANDMARK_H = 84.0      # the tower's, which is the roof the party is on
SPIRE_H = 34.0         # and the spire's over that
PARTY_BPM = 128.0
LANDMARK_NAMES = ["THE ZENITH", "THE MERIDIAN", "THE APEX", "THE SOVEREIGN",
                  "THE CORONET"]
WOODS_HALF_I = 70      # half its size along x, in cells - 700 units across
WOODS_HALF_J = 42      # and along z
WOODS_OPEN = 54        # percent of the wood you can walk through, off the trails
HOLLOW_RI = 4.6        # the hollow in the middle: radii, in cells
HOLLOW_RJ = 3.4
CROWD = 34             # how many are in it when the rig is on
RAVE_SLOT = 320.0      # seconds per slot in which one might be on
RAVE_ODDS = 7          # and only one slot in this many has one
RAVE_SHORT = 90.0      # the shortest it goes on for
RAVE_LONG = 200.0
RAVE_BPM = 168.0
RAVE_TONES = (1, 6, 5, 2)   # the rig's palette: magenta, purple, green, cyan
RING_GAP = 5.0         # world units between the rings of light on the ground
LAKE_RI = 8.0          # the lake in the woods: radii, in cells
LAKE_RJ = 5.0

# --- the carnival on the bank ---
# A small fairground on the riverbank every so often along it: a big wheel
# with the lights going round, a carousel, a row of stalls, and a string of
# bulbs the length of it. Lit all night, and the wheel lies on the water.
CARNIVAL_GAP = 200     # cells along the river between one and the next
FAIR_LONG = 11         # cells of bank it takes up, along the river
FAIR_DEEP = 4          # and back from the water
CARNIVAL_BESIDE = 2    # cells kept clear between it and the big bridge
FAIR_PIER = 6          # by the big bridge the fair is on a pier this many cells out
FAIR_PIER_MAX = 0.5    # and never further than half way over
SEAFRONT_DEEP = 30     # cells inland the town behind that pier is kept low
# Out on the pier, two more rides: a drop tower near the end, taller than
# the wheel by half again so it is the first thing you see from the
# headland, and a roller coaster looping over the east half of the deck.
DROP_H = 34.0          # the tower's height
DROP_CYCLE = 20.0      # seconds: load, climb, hang, drop, brake
COASTER_LAP = 18.0     # seconds for the train to go round once
COASTER_CARS = 5
WHEEL_R = 10.0         # the wheel's radius in world units
WHEEL_RPM = 1.3

# --- the claw machine, at the end of the row of stalls ---
# One go is one press of p to send the claw sweeping across the glass and a
# second to drop it. Honest the way the slot is: whether it holds is drawn
# when it drops, from how square it came down, and the claw is then shown
# doing it. Square on, it holds a bit under half the time; a column out, a
# fifth; a prize with another sitting on it, never.
CLAW_GLASS = 12        # rows of glass inside the cabinet
CLAW_SWEEP = 7.0       # columns a second the claw travels while you aim
CLAW_TIME = 10.0       # seconds to aim before it drops by itself
CLAW_DROP = 6.0        # rows a second going down, and coming back up
CLAW_FALL = 12.0       # rows a second for a prize that has been let go
CLAW_MOVE = 8.0        # columns a second, carrying it home to the chute
CLAW_SHUT = 0.5        # seconds for the claw to close, or to open
CLAW_HOLD = 2.5        # how long the verdict stays up afterwards
CLAW_GRIP = [0.45, 0.2]  # chance it holds, square on and one column out
# The strength tester, the hammer and the bell: a meter swings up and down
# beside the post and p swings the hammer, the puck going up as far as the
# meter was showing. Near enough the top and the bell goes, and a prize.
STRIKE_SWING = 2.7     # how fast the meter goes, radians a second
STRIKE_BELL = 0.93     # how near the top it has to be for the bell
STRIKE_UP = 0.7        # seconds for the puck to go up, and again to come down
STRIKE_HOLD = 1.6      # and how long the verdict stays up after
STRIKE_SAYS = [(0.0, "WEAKLING"), (0.3, "NOT BAD"), (0.55, "STRONG"),
               (0.75, "MIGHTY"), (STRIKE_BELL, "DING!")]

# --- the big bridge ---
# Once in a long way along the river it opens into a bay, and a suspension
# bridge crosses it: two towers standing in the water, the main cables slung
# over them, and a string of lights the whole way along each cable, which is
# the thing anyone would recognise it by at night.
GRAND_GAP = 600        # cells along the river between one and the next
BAY_WIDEN = 2.2        # how much wider the channel gets under it, on top of itself
BAY_REACH = 16.0       # over how many cells either side it opens out
TOWER_H = 32.0         # world units
TOWER_OUT = 2.5        # the legs stand this far outside the deck's edges
CABLE_SAG = 9.0        # the main cable's height at mid-span
GRAND_SEEN = 340.0     # how far off it is drawn from

# --- and what it lands on ---
# The far side of the bay is not the city. A rocky headland with water round
# three sides of it, nothing built on it, and a lighthouse at the point whose
# beam goes round over the bay, the bridge and the town every few seconds.
HEAD_RI = 16.0         # the headland's radii, in cells
HEAD_RJ = 8.0
HEAD_MOAT = 1.75       # the water round it reaches this far out, in radii
HEAD_BACK = 2.5        # and this far behind the point, so the far town keeps off
LIGHT_H = 21.0         # the lighthouse, in world units
BEAM_TURN = 7.0        # seconds for the beam to go round once
BEAM_REACH = 150.0

# --- the promenade, and what is on the water ---
# Along most of the near bank the buildings stop short of the water and
# leave a walk: a railing, lamps, benches, people leaning. It is where the
# river gets looked at from. And on the water, small things - a ferry
# crossing the bay, a rowing boat with a lantern drifting down - and on one
# night in a dozen, lanterns by the hundred going down with the current.
PROM_STRETCH = 40      # cells; two stretches in three have a promenade
PROM_DEEP = 2          # cells back from the water it takes up
FERRY_PERIOD = 160.0   # seconds for a crossing there and back
ROWBOAT_GAP = 260      # cells along the river between one boat and the next
ROWBOAT_DRIFT = 0.7    # world units a second, with the current
LANTERN_ODDS = 12      # one night in this many has lanterns on the river
LANTERN_DRIFT = 0.9

# --- tunnels ---
# Here and there an avenue goes under a road deck for a stretch: a short
# underpass under one, two cells of it, and now and then a long one where a
# cross street was built over and the avenue goes under the whole block.
# Under the short ones somebody has a fire going in a can.
TUNNEL_H = 5.0         # the ceiling, world units off the road
SHORT_ODDS = 20        # of the avenue-blocks, one in this many has a short one
LONG_ODDS = 3          # of the stretches a long one could go, one in this many
TUNNEL_LAMP = 6.0      # world units between the lights in a long one
_tunnel_cache = {}

# --- dawn ---
# Once in a while a night ends. Over its last DAWN_LEN seconds the sky pales
# from the horizon up, the stars go, the signs switch off one by one and the
# windows go dark, and the city stands black against the morning - and then
# the next night begins, as every night here does.
DAWN_ODDS = 12
DAWN_LEN = 120.0
DAWN_HOLD = 15.0       # seconds of full dawn before the night comes round again

# --- fireworks over the bay ---
# One night in FIREWORK_ODDS somebody puts on a show over the big bridge's
# bay: shells going up off the water all night, and a finale every few
# minutes. Every spark is a world point, so the reflection lays them on the
# bay and the buildings hide the ones behind them.
FIREWORK_ODDS = 15
FW_SLOT = 0.75         # seconds between one launch and the next
FW_RISE = 1.3          # seconds a shell takes to climb
FW_LIFE = 2.4          # and how long the sparks last once it bursts
FW_FINALE = 180.0      # seconds between finales
FW_REACH = 900.0       # how far off you can see them from

# --- your own show, fired from the lighthouse ---
# In at the lighthouse's door and up its stair to the gallery. f up there
# lights a show with you on the button: cues come along a bar at the bottom
# of the screen and every press on the beat sends a real shell up over the
# bay - on time a big one, near enough a smaller one, off the beat a fizzle.
# Anybody on the bridge or the far bank sees what you fire. The better you
# did, the bigger the finale.
SHOW_BPM = 96
SHOW_COUNT = 4         # beats of count-in before the first cue
SHOW_BARS = 12         # four beats a bar
SHOW_GREAT = 0.09      # seconds either side of a cue that count as on it
SHOW_GOOD = 0.18       # and as near enough
SHOW_AHEAD = 3.0       # seconds of cues the bar shows coming
SHOW_FINALE = 7.0      # seconds of finale after the last cue
SHOW_SPREAD = 0.5      # how wide over the bay your shells go up, against a show's
FIRE_REACH = 3.0       # how near the lighthouse's middle the gallery is
LIGHT_DOOR = 1.75      # the door, out from the middle of the tower at its foot
GALLERY_R = 1.6        # where you stand on the gallery, from the middle
# One bar of cues per row: 1 a shell, 2 a big one. The first bars come from
# the easy ones, so the count-in is not followed by a wall of them.
SHOW_BARS_EASY = [(1, 0, 1, 0), (1, 0, 0, 0), (2, 0, 1, 0)]
SHOW_BARS_ALL = SHOW_BARS_EASY + [(1, 0, 1, 1), (1, 1, 1, 0), (2, 0, 0, 2),
                                  (0, 1, 0, 2), (1, 1, 2, 0), (1, 1, 1, 1)]
CASINO_REACH = 2.3     # how close to the door you have to get to be inside
CASINO_AGAIN = 1.6     # seconds before it deals you another one

# --- the sky deck ---
# One tall building in TOWER_ODDS has a lobby you can walk into and a lift to
# the roof. You ride it up - doors, a floor counter, the shaft going by - and
# step out onto the roof with the real city under you.
TOWER_ODDS = 9         # of the buildings tall enough, one in this many
TOWER_MIN = 34.0       # how tall, in world units, a building must be to have one
TOWER_TOP = 72.0       # and how tall it is made: over everything else in town
ROOF_REACH = 260.0     # how far you can see from up there
# The top floors of a sky-deck tower are a weather beacon, the old way:
#   steady blue, clear view; flashing blue, clouds due;
#   steady red, rain ahead; flashing red, snow instead -
# and in a storm, red and white as fast as it will go.
CROWN_FLOORS = 2       # how many storeys at the top are lit
CROWN_BLINK = 1.2      # flashes a second, for the flashing ones
ROOF_STEP = 1.6        # how far from the middle of the roof you stand
CLIMB_ODDS = 3         # one alley fire escape in this many goes all the way up
CLIMB_FLOOR = 0.45     # seconds a storey, climbing
CLIMB_REACH = 1.9      # how close to the ladder you have to be
LIFT_DOORS = 0.9       # seconds for the doors to close or open
LIFT_FLOOR = 0.07      # seconds per floor going past

# --- the diner, and the billboards ---
# The diner is open all night and you can see the whole of it from the street:
# a long lit window with the counter and the backs of a few people sat apart.
# The billboards are up on the roofs over the wide streets, selling soda.
DINER_ODDS = 1100      # like the club and the cinema, on its own hash
DINER_POUR = 5.0       # seconds after you sit down that the coffee comes
# Somewhere a few decades on from the rest of the street: gunmetal and neon
# seams, the window lit cold, and on the roof a coffee cup in neon tube the
# size of a car with neon steam coming off it. You find one by the cup.
DINER_NAMES = ["NULL CAFE", "CHROME CUP", "BYTE & BREW", "NEON BREW", "CAFE 2088",
               "DATA DINER", "OVERCLOCK", "GHOST SHIFT"]
CUP_REACH = 170.0      # how far off the cup on the roof is seen from
CUP_SCALE = 0.85       # the cup's size against cup_shape()'s own units
DINER_H = 5.2          # the tallest a diner is: one tall storey and a band
CUP_GLITCH = 6.0       # seconds between the tube's flickers, give or take
BILL_ODDS = 90         # of the wide-street roofs in the busy parts, one in this
BILL_W = 11.0          # world units across a board: big, it is an advert
BILL_ROW = 1.1         # and per row of it
BILL_SEEN = 170.0
BILL_DISTRICTS = ("downtown", "market", "docks", "old town", "chinatown")
ADS = [
    (["FIZZ COLA", "ICE COLD"], 0),
    (["SPARKLE", "TASTE THE NIGHT"], 2),
    (["NOVA SODA", "OUT OF THIS WORLD"], 6),
    (["KOLA KING", "THE REAL THING"], 3),
    (["ZAP!", "LEMON-LIME LIGHTNING"], 5),
    (["DRINK BUBBL", "IT'S A GAS"], 1),
]

# --- the cinema ---
# As rare as a casino and like one only from the outside: a marquee over the
# doors with the film's name in it. Inside it is the quietest light in the
# city - one black-and-white film, on a loop, on the city's own clock, so you
# walk in on whatever is showing.
CINEMA_BIG = 40.0      # nearer than this, the title goes up in the big font
SEARCH_REACH = 260.0   # how far off the searchlights are seen from
SEARCH_LONG = 160.0    # how far up into the sky a beam reaches
SEARCH_LEAN = 0.65     # radians off the vertical: well over, across the sky
FILM_TITLES = ["THE LONG NIGHT", "NEON RAIN", "LAST TRAIN", "AFTER HOURS",
               "CITY OF GLASS", "THE QUIET STREET", "BLUE HOUR", "NOWHERE MAN"]
# And the other half of the cinemas are showing an action picture.
ACTION_TITLES = ["OVERDRIVE", "BURN ZONE", "STEEL NERVE", "ZERO HOUR"]

# --- the arcade ---
# Low, two or three storeys, and loud with it: the whole front is a wall of
# coloured lights running patterns, bulbs going round the roof in every
# colour, ARCADE over the door in big letters that light up one by one and
# then flash, and the glow of the cabinets in the window. The games inside are
# still being built; for now the cabinets run their demos and say so.
ARCADE_ODDS = 1000     # like the club and the cinema, on its own hash
TEMPLE_ODDS = 1100     # the temple: rarer than the arcade, on its own hash
TEMPLE_H = 11.0        # low enough that the rose window is in sight from the road
TEMPLE_GABLE = 2.6     # how far the gable over the front rises past the roof
ROSE_Y = 5.4           # the rose window's middle, over the door
ROSE_R = 1.15
TEMPLE_NAMES = ["THE TEMPLE", "ST. NEON", "HOLY LIGHT", "THE CATHEDRAL", "SANCTUARY"]
ARCADE_BIG = 45.0      # nearer than this, the sign is in the big font
ARCADE_MODE = 5.0      # seconds the light wall runs one pattern before the next
ARCADE_NAMES = ["PIXEL PALACE", "HI-SCORE", "GAME ZONE", "TURBO", "BLIP BLOP",
                "1UP", "POWER UP", "BONUS ROUND", "EXTRA LIFE", "CONTINUE?"]
# The cabinets inside, by what they will be: each runs a demo of its own.
ARCADE_GAMES = ["ROOFTOP RUN", "FIX THE NEON", "LATE DELIVERY", "NEON DRIFT",
                "SKY SHOW", "NIGHT OWL"]

# The casino from the street: a blade sign up the front corner, the name
# stacked down it, standing well out of the wall and up over the roofline; a
# red carpet to the kerb with a doorman by it; and when somebody inside hits
# 777, the whole building in gold, flashing, for half a minute.
BLADE_U = 0.35         # how far along the front the blade stands: at the corner
BLADE_OUT = 1.6        # out from the wall, to its middle
BLADE_HALF = 1.3       # and half its depth either side of that
BLADE_RISE = 3.0       # how far it goes up over the roof
CARPET_HALF = 0.9      # half the carpet's width
JACKPOT_LONG = 30.0    # seconds a casino celebrates a 777

# --- the stock exchange, in the financial district ---
# A classical front among the glass, a ticker running across it with the
# made-up market going by in green and red, and inside a trading floor with
# candles for the house stock and an account to buy and sell it with. The
# prices are a function of time alone: they step every TICK_LEN seconds, and
# a candle is one of those steps, with the high and the low of the way the
# price went inside it.
EXCHANGE_ODDS = 400    # of the financial district's street fronts, one in this
TICK_LEN = 30.0        # seconds a price stands before the next
CANDLES = 48           # how many the chart goes back, at most
LOTS = [1, 10, 100, 0] # how many a trade is: 0 is as many as you can
STARTING_MONEY = 1000.0  # dollars, to start the night with
# What things cost, out of the one wallet.
FEES = {"cinema": 12, "club": 20, "ramen": 14, "diner": 4}
LIFT_FEES = {None: 15, "party": 30}   # the sky decks, and the roof party
SHOW_FEE = 50          # a show fired from the lighthouse
CLAW_COST = 2
STRIKE_COST = 1
ARCADE_COST = 1
SECTORS = ["TECH", "FOOD", "TRANSPORT", "LEISURE"]
STOCKS = [("NEON", "NEON TUBES CO", 0), ("BLIP", "BLIP ARCADES", 0),
          ("GLOW", "GLOWSTICK INDUSTRIES", 0), ("HOLO", "HOLO SIGNAGE", 0),
          ("RAMN", "RAMEN HOLDINGS", 1), ("NOOD", "NOODLE FUTURES", 1),
          ("CUPS", "COFFEE CUP CORP", 1), ("PIES", "PIE CASE INC", 1),
          ("DRFT", "DRIFT MOTORS", 2), ("LIFT", "SKYDECK LIFTS", 2),
          ("FERY", "BAY FERRY LINES", 2), ("ELEV", "EL LINE TRANSIT", 2),
          ("CLAW", "CLAW AND CO", 3), ("CINE", "PICTURE HOUSE", 3),
          ("LUCK", "LUCKY SEVEN GAMING", 3), ("PIER", "PLEASURE PIER LTD", 3)]
# What a stock is doing, for EPOCH ticks at a time: (name, how far it carries
# the price over the epoch in log units, how wild the noise is, how often).
# A move rises across its epoch and then fades back out across the next, so a
# hot streak is followed by the air coming out of it.
EPOCH = 24
MODES = [("stable", 0.0, 1.0, 38), ("rising", 0.22, 1.0, 14),
         ("falling", -0.22, 1.0, 14),
         ("hot", 0.62, 1.2, 9), ("crash", -0.45, 1.5, 7), ("chaotic", 0.0, 3.0, 18)]
STREAK = 4             # ticks one way in a row that the list calls a streak

CASINO_NAMES = ["ROYALE", "GOLDEN", "LUCKY", "ACES", "MIRAGE", "JACKPOT",
                "FORTUNA", "DIAMOND", "SPHINX", "MONTE"]

WINDOW_GLYPHS = "08XZ:+=*%@o.#"

# ---------------------------------------------------------------------------
# Districts
#
# Which part of town a cell is in. Everything a building is - how tall, how
# lit, whether it carries neon and in what colour, what its alleys are like -
# comes from here, so a district is one row of table rather than special cases
# scattered through the generator.
#
# scale multiplies the block's own base height; hi/lo then clamp it, so a block
# still has a coherent skyline of its own inside a district's range.
# neon is which of the eight tubes the district's signs may use, by index, or
# None for any of them - that is what makes Chinatown red and gold and downtown
# every colour at once.
#
# The rest is the wall itself, and it matters more than any of the above: from
# the street you see four storeys of frontage and hardly any roofline, so a
# district told apart only by how tall and how lit it is cannot be told apart
# at all. glyphs is the window alphabet; band draws a line at every storey
# (balconies, or the ribs of a corrugated shed); mullion draws a vertical one
# at every bay, which is what a glass curtain wall looks like and nothing else
# does; ground is what the shopfronts are made of and gap how often there is a
# doorway instead. What goes on a face that gives onto an alley is not a
# district's business at all: see yokocho_at().
# ---------------------------------------------------------------------------

DISTRICT_CELLS = 36        # about 180 world units square, a few blocks

DISTRICTS = [
    dict(key="1", name="downtown", weight=7, scale=1.5, lo=12.0, hi=58.0,
         dens=(0.26, 0.70), flat=0.45, hung=0.45, smoke=0.30, bulb=0.45,
         neon=None, lantern=0.0, park=False,
         glyphs="08XZ*%@#", band=None, mullion=False, ground="#", gap=4,
         pal="near", roof="=", whole_floors=False, cjk=False),
    dict(key="2", name="residential", weight=5, scale=0.45, lo=6.0, hi=14.0,
         dens=(0.34, 0.66), flat=0.0, hung=0.0, smoke=0.18, bulb=0.30,
         neon=None, lantern=0.0, park=False,
         glyphs="0oo.", band="\"", mullion=False, ground="n", gap=3,
         pal="warm", roof="=", whole_floors=False, cjk=False),
    dict(key="3", name="old town", weight=4, scale=0.6, lo=7.0, hi=18.0,
         dens=(0.30, 0.62), flat=0.15, hung=0.20, smoke=0.30, bulb=0.40,
         neon=(2, 5, 7), lantern=0.0, park=False,
         glyphs="+:8O", band=None, mullion=False, ground="n", gap=3,
         pal="mid", roof="^", whole_floors=False, cjk=False),
    dict(key="4", name="chinatown", weight=3, scale=0.7, lo=8.0, hi=22.0,
         dens=(0.38, 0.78), flat=0.80, hung=0.50, smoke=0.30, bulb=0.55,
         neon=(3, 4, 7), lantern=0.85, park=False,
         glyphs="#8%@", band="=", mullion=False, ground="#", gap=5,
         pal="red", roof="~", whole_floors=False, cjk=True),
    dict(key="5", name="market", weight=3, scale=0.65, lo=7.0, hi=20.0,
         dens=(0.32, 0.68), flat=0.55, hung=0.32, smoke=0.35, bulb=0.60,
         neon=(4, 7), lantern=0.70, park=False,
         glyphs="oO0", band=None, mullion=False, ground="A", gap=2,
         pal="warm", roof="=", whole_floors=False, cjk=False),
    dict(key="6", name="financial", weight=3, scale=1.9, lo=26.0, hi=64.0,
         dens=(0.05, 0.16), flat=0.0, hung=0.0, smoke=0.08, bulb=0.15,
         neon=None, lantern=0.0, park=False,
         glyphs=":.:", band=None, mullion=False, ground=":", gap=6,
         pal="cold", roof="=", whole_floors=True, cjk=False),
    dict(key="7", name="docks", weight=2, scale=0.45, lo=5.0, hi=13.0,
         dens=(0.06, 0.20), flat=0.05, hung=0.05, smoke=0.25, bulb=0.55,
         neon=(4,), lantern=0.0, park=False,
         glyphs="==-", band="-", mullion=False, ground="#", gap=6,
         pal="rust", roof="=", whole_floors=False, cjk=False),
    dict(key="8", name="park", weight=2, scale=0.5, lo=5.0, hi=10.0,
         dens=(0.20, 0.45), flat=0.0, hung=0.0, smoke=0.15, bulb=0.20,
         neon=None, lantern=0.0, park=True,
         glyphs="&%", band=None, mullion=False, ground="&", gap=3,
         pal="leaf", roof="=", whole_floors=False, cjk=False),
]

DISTRICT_PICK = [n for n, d in enumerate(DISTRICTS) for _ in range(d["weight"])]

# The woods are not in the table: they are not picked, they are placed. A
# park's row with the trees taller and nobody smoking under them.
WOODS = dict(key="", name="the woods", weight=0, scale=1.0, lo=9.0, hi=15.0,
             dens=(0.0, 0.0), flat=0.0, hung=0.0, smoke=0.0, bulb=0.0,
             neon=None, lantern=0.0, park=True,
             glyphs="&%", band=None, mullion=False, ground="&", gap=3,
             pal="leaf", roof="=", whole_floors=False, cjk=False)
_district_cache = {}


def district_at(i, j):
    """Which part of town, as an index into DISTRICTS.

    The grid of districts is offset a different amount on every row, so the
    boundaries stagger like brickwork instead of lining up into one long seam
    across the whole city."""
    key = i * 1048576 + j
    hit = _district_cache.get(key)
    if hit is None:
        _evict(_district_cache, 40000)
        dj = j // DISTRICT_CELLS
        di = (i + _mix(dj, 0, 71) % DISTRICT_CELLS) // DISTRICT_CELLS
        hit = DISTRICT_PICK[_mix(di, dj, 313) % len(DISTRICT_PICK)]
        _district_cache[key] = hit
    return hit


HEADLAND = dict(WOODS, name="the headland", park=False)


def district(i, j):
    if woods_at(i, j):
        return WOODS
    if headland_at(i, j):
        return HEADLAND
    return DISTRICTS[district_at(i, j)]

# Chinatown's signs, if the terminal can draw them. Two or three characters
# each, which is what fits a vertical sign and what they actually say: bar,
# noodle house, teahouse, hotpot, dim sum, pharmacy, seafood, roast meats.
CJK_SIGNS = ["酒吧", "麵館", "茶樓", "飯店", "火鍋", "點心",
             "藥房", "金龍", "海鮮", "包子", "餃子", "燒臘"]

# A yokocho is a back lane you would actually go down: the same one-cell width
# as any other alley, but lit, and lined with places too small to have a front
# on the street. Its signs are Japanese for the same reason Chinatown's are
# Chinese - two or three characters is what fits a vertical sign, and it is
# what they say: izakaya, yakitori, sushi, oden, ramen, a stall, a quick one
# standing up.
JP_SIGNS = ["居酒屋", "焼鳥", "寿司", "おでん", "屋台", "立呑",
            "焼肉", "串カツ", "もつ煮", "一杯", "酒処", "麺"]

# Short enough to go over a door rather than down a bracket.
JP_OVER_DOOR = ["居酒屋", "焼鳥", "一杯", "酒",
                "串", "呑", "おでん", "肉"]

# Set once at startup by asking the terminal rather than assuming - a
# double-width character on a terminal that cannot place one wrecks the
# alignment of the whole row.
WIDE_OK = False

SIGN_WORDS = [
    "BAR", "OPEN", "HOTEL", "MOTEL", "PHO", "RAMEN", "SUSHI", "COFFEE",
    "24H", "LIVE", "JAZZ", "TATTOO", "PAWN", "DINER", "LAUNDRY", "EAT",
    "BEER", "ROOMS", "CLUB", "KARAOKE", "NOODLES", "LOTTO",
]

# ---------------------------------------------------------------------------
# Colour setup
#
# curses works with numbered "colour pairs" (foreground + background). We build
# one pair per colour we care about, then remember which pair number is which.
# ---------------------------------------------------------------------------

PALETTES = {}      # e.g. {"near": [3, 7, 12, ...]} -> lists of curses pair numbers
NEON = []          # [(lit, unlit), ...] - one entry per neon tube colour
STAR = STREET = HUD = CURB = HAZE = SMOKE = EMBER = EMBER_HOT = 0
FIREFLY = EYES = SNOW = 0
RAIN = RAIN_FAR = BULB = BULB_DIM = FLASH = CONCRETE = 0
GOLD = GOLD_DIM = ROU_RED = ROU_BLACK = ROU_GREEN = LANE = 0
GRASS = BARK = ROOF = 0
STAR_DIM = STAR_WARM = STAR_COLD = MOON = MOON_DIM = BAND = 0
BEAM = BEAM_DIM = CROWN_BLUE = CROWN_RED = 0


def init_colors():
    global PALETTES, NEON, STAR, STREET, HUD, CURB, HAZE, SMOKE, EMBER
    global EMBER_HOT, RAIN, RAIN_FAR, BULB, BULB_DIM, FLASH, CONCRETE
    global GOLD, GOLD_DIM, ROU_RED, ROU_BLACK, ROU_GREEN, LANE, GRASS, BARK
    global FIREFLY, EYES, SNOW
    global ROOF, STAR_DIM, STAR_WARM, STAR_COLD, MOON, MOON_DIM, BAND
    global BEAM, BEAM_DIM, CROWN_BLUE, CROWN_RED

    curses.start_color()
    try:
        curses.use_default_colors()   # lets us keep the terminal's own background
        bg = -1
    except curses.error:
        bg = curses.COLOR_BLACK

    if curses.COLORS >= 256:
        # xterm-256 colour numbers. Bright saturated up front, muted in back.
        groups = {
            "near": [226, 33, 202, 48, 51, 201, 220, 39, 208, 84, 214, 45],
            "mid":  [31, 130, 100, 65, 96, 67, 137, 72],
            "far":  [24, 60, 23, 238, 59, 66],
            "dark": [235, 236, 237, 238, 239],      # what an alley is lit by
            "leaf": [22, 28, 29, 34, 65],           # a park, at night
            "warm": [180, 179, 215, 137, 223],      # lamps behind curtains
            "cold": [67, 68, 110, 74, 111],         # glass, and nobody home
            "rust": [130, 166, 172, 94, 136],       # sodium light on steel
            "red":  [160, 196, 202, 208, 203],      # lanterns and gold leaf
        }
        # (tube lit, tube dark) - the dark one is also what the sign spills
        # onto the wet road below it.
        neon = [(198, 89), (201, 54), (51, 23), (196, 52),
                (208, 94), (46, 22), (141, 60), (226, 58)]
        extras = {"star": 254, "street": 240, "hud": 245, "curb": 246,
                  "haze": 237, "smoke": 244, "ember": 166, "ember_hot": 208,
                  "rain": 110, "rain_far": 60, "bulb": 222, "bulb_dim": 58,
                  "flash": 231, "concrete": 234, "gold": 220,
                  "gold_dim": 136, "rou_red": 196, "rou_black": 252,
                  "rou_green": 46, "lane": 250, "grass": 22, "bark": 58,
                  "roof": 252, "star_dim": 244, "star_warm": 223,
                  "star_cold": 153, "moon": 231, "moon_dim": 250,
                  "band": 60, "firefly": 118, "eyes": 190, "snow": 255,
                  "crown_blue": 33}
        attrs = {}
    else:
        # 8-colour fallback: bold = the "bright" version of a colour.
        groups = {
            "near": [curses.COLOR_YELLOW, curses.COLOR_BLUE, curses.COLOR_RED,
                     curses.COLOR_GREEN, curses.COLOR_CYAN, curses.COLOR_MAGENTA],
            "mid":  [curses.COLOR_CYAN, curses.COLOR_BLUE, curses.COLOR_GREEN],
            "far":  [curses.COLOR_BLUE, curses.COLOR_BLACK],
            "dark": [curses.COLOR_BLACK],
            "leaf": [curses.COLOR_GREEN],
            "warm": [curses.COLOR_YELLOW],
            "cold": [curses.COLOR_CYAN],
            "rust": [curses.COLOR_RED],
            "red": [curses.COLOR_RED],
        }
        neon = [(curses.COLOR_MAGENTA, curses.COLOR_MAGENTA),
                (curses.COLOR_CYAN, curses.COLOR_CYAN),
                (curses.COLOR_RED, curses.COLOR_RED),
                (curses.COLOR_YELLOW, curses.COLOR_YELLOW)]
        extras = {"star": curses.COLOR_WHITE, "street": curses.COLOR_BLACK,
                  "hud": curses.COLOR_WHITE, "curb": curses.COLOR_WHITE,
                  "haze": curses.COLOR_BLUE, "smoke": curses.COLOR_WHITE,
                  "ember": curses.COLOR_RED, "ember_hot": curses.COLOR_RED,
                  "rain": curses.COLOR_CYAN, "rain_far": curses.COLOR_BLUE,
                  "bulb": curses.COLOR_YELLOW, "bulb_dim": curses.COLOR_BLACK,
                  "flash": curses.COLOR_WHITE, "concrete": curses.COLOR_BLACK,
                  "gold": curses.COLOR_YELLOW, "gold_dim": curses.COLOR_YELLOW,
                  "rou_red": curses.COLOR_RED, "rou_black": curses.COLOR_WHITE,
                  "rou_green": curses.COLOR_GREEN,
                  "lane": curses.COLOR_WHITE, "grass": curses.COLOR_GREEN,
                  "bark": curses.COLOR_BLACK,
                  "roof": curses.COLOR_WHITE, "star_dim": curses.COLOR_BLACK,
                  "star_warm": curses.COLOR_YELLOW,
                  "star_cold": curses.COLOR_CYAN, "moon": curses.COLOR_WHITE,
                  "moon_dim": curses.COLOR_WHITE, "band": curses.COLOR_BLUE,
                  "firefly": curses.COLOR_GREEN, "eyes": curses.COLOR_YELLOW,
                  "snow": curses.COLOR_WHITE, "crown_blue": curses.COLOR_BLUE}
        attrs = {"near": curses.A_BOLD}

    pair = 1
    for name, colours in groups.items():
        ids = []
        for c in colours:
            curses.init_pair(pair, c, bg)
            ids.append(curses.color_pair(pair) | attrs.get(name, 0))
            pair += 1
        PALETTES[name] = ids

    NEON = []
    for lit, unlit in neon:
        curses.init_pair(pair, lit, bg)
        on = curses.color_pair(pair) | curses.A_BOLD
        pair += 1
        curses.init_pair(pair, unlit, bg)
        off = curses.color_pair(pair)
        pair += 1
        NEON.append((on, off))

    made = {}
    for name, c in extras.items():
        curses.init_pair(pair, c, bg)
        made[name] = curses.color_pair(pair)
        pair += 1

    STAR = made["star"]
    STREET = made["street"]
    HUD = made["hud"] | curses.A_BOLD
    CURB = made["curb"]
    HAZE = made["haze"]
    SMOKE = made["smoke"]
    EMBER = made["ember"]
    EMBER_HOT = made["ember_hot"] | curses.A_BOLD
    RAIN = made["rain"]
    RAIN_FAR = made["rain_far"]
    BULB = made["bulb"] | curses.A_BOLD
    BULB_DIM = made["bulb_dim"]
    CROWN_BLUE = made["crown_blue"] | curses.A_BOLD
    CROWN_RED = made["rou_red"]
    # The cinemas' searchlights: the lamp colours, under their own names, so
    # nothing that counts stars or the moon ever counts a beam.
    BEAM, BEAM_DIM = BULB, BULB_DIM
    FLASH = made["flash"] | curses.A_BOLD
    CONCRETE = made["concrete"]
    GOLD = made["gold"] | curses.A_BOLD
    GOLD_DIM = made["gold_dim"]
    ROU_RED = made["rou_red"] | curses.A_BOLD
    ROU_BLACK = made["rou_black"] | curses.A_BOLD
    ROU_GREEN = made["rou_green"] | curses.A_BOLD
    LANE = made["lane"]
    GRASS = made["grass"]
    BARK = made["bark"]
    ROOF = made["roof"] | curses.A_BOLD
    STAR_DIM = made["star_dim"]
    STAR_WARM = made["star_warm"]
    STAR_COLD = made["star_cold"]
    MOON = made["moon"] | curses.A_BOLD
    MOON_DIM = made["moon_dim"]
    FIREFLY = made["firefly"] | curses.A_BOLD
    EYES = made["eyes"]
    SNOW = made["snow"] | curses.A_BOLD
    BAND = made["band"]


def wide_chars_work(stdscr):
    """Whether this terminal and this curses can place a double-width glyph.

    Asked, not assumed, the same way termimage asks about the graphics protocol
    rather than guessing from $TERM: write one into a corner and see whether
    ncurses moves the cursor on two columns instead of one. A curses built
    without wide character support moves it one, and every row with a sign in
    it would come out a column short."""
    try:
        h = stdscr.getmaxyx()[0]
        stdscr.addstr(h - 1, 0, CJK_SIGNS[0][0])
        ok = stdscr.getyx()[1] == 2
        stdscr.move(h - 1, 0)
        stdscr.clrtoeol()
        return ok
    except Exception:
        return False


def is_wide(ch):
    return unicodedata.east_asian_width(ch) in ("W", "F")


def tone_colour(name, tone):
    """Resolve a stored 0..1 'tone' to an actual colour in one of the palettes.

    Generation stores the tone rather than the colour so that a given building
    is the same building whether the terminal has 8 colours or 256."""
    pal = PALETTES[name]
    return pal[min(len(pal) - 1, int(tone * len(pal)))]


def _mix(a, b, c):
    """A tiny deterministic hash. Unlike hash() it does not depend on the run."""
    h = ((a * 73856093) ^ (b * 19349663) ^ (c * 83492791)) & 0xFFFFFFFF
    h ^= h >> 13
    return (h * 2654435761) & 0xFFFFFFFF


# ===========================================================================
# SKYLINE VIEW - the city from outside
# ===========================================================================

# ---------------------------------------------------------------------------
# Building generation
#
# A building is just a list of strings (its rows, top to bottom) plus a colour.
# ---------------------------------------------------------------------------

def make_building(rng, avail_rows, spec):
    w = rng.randint(*spec["w"])
    h = max(3, int(avail_rows * rng.uniform(*spec["h"])))

    glyphs = rng.sample(WINDOW_GLYPHS, 2)   # each building uses its own 2 glyphs
    col_step = rng.choice([1, 2, 2, 3])     # spacing between window columns
    row_step = rng.choice([1, 1, 2])        # spacing between window rows
    density = rng.uniform(*spec["dens"])    # how many of those slots are lit

    rows = []

    # Optional antenna / mast on the roof.
    if w > 3 and rng.random() < 0.55:
        col = rng.randrange(1, w - 1)
        mast = [rng.choice("^|H+")] + ["|"] * rng.randint(0, 3)
        for ch in mast:
            line = [" "] * w
            line[col] = ch
            rows.append("".join(line))

    rows.append("=" * w)                    # the roof line

    for r in range(1, h):
        line = []
        for c in range(w):
            if c == 0 or c == w - 1:
                line.append("|")            # bright vertical edge of the tower
            elif c % col_step == 0 and r % row_step == 0 and rng.random() < density:
                line.append(rng.choice(glyphs))
            else:
                line.append(" ")            # a dark, unlit window
        rows.append("".join(line))

    return {"w": w, "rows": rows, "color": rng.choice(PALETTES[spec["palette"]])}


# ---------------------------------------------------------------------------
# Chunks
#
# The city is infinite, so we can't generate it all up front. Instead the world
# is cut into fixed-width chunks. Chunk number 7 of layer 1 always gets the same
# random seed, so it always generates the exact same buildings - walk away and
# come back and the city is unchanged, without storing anything.
# ---------------------------------------------------------------------------

_cache = {}


def get_chunk(layer_i, chunk_i, avail_rows):
    key = (layer_i, chunk_i, avail_rows)
    if key not in _cache:
        if len(_cache) > 400:
            _cache.clear()   # walked a long way; the seeds rebuild it identically
        spec = LAYERS[layer_i]
        rng = random.Random(f"city|{layer_i}|{chunk_i}")   # the deterministic seed
        buildings = []
        x = chunk_i * CHUNK_W
        end = x + CHUNK_W
        while x < end:
            b = make_building(rng, avail_rows, spec)
            b["x"] = x
            buildings.append(b)
            x += b["w"] + rng.randint(*spec["gap"])
        _cache[key] = buildings
    return _cache[key]


# ---------------------------------------------------------------------------
# Rendering
#
# We never draw straight to the screen. We fill two grids - one of characters,
# one of colours - back to front, so nearer buildings paint over farther ones.
# Then the whole thing gets blitted in one go, which stops the picture flickering.
# ---------------------------------------------------------------------------

def blit(dst_ch, dst_co, b, sx, ground):
    rows = b["rows"]
    height = len(dst_ch)
    width = len(dst_ch[0])
    top = ground - len(rows) + 1
    for i, line in enumerate(rows):
        y = top + i
        if not (0 <= y < height):
            continue
        for j, ch in enumerate(line):
            if ch == " ":
                continue
            x = sx + j
            if 0 <= x < width:
                dst_ch[y][x] = ch
                dst_co[y][x] = b["color"]


def dawn_glow(col, y, horizon, amount):
    """What the morning sky looks like at this cell, or None for still dark.

    The light comes up from the horizon: the band nearest it goes first and
    goes orange, then peach above it, then a pale blue climbing higher as it
    gets lighter, and the dark at the top last of all. Dithered, so it is a
    gradient and not stripes."""
    up = (horizon - y) / float(max(1, horizon))       # 0 at the horizon, 1 overhead
    reach = amount * 1.25                              # how high the light has got
    if up > reach:
        return None
    strength = 1.0 - up / max(1e-6, reach)
    if _mix(col, y, 2101) % 100 >= 25 + 70 * strength:
        return None
    if up < 0.12 * amount:
        return "=", EMBER                              # the line of the sunrise
    if up < 0.3 * amount:
        return "-", STAR_WARM
    if up < 0.65 * amount:
        return ":", STAR_COLD
    return ".", BAND


def draw_stars(ch, co, cam_x, ground, wet, now, tops):
    """The same night as the street sees, over the water.

    This is where a night actually gets to be a night: from a street you have a
    strip of sky between the rooftops, and here you have all of it. Stars are
    keyed on a slow scroll of the camera rather than a bearing, since there is
    no turning in this view - drifting almost imperceptibly is what tells you
    they are a very long way off."""
    n = night(now)
    cloud = 1.0 if overcast_held() else (0.0 if n["alien"] else cloud_cover(now))
    morning = dawn(now)
    clear = n["clarity"] * (1.0 - cloud) * max(0.0, 1.0 - morning * 1.4)
    if morning > 0.0:
        width = len(ch[0])
        off = int(cam_x * 0.05)
        for sx in range(width):
            for y in range(min(ground, tops[sx])):
                if ch[y][sx] == " ":
                    g = dawn_glow(sx + off, y, ground, morning)
                    if g is not None:
                        ch[y][sx], co[y][sx] = g
            # And the far bank's windows going out as it gets light - the
            # same switching-off the street sees, on buildings the street's
            # renderer never built.
            for y in range(max(0, tops[sx]), ground + 1):
                if (ch[y][sx] not in " |=_-~^:." and _mix(sx + off, y, 2103) % 100
                        < morning * 90):
                    ch[y][sx] = " "
    if clear <= 0.02:
        return
    width = len(ch[0])
    off = int(cam_x * 0.05)
    top = max(1, ground - 3)
    for sx in range(width):
        col = sx + off
        ceiling = min(top, tops[sx])
        band_mid = (0.5 + n["tilt"] * math.sin(col * 0.012 - n["swing"])
                    if n["band"] else None)
        for y in range(ceiling):
            m = _mix(col, y, 71)
            alt = 1.0 - y / float(top)
            rate = STAR_RATE * clear
            if n["alien"]:
                rate += 190.0
            if band_mid is not None:
                near = max(0.0, 1.0 - abs(alt - band_mid) / 0.19)
                rate += BAND_RATE * clear * near
            if (m % 1000) >= rate:
                continue
            glyph, attr = star_look(m, n["warmth"])
            if (band_mid is not None and glyph == "."
                    and abs(alt - band_mid) < 0.14):
                attr = BAND
            if n["alien"]:
                attr = alien_light(now, (m >> 6) & 7)
                if glyph == ".":
                    glyph = "*'+"[(m >> 3) % 3]
            ch[y][sx] = glyph
            co[y][sx] = attr

    if n["alien"]:
        sky = SkyBox(width, top, off)
        draw_sky_beams(ch, co, sky, tops, now, set())
        draw_mother(ch, co, sky, tops, now, set())
        draw_saucers(ch, co, sky, tops, now, set())
        draw_landing_beam(ch, co, sky, tops, now, set())

    # The moon rides the same slow scroll, so it keeps its place among them.
    face = moon_face(n["phase"])
    if face and clear > 0.15:
        bearing, alt = moon_dir(now)
        mx = int(bearing / math.tau * width * 2.6 - off) % (width * 2) - width // 2
        my = int(round((1.0 - alt) * (top - 1)))
        dim = abs(n["phase"] - 0.5) * 2.0 > 0.34
        for k, c in enumerate(face):
            x = mx + k
            if 0 <= x < width and 0 <= my < min(top, tops[x]):
                ch[my][x] = c
                co[my][x] = MOON_DIM if dim else MOON


def draw_flash_sky(ch, co, water, flash):
    """The same lightning that is going off over the street, seen from here:
    the sky goes pale and the whole skyline turns into a shape against it."""
    if flash < 0.05:
        return
    width = len(ch[0])
    for y in range(water):
        row, rowc = ch[y], co[y]
        for x in range(width):
            if row[x] == " " and _mix(x, y, 29) % 100 < flash * 96:
                row[x] = "." if flash < 0.5 else ":"
                rowc[x] = FLASH


def reflect(ch, co, water, now, wet, flash):
    """Mirror the city into the water below the far bank.

    A reflection in ASCII lives or dies on being broken up: it is the same
    glyphs, displaced sideways by a swell that changes with depth and time, and
    thinned out the further down it goes until it is gone. Rain roughens the
    surface, so the harder it comes down the less of the city you can read in
    it."""
    height = len(ch)
    width = len(ch[0])
    chop = int(now * 3.0)
    for y in range(water + 1, height):
        d = y - water                      # how far down into the water
        src = water - d
        if src < 0:
            return
        shift = int(round(2.2 * math.sin(now * 1.3 + d * 0.7)
                          + 1.5 * wet * math.sin(now * 4.1 + d * 1.9)))
        keep = 82 - d * 9 - int(30 * wet)
        if keep <= 0:
            return
        row, rowc = ch[src], co[src]
        for x in range(width):
            sx = x + shift
            if not 0 <= sx < width:
                continue
            glyph = row[sx]
            if glyph == " " or _mix(x, y, 61 + chop) % 100 >= keep:
                continue
            ch[y][x] = glyph
            co[y][x] = rowc[sx] if flash > 0.35 else rowc[sx] & ~curses.A_BOLD


def draw_water(ch, co, water, now, wet):
    """The surface itself: the line of the far bank, and the chop on it."""
    height = len(ch)
    width = len(ch[0])
    for x in range(width):
        ch[water][x] = "~" if _mix(x, 0, 41) % 5 else "-"
        co[water][x] = CURB
    every = max(3, 13 - int(8 * wet))      # rain dimples the whole surface
    chop = int(now * 2.0)
    for y in range(water + 1, height):
        row, rowc = ch[y], co[y]
        for x in range(width):
            if row[x] == " " and _mix(x, y * 3 + chop, 83) % every == 0:
                row[x] = "~"
                rowc[x] = RAIN_FAR if wet > 0.3 else STREET


def draw_skyline_rain(ch, co, cam_x, water, now, wet, flash):
    """Rain across the vista, locked to the world so it drifts past as you walk
    rather than sitting still on the screen."""
    if wet < 0.03:
        return
    height = len(ch)
    width = len(ch[0])
    wind = 3.2 * math.sin(now / 23.0)
    span = height + 6
    base = int(cam_x)
    for salt in (907, 911):
        for wx in range(base - 2, base + width + 2):
            m = _mix(wx, salt, 5)
            if (m & 255) > wet * 170:
                continue
            phase = ((m >> 8) & 255) / 256.0
            y = (now * 26.0 + phase * span) % span - 3.0
            x = wx - base
            for dy in range(2 + ((m >> 17) & 1)):
                yy = int(y) - dy
                xx = x + int(dy * wind * 0.2)
                if not (0 <= yy < height and 0 <= xx < width):
                    continue
                if ch[yy][xx] != " ":
                    continue           # it falls behind the city, not over it
                ch[yy][xx] = "|" if abs(wind) < 1.6 else ("\\" if wind > 0 else "/")
                co[yy][xx] = FLASH if flash > 0.35 else (
                    RAIN if yy > water - 6 else RAIN_FAR)


def draw_skyline_snow(ch, co, cam_x, water, tops, now):
    """Snow across the vista - slow, swaying, locked to the world - and lying
    white along the top of every building on the far bank."""
    cover = snow_cover(now)
    width = len(ch[0])
    if cover > 0.35:
        for x in range(width):
            y = tops[x]
            if 0 <= y < water and ch[y][x] != " ":
                co[y][x] = SNOW
    fall = snowfall(now)
    if fall < 0.03:
        return
    height = len(ch)
    span = height + 4
    base = int(cam_x)
    for wx in range(base - 2, base + width + 2):
        for salt in (913, 919, 929):
            m = _mix(wx, salt, 7)
            if (m & 255) > fall * 120:
                continue
            phase = ((m >> 8) & 255) / 256.0
            y = int((now * 2.2 + phase * span) % span) - 2
            x = wx - base + int(round(1.5 * math.sin(now * 0.7 + phase * 9.0)))
            if 0 <= y < height and 0 <= x < width and ch[y][x] == " ":
                ch[y][x] = "*" if m >> 17 & 3 == 0 else "."
                co[y][x] = SNOW


def draw_skyline_fireworks(ch, co, cam_x, water, tops, now):
    """The show from across the water: the same shells, laid out along the
    far bank on the middle layer's parallax and drawn as rings in screen
    space - and drawn before the reflection, so they lie on the water too."""
    if not night(now)["fireworks"]:
        return
    width = len(ch[0])
    for t0, m in shells(now):
        cx = 6 + ((m >> 12) & 1023) / 1023.0 * (width - 12)
        t = now - t0
        top = max(2, water // 4 + ((m >> 2) & 7) - 3)
        if t < FW_RISE:
            y = int(water - (water - top) * (1.0 - (1.0 - t / FW_RISE) ** 2))
            if 0 <= y < water and 0 <= int(cx) < width:
                ch[y][int(cx)], co[y][int(cx)] = "|", EMBER
            continue
        tt = t - FW_RISE
        r = 9.0 * (1.0 - math.exp(-1.8 * tt)) / 1.8 * 1.6
        fade = 1.0 - tt / FW_LIFE
        tone = (m >> 28) & 7
        attr = NEON[tone % len(NEON)][0 if fade > 0.35 else 1]
        for k in range(22):
            a = k * math.tau / 22.0 + (m & 7)
            x = int(round(cx + math.cos(a) * r * 2.0))
            y = int(round(top + math.sin(a) * r + tt * tt * 0.8))
            if 0 <= x < width and 0 <= y < water and y < tops[x]:
                ch[y][x] = "*" if tt < 0.5 else ("+" if tt < 1.2 else ".")
                co[y][x] = attr


def draw_skyline_el(ch, co, cam_x, ground, tops, now):
    """The elevated from across the water: a dotted line of track running
    across in front of the middle layer, and now and then a train along it -
    a row of lit windows sliding across the city. It moves with that layer's
    parallax, so it sits in the town rather than on the glass."""
    width = len(ch[0])
    y = ground - max(3, int((ground + 1) * 0.12))
    if y < 2:
        return
    off = cam_x * LAYERS[1]["parallax"]
    for x in range(width):
        wx = int(x + off)
        if wx % 3 == 0:
            ch[y][x] = "-"
            co[y][x] = CONCRETE
        if wx % 17 == 0:
            ch[y + 1][x] = "|"
            co[y + 1][x] = CONCRETE
    # A train every so often, one way then the other, taking half a minute to
    # cross and with a quiet spell between.
    period = 48.0
    k = int(now / period)
    t = (now % period) / 30.0
    if t <= 1.0:
        d = 1 if k % 2 == 0 else -1
        head = -30 + t * (width + 60)
        if d < 0:
            head = width + 30 - t * (width + 60)
        for c in range(22):
            x = int(round(head - d * c))
            if 0 <= x < width:
                ch[y - 1][x] = "o" if c % 3 else "|"
                co[y - 1][x] = BULB if c % 3 else CURB


def render_skyline(cam_x, width, height, now):
    """The city from across the water, in whatever weather the street is in.

    Both views share one clock, so the downpour you walked in out of is the
    downpour falling here, and a strike lights them both."""
    wet = rain_intensity(now)
    flash = lightning(now, wet)
    water = max(5, min(height - 4, int(height * 0.58)))
    ground = water - 1                   # the far bank the city stands on
    avail = ground + 1

    ch = [[" "] * width for _ in range(height)]
    co = [[0] * width for _ in range(height)]

    # The city goes up first and the sky goes in around it. Drawn the other way
    # round - stars, then buildings over them - every unlit window is a hole
    # you can see a star through, because blit() leaves blanks alone. The
    # silhouette is what a star has to clear, not the lit parts of it.
    tops = [ground + 1] * width
    for li, spec in enumerate(LAYERS):
        off = cam_x * spec["parallax"]   # nearer layers slide past faster
        first = int(off // CHUNK_W) - 1
        last = int((off + width) // CHUNK_W) + 1
        for ci in range(first, last + 1):
            for b in get_chunk(li, ci, avail):
                sx = int(round(b["x"] - off))
                if sx + b["w"] < 0 or sx >= width:
                    continue
                blit(ch, co, b, sx, ground)
                roof = ground - len(b["rows"]) + 1
                for x in range(max(0, sx), min(width, sx + b["w"])):
                    if roof < tops[x]:
                        tops[x] = roof

    draw_stars(ch, co, cam_x, ground, max(wet, snowfall(now) * 0.8), now, tops)
    draw_skyline_el(ch, co, cam_x, ground, tops, now)

    draw_flash_sky(ch, co, water, flash)
    if flash >= 0.05:
        dens = int(flash * 70)
        for y in range(water):
            row, rowc = ch[y], co[y]
            for x in range(width):
                if row[x] == " " and _mix(x, y, 97) % 100 < dens:
                    row[x] = ":"
                    rowc[x] = FLASH
    draw_skyline_fireworks(ch, co, cam_x, water, tops, now)
    reflect(ch, co, water, now, wet, flash)
    draw_water(ch, co, water, now, wet)
    draw_skyline_rain(ch, co, cam_x, water, now, wet, flash)
    draw_skyline_snow(ch, co, cam_x, water, tops, now)
    return ch, co


# ===========================================================================
# STREET VIEW - the city from inside
# ===========================================================================

# ---------------------------------------------------------------------------
# The street plan
#
# Every question about the layout is answered by a hash of the cell's own
# coordinates, so the city is infinite, identical every time you walk back to
# it, and stored nowhere. The point of the irregularity below is that you
# should be able to get lost in it:
#
#   - avenues sit on a period but vary in width and offset, and roughly one in
#     thirteen is built over entirely, so two blocks merge into a long one
#   - each block may be split by a one-cell alley, and that alley is cut into
#     stretches, so some of them lead through and some are dead ends
#   - the odd cell inside a block is missing altogether: a yard you can stand in
# ---------------------------------------------------------------------------

# --- the river -------------------------------------------------------------
# It runs along i and wanders across j, so it cuts the street grid at an angle
# and no two stretches of bank are alike. Water is the first cell in this city
# that is neither open nor solid: you can see across a river but not walk on
# it, so is_open() (which answers "does light get through") says yes and
# can_stand() has a test of its own.
RIVER_HALF = 3.4       # half the channel, in cells, before the wobble
_river_cache = {}


_centre_cache = {}
_span_cache = {}


def river_centre(i):
    """Where the middle of the channel is, in cells across.

    Cached per column: with the promenade, the fairground, the headland and
    the moat all keyed on where the river is, this was being asked several
    thousand times a frame, three sines each."""
    hit = _centre_cache.get(i)
    if hit is None:
        _evict(_centre_cache, 20000)
        hit = (26.0 * math.sin(i / 55.0)
               + 8.0 * math.sin(i / 23.0 + 1.7)
               + 3.0 * math.sin(i / 11.0 + 0.4))
        _centre_cache[i] = hit
    return hit


def near_river(i, j):
    """Within reach of anything the river puts on its banks. Cheap, and
    the gate in front of every bank test: most of the city is nowhere near."""
    return abs(j - river_centre(i)) < 48.0


_grand_cache = {}


def grand_avenue(i):
    """(first cell, width) of the avenue the big bridge is on, for the stretch
    of river this cell is in. The nearest avenue to a hashed spot that has not
    been built over - so there is always exactly one per stretch."""
    k = i // GRAND_GAP
    hit = _grand_cache.get(k)
    if hit is None:
        want = k * GRAND_GAP + 120 + _mix(k, 0, 1307) % (GRAND_GAP - 240)
        hit = None
        for step in range(0, 20):
            a = want // XP + (step + 1) // 2 * (1 if step % 2 else -1)
            span = road_span(a * XP + 1, XP, 91)
            if span is not None:
                hit = span
                break
        _grand_cache[k] = hit
    return hit


def grand_at(i):
    """Is this column the big bridge's avenue."""
    span = grand_avenue(i)
    return span is not None and span[0] <= i < span[0] + span[1]


def headland_home(i):
    """(li, lj) the centre of the headland at the far end of the big bridge in
    this stretch, in cells, or None."""
    span = grand_avenue(i)
    if span is None:
        return None
    li = span[0] + span[1] // 2
    lo, _ = river_span(li)              # the bay's bank, not the channel's
    return li, int(lo) - 6


def headland_r(i, j, back=1.0):
    """Distance from the headland's centre in units of its own radius: under
    one is rock, up to HEAD_MOAT is the water round it. back stretches the
    shape out behind the point (away from the bay), which is how the water
    reaches further there than at the sides."""
    home = headland_home(i)
    if home is None:
        return 9.0
    li, lj = home
    di, dj = i - li, j - lj
    # The box first: nearly every cell asked about is nowhere near, and the
    # trig below was most of what road_at() cost near the river.
    if abs(di) > HEAD_RI * HEAD_MOAT + 1.0 or abs(dj) > HEAD_RJ * HEAD_BACK + 1.0:
        return 9.0
    a = math.atan2(dj, di)
    wob = 1.0 + 0.10 * math.sin(a * 4.0 + li) + 0.06 * math.sin(a * 7.0 + lj)
    rj = HEAD_RJ * wob * (back if dj < 0 else 1.0)
    return math.sqrt((di / (HEAD_RI * wob)) ** 2 + (dj / rj) ** 2)


def headland_at(i, j):
    return near_river(i, j) and headland_r(i, j) < 1.0 and not river_at(i, j)


def moat_at(i, j):
    """The water round the headland: out to HEAD_MOAT at the sides, and out
    to HEAD_BACK behind the point, so the far town's buildings stand well
    back across the water instead of crowding the rock. Not on the bay side,
    which is the bay's - stretched that way it would flood the near bank."""
    # And never on the near bank: away from the bridge the bay narrows, and
    # the ellipse reached over it and flooded a strip of the other side -
    # under the carnival, as it turned out.
    return (near_river(i, j) and headland_r(i, j) >= 1.0
            and headland_r(i, j, HEAD_BACK / HEAD_MOAT) < HEAD_MOAT
            and j < river_span(i)[1])


def lighthouse_spot(i):
    """Where the lighthouse stands: at the point, in world units."""
    home = headland_home(i)
    if home is None:
        return None
    li, lj = home
    return (li + 0.5) * CELL, (lj - 3.5) * CELL


def river_span(i):
    """(near bank, far bank) in cells, for this step along the channel.

    Widened by the slope of the meander: the band is measured straight across,
    so on a steep bend it is a slanted strip and the channel would pinch to
    half its width exactly where it turns - which is the one place a river gets
    wider, not narrower. And opened out into a bay under the big bridge, which
    wants water worth spanning."""
    hit = _span_cache.get(i)
    if hit is not None:
        return hit
    _evict(_span_cache, 20000)
    mid = river_centre(i)
    slope = (river_centre(i + 1) - river_centre(i - 1)) * 0.5
    half = ((RIVER_HALF + 1.1 * math.sin(i / 17.0 + 2.2))
            * math.sqrt(1.0 + slope * slope))
    span = grand_avenue(i)
    if span is not None:
        d = (i - (span[0] + span[1] * 0.5)) / BAY_REACH
        half *= 1.0 + BAY_WIDEN * math.exp(-d * d)
    hit = (mid - half, mid + half)
    _span_cache[i] = hit
    return hit


def river_at(i, j):
    key = i * 1048576 + j
    hit = _river_cache.get(key)
    if hit is None:
        _evict(_river_cache, 60000)
        lo, hi = river_span(i)
        hit = lo < j < hi
        _river_cache[key] = hit
    return hit


PIER_LEN = 7           # how far one reaches out, at most
PIER_WIDE = 3          # and how many cells across it is


def pier_at(i, j):
    """A pier: a walkable finger of decking out over the water.

    Off the near bank only, a few cells wide, and it stops well short of the
    far side - the point of one is that it ends, and you stand at the end of it
    with the whole city behind you. That view does not otherwise exist from
    inside the street."""
    if not river_at(i, j) or _mix(i // PIER_WIDE, 0, 457) % 19:
        return False
    span = grand_avenue(i)
    if span is not None and abs(i - span[0]) < BAY_REACH * 2:
        return False                    # the bay is the bridge's
    lo, hi = river_span(i)
    # Never more than half way over. The channel narrows to under five cells on
    # some stretches, and a fixed seven-cell pier there quietly spans it - you
    # would have built a footbridge and called it a pier.
    return lo < j < lo + min(PIER_LEN, (hi - lo) * 0.5)


def deck_at(i, j):
    """Anything over the water you can put a foot on."""
    return bridge_at(i, j) or pier_at(i, j) or fair_pier_at(i, j)


BRIDGE_ODDS = 4        # one avenue in this many gets a crossing


def bridge_at(i, j):
    """A crossing: where an avenue running across the river meets the water.

    Not every avenue - one in four. Every avenue would be a crossing every
    forty-five units, and a river you can step over anywhere is a boardwalk
    with a puddle under it. At one in four you walk the bank to find one, which
    is what makes a bridge worth having.

    A footbridge: railings, warm lamps, a string of lights between them."""
    if not (river_at(i, j) and _is_road(i, XP, 91)):
        return False
    if grand_at(i):
        return True
    # The big bridge is the only way onto the headland: no ordinary crossing
    # anywhere the rock and its water reach along the far bank.
    span = grand_avenue(i)
    reach = HEAD_RI * HEAD_MOAT + 2
    if span is not None and abs(i - (span[0] + span[1] // 2)) <= reach:
        return False
    return _mix(i // XP, 0, 719) % BRIDGE_ODDS == 0


PARK_ODDS = 26         # one city block in this many is a car park
PARK_DISTRICTS = ("downtown", "market", "docks", "old town", "residential")
PARK_BAY = 2.6         # a parking bay's width along the row
BAY_ROW = 16.0         # bays, aisle, bays: one double row, in world units along z
LAMP_GAP = 13.0        # between the sodium lamps down an aisle
_car_park_cache = {}


def car_park_block(bi, bj):
    """Is the city block (bi, bj) a car park."""
    if _mix(bi, bj, 1951) % PARK_ODDS:
        return False
    ci, cj = bi * XP + XP // 2, bj * ZP + ZP // 2
    return DISTRICTS[district_at(ci, cj)]["name"] in PARK_DISTRICTS


def car_park_at(i, j):
    """Is this cell part of a car park: in a car-park block, and not the
    street round it, the river, or anything else that claims the ground."""
    key = i * 1048576 + j
    hit = _car_park_cache.get(key)
    if hit is None:
        _evict(_car_park_cache, 40000)
        hit = (car_park_block(i // XP, j // ZP)
               and not _is_road(i, XP, 91) and not _is_road(j, ZP, 137)
               and not woods_at(i, j) and not water_at(i, j)
               and not (near_river(i, j) and (fair_at(i, j) or prom_at(i, j)
                                              or headland_at(i, j))))
        _car_park_cache[key] = hit
    return hit


def bay_of(x, z):
    """(slot along the row, row, how far into the row) for a point on the
    asphalt: rows of bays BAY_ROW apart with an aisle down the middle."""
    k, along = divmod(z, BAY_ROW)
    return int(math.floor(x / PARK_BAY)), int(k), along


def tunnel_run(i, j):
    """(kind, first j, last j) of the tunnel this avenue cell is in, or None.

    Short ones sit in the middle of a block, clear of the cross streets at
    either end. Long ones only go where the next cross street was built over,
    so the avenue runs a long way with nothing crossing it - a tunnel with a
    side street opening off it halfway is not a tunnel."""
    key = i * 1048576 + j
    hit = _tunnel_cache.get(key, 0)
    if hit != 0:
        return hit
    _evict(_tunnel_cache, 40000)
    hit = None
    span = road_span(i, XP, 91)
    if (span is not None and not woods_at(i, j) and not el_at(i) and not grand_at(i)
            and not hwy_at(i)):
        a = span[0]
        b = j // ZP
        lng = None
        for bb in (b, b - 1):
            if _mix(a, bb, 2203) % LONG_ODDS == 0:
                # From the middle of this block, under the built-over cross
                # street, to the middle of the next - stopping short of the
                # cross street after it.
                j0, j1 = bb * ZP + 5, (bb + 1) * ZP + 7
                if (j0 <= j <= j1 and all(not _is_road(k, ZP, 137)
                                           for k in range(j0, j1 + 1))):
                    lng = ("long", j0, j1)
        if lng is not None:
            hit = lng
        elif _mix(a, b, 2201) % SHORT_ODDS == 0:
            j0, j1 = b * ZP + 5, b * ZP + 6
            if j0 <= j <= j1 and not any(_is_road(k, ZP, 137)
                                         for k in range(j0 - 1, j1 + 2)):
                hit = ("short", j0, j1)
        if hit is not None and any(water_at(i, k) for k in range(hit[1], hit[2] + 1)):
            hit = None
    _tunnel_cache[key] = hit
    return hit


def tunnel_at(i, j):
    return tunnel_run(i, j) is not None


def near_tunnels(v, reach):
    """(x0, x1, z0, z1, kind) for each tunnel in reach: the avenue's edges and
    the two mouths, in world units."""
    out = []
    seen = set()
    n = int(reach / CELL) + 1
    ci = int(v.x / CELL + BIG) - BIG
    cj = int(v.z / CELL + BIG) - BIG
    for i in range(ci - n, ci + n + 1):
        span = road_span(i, XP, 91)
        if span is None or span[0] != i:
            continue
        for j in range(cj - n, cj + n + 1):
            run = tunnel_run(i, j)
            if run is None or (i, run[1]) in seen:
                continue
            seen.add((i, run[1]))
            out.append((span[0] * CELL, (span[0] + span[1]) * CELL,
                        run[1] * CELL, (run[2] + 1) * CELL, run[0]))
    return out


def shore_j(i):
    """The first row of dry land on the near bank in column i. A row is
    river while it is under hi, so this is hi rounded up - not int(hi) + 1,
    which is the same thing for a positive hi and one row too far for a
    negative one: in every stretch where the bank's row was below zero that
    left a building a cell wide between the water and the promenade, or the
    fair."""
    return math.ceil(river_span(i)[1])


def prom_at(i, j):
    """The promenade: open bank on the near side, two cells deep, along two
    stretches in three."""
    if not near_river(i, j) or _mix(i // PROM_STRETCH, 0, 1401) % 3 == 0:
        return False
    s = shore_j(i)
    return s <= j < s + PROM_DEEP


_carnival_cache = {}


def carnival_col(i):
    """The first cell along the river of the carnival in this stretch.

    In the stretch with the big bridge in it, the carnival stands on the
    near bank across the bay from the headland, wherever along there it
    comes closest to the rock (`_by_the_headland()`) - so the bridge, the
    wheel and the lighthouse are in the one view, and the wheel is near
    enough from the rock to make out. Worked out once a stretch: fair_at()
    asks for it every cell."""
    k = i // CARNIVAL_GAP
    hit = _carnival_cache.get(k)
    if hit is not None:
        return hit
    _evict(_carnival_cache, 4000)
    lo = k * CARNIVAL_GAP
    span = grand_avenue(lo)
    hit = None
    if span is not None:
        # The one by the big bridge belongs to the bridge's whole stretch of
        # river, not to one of these: it is this stretch's carnival if the
        # bridge is in here, or if it starts in here, and replaces the one
        # the hash would have put here either way.
        c = _by_the_headland(span)
        if c // CARNIVAL_GAP == k or span[0] // CARNIVAL_GAP == k:
            hit = c
    if hit is None:
        hit = lo + 30 + _mix(k, 0, 1301) % (CARNIVAL_GAP - 70)
    _carnival_cache[k] = hit
    return hit


_headland_fair = {}         # by the bridge: its carnival's first column


def _by_the_headland(span):
    """Of the places along the near bank beside the big bridge, the one that
    puts the wheel nearest the headland's rock. Kept clear of the bridge and
    of where the ferry docks. Measured: standing at a
    fixed distance west of the bridge, the wheel was anywhere from 64 to 214
    units from the rock, because the river meanders away from the headland
    in some stretches; chosen like this it is 60 to 110 in most. It may start
    in the stretch next to the bridge's, which carnival_col() allows for."""
    hit = _headland_fair.get(span[0])
    if hit is not None:
        return hit
    li, lj = headland_home(span[0])
    rock = [((a + 0.5) * CELL, (b + 0.5) * CELL)
            for a in range(li - int(HEAD_RI) - 4, li + int(HEAD_RI) + 5)
            for b in range(lj - int(HEAD_RJ) - 4, lj + int(HEAD_RJ) + 6)
            if headland_at(a, b)]
    ferry = span[0] + span[1] + 9
    best = None
    for c in range(span[0] - 45, span[0] + 45):
        cols = range(c, c + FAIR_LONG)
        if any(span[0] - CARNIVAL_BESIDE <= a < span[0] + span[1] + CARNIVAL_BESIDE
               or abs(a - ferry) <= 2 for a in cols):
            continue
        wx = (c + 2.5) * CELL
        wz = (pier_tip(c, force=True, k=2.5) + 1.8) * CELL
        d = min((x - wx) ** 2 + (z - wz) ** 2 for x, z in rock) if rock else 0.0
        if best is None or d < best[0]:
            best = (d, c)
    hit = best[1] if best is not None else span[0] - CARNIVAL_BESIDE - FAIR_LONG
    _evict(_headland_fair, 400)
    _headland_fair[span[0]] = hit
    return hit


def carnival_over(i, margin=0):
    """The first column of the carnival standing over column i (give or take
    margin), or None. A carnival starts inside its own stretch but may run on
    into the next - the one by the big bridge goes wherever is nearest the
    headland - so the stretch before is asked as well."""
    for c in (carnival_col(i), carnival_col(i - FAIR_LONG - margin)):
        if c - margin <= i < c + FAIR_LONG + margin:
            return c
    return None


def fair_at(i, j):
    """The fairground: a strip of open bank on the near side, the depth of
    a few cells, that nothing is built on."""
    if carnival_over(i) is None:
        return False
    s = shore_j(i)
    return s <= j < s + FAIR_DEEP


def bank_z(i):
    """The near bank's edge in this column, in world units: where the
    fairground's ground starts."""
    return shore_j(i) * CELL


def carnival_spots(c):
    """Where things stand, given the carnival's first column: the wheel, the
    carousel, and the stalls, in world units, and the middle column's bank.

    Each one stands back from the bank of its own column. They used to be laid
    out from the middle column's, and that held only while the bank ran
    straight: it slopes as much as half a cell a column along the meander and
    more beside the bay, which over the eleven columns of a fair is five
    cells, and put the stalls at one end in the river."""
    tip = pier_tip(c)
    if tip is not None:
        # Out on the pier: laid out from its far end, the wheel out at the
        # tip the way the big one on a pleasure pier is, the stalls back
        # towards the shore.
        def at(k, d):
            return (c + k) * CELL, (pier_tip(c, k=k) + d) * CELL
        stalls = [at(k, 3.8) for k in (5.5, 7.0, 8.5, 10.0)]
        return at(2.5, 1.8), at(7.5, 2.0), stalls, bank_z(c + FAIR_LONG // 2)

    def at(k, back):
        return (c + k) * CELL, bank_z(int(c + k + BIG) - BIG) + back * CELL
    stalls = [at(k, 3.6) for k in (5.5, 7.0, 8.5, 10.0)]
    return at(2.5, 2.2), at(7.0, 1.6), stalls, bank_z(c + FAIR_LONG // 2)


def by_the_bridge(c):
    """Is this the carnival beside a big bridge, the one on the pier."""
    span = grand_avenue(c)
    return span is not None and _by_the_headland(span) == c


_pier_cache = {}


def pier_tip(c, force=False, k=None):
    """The row the fair's pier reaches out to - in the column k cells along
    it, or None for a carnival on the bank. FAIR_PIER cells out from the bank
    in each column, and pulled back so it is never more than FAIR_PIER_MAX of
    the way over, or in a narrow stretch it would be a bridge to the
    headland. Per column rather than one straight end: the narrowest column
    held a straight end to one or two cells across the whole fair. force asks
    for the one a carnival here would have, while it is still being decided
    where to put it."""
    if not force and not by_the_bridge(c):
        return None
    hit = _pier_cache.get(c)
    if hit is None:
        _evict(_pier_cache, 400)
        hit = []
        for i in range(c, c + FAIR_LONG):
            lo, hi = river_span(i)
            hit.append(max(shore_j(i) - FAIR_PIER,
                           math.floor(lo + (hi - lo) * (1.0 - FAIR_PIER_MAX)) + 1))
        _pier_cache[c] = hit
    if k is None:
        return min(hit)
    return hit[max(0, min(FAIR_LONG - 1, int(k)))]


def fair_pier_at(i, j):
    """The deck of the fair's pier: out over the water from the bank to its
    end, across the width of the fair. Walkable, and planked by the ground
    pass like any other pier."""
    if not river_at(i, j):
        return False
    c = carnival_over(i)
    if c is None:
        return False
    tip = pier_tip(c)
    return tip is not None and j >= pier_tip(c, k=i - c)


def seafront_cap(i, j):
    """How tall a building may be behind the fair's pier, or None. Low at the
    water and rising inland, so from the headland the town stays under the
    line over the top of the wheel and the wheel stands against the sky: with
    towers right behind it, its lights were lost in their windows."""
    c = carnival_over(i, 10)
    if c is None or pier_tip(c) is None:
        return None
    back = j - shore_j(i) + 1
    if not 0 < back <= SEAFRONT_DEEP:
        return None
    return 6.0 + 1.5 * back


def striker_spot(c):
    """The strength tester: at the west end of the row the stalls are in."""
    tip = pier_tip(c)
    if tip is not None:
        return (c + 0.8) * CELL, (pier_tip(c, k=0.8) + 3.8) * CELL
    return (c + 0.8) * CELL, bank_z(c) + 3.6 * CELL


def claw_spot(c):
    """The claw machine: in the row with the stalls, before the first of them."""
    tip = pier_tip(c)
    if tip is not None:
        return (c + 4.2) * CELL, (pier_tip(c, k=4.2) + 3.8) * CELL
    return (c + 4.2) * CELL, bank_z(c + 4) + 3.6 * CELL


_open_cache = {}
_road_cache = {}


def _evict(cache, limit):
    """Drop the oldest third once a cache gets big.

    Wiping the lot instead means the next frame has to rebuild every cell in
    sight at once, which on a long walk is a visible hitch. Dicts keep their
    insertion order, and while you are moving the oldest entries are the ones
    behind you, so this throws away roughly what you have walked past."""
    if len(cache) <= limit:
        return
    for k in list(cache)[:limit // 3]:
        del cache[k]


def _built_over(k, salt):
    return _mix(k, 0, salt) % 13 == 0


def road_span(i, period, salt):
    """(first cell, width in cells) of the road cell i belongs to, or None.

    Knowing where a road starts and how wide it is - not merely that a cell is
    one - is what lets the ground pass find the middle of it to paint a line
    down."""
    k, r = divmod(i, period)
    # An avenue may be built over, but never two in a row. Left to chance they
    # clump: three in a row leaves a 180-unit stretch with no cross street
    # anywhere in it, and that stops reading as a long block and starts reading
    # as the city having quietly changed into somewhere else. One at a time
    # still merges two blocks, which is the point.
    if _built_over(k, salt) and not _built_over(k - 1, salt):
        return None
    m = _mix(k, 0, salt)
    off = (m >> 9) % 2
    wide = 2 + ((m >> 4) & 1)
    return (k * period + off, wide) if off <= r < off + wide else None


def _is_road(i, period, salt):
    key = i * 31 + salt
    hit = _road_cache.get(key)
    if hit is None:
        _evict(_road_cache, 8000)
        hit = road_span(i, period, salt) is not None
        _road_cache[key] = hit
    return hit


def _is_alley(i, j, period, salt, run_salt):
    k, r = divmod(i, period)
    m = _mix(k, 0, salt)
    if (m >> 20) % 3 == 0 or r != 4 + ((m >> 17) % 3):
        return False
    # Broken into stretches: one in five is missing, which is what turns an
    # alley into a dead end you have to back out of.
    return _mix(i, j // 6, run_salt) % 5 != 0


_yoko_cache = {}


_woods_cache = {}


def woods_home(i, j):
    """Centre (ci, cj) of the woods in the tile this cell belongs to."""
    ti, tj = i // WOODS_TILE, j // WOODS_TILE
    m = _mix(ti, tj, 1201)
    return (ti * WOODS_TILE + WOODS_TILE // 2 + (m & 63) - 32,
            tj * WOODS_TILE + WOODS_TILE // 2 + ((m >> 6) & 63) - 32)


def woods_depth(i, j):
    """How far inside the woods this cell is, in cells; negative outside.

    The edge wanders rather than running straight, so the wood is not a
    rectangle with corners on it. Kept to a gentle slope - under one cell per
    cell - so the ring trail that follows the edge stays joined up."""
    key = i * 1048576 + j
    hit = _woods_cache.get(key)
    if hit is None:
        _evict(_woods_cache, 60000)
        ci, cj = woods_home(i, j)
        di, dj = i - ci, j - cj
        ei = (WOODS_HALF_I + 3.0 * math.sin(dj / 9.0 + ci)
              + 2.0 * math.sin(dj / 4.0 + 1.0))
        ej = (WOODS_HALF_J + 3.0 * math.sin(di / 9.0 + cj)
              + 2.0 * math.sin(di / 4.0 + 2.0))
        hit = min(ei - abs(di), ej - abs(dj))
        _woods_cache[key] = hit
    return hit


def woods_at(i, j):
    """Is this cell in the woods - the big one, not a park."""
    return woods_depth(i, j) > 0.0


def hollow_centre(ci, cj):
    """The hollow is near the middle of the woods, never exactly at it."""
    m = _mix(ci, cj, 1207)
    return ci + (m & 15) - 8, cj + ((m >> 4) & 7) - 4


def hollow_at(i, j):
    ci, cj = woods_home(i, j)
    hi, hj = hollow_centre(ci, cj)
    di, dj = i - hi, j - hj
    wob = 1.0 + 0.12 * math.sin(math.atan2(dj, di) * 3.0 + hi)
    return (di / (HOLLOW_RI * wob)) ** 2 + (dj / (HOLLOW_RJ * wob)) ** 2 < 1.0


def trail_at(i, j):
    """The paths through the woods, two or three cells wide and wandering.

    Three the long way, two across, a ring just inside the edge that the
    others run into, and one straight path down into the hollow. Every road
    that meets the edge gets a gate through to the ring, so the wood is always
    enterable and you can always get back out - but off the trails the trees
    are thick enough that you will not go far before turning round."""
    depth = woods_depth(i, j)
    if depth <= 0.0:
        return False
    if depth < 3.5:
        if depth > 1.0:
            return True                              # the ring
        return _is_road(i, XP, 91) or _is_road(j, ZP, 137)   # a gate
    ci, cj = woods_home(i, j)
    di, dj = i - ci, j - cj
    for n, off in enumerate((-22, 0, 24)):
        m = _mix(ci, n, 1213)
        f = (off + 6.0 * math.sin(di / 23.0 + (m & 7))
             + 3.0 * math.sin(di / 8.0 + ((m >> 3) & 7)))
        if abs(dj - f) < 1.5:
            return True
    for n, off in enumerate((-30, 28)):
        m = _mix(cj, n, 1217)
        f = (off + 5.0 * math.sin(dj / 17.0 + (m & 7))
             + 2.5 * math.sin(dj / 6.0 + ((m >> 3) & 7)))
        if abs(di - f) < 1.5:
            return True
    hi, hj = hollow_centre(ci, cj)
    if abs(i - hi) <= 1 and hj - HOLLOW_RJ - 14 <= j <= hj:
        return True
    # And a path round the lake, which any trail that reaches the water
    # joins; a trail that simply ran into the lake would end in it.
    return 0.0 <= lake_dist(i, j) < 2.2


def lake_centre(ci, cj):
    """The lake lies off towards one end of the woods, away from the hollow -
    they are two different places to end up, and between them is where you
    get lost."""
    m = _mix(ci, cj, 1231)
    side = 1 if (m & 1) else -1
    return ci + side * (30 + ((m >> 1) & 7)), cj - 12 + ((m >> 4) & 7)


def lake_dist(i, j):
    """How far outside the lake's edge this cell is, in cells - negative in
    the water. The shore wanders the way the woods' own edge does."""
    ci, cj = woods_home(i, j)
    li, lj = lake_centre(ci, cj)
    di, dj = i - li, j - lj
    a = math.atan2(dj, di)
    wob = 1.0 + 0.16 * math.sin(a * 3.0 + li) + 0.08 * math.sin(a * 5.0 + lj)
    r = math.sqrt((di / (LAKE_RI * wob)) ** 2 + (dj / (LAKE_RJ * wob)) ** 2)
    return (r - 1.0) * LAKE_RJ * wob


def lake_at(i, j):
    return woods_depth(i, j) > 4.0 and lake_dist(i, j) < 0.0


def water_at(i, j):
    """Anything you can see across but not stand on."""
    return river_at(i, j) or moat_at(i, j) or lake_at(i, j)


def nearest_hollow(x, z):
    """(hx, hz, hi, hj) of the hollow nearest this point, in world units and
    cells. There is one woods a tile, so it is one of nine."""
    ci = int(x / CELL + BIG) - BIG
    cj = int(z / CELL + BIG) - BIG
    best = None
    for a in (-1, 0, 1):
        for b in (-1, 0, 1):
            wi, wj = woods_home(ci + a * WOODS_TILE, cj + b * WOODS_TILE)
            hi, hj = hollow_centre(wi, wj)
            hx, hz = (hi + 0.5) * CELL, (hj + 0.5) * CELL
            d2 = (hx - x) ** 2 + (hz - z) ** 2
            if best is None or d2 < best[0]:
                best = (d2, hx, hz, hi, hj)
    return best[1:]


_forced_rave = None     # when one was called up, rather than being due


def force_rave(now):
    global _forced_rave
    _forced_rave = now


def rave_window(now):
    """(start, length) of the rave that is on, or None. Same shape as a storm,
    on a longer slot and longer odds - about one hour in seven has one."""
    if _forced_rave is not None and _forced_rave <= now < _forced_rave + RAVE_LONG:
        return _forced_rave, RAVE_LONG
    if night(now)["alien"]:
        # The rig in the trees knew. Whoever carried a sound system into the
        # woods on the one night in forty the sky has something in it was not
        # guessing: on that night it is on from dusk to dawn.
        k = int((now + _night_skip) / NIGHT_LENGTH)
        return k * NIGHT_LENGTH - _night_skip, NIGHT_LENGTH
    k = int(now / RAVE_SLOT)
    for kk in (k, k - 1):
        m = _mix(kk, 0, 829)
        if m % RAVE_ODDS:
            continue
        start = kk * RAVE_SLOT + ((m >> 8) & 1023) / 1023.0 * RAVE_SLOT * 0.4
        length = RAVE_SHORT + ((m >> 19) & 255) / 255.0 * (RAVE_LONG - RAVE_SHORT)
        if start <= now < start + length:
            return start, length
    return None


def rave_light(now, phase, tone):
    """What the rig is doing this instant, or None between hits. Same idea as
    club_light() but faster and less forgiving - no colour wash between the
    kicks, just dark."""
    sync = city_sync(now)
    if sync is not None:                # and on that night it is on the sky's beat
        if sync == "flash":
            return FLASH
        if sync == "off":
            return None
        return rave_tone(tone, int(now * ALIEN_BPM / 60.0))
    t = now * RAVE_BPM / 60.0 + phase
    beat = t % 1.0
    if (int(t) // 4) % 16 == 15 and int(t * 8) % 2:
        return FLASH                    # the strobe run at the end of a phrase
    if beat < 0.10:
        return FLASH
    if beat < 0.26:
        return rave_tone(tone, int(t / 4))
    return None


def rave_tone(tone, bar):
    """The rig's colour this bar, from its own palette - purples and greens,
    never the whole neon rainbow, which is the club's."""
    k = RAVE_TONES[(int(tone * 4) + bar) % len(RAVE_TONES)]
    return NEON[min(len(NEON) - 1, k)][0]


def yokocho_at(i, j):
    """Is this alley cell a lit one.

    Keyed on the same run the alley itself is cut into, so a yokocho is a whole
    stretch of lane rather than a few cells of one - you turn into it and it
    stays lit until it ends."""
    key = i * 1048576 + j
    hit = _yoko_cache.get(key)
    if hit is None:
        _evict(_yoko_cache, 40000)
        hit = False
        if is_open(i, j) and not road_at(i, j) and not woods_at(i, j):
            if _is_alley(i, j, XP, 91, 211) and _mix(i, j // 6, 331) % 4 == 0:
                hit = True
            elif _is_alley(j, i, ZP, 137, 223) and _mix(j, i // 6, 337) % 4 == 0:
                hit = True
        _yoko_cache[key] = hit
    return hit


def face_kind(i, j):
    """What the open cell in front of a facade is: a street, a lit lane, or a
    dark one. Passed around instead of a bare "is it lit" flag, because a
    yokocho is lit but is not a street and should not look like one."""
    if road_at(i, j):
        return "road"
    return "yokocho" if yokocho_at(i, j) else None


def road_at(i, j):
    """Is this cell part of a proper street - the kind that gets neon?

    No street runs through the woods: the avenue stops at the trees and a gate
    in the ring trail is what continues it."""
    if woods_at(i, j) or headland_at(i, j):
        return False
    return _is_road(i, XP, 91) or _is_road(j, ZP, 137)


_landmark_cache = {}


def landmark_of(ti, tj):
    """The landmark in tile (ti, tj), worked out once, or None: a city block
    away from the river, the woods and the parks, wide enough to take it -
    the footprint is the block's own, held against its south and west
    streets so the lobby fronts a road, and no more than LANDMARK_MAX across.
    Pure in its coordinates: road_span and friends never ask is_open()."""
    key = (ti, tj)
    if key in _landmark_cache:
        return _landmark_cache[key]
    hit = None
    for n in range(10):
        m = _mix(ti * 977 + n, tj, 2601)
        ci = ti * LANDMARK_TILE + 40 + m % (LANDMARK_TILE - 80)
        cj = tj * LANDMARK_TILE + 40 + (m >> 12) % (LANDMARK_TILE - 80)
        if (abs(cj - river_centre(ci)) < 70 or _is_road(ci, XP, 91)
                or _is_road(cj, ZP, 137)):
            continue
        i_lo, i_hi, j_lo, j_hi = ci, ci, cj, cj
        while not _is_road(i_lo - 1, XP, 91) and ci - i_lo < 20:
            i_lo -= 1
        while not _is_road(i_hi + 1, XP, 91) and i_hi - ci < 20:
            i_hi += 1
        while not _is_road(j_lo - 1, ZP, 137) and cj - j_lo < 20:
            j_lo -= 1
        while not _is_road(j_hi + 1, ZP, 137) and j_hi - cj < 20:
            j_hi += 1
        i1 = min(i_hi, i_lo + LANDMARK_MAX - 1)
        j0 = max(j_lo, j_hi - LANDMARK_MAX + 1)
        if i1 - i_lo < 5 or j_hi - j0 < 5:
            continue
        cells = [(a, b) for a in range(i_lo, i1 + 1) for b in range(j0, j_hi + 1)]
        if any(woods_at(a, b) or DISTRICTS[district_at(a, b)]["park"]
               or car_park_at(a, b) or near_river(a, b) for a, b in cells):
            continue
        hit = {"i0": i_lo, "i1": i1, "j0": j0, "j1": j_hi,
               "name": LANDMARK_NAMES[m % len(LANDMARK_NAMES)],
               "lobby": ((i_lo + i1) // 2, j_hi), "seed": m % 9973}
        break
    if len(_landmark_cache) > 400:
        _landmark_cache.clear()
    _landmark_cache[key] = hit
    return hit


def landmark_at(i, j):
    """The landmark this cell is part of, or None."""
    lm = landmark_of(i // LANDMARK_TILE, j // LANDMARK_TILE)
    if lm is None or not (lm["i0"] <= i <= lm["i1"] and lm["j0"] <= j <= lm["j1"]):
        return None
    return lm


def landmark_ring(lm, i, j):
    """How far in from the landmark's edge a cell is: 0 is the base."""
    return min(i - lm["i0"], lm["i1"] - i, j - lm["j0"], lm["j1"] - j)


def party_roof(lm):
    """(x0, z0, x1, z1) of the tower's roof, where the party is."""
    return ((lm["i0"] + 1) * CELL, (lm["j0"] + 1) * CELL,
            lm["i1"] * CELL, lm["j1"] * CELL)


def near_landmarks(v, reach):
    ti, tj = int(v.x // (LANDMARK_TILE * CELL)), int(v.z // (LANDMARK_TILE * CELL))
    for a in (ti - 1, ti, ti + 1):
        for b in (tj - 1, tj, tj + 1):
            lm = landmark_of(a, b)
            if lm is None:
                continue
            x0, z0, x1, z1 = party_roof(lm)
            dx, dz = (x0 + x1) * 0.5 - v.x, (z0 + z1) * 0.5 - v.z
            if dx * dx + dz * dz < reach * reach:
                yield lm


def is_open(i, j):
    key = i * 1048576 + j
    hit = _open_cache.get(key)
    if hit is None:
        _evict(_open_cache, 60000)
        if water_at(i, j):
            hit = True          # you can see across it; standing is elsewhere
        elif landmark_at(i, j) is not None:
            hit = False         # the landmark: solid, a whole block of it
        elif (fair_at(i, j) or headland_at(i, j) or prom_at(i, j)
              or car_park_at(i, j)):
            hit = True          # fairground, headland, promenade: nothing built
        elif woods_at(i, j):
            # Trails, the hollow, and otherwise trees thick enough that the
            # open cells do not join up: off a trail you get a few cells in and
            # have to turn round, which is what being lost in a wood is.
            hit = (trail_at(i, j) or hollow_at(i, j)
                   or _mix(i, j, 89) % 100 < WOODS_OPEN)
        elif DISTRICTS[district_at(i, j)]["park"]:
            # Roads still cross a park; everything else is grass, but for the
            # clumps of trees - which are solid, so the renderer and the
            # collision both already know what to do with them. The wood
            # thickens towards the middle: a third of the core is trees against
            # a quarter of the lawn round the edges, which is what gives the
            # interior somewhere properly hidden. Not much past a third, or the
            # clumps join up and the middle of every park is a wall - open
            # cells stop percolating somewhere around 60%.
            hit = road_at(i, j) or _mix(i, j, 83) % (3 if park_core(i, j)
                                                     else 4) != 0
        else:
            hit = (road_at(i, j)
                   or _is_alley(i, j, XP, 91, 211) or _is_alley(j, i, ZP, 137, 223)
                   or _mix(i, j, 57) % 47 == 0)
        _open_cache[key] = hit
    return hit


_core_cache = {}


def park_core(i, j):
    """Deep inside a park, rather than out on its edge.

    Sampled at a handful of offsets instead of measured properly: the distance
    to the nearest edge would be a flood fill, and this is asked for every cell
    the raycaster steps through. Cardinals at five cells and diagonals at four
    is enough to tell the middle of a park from its lawn."""
    key = i * 1048576 + j
    hit = _core_cache.get(key)
    if hit is None:
        _evict(_core_cache, 40000)
        hit = all(DISTRICTS[district_at(i + a, j + b)]["park"]
                  for a, b in ((0, 0), (-5, 0), (5, 0), (0, -5), (0, 5),
                               (-4, -4), (4, 4), (-4, 4), (4, -4)))
        _core_cache[key] = hit
    return hit


def open_at(x, z):
    return is_open(int(x / CELL + BIG) - BIG, int(z / CELL + BIG) - BIG)


def dry_at(x, z):
    """Open, and not water - which is what your feet care about."""
    i = int(x / CELL + BIG) - BIG
    j = int(z / CELL + BIG) - BIG
    if not is_open(i, j):
        return False
    return not water_at(i, j) or deck_at(i, j)


def can_stand(x, z):
    return (dry_at(x - BODY, z) and dry_at(x + BODY, z)
            and dry_at(x, z - BODY) and dry_at(x, z + BODY))


# ---------------------------------------------------------------------------
# What stands on a cell
#
# Each solid cell is one narrow building. Heights are drawn around a base that
# belongs to the whole block, so a block has a skyline of its own rather than
# every building being independently random.
#
# All four faces are generated whether or not anything fronts them, so what a
# building looks like never depends on what happens to be next to it. Which of
# those decorations actually get drawn does: a face on an avenue gets the neon,
# a face on an alley gets a bare bulb and a fire escape.
# ---------------------------------------------------------------------------

FACES = ((-1, 0), (1, 0), (0, -1), (0, 1))     # outward normal of face 0..3

_lots = {}


YOKOCHO_TUBES = {"neon": (0, 3, 4, 7)}      # red and amber, like the lanterns


def _tube(rng, d):
    """A neon colour this district is willing to use, stored as the same 0..1
    tone every sign already carries so nothing downstream has to change."""
    picks = d["neon"]
    idx = rng.randrange(8) if picks is None else rng.choice(picks)
    return (idx + 0.5) / 8.0


def make_face(rng, height, d, kind):
    floors = max(1, int(height / FLOOR_H))
    face = {"flat": None, "hung": None, "smoker": None,
            "bulb": None, "escape": False}

    # A yokocho is signed like a yokocho whatever part of town it runs behind.
    yoko = kind == "yokocho"
    words = (JP_SIGNS if (WIDE_OK and yoko)
             else CJK_SIGNS if (WIDE_OK and d["cjk"] and not yoko)
             else SIGN_WORDS)

    # Flat signs stay Latin whatever the district. They are painted along the
    # wall and squashed by perspective to one column a letter, and the facade
    # path writes single cells with no way to reserve the column a wide glyph
    # spills into - it would corrupt the row. The vertical hung signs are where
    # the Chinese and Japanese go, and they are the ones you can read anyway.
    if floors >= 3 and rng.random() < (0.7 if yoko else d["flat"]):
        text = rng.choice(SIGN_WORDS)
        flicker = rng.random() < 0.25
        face["flat"] = {
            "text": text,
            "floor": rng.randrange(1, min(floors, 6)),
            "step": CELL / (len(text) + 1.0),
            "tone": _tube(rng, d),
            "flicker": flicker,
            "dead": frozenset(rng.sample(range(len(text)), rng.randint(0, 1)))
            if flicker else frozenset(),
            "period": rng.uniform(1.7, 5.0),
            "phase": rng.uniform(0.0, 5.0),
        }

    # Every value is drawn whether or not the sign ends up existing, so that
    # deciding it will not fit cannot shift what the rest of the building rolls.
    want = rng.random() < (0.8 if yoko else d["hung"])
    text = rng.choice(words)
    flicker = rng.random() < 0.3
    u = rng.uniform(1.2, CELL - 1.2)
    tone = _tube(rng, d)
    dead = (frozenset(rng.sample(range(len(text)), rng.randint(0, 1)))
            if flicker else frozenset())
    period = rng.uniform(1.7, 5.0)
    phase = rng.uniform(0.0, 5.0)
    lift = rng.random()
    # A sign hangs from its top and reads downwards, so where it ends is what
    # matters and constraining the top alone guarantees nothing: a quarter of
    # them used to finish below eye level and one in thirty ran into the
    # pavement. Hang it high enough that the last letter clears a head, and if
    # the building is too short for the whole word, it does not get one.
    low = SIGN_CLEAR + SIGN_STEP * (len(text) - 1)
    if want and low <= height - 0.5:
        # And no higher than a storey or two over that. Hanging it anywhere in
        # the building's height puts the signs on the tall ones up in the sky,
        # where nobody in the street is looking.
        high = min(height - 0.5, low + 5.0)
        face["hung"] = {"text": text, "u": u, "out": SIGN_OUT,
                        "top": low + lift * (high - low),
                        "tone": tone, "flicker": flicker, "dead": dead,
                        "period": period, "phase": phase}

    if rng.random() < d["smoke"]:
        face["smoker"] = {"u": rng.uniform(1.2, CELL - 1.2), "out": 1.05,
                          "phase": rng.uniform(0.0, SMOKE_CYCLE)}

    # For the alley side of the same building.
    if rng.random() < d["bulb"]:
        face["bulb"] = {"u": rng.uniform(1.0, CELL - 1.0), "out": 0.45,
                        "y": rng.uniform(2.6, 3.4),
                        "phase": rng.uniform(0.0, 9.0),
                        "dying": rng.random() < 0.3}
    # Strung along the frontage: Chinatown and the market over the street,
    # yokocho over the alley, which is most of what tells them apart from a
    # dark back lane at a glance.
    face["lanterns"] = ({"y": rng.uniform(4.3, 5.6),
                         "tone": _tube(rng, YOKOCHO_TUBES if yoko else d),
                         "phase": rng.uniform(0.0, 6.2)}
                        if rng.random() < (0.9 if yoko else d["lantern"])
                        else None)
    # A place on a lit lane small enough that you can see the whole of it
    # through the window: a counter, and whoever is sitting at it.
    face["pub"] = (yoko and rng.random() < 0.55)
    face["over"] = rng.choice(JP_OVER_DOOR)
    face["escape"] = rng.random() < 0.4
    face["bin"] = rng.uniform(1.2, CELL - 1.2) if rng.random() < 0.3 else None

    # One sign per frontage. A five-metre shopfront carrying a flat neon, a
    # hanging sign and a string of lanterns all at once buries its own corners
    # and roofline, and a street of them is a wall of light with no buildings
    # in it - which was reported as "too many lights to make them out". The
    # hanging sign wins, because it is the one you can read from down the
    # street. Decided off values already drawn rather than new draws, so no
    # other face of the lot - nor anything else about the city - moves.
    if not yoko and face["hung"] is not None:
        if face["flat"] is not None and face["hung"]["phase"] > 1.0:
            face["flat"] = None                  # one in five keeps both
        if face["lanterns"] is not None and face["lanterns"]["phase"] > 1.6:
            face["lanterns"] = None              # one in four keeps both
    return face


def _wide_face(i, j, prefer):
    """A face onto one of the wide streets - three cells across - preferring
    the one asked for, or None. What the diner and the billboards want: they
    are for the traffic as much as for the pavement."""
    for f in [prefer] + [k for k in range(4) if k != prefer]:
        nx, nz = FACES[f]
        a, c = i + nx, j + nz
        if not is_open(a, c) or not road_at(a, c):
            continue
        span = road_span(a, XP, 91) if nx else road_span(c, ZP, 137)
        if span is not None and span[1] >= 3:
            return f
    return None


def _road_face(i, j, prefer):
    """A face giving onto a proper street, preferring the one asked for, or
    None if the building has no street frontage at all.

    A casino down a five-foot alley can never be stood far enough back from to
    read - its marquee lands off the top of the screen - so a building with
    nothing but alley on every side does not get to be one. That also gives the
    city a division of labour worth having: the casinos out on the main roads
    shouting about it, the club down a back street with no sign at all.

    Safe to ask about the neighbours from inside generation: is_open() and
    road_at() are pure functions of their own coordinates and never call lot(),
    so there is no circle to get stuck in."""
    for f in [prefer] + [k for k in range(4) if k != prefer]:
        nx, nz = FACES[f]
        if is_open(i + nx, j + nz) and road_at(i + nx, j + nz):
            return f
    return None


def lot(i, j):
    key = i * 1048576 + j
    b = _lots.get(key)
    if b is None:
        _evict(_lots, 6000)
        rng = random.Random(f"lot|{i}|{j}")
        d = district(i, j)
        base = 11.0 + _mix(i // XP, j // ZP, 43) % 26      # the block's own scale
        b = {
            "height": max(d["lo"], min(d["hi"],
                                       base * rng.uniform(0.7, 1.5) * d["scale"])),
            # The same draw either way, so the woods change nothing else.
            "tone": rng.random() * (0.4 if d is WOODS else 1.0),
            "glyphs": rng.sample(d["glyphs"], 2),
            "density": rng.uniform(*d["dens"]),
            "seed": rng.randrange(1 << 28),
            # Shared by every cell of a block, so a thing can be decided for a
            # whole building rather than for one five-metre slice of it.
            "block": _mix(i // 3, j // 3, 97),
            "ij": (i, j),
            "district": d,
            "tree": d["park"],
        }
        # What is in front of a face decides what goes on it, and asking is
        # safe: face_kind() is a pure function of coordinates and never calls
        # back into lot().
        cap = seafront_cap(i, j)
        if cap is not None:
            b["height"] = min(b["height"], cap)
        b["faces"] = [make_face(rng, b["height"], d,
                                face_kind(i + FACES[f][0], j + FACES[f][1]))
                      for f in range(4)]
        # Every so often the slab is not offices at all. Drawn last so that
        # deciding it changes nothing about the building it was going to be.
        # Neither belongs in a park: the cell would be a clump of trees, and
        # draw_wall_column() would draw it as one, so the venue would exist
        # and be invisible.
        b["club"] = b["casino"] = b["tower"] = b["cinema"] = None
        b["diner"] = b["billboard"] = b["arcade"] = b["exchange"] = None
        b["temple"] = None
        if d["park"]:
            pass
        elif _mix(i, j, 909) % CLUB_ODDS == 0:
            b["height"] = rng.uniform(7.5, 12.0)      # squat, windowless
            b["club"] = {"door": rng.randrange(4),
                         "u": rng.uniform(1.4, CELL - 1.4),
                         "tone": rng.random(),
                         "phase": rng.uniform(0.0, 4.0)}
        elif _mix(i, j, 911) % CLUB_ODDS == 0:
            # Same odds as the club and the exact opposite of it in every
            # other respect.
            face = _road_face(i, j, rng.randrange(4))
            if face is not None:
                b["height"] = rng.uniform(9.0, 16.0)
                b["casino"] = {"door": face,
                               "u": rng.uniform(1.4, CELL - 1.4),
                               "name": rng.choice(CASINO_NAMES),
                               "tone": rng.random(),
                               "sign_tone": rng.random(),
                               "phase": rng.uniform(0.0, 5.0),
                               "i": i, "j": j, "height": b["height"]}
        elif _mix(i, j, 2401) % DINER_ODDS == 0:
            # A diner wants a wide street out front, and only one storey or
            # two over it: it is a low, long, lit box.
            face = _wide_face(i, j, _mix(i, j, 2403) % 4)
            if face is not None:
                # Low whatever part of town it is in, the way a club is a
                # bunker anywhere: the cup on the roof is only in sight
                # from across the street if the roof is.
                b["height"] = min(b["height"], DINER_H)
                b["diner"] = {"door": face, "u": CELL * 0.5, "i": i, "j": j,
                              "height": b["height"],
                              "name": DINER_NAMES[_mix(i, j, 2415)
                                                  % len(DINER_NAMES)],
                              "seed": _mix(i, j, 2417) % 9973}
        elif _mix(i, j, 1961) % CLUB_ODDS == 0 and not d["park"]:
            face = _road_face(i, j, _mix(i, j, 1963) % 4)
            if face is not None:
                b["height"] = max(b["height"], 10.0)
                b["cinema"] = {"door": face, "u": CELL * 0.5,
                               "title": _film_pick(i, j),
                               "offset": _mix(i, j, 1969) % 997,
                               "i": i, "j": j, "height": b["height"]}
        elif d["name"] == "financial" and _mix(i, j, 2701) % EXCHANGE_ODDS == 0 \
                and _road_face(i, j, _mix(i, j, 2703) % 4) is not None:
            # The exchange: low and old among the towers, columns and stone.
            b["height"] = 16.0
            b["exchange"] = {"door": _road_face(i, j, _mix(i, j, 2703) % 4),
                             "u": CELL * 0.5, "i": i, "j": j,
                             "stock": _mix(i, j, 2705) % len(STOCKS),
                             "seed": _mix(i, j, 2707) % 9973}
        elif _mix(i, j, 2501) % ARCADE_ODDS == 0 and d["name"] != "financial":
            # Low, so the light wall and the sign over the door are where you
            # are looking from across the street, not off the top of it - but
            # never under what its district builds. Not in the financial
            # district, which is the cold dark one and keeps to itself.
            face = _road_face(i, j, _mix(i, j, 2503) % 4)
            if face is not None:
                b["height"] = max(d["lo"], min(b["height"], 11.0))
                b["arcade"] = {"door": face, "u": CELL * 0.5, "i": i, "j": j,
                               "name": ARCADE_NAMES[_mix(i, j, 2505)
                                                    % len(ARCADE_NAMES)],
                               "seed": _mix(i, j, 2507) % 9973,
                               "height": b["height"]}
        elif _mix(i, j, 3201) % TEMPLE_ODDS == 0 and d["name"] != "financial":
            # Stone among the shopfronts, with its front on a street, and
            # low: the rose window over the door has to be in sight from
            # across the road.
            face = _road_face(i, j, _mix(i, j, 3203) % 4)
            if face is not None:
                b["height"] = TEMPLE_H
                b["temple"] = {"door": face, "u": CELL * 0.5, "i": i, "j": j,
                               "name": TEMPLE_NAMES[_mix(i, j, 3205)
                                                    % len(TEMPLE_NAMES)],
                               "seed": _mix(i, j, 3207) % 9973,
                               "height": b["height"]}
        elif b["height"] >= TOWER_MIN and _mix(i, j, 1907) % TOWER_ODDS == 0:
            # A sky deck. Off a hash rather than the lot's rng, so being one
            # moves nothing else about the building; and only with a street
            # front, for the same reason as the casino.
            face = _road_face(i, j, _mix(i, j, 1909) % 4)
            if face is not None:
                # Taller than anything else in the city, so the view from the
                # top is over the town rather than into the next tower - the
                # first ones were often hemmed in by taller neighbours - and so
                # its light is a landmark from across it.
                b["height"] = TOWER_TOP + _mix(i, j, 1913) % 9
                b["tower"] = {"door": face, "u": CELL * 0.5, "i": i, "j": j,
                              "height": b["height"]}
        if (b["club"] is None and b["casino"] is None and b["tower"] is None
                and b["cinema"] is None and b["diner"] is None
                and b["arcade"] is None and b["exchange"] is None and not d["park"]
                and b["temple"] is None
                and d["name"] in BILL_DISTRICTS and 8.0 <= b["height"] <= 12.0
                and _mix(i, j, 2405) % BILL_ODDS == 0):
            face = _wide_face(i, j, _mix(i, j, 2407) % 4)
            if face is not None:
                words, tone = ADS[_mix(i, j, 2409) % len(ADS)]
                b["billboard"] = {"face": face, "words": words, "tone": tone,
                                  "i": i, "j": j, "height": b["height"]}
        lm = landmark_at(i, j)
        if lm is not None:
            # The landmark, over whatever else this cell was going to be.
            ring = landmark_ring(lm, i, j)
            b["height"] = LANDMARK_BASE if ring == 0 else LANDMARK_H
            b["club"] = b["casino"] = b["cinema"] = b["diner"] = None
            b["arcade"] = b["billboard"] = b["tower"] = b["exchange"] = None
            b["temple"] = None
            b["tree"] = False
            if (i, j) == lm["lobby"]:
                b["tower"] = {"door": 3, "u": CELL * 0.5, "i": i, "j": j,
                              "height": LANDMARK_H, "kind": "party", "landmark": lm}
        b["landmark"] = lm
        _lots[key] = b
    return b


def face_origin(i, j, f):
    """Where face f of cell (i, j) starts, and which way it runs.

    Returns (plane, u0, axis): the wall lies at x = plane for faces 0 and 1 and
    at z = plane for 2 and 3; u is measured along the wall from u0."""
    if f == 0:
        return i * CELL, j * CELL, 0
    if f == 1:
        return (i + 1) * CELL, j * CELL, 0
    if f == 2:
        return j * CELL, i * CELL, 1
    return (j + 1) * CELL, i * CELL, 1


def face_point(i, j, f, u, out, y):
    """A world point u along face f, standing `out` clear of the wall."""
    nx, nz = FACES[f]
    plane, u0, axis = face_origin(i, j, f)
    if axis == 0:
        return (plane + nx * out, y, u0 + u)
    return (u0 + u, y, plane + nz * out)


# ---------------------------------------------------------------------------
# The view: a camera you can turn, and the rays it casts
# ---------------------------------------------------------------------------

class View:
    """Turns world coordinates into screen cells, and back again.

    dir is where you are looking and plane is the camera plane across it, the
    standard pair for a grid raycaster: the ray through screen column sx is
    dir + plane * cam, and the distance the cast returns is already measured
    along dir, so it needs no correction for the fisheye at the edges.

    Terminal cells are about twice as tall as they are wide, so the vertical
    focal length is half the horizontal one."""

    def __init__(self, x, z, yaw, width, height, eye=EYE_Y, reach=MAX_VIEW):
        self.x = x
        self.z = z
        self.eye = eye          # how high the camera is: the street, or a roof
        self.reach = reach      # how far a wall ray is followed
        # and how many walls deep: from the street the fourth wall back is
        # hidden behind the first three; from a roof you see over all of them.
        self.depth = 4 if eye < 10.0 else 14
        self.yaw = yaw
        self.width = width
        self.height = height
        self.horizon = max(2, min(height - 6, int(height * 0.44)))
        self.dx = math.sin(yaw)
        self.dz = math.cos(yaw)
        self.plx = self.dz * PLANE          # the camera plane, dir turned 90
        self.plz = -self.dx * PLANE
        self.cx = (width - 1) / 2.0
        self.fx = self.cx / PLANE
        self.fy = self.fx * 0.5
        self.wide = set()       # cells holding a double-width glyph
        self.rave = None        # (colour, x, z) of a rig lighting the woods
        self.hollow = None      # (x, z, beat, colour) of the rave on the ground
        self.water = set()      # cells the river was drawn into
        self.wet = 0.0          # how hard it is raining, 0..1
        self.roof = None        # the sky-deck tower you are standing on, if any
        self.ceiling = {}       # tunnel ceiling cells: row * 4096 + col -> distance
        self.tunnels = []       # the tunnels in reach this frame, found once
        self.snow = 0.0         # how hard it is snowing
        self.dawn = 0.0         # how far into the morning, 0..1
        self.cover = 0.0        # and how much is lying
        self.flash = 0.0        # how bright the lightning is this instant
        self.crown = None       # the sky decks' weather light this instant
        self.bass = set()       # the lots by a club whose windows shake this instant
        self.skip = None        # cells not to draw: the landmark whose roof you are on

    def ray(self, sx):
        cam = 2.0 * sx / (self.width - 1) - 1.0
        return self.dx + self.plx * cam, self.dz + self.plz * cam

    def sky_x(self, bearing):
        """Which column a compass bearing falls in, or None if it is behind
        you. Anything hung in the sky is placed by bearing rather than by
        column, or it slides about as you turn."""
        d = (bearing - self.yaw + math.pi) % math.tau - math.pi
        if abs(d) > 1.3:
            return None
        cam = math.tan(d) / PLANE
        if abs(cam) > 1.0:
            return None
        return int(round((cam + 1.0) * 0.5 * (self.width - 1)))

    def project(self, x, y, z):
        """World point -> (screen x, screen y, distance), or None if behind."""
        rx = x - self.x
        rz = z - self.z
        perp = rx * self.dx + rz * self.dz
        if perp < NEAR_Z:
            return None
        lat = rx * self.dz - rz * self.dx
        return (self.cx + lat * self.fx / perp,
                self.horizon - (y - self.eye) * self.fy / perp,
                perp)

    def reflect_row(self, y, perp):
        """Where a thing at height y shows up in the wet road under it: the
        mirror image sits at -y, which is the same column, further down."""
        return self.horizon + (y + self.eye) * self.fy / perp


def cast(v, rdx, rdz, limit=4):
    """March a ray through the grid, collecting the walls it meets, nearest
    first. It keeps going past the first one because a taller building behind a
    short one still shows over its roof."""
    cx = v.x / CELL
    cz = v.z / CELL
    i = int(cx + BIG) - BIG
    j = int(cz + BIG) - BIG

    if rdx:
        dt_x = abs(1.0 / rdx)
        if rdx < 0:
            step_i, next_x = -1, (cx - i) * dt_x
        else:
            step_i, next_x = 1, (i + 1 - cx) * dt_x
    else:
        dt_x = next_x = 1e30
        step_i = 0
    if rdz:
        dt_z = abs(1.0 / rdz)
        if rdz < 0:
            step_j, next_z = -1, (cz - j) * dt_z
        else:
            step_j, next_z = 1, (j + 1 - cz) * dt_z
    else:
        dt_z = next_z = 1e30
        step_j = 0

    hits = []
    max_cells = v.reach / CELL
    while True:
        if next_x < next_z:
            t = next_x
            next_x += dt_x
            i += step_i
            f = 0 if step_i > 0 else 1       # we came in through this face
        else:
            t = next_z
            next_z += dt_z
            j += step_j
            f = 2 if step_j > 0 else 3
        if t > max_cells:
            return hits
        if not is_open(i, j):
            dist = t * CELL
            plane, u0, axis = face_origin(i, j, f)
            if axis == 0:
                u = v.z + rdz * dist - u0
            else:
                u = v.x + rdx * dist - u0
            hits.append((max(dist, 0.35), i, j, f, u))
            if len(hits) >= limit:
                return hits


# ---------------------------------------------------------------------------
# Facades
# ---------------------------------------------------------------------------

def sign_u(face, u):
    """Where along a face a painted letter goes, measured left to right *on
    screen*.

    `u` from cast() always runs with +z on an x-facing wall and with +x on a
    z-facing one, whichever side of the wall you are standing on - which is
    right for two of the four faces and backwards for the other two. Nothing
    else on a facade noticed, because a row of windows reads the same either
    way round. A word does not: every sign on a face whose outward normal is
    -x or +z came out mirrored, and OPEN read as NEPO. Measured over 200
    frames before the fix: 138 signs reversed against 104 the right way round.
    """
    return CELL - u if face in (0, 3) else u


def wall_span(v, dist, height):
    scale = v.fy / dist
    return (int(math.floor(v.horizon - (height - v.eye) * scale)),
            int(math.ceil(v.horizon + v.eye * scale)))


def roof_colour(b, dist, flash=0.0, cover=0.0):
    """A roofline is the edge of the building against the sky, and it was
    getting the same near-black trim as every other horizontal line on the
    facade - the awning, and the balconies at every storey. On a tall building
    that hardly matters because the roof is off the top of the screen; on a low
    one it is the only thing telling you where the building stops, and it was
    losing to its own balconies.

    So a near roofline gets a colour of its own, brighter than anything else
    on the building - not the kerb's, which is already doing the pavement and
    the footing and would have the top of a building drawn the same as the
    ground. Far ones still fog out, or every roofline in the city would read as
    equally close."""
    if cover > 0.35:
        return SNOW                     # snow lying along every roofline
    if flash > 0.35:
        return FLASH
    if dist < 60.0:
        return ROOF
    # And it fades in one step rather than dropping straight into the fog. The
    # rooflines you can actually see are the middle-distance ones - a near
    # building's roof is off the top of the screen - so fogging at the first
    # opportunity hides exactly the ones this was meant to fix.
    return CURB if dist < 115.0 else tone_colour("far", b["tone"])


def wall_colour(b, dist, lit, flash=0.0):
    """What colour a lit window is.

    Each part of town has its own palette, and that carries more of the
    difference between them than anything drawn does: from the street, the
    structure - corners, roofs, awnings, bands - is most of what is on screen
    and windows are under a seventh of it, so a district told apart by its
    window *glyphs* is barely told apart at all. Told apart by being amber
    rather than cold blue, it is obvious at a glance.

    An alley face still gets the dark palette at any range, which is the whole
    reason an alley reads as somewhere you shouldn't go - except for the half
    second a lightning flash lasts, when you can suddenly see what is down
    there."""
    if not lit:
        return tone_colour("far" if flash > 0.35 else "dark", b["tone"])
    if dist > 70.0:
        return tone_colour("far", b["tone"])       # everything fogs out alike
    if lit == "yokocho":
        return tone_colour("red", b["tone"])       # lanterns, not office light
    return tone_colour(b["district"]["pal"], b["tone"])


def neon_attr(s, i, now):
    lit, dark = NEON[min(len(NEON) - 1, int(s["tone"] * len(NEON)))]
    d = dawn(now)
    if d > 0.0 and s["phase"] / 5.0 < d * 1.15:
        return dark             # switched off for the morning, one by one
    sync = city_sync(now)
    if sync is not None:
        # The bad tubes are cured for one night, along with everything else.
        return FLASH if sync == "flash" else (lit if sync == "on" else dark)
    if i in s["dead"]:
        return dark             # one letter of this sign gave up long ago
    if s["flicker"]:
        p = (now + s["phase"]) % s["period"]
        if p < 0.07 or 0.13 < p < 0.17:
            return dark
    return lit


def hidden(walls, sx, sy, dist):
    """Is this cell behind a facade? A facade is a vertical plane, so one
    distance and one row range per column is all the depth anyone needs."""
    wd = walls[0][sx]
    return wd is not None and wd < dist and walls[1][sx] <= sy <= walls[2][sx]


def facade_line(ch, co, sx, row, prev_row, r_lo, r_hi, glyph, attr):
    """A horizontal line on a facade - a roof, an awning - is a slope on
    screen, and a steep one when you are close, so it is drawn as the run of
    rows between where it was in the previous column and where it is now."""
    lo = hi = row
    if prev_row is not None:
        lo, hi = min(row, prev_row), max(row, prev_row)
    for y in range(max(r_lo, lo), min(r_hi, hi) + 1):
        ch[y][sx] = glyph
        co[y][sx] = attr


def club_door(now, club):
    """(is the door open, how many have gone in). It opens once every
    CLUB_DOOR seconds, at a different moment in each, and stands open for
    CLUB_OPEN; the count goes up smoothly while it is open, which is what
    walks the front of the queue in and shuffles the rest up."""
    shut = club_closing(now)
    if shut is not None:
        # Open for good, and the count stops where it was.
        return True, club_door(now - shut - 1e-3, club)[1]
    seed = int(club["tone"] * 1e6)
    t = now + club["phase"] * 3.0
    k = int(t // CLUB_DOOR)
    at = (_mix(k, seed, 1231) & 255) / 255.0 * (CLUB_DOOR - CLUB_OPEN)
    into = t - k * CLUB_DOOR - at
    return 0.0 <= into < CLUB_OPEN, k + min(1.0, max(0.0, into / CLUB_OPEN))


def club_line(i, j, f, club, now):
    """Everything standing outside a club, as (kind, what, where): the queue
    along the wall, the bouncer the other side of the door, the rope between
    the queue and the street, and the light out of the door.

    Each person is numbered, and their place in the line is their number less
    how many have gone in - so when the door opens the one at the front walks
    in, everyone behind steps up, and somebody new joins the back, with no
    state kept anywhere. Who they are is a hash of the number, so the same
    person shuffles up the line rather than turning into someone else."""
    nx, nz = FACES[f]
    side = -1.0 if club["u"] > CELL * 0.5 else 1.0   # the line runs the long way
    seed = int(club["tone"] * 1e6)
    moved = club_door(now, club)[1]
    out = []
    shut = club_closing(now)
    if shut is not None:
        out += going_home(i, j, f, club, shut)
    for q in range(int(moved) - 1, int(moved) + CLUB_QUEUE + 1):
        if shut is not None:
            break                                    # no queue at closing time
        place = q - moved
        if place <= -0.75 or place > CLUB_QUEUE - 1:
            continue
        if place >= 0.0:
            u, o = club["u"] + side * (1.0 + place * CLUB_GAP), 1.0
        else:                                       # going in at the door
            k = place + 1.0
            u, o = club["u"] + side * k, 0.3 + 0.7 * k
        w = face_point(i, j, f, u, o, 0.0)
        m = _mix(seed, q, 1233)
        if m % 5 < 3:
            out.append(("raver", {"club": club, "tone": ((m >> 4) % 97) / 97.0,
                                  "swing": ((m >> 11) % 31) / 31.0,
                                  "tangent": (-nz, nx)}, w))
        else:
            out.append(("smoker", {"phase": ((m >> 4) % 100) / 14.0}, w))
    out.append(("bouncer", club,
                face_point(i, j, f, club["u"] - side * 0.95, 0.7, 0.0)))
    out.append(("rope", (i, j, f, side, club),
                face_point(i, j, f, club["u"] + side * 2.3, 1.7, 0.0)))
    out.append(("clubdoor", (i, j, f, club),
                face_point(i, j, f, club["u"], 0.3, 0.0)))
    out.append(("bass", (i, j, f, club), face_point(i, j, f, club["u"], 0.9, 0.0)))
    return out


def club_closing(now):
    """Seconds into closing time, or None while the night is still going.
    The last CLOSE_LEN of every night - into the dawn, on a night that has
    one - and never on the strange night, when the rig is playing to the sky
    and nobody is going anywhere."""
    nt = night(now)
    if nt["alien"]:
        return None
    t = (now + _night_skip) % NIGHT_LENGTH
    start = NIGHT_LENGTH - CLOSE_LEN
    return t - start if t >= start else None


def going_home(i, j, f, club, shut):
    """Everyone coming out at closing time: one through the door every
    LEAVE_GAP, out onto the pavement, and off down the street one way or the
    other, for LEAVE_FOR seconds, and then the street is empty. Each is a
    number and where they are is a function of how long ago they came out,
    like the queue."""
    out = []
    last = int(min(shut, LEAVE_FOR) / LEAVE_GAP)
    for k in range(max(0, last - 24), last + 1):
        age = shut - k * LEAVE_GAP
        if age < 0.0:
            continue
        m = _mix(int(club["tone"] * 1e6), k, 1237)
        way = 1.0 if m & 1 else -1.0
        if age < 1.2:                              # through the door and out
            u, o, walked = club["u"], 0.3 + 0.8 * age / 1.2, 0.0
        else:
            walked = (age - 1.2) * LEAVE_PACE * (0.85 + (m >> 4 & 7) * 0.05)
            u, o = club["u"] + way * walked, 0.9 + (m >> 8 & 3) * 0.12
        if walked > 26.0:
            continue                               # gone round the corner
        out.append(("leaver", {"stride": walked, "tone": (m >> 12) % 4},
                    face_point(i, j, f, u, o, 0.0)))
    return out


def club_kick(now, club):
    """How far through the beat the club is, 0 on the kick, or None when
    there is no beat - at closing time. On the strange night it is the sky's
    beat, the way the lights are."""
    if club_closing(now) is not None:
        return None
    sync = city_sync(now)
    if sync is not None:
        return 0.0 if sync == "flash" else 0.5
    return (now * CLUB_BPM / 60.0 + club["phase"]) % 1.0


def near_clubs(v, reach):
    """(i, j, club) of the clubs round you, hash first, so it costs a few
    hundred multiplies and not a lot each."""
    n = int(reach / CELL) + 1
    ci = int(v.x / CELL + BIG) - BIG
    cj = int(v.z / CELL + BIG) - BIG
    for i in range(ci - n, ci + n + 1):
        for j in range(cj - n, cj + n + 1):
            if _mix(i, j, 909) % CLUB_ODDS or is_open(i, j):
                continue
            c = lot(i, j)["club"]
            if c is not None:
                yield i, j, c


def bass_lots(v, now):
    """The buildings next to a club whose windows are shaking this instant:
    on the kick, everything within BASS_REACH of the sound system."""
    hit = set()
    for i, j, c in near_clubs(v, 70.0):
        beat = club_kick(now, c)
        if beat is not None and beat < 0.18:
            for a in range(i - BASS_REACH, i + BASS_REACH + 1):
                for b in range(j - BASS_REACH, j + BASS_REACH + 1):
                    if (a, b) != (i, j):
                        hit.add((a, b))
    return hit


def draw_bass(ch, co, v, walls, i, j, f, club, now, wet):
    """The kick, in the puddles: a ring of ripples going out across the wet
    pavement from the club's door on every beat, and the last one's fainter
    behind it. Only when it has been raining - a dry pavement has nothing to
    ripple."""
    if wet < 0.12:
        return
    beat = club_kick(now, club)
    if beat is None:
        return
    lit, dark = NEON[min(len(NEON) - 1, int(club["tone"] * len(NEON)))]
    for r, attr in ((0.6 + beat * 6.0, lit if beat < 0.35 else dark),
                    (6.6 + beat * 6.0, dark)):
        if r > 9.0:
            continue
        steps = max(12, int(r * 14))
        for rr in (r, r + 0.35):                 # a ripple has some width to it
            for k in range(steps + 1):
                a = math.pi * k / steps
                put_point(ch, co, v, walls,
                          *face_point(i, j, f, club["u"] + math.cos(a) * rr,
                                      0.15 + math.sin(a) * rr, 0.03),
                          "~" if k % 2 else "-", attr)


def draw_rope(ch, co, v, walls, i, j, f, side, club, now):
    """Three brass posts between the queue and the street, and the red rope
    sagging between them."""
    posts = [club["u"] + side * (0.6 + k * 1.7) for k in range(3)]
    for k, pu in enumerate(posts):
        for y in (0.3, 0.6):
            put_point(ch, co, v, walls, *face_point(i, j, f, pu, 1.7, y), "|", GOLD_DIM)
        put_point(ch, co, v, walls, *face_point(i, j, f, pu, 1.7, 0.95), "o", GOLD)
        if k + 1 < len(posts):
            for n in range(1, 6):
                t = n / 6.0
                put_point(ch, co, v, walls,
                          *face_point(i, j, f, pu + (posts[k + 1] - pu) * t, 1.7,
                                      0.88 - 0.2 * math.sin(math.pi * t)),
                          "~", ROU_RED)


def draw_door_light(ch, co, v, walls, i, j, f, club, now):
    """While the door is open, the light inside pours out across the street:
    a wedge on the ground widening away from the door, in time with the
    room, thinning out the further it gets."""
    if not club_door(now, club)[0]:
        return
    lamp = club_light(now, club)
    glow = lamp if lamp is not None else NEON[min(
        len(NEON) - 1, int(club["tone"] * len(NEON)))][1]
    d = 0.6
    while d < 9.0:
        half = 0.3 + d * 0.22
        w = -half
        while w <= half:
            if _mix(int(d * 10), int(w * 10), 1235) % 4 < (3 if d < 4.0 else 2):
                put_point(ch, co, v, walls,
                          *face_point(i, j, f, club["u"] + w, d, 0.03),
                          ":" if d < 4.0 else ".", glow)
            w += 0.35
        d += 0.45


def draw_club_column(ch, co, v, sx, dist, b, face, u, r_lo, r_hi, edge, cont,
                     now):
    """One column of a windowless concrete slab with a sound system in it.

    It carries no sign of any kind, which is the joke and also the point: the
    only things that give it away are the light going off behind the slit
    windows on the beat, the door, and the queue standing outside in the rain."""
    scale = v.fy / dist
    club = b["club"]
    trim = FLASH if v.flash > 0.35 else CONCRETE
    roof = int(round(v.horizon - (b["height"] - v.eye) * scale))
    foot = int(round(v.horizon + v.eye * scale))

    if edge:
        for y in range(r_lo, r_hi + 1):
            ch[y][sx] = "|"
            co[y][sx] = trim
        return roof, None, foot, None, ()

    facade_line(ch, co, sx, roof, cont[0], r_lo, r_hi, "=",
                roof_colour(b, dist, v.flash, v.cover))
    facade_line(ch, co, sx, foot, cont[2], r_lo, r_hi, "_", CURB)

    # Bare concrete. Speckled rather than filled, so it reads as a mass with
    # no windows in it instead of as a hole in the street.
    for y in range(r_lo, r_hi + 1, 2):
        if _mix(b["seed"], sx & 7, y) % 5 == 0:
            ch[y][sx] = "."
            co[y][sx] = CONCRETE

    lamp = club_light(now, club)

    # A band of slit windows under the roof, and the light behind them.
    slit = int(round(v.horizon - (b["height"] - 1.7 - v.eye) * scale))
    if r_lo <= slit <= r_hi and int(u / 1.1) % 2 == 0:
        ch[slit][sx] = "=" if lamp is None else "#"
        co[slit][sx] = CONCRETE if lamp is None else lamp

    # The door. Steel, shut most of the time, with the beat leaking out
    # under it - and blinding when it opens.
    if face == club["door"] and abs(u - club["u"]) < 0.8:
        head = int(round(v.horizon - (2.3 - v.eye) * scale))
        sill = int(round(v.horizon - (0.15 - v.eye) * scale))
        if club_door(now, club)[0]:
            glow = lamp if lamp is not None else NEON[min(
                len(NEON) - 1, int(club["tone"] * len(NEON)))][1]
            for y in range(max(r_lo, head), r_hi + 1):
                ch[y][sx], co[y][sx] = "#", glow
        else:
            for y in range(max(r_lo, head), r_hi + 1):
                if y >= sill and lamp is not None:
                    ch[y][sx], co[y][sx] = "_", lamp
                else:
                    ch[y][sx], co[y][sx] = "]", CONCRETE
    return roof, None, foot, None, ()


def chase(u, now, period=0.8):
    """A running bulb chase, the kind that goes round a casino sign. Lit is a
    function of where the bulb is and what time it is, so the whole building
    agrees on the pattern without anything being stored.

    The bulbs sit close together on purpose: space them by half a world unit
    and at arm's length one bulb covers eight columns, which reads as a lit
    stripe rather than as a row of lights."""
    return (int(u / 0.2) - int(now * 24.0)) % 3 == 0





def draw_casino_column(ch, co, v, sx, dist, b, face, u, r_lo, r_hi, edge,
                       cont, now):
    """One column of a casino: everything the club is not.

    Bulbs chasing round the roof and the door, its name across the front in
    neon, and every window in the place lit."""
    scale = v.fy / dist
    cas = b["casino"]
    party = jackpot_on(now, cas)
    blink = FLASH if int(now * 8) % 2 else GOLD
    trim = FLASH if v.flash > 0.35 else (blink if party else GOLD_DIM)
    roof = int(round(v.horizon - (b["height"] - v.eye) * scale))
    foot = int(round(v.horizon + v.eye * scale))

    if edge:
        for y in range(r_lo, r_hi + 1):
            ch[y][sx] = "|"
            co[y][sx] = trim
        return roof, None, foot, None, ()

    prev_roof, prev_awn, prev_foot, prev_k = cont[:4]
    awning = int(round(v.horizon - (FLOOR_H - v.eye) * scale))
    facade_line(ch, co, sx, roof, prev_roof, r_lo, r_hi, "=",
                roof_colour(b, dist, v.flash, v.cover))
    facade_line(ch, co, sx, awning, prev_awn, r_lo, r_hi, "-", trim)

    # Bulbs along the roof and along the canopy over the door.
    for row in (roof, awning):
        if r_lo <= row <= r_hi and (party or chase(u, now)):
            ch[row][sx] = "o"
            co[row][sx] = blink if party else GOLD

    # The name, in neon, across the middle of the front.
    text = cas["name"]
    step = CELL / (len(text) + 1.0)
    letter_k = None
    k = int((sign_u(face, u) - CELL / (2.0 * (len(text) + 1.0))) / step)
    if 0 <= k < len(text):
        letter_k = k
    sign_floor = max(1, int(b["height"] / FLOOR_H) - 2)
    neon = NEON[min(len(NEON) - 1, int(cas["tone"] * len(NEON)))][0]

    bay = int(u / BAY_W)
    frac = u / BAY_W - bay
    lit_bay = BAY_W * v.fx / dist <= 2.0 or 0.30 < frac < 0.70
    thick = max(1, min(5, int(FLOOR_H * scale * 0.45)))
    gold = tone_colour("near", 0.55)

    for f in range(int(b["height"] / FLOOR_H)):
        y = int(round(v.horizon - ((f + 0.55) * FLOOR_H - v.eye) * scale))
        if y > r_hi or y + thick < r_lo:
            continue
        if letter_k is not None and f == sign_floor:
            if prev_k == letter_k:
                continue
            glyph, attr = text[letter_k], neon
        elif not lit_bay:
            continue
        elif f == 0:
            if abs(u - cas["u"]) < 0.9 and face == cas["door"]:
                glyph, attr = ("o", GOLD) if chase(u + now, now) else ("#", GOLD_DIM)
            else:
                glyph, attr = "#", gold
        else:
            # Most of the lights on, not all of them: lit wall to wall, the
            # casino was a gold block with no floors in it, and with the
            # bulbs chasing round the edge on top you could not see where
            # the building stopped.
            m = _mix(b["seed"] + face, f, bay)
            if (m & 0xFFFF) / 65535.0 >= 0.62 and not party:
                continue
            glyph, attr = b["glyphs"][(m >> 17) & 1], gold
            if party:                       # every window on, and flashing
                attr = FLASH if int(now * 8 + f + bay) % 2 else GOLD
        for dy in range(thick):
            yy = y + dy
            if r_lo <= yy <= r_hi:
                ch[yy][sx] = glyph
                co[yy][sx] = attr
    # Last, so nothing paints over where the wall meets the ground.
    facade_line(ch, co, sx, foot, prev_foot, r_lo, r_hi, "_", CURB)
    return roof, awning, foot, letter_k, ()


def arcade_pixel(arc, bay, floor, now):
    """Which neon tube one pane of the arcade's light wall shows this instant,
    or None for dark. The wall runs one pattern for ARCADE_MODE seconds and
    then the next - a rainbow rolling across, a chequer flipping, a bar
    sweeping along, a sparkle - and every arcade starts the cycle somewhere
    different, so two down the same street are not in step."""
    n = len(NEON)
    mode = (int(now / ARCADE_MODE) + arc["seed"]) % 4
    if mode == 0:
        return (bay + floor - int(now * 6.0)) % n
    if mode == 1:
        tick = int(now * 2.5)
        return (tick // 2 + arc["seed"]) % n if (bay + floor + tick) % 2 else None
    if mode == 2:
        return (floor * 3 + arc["seed"]) % n if (bay - int(now * 9.0)) % 6 < 3 else None
    m = _mix(bay, floor, int(now * 7.0) + arc["seed"])
    return (m >> 5) % n if m % 2 == 0 else None


def draw_arcade_column(ch, co, v, sx, dist, b, face, u, r_lo, r_hi, edge,
                       cont, now):
    """One column of an arcade: the loudest front in the city.

    Above the shopfront the whole face is a wall of coloured panes running
    arcade_pixel()'s patterns - solid blocks with a dark line between, so it
    reads as a screen of big pixels rather than as lit windows. Bulbs in every
    colour chase round the roof and along the canopy, the corners change
    colour, and the ground floor is glass with the cabinets' screens glowing
    through it."""
    scale = v.fy / dist
    arc = b["arcade"]
    n = len(NEON)
    roof = int(round(v.horizon - (b["height"] - v.eye) * scale))
    foot = int(round(v.horizon + v.eye * scale))
    if edge:
        corner = FLASH if v.flash > 0.35 else NEON[int(now * 4.0 + face) % n][0]
        for y in range(r_lo, r_hi + 1):
            ch[y][sx] = "|"
            co[y][sx] = corner
        return roof, None, foot, None, ()

    prev_roof, prev_awn, prev_foot = cont[:3]
    awning = int(round(v.horizon - (FLOOR_H - v.eye) * scale))
    trim = FLASH if v.flash > 0.35 else tone_colour("dark", 0.3)
    facade_line(ch, co, sx, roof, prev_roof, r_lo, r_hi, "=",
                roof_colour(b, dist, v.flash, v.cover))
    facade_line(ch, co, sx, awning, prev_awn, r_lo, r_hi, "-", trim)
    for row in (roof, awning):
        if r_lo <= row <= r_hi and chase(u, now):
            ch[row][sx] = "o"
            co[row][sx] = NEON[(int(u * 2.5) + int(now * 3.0)) % n][0]

    bay = int(u / BAY_W) + face * 8
    frac = u / BAY_W - int(u / BAY_W)
    gap = BAY_W * v.fx / dist > 3.0 and not 0.12 < frac < 0.88
    floors = int(b["height"] / FLOOR_H)
    for f in range(floors):
        top = int(round(v.horizon - ((f + 0.92) * FLOOR_H - v.eye) * scale))
        bot = int(round(v.horizon - ((f + 0.12) * FLOOR_H - v.eye) * scale))
        if bot < r_lo or top > r_hi or gap:
            continue
        if f == 0:
            # The window: dark glass with a cabinet's screen in each bay,
            # flickering between colours, and the doors lit.
            if abs(u - arc["u"]) < 0.9 and face == arc["door"]:
                glyph, attr = "#", BULB
            elif 0.3 < frac < 0.7 or BAY_W * v.fx / dist <= 2.0:
                m = _mix(bay, face, int(now * 3.0 + bay * 0.37))
                glyph, attr = "#", NEON[(m >> 6) % n][(m >> 3) & 1]
            else:
                continue
        else:
            k = arcade_pixel(arc, bay, f, now)
            if k is None:
                continue
            glyph, attr = "#", NEON[k][0]
        for yy in range(max(r_lo, top), min(r_hi, bot) + 1):
            ch[yy][sx] = glyph
            co[yy][sx] = attr
    facade_line(ch, co, sx, foot, prev_foot, r_lo, r_hi, "_", CURB)
    return roof, awning, foot, None, ()


def draw_landmark_column(ch, co, v, sx, dist, b, face, u, r_lo, r_hi, edge,
                         cont, now):
    """One column of the landmark: pale stone with a pier up every bay, lit
    windows between, a line of lights along every setback, and the top
    floors of the tower floodlit in a colour that changes every so often, the
    way the real ones are."""
    scale = v.fy / dist
    lm = b["landmark"]
    stone = FLASH if v.flash > 0.35 else MOON_DIM
    roof = int(round(v.horizon - (b["height"] - v.eye) * scale))
    foot = int(round(v.horizon + v.eye * scale))
    if edge:
        for y in range(r_lo, r_hi + 1):
            ch[y][sx], co[y][sx] = "|", stone
        return roof, None, foot, None, ()
    prev_roof, prev_awn, prev_foot = cont[:3]
    facade_line(ch, co, sx, roof, prev_roof, r_lo, r_hi, "=", ROOF)
    if r_lo <= roof + 1 <= r_hi and chase(u, now):
        ch[roof + 1][sx], co[roof + 1][sx] = "o", BULB      # lights along it
    frac = u / BAY_W - int(u / BAY_W)
    pier = BAY_W * v.fx / dist > 2.5 and not 0.2 < frac < 0.8
    floors = int(b["height"] / FLOOR_H)
    flood = NEON[(int(now / 8.0) + lm["seed"]) % len(NEON)][0]
    bay = int(u / BAY_W)
    thick = max(1, min(4, int(FLOOR_H * scale * 0.45)))
    for f in range(floors):
        y = int(round(v.horizon - ((f + 0.55) * FLOOR_H - v.eye) * scale))
        if y > r_hi or y + thick < r_lo:
            continue
        if pier:
            glyph, attr = "|", stone
            thick_ = int(FLOOR_H * scale) + 1
        elif b["height"] >= LANDMARK_H and f >= floors - 4:
            glyph, attr, thick_ = "#", flood, int(FLOOR_H * scale) + 1
        else:
            m = _mix(b["seed"] + face, f, bay)
            if (m & 0xFFFF) / 65535.0 >= 0.5:
                continue
            glyph, attr, thick_ = "#", tone_colour("warm", 0.7), thick
        for dy in range(thick_):
            yy = y + dy
            if r_lo <= yy <= r_hi:
                ch[yy][sx], co[yy][sx] = glyph, attr
    facade_line(ch, co, sx, foot, prev_foot, r_lo, r_hi, "_", CURB)
    return roof, None, foot, None, ()


def _noise(x, salt):
    """Smooth value noise in -1..1: a hashed value at every whole x, eased
    between."""
    k = math.floor(x)
    f = x - k
    f = f * f * (3.0 - 2.0 * f)
    a = (_mix(int(k), salt, 2711) & 0xFFFF) / 32767.5 - 1.0
    b = (_mix(int(k) + 1, salt, 2711) & 0xFFFF) / 32767.5 - 1.0
    return a + (b - a) * f


def stock_mode(s, e):
    """What stock s is doing in epoch e."""
    m = _mix(s, e, 2721) % sum(w for *_, w in MODES)
    for mode in MODES:
        if m < mode[3]:
            return mode
        m -= mode[3]
    return MODES[0]


def _moves(s, k):
    """(how far its modes have carried the price, how wild its noise is), at
    tick k: this epoch's move rising, the last one's fading back out, and the
    wildness eased over from the last epoch's in a couple of ticks."""
    e = int(math.floor(k / EPOCH))
    carry = 0.0
    for ee in (e, e - 1):
        t = (k - ee * EPOCH) / EPOCH
        amp = stock_mode(s, ee)[1]
        carry += amp * (t if t <= 1.0 else max(0.0, 2.0 - t))
    into = k - e * EPOCH
    wild = stock_mode(s, e)[2]
    if into < 2.0:
        before = stock_mode(s, e - 1)[2]
        wild = before + (wild - before) * into / 2.0
    return carry, wild


def market(k):
    """The tide the whole market is on: everything rises and falls on it, some
    stocks more than others."""
    # Slow, for the long bulls and bears; and quick, for the market's nerves
    # on the day, which every stock feels on the same tick.
    return (0.18 * math.sin(k / 157.0 + 1.3) + 0.12 * _noise(k / 23.0, 999)
            + 0.06 * _noise(k / 1.5, 998))


def stock_price(s, t):
    """What stock s is worth at time t, the way it went in between the
    ticks. Four things, all functions of time, so it is the same market
    however you come back to it and nothing is kept: the market's tide, with
    the stock's own beta on it; its sector's current, shared with the other
    three in it; its own swings and noise, wilder in a chaotic epoch; and its
    mode's move - a rise, a fall, a hot streak, a crash."""
    k = t / TICK_LEN
    m = _mix(s, 0, 2713)
    base = 20.0 + (m & 255) * 0.6
    vol = 0.7 + ((m >> 8) & 255) / 255.0 * 0.6
    beta = 0.6 + ((m >> 16) & 63) / 63.0 * 0.9
    b_, c = ((m >> 22) & 63) * 0.1, ((m >> 26) & 31) * 0.2
    sec = STOCKS[s][2]
    carry, wild = _moves(s, k)
    x = (beta * market(k)
         + 0.12 * _noise(k / 17.0, 1000 + sec) + 0.06 * math.sin(k / 41.0 + sec)
         + 0.05 * _noise(k / 2.0, 1100 + sec)
         + 0.10 * math.sin(k / 31.0 + b_) + 0.05 * math.sin(k / 7.3 + c)
         + wild * (0.08 * _noise(k / 2.0, s) + 0.025 * _noise(k * 3.0, s + 17))
         + carry)
    return base * math.exp(vol * x)


def streak(s, now):
    """How many ticks in a row stock s has gone up (or down, negative)."""
    k = tick_of(now)
    run, way = 0, 0
    for q in range(k, k - 30, -1):
        d = stock_price(s, q * TICK_LEN) - stock_price(s, (q - 1) * TICK_LEN)
        w = 1 if d >= 0 else -1
        if way and w != way:
            break
        way, run = w, run + 1
    return run * way


def mood(now):
    """The market's mood for the floor's header: which way the tide has gone
    over the last ten ticks."""
    k = tick_of(now)
    d = market(k) - market(k - 10)
    if d > 0.02:
        return "BULL MARKET"
    return "BEAR MARKET" if d < -0.02 else "FLAT MARKET"


def tick_of(now):
    return int(math.floor(now / TICK_LEN))


def stock_now(s, now):
    """The price you can trade at: the one the last tick set."""
    return stock_price(s, tick_of(now) * TICK_LEN)


def candle(s, k):
    """(open, high, low, close) of tick k: from its price to the next one's,
    and how high and low it went on the way."""
    o, c = stock_price(s, k * TICK_LEN), stock_price(s, (k + 1) * TICK_LEN)
    path = [stock_price(s, (k + f / 12.0) * TICK_LEN) for f in range(13)]
    return o, max(path), min(path), c


def ticker(now):
    """The market going by: every stock, its price, and how it did on the
    last tick, as (text, colour) runs."""
    out = []
    k = tick_of(now)
    for n, (sym, _, _) in enumerate(STOCKS):
        p, q = stock_price(n, k * TICK_LEN), stock_price(n, (k - 1) * TICK_LEN)
        up = p >= q
        out.append((sym + " ", GOLD))
        out.append(("%.2f " % p, FLASH))
        out.append(("%s%.1f%%   " % ("^+" if up else "v-", abs(p / q - 1.0) * 100.0),
                    ROU_GREEN if up else ROU_RED))
    return out


def draw_exchange_column(ch, co, v, sx, dist, b, face, u, r_lo, r_hi, edge,
                         cont, now):
    """One column of the exchange: pale stone among the glass towers, a
    column standing up the front in every bay, dark between, a cornice along
    the top and steps at the foot."""
    scale = v.fy / dist
    stone = FLASH if v.flash > 0.35 else MOON_DIM
    roof = int(round(v.horizon - (b["height"] - v.eye) * scale))
    foot = int(round(v.horizon + v.eye * scale))
    if edge:
        for y in range(r_lo, r_hi + 1):
            ch[y][sx], co[y][sx] = "|", stone
        return roof, None, foot, None, ()
    prev_roof, prev_awn, prev_foot = cont[:3]
    cornice = int(round(v.horizon - (b["height"] - 1.6 - v.eye) * scale))
    facade_line(ch, co, sx, roof, prev_roof, r_lo, r_hi, "=", ROOF)
    facade_line(ch, co, sx, cornice, None, r_lo, r_hi, "=", stone)
    frac = u / BAY_W - int(u / BAY_W)
    if BAY_W * v.fx / dist > 2.5 and 0.3 < frac < 0.6 or BAY_W * v.fx / dist <= 2.5:
        for y in range(max(r_lo, cornice + 1), min(r_hi, foot - 1) + 1):
            ch[y][sx], co[y][sx] = "|", stone                # a column
    else:
        for y in range(max(r_lo, cornice + 1), min(r_hi, foot - 1) + 1):
            if (y + sx) % 5 == 0:
                ch[y][sx], co[y][sx] = ".", tone_colour("warm", 0.4)
    steps = int(round(v.horizon - (0.5 - v.eye) * scale))
    for y in range(max(r_lo, steps), min(r_hi, foot) + 1):
        ch[y][sx], co[y][sx] = "_" if (y - steps) % 2 == 0 else "=", stone
    facade_line(ch, co, sx, foot, prev_foot, r_lo, r_hi, "_", CURB)
    return roof, None, foot, None, ()


def draw_temple_column(ch, co, v, sx, dist, b, face, u, r_lo, r_hi, edge,
                       cont, now):
    """One column of the temple: pale stone, a buttress at every corner, and
    in every bay a tall pointed window of stained glass lit from inside by
    candles - the panes in the city's colours, flickering, with the lead
    between them. Over the front a gable comes to a point; the middle bay of
    the front is the door and the rose window, which draw_temple_front()
    does."""
    scale = v.fy / dist
    tp = b["temple"]
    stone = FLASH if v.flash > 0.35 else MOON_DIM
    front = face == tp["door"]
    rise = TEMPLE_GABLE * max(0.0, 1.0 - abs(u - CELL * 0.5) / (CELL * 0.5)) \
        if front else 0.0
    roof = int(round(v.horizon - (b["height"] + rise - v.eye) * scale))
    foot = int(round(v.horizon + v.eye * scale))
    if edge:
        for y in range(r_lo, r_hi + 1):
            ch[y][sx], co[y][sx] = "|", stone
        return roof, None, foot, None, ()
    prev_roof, prev_awn, prev_foot = cont[:3]
    slope = "^" if rise > TEMPLE_GABLE * 0.9 else (
        "/" if u < CELL * 0.5 else "\\") if front else "="
    facade_line(ch, co, sx, roof, prev_roof, r_lo, r_hi, slope, ROOF)
    n = len(NEON)
    frac = u / BAY_W - int(u / BAY_W)
    narrow = BAY_W * v.fx / dist <= 2.5        # far off: one column a bay
    door_bay = front and abs(u - CELL * 0.5) < 1.1
    w_bot, w_top = 1.4, b["height"] - 1.2
    for y in range(max(r_lo, roof + 1), min(r_hi, foot - 1) + 1):
        h = v.eye + (v.horizon - y) / scale
        half = 0.26
        if h > w_top - 1.4:                    # the pointed arch at the top
            half *= max(0.0, (w_top - h) / 1.4)
        glass = (not door_bay and w_bot < h < w_top
                 and (narrow or abs(frac - 0.5) < half))
        if glass:
            row = int(h * 1.6)
            if row % 3 == 0 and not narrow:
                ch[y][sx], co[y][sx] = "-", CONCRETE          # the lead
            else:
                k = (row // 3 + int(u * 2.0) + tp["seed"]) % n
                lit = _mix(sx, row, int(now * 5.0)) % 9 != 0  # candlelight
                ch[y][sx], co[y][sx] = "#", NEON[k][0 if lit else 1]
        elif abs(frac - 0.5) > 0.44 and not door_bay:
            ch[y][sx], co[y][sx] = "|", stone                 # a buttress
        elif (y + sx) % 7 == 0:
            ch[y][sx], co[y][sx] = ".", tone_colour("warm", 0.3)
    steps = int(round(v.horizon - (0.45 - v.eye) * scale))
    for y in range(max(r_lo, steps), min(r_hi, foot) + 1):
        ch[y][sx], co[y][sx] = "_" if (y - steps) % 2 == 0 else "=", stone
    facade_line(ch, co, sx, foot, prev_foot, r_lo, r_hi, "_", CURB)
    return roof, None, foot, None, ()


def draw_temple_front(ch, co, v, walls, tp, world, now):
    """The front's middle bay: the rose window over the door - a ring of
    stone, spokes of coloured glass turning slowly with the light, a bright
    eye in the middle - and under it the arched door standing open on the
    candles inside, a candle each side of it, and the name over it."""
    i, j, f = tp["i"], tp["j"], tp["door"]
    mid = CELL * 0.5
    n = len(NEON)

    def at(a, h, out=0.15):
        return face_point(i, j, f, mid + a, out, h)

    for k in range(40):                         # the ring
        a = k * math.tau / 40
        put_point(ch, co, v, walls, *at(ROSE_R * math.cos(a), ROSE_Y + ROSE_R
                                         * math.sin(a)), "o", MOON_DIM)
    for k in range(12):                          # the spokes, in glass
        a = k * math.tau / 12
        hue = NEON[(k + int(now * 0.8) + tp["seed"]) % n][0]
        for r in (0.3, 0.5, 0.7, 0.9):
            put_point(ch, co, v, walls, *at(r * math.cos(a), ROSE_Y + r * math.sin(a)),
                      "*" if r > 0.8 else "#", hue)
    put_point(ch, co, v, walls, *at(0.0, ROSE_Y, 0.2), "@", GOLD)
    # The door, arched, open, and the candlelight inside it.
    for k in range(13):
        h = k * 0.2
        half = 0.6 if h < 1.9 else 0.6 * math.sqrt(max(0.0, 1 - ((h - 1.9) / 0.7) ** 2))
        for a in (-half, half):
            put_point(ch, co, v, walls, *at(a, h, 0.2), "|" if h < 1.9 else
                      ("/" if a < 0 else "\\"), MOON_DIM)
        if half > 0.15:
            put_point(ch, co, v, walls, *at(0.0, h, 0.1),
                      ":" if _mix(k, int(now * 6), 3209) % 3 else ".", BULB)
    for a in (-1.0, 1.0):                        # a candle each side
        put_point(ch, co, v, walls, *at(a, 1.1, 0.35), "|", STAR)
        put_point(ch, co, v, walls, *at(a, 1.35, 0.35),
                  "*" if int(now * 7 + a) % 3 else "'", EMBER_HOT)
    pr = v.project(*at(0.0, 3.3, 0.3))
    if pr is not None and pr[2] < 70.0:
        name = tp["name"]
        x0 = int(round(pr[0])) - len(name) // 2
        for k, c in enumerate(name):
            put_cell(ch, co, v, walls, x0 + k, int(round(pr[1])), pr[2], c, GOLD)


def draw_exchange_front(ch, co, v, walls, ex, world, now):
    """STOCK EXCHANGE over the columns, and the ticker running across the
    front under it - the market going by, green when it went up and red when
    it came down. Screen space, for the casino marquee's reason: a ticker
    you cannot read is a stripe."""
    pr = v.project(world[0], world[1], world[2])
    if pr is None or pr[2] > 90.0:
        return
    sx, sy, dist = int(round(pr[0])), int(round(pr[1])), pr[2]
    word = "STOCK  EXCHANGE"
    for k, c in enumerate(word):
        put_cell(ch, co, v, walls, sx - len(word) // 2 + k, sy - 1, dist, c, GOLD)
    width_ = max(16, min(48, int(CELL * v.fx / dist)))
    runs = ticker(now)
    text = "".join(t for t, _ in runs)
    colours = [a for t, a in runs for _ in t]
    shift = int(now * 6.0)
    x0 = sx - width_ // 2
    for k in range(width_):
        n = (k + shift) % len(text)
        put_cell(ch, co, v, walls, x0 + k, sy + 1, dist, text[n], colours[n])
    for x in (x0 - 1, x0 + width_):
        put_cell(ch, co, v, walls, x, sy + 1, dist, "|", GOLD_DIM)


class Broker:
    """Your account at the exchange: cash, and how many of each stock you
    hold and what you paid for them. One for the night, whichever exchange
    you walk into. The cash is the one wallet's."""

    @property
    def cash(self):
        return self.wallet.money

    @cash.setter
    def cash(self, n):
        self.wallet.money = n

    def __init__(self, wallet=None):
        self.wallet = wallet if wallet is not None else Wallet()
        self.held = {}               # stock -> shares
        self.paid = {}               # stock -> what they cost, in all
        self.lot = 0                 # index into LOTS
        self.said = ("", -1e9)
        self.sel = 0                 # the stock picked on the floor
        self.listing = False         # the list of them all, or the chart

    def size(self, s, price, buying):
        n = LOTS[self.lot]
        if n:
            return n
        return int(self.cash // price) if buying else self.held.get(s, 0)

    def buy(self, s, now):
        price = stock_now(s, now)
        n = self.size(s, price, True)
        if n <= 0 or n * price > self.cash + 1e-9:
            self.said = ("not enough cash", now)
            return False
        self.cash -= n * price
        self.held[s] = self.held.get(s, 0) + n
        self.paid[s] = self.paid.get(s, 0.0) + n * price
        self.said = ("bought %d at %.2f" % (n, price), now)
        return True

    def sell(self, s, now):
        price = stock_now(s, now)
        have = self.held.get(s, 0)
        n = min(self.size(s, price, False), have)
        if n <= 0:
            self.said = ("nothing to sell", now)
            return False
        cost = self.paid[s] * n / have
        self.cash += n * price
        self.held[s] = have - n
        self.paid[s] -= cost
        self.said = ("sold %d at %.2f, %s%.2f" % (n, price, "+" if n * price >= cost
                                                  else "-", abs(n * price - cost)), now)
        return True


def render_exchange(ex, broker, width, height, now):
    """The trading floor: the ticker along the top, then either the chart -
    the chosen stock's candles, green where a tick closed up and red where it
    closed down, the wick from its high to its low, the scale down the side -
    or the list of every stock on the floor, to pick from and trade; and
    under either, your account and what to press."""
    ch = [[" "] * width for _ in range(height)]
    co = [[0] * width for _ in range(height)]
    s = broker.sel % len(STOCKS)
    sym, name, sec = STOCKS[s]
    price = stock_now(s, now)
    if width < 50 or height < 18:
        _text(ch, co, height // 2, 1, "%s %.2f" % (sym, price), GOLD)
        _text(ch, co, min(height - 1, height // 2 + 1), 1, "b buys  n sells  s leaves",
              GOLD_DIM)
        return ch, co
    runs = ticker(now)
    text = "".join(t for t, _ in runs)
    colours = [a for t, a in runs for _ in t]
    shift = int(now * 6.0)
    for x in range(width):
        n = (x + shift) % len(text)
        ch[1][x], co[1][x] = text[n], colours[n]
    k = tick_of(now)
    left = int(TICK_LEN - (now - k * TICK_LEN))
    md = mood(now)
    _text(ch, co, 3, 2, "THE EXCHANGE  -  " + md,
          {"BULL": ROU_GREEN, "BEAR": ROU_RED}.get(md[:4], GOLD))
    _text(ch, co, 3, width - 24, "next price in %2ds" % left, GOLD_DIM)
    top, bot = 5, height - 7
    if broker.listing:
        _exchange_list(ch, co, broker, width, top, bot, now)
    else:
        _exchange_chart(ch, co, s, width, top, bot, now)
    held = broker.held.get(s, 0)
    worth = broker.cash + sum(n_ * stock_now(t, now) for t, n_ in broker.held.items())
    cost = broker.paid.get(s, 0.0)
    pl = held * price - cost
    lot = LOTS[broker.lot]
    lines = [
        ("%s %.2f   you hold %d   avg cost %s   on them %s%.2f" % (
            sym, price, held, "%.2f" % (cost / held) if held else "-",
            "+" if pl >= 0 else "-", abs(pl)), ROU_GREEN if pl >= 0 else ROU_RED),
        ("cash %.2f   worth %.2f   in lots of %s" % (
            broker.cash, worth, lot if lot else "max"), GOLD),
        ("b buys  n sells  +/- lot  arrows pick  l %s  s walks out"
         % ("chart" if broker.listing else "list"), GOLD_DIM),
    ]
    for r, (line, attr) in enumerate(lines):
        _text(ch, co, height - 5 + r, 2, line[:width - 3], attr)
    said, at = broker.said
    if now - at < 3.0:
        _text(ch, co, height - 6, 2, said, FLASH)
    return ch, co


def _exchange_chart(ch, co, s, width, top, bot, now):
    sym, name, sec = STOCKS[s]
    price = stock_now(s, now)
    _text(ch, co, top - 1, 2, "%s (%s, %s)  %d/%d" % (name, sym, SECTORS[sec].lower(),
                                                   s + 1, len(STOCKS)), GOLD)
    k = tick_of(now)
    n = max(4, min(CANDLES, (width - 14) // 2))
    cs = [candle(s, k - n + q) for q in range(n)]
    hi = max(c[1] for c in cs)
    lo = min(c[2] for c in cs)
    span = max(1e-6, hi - lo)
    top += 1

    def row(p):
        return bot - int(round((p - lo) / span * (bot - top)))
    for r in range(5):
        p = lo + span * r / 4.0
        _text(ch, co, row(p), width - 11, "- %7.2f" % p, CONCRETE)
    for q, (o, h, l_, c) in enumerate(cs):
        x = 2 + q * 2
        attr = ROU_GREEN if c >= o else ROU_RED
        for y in range(row(h), row(l_) + 1):
            ch[y][x], co[y][x] = "|", attr
        for y in range(min(row(o), row(c)), max(row(o), row(c)) + 1):
            ch[y][x], co[y][x] = "#", attr
    _text(ch, co, row(price), width - 12, ">", FLASH)


def _exchange_list(ch, co, broker, width, top, bot, now):
    """Every stock on the floor, a row each, the chosen one picked out:
    what it is, what it costs, its last move, what you hold of it and what
    that is worth, and whether it is on a streak."""
    _text(ch, co, top, 2,
          "  STOCK  COMPANY               PRICE    MOVE    HELD     VALUE", GOLD_DIM)
    rows = bot - top - 1
    first = max(0, min(len(STOCKS) - rows, broker.sel % len(STOCKS) - rows // 2))
    for r, s in enumerate(range(first, min(len(STOCKS), first + rows))):
        sym, name, _ = STOCKS[s]
        p = stock_now(s, now)
        q = stock_price(s, (tick_of(now) - 1) * TICK_LEN)
        move = p / q - 1.0
        held = broker.held.get(s, 0)
        run = streak(s, now)
        tag = "HOT!" if run >= STREAK else ("SLIDE" if run <= -STREAK else "")
        mine = s == broker.sel % len(STOCKS)
        y = top + 1 + r
        _text(ch, co, y, 2, ">" if mine else " ", FLASH)
        _text(ch, co, y, 4, "%-5s  %-20s" % (sym, name[:20]), FLASH if mine else GOLD)
        _text(ch, co, y, 34, "%8.2f" % p, FLASH if mine else CONCRETE)
        _text(ch, co, y, 44, "%+6.1f%%" % (move * 100),
              ROU_GREEN if move >= 0 else ROU_RED)
        if held:
            _text(ch, co, y, 52, "%6d  %9.2f" % (held, held * p), GOLD)
        if tag and width > 76:
            _text(ch, co, y, 70, tag, ROU_GREEN if run > 0 else ROU_RED)


def draw_tree_column(ch, co, v, sx, dist, b, u, r_lo, r_hi):
    """A clump of trees, which is what a park has instead of buildings.

    No roof line, no corner, no footing: the whole point of it is that nothing
    about it is straight. The canopy height wanders along the clump so it has a
    ragged top, and the trunks only show through in the gap underneath."""
    scale = v.fy / dist
    wob = (_mix(b["seed"], int(u * 2.5), 5) % 100) / 100.0
    top_y = b["height"] * (0.70 + 0.30 * wob)
    crown = int(round(v.horizon - (top_y - v.eye) * scale))
    under = int(round(v.horizon - (top_y * 0.34 - v.eye) * scale))
    leaf = tone_colour("leaf", b["tone"])
    # A rig in a clearing throws its light up into the leaves around it, and
    # that is what you see first - long before the stack, the fire or anyone
    # standing in front of them. Nearest trees take the most of it.
    if v.rave is not None:
        lamp, rx, rz = v.rave
        zw = v.z + v.dz * dist
        xw = v.x + v.dx * dist
        near = (xw - rx) ** 2 + (zw - rz) ** 2
        if near < 4900.0:
            leaf = lamp
    for y in range(max(r_lo, crown), min(r_hi, under) + 1):
        if _mix(sx, y, 11) % 100 < 64:
            ch[y][sx] = "&%*#"[_mix(sx, y, 13) % 4]
            co[y][sx] = leaf
            # Snow sits on the top of the canopy first, then works down.
            if v.cover > 0.2 and (_mix(sx, y, 19) % 100
                                  < v.cover * (70 - 40 * (y - crown)
                                               / max(1, under - crown))):
                co[y][sx] = SNOW
    for y in range(max(r_lo, under + 1), r_hi + 1):
        if _mix(sx, y, 17) % 5 == 0:
            ch[y][sx] = "|"
            co[y][sx] = BARK
    return crown, None, None, None, ()


TOWER_GRID = 20.0       # buildings this tall show their dark windows as a grid


def draw_wall_column(ch, co, v, sx, dist, b, face, u, r_lo, r_hi,
                     edge, cont, lit, now):
    """One screen column of one facade. Returns what the caller needs to keep
    the lines along it joined up in the next column."""
    if b["tree"]:
        return draw_tree_column(ch, co, v, sx, dist, b, u, r_lo, r_hi)
    if b["club"] is not None:
        return draw_club_column(ch, co, v, sx, dist, b, face, u,
                                r_lo, r_hi, edge, cont, now)
    if b["casino"] is not None:
        return draw_casino_column(ch, co, v, sx, dist, b, face, u,
                                  r_lo, r_hi, edge, cont, now)
    if b["arcade"] is not None:
        return draw_arcade_column(ch, co, v, sx, dist, b, face, u,
                                  r_lo, r_hi, edge, cont, now)
    if b["temple"] is not None:
        return draw_temple_column(ch, co, v, sx, dist, b, face, u,
                                  r_lo, r_hi, edge, cont, now)
    if b["diner"] is not None:
        return draw_diner_column(ch, co, v, sx, dist, b, face, u,
                                 r_lo, r_hi, edge, cont, now)
    if b["landmark"] is not None:
        return draw_landmark_column(ch, co, v, sx, dist, b, face, u,
                                    r_lo, r_hi, edge, cont, now)
    if b["exchange"] is not None:
        return draw_exchange_column(ch, co, v, sx, dist, b, face, u,
                                    r_lo, r_hi, edge, cont, now)
    d = b["district"]
    scale = v.fy / dist
    trim = tone_colour("dark" if not lit else "far", b["tone"])
    if v.flash > 0.35:
        # Lightning picks out every edge in the city at once, which is what
        # makes a flash read as a flash rather than as the screen blinking.
        trim = FLASH
    roof = int(round(v.horizon - (b["height"] - v.eye) * scale))
    awning = int(round(v.horizon - (FLOOR_H - v.eye) * scale))
    foot = int(round(v.horizon + v.eye * scale))

    if edge:
        # A building corner. Solid, so it reads as a hard edge and nothing
        # behind it leaks through the unlit windows. It still reports where its
        # lines are, or the next column would think it was a corner too, and
        # the whole facade would come out as bars.
        for y in range(r_lo, r_hi + 1):
            ch[y][sx] = "|"
            co[y][sx] = trim
        return roof, awning, foot, None, ()

    prev_roof, prev_awn, prev_foot, prev_k, prev_bands = cont
    facade_line(ch, co, sx, roof, prev_roof, r_lo, r_hi, d["roof"],
                roof_colour(b, dist, v.flash, v.cover))
    if lit:                       # an alley has no shopfronts to put one over
        facade_line(ch, co, sx, awning, prev_awn, r_lo, r_hi, "-", trim)

    fc = b["faces"][face]
    sign = fc["flat"] if lit else None
    letter_k = None
    if sign is not None:
        k = int((sign_u(face, u) - CELL / (2.0 * (len(sign["text"]) + 1.0)))
                / sign["step"])
        if 0 <= k < len(sign["text"]):
            letter_k = k

    # A bay is wider than one column once you are close, and a window that
    # filled its whole bay would smear the facade into horizontal stripes.
    # Windows get the middle of their bay; a sign letter gets exactly one
    # column, the first it appears in, so the word does not stutter.
    bay = int(u / BAY_W)
    frac = u / BAY_W - bay
    bay_cols = BAY_W * v.fx / dist
    lit_bay = bay_cols <= 2.0 or 0.30 < frac < 0.70

    colour = wall_colour(b, dist, lit, v.flash)
    thick = max(1, min(5, int(FLOOR_H * scale * 0.45)))   # windows have height
    density = b["density"] if lit else b["density"] * 0.35
    density *= 1.0 - 0.92 * v.dawn          # the windows going out at dawn
    # The colour a dark window is drawn in, or None for no dot: only on the
    # tall ones - a low building is outlined by its own roof against the sky,
    # a tower's roof is off the top of the screen - on faces near enough to
    # see the grid of, and fogged out with everything else.
    unlit = (tone_colour("dark", b["tone"])
             if b["height"] >= TOWER_GRID and bay_cols > 1.2 and dist < 90.0
             else None)
    storeys = int(b["height"] / FLOOR_H)

    # A line at every storey: balconies in Chinatown and the housing, ribbing
    # on a corrugated shed down at the docks. It needs the joining-up the roof
    # gets, remembered per storey, or the wall comes out as a fan of dashes -
    # which is what killed the first attempt at this months ago.
    bands = ()
    if d["band"]:
        bands = tuple(int(round(v.horizon - (f * FLOOR_H - v.eye) * scale))
                      for f in range(1, storeys))
        for n, by in enumerate(bands):
            if r_lo - 2 <= by <= r_hi + 2:
                facade_line(ch, co, sx, by,
                            prev_bands[n] if n < len(prev_bands) else None,
                            r_lo, r_hi, d["band"], trim)

    # A mullion at every bay, which is what a glass curtain wall looks like
    # from the street and nothing else in this city does. One column wide at
    # any distance, the same way a sign letter is.
    if d["mullion"] and frac * bay_cols < 1.0:
        for y in range(r_lo, r_hi + 1):
            ch[y][sx] = "|"
            co[y][sx] = trim
        facade_line(ch, co, sx, foot, prev_foot, r_lo, r_hi, "_", CURB)
        return roof, awning, foot, None, bands

    # A fire escape zigzags down the back of an alley building, one landing per
    # storey, and is the only thing up there catching any light.
    escape = (not lit) and fc["escape"] and 0.45 < frac < 0.8

    crown = storeys - CROWN_FLOORS if b["tower"] is not None else storeys
    # Next door to a club, the windows shake on the kick.
    shake = 1 if b["ij"] in v.bass else 0
    for f in range(storeys):
        y = int(round(v.horizon - ((f + 0.55) * FLOOR_H - v.eye) * scale)) + shake
        if y > r_hi or y + thick < r_lo:
            continue
        if f >= crown:
            # The weather beacon: a solid band, every column of it, so it
            # reads as one light across the top and not as lit windows.
            if v.crown is None:
                continue
            glyph, attr = "#", v.crown
        elif letter_k is not None and sign["floor"] == f:
            if prev_k == letter_k:
                continue
            glyph, attr = sign["text"][letter_k], neon_attr(sign, letter_k, now)
        elif escape and f:
            glyph, attr = "=", trim
        elif not (lit_bay or d["whole_floors"]):
            continue
        elif f == 0:
            if _mix(b["seed"], face, bay) % d["gap"] == 0:
                continue                      # a doorway between the shopfronts
            glyph, attr = d["ground"], colour
        elif d["whole_floors"]:
            # A glass tower is not lit window by window: it is dark, and then
            # somewhere up it one whole floor is on because the cleaners are
            # there. A solid bright line across a black slab, which nothing
            # else in the city looks remotely like.
            # Keyed on the block, not the cell, or the lit floor is five
            # metres of one and stops reading as a floor of a tower.
            if _mix(b["block"], f, 3) % 11:
                if unlit is not None and r_lo <= y <= r_hi:
                    ch[y][sx], co[y][sx] = ".", unlit
                continue
            glyph, attr = d["glyphs"][0], colour
        else:
            m = _mix(b["seed"] + face, f, bay)
            if (m & 0xFFFF) / 65535.0 >= density:
                # A dark window is still a window. Drawn as nothing, a tower
                # with few lights on was a black face with scattered points -
                # which is exactly what the night sky is, and the two could
                # not be told apart ("hard to make out a skyscraper against
                # the night sky"). A faint dot on the window grid gives the
                # face the regularity stars never have.
                if unlit is not None and r_lo <= y <= r_hi:
                    ch[y][sx], co[y][sx] = ".", unlit
                continue
            glyph, attr = b["glyphs"][(m >> 17) & 1], colour
        for dy in range(thick):
            yy = y + dy
            if r_lo <= yy <= r_hi:
                ch[yy][sx] = glyph
                co[yy][sx] = attr
    # Through the window of a place on a lit lane: the counter, and the backs
    # of the people at it. Drawn after the storeys so it wins the ground floor,
    # which would otherwise be a shopfront like anywhere else.
    if lit == "yokocho" and fc["pub"]:
        # Stacked in rows off the counter rather than placed at true heights.
        # Half a metre between someone's shoulders and their head is a dozen
        # rows when you are stood right outside, and they come apart into
        # unrelated marks - the same reason the hung signs count rows.
        warm = tone_colour("warm", b["tone"])
        base = int(round(v.horizon - (1.05 - v.eye) * scale))
        if r_lo <= base <= r_hi:
            ch[base][sx] = "="
            co[base][sx] = trim
        # One column a person, however close you are, or a slot wider than a
        # cell smears them into a row of Ms - the same trick the sign letters
        # use to stop a word stuttering.
        slot = u / 0.8
        seat_cols = 0.8 * v.fx / dist
        if int(slot) % 2 == 0 and (slot - int(slot)) * max(1.0, seat_cols) < 1.0:
            for dy, glyph in ((1, "M"), (2, "o")):
                if r_lo <= base - dy <= r_hi:
                    ch[base - dy][sx] = glyph
                    co[base - dy][sx] = warm

    facade_line(ch, co, sx, foot, prev_foot, r_lo, r_hi, "_", CURB)
    return roof, awning, foot, letter_k, bands


def draw_walls(ch, co, v, now):
    """Cast one ray per screen column and paint what it hits.

    Within a column the hits are drawn nearest first and each one after is
    clipped to the rows above everything already drawn, so a tall building
    behind a short one shows over its roof and nothing else leaks through."""
    width = v.width
    wall_d = [None] * width
    wall_top = [v.height] * width
    wall_base = [-1] * width
    # The highest roof of anything in the column, near or far. wall_top is the
    # nearest wall's and is what occlusion wants; this is what the sky wants,
    # and they are not the same the moment a tall building stands behind a
    # short one - which is most of a city.
    sky_top = [v.height] * width
    seen = {}          # (cell, face) -> what the column to the left left off at

    for sx in range(width):
        rdx, rdz = v.ray(sx)
        cover = None
        for n, (dist, i, j, f, u) in enumerate(cast(v, rdx, rdz, v.depth)):
            if v.skip and (i, j) in v.skip:
                continue                 # the building you are standing on
            b = lot(i, j)
            top, base = wall_span(v, dist, b["height"])
            r_lo = max(0, top)
            r_hi = min(v.height - 1, base)
            if cover is not None:
                r_hi = min(r_hi, cover - 1)
            if r_hi < r_lo:
                continue
            key = (i, j, f)
            was = seen.get(key)
            cont = was[1] if was is not None and was[0] == sx - 1 else None
            if cont is None:
                # The column to the left may have been the building next door
                # on the same plane. That is a terrace, not a corner: draw no
                # bar and let the roof line step between the two heights, which
                # is the only edge actually there.
                for nk in (((i, j - 1, f), (i, j + 1, f)) if f < 2
                           else ((i - 1, j, f), (i + 1, j, f))):
                    w = seen.get(nk)
                    if w is not None and w[0] == sx - 1:
                        cont = (w[1][0], w[1][1], w[1][2], None, w[1][4])
                        break
            nx, nz = FACES[f]
            seen[key] = (sx, draw_wall_column(
                ch, co, v, sx, dist, b, f, u, r_lo, r_hi,
                cont is None and sx > 0,
                cont or (None, None, None, None, ()),
                face_kind(i + nx, j + nz), now))
            if b["diner"] is not None and f == b["diner"]["door"]:
                diner_window(ch, co, v, sx, dist, u, f, r_lo, r_hi, b)
            if v.tunnels and tunnel_at(i + nx, j + nz):
                tunnel_lining(ch, co, v, sx, dist, r_lo, r_hi, j, _mix(i, j, 2209))
            cover = r_lo if cover is None else min(cover, r_lo)
            sky_top[sx] = cover
            if not n:
                wall_d[sx] = dist
                wall_top[sx] = r_lo
                wall_base[sx] = r_hi
            if cover <= 0:
                break

    return (wall_d, wall_top, wall_base, sky_top)


# ---------------------------------------------------------------------------
# Sky, ground and the light lying on it
# ---------------------------------------------------------------------------

def draw_flash(ch, co, v, walls, flash):
    """What a strike actually does: pick out the whole city at once.

    Lighting only the sky leaves every facade the same dark shape it was, and
    the strike reads as the rain having gone white. Filling the blank parts of
    each wall turns the buildings into lit surfaces for the tenth of a second
    they are lit for, which is the entire point of lightning."""
    if flash < 0.05:
        return
    walls_d, walls_top, walls_base = walls[0], walls[1], walls[2]
    dens = int(flash * 66)
    for sx in range(v.width):
        if walls_d[sx] is None:
            continue
        lo = max(0, walls_top[sx])
        hi = min(v.height - 1, walls_base[sx])
        for y in range(lo, hi + 1):
            if ch[y][sx] == " " and _mix(sx, y, 97) % 100 < dens:
                ch[y][sx] = ":"
                co[y][sx] = FLASH
    ground = int(flash * 38)
    for y in range(v.horizon + 1, v.height):
        row, rowc = ch[y], co[y]
        for sx in range(v.width):
            if row[sx] == " " and _mix(sx, y, 131) % 100 < ground:
                row[sx] = "."
                rowc[sx] = FLASH


class SkyBox:
    """Just enough of a View for the sky effects to draw into the skyline.

    They want a width and a horizon and nothing else - the street's View
    carries a camera the waterfront has no use for."""

    def __init__(self, width, horizon, off=0):
        self.width = width
        self.horizon = horizon
        self.height = horizon
        self.off = off

    def sky_x(self, bearing):
        """The waterfront has no camera to turn, so a bearing just maps across
        the same slow scroll the stars ride on."""
        span = self.width * 2
        return (int(bearing / math.tau * span - self.off) % span
                - self.width // 2)


# Stars per thousand sky cells on a perfectly clear night, and how many more
# the milky way adds where it is up. Halved from what they were: the sky was
# reported as "too distracting and too much", and on a clear night with the
# band up it had been a seventh of everything above the roofs.
STAR_RATE = 45.0
BAND_RATE = 210.0

STAR_TIERS = ((720, ".", "dim"), (905, "'", "dim"), (975, "*", "mid"),
              (996, "+", "bright"), (1000, "o", "bright"))


def star_look(m, warmth):
    """One star's glyph and colour. Most of them are faint: a sky where every
    star is bright reads as static, and the few that are bright stop counting
    for anything."""
    roll = (m >> 9) % 1000
    for edge, glyph, tier in STAR_TIERS:
        if roll < edge:
            break
    hue = (m >> 21) % 1000 / 1000.0
    if tier == "dim":
        attr = STAR_DIM
    elif tier == "mid":
        attr = STAR
    else:
        attr = STAR | curses.A_BOLD
    if hue < warmth * 0.5:
        attr = STAR_WARM
    elif hue > 1.0 - warmth * 0.35:
        attr = STAR_COLD
    return glyph, attr


def sky_col(v, bearing):
    """Which screen column a compass bearing falls in, or None if it is not in
    front of you. The inverse of the bearing the star field is keyed on."""
    d = (bearing - v.yaw + math.pi) % math.tau - math.pi
    if abs(d) > 1.3:
        return None
    cam = math.tan(d) / PLANE
    if abs(cam) > 1.0:
        return None
    return int(round((cam + 1.0) * 0.5 * (v.width - 1)))


def draw_moon(ch, co, v, tops, now, seen):
    """The moon, if it is up and this side of the sky.

    One or two characters and no glow around it. It is the only object in the
    sky and it does not need help - anything more and it stops being a moon in
    a city and starts being a poster."""
    face = moon_face(night(now)["phase"])
    if not face:
        return
    bearing, alt = moon_dir(now)
    sx = sky_col(v, bearing)
    if sx is None:
        return
    y = int(round((1.0 - alt) * (v.horizon - 2)))
    dim = abs(night(now)["phase"] - 0.5) * 2.0 > 0.34
    for k, c in enumerate(face):
        x = sx + k
        if 0 <= x < v.width and 0 <= y < tops[x] and y < v.horizon:
            ch[y][x] = c
            co[y][x] = MOON_DIM if dim else MOON
            seen.add((y, x))


def draw_meteor(ch, co, v, tops, now, seen):
    """A streak, now and then, on the nights that have them. Short enough that
    you are never sure you saw it, which is the whole of a meteor."""
    n = night(now)
    if not n["meteors"]:
        return
    slot = int(now / 3.0)
    m = _mix(slot, 0, 887)
    if m % max(2, 26 - n["meteors"] * 3):
        return
    t = (now / 3.0) % 1.0
    if t > 0.22:
        return
    bearing = ((m >> 8) & 1023) / 1023.0 * math.tau
    sx = sky_col(v, bearing)
    if sx is None:
        return
    y0 = ((m >> 18) & 15) / 15.0 * 0.5 + 0.05
    slope = 1.0 if (m >> 3) & 1 else -1.0
    run = int(t / 0.22 * 9)
    for k in range(max(0, run - 3), run + 1):
        x = sx + int(k * slope)
        y = int(round((y0 + k * 0.035) * (v.horizon - 2)))
        if 0 <= x < v.width and 0 <= y < tops[x] and y < v.horizon:
            ch[y][x] = "\\" if slope > 0 else "/"
            co[y][x] = MOON if k == run else STAR_DIM
            seen.add((y, x))


def draw_sky(ch, co, v, walls, wet, now):
    """Stars, and a haze of distant roofs at the horizon.

    Drawn after the walls rather than before: an unlit window is a blank cell,
    so wall_top is the only thing that knows a building is in the way. The
    stars are keyed by the compass bearing of the ray rather than the screen
    column, so they hold still while you turn under them - and they are gone
    altogether once the cloud comes over.

    A column that hit no wall at all is looking straight out of the city down a
    cross street. Rather than leave a void at the vanishing point it gets a
    taller silhouette, which is what the rest of the city looks like from
    further away than anyone is going to draw it."""
    thin = 2 + int(3.0 * wet)
    n = night(now)
    # Cloud takes the sky away gradually rather than all at once at a
    # threshold, so a night can be half lost behind it.
    cloud = 1.0 if overcast_held() else (0.0 if n["alien"] else cloud_cover(now))
    clear = n["clarity"] * (1.0 - cloud) * max(0.0, 1.0 - v.dawn * 1.4)
    # walls[3], not walls[1]: a star must clear every roof in its column, not
    # only the nearest one. The part of a far tower that shows above a nearer
    # roof is still a building, and stars were being drawn straight into it.
    tops = walls[3]
    seen = set()

    for sx in range(v.width):
        top = tops[sx]
        cam = 2.0 * sx / (v.width - 1) - 1.0
        rad = v.yaw + math.atan(cam * PLANE)
        bearing = int(rad * 90.0)
        if clear > 0.02:
            # Per visible cell, not per bearing with a random height: from a
            # street the rooftops hide five sixths of the sky, so stars
            # scattered over the whole hemisphere nearly all land behind a
            # building and you get one or two. Keyed on (bearing, row), which
            # still holds them still while you turn.
            band_mid = (0.5 + n["tilt"] * math.sin(rad - n["swing"])
                        if n["band"] else None)
            for y in range(min(top, v.horizon)):
                m = _mix(bearing, y, 71)
                alt = 1.0 - y / float(max(1, v.horizon - 1))
                rate = STAR_RATE * clear
                if n["alien"]:
                    rate += 190.0     # the sky is the rig tonight
                if band_mid is not None:
                    near = max(0.0, 1.0 - abs(alt - band_mid) / 0.19)
                    rate += BAND_RATE * clear * near
                if (m % 1000) >= rate:
                    continue
                glyph, attr = star_look(m, n["warmth"])
                if (band_mid is not None and glyph == "."
                        and abs(alt - band_mid) < 0.14):
                    attr = BAND
                if n["alien"]:
                    attr = alien_light(now, (m >> 6) & 7)
                    if glyph == ".":
                        glyph = "*'+"[(m >> 3) % 3]
                ch[y][sx] = glyph
                co[y][sx] = attr
                seen.add((y, sx))
        empty = walls[0][sx] is None
        deep = _mix(bearing // 3, 2, 17) % 7 if empty else 0
        for d in range(max(deep, _mix(bearing, 1, 3) % thin)):
            y = v.horizon - 1 - d
            if 0 <= y < top:
                ch[y][sx] = ":" if d else "."
                co[y][sx] = HAZE
        if v.flash > 0.05:
            # The whole sky goes pale, so everything with a roof on it turns
            # into a black shape against it.
            for y in range(0, min(top, v.horizon)):
                if _mix(sx, y, 29) % 100 < v.flash * 96:
                    ch[y][sx] = "." if v.flash < 0.5 else ":"
                    co[y][sx] = FLASH

    if v.dawn > 0.0:
        for sx in range(v.width):
            cam = 2.0 * sx / (v.width - 1) - 1.0
            bearing = int((v.yaw + math.atan(cam * PLANE)) * 90.0)
            for y in range(min(tops[sx], v.horizon)):
                if ch[y][sx] == " ":
                    g = dawn_glow(bearing, y, v.horizon, v.dawn)
                    if g is not None:
                        ch[y][sx], co[y][sx] = g
    if n["alien"] and not overcast_held():
        draw_sky_beams(ch, co, v, tops, now, seen)
        draw_mother(ch, co, v, tops, now, seen)
        draw_saucers(ch, co, v, tops, now, seen)
        draw_landing_beam(ch, co, v, tops, now, seen)
    if clear > 0.15:
        draw_moon(ch, co, v, tops, now, seen)
        draw_meteor(ch, co, v, tops, now, seen)


GLOW_CELL = 1.6


def collect_glow(v, now, wet):
    """A coarse world map of what colour is spilling onto the ground where.

    Neon does it when the road is wet; a bare bulb over an alley door does it
    whatever the weather, and is often the only thing down there that does."""
    glow = {}
    reach = 7.0
    for lx, lz in near_park_lamps(v, 60.0):
        _spill(glow, lx, lz, 6.5, EMBER)
    for _, cx_, cz_, (dx_, dz_), kind, g in near_cars(v, now, 70.0, every=True):
        _spill(glow, cx_ + dx_ * 5.0, cz_ + dz_ * 5.0, 2.5, BULB_DIM)
        if kind == "police":
            _spill(glow, cx_, cz_, 9.0, police_light(now, g))
    for tx0, tx1, tz0, tz1, kind in v.tunnels:
        if kind == "short":
            _spill(glow, *camp_spot(tx0, tx1, tz0, tz1), 5.0, EMBER)
    for c_ in near_carnivals(v, 60.0):
        (wx, wz), (cx, cz), stalls, _ = carnival_spots(c_)
        _spill(glow, wx, wz, 11.0, NEON[int(now * 5.0) % len(NEON)][1])
        _spill(glow, cx, cz, 4.0, GOLD_DIM)
    for i, j, b in near_lots(v, 60.0):
        for f in range(4):
            nx, nz = FACES[f]
            if not is_open(i + nx, j + nz):
                continue
            if b["club"] is not None:
                if f == b["club"]["door"]:
                    lamp = club_light(now, b["club"])
                    if lamp is not None:
                        p = face_point(i, j, f, b["club"]["u"], 1.0, 0.0)
                        _spill(glow, p[0], p[2], 5.5, lamp)
                    if club_door(now, b["club"])[0]:
                        # The door open: the street in front takes the light.
                        p = face_point(i, j, f, b["club"]["u"], 4.0, 0.0)
                        _spill(glow, p[0], p[2], 6.0, lamp or NEON[min(
                            len(NEON) - 1, int(b["club"]["tone"] * len(NEON)))][1])
                continue
            if b["casino"] is not None:
                p = face_point(i, j, f, CELL * 0.5, 1.0, 0.0)
                _spill(glow, p[0], p[2], 6.0, GOLD_DIM)
                continue
            if b["exchange"] is not None:
                if f == b["exchange"]["door"]:
                    p = face_point(i, j, f, CELL * 0.5, 1.0, 0.0)
                    _spill(glow, p[0], p[2], 5.0, GOLD_DIM)
                continue
            if b["temple"] is not None:
                if f == b["temple"]["door"]:
                    p = face_point(i, j, f, CELL * 0.5, 1.0, 0.0)
                    _spill(glow, p[0], p[2], 4.5, BULB_DIM)
                continue
            if b["arcade"] is not None:
                # The pavement in front takes the colour of whatever the
                # light wall is doing.
                p = face_point(i, j, f, CELL * 0.5, 1.0, 0.0)
                _spill(glow, p[0], p[2], 6.5, NEON[int(now * 2.0 + f) % len(NEON)][1])
                continue
            fc = b["faces"][f]
            if face_kind(i + nx, j + nz):
                # Neon reaches the water whatever the weather - a river does
                # not need rain to be wet.
                if wet < 0.12 and not river_at(i + nx * 3, j + nz * 3):
                    continue
                for s in (fc["flat"], fc["hung"]):
                    if s is None:
                        continue
                    u = s.get("u", CELL * 0.5)
                    p = face_point(i, j, f, u, 1.0, 0.0)
                    dark = NEON[min(len(NEON) - 1,
                                    int(s["tone"] * len(NEON)))][1]
                    _spill(glow, p[0], p[2], reach * wet, dark)
            elif fc["bulb"] is not None:
                p = face_point(i, j, f, fc["bulb"]["u"], 1.0, 0.0)
                _spill(glow, p[0], p[2], 3.4, BULB_DIM)
    return glow


def _spill(glow, x, z, reach, attr):
    gi = int(x / GLOW_CELL + BIG) - BIG
    gj = int(z / GLOW_CELL + BIG) - BIG
    n = max(1, int(reach / GLOW_CELL))
    for a in range(gi - n, gi + n + 1):
        for b in range(gj - n, gj + n + 1):
            if (a - gi) ** 2 + (b - gj) ** 2 <= n * n:
                glow[a * 65536 + b] = attr


ANGLER = [
    " o    ",
    "/|\\__ ",
    " |   \\",
    "/ \\   ",
]

# Somebody leaning on a bridge railing, seen from behind: elbows out on the
# rail, looking down the river. Not on every bridge.
LEANER = [
    "  ,-.  ",
    "  ( )  ",
    "_/ | \\_",
    "  |#|  ",
    "  | |  ",
    " _| |_ ",
]


def draw_river_mist(ch, co, v, walls, now, wet):
    """Mist lying on the water on a cold clear night.

    It sits on the surface and thickens away from you, so the far bank stands
    out of it rather than the whole river being fogged: drawn upward from the
    furthest water in each column, which is the one place mist reads as depth
    instead of as dirt on the screen. Rain kills it - you do not get both."""
    n = night(now)
    amount = (n["mist"] * n["clarity"] * max(0.0, 1.0 - wet * 4.0)
              * (0.0 if v.snow > 0.03 else 1.0))      # snow clears it too
    if amount < 0.12 or not v.water:
        return
    far = {}
    for y, sx in v.water:
        if sx not in far or y < far[sx]:
            far[sx] = y
    drift = int(now * 1.7)
    for sx, top in far.items():
        for k in range(int(1 + amount * 5)):
            y = top - k
            if y <= v.horizon or y >= v.height:
                continue
            if ch[y][sx] != " " and k:
                continue
            if _mix(sx + drift, y, 97) % 100 >= 74 - k * 13:
                continue
            ch[y][sx] = "-" if k else "~"
            co[y][sx] = HAZE


def quay_at(i, j):
    """Water, or the promenade - which on the docks' stretch is a quay, and
    a crane reaches over it to the water."""
    return river_at(i, j) or prom_at(i, j)


def near_dock_cranes(v, reach):
    """Docks lots standing on the quay, which is where a crane goes.

    Every one of them, with no extra thinning: the docks are 7% of the city and
    the river is a narrow band, so their overlap is already rare - one lot in
    thirteen hundred. Thin that again and there are no cranes at all."""
    n = int(reach / CELL) + 1
    ci = int(v.x / CELL + BIG) - BIG
    cj = int(v.z / CELL + BIG) - BIG
    for i in range(ci - n, ci + n + 1):
        # Only the rows either side of the channel: a crane is on the bank,
        # and scanning the whole square was a millisecond and a half a frame.
        lo, hi = river_span(i)
        j0 = max(cj - n, int(lo) - 2)
        j1 = min(cj + n, int(hi) + PROM_DEEP + 3)
        for j in range(j0, j1 + 1):
            if is_open(i, j):
                continue
            if DISTRICTS[district_at(i, j)]["name"] != "docks":
                continue
            if not any(quay_at(i + a, j + b)
                       for a, b in ((-1, 0), (1, 0), (0, -1), (0, 1))):
                continue
            rx = (i + 0.5) * CELL - v.x
            rz = (j + 0.5) * CELL - v.z
            if rx * v.dx + rz * v.dz < -CELL or rx * rx + rz * rz > reach * reach:
                continue
            yield i, j


def draw_dock_crane(ch, co, v, walls, i, j, now, wet):
    """A gantry over the quay: two legs, a beam, and a hoist that creeps along
    it. Slow enough that you only notice it has moved if you look twice."""
    x0 = (i + 0.5) * CELL
    z0 = (j + 0.5) * CELL
    b = lot(i, j)
    base = b["height"]
    m = _mix(i, j, 281)
    span = 4.0 + (m & 3)
    for leg in (-span, span):
        for h in range(11):
            put_point(ch, co, v, walls, x0 + leg, base + h * 1.2, z0, "#",
                      CONCRETE)
    top = base + 12.0
    for k in range(-int(span), int(span) + 1):
        put_point(ch, co, v, walls, x0 + k, top, z0, "=", CONCRETE)
    hoist = math.sin(now * 0.11 + (m >> 4 & 15)) * span
    for h in range(4):
        put_point(ch, co, v, walls, x0 + hoist, top - 1.0 - h * 1.1, z0, "|",
                  CURB)
    put_point(ch, co, v, walls, x0 + hoist, top - 5.2, z0, "H", CURB)
    if int(now * 0.8) % 2:
        put_lit(ch, co, v, walls, x0 + span, top + 0.9, z0, "*", EMBER_HOT,
                max(wet, 0.3), now)


def near_piers(v, reach):
    """Each pier in front of you, as (i at its middle, last plank)."""
    n = int(reach / CELL) + 1
    ci = int(v.x / CELL + BIG) - BIG
    seen = set()
    for i in range(ci - n, ci + n + 1):
        lo, hi = river_span(i)
        end = None
        for k in range(int(lo), int(lo) + PIER_LEN + 2):
            if pier_at(i, k):
                end = k
        if end is None:
            continue
        run = i - (i % PIER_WIDE)
        if run in seen:
            continue
        x = (run + PIER_WIDE * 0.5) * CELL
        z = (end + 0.5) * CELL
        rx, rz = x - v.x, z - v.z
        if rx * v.dx + rz * v.dz < -CELL or rx * rx + rz * rz > reach * reach:
            continue
        seen.add(run)
        yield run, end


def draw_pier(ch, co, v, walls, run, end, now, wet):
    """What is on a pier. Bollards down both sides, a lamp part way out,
    somebody fishing off the end, and a gull on a post.

    A pier with nothing on it reads as unfinished rather than quiet."""
    lo, _ = river_span(run)
    x0 = run * CELL
    for k in range(int(lo) + 1, end + 1):
        z = (k + 0.5) * CELL
        for side in (0.35, PIER_WIDE - 0.35):
            if _mix(run, k, 641) % 3:
                continue
            put_point(ch, co, v, walls, x0 + side * CELL, 0.45, z, "0", CURB)
        if k == int(lo) + 3:
            lx = x0 + PIER_WIDE * 0.5 * CELL
            for h in (0.8, 1.8, 2.8):
                put_point(ch, co, v, walls, lx, h, z, "|", CONCRETE)
            put_lit(ch, co, v, walls, lx, 3.5, z, "o", BULB, max(wet, 0.3), now)

    # The angler, at the very end, rod out over the water.
    ax = x0 + PIER_WIDE * 0.35 * CELL
    az = (end + 0.2) * CELL
    blit_sprite(ch, co, v, walls, ANGLER, ax, az, 0.05, 1.7, 0.85, CURB)
    put_point(ch, co, v, walls, ax + 2.6, 0.2, az - 1.4, ".", RAIN_FAR)

    # And a gull on the last bollard, which shuffles about but does not leave.
    gx = x0 + (PIER_WIDE - 0.35) * CELL
    gz = (end + 0.5) * CELL
    if int(now * 0.7) % 5:
        put_point(ch, co, v, walls, gx, 0.85, gz, "v", MOON)


def draw_gulls(ch, co, v, walls, now):
    """A few over the water, going round. They are the one thing out here that
    is neither on a clock nor standing still."""
    for k in range(5):
        m = _mix(k, 0, 863)
        r = 14.0 + (m & 15)
        a = now * (0.10 + (m >> 4 & 7) * 0.012) + (m >> 8 & 255) / 40.0
        i = int(v.x / CELL + BIG) - BIG
        cx = v.x + math.sin(a) * r
        cz = (river_centre(i) + 0.5) * CELL + math.cos(a) * r * 0.6
        y = 5.5 + (m >> 12 & 7) * 0.8 + math.sin(now * 0.8 + k) * 0.6
        put_point(ch, co, v, walls, cx, y, cz,
                  "v" if math.sin(now * 3.0 + k * 2.0) > 0 else "^", MOON_DIM)


def near_buoys(v, reach):
    """Channel markers, at fixed places along the river."""
    n = int(reach / CELL) + 1
    ci = int(v.x / CELL + BIG) - BIG
    for i in range(ci - n, ci + n + 1):
        if _mix(i // 4, 0, 331) % 9:
            continue
        lo, hi = river_span(i)
        m = _mix(i // 4, 1, 337)
        side = 0.28 if m & 1 else 0.72
        x = (i + 0.5) * CELL
        z = (lo + (hi - lo) * side) * CELL
        rx, rz = x - v.x, z - v.z
        if rx * v.dx + rz * v.dz < -CELL or rx * rx + rz * rz > reach * reach:
            continue
        yield x, z, m


def draw_buoy(ch, co, v, walls, x, z, m, now, wet):
    """A buoy, blinking on its own count.

    Deliberately not on any of the city's clocks and not on its neighbour's
    either: a row of lights in step reads as decoration, and the whole point of
    a channel marker is that it is not part of the town."""
    period = 2.2 + (m & 7) * 0.45
    lit = ((now + (m >> 4) % 100 / 13.0) % period) < 0.5
    bob = 0.12 * math.sin(now * 1.3 + (m >> 8 & 15))
    put_point(ch, co, v, walls, x, 0.35 + bob, z, "A", CURB)
    if lit:
        put_lit(ch, co, v, walls, x, 1.15 + bob, z, "o",
                ROU_GREEN if m & 1 else ROU_RED, max(wet, 0.45), now)
    else:
        put_point(ch, co, v, walls, x, 1.15 + bob, z, ".", CONCRETE)


def reflect_river(ch, co, v, walls, now, wet):
    """The far bank lying across the water.

    A planar mirror in one line: a facade point drawn at row r reflects to
    2*horizon - r, pushed down by twice the waterline offset for that
    building's distance. Falls straight out of the projection - the height that
    put a point at r puts its mirror image the same distance the other side of
    the horizon, and the eye being above the water rather than on it is the
    whole of the correction.

    Only the *lights* come across - windows, neon, bulbs - and never the walls,
    roofs and corners round them. Real water at night does exactly this: the
    structure of the far bank is black and what lies on the surface is its
    lit windows, smeared downwards. Mirroring every glyph gave a second,
    readable copy of the city under the first, which from a pier - where the
    water fills the bottom half of the screen - was most of what you saw.
    Below the first couple of rows the glyph gives way to ':', because a
    reflection that far out is a streak, not a letter.

    Only into cells the river was actually drawn into, so the reflection stops
    at the bank instead of running up the road."""
    if not v.water:
        return
    chop = int(now * 2.0)
    for sx in range(v.width):
        dist = walls[0][sx]
        if dist is None:
            dist = MAX_VIEW              # open sky over the water: still mirrors
        drop = 2.0 * v.eye * v.fy / dist
        top = max(0, walls[3][sx])
        for r in range(0, v.horizon):
            glyph = ch[r][sx]
            if glyph == " ":
                continue
            # Above the roofline it is sky, and anything in it is a light -
            # stars, the moon, whatever else is up there. On the facades only
            # the lights come across; and a canopy lit by the rig counts.
            if r >= top and not (glyph.isalnum() or glyph in "*+@"
                                 or (v.rave is not None
                                     and co[r][sx] == v.rave[0])):
                continue
            r2 = int(round(2 * v.horizon - r + drop))
            deep = r2 - v.horizon
            if deep < 1 or r2 >= v.height:
                continue
            if _mix(sx, r2, 61 + chop) % 100 >= 85 - deep * 6 - int(30 * wet):
                continue
            tx = sx + int(round(1.7 * math.sin(now * 1.1 + deep * 0.55)
                                + 1.3 * wet * math.sin(now * 3.7 + deep)))
            if (r2, tx) not in v.water:
                continue
            attr = co[r][sx] & ~curses.A_BOLD
            ch[r2][tx] = (glyph if deep <= 3 and r >= top
                          else ":" if glyph.isalnum() else glyph)
            co[r2][tx] = attr
            # And the streak under it. Lamplight on water is a smear, not a
            # dot, and the smear is what makes it read as a reflection.
            for tail in (1, 2, 3):
                ty = r2 + tail
                if (ty, tx) not in v.water or ch[ty][tx] not in " ~-":
                    break
                if _mix(tx, ty, 67 + chop) % 4 == 3:
                    break
                ch[ty][tx] = ":"
                co[ty][tx] = attr


MANHOLE_ODDS = 34      # one street cell in this many has a manhole in it
MANHOLE_R = 0.6        # the cover's radius
MANHOLE_ON = 2.0       # how near you have to be to lift it: a tap of w is 2.3


def manhole_at(i, j):
    """The manhole in this cell, if there is one: (x, z, steaming). Only in a
    proper street, never on a bridge or in the water, in the middle of the
    roadway - the hash first, since nearly every cell has none."""
    m = _mix(i, j, 3101)
    if m % MANHOLE_ODDS or not road_at(i, j) or not is_open(i, j) or water_at(i, j):
        return None
    x, z = (i + 0.5) * CELL, (j + 0.5) * CELL
    # Off the middle along the street, where there is street on both sides.
    shift = ((m >> 8) % 3 - 1) * 1.1
    if is_open(i - 1, j) and is_open(i + 1, j):
        x += shift
    elif is_open(i, j - 1) and is_open(i, j + 1):
        z += shift
    return x, z, (m >> 12) % 3 == 0


def manhole_under(x, z):
    """The manhole you are standing on, if you are."""
    for i in (int(x / CELL + BIG) - BIG,):
        for j in (int(z / CELL + BIG) - BIG,):
            for a in (i - 1, i, i + 1):
                for b in (j - 1, j, j + 1):
                    mh = manhole_at(a, b)
                    if mh and (mh[0] - x) ** 2 + (mh[1] - z) ** 2 < MANHOLE_ON ** 2:
                        return mh
    return None


def manhole_near(x, z, reach=4.0):
    ci, cj = int(x / CELL + BIG) - BIG, int(z / CELL + BIG) - BIG
    n = int(reach / CELL) + 1
    for a in range(ci - n, ci + n + 1):
        for b in range(cj - n, cj + n + 1):
            mh = manhole_at(a, b)
            if mh and (mh[0] - x) ** 2 + (mh[1] - z) ** 2 < reach * reach:
                return mh
    return None


def draw_manhole_steam(ch, co, v, walls, now):
    """Steam out of the covers that have it, curling up into the street
    light: puffs that grow and thin from white to haze as they rise."""
    n = 8
    ci, cj = int(v.x / CELL + BIG) - BIG, int(v.z / CELL + BIG) - BIG
    for i in range(ci - n, ci + n + 1):
        for j in range(cj - n, cj + n + 1):
            if _mix(i, j, 3101) % MANHOLE_ODDS:
                continue
            rx, rz = (i + 0.5) * CELL - v.x, (j + 0.5) * CELL - v.z
            if rx * v.dx + rz * v.dz < -CELL:
                continue
            mh = manhole_at(i, j)
            if mh is None or not mh[2]:
                continue
            seed = _mix(i, j, 3103)
            for k in range(9):
                age = (now * 0.3 + k / 9.0 + (seed % 7) * 0.1) % 1.0
                drift = 0.5 * math.sin(now * 0.4 + k * 1.3 + seed % 5) * age
                r = 0.15 + age * 0.7
                y = 0.15 + age * 4.2
                tone = SNOW if age < 0.25 else SMOKE if age < 0.6 else HAZE
                for da, dh, g in ((0.0, 0.0, "~"), (-r, 0.1, "("), (r, 0.1, ")")):
                    if age > 0.7 and g != "~":
                        continue
                    put_point(ch, co, v, walls, mh[0] + drift + da * v.plx,
                              y + dh * age, mh[1] + drift * 0.5 + da * v.plz, g, tone)


def draw_ground(ch, co, v, walls, glow, wet, now):
    """Road, pavement and kerb.

    Every screen row below the horizon is one fixed distance - the ground is a
    plane at y = 0 - so a row's world positions are a straight line from the
    left ray to the right one, and stepping along it costs an add per column."""
    width = v.width
    wall_base = walls[2]
    rdx0 = v.dx - v.plx
    rdz0 = v.dz - v.plz
    rdx1 = v.dx + v.plx
    rdz1 = v.dz + v.plz
    inv = 1.0 / CELL
    ripple = wet > 0.45
    # From a roof every row of ground on screen is further off than the street
    # ever needs - at seventy units up the nearest is a hundred away - so the
    # ground goes as far as the view does.
    far = GROUND_FAR if v.eye < 10.0 else v.reach

    for y in range(v.horizon + 1, v.height):
        d = v.eye * v.fy / (y - v.horizon)
        if d > far:
            continue
        wx = v.x + rdx0 * d
        wz = v.z + rdz0 * d
        stepx = (rdx1 - rdx0) * d / (width - 1)
        stepz = (rdz1 - rdz0) * d / (width - 1)
        li = lj = None
        solid = False
        x0 = y0 = 0.0

        for sx in range(width):
            x, z = wx, wz
            wx += stepx
            wz += stepz
            if y <= wall_base[sx]:
                continue
            i = int(x * inv + BIG) - BIG
            j = int(z * inv + BIG) - BIG
            if i != li or j != lj:
                li, lj = i, j
                solid = not is_open(i, j)
                x0, y0 = i * CELL, j * CELL
                # Which neighbours are walls, asked once per cell rather than
                # once per point: on open ground - the riverbank, a fairground
                # - the points outnumber the cells fifty to one, and this was
                # most of the frame.
                wall_w = not is_open(i - 1, j)
                wall_e = not is_open(i + 1, j)
                wall_n = not is_open(i, j - 1)
                wall_s = not is_open(i, j + 1)
                # Only the wider streets are marked, and never through a
                # junction - which is also how it works outside.
                wet_cell = water_at(i, j)
                deck = wet_cell and deck_at(i, j)
                pier = wet_cell and (pier_at(i, j) or fair_pier_at(i, j))
                woods = not wet_cell and woods_at(i, j)
                green = (not wet_cell and (woods or district(i, j)["park"])
                         and not road_at(i, j))
                trail = woods and trail_at(i, j)
                fair = (not wet_cell and not solid and not road_at(i, j)
                        and fair_at(i, j))
                rock = not wet_cell and not solid and headland_at(i, j)
                tarmac = not wet_cell and not solid and car_park_at(i, j)
                mh = None if solid or wet_cell else manhole_at(i, j)
                hollow = (woods and v.hollow is not None
                          and hollow_at(i, j))
                lane = None
                if not solid and not woods:
                    along_x = road_span(i, XP, 91)
                    along_z = road_span(j, ZP, 137)
                    if along_x and along_z:
                        lane = None
                    elif along_x and along_x[1] >= 3:
                        lane = (0, (along_x[0] + along_x[1] * 0.5) * CELL)
                    elif along_z and along_z[1] >= 3:
                        lane = (1, (along_z[0] + along_z[1] * 0.5) * CELL)
            if solid:
                continue

            # How far this point is from the nearest wall decides whether it is
            # pavement, the kerb line, or road.
            fx_ = x - x0
            fz_ = z - y0
            edge = 1e9
            if fx_ < PAVE and wall_w:
                edge = fx_
            elif CELL - fx_ < PAVE and wall_e:
                edge = CELL - fx_
            if fz_ < edge and fz_ < PAVE and wall_n:
                edge = fz_
            elif CELL - fz_ < edge and CELL - fz_ < PAVE and wall_s:
                edge = CELL - fz_

            if mh is not None:
                # The cover: a rim, and the grip pattern cast into it. Before
                # the snow, because what comes up from under it melts it.
                d2 = (x - mh[0]) ** 2 + (z - mh[1]) ** 2
                if d2 < MANHOLE_R * MANHOLE_R:
                    if d2 > (MANHOLE_R * 0.78) ** 2:
                        ch[y][sx], co[y][sx] = "o", CURB
                    elif (int((x - mh[0]) * 5.0 + 9) + int((z - mh[1]) * 5.0 + 9)) % 2:
                        ch[y][sx], co[y][sx] = "#", STREET
                    else:
                        ch[y][sx], co[y][sx] = "+", CURB
                    continue
            if (v.cover > 0.05 and not wet_cell and not deck and not tunnel_at(i, j)
                    and not (PAVE - 0.3 <= edge < PAVE)):
                # Snow lying, ahead of everything else the ground would draw:
                # it covers the bare road as well as the texture, by degrees
                # as it settles - all but the kerb line, which is how you
                # still tell the street from the pavement under it.
                h2 = _mix(int(x * 3.0), int(z * 3.0), 41) % 100
                if h2 < v.cover * 55:
                    ch[y][sx] = "." if h2 % 4 else "'"
                    co[y][sx] = SNOW
                    continue
            g = glow.get(((int(x / GLOW_CELL + BIG) - BIG) * 65536)
                         + (int(z / GLOW_CELL + BIG) - BIG))
            if deck:
                # A pier is planked across its width, so what you see is the
                # seam between one plank and the next, every so often, and
                # dark timber between them. Scattering random '=' over it
                # instead reads as noise, and at your feet - where one cell is
                # most of the screen - it was the loudest thing in the view.
                # A bridge is paved and gets the road's own grain.
                if pier:
                    if (z * 1.4) % 1.0 < 0.2:
                        glyph, attr = "-", CURB
                    elif _mix(int(x * 3.0), int(z * 3.0), 37) % 13 == 0:
                        glyph, attr = ".", STREET
                    else:
                        continue
                elif fx_ < 0.5 and not bridge_at(i - 1, j):
                    glyph, attr = "=", CURB            # the deck's kerb
                elif CELL - fx_ < 0.5 and not bridge_at(i + 1, j):
                    glyph, attr = "=", CURB
                elif _mix(int(x * 3.0), int(z * 3.0), 7) % 3 == 0:
                    glyph, attr = ".", CURB            # paving, not water
                else:
                    continue
            elif wet_cell:
                # Water. It moves along the channel, and it takes whatever the
                # city is putting out: the glow map is already worked out for
                # the wet road, and a river is wetter than any road.
                h = _mix(int(x * 2.0) - int(now * 1.6), int(z * 2.0), 29)
                v.water.add((y, sx))
                if g is not None and h % 3 == 0:
                    glyph, attr = ":", g
                elif h % 4 == 0:
                    glyph, attr = "~", RAIN_FAR
                elif h % 11 == 0:
                    glyph, attr = "-", STREET
                else:
                    continue
            elif hollow:
                # The rings. Light pulsing out across the ground from the
                # altar on every beat, which is the one thing in the city
                # meant to look like it is doing something to you.
                ax, az, beat, lamp = v.hollow
                dd = math.hypot(x - ax, z - az)
                if lamp is not None and (dd - beat * RING_GAP) % RING_GAP < 0.8:
                    glyph, attr = ":", lamp
                elif _mix(int(x * 3.0), int(z * 3.0), 23) % 5 == 0:
                    glyph, attr = ".", BARK               # trampled bare
                else:
                    continue
            elif trail:
                h = _mix(int(x * 3.0), int(z * 3.0), 23)
                if h % 4:
                    continue
                glyph, attr = ("." if h % 3 else ":"), CURB   # beaten earth
            elif fair:
                h = _mix(int(x * 3.0), int(z * 3.0), 23)
                if h % 5:
                    continue
                glyph, attr = ",", GOLD_DIM                   # sawdust
            elif tarmac:
                # Painted bays: a line between every one, a line across their
                # ends, and the aisle down the middle left bare.
                _, _, along = bay_of(x, z)
                in_bays = along < 5.0 or along > BAY_ROW - 5.0
                if in_bays and (x % PARK_BAY) < 0.2:
                    glyph, attr = "|", LANE
                elif abs(along - 5.0) < 0.15 or abs(along - (BAY_ROW - 5.0)) < 0.15:
                    glyph, attr = "-", LANE
                elif _mix(int(x * 3.0), int(z * 3.0), 47) % 11 == 0:
                    glyph, attr = ".", STREET               # the asphalt
                else:
                    continue
            elif rock:
                h = _mix(int(x * 3.0), int(z * 3.0), 23)
                if h % 6:
                    continue
                glyph, attr = ("^" if h % 5 == 0 else "."), CONCRETE
            elif green:
                h = _mix(int(x * 3.0), int(z * 3.0), 23)
                if h % 3:
                    continue
                glyph, attr = ('"' if h % 7 == 0 else ","), GRASS
            elif edge < PAVE - 0.3:
                if _mix(int(x * 3.0), int(z * 3.0), 11) & 3:
                    continue
                glyph, attr = ",", CURB
            elif edge < 1e8:
                glyph, attr = "=", CURB               # the kerb
            elif (lane is not None
                  and abs((x if lane[0] == 0 else z) - lane[1]) < 0.34
                  and int((z if lane[0] == 0 else x) / 3.0) % 2 == 0):
                glyph, attr = "'", LANE               # the line down the middle
            else:
                h = _mix(int(x * 3.0), int(z * 3.0), 7)
                if ripple and h & 31 == 0:
                    glyph, attr = "~", RAIN_FAR       # rain standing on the road
                elif h & 7:
                    continue
                else:
                    glyph, attr = ".", STREET
            if g is not None:
                attr = g
            if v.flash > 0.3 and _mix(int(x * 2.0), int(z * 2.0), 19) % 3 == 0:
                attr = FLASH
            ch[y][sx] = glyph
            co[y][sx] = attr


# ---------------------------------------------------------------------------
# Things standing in the street
#
# These are billboards: flat pictures kept facing you, scaled by distance and
# sampled nearest-neighbour into whatever screen rectangle they land in.
# ---------------------------------------------------------------------------

SMOKER_REST = [
    " ,-. ",
    "(- -)",
    " /|\\ ",
    " |#|\\",
    " / \\ ",
    "_| |_",
]

SMOKER_DRAG = [
    " ,-. ",
    "(- o)",
    " /|\\|",
    " |#| ",
    " / \\ ",
    "_| |_",
]

BIN = [
    "  ______  ",
    " /##  ##\\ ",
    " |##  ##| ",
    " |______| ",
]

RAVER_UP = [
    "\\,-./",
    " (-) ",
    " \\|/ ",
    "  |  ",
    " / \\ ",
    "_| |_",
]

RAVER_DOWN = [
    " ,-. ",
    " (-) ",
    "/ | \\",
    "  |  ",
    " / \\ ",
    "_| |_",
]

# Head back, hands down, not moving. Used by everyone on the pavement on the
# one night there is something to look at - it is the stillness that reads,
# more than the figure: a street where nobody is doing anything is a street
# where everybody is looking at the same thing.
# On the door of the club, arms folded, not dancing, not smoking, and not
# letting you in yet.
# On the casino's door: cap, braid, white gloves, and opening it for you.
DOORMAN = [
    "  _=_  ",
    "  (o)  ",
    " /[#]\\ ",
    " |[#]| ",
    "  | |  ",
    " _| |_ ",
]

PARTY_BOOTH = [
    "  _________  ",
    " |o  DJ   o| ",
    "[=====-=====]",
]

PARTY_STACK = [
    "[OO]",
    "[OO]",
    "[OO]",
    "[__]",
]

LIFT_HUT = [
    ".------.",
    "| LIFT |",
    "| [||] |",
    "|_[||]_|",
]

BOUNCER = [
    "  ,-.  ",
    " (-_-) ",
    "/=====\\",
    "|#|=|#|",
    " |   | ",
    " |_ _| ",
]

LOOK_UP = [
    " ,-. ",
    "(' ')",
    "  |  ",
    " /#\\ ",
    " | | ",
    "_| |_",
]

SMOKER_H = 1.9         # how tall he is, in world units
SMOKER_W = 0.79        # chosen so the art keeps its aspect ratio on screen

# --- the elevated line ---
# One avenue in EL_EVERY carries a steel viaduct down its middle: columns on
# both kerbs, a deck overhead, two tracks, and trains rattling along them
# with their windows lit. Position is a function of time, like everything
# that moves here. A station every so often, with a lit canopy.
EL_EVERY = 12          # avenues
EL_H = 6.4             # the deck's height, world units
EL_COL = 7.5           # between columns along the kerb
EL_SPEED = 13.0        # world units a second
EL_SPACING = 900.0     # between one train and the next on the same track
EL_CARS = 4
EL_CAR = 9.0           # one car's length
EL_STATION = 34        # cells between stations
EL_REACH = 120.0

# --- the highway ---
# Most of the traffic is not in town at all: it is up on an elevated highway
# that runs straight through, over one of the wide avenues in HWY_EVERY, on
# piers down the middle of it - over the river, over the woods, over
# everything, so it never has to stop at the water. Two lanes each way, cars
# close together and quick, a river of headlights one way and tail lights the
# other. Under it the pavement is yours.
HWY_EVERY = 7          # avenues (of which only the wide ones qualify)
HWY_H = 9.0            # the deck, above the El and the street lamps
HWY_SLOT = 11.0        # between slots on a lane
HWY_ODDS = 2           # one slot in this many has a car
HWY_PIER = 15.0        # between piers
HWY_LAMP = 30.0        # between the lamps along the median
HWY_REACH = 220.0

# People walking. A lane down each pavement of every street, slots along it
# sliding with time at the lane's pace, and one slot in a few has somebody
# in it - so nothing is stored, a walker is where they should be whether or
# not you were looking, and two on the same lane never walk through each
# other. Sparse on purpose: it is a city at night.
WALK_SLOT = 9.0        # world units between slots along a lane
WALK_REACH = 70.0      # how far off they are drawn
CROWDS = ["some", "busy", "none"]
_crowd = 0             # index into CROWDS, set from the cheat menu
CROWD_ODDS = {"some": 5, "busy": 2}      # one slot in this many is filled

WALKER_A = [
    " ,-. ",
    " (_) ",
    " /#\\ ",
    "/|#|\\",
    " / | ",
    "_|  \\",
]
WALKER_B = [
    " ,-. ",
    " (_) ",
    " /#\\ ",
    "/|#|\\",
    " | \\ ",
    " |_ \\",
]
UMBRELLA = [
    " .---. ",
    "/_____\\",
    "   |   ",
    "  (_)  ",
    "  /#|  ",
    "  |#|  ",
    "  / \\  ",
]


def put_cell(ch, co, v, walls, sx, sy, dist, glyph, attr):
    """One cell, if it is on the screen and no facade is in front of it - and,
    inside a tunnel, no ceiling either."""
    if not (0 <= sx < v.width and 0 <= sy < v.height):
        return
    if hidden(walls, sx, sy, dist):
        return
    if v.ceiling:
        cd = v.ceiling.get(sy * 4096 + sx)
        if cd is not None and cd < dist:
            return
    ch[sy][sx] = glyph
    co[sy][sx] = attr


def put_wide(ch, co, v, walls, sx, sy, dist, glyph, attr):
    """A double-width glyph, and the column it spills into.

    The cell to the right is claimed as well - blanked, and remembered in
    v.wide - because the blit loop writes left to right and would otherwise
    paint straight over the right half of the character."""
    if not (0 <= sx < v.width - 1 and 0 <= sy < v.height):
        return
    if hidden(walls, sx, sy, dist) or hidden(walls, sx + 1, sy, dist):
        return
    # Two signs can overlap on the same row. Whichever is drawn last is the
    # nearer one and should win, so clear anything already claiming these
    # columns - leaving it would put two double-width glyphs one column apart
    # and the blit loop would swallow the second one whole.
    for dx in (-1, 0, 1):
        at = sx + dx
        if at >= 0 and (sy, at) in v.wide:
            v.wide.discard((sy, at))
            ch[sy][at] = " "
    ch[sy][sx] = glyph
    co[sy][sx] = attr
    ch[sy][sx + 1] = " "
    v.wide.add((sy, sx))


def put_point(ch, co, v, walls, x, y, z, glyph, attr):
    pr = v.project(x, y, z)
    if pr is not None:
        put_cell(ch, co, v, walls,
                 int(round(pr[0])), int(round(pr[1])), pr[2], glyph, attr)


def put_lit(ch, co, v, walls, x, y, z, glyph, attr, wet, now):
    """A light, and its reflection in the wet road under it."""
    pr = v.project(x, y, z)
    if pr is None:
        return
    sx, sy, d = int(round(pr[0])), int(round(pr[1])), pr[2]
    put_cell(ch, co, v, walls, sx, sy, d, glyph, attr)
    if wet > 0.15:
        ry = v.reflect_row(y, d) + 1.5 * wet * math.sin(now * 2.7 + sx * 0.9)
        if _mix(sx, int(ry), int(now * 6.0)) % 5 < 1 + int(3 * wet):
            put_cell(ch, co, v, walls, sx, int(round(ry)), d, ":", attr)


SPRITE_NEAR = 0.7      # sprites are drawn until they are this close to your eyes


def blit_sprite(ch, co, v, walls, art, x, z, y_bot, y_top, w_world, colour):
    p_top = v.project(x, y_top, z)
    p_bot = v.project(x, y_bot, z)
    if p_top is None or p_bot is None:
        return
    dist = p_top[2]
    if dist < SPRITE_NEAR:
        # Close enough that you are standing in it. This was 1.6 for a long
        # time, on the theory that a six-row sprite blown up to forty rows was
        # porridge - and it is not: it is a big, perfectly readable figure, and
        # what was porridge was people and cars popping out of existence as
        # you walked up to them, which was reported as "things disappear when
        # I get close".
        return
    top, bot = p_top[1], p_bot[1]
    half = 0.5 * w_world * v.fx / dist
    left, right = p_top[0] - half, p_top[0] + half

    r0, r1 = max(0, int(top)), min(v.height - 1, int(math.ceil(bot)))
    c0, c1 = max(0, int(left)), min(v.width - 1, int(math.ceil(right)))
    if r1 < r0 or c1 < c0:
        return
    rows, cols = len(art), len(art[0])
    hspan = max(1e-6, bot - top)
    wspan = max(1e-6, right - left)

    for y in range(r0, r1 + 1):
        sr = int((y + 0.5 - top) / hspan * rows)
        if not 0 <= sr < rows:
            continue
        line = art[sr]
        for sx in range(c0, c1 + 1):
            sc = int((sx + 0.5 - left) / wspan * cols)
            if 0 <= sc < cols and line[sc] != " ":
                put_cell(ch, co, v, walls, sx, y, dist, line[sc], colour)


def draw_smoker(ch, co, v, walls, p, now, wet):
    t = (now + p["phase"]) % SMOKE_CYCLE
    dragging = t < DRAG_LEN
    x, _, z = p["world"]
    if night(now)["alien"]:
        # The cigarette can wait.
        blit_sprite(ch, co, v, walls, LOOK_UP, x, z, 0.05, SMOKER_H,
                    SMOKER_W, CURB)
        return
    blit_sprite(ch, co, v, walls,
                SMOKER_DRAG if dragging else SMOKER_REST,
                x, z, 0.05, SMOKER_H, SMOKER_W, CURB)

    # The ember is drawn as its own point rather than left to the sprite: it is
    # one cell, and it is the thing you can still pick out at the far end of
    # the street long after he has shrunk to a smudge.
    nx, nz = p["normal"]
    if dragging:
        ex, ez, ey = x + nx * 0.12, z + nz * 0.12, 1.62      # up at his mouth
    else:
        ex, ez, ey = x + nx * 0.5, z + nz * 0.5, 1.02        # down by his hip
    put_lit(ch, co, v, walls, ex, ey, ez, "o",
            EMBER_HOT if dragging else EMBER, wet, now)

    # Smoke. No state is kept: every puff's position is a function of how long
    # ago the drag it came from was.
    for k in range(7):
        age = t - DRAG_LEN - k * 0.3
        if not 0.0 < age < 2.8:
            continue
        drift = 0.12 + 0.15 * age
        wobble = 0.3 * math.sin(age * 1.7 + k)
        put_point(ch, co, v, walls,
                  x + nx * drift + nz * wobble, 1.7 + 0.55 * age,
                  z + nz * drift - nx * wobble,
                  ".oOo."[min(4, int(age / 0.6))], SMOKE)


def draw_raver(ch, co, v, walls, p, now, wet):
    """Someone outside the club with a glow stick in each hand.

    They are on the same clock as the sound system, so the whole pavement is
    dancing to the same beat and goes white together on the kick. The sticks
    are drawn as a short trail of their own past positions, which is the only
    way a single moving cell reads as a light rather than as a speck."""
    club = p["club"]
    t = now * CLUB_BPM / 60.0 + club["phase"]
    # All on the same beat, but not all on the same frame of it.
    up = (t + p["swing"] * 0.18) % 1.0 < 0.5
    lamp = club_light(now, club)
    x, _, z = p["world"]
    if night(now)["alien"]:
        # Even the queue stops dancing for this.
        blit_sprite(ch, co, v, walls, LOOK_UP, x, z, 0.05, SMOKER_H,
                    SMOKER_W, lamp if lamp is not None else CURB)
        return
    blit_sprite(ch, co, v, walls, RAVER_UP if up else RAVER_DOWN,
                x, z, 0.05, SMOKER_H, SMOKER_W,
                lamp if lamp is not None else CURB)

    lit, dark = NEON[min(len(NEON) - 1, int(p["tone"] * len(NEON)))]
    tx, tz = p["tangent"]
    for hand in (0, math.pi):
        for m in range(3):
            a = (t + p["swing"]) * math.pi - m * 0.24 + hand
            off = 0.44 * math.sin(a)
            y = 1.5 + (0.42 if up else 0.0) + 0.34 * math.cos(a)
            put_point(ch, co, v, walls, x + tx * off, y, z + tz * off,
                      "*o."[m], lit if m == 0 else dark)


def draw_diner_column(ch, co, v, sx, dist, b, face, u, r_lo, r_hi, edge,
                      cont, now):
    """One column of the diner: gunmetal, and seamed with neon.

    A cyan seam up every corner, a magenta strip under the roof, and over the
    shopfront a cyan band with a bright packet running along it now and then,
    like data down a line. Upstairs is dark panelling with a small purple
    window in each bay. The long window itself is diner_window()'s, drawn
    over the ground floor of the front afterwards."""
    scale = v.fy / dist
    dn = b["diner"]
    cyan, magenta, purple = NEON[2], NEON[1], NEON[6]
    roof = int(round(v.horizon - (b["height"] - v.eye) * scale))
    foot = int(round(v.horizon + v.eye * scale))
    if edge:
        for y in range(r_lo, r_hi + 1):
            ch[y][sx], co[y][sx] = "|", FLASH if v.flash > 0.35 else cyan[0]
        return roof, None, foot, None, ()
    prev_roof, prev_awn, prev_foot = cont[:3]
    awning = int(round(v.horizon - (FLOOR_H * 1.2 - v.eye) * scale))
    strip = int(round(v.horizon - (b["height"] - 0.35 - v.eye) * scale))
    facade_line(ch, co, sx, roof, prev_roof, r_lo, r_hi, "=",
                roof_colour(b, dist, v.flash, v.cover))
    if r_lo <= strip <= r_hi and strip > roof:
        ch[strip][sx], co[strip][sx] = "-", magenta[0]
    packet = (u + face * CELL - now * 9.0 - dn["seed"]) % 23.0 < 1.2
    facade_line(ch, co, sx, awning, prev_awn, r_lo, r_hi, "=",
                FLASH if packet else cyan[0])
    # Upstairs: panel seams every other row, and a window in each bay.
    bay = u / BAY_W - int(u / BAY_W)
    top = max(r_lo, roof + 1, strip + 1)
    for y in range(top, min(r_hi, awning - 1) + 1):
        if 0.35 < bay < 0.65 and (y - top) % 3 == 1:
            ch[y][sx], co[y][sx] = "#", purple[0 if int(now * 0.7 + u) % 9 else 1]
        elif (y + sx) % 4 == 0:
            ch[y][sx], co[y][sx] = ".", CONCRETE
    # Round the sides, the ground floor is dark glass with the seam's glow.
    if face != dn["door"]:
        for y in range(max(r_lo, awning + 1), min(r_hi, foot - 1) + 1):
            if (y + sx) % 3 == 0:
                ch[y][sx], co[y][sx] = ":", cyan[1]
    facade_line(ch, co, sx, foot, prev_foot, r_lo, r_hi, "_", CURB)
    return roof, awning, foot, None, ()


def diner_window(ch, co, v, sx, dist, u, f, r_lo, r_hi, b):
    """The diner's front from the street: the whole ground floor one long
    window, lit cold from inside and lined like a screen, the counter across
    it and three people sat at it well apart, dark against the light - and
    one of them with a red light where an eye would be."""
    scale = v.fy / dist
    top = int(round(v.horizon - (FLOOR_H * 1.15 - v.eye) * scale))
    sill = int(round(v.horizon - (0.6 - v.eye) * scale))
    bar = int(round(v.horizon - (1.05 - v.eye) * scale))
    light = tone_colour("cold", 0.9)
    dim = tone_colour("cold", 0.4)
    su = sign_u(f, u)
    sitters = (0.9, 2.6, 4.3)
    near_one = min(abs(su - s) for s in sitters)
    cols = 0.5 * v.fx / dist                    # how many columns a person is
    head = bar - max(1, int(round(0.45 * scale)))
    for y in range(max(r_lo, top), min(r_hi, sill) + 1):
        if y == top or y == sill:
            g, a = "=", NEON[1][0]              # the frame, in magenta tube
        elif y == bar:
            g, a = "=", CONCRETE                # the counter, chrome
        elif y < bar and near_one < 0.25 * max(1.0, 1.0 / max(cols, 1e-6)) and \
                y >= bar - max(1, int(round(0.7 * scale))):
            g, a = ("o" if y < head else "M"), BARK
            if y < head and abs(su - sitters[1]) < 0.3:
                a = ROU_RED                     # the one with the eye
        else:
            g, a = (":", light) if (y - top) % 2 else (".", dim)
        ch[y][sx], co[y][sx] = g, a


def draw_diner_sign(ch, co, v, walls, dn, world, now):
    """The name over the window in cyan, OPEN 24/7 under it - in screen space,
    like the cinema's, so it can be read. Every few seconds the sign glitches:
    the name jumps a column, its letters go to noise in magenta for a frame or
    two, and comes back."""
    pr = v.project(world[0], world[1], world[2])
    if pr is None or pr[2] > 80.0:
        return
    sx, sy, dist = int(round(pr[0])), int(round(pr[1])), pr[2]
    name = "[ %s ]" % dn["name"]
    t = (now + dn["seed"] * 0.01) % 5.0
    glitch = t < 0.18
    jump = (1 if int(now * 30) % 2 else -1) if glitch else 0
    for k, c in enumerate(name):
        m = _mix(k, int(now * 20), dn["seed"])
        noise = glitch and m % 3 == 0 and c not in " []"
        put_cell(ch, co, v, walls, sx - len(name) // 2 + k + jump, sy, dist,
                 "#%/=?"[m % 5] if noise else c,
                 NEON[1][0] if noise else NEON[2][0])
    under = "OPEN 24/7"
    for k, c in enumerate(under):
        lit = k >= 5 or int(now * 1.2) % 3
        put_cell(ch, co, v, walls, sx - len(under) // 2 + k, sy + 1, dist, c,
                 (NEON[5][0] if k < 4 else NEON[6][0]) if lit else NEON[5][1])


_diner_blocks = {}


def diners_in_block(bi, bj):
    """The diners in city block (bi, bj), worked out once: the cup on the
    roof is seen from blocks away, like the cinema's searchlights."""
    key = (bi, bj)
    hit = _diner_blocks.get(key)
    if hit is None:
        _evict(_diner_blocks, 4000)
        hit = []
        for i in range(bi * XP, bi * XP + XP):
            for j in range(bj * ZP, bj * ZP + ZP):
                if _mix(i, j, 2401) % DINER_ODDS or is_open(i, j):
                    continue
                dn = lot(i, j)["diner"]
                if dn is not None:
                    hit.append(dn)
        _diner_blocks[key] = hit
    return hit


def near_diners(v, reach):
    b0, b1 = int((v.x - reach) // (XP * CELL)), int((v.x + reach) // (XP * CELL))
    c0, c1 = int((v.z - reach) // (ZP * CELL)), int((v.z + reach) // (ZP * CELL))
    for bi in range(b0, b1 + 1):
        for bj in range(c0, c1 + 1):
            for dn in diners_in_block(bi, bj):
                rx = (dn["i"] + 0.5) * CELL - v.x
                rz = (dn["j"] + 0.5) * CELL - v.z
                if rx * v.dx + rz * v.dz < -CELL or rx * rx + rz * rz > reach * reach:
                    continue
                yield dn


def draw_tube(ch, co, v, walls, pts, attr):
    """A neon tube through world points, each cell's glyph taken from which
    way the tube runs on screen there - the searchlights' trick - so a curve
    reads as a curve and not as a row of dots."""
    prev = None
    for x, y, z in pts:
        pr = v.project(x, y, z)
        if pr is not None and prev is not None:
            ax, ay = pr[0] - prev[0], (pr[1] - prev[1]) * 2.0
            if abs(ax) + abs(ay) > 1e-6:
                glyph = ("|" if abs(ax) < 0.4 * abs(ay) else
                         "-" if abs(ay) < 0.4 * abs(ax) else
                         "/" if ax * ay < 0 else "\\")
                put_cell(ch, co, v, walls, int(round(pr[0])), int(round(pr[1])),
                         pr[2], glyph, attr)
        prev = pr


def cup_shape():
    """The cup, in the sign's own (across, up) units: a tapering body, a
    handle, a saucer with its ends turned up, and the coffee in it. Each is a
    list of points along the tube, close enough to join up from across the
    street."""
    def line(a0, h0, a1, h1, n):
        return [(a0 + (a1 - a0) * k / n, h0 + (h1 - h0) * k / n) for k in range(n + 1)]
    body = (line(-1.7, 3.0, -1.25, 0.7, 14) + line(-1.25, 0.7, 1.25, 0.7, 16)
            + line(1.25, 0.7, 1.7, 3.0, 14) + line(1.7, 3.0, -1.7, 3.0, 20))
    handle = [(1.6 + 0.75 * math.cos(a), 1.9 + 0.62 * math.sin(a))
              for a in [-math.pi / 2 + math.pi * k / 16 for k in range(17)]]
    saucer = (line(-2.5, 0.65, -2.1, 0.35, 4) + line(-2.1, 0.35, 2.1, 0.35, 24)
              + line(2.1, 0.35, 2.5, 0.65, 4))
    coffee = line(-1.35, 2.35, 1.35, 2.35, 14)
    return body, handle, saucer, coffee


_CUP = cup_shape()


def draw_diner_cup(ch, co, v, walls, dn, now):
    """The cup on the roof: a coffee cup in neon tube, on a saucer, standing
    up off the front edge of the roof facing the street, with three strands
    of neon steam rising off it in pulses. Every so often the tube flickers
    the way cheap neon does. All world points, so it stands on the roof and
    the buildings in between hide it."""
    i, j, f = dn["i"], dn["j"], dn["door"]
    base = dn["height"] + 0.25

    def world(a, h):
        return face_point(i, j, f, CELL * 0.5 + a * CUP_SCALE, -0.4,
                          base + h * CUP_SCALE)

    t = (now + dn["seed"] * 0.37) % CUP_GLITCH
    flicker = t < 0.25 and int(now * 25) % 2 == 0
    cyan, magenta = NEON[2], NEON[1]
    body, handle, saucer, coffee = _CUP
    tube = cyan[1] if flicker else cyan[0]
    # Dark inside the cup first, or the facade of whatever stands behind it
    # shows through the tube and the outline is lost in it.
    h = 0.75
    while h < 2.95:
        half = 1.25 + (h - 0.7) / 2.3 * 0.45 - 0.1
        a = -half
        while a <= half:
            pr = v.project(*world(a, h))
            if pr is not None:
                put_cell(ch, co, v, walls, int(round(pr[0])), int(round(pr[1])),
                         pr[2], " ", tube)
            a += 0.12
        h += 0.12
    for path in (body, handle, saucer):
        draw_tube(ch, co, v, walls, [world(a, h) for a, h in path], tube)
    draw_tube(ch, co, v, walls, [world(a, h) for a, h in coffee], EMBER_HOT)
    # The steam: three strands curling up, lit in pulses that climb them.
    for k, a0 in enumerate((-0.8, 0.0, 0.8)):
        pts = []
        h = 3.3
        while h < 6.0:
            # Curling, and drifting off to one side as it goes up.
            a = (a0 + 0.45 * math.sin(h * 1.7 - now * 2.2 + k * 2.1)
                 + 0.35 * (h - 3.3))
            on = (h - now * 1.3 + k * 0.9) % 1.5 < 0.9
            pts.append((world(a, h), on, h))
            h += 0.1
        run = []
        for w, on, h in pts:
            if on:
                run.append(w)
                continue
            if len(run) > 1:
                draw_tube(ch, co, v, walls, run,
                          magenta[0] if h < 5.4 and not flicker else magenta[1])
            run = []
        if len(run) > 1:
            draw_tube(ch, co, v, walls, run, magenta[1])


def near_billboards(v, reach):
    """Billboards in reach, by city block, worked out once a block - the way
    the sky decks' beacons are, for the same reason."""
    b0, b1 = int((v.x - reach) // (XP * CELL)), int((v.x + reach) // (XP * CELL))
    c0, c1 = int((v.z - reach) // (ZP * CELL)), int((v.z + reach) // (ZP * CELL))
    for bi in range(b0, b1 + 1):
        for bj in range(c0, c1 + 1):
            for bb in bills_in_block(bi, bj):
                rx = (bb["i"] + 0.5) * CELL - v.x
                rz = (bb["j"] + 0.5) * CELL - v.z
                if rx * rx + rz * rz < reach * reach:
                    yield bb


_bill_blocks = {}


def bills_in_block(bi, bj):
    key = (bi, bj)
    hit = _bill_blocks.get(key)
    if hit is None:
        _evict(_bill_blocks, 4000)
        hit = []
        for i in range(bi * XP, bi * XP + XP):
            for j in range(bj * ZP, bj * ZP + ZP):
                if _mix(i, j, 2405) % BILL_ODDS or is_open(i, j):
                    continue
                bb = lot(i, j)["billboard"]
                if bb is not None:
                    hit.append(bb)
        _bill_blocks[key] = hit
    return hit


def draw_billboard(ch, co, v, walls, bb, now, wet):
    """A soda ad hung out over the street from a roof, facing the traffic.

    It stands out from the roof edge at right angles to the frontage, across
    the road like a gantry board, so it has a face to each end of the street
    and is read from down the street. Where it is, how big, and what is in
    front of it are all worked out in the world - its corners projected, the
    depth checked per column - but the lettering is laid out in screen space
    across what those corners cover, like the cinema's and the diner's signs.
    Each letter a point on the board's plane looked right and could not be
    read: from any way back the brand and the slogan landed on the same rows
    and overwrote each other. The brand in neon, the slogan under it if there
    is room, bubbles going up the sides, and lamps along the bottom."""
    i, j, f = bb["i"], bb["j"], bb["face"]
    nx, nz = FACES[f]
    tx, tz = -nz, nx                             # along the street
    mx, _, mz = face_point(i, j, f, CELL * 0.5, 0.0, 0.0)
    if abs((v.x - mx) * tx + (v.z - mz) * tz) < 1.0:
        return                                   # edge on: nothing to read
    base = bb["height"] + 0.8
    top = base + BILL_ROW * 5
    ends = []
    for out in (0.6, 0.6 + BILL_W):              # out over the street
        lo = v.project(mx + nx * out, base, mz + nz * out)
        hi = v.project(mx + nx * out, top, mz + nz * out)
        if lo is None or hi is None:
            return
        ends.append((lo, hi))
    (la, ha), (lb, hb) = ends
    if la[0] > lb[0]:
        (la, ha), (lb, hb) = (lb, hb), (la, ha)
    x0, x1 = int(round(la[0])), int(round(lb[0]))
    y0 = int(round(min(ha[1], hb[1])))
    y1 = int(round(max(la[1], lb[1])))
    w, h = x1 - x0 + 1, y1 - y0 + 1
    words = bb["words"]
    if w < 6 or h < 2 or w > v.width * 2:
        return
    lit, dark = NEON[bb["tone"] % len(NEON)]
    second = NEON[(bb["tone"] + 4) % len(NEON)][0]
    flick = int(now * 0.7 + i) % 9 != 0           # the brand dips now and then
    brand = words[0] if len(words[0]) + 2 <= w else words[0][:w - 2]
    slogan = words[1][:w - 2]
    mid = y0 + h // 2
    rows = {mid - (1 if h >= 4 else 0): (brand, lit if flick else dark)}
    if h >= 4:
        rows[mid + (1 if h >= 6 else 0)] = (slogan, second)
    for sx in range(max(0, x0), min(v.width - 1, x1) + 1):
        frac = (sx - x0) / max(1, x1 - x0)
        dist = la[2] + (lb[2] - la[2]) * frac
        for sy in range(max(0, y0), min(v.height - 1, y1) + 1):
            edge_x, edge_y = sx in (x0, x1), sy in (y0, y1)
            if edge_x and edge_y:
                g = "." if sy == y0 else "'"
            elif edge_y:
                g = "-"
            elif edge_x:
                g = "|"
            else:
                g, line = " ", rows.get(sy)
                if line is not None:
                    text, attr = line
                    k = sx - (x0 + 1) - (w - 2 - len(text)) // 2
                    if 0 <= k < len(text):
                        g = text[k]
                side_col = sx - x0 in (2, 3) or x1 - sx in (2, 3)
                if g == " " and sy not in rows and side_col \
                        and int(now * 3.0 - sy + sx) % 4 == 0:
                    g, attr = "o", second       # bubbles, rising
                if g == " ":
                    # The board is solid: blank it, or the city shows through.
                    if not hidden(walls, sx, sy, dist):
                        ch[sy][sx], co[sy][sx] = " ", 0
                    continue
                put_cell(ch, co, v, walls, sx, sy, dist, g, attr)
                continue
            put_cell(ch, co, v, walls, sx, sy, dist, g, CONCRETE)
    for k in range(5):                             # lamps shining up at it
        out = 0.6 + BILL_W * (k + 0.5) / 5.0
        put_lit(ch, co, v, walls, mx + nx * out, base - 0.4, mz + nz * out,
                "o", BULB, max(wet, 0.3), now)
    for out in (0.6, 0.6 + BILL_W * 0.5):          # the brackets
        put_point(ch, co, v, walls, mx + nx * out, bb["height"] + 0.3,
                  mz + nz * out, "/", CONCRETE)


def _title_lines(title, room):
    """The title in as few lines of the big font as fit in room columns: one,
    or two broken at the space nearest the middle. None if it will not go."""
    if big_width(title) <= room:
        return [title]
    gaps = [k for k, c in enumerate(title) if c == " "]
    if not gaps:
        return None
    k = min(gaps, key=lambda g: abs(g - len(title) / 2.0))
    lines = [title[:k], title[k + 1:]]
    return lines if max(big_width(t) for t in lines) <= room else None


def draw_cinema_front(ch, co, v, walls, cin, world, now):
    """The title in lights over the doors, ringed with chasing bulbs, and the
    lit doors under it.

    Near enough to read it, the title goes up in the big font, the way it is
    on the front of a real one - the whole point of a cinema front is the name
    of the film, and in a row of ordinary letters it was a line of print over
    a door. Further off, NOW SHOWING and the title in a box the old size.
    Both are in screen space for the casino marquee's reason: unreadable is
    worse than the wrong size."""
    pr = v.project(world[0], world[1], world[2])
    if pr is None or pr[2] > 70.0:
        return
    sx, sy, dist = int(round(pr[0])), int(round(pr[1])), pr[2]
    lines = _title_lines(cin["title"], v.width - 8) if dist < CINEMA_BIG else None
    if lines is None:
        small = ["NOW SHOWING", cin["title"]]
        w = max(len(t) for t in small) + 4
        x0, y0 = sx - w // 2, sy - 2
        rows = [(r, t, GOLD_DIM if r == 0 else FLASH) for r, t in enumerate(small)]
        height = 2
    else:
        w = max(big_width(t) for t in lines) + 4
        height = 1 + len(lines) * 6
        x0, y0 = sx - w // 2, sy + 1 - (height + 1)
        rows = [(0, "NOW SHOWING", GOLD)]
    # The ring of bulbs, chasing round.
    for k in range(w):
        for y in (y0, y0 + height + 1):
            lit = chase(k * 0.6 + (y - y0), now)
            put_cell(ch, co, v, walls, x0 + k, y, dist, "o" if lit else ".",
                     GOLD if lit else GOLD_DIM)
    for r in range(1, height + 1):
        for x in (x0, x0 + w - 1):
            lit = chase(r * 0.6 + x - x0, now)
            put_cell(ch, co, v, walls, x, y0 + r, dist, "o" if lit else ".",
                     GOLD if lit else GOLD_DIM)
        for x in range(x0 + 1, x0 + w - 1):         # a dark board behind it
            put_cell(ch, co, v, walls, x, y0 + r, dist, " ", GOLD_DIM)
    for r, t, attr in rows:
        for k, c in enumerate(t.center(w - 2)):
            put_cell(ch, co, v, walls, x0 + 1 + k, y0 + 1 + r, dist, c, attr)
    if lines is not None:
        for n, t in enumerate(lines):
            lx = sx - big_width(t) // 2
            for dx, dy, _ in big_cells(t):
                put_cell(ch, co, v, walls, lx + dx, y0 + 2 + n * 6 + dy, dist,
                         "#", FLASH)
    blit_sprite(ch, co, v, walls, ["[|][|]", "[|][|]", "[|][|]"], world[0],
                world[2], 0.0, 2.4, 2.4, BULB)


def arcade_letter(arc, k, now):
    """The colour of the k-th letter of ARCADE this instant. Every few seconds
    the sign runs its routine: dark, the letters coming on one at a time, the
    whole word flashing, then each letter in its own colour, turning slowly."""
    n = len(NEON)
    t = (now + arc["seed"] * 0.01) % 5.0
    if t < 0.15 * 6:
        return NEON[k % n][0] if k < int(t / 0.15) else NEON[k % n][1]
    if t < 0.9 + 0.9:
        return FLASH if int((t - 0.9) / 0.15) % 2 == 0 else NEON[k % n][1]
    return NEON[(k + int(now * 1.5)) % n][0]


def draw_arcade_front(ch, co, v, walls, arc, world, now):
    """ARCADE over the door, on a dark board ringed with bulbs in every colour
    - in the big font when you are near enough to take it in, the letters
    going through arcade_letter()'s routine - the arcade's name under it, and
    INSERT COIN blinking over the door. Screen space, for the casino marquee's
    reason. The board is blanked first: on a wall of coloured panes, letters
    made of the same blocks would be lost."""
    pr = v.project(world[0], world[1], world[2])
    if pr is None or pr[2] > 80.0:
        return
    sx, sy, dist = int(round(pr[0])), int(round(pr[1])), pr[2]
    n = len(NEON)
    big = dist < ARCADE_BIG and big_width("ARCADE") + 6 <= v.width
    w = (big_width("ARCADE") if big else len("ARCADE")) + 6
    w = max(w, len(arc["name"]) + 4)
    rows = 7 if big else 3
    x0, y0 = sx - w // 2, sy - rows
    for r in range(rows + 1):
        for x in range(x0, x0 + w):
            ring = r in (0, rows) or x in (x0, x0 + w - 1)
            if ring:
                lit = chase((x - x0 + r) * 0.4, now)
                put_cell(ch, co, v, walls, x, y0 + r, dist, "o" if lit else ".",
                         NEON[(x - x0 + r + int(now * 4.0)) % n][0 if lit else 1])
            else:
                put_cell(ch, co, v, walls, x, y0 + r, dist, " ", GOLD_DIM)
    if big:
        lx = sx - big_width("ARCADE") // 2
        for dx, dy, k in big_cells("ARCADE"):
            put_cell(ch, co, v, walls, lx + dx, y0 + 1 + dy, dist, "#",
                     arcade_letter(arc, k, now))
    else:
        for k, c in enumerate("ARCADE"):
            put_cell(ch, co, v, walls, sx - 3 + k, y0 + 1, dist, c,
                     arcade_letter(arc, k, now))
    name = arc["name"]
    for k, c in enumerate(name):
        put_cell(ch, co, v, walls, sx - len(name) // 2 + k, y0 + rows - 1, dist, c,
                 GOLD)
    door = v.project(*face_point(arc["i"], arc["j"], arc["door"], arc["u"], 0.5,
                                 FLOOR_H - 0.1))
    if door is not None and int(now * 1.6) % 2 == 0:
        word = "INSERT COIN"
        for k, c in enumerate(word):
            put_cell(ch, co, v, walls, int(round(door[0])) - len(word) // 2 + k,
                     int(round(door[1])), door[2], c, FLASH)


_jackpot = None         # (when, i, j) of the last 777, and whose machine it was


def hit_jackpot(now, cas):
    """777 on a slot: the casino it was in goes up in gold for JACKPOT_LONG."""
    global _jackpot
    _jackpot = (now, cas["i"], cas["j"])


def jackpot_on(now, cas):
    """Is this casino celebrating."""
    return (_jackpot is not None and cas.get("i") == _jackpot[1]
            and cas.get("j") == _jackpot[2] and 0.0 <= now - _jackpot[0] < JACKPOT_LONG)


def draw_blade(ch, co, v, walls, cas, i, j, f, now):
    """The casino's name up the corner of the building on a blade sign, the
    old Las Vegas way: a tall panel standing out from the wall at right
    angles, the letters stacked top to bottom, bulbs chasing down both edges.
    It runs from over the canopy to above the roofline.

    Its two edges are projected from the world like a hung sign's, so it
    stands out of the wall and foreshortens as you walk - edge-on from
    straight across the road, open as you come down the street, which is
    when a blade is meant to be read and when the marquee over the door is
    hardest to. The letters are in screen rows, between where its top and
    bottom are on screen - and if the top is over the top of the screen, they
    close up to fit under it: from across a narrow street a blade's upper
    half is out of sight, and the name with its first letters gone is worse
    than the name a little squeezed.

    The letters light one at a time from the top down, the whole name
    flashes, and then it holds in its own colour - and on a jackpot it is
    all gold and flashing for as long as the building is."""
    lit, dark = NEON[min(len(NEON) - 1, int(cas["sign_tone"] * len(NEON)))]
    name = cas["name"]
    top_y, foot_y = cas["height"] + BLADE_RISE, FLOOR_H + 1.0
    nx, nz = FACES[f]
    edges = []
    for out in (BLADE_OUT - BLADE_HALF, BLADE_OUT + BLADE_HALF):
        pt = v.project(*face_point(i, j, f, BLADE_U, out, top_y))
        pb = v.project(*face_point(i, j, f, BLADE_U, out, foot_y))
        if pt is None or pb is None:
            return
        edges.append((pt[0], pt[1], pb[0], pb[1], (pt[2] + pb[2]) * 0.5))
    dist = min(e[4] for e in edges)
    if dist > 120.0:
        return
    party = jackpot_on(now, cas)
    # The edges: lines of bulbs chasing downwards, unless edge-on.
    cols = [int(round((e[0] + e[2]) * 0.5)) for e in edges]
    open_ = abs(cols[0] - cols[1]) > 2
    y0 = int(round(min(e[1] for e in edges)))
    y1 = int(round(max(e[3] for e in edges)))
    if open_:
        a, b = sorted(cols)
        for y in range(max(0, y0), min(v.height, y1 + 1)):
            for x in range(a + 1, b):                  # a dark board behind
                put_cell(ch, co, v, walls, x, y, dist, " ", GOLD_DIM)
            for x in (a, b):
                on = (y - int(now * 14.0)) % 3 == 0
                put_cell(ch, co, v, walls, x, y, dist, "o" if on else ".",
                         (FLASH if int(now * 8) % 2 else GOLD) if party
                         else (GOLD if on else GOLD_DIM))
    # The letters, top to bottom, between the board's top and its foot -
    # closed up under the top of the screen when its top is above it.
    first, last = max(1, y0 + 1), y1 - 1
    if last - first < len(name) - 1:
        return
    mid = (cols[0] + cols[1]) // 2
    t = (now + cas["phase"]) % 5.0

    def colour(k):
        if party:
            return FLASH if int(now * 8 + k) % 2 else GOLD
        if t < 0.25 * len(name):
            return lit if k <= int(t / 0.25) else dark
        if t < 0.25 * len(name) + 1.2:
            return FLASH if int((t - 0.25 * len(name)) / 0.2) % 2 == 0 else lit
        return lit
    # The letters spread down the whole board - in the big font when it is
    # wide enough and tall enough to take them, which it is from down the
    # street, and in plain letters otherwise.
    if open_ and abs(cols[0] - cols[1]) >= 5 and last - first + 1 >= len(name) * 6 - 1:
        step = (last - first + 2 - 5) / max(1, len(name) - 1) if len(name) > 1 else 0
        for dx, dy, k in big_cells(name):
            cx, row = dx - k * 4, dy                   # the letter's own cell
            put_cell(ch, co, v, walls, mid - 1 + cx, int(round(first + k * step)) + row,
                     dist, "#", colour(k))
        return
    step = (last - first) / max(1, len(name) - 1) if len(name) > 1 else 0
    for k, c in enumerate(name):
        put_cell(ch, co, v, walls, mid, int(round(first + k * step)), dist, c,
                 colour(k))


def draw_red_carpet(ch, co, v, walls, cas, i, j, f, now):
    """A red carpet from the casino's door to the kerb, brass posts down both
    sides of it with a red rope slung between them."""
    u = cas["u"]
    out = 0.1
    while out < PAVE - 0.05:
        w = -CARPET_HALF
        while w <= CARPET_HALF:
            put_point(ch, co, v, walls, *face_point(i, j, f, u + w, out, 0.03), "=",
                      ROU_RED)
            w += 0.22
        out += 0.3
    for side in (-1.0, 1.0):
        su = u + side * (CARPET_HALF + 0.25)
        posts = (0.5, PAVE - 0.15)
        for po in posts:
            for y in (0.25, 0.55):
                put_point(ch, co, v, walls, *face_point(i, j, f, su, po, y), "|",
                          GOLD_DIM)
            put_point(ch, co, v, walls, *face_point(i, j, f, su, po, 0.9), "o", GOLD)
        for n in range(1, 5):
            t = n / 5.0
            put_point(ch, co, v, walls,
                      *face_point(i, j, f, su, posts[0] + (posts[1] - posts[0]) * t,
                                  0.82 - 0.16 * math.sin(math.pi * t)),
                      "~", ROU_RED)


def draw_marquee(ch, co, v, walls, cas, world, now):
    """The word, in lights, across the front of a casino.

    Laid out in screen space with the letters side by side. A marquee that
    shrank with distance is a smear long before you can stand far enough back
    to see the whole building - and on a fifteen-foot street you never can - so
    this one is a stylised fixed size. Unreadable is worse than the wrong size,
    which is the same call the hung signs make about their rows."""
    pr = v.project(world[0], world[1], world[2])
    if pr is None:
        return
    sx, sy, dist = int(round(pr[0])), int(round(pr[1])), pr[2]
    neon = NEON[min(len(NEON) - 1, int(cas["sign_tone"] * len(NEON)))][0]
    if jackpot_on(now, cas):
        neon = FLASH if int(now * 8) % 2 else GOLD
    for row, (word, attr) in enumerate((("CASINO", neon), (cas["name"], GOLD))):
        x0 = sx - len(word) // 2
        for k, c in enumerate(word):
            put_cell(ch, co, v, walls, x0 + k, sy + row, dist, c, attr)
    span = max(len("CASINO"), len(cas["name"])) // 2 + 2
    for k in range(-span, span + 1):
        for dy in (-1, 2):
            if chase(k * 0.2 + dy * 0.4, now):
                put_cell(ch, co, v, walls, sx + k, sy + dy, dist, "o", GOLD)


def draw_lanterns(ch, co, v, walls, s, i, j, f, now, wet):
    """A row of paper lanterns along a frontage, on their string, swaying.

    Four of them across a five-metre front, which is close enough together to
    read as a string rather than as four unrelated lights."""
    lit, dark = NEON[min(len(NEON) - 1, int(s["tone"] * len(NEON)))]
    for k in range(4):
        u = 0.65 + k * 1.2
        sway = 0.13 * math.sin(now * 1.1 + s["phase"] + k * 0.8)
        x, _, z = face_point(i, j, f, u + sway, 0.6, 0.0)
        put_cell_world(ch, co, v, walls, x, s["y"] + 0.55, z, "-", dark)
        sync = city_sync(now)
        glow = lit if sync is None else (
            FLASH if sync == "flash" else (lit if sync == "on" else dark))
        put_lit(ch, co, v, walls, x, s["y"], z, "o", glow, wet, now)


def put_cell_world(ch, co, v, walls, x, y, z, glyph, attr):
    put_point(ch, co, v, walls, x, y, z, glyph, attr)


SIGN_LIT_FAR = 55.0    # beyond this a hanging sign is drawn unlit


def draw_hung_sign(ch, co, v, walls, s, world, normal, now, wet):
    """A neon sign on a bracket over the pavement, letters stacked downwards.

    The panel hangs **perpendicular to the wall**, the way a real projecting
    sign does, and its two edges are projected as world points rather than
    stepped out in screen columns. Framing it in screen space makes it a
    billboard that turns to face you wherever you stand, so walking along the
    pavement swings it out into the road and it reads as something you walked
    straight through. Done properly it foreshortens to a strip when you are
    square in front of it and opens out as you come along the street, which is
    also when a sign like this is meant to be read.

    The letters are laid out in rows rather than by true height: spacing them
    by a real height makes two of them round onto the same row as the sign
    recedes, and a HOTEL with the T missing is worse than one slightly the
    wrong size."""
    nx, nz = normal
    pr = v.project(world[0], s["top"], world[2])
    if pr is None:
        return
    sx, top, dist = int(round(pr[0])), int(round(pr[1])), pr[2]
    step = max(1, int(round(SIGN_STEP * v.fy / dist)))
    wide = any(is_wide(c) for c in s["text"])
    dark = NEON[min(len(NEON) - 1, int(s["tone"] * len(NEON)))][1]

    foot = s["top"] - SIGN_STEP * (len(s["text"]) - 1)
    edges = []
    for d in (-SIGN_HALF, SIGN_HALF):
        pt = v.project(world[0] + nx * d, s["top"] + 0.45, world[2] + nz * d)
        pb = v.project(world[0] + nx * d, foot - 0.45, world[2] + nz * d)
        if pt is not None and pb is not None:
            edges.append((int(round(pt[0])), int(round(pt[1])),
                          int(round(pb[1])), pt[2]))
    # Edge-on the two sides land in the same column; drawing them then would
    # only bury the letters behind their own frame.
    # A wide glyph needs more room between the brackets than a letter does,
    # or the frame lands on top of the character it is framing.
    if len(edges) == 2 and abs(edges[0][0] - edges[1][0]) > (3 if wide else 1):
        for ex, y0, y1, ed in edges:
            for y in range(min(y0, y1), max(y0, y1) + 1):
                put_cell(ch, co, v, walls, ex, y, ed, "|", dark)
    # Far down the street a sign is a lit tube you cannot read anyway, and a
    # street of them lit reads as a wall of light with no buildings in it.
    # Past SIGN_LIT_FAR they are drawn in their unlit colour: the near ones
    # stay bright and the far end of the street goes quiet behind them.
    far = dist > SIGN_LIT_FAR and city_sync(now) is None
    for i, letter in enumerate(s["text"]):
        attr = dark if far else neon_attr(s, i, now)
        if is_wide(letter):
            # Centre it on the bracket rather than hanging it off to the right.
            put_wide(ch, co, v, walls, sx - 1, top + i * step, dist, letter, attr)
        else:
            put_cell(ch, co, v, walls, sx, top + i * step, dist, letter, attr)
        if wet > 0.15:
            y = s["top"] - i * 1.15
            ry = v.reflect_row(y, dist) + 2.0 * wet * math.sin(now * 2.3 + i)
            if _mix(sx, int(ry), int(now * 5.0)) % 6 < 1 + int(3 * wet):
                put_cell(ch, co, v, walls, sx, int(round(ry)), dist, ":", attr)


def draw_lantern_string(ch, co, v, walls, i, j, now):
    """A string of lanterns slung across the lane, wall to wall.

    Hanging them off one facade is what a shopfront does; a yokocho strings
    them over your head from one side to the other, and that one difference is
    most of what makes the lane feel like somewhere rather than a gap between
    two buildings. The wire sags in the middle and drifts, because a dead
    straight line of dots reads as a fence."""
    m = _mix(i, j, 401)
    if m % 2:
        return                      # not across every cell, or it is a ceiling
    across_x = _is_alley(i, j, XP, 91, 211)
    lit, dark = NEON[min(len(NEON) - 1, int(((m >> 4) % 8 + 0.5) / 8.0 * len(NEON)))]
    top = 4.6 + (m & 7) * 0.1
    at = ((j if across_x else i) + 0.25 + ((m >> 8) & 7) / 11.0) * CELL
    steps = 10
    for k in range(steps + 1):
        t = k / float(steps)
        run = ((i if across_x else j) + t) * CELL
        y = top - 0.55 * math.sin(math.pi * t) + 0.07 * math.sin(now * 0.9 + k)
        x, z = (run, at) if across_x else (at, run)
        if k % 3 == 1:
            put_lit(ch, co, v, walls, x, y - 0.3, z, "o", lit, v.wet, now)
        else:
            put_point(ch, co, v, walls, x, y, z, "-", dark)


def draw_over_door(ch, co, v, walls, text, world, now, tone):
    """A small neon over a pub door, horizontal, in screen space so the
    characters sit side by side - each one is two columns wide, so they step
    two at a time."""
    pr = v.project(world[0], world[1], world[2])
    if pr is None:
        return
    sx, sy, dist = int(round(pr[0])), int(round(pr[1])), pr[2]
    lit = NEON[min(len(NEON) - 1, int(tone * len(NEON)))][0]
    for k, c in enumerate(text):
        put_wide(ch, co, v, walls, sx - len(text) + k * 2, sy, dist, c, lit)


def draw_noren(ch, co, v, walls, world, normal, now):
    """The split red curtain over a ramen shop's door, and the steam coming
    out under it - which is how you know from down the lane."""
    x, _, z = world
    ax, az = -normal[1], normal[0]           # along the wall
    for k in range(-3, 4):
        for h in (2.2, 2.5, 2.8):
            if k % 2 == 0 and h < 2.5:
                continue                     # the slits between the panels
            put_point(ch, co, v, walls, x + ax * k * 0.45, h, z + az * k * 0.45,
                      "#", ROU_RED)
    for k in range(5):
        y = 2.0 + k * 0.6
        drift = 0.4 * math.sin(now * 1.3 + k)
        if (int(now * 4) + k) % 4 == 0:
            continue
        put_point(ch, co, v, walls, x + ax * drift + normal[0] * (0.3 + k * 0.1),
                  y, z + az * drift + normal[1] * (0.3 + k * 0.1),
                  "(" if k % 2 else ")", HAZE)


RAMEN_BOWL = 0.42     # world units to one of the bowl sign's own
RAMEN_SIGN_Y = 3.72   # where the bowl sits: over the name, and in view from
                      # across the lane, which sees nothing above five
RAMEN_PUFFS = 16      # puffs of steam out of the duct at once


def bowl_shape():
    """The bowl, in the sign's own (across, up) units: the rim, a round body
    down to a foot, a pair of chopsticks lifting noodles out of it, and the
    noodles - which are drawn per frame, because they swing."""
    def line(a0, h0, a1, h1, n):
        return [(a0 + (a1 - a0) * k / n, h0 + (h1 - h0) * k / n) for k in range(n + 1)]
    rim = line(-2.2, 1.7, 2.2, 1.7, 24)
    body = [(2.2 * math.cos(t), 1.7 - 1.35 * math.sin(t))
            for t in [math.pi * k / 24 for k in range(25)]]
    foot = line(-0.8, 0.15, -0.65, 0.0, 2) + line(-0.65, 0.0, 0.65, 0.0, 8) \
        + line(0.65, 0.0, 0.8, 0.15, 2)
    band = [(1.75 * math.cos(t), 1.25 - 0.9 * math.sin(t))
            for t in [math.pi * (0.15 + 0.7 * k / 16) for k in range(17)]]
    return rim, body, foot, band


_BOWL = bowl_shape()


def draw_ramen_front(ch, co, v, walls, i, j, f, now, wet):
    """A ramen shop's front, made to be found from down the lane: a neon bowl
    over the door with the chopsticks lifting noodles out of it and steam
    curling off the top; a duct up the wall pouring steam out over the lane;
    more of it rolling out under the curtain; a red lantern each side of the
    door, and the ticket machine by it, lit. All world points, so it
    foreshortens down the lane and the next shop's front hides it."""
    seed = _mix(i, j * 4 + f, 1607)
    nx, nz = FACES[f]
    mid = CELL * 0.5

    def world(a, h, out=0.25):
        return face_point(i, j, f, mid + a * RAMEN_BOWL, out,
                          RAMEN_SIGN_Y + h * RAMEN_BOWL)

    red, orange, yellow = NEON[3], NEON[4], NEON[7]
    flicker = (now + seed % 97 * 0.31) % 9.0 < 0.2 and int(now * 25) % 2 == 0
    # Dark inside the bowl first, or the wall behind shows through the tube.
    h = 0.4
    while h < 1.65:
        half = 2.2 * math.sqrt(max(0.0, 1.0 - ((1.7 - h) / 1.35) ** 2)) - 0.15
        a = -half
        while a <= half:
            pr = v.project(*world(a, h))
            if pr is not None:
                put_cell(ch, co, v, walls, int(round(pr[0])), int(round(pr[1])),
                         pr[2], " ", red[0])
            a += 0.14
        h += 0.14
    rim, body, foot, band = _BOWL
    tube = red[1] if flicker else red[0]
    for path in (rim, body, foot):
        draw_tube(ch, co, v, walls, [world(a, h) for a, h in path], tube)
    # The pattern round the bowl, every other stretch lit.
    for k in range(0, len(band) - 1, 2):
        draw_tube(ch, co, v, walls, [world(*band[k]), world(*band[k + 1])],
                  orange[0])
    # The chopsticks, lifting and dipping, and the noodles hanging off them.
    lift = 0.35 + 0.35 * math.sin(now * 1.6 + seed % 13)
    for off in (0.0, 0.32):
        draw_tube(ch, co, v, walls,
                  [world(0.2 + off + 2.4 * k / 10, 2.0 + lift + 2.1 * k / 10)
                   for k in range(11)], orange[0])
    for k, a0 in enumerate((0.25, 0.55, 0.85)):
        top = 2.05 + lift + 0.3 * k / 2
        pts = []
        h = top
        while h > 1.7:
            pts.append(world(a0 + 0.12 * math.sin(h * 6.0 + now * 3.0 + k), h))
            h -= 0.1
        draw_tube(ch, co, v, walls, pts, yellow[1] if flicker else yellow[0])
    # Steam off the bowl: three strands, lit in pulses that climb them.
    for k, a0 in enumerate((-1.1, -0.3, 0.5)):
        run = []
        h = 2.0
        while h < 4.6:
            a = a0 + 0.4 * math.sin(h * 1.9 - now * 2.0 + k * 2.3)
            if (h - now * 1.4 + k * 0.7) % 1.4 < 0.85:
                run.append(world(a, h))
            else:
                if len(run) > 1:
                    draw_tube(ch, co, v, walls, run, SNOW if h < 3.6 else SMOKE)
                run = []
            h += 0.1
        if len(run) > 1:
            draw_tube(ch, co, v, walls, run, SMOKE)

    # The duct: up the wall at one end of the front, out over the lane at the
    # top, and the steam coming out of it in puffs that grow and thin out.
    top = 4.1           # a vent, not a chimney: low enough to see from the lane
    du = 0.55 if seed & 1 else CELL - 0.55
    pts = [face_point(i, j, f, du, 0.2, 2.6 + (top - 2.6) * k / 12) for k in range(13)]
    pts += [face_point(i, j, f, du, 0.2 + 0.8 * k / 4, top) for k in range(1, 5)]
    draw_tube(ch, co, v, walls, pts, CURB)
    wind = 0.6 * math.sin(now * 0.13 + seed % 7)
    for k in range(RAMEN_PUFFS):
        age = (now * 0.22 + k / float(RAMEN_PUFFS) + (seed % 11) * 0.09) % 1.0
        if age > 0.92:
            continue
        r = 0.25 + age * 1.3
        cx, cy, cz = face_point(i, j, f, du + wind * age * 3.0
                                + 0.5 * math.sin(k * 2.7 + now * 0.7),
                                1.1 + age * 2.0, top + 0.1 + age * age * 6.0)
        tone = SNOW if age < 0.3 else SMOKE if age < 0.65 else HAZE
        ax, az = -nz, nx
        for da, dh, g in ((0.0, 0.0, "~"), (-r, 0.0, "("), (r, 0.0, ")"),
                          (0.0, r * 0.6, "~"), (-r * 0.6, r * 0.5, "("),
                          (r * 0.6, r * 0.5, ")")):
            if age > 0.6 and g != "~" and (k + int(now * 3)) % 2:
                continue                         # thinning out
            put_point(ch, co, v, walls, cx + ax * da, cy + dh, cz + az * da, g, tone)

    # Steam rolling out under the curtain into the lane.
    for k in range(10):
        age = (now * 0.35 + k / 10.0) % 1.0
        along = 1.3 * math.sin(k * 1.9 + now * 0.5)
        px, py, pz = face_point(i, j, f, mid + along, 0.3 + age * 2.3, 1.9 + age * 2.2)
        put_point(ch, co, v, walls, px, py, pz,
                  "~" if k % 3 else "(" if along < 0 else ")",
                  SNOW if age < 0.35 else SMOKE if age < 0.7 else HAZE)

    # A red lantern each side of the door, swaying.
    for side in (-1, 1):
        sway = 0.06 * math.sin(now * 1.2 + side + seed % 5)
        lx, _, lz = face_point(i, j, f, mid + side * 1.95 + sway, 0.45, 0.0)
        glow = red[0] if (int(now * 2) + side) % 9 else FLASH
        blit_sprite(ch, co, v, walls, [".-.", "(#)", "'-'"],
                    lx, lz, 2.25, 3.05, 0.38, glow)
        put_lit(ch, co, v, walls, lx, 2.6, lz, "#", glow, wet, now)
    # And the ticket machine: pay here, then sit down.
    tu = CELL - 0.9 if seed & 1 else 0.9
    tx, _, tz = face_point(i, j, f, tu, 0.35, 0.0)
    blit_sprite(ch, co, v, walls, ["[==]", "|oo|", "|oo|", "|[]|", "|__|"],
                tx, tz, 0.0, 1.5, 0.45, NEON[2][0])


def near_yokocho(v, reach):
    """Open cells of a lit lane in front of you."""
    n = int(reach / CELL) + 1
    ci = int(v.x / CELL + BIG) - BIG
    cj = int(v.z / CELL + BIG) - BIG
    for i in range(ci - n, ci + n + 1):
        for j in range(cj - n, cj + n + 1):
            rx = (i + 0.5) * CELL - v.x
            rz = (j + 0.5) * CELL - v.z
            if rx * v.dx + rz * v.dz < -CELL:
                continue
            if yokocho_at(i, j):
                yield i, j


STACK = [
    " ___ ",
    "|OOO|",
    "|OOO|",
    "|___|",
    "|OOO|",
    "|OOO|",
    "|___|",
]


COMPASS = ("N", "NE", "E", "SE", "S", "SW", "W", "NW")


def rave_hint(v, now):
    """What the HUD says when the rig is going.

    Which way, not just that there is one: a wood is disorienting on purpose,
    and "music somewhere" in a place with no landmarks is a fact you can do
    nothing with. A bearing is one you can walk on."""
    if rave_window(now) is None:
        return ""
    hx, hz, hi, hj = nearest_hollow(v.x, v.z)
    jx, jz = jack_spot(hi, hj)
    if math.hypot(jx - v.x, jz - v.z) < 7.0:
        return JACK_LINE
    d = math.hypot(hx - v.x, hz - v.z)
    if d > 700.0:
        return ""
    way = COMPASS[int(((math.atan2(hx - v.x, hz - v.z)
                        / math.tau % 1.0) * 8 + 0.5)) % 8]
    return "  ~ a bass line %s, %s ~" % (
        way, "close" if d < 30.0 else "not far" if d < 100.0
        else "a way off" if d < 300.0 else "far off")


# The crowd in the hollow. Hoods up, and the one thing they all do is the same
# thing at the same time.
ZOMB_UP = [
    "\\_n_/",
    " (.) ",
    " \\#/ ",
    "  #  ",
    " / \\ ",
    "_| |_",
]

ZOMB_DOWN = [
    " _n_ ",
    " (.) ",
    "/ # \\",
    "  #  ",
    " / \\ ",
    "_| |_",
]

# The booth at the far end of the hollow: the stack, and the decks on it.
ALTAR = [
    "  _|=|_  ",
    " |[o][o]|",
    " |_____| ",
    "|#||#||#|",
    "|#||#||#|",
    "|_||_||_|",
]
ALTAR_H = 4.2
ALTAR_W = 3.15

# And who is on the decks. Aku: the crest of flame with the two great horns,
# the green face, the brows that are flames, the grin. Drawn in layers so each
# part can take its own colour - the one sprite in the city that is not one
# colour - and standing behind the booth, which hides his feet, if he has any.
AKU_BODY = [
    '\\                 /',
    ' \\     /\\  /\\    / ',
    '  \\   /  \\/  \\  /  ',
    '   \\_/  /\\   \\_/   ',
    '                   ',
    '                   ',
    '                   ',
    '                   ',
    '                   ',
    '  ____\\______/____ ',
    ' /    |      |    \\',
    '/     |      |     ',
]
AKU_FACE = [
    '                   ',
    '                   ',
    '                   ',
    '                   ',
    '    (##########)   ',
    '    (##########)   ',
    '    (##########)   ',
    '    (##########)   ',
    '     \\########/    ',
    '                   ',
    '                   ',
    '                   ',
]
AKU_BROW = [
    '                   ',
    '                   ',
    '                   ',
    '                   ',
    '      /\\    /\\     ',
    '                   ',
    '                   ',
    '                   ',
    '                   ',
    '                   ',
    '                   ',
    '                   ',
]
AKU_WHITE = [
    '                   ',
    '                   ',
    '                   ',
    '                   ',
    '                   ',
    '       o    o      ',
    '                   ',
    '      VVVVVVVV     ',
    '                   ',
    '                   ',
    '                   ',
    '                   ',
]
AKU_H = 7.6
AKU_W = 6.0
AKU_FEET = 2.4         # he stands up behind the booth, towering over it

# The one who is awake. Topknot, white gi, the sword at his hip. He stands at
# the edge of the hollow with his back to the altar, facing whoever comes down
# the path - which is you - and he does not move to the beat.
JACK = [
    "  _o_  ",
    "  (-.) ",
    " /|##|\\",
    "/ |##| |",
    "  |__|/ ",
    "  |  |  ",
    " _|  |_ ",
]
JACK_H = 2.05
JACK_W = 0.85
JACK_LINE = '  ~ "it is the music. do not listen to it." ~'


def jack_spot(hi, hj):
    """Where he stands: at the near edge of the hollow, off to one side of the
    path in, so you come past him on the way to the crowd."""
    m = _mix(hi, hj, 1237)
    hx, hz = (hi + 0.5) * CELL, (hj + 0.5) * CELL
    return (hx + (4.5 if m & 1 else -4.5),
            hz - HOLLOW_RJ * CELL * 0.62)


def draw_hollow_rave(ch, co, v, walls, hi, hj, now, wet):
    """The rig in the hollow, and everyone who came to it.

    The altar is at the far end and the crowd faces it with their backs to
    you, and every one of them moves on the same beat with no offset at all -
    hoods up, arms up, arms down, together. That is what makes it not a party.
    The club's queue is in time; this is in step. Between the kicks, when the
    hollow goes dark, what is left is their eyes."""
    hx, hz = (hi + 0.5) * CELL, (hj + 0.5) * CELL
    m = _mix(hi, hj, 977)
    phase = (m & 255) / 255.0 * 6.0
    tone = ((m >> 8) & 255) / 255.0
    lamp = rave_light(now, phase, tone)
    t = now * RAVE_BPM / 60.0 + phase
    if city_sync(now) is not None:
        t = now * ALIEN_BPM / 60.0
    kick = lamp == FLASH

    ax, az = hx, hz + HOLLOW_RJ * CELL * 0.72
    # Beams going up into the canopy - the giveaway, from much further off
    # than any of the rest of it.
    if lamp is not None:
        for k in range(8):
            a = math.sin(t * (0.5 + k * 0.17) + k * 1.9)
            for step in range(10):
                h = 2.0 + step * 1.5
                put_point(ch, co, v, walls, ax + a * h * 0.45, h,
                          az - h * 0.15 + math.cos(t * 0.3 + k) * h * 0.22,
                          "|" if abs(a) < 0.4 else ("\\" if a > 0 else "/"),
                          rave_tone(tone, k + int(t / 8)))

    # The booth, against the trees at the back, and Aku behind it, on the
    # decks - drawn after the beams, so they come up from behind him. He bobs
    # on the kick. His body is the dark purple the rig leaves on things
    # between hits, and white when the strobe takes everything.
    up = (t % 1.0) < 0.5
    bob = AKU_FEET + (0.35 if up else 0.0)
    body = FLASH if kick else NEON[min(len(NEON) - 1, 6)][1]
    for art, colour in ((AKU_BODY, body), (AKU_FACE, ROU_GREEN),
                        (AKU_BROW, ROU_RED), (AKU_WHITE, FLASH)):
        blit_sprite(ch, co, v, walls, art, ax, az + 1.8, bob, bob + AKU_H,
                    AKU_W, colour)
    blit_sprite(ch, co, v, walls, ALTAR, ax, az, 0.0, ALTAR_H, ALTAR_W,
                lamp if lamp is not None else CONCRETE)

    # The crowd. Furthest first so the near ones are drawn over them.
    crowd = []
    for k in range(CROWD):
        g = _mix(hi, hj, 40 + k)
        r = math.sqrt((g & 255) / 255.0) * 0.86
        a = ((g >> 8) & 1023) / 1023.0 * math.tau
        px = hx + r * HOLLOW_RI * CELL * math.cos(a)
        pz = hz + r * HOLLOW_RJ * CELL * math.sin(a)
        if (px - ax) ** 2 + (pz - az) ** 2 < 9.0:
            continue                    # nobody stands on the altar
        crowd.append(((px - v.x) ** 2 + (pz - v.z) ** 2, px, pz))
    for d2, px, pz in sorted(crowd, reverse=True):
        blit_sprite(ch, co, v, walls, ZOMB_UP if up else ZOMB_DOWN,
                    px, pz, 0.05, SMOKER_H, SMOKER_W,
                    lamp if lamp is not None else BARK)
        if lamp is None and d2 < 900.0:
            for ex in (-0.1, 0.1):
                put_point(ch, co, v, walls, px + ex, 1.55, pz, ".", EYES)

    # And the one who is not with them. Pale where they are dark, still
    # where they move, and no light in his eyes.
    jx, jz = jack_spot(hi, hj)
    blit_sprite(ch, co, v, walls, JACK, jx, jz, 0.0, JACK_H, JACK_W,
                FLASH if kick else MOON_DIM)


def draw_drawn_in(ch, co, v, walls, hi, hj, now):
    """The ones still on their way: standing on the trails near the hollow,
    hoods up, facing it, not moving. They heard it too."""
    hx, hz = (hi + 0.5) * CELL, (hj + 0.5) * CELL
    n = int(60.0 / CELL)
    ci = int(v.x / CELL + BIG) - BIG
    cj = int(v.z / CELL + BIG) - BIG
    for i in range(ci - n, ci + n + 1):
        for j in range(cj - n, cj + n + 1):
            g = _mix(i, j, 1223)
            if g % 5 or hollow_at(i, j) or not trail_at(i, j):
                continue
            x, z = (i + 0.5) * CELL, (j + 0.5) * CELL
            if (x - hx) ** 2 + (z - hz) ** 2 > 90.0 ** 2:
                continue
            if (x - v.x) * v.dx + (z - v.z) * v.dz < 0.0:
                continue
            x += ((g >> 4) & 7) / 7.0 * 2.4 - 1.2
            blit_sprite(ch, co, v, walls, ZOMB_DOWN, x, z, 0.05,
                        SMOKER_H, SMOKER_W, BARK)
            for ex in (-0.1, 0.1):
                put_point(ch, co, v, walls, x + ex, 1.55, z, ".", EYES)


def draw_woods_life(ch, co, v, walls, now, wet):
    """What is out in the trees with you: fireflies over the open ground on a
    dry night, and now and then two points of light under a tree that go out
    when you look at them for long enough. Nothing is ever shown attached to
    them."""
    n = int(36.0 / CELL)
    ci = int(v.x / CELL + BIG) - BIG
    cj = int(v.z / CELL + BIG) - BIG
    for i in range(ci - n, ci + n + 1):
        for j in range(cj - n, cj + n + 1):
            if not woods_at(i, j):
                continue
            x, z = (i + 0.5) * CELL, (j + 0.5) * CELL
            if (x - v.x) * v.dx + (z - v.z) * v.dz < -CELL:
                continue
            m = _mix(i, j, 1301)
            if is_open(i, j):
                if wet > 0.2:
                    continue
                # Most of the wood is behind the nearest trees, so the ones
                # you actually see are the ones over the trail you are on.
                for k in range(2 + m % 3 if trail_at(i, j) else m % 3):
                    s = (m >> (4 + 6 * k)) & 63
                    if math.sin(now * 1.7 + s) < 0.1:
                        continue
                    fx = x + math.sin(now * 0.31 + s) * 1.6
                    fz = z + math.cos(now * 0.23 + s * 2) * 1.6
                    fy = 0.7 + 0.4 * math.sin(now * 0.5 + s * 3)
                    put_point(ch, co, v, walls, fx, fy, z + (fz - z), "'",
                              FIREFLY)
            elif m % 3 == 0:
                if int(now * 0.4 + (m >> 8)) % 7 == 0:
                    continue                    # blinked
                dx, dz = v.x - x, v.z - z
                d = math.hypot(dx, dz) or 1.0
                if d > 24.0:
                    continue                    # further off, a tree hides it
                # Just clear of the trunk on the side facing you - far
                # enough out to be in the next cell whichever way that is,
                # and only if that cell is open, or the tree hides its own eyes.
                ex, ez = x + dx / d * 3.8, z + dz / d * 3.8
                if not open_at(ex, ez):
                    continue
                for side in (-0.2, 0.2):
                    put_point(ch, co, v, walls, ex - dz / d * side, 0.75,
                              ez + dx / d * side, ".", EYES)


STALL = [
    "/^^^^^^^\\",
    "|_______|",
    "| o   o |",
    "|_______|",
]

STRIKER_POST = [
    " (O) ",
    " |=| ",
    " |-| ",
    " |=| ",
    " |-| ",
    " |=| ",
    " |-| ",
    "_|_|_",
    "[___]",
]

CLAW_BOOTH = [
    ".-----.",
    "|  T  |",
    "|o^.^o|",
    "|=====|",
    "|_[_]_|",
]

CAROUSEL = [
    "    ^    ",
    "  /   \\  ",
    " /_____\\ ",
    "|_______|",
    "|       |",
    "|_______|",
]


def near_carnivals(v, reach):
    """The first column of each carnival in front of you."""
    ci = int(v.x / CELL + BIG) - BIG
    seen = set()
    for k in range(ci - int(reach / CELL) - FAIR_LONG, ci + int(reach / CELL) + 1):
        c = carnival_col(k)
        if c in seen or not c <= k < c + FAIR_LONG:
            continue
        seen.add(c)
        (wx, wz), _, _, _ = carnival_spots(c)
        rx, rz = wx - v.x, wz - v.z
        if rx * v.dx + rz * v.dz < -CELL or rx * rx + rz * rz > reach * reach:
            continue
        yield c


def draw_carnival(ch, co, v, walls, c, now, wet):
    """A wheel, a carousel, a row of stalls and the bulbs strung between.

    The wheel is world points, not a sprite: a ring of bulbs chasing round it,
    eight spokes, eight cabins that hang from the rim and stay upright as it
    turns, and an A-frame under the hub. Its plane faces the water, so from
    the far bank and the pier you see the whole circle and its reflection,
    and from the bank you are on it comes up edge-on as you walk towards it.
    Everything else is a billboard."""
    (wx, wz), (cx, cz), stalls, z0 = carnival_spots(c)
    hub = WHEEL_R + 1.6
    turn = now * WHEEL_RPM * math.tau / 60.0
    chase = int(now * 5.0)

    # On the pier: bulbs along its rails, the far end and both sides, with
    # posts under them down to the water, and the sign over the way on.
    tip = pier_tip(c)
    if tip is not None:
        x0, x1 = c * CELL, (c + FAIR_LONG) * CELL
        k = 0
        x = x0
        while x <= x1:
            zt = pier_tip(c, k=(x - x0) / CELL) * CELL + 0.3
            put_lit(ch, co, v, walls, x, 1.1, zt, "o",
                    NEON[(k // 2 + chase // 2) % len(NEON)][0], max(wet, 0.3), now)
            if k % 3 == 0:
                put_point(ch, co, v, walls, x, 0.55, zt, "|", CONCRETE)
                put_point(ch, co, v, walls, x, 0.05, zt - 0.2, "|", BARK)
            x += 1.0
            k += 1
        for x in (x0 + 0.3, x1 - 0.3):
            z = pier_tip(c, k=(x - x0) / CELL) * CELL
            while z < bank_z(int(x / CELL + BIG) - BIG):
                put_lit(ch, co, v, walls, x, 1.1, z, "o", BULB, max(wet, 0.3), now)
                z += 1.6
        draw_pier_sign(ch, co, v, walls, (c + FAIR_LONG * 0.5) * CELL,
                       bank_z(c + FAIR_LONG // 2) - 0.6, now)

    if tip is not None:
        draw_drop_tower(ch, co, v, walls, c, now, wet)
        draw_coaster(ch, co, v, walls, c, now, wet)

    # The A-frame, then the spokes, then the rim over both.
    for h in range(0, int(hub * 2)):
        y = h * 0.5
        d = (hub - y) * 0.45
        put_point(ch, co, v, walls, wx - d, y, wz, "/", CONCRETE)
        put_point(ch, co, v, walls, wx + d, y, wz, "\\", CONCRETE)
    for s in range(8):
        a = turn + s * math.tau / 8.0
        for r in range(1, int(WHEEL_R)):
            put_point(ch, co, v, walls, wx + math.cos(a) * r, hub + math.sin(a) * r,
                      wz, "-" if abs(math.cos(a)) > 0.7 else "|", CONCRETE)
    put_point(ch, co, v, walls, wx, hub, wz, "O", GOLD)
    for k in range(56):
        a = turn + k * math.tau / 56.0
        x, y = wx + math.cos(a) * WHEEL_R, hub + math.sin(a) * WHEEL_R
        colour = NEON[(k // 7 + chase) % len(NEON)][0]
        put_lit(ch, co, v, walls, x, y, wz, "o", colour, max(wet, 0.3), now)
    for s in range(8):
        a = turn + s * math.tau / 8.0
        x, y = wx + math.cos(a) * WHEEL_R, hub + math.sin(a) * WHEEL_R
        put_point(ch, co, v, walls, x - 0.45, y - 0.7, wz, "[", CURB)
        put_point(ch, co, v, walls, x + 0.45, y - 0.7, wz, "]", CURB)
        put_point(ch, co, v, walls, x, y - 0.7, wz, "o", BULB_DIM)

    # The carousel: the roof and platform are a billboard, the riders go
    # round it on their own, bobbing.
    blit_sprite(ch, co, v, walls, CAROUSEL, cx, cz, 0.0, 3.6, 3.4,
                NEON[(chase // 3) % len(NEON)][0])
    for k in range(6):
        a = -turn * 2.5 + k * math.tau / 6.0
        put_point(ch, co, v, walls, cx + math.cos(a) * 1.5, 1.1
                  + 0.25 * math.sin(now * 3.0 + k), cz + math.sin(a) * 1.0,
                  "n", BULB)

    # The stalls, each its own colour, and a string of bulbs the length of
    # the ground, sagging between the poles the way the bridge's does.
    for k, (sx_, sz_) in enumerate(stalls):
        blit_sprite(ch, co, v, walls, STALL, sx_, sz_, 0.0, 2.4, 2.3,
                    NEON[(k * 3 + 1) % len(NEON)][0])
        put_lit(ch, co, v, walls, sx_, 1.2, sz_ - 0.3, "*", BULB,
                max(wet, 0.3), now)
    sx_, sz_ = striker_spot(c)
    blit_sprite(ch, co, v, walls, STRIKER_POST, sx_, sz_, 0.0, 4.6, 1.4, GOLD_DIM)
    put_lit(ch, co, v, walls, sx_, 4.9, sz_, "O", GOLD, max(wet, 0.3), now)
    bx, bz = claw_spot(c)
    blit_sprite(ch, co, v, walls, CLAW_BOOTH, bx, bz, 0.0, 2.8, 1.7,
                NEON[_mix(c, 1, 1307) % len(NEON)][0])
    put_lit(ch, co, v, walls, bx, 3.1, bz, "*", BULB, max(wet, 0.3), now)
    for k in range(FAIR_LONG + 1 if tip is None else 0):
        px = (c + k) * CELL
        pz, pz1 = bank_z(c + k) + 0.6 * CELL, bank_z(c + k + 1) + 0.6 * CELL
        for h in (1.0, 2.0, 3.0):
            put_point(ch, co, v, walls, px, h, pz, "|", CONCRETE)
        if k < FAIR_LONG:
            for step in range(1, 5):
                t = step / 5.0
                y = 3.1 - 0.5 * math.sin(math.pi * t)
                put_lit(ch, co, v, walls, px + t * CELL, y, pz + (pz1 - pz) * t, "o",
                        NEON[(k + step + chase // 2) % len(NEON)][0],
                        max(wet, 0.2), now)

    # A few people, looking up at the wheel.
    for k in range(4):
        m = _mix(c, k, 1303)
        px = (c + 1.5 + (m & 255) / 255.0 * 8.0) * CELL
        if tip is not None:
            pz = (pier_tip(c, k=px / CELL - c) + 0.9
                  + ((m >> 8) & 255) / 255.0 * 2.2) * CELL
        else:
            pz = (bank_z(int(px / CELL + BIG) - BIG)
                  + (0.9 + ((m >> 8) & 255) / 255.0 * 2.0) * CELL)
        blit_sprite(ch, co, v, walls, LOOK_UP, px, pz, 0.0, SMOKER_H, SMOKER_W,
                    CURB)


def drop_car(t):
    """How high the drop tower's car is, t seconds into its cycle, and
    whether it is falling: waiting at the bottom while they get in, a slow
    climb, a hang at the top long enough to look at the view, then the drop -
    falling, not easing - and the brakes."""
    t %= DROP_CYCLE
    low, high = 1.2, DROP_H - 3.0
    if t < 3.0:
        return low, False
    if t < 11.0:
        k = (t - 3.0) / 8.0
        return low + (high - low) * (0.5 - 0.5 * math.cos(k * math.pi)), False
    if t < 13.5:
        return high, False
    if t < 14.6:
        k = (t - 13.5) / 1.1
        return high - (high - low) * k * k, True        # gravity, near enough
    return low, False


def draw_drop_tower(ch, co, v, walls, c, now, wet):
    """The drop tower near the end of the pier: a mast ringed with bulbs,
    a red light on top, and the car of riders round it going up slowly and
    coming down all at once. While it climbs the lights creep up after it;
    when it drops they race down with it."""
    k = 9.5
    x, z = (c + k) * CELL, (pier_tip(c, k=k) + 1.2) * CELL
    car, falling = drop_car(now + c * 0.37)
    for a in range(4):                       # the mast, four legs
        ang = a * math.tau / 4.0 + 0.4
        dx, dz = math.cos(ang) * 0.5, math.sin(ang) * 0.5
        y = 0.3
        while y < DROP_H:
            put_point(ch, co, v, walls, x + dx, y, z + dz, "|", CONCRETE)
            y += 0.6
    y = 1.0
    n = 0
    while y < DROP_H - 0.5:                  # the bulbs up the front of it
        if falling:
            lit = car - 1.0 <= y <= car + 6.0
        else:
            lit = (n - int(now * 6.0)) % 5 == 0 or y < car
        put_lit(ch, co, v, walls, x, y, z - 0.6, "o",
                (FLASH if falling else NEON[(n // 3) % len(NEON)][0]) if lit
                else BULB_DIM, max(wet, 0.3), now)
        y += 1.2
        n += 1
    blink = int(now * 1.3) % 2 == 0
    put_lit(ch, co, v, walls, x, DROP_H + 0.6, z, "*" if blink else ".",
            ROU_RED if blink else CONCRETE, max(wet, 0.3), now)
    # The car: a ring of seats round the mast with somebody in each.
    for a in range(10):
        ang = a * math.tau / 10.0
        sx, sz = x + math.cos(ang) * 1.3, z + math.sin(ang) * 1.3
        put_point(ch, co, v, walls, sx, car, sz, "=", GOLD)
        put_point(ch, co, v, walls, sx, car + 0.55, sz, "o", CURB)


def coaster_point(c, a):
    """A point on the coaster's track, a going round it: an oval over the
    east half of the pier, climbing and diving as it goes round."""
    x0 = (c + 8.0) * CELL
    z0 = (pier_tip(c, k=8.0) + 2.0) * CELL
    h = 5.0 + 3.5 * math.sin(2.0 * a + 0.5) + 2.0 * math.sin(3.0 * a)
    return x0 + 13.0 * math.cos(a), max(2.2, h), z0 + 7.2 * math.sin(a)


def coaster_at(c, now):
    """Where the train's front car is on the track, as an angle: slow up the
    climbs and quick down the dips, which is a function of where it is on
    the lap and not something integrated, so nothing is stored."""
    lap = ((now + c * 0.53) % COASTER_LAP) / COASTER_LAP
    a = lap * math.tau
    return a + 0.35 * math.sin(2.0 * a + 0.5)


def draw_coaster(ch, co, v, walls, c, now, wet):
    """The roller coaster: the track in tube, glyph by which way it runs on
    screen, bulbs chasing round it, legs down to the deck, and the train -
    five cars of riders with a light on the front - going round."""
    steps = 140
    pts = [coaster_point(c, k * math.tau / steps) for k in range(steps + 1)]
    draw_tube(ch, co, v, walls, pts, CONCRETE)
    chase_k = int(now * 8.0)
    for k, (x, y, z) in enumerate(pts[:-1]):
        if k % 4 == 0:
            on = (k // 4 - chase_k) % 6 == 0
            put_lit(ch, co, v, walls, x, y + 0.35, z, "o",
                    NEON[(k // 4) % len(NEON)][0] if on else BULB_DIM,
                    max(wet, 0.3), now)
        if k % 10 == 0:                      # the legs
            h = y - 0.4
            while h > 0.3:
                put_point(ch, co, v, walls, x, h, z, "|", BARK)
                h -= 0.9
    front = coaster_at(c, now)
    for n in range(COASTER_CARS):
        x, y, z = coaster_point(c, front - n * 0.13)
        put_point(ch, co, v, walls, x, y + 0.45, z, "#", ROU_RED)
        put_point(ch, co, v, walls, x, y + 1.0, z, "o", CURB)
    x, y, z = coaster_point(c, front + 0.04)
    put_lit(ch, co, v, walls, x, y + 0.5, z, "*", FLASH, max(wet, 0.3), now)


def draw_pier_sign(ch, co, v, walls, x, z, now):
    """PLEASURE PIER over the way onto it: an arch of bulbs on two posts with
    the words in neon, in screen space so it reads, for the casino marquee's
    reason. Drawn for the near half of the city only - from the water it is a
    line of lights, which is what it should be."""
    pr = v.project(x, 4.6, z)
    if pr is None or pr[2] > 90.0:
        return
    sx, sy, dist = int(round(pr[0])), int(round(pr[1])), pr[2]
    word = "PLEASURE PIER"
    for k, c in enumerate(word):
        put_cell(ch, co, v, walls, sx - len(word) // 2 + k, sy, dist, c,
                 NEON[(k + int(now * 2.0)) % len(NEON)][0] if c != " " else GOLD_DIM)
    for k in range(-len(word) // 2 - 2, len(word) // 2 + 3):
        lit = chase(k * 0.4, now)
        put_cell(ch, co, v, walls, sx + k, sy - 1, dist, "o" if lit else ".",
                 GOLD if lit else GOLD_DIM)
    for side in (-1.0, 1.0):
        for h in (0.8, 1.8, 2.8, 3.8):
            put_point(ch, co, v, walls, x + side * 4.5, h, z, "|", CONCRETE)


def _cable_y(zf, za, zt1, zt2, zb):
    """Height of the main cable at zf: up from the anchorage to the first
    tower, down into the sag and up to the second, down to the far anchorage.
    Three parabolas that meet at the tower tops."""
    if zf < zt1:
        t = (zf - za) / max(1e-6, zt1 - za)
        return 1.5 + (TOWER_H - 1.5) * t * t
    if zf > zt2:
        t = (zb - zf) / max(1e-6, zb - zt2)
        return 1.5 + (TOWER_H - 1.5) * t * t
    zm = (zt1 + zt2) * 0.5
    t = (zf - zm) / max(1e-6, zt2 - zm)
    return CABLE_SAG + (TOWER_H - CABLE_SAG) * t * t


def draw_grand_bridge(ch, co, v, walls, i, j, now, wet):
    """The big one. Two towers in the water, the cables over them, the
    suspenders down to the deck, and lights along every cable.

    Everything is world points. The towers are a pair of legs with the cross
    bracing between them that makes a suspension tower read as one, in the
    orange those bridges are painted; the cables are dim and it is the bulbs
    on them that draw the curve, which is what you actually see of one at
    night. A red light on each tower top, blinking, for the aircraft."""
    xa, xb, z0, z1 = bridge_edges(i)
    xa, xb = xa - TOWER_OUT, xb + TOWER_OUT     # the deck passes between the legs
    za, zb = z0 - 0.5 * CELL, z1 + 0.5 * CELL           # the anchorages
    zt1, zt2 = za + (zb - za) * 0.27, za + (zb - za) * 0.73
    blink = int(now * 1.1) % 2 == 0
    draw_bridge_body(ch, co, v, walls, xa + TOWER_OUT, xb - TOWER_OUT, z0, z1,
                     arches=False)

    for x in (xa, xb):
        # The main cable, a bulb every few units along it.
        zf = za
        while zf <= zb:
            y = _cable_y(zf, za, zt1, zt2, zb)
            slope = _cable_y(zf + 0.5, za, zt1, zt2, zb) - y
            glyph = "-" if abs(slope) < 0.18 else ("\\" if slope > 0 else "/")
            put_point(ch, co, v, walls, x, y, zf, glyph, EMBER)
            zf += 0.6
        zf = za + 1.0
        while zf < zb:
            put_lit(ch, co, v, walls, x, _cable_y(zf, za, zt1, zt2, zb) + 0.3,
                    zf, "o", BULB, max(wet, 0.3), now)
            zf += 2.1
        # Suspenders, from the cable down to the deck.
        zf = za + 1.6
        while zf < zb:
            top = _cable_y(zf, za, zt1, zt2, zb)
            y = 1.0
            while y < top - 0.4:
                put_point(ch, co, v, walls, x, y, zf, "|", CONCRETE)
                y += 1.1
            zf += 2.4

    # The towers.
    for zt in (zt1, zt2):
        for x in (xa, xb):
            y = 0.0
            while y <= TOWER_H:
                put_point(ch, co, v, walls, x, y, zt, "|", EMBER_HOT)
                y += 0.55
        for y in (6.0, 13.0, 20.0, 27.0, TOWER_H):
            x = xa
            while x <= xb:
                put_point(ch, co, v, walls, x, y, zt, "=", EMBER_HOT)
                x += 0.8
        for x in (xa, xb):
            put_point(ch, co, v, walls, x, TOWER_H + 0.7, zt,
                      "*" if blink else ".", ROU_RED if blink else CONCRETE)

    # Lamps down the deck, both sides, and the way the footbridge does it.
    zf = z0 + 2.0
    while zf < z1:
        for x in (xa, xb):
            for h in (1.4, 2.2, 3.0):
                put_point(ch, co, v, walls, x, h, zf, "|", CONCRETE)
            put_lit(ch, co, v, walls, x, 3.5, zf, "o", BULB, max(wet, 0.3), now)
        zf += 9.0


BENCH = [
    "_______",
    "|_____|",
    "|     |",
]


FERRY = [
    "      __|__      ",
    "  ___|o o o|___  ",
    " |o o o o o o o| ",
    "\\_______________/",
]

ROWBOAT = [
    "  o  ",
    "\\_|_/",
]


def near_promenades(v, reach):
    """Each promenade stretch in front of you, as its first column."""
    ci = int(v.x / CELL + BIG) - BIG
    n = int(reach / CELL) + PROM_STRETCH
    seen = set()
    for i in range(ci - n, ci + n + 1):
        s = i // PROM_STRETCH
        if s in seen or not prom_at(i, shore_j(i)):
            continue
        seen.add(s)
        yield s * PROM_STRETCH


def draw_promenade(ch, co, v, walls, s, now, wet):
    """The railing along the water, lamps, benches, and people at the rail.

    Everything follows the bank cell by cell, because the bank meanders and a
    straight railing would walk into the river and out again."""
    ci = int(v.x / CELL + BIG) - BIG
    for i in range(max(s, ci - 22), min(s + PROM_STRETCH, ci + 23)):
        _, hi = river_span(i)
        ze = shore_j(i) * CELL + 0.4                   # the water's edge
        x0 = i * CELL
        if (x0 - v.x) * v.dx + (ze - v.z) * v.dz < -CELL * 2:
            continue
        for k in range(4):
            x = x0 + k * 1.25
            put_point(ch, co, v, walls, x, 0.95, ze, "-", CURB)
            if k % 2 == 0:
                put_point(ch, co, v, walls, x, 0.5, ze, "|", CURB)
        m = _mix(i, 0, 1409)
        if i % 3 == 0:
            for h in (1.2, 2.1, 3.0):
                put_point(ch, co, v, walls, x0 + 2.5, h, ze + 1.4, "|", CONCRETE)
            put_lit(ch, co, v, walls, x0 + 2.5, 3.4, ze + 1.4, "o", BULB,
                    max(wet, 0.3), now)
        elif i % 3 == 1 and m % 2:
            blit_sprite(ch, co, v, walls, BENCH, x0 + 2.5, ze + 4.0, 0.0, 0.9,
                        1.6, CURB)
        if m % 7 == 0:
            blit_sprite(ch, co, v, walls, LEANER, x0 + 1.0 + (m >> 4 & 3),
                        ze + 0.9, 0.0, 1.75, 0.95, CURB)


def ferry_spot(now, c):
    """Where the ferry is: it crosses the bay beside the big bridge, near
    bank to far bank and back, and waits a while at each end."""
    span = grand_avenue(c)
    if span is None:
        return None
    i = span[0] + span[1] + 9
    lo, hi = river_span(i)
    t = (now / FERRY_PERIOD) % 1.0
    # 0..0.1 waiting, 0.1..0.5 over, 0.5..0.6 waiting, 0.6..1 back.
    if t < 0.1:
        f = 0.0
    elif t < 0.5:
        f = (t - 0.1) / 0.4
    elif t < 0.6:
        f = 1.0
    else:
        f = 1.0 - (t - 0.6) / 0.4
    f = 0.5 - 0.5 * math.cos(f * math.pi)          # eases off and on
    za, zb = (int(hi) + 0.4) * CELL, (int(lo) + 0.9) * CELL
    return (i + 0.5) * CELL, za + (zb - za) * f, f


def draw_ferry(ch, co, v, walls, x, z, moving, now, wet):
    blit_sprite(ch, co, v, walls, FERRY, x, z, 0.0, 3.2, 6.5, CONCRETE)
    put_lit(ch, co, v, walls, x, 3.5, z, "*", BULB, max(wet, 0.4), now)
    for k in range(1, 7):
        put_lit(ch, co, v, walls, x - 2.6 + k * 0.85, 1.7, z, "o", BULB_DIM,
                max(wet, 0.3), now)
    if 0.0 < moving < 1.0:
        for k in range(1, 7):
            put_point(ch, co, v, walls, x + (k % 2 - 0.5) * 1.6, 0.12,
                      z + (k * 1.7 if moving < 0.5 else -k * 1.7), "~", RAIN_FAR)


def near_rowboats(v, now, reach):
    """A rowing boat every so often, drifting down with the current and a
    lantern in it. Position is a function of time, nothing is stored."""
    drift = (now * ROWBOAT_DRIFT) % (ROWBOAT_GAP * CELL)
    base = int((v.x - reach - drift) / (ROWBOAT_GAP * CELL)) - 1
    for n in range(base, base + int(2 * reach / (ROWBOAT_GAP * CELL)) + 3):
        x = n * ROWBOAT_GAP * CELL + drift
        if abs(x - v.x) > reach:
            continue
        i = int(x / CELL + BIG) - BIG
        lo, hi = river_span(i)
        side = 0.35 if _mix(n, 0, 1423) & 1 else 0.65
        z = (lo + (hi - lo) * side) * CELL
        if (x - v.x) * v.dx + (z - v.z) * v.dz < -CELL:
            continue
        yield x, z


def draw_rowboat(ch, co, v, walls, x, z, now, wet):
    bob = 0.1 * math.sin(now * 1.4 + x)
    blit_sprite(ch, co, v, walls, ROWBOAT, x, z, bob, bob + 1.1, 2.4, CURB)
    put_lit(ch, co, v, walls, x + 0.9, bob + 0.8, z, "o", EMBER_HOT,
            max(wet, 0.5), now)


def draw_river_lanterns(ch, co, v, walls, now, wet):
    """Lanterns by the hundred going down the river with the current.

    On the night for it. A lattice along the channel, two or three a cell,
    each on its own little bob, the whole field sliding downstream at the
    current's pace - and every one a light, so the reflection pass carries
    them and the water is more light than water."""
    n = int(85.0 / CELL) + 1
    ci = int((v.x - now * LANTERN_DRIFT) / CELL + BIG) - BIG
    for a in range(ci - n, ci + n + 1):
        m = _mix(a, 0, 1427)
        x = a * CELL + now * LANTERN_DRIFT
        i = int(x / CELL + BIG) - BIG
        lo, hi = river_span(i)
        for k in range(4 + m % 3):
            s = (m >> (2 + 5 * k)) & 127
            z = (lo + 0.6 + (hi - lo - 1.2) * (s / 127.0)) * CELL
            z += 0.6 * math.sin(now * 0.4 + s)
            if (x - v.x) * v.dx + (z - v.z) * v.dz < NEAR_Z:
                continue
            put_lit(ch, co, v, walls, x + 0.3 * math.sin(now * 0.7 + s), 0.18, z,
                    "o", (EMBER_HOT, GOLD, BULB)[s % 3], max(wet, 0.5), now)


def bay_centre(i):
    """(x, z) of the middle of the bay in this stretch of river, or None."""
    span = grand_avenue(i)
    if span is None:
        return None
    gi = span[0] + span[1] // 2
    lo, hi = river_span(gi)
    return (gi + 0.5) * CELL, (lo + hi) * 0.5 * CELL


def shells(now):
    """(launch time, seed) of every shell in the air or bursting now. One a
    slot, three in four slots - and in the last twenty seconds before each
    finale, three a slot."""
    k0 = int((now - FW_RISE - FW_LIFE) / FW_SLOT)
    for k in range(k0, int(now / FW_SLOT) + 1):
        finale = (k * FW_SLOT) % FW_FINALE > FW_FINALE - 20.0
        for n in range(3 if finale else 1):
            m = _mix(k, n, 2001)
            if not finale and m % 4 == 0:
                continue
            t0 = k * FW_SLOT + (m >> 4 & 255) / 255.0 * FW_SLOT
            if t0 <= now < t0 + FW_RISE + FW_LIFE:
                yield t0, m


def shell_sparks(bx, bz, t0, m, now, size=1.0, spread=1.0, willow=None):
    """The points of one shell this instant: (x, y, z, glyph, colour-index,
    brightness), going up as a trail and then bursting into a sphere of sparks
    that slow, fall and fade. size scales the burst - a dud is a small one -
    and spread how far from the middle of the bay it goes up."""
    ox = bx + (((m >> 12) & 255) / 255.0 * 120.0 - 60.0) * spread
    oz = bz + (((m >> 20) & 63) / 63.0 * 30.0 - 15.0) * spread
    # Just over the bridge's towers: high enough to clear them, low enough to
    # be in the sky from the bank - at seventy units they went off the top of
    # the screen from anywhere near enough to see them properly.
    top = 30.0 + ((m >> 2) & 15)
    t = now - t0
    if t < FW_RISE:
        y = top * (1.0 - (1.0 - t / FW_RISE) ** 2)
        return [(ox, y - d * 1.5, oz, "|" if d == 0 else ".", -1, 1.0 - d * 0.3)
                for d in range(3)]
    tt = t - FW_RISE
    if willow is None:
        willow = (m >> 26) % 5 == 0
    n = max(5, int((34 if not willow else 24) * min(1.0, size)))
    speed = (17.0 if not willow else 10.0) * size
    out = []
    reach = speed * (1.0 - math.exp(-1.8 * tt)) / 1.8
    sink = (0.9 if not willow else 2.2) * tt * tt
    fade = 1.0 - tt / FW_LIFE
    for k in range(n):
        # Spread over the sphere by the golden angle, turned per shell.
        y_ = 1.0 - 2.0 * (k + 0.5) / n
        r = math.sqrt(max(0.0, 1.0 - y_ * y_))
        a = k * 2.399963 + (m >> 8 & 63)
        dx, dz = r * math.cos(a), r * math.sin(a)
        x, y, z = ox + dx * reach, top + y_ * reach - sink, oz + dz * reach
        glyph = "*" if tt < 0.5 else ("+" if tt < 1.2 else ("." if fade > 0.2
                                                            else "'"))
        out.append((x, y, z, glyph, -2 if willow else (m >> 28) & 7, fade))
    return out


def lighthouse_info(i):
    """The lighthouse in this stretch as a place you can go into, or None:
    where it stands, its door at the foot facing the bridge's landing, where
    you come out again, and where a show fired from its gallery goes up -
    over the bay between the bridge and the carnival's wheel, so from up
    there the three are in the one view."""
    spot = lighthouse_spot(i)
    if spot is None:
        return None
    lx, lz = spot
    span = grand_avenue(i)
    gx = (span[0] + span[1] * 0.5) * CELL
    (wx, _), _, _, _ = carnival_spots(carnival_col(span[0]))
    bay = bay_centre(i)
    return {"kind": "lighthouse", "x": lx, "z": lz, "height": LIGHT_H,
            "i": int(lx / CELL + BIG) - BIG, "j": int(lz / CELL + BIG) - BIG,
            "door": (lx, lz + LIGHT_DOOR), "exit": (lx, lz + LIGHT_DOOR + 2.6, 0.0),
            "show": ((gx + wx) * 0.5, bay[1])}


def near_lighthouse(x, z, reach):
    """The lighthouse whose middle you are within reach of - which is to say,
    up on its gallery - or None."""
    ci = int(x / CELL + BIG) - BIG
    for k in range(-1, 2):
        spot = lighthouse_spot(ci + k * GRAND_GAP)
        if spot is not None and (spot[0] - x) ** 2 + (spot[1] - z) ** 2 < reach ** 2:
            return lighthouse_info(ci + k * GRAND_GAP)
    return None


def lighthouse_door(x, z):
    """The lighthouse whose door you are standing in, or None."""
    ci = int(x / CELL + BIG) - BIG
    for k in range(-1, 2):
        spot = lighthouse_spot(ci + k * GRAND_GAP)
        if spot is None:
            continue
        dx, dz = spot[0], spot[1] + LIGHT_DOOR
        if (dx - x) ** 2 + (dz - z) ** 2 < CASINO_REACH ** 2:
            return lighthouse_info(ci + k * GRAND_GAP)
    return None


def gallery_view(t, yaw, width, height):
    """The camera on the lighthouse's gallery, round the lantern: at the rail
    on whichever side you are facing, and turning walks you round it, the way
    a sky deck's roof does."""
    x = t["x"] + math.sin(yaw) * GALLERY_R
    z = t["z"] + math.cos(yaw) * GALLERY_R
    return View(x, z, yaw, width, height, eye=t["height"] + 1.5, reach=ROOF_REACH)


class Show:
    """One show fired from the box. The cues are laid out when it is lit,
    one bar at a time from SHOW_BARS_EASY and SHOW_BARS_ALL; press() judges a
    press against the nearest cue still waiting and puts the shell up, and
    update() counts the cues that went by and lays out the finale once the
    last has gone. Every shell is (launch time, seed, size, willow), and
    draw_fireworks() draws them over the bay the show was lit for."""

    def __init__(self, now, bay, seed):
        self.t0, self.bay, self.seed = now, bay, seed
        self.beat = 60.0 / SHOW_BPM
        self.cues = []
        for b in range(SHOW_BARS):
            pool = SHOW_BARS_EASY if b < 2 else SHOW_BARS_ALL
            for k, cue in enumerate(pool[_mix(seed, b, 2011) % len(pool)]):
                if cue:
                    self.cues.append({"t": now + (SHOW_COUNT + b * 4 + k) * self.beat,
                                      "big": cue == 2, "got": None})
        self.end = now + (SHOW_COUNT + SHOW_BARS * 4) * self.beat
        self.shots = []
        self.score = self.streak = 0
        self.tally = {"great": 0, "good": 0, "miss": 0, "fizzle": 0}
        self.said = ("", -1e9)            # the last verdict, and when
        self.pressed = -1e9               # and the last time you pressed
        self.best = sum(self.points("great", n) for n in range(len(self.cues)))
        self.finale = False

    def points(self, grade, streak):
        return (100 if grade == "great" else 50) + 10 * min(streak, 10)

    def launch(self, now, size, willow=None):
        self.shots.append((now, _mix(self.seed, len(self.shots), 2013), size, willow))

    def press(self, now):
        """f, on the button. Returns how it was judged."""
        if now >= self.end:
            return None                   # the finale is the show's own
        self.pressed = now
        best = None
        for c in self.cues:
            if c["got"] is None and abs(c["t"] - now) <= SHOW_GOOD and (
                    best is None or abs(c["t"] - now) < abs(best["t"] - now)):
                best = c
        if best is None:
            self.tally["fizzle"] += 1
            self.streak = 0
            self.launch(now, 0.35)
            self.said = ("FIZZLE", now)
            return "fizzle"
        grade = "great" if abs(best["t"] - now) <= SHOW_GREAT else "good"
        best["got"] = grade
        self.score += self.points(grade, self.streak)
        self.streak += 1
        self.tally[grade] += 1
        size = 1.25 if grade == "great" else 0.85
        self.launch(now, size)
        if best["big"]:
            self.launch(now, size, willow=True)      # and a gold willow with it
        self.said = (grade.upper(), now)
        return grade

    def update(self, now):
        global _show_best
        for c in self.cues:
            if c["got"] is None and now > c["t"] + SHOW_GOOD:
                c["got"] = "miss"
                self.tally["miss"] += 1
                self.streak = 0
                self.said = ("MISS", c["t"] + SHOW_GOOD)
        if not self.finale and now >= self.end:
            # The better the show went, the more goes up at the end of it.
            self.finale = True
            _show_best = max(_show_best, self.score)
            for k in range(3 + int(round(21 * self.score / max(1, self.best)))):
                m = _mix(self.seed, k, 2017)
                t = self.end + (m & 1023) / 1023.0 * (SHOW_FINALE - 2.0)
                self.shots.append((t, m, 1.2, None))

    def over(self, now):
        return now >= self.end + SHOW_FINALE + FW_RISE + FW_LIFE

    def word(self, now):
        """What the bar says: the count-in, the last verdict, the finale."""
        if now < self.t0 + SHOW_COUNT * self.beat:
            left = SHOW_COUNT - int((now - self.t0) / self.beat)
            return "GO" if left == 1 else str(left - 1), GOLD
        if now >= self.end:
            return ("FINALE!" if now < self.end + SHOW_FINALE else "SHOW OVER"), FLASH
        word, at = self.said
        if now - at < 0.6:
            return word, {"GREAT": FLASH, "GOOD": GOLD}.get(word, ROU_RED)
        return "", GOLD


_show = None            # the show being fired from a box, if any
_show_best = 0          # the best score tonight


def light_show(now, x, z):
    """f on the lighthouse's gallery: light a show, unless one is already
    going up."""
    global _show
    if _show is not None and not _show.over(now):
        return False
    lh = near_lighthouse(x, z, FIRE_REACH)
    if lh is None:
        return False
    _show = Show(now, lh["show"], int(now * 1000.0) & 0xFFFFFF)
    return True


def show_hint(now, x, z):
    """For the HUD, at the foot of the lighthouse: that you can go up."""
    ci = int(x / CELL + BIG) - BIG
    for k in range(-1, 2):
        spot = lighthouse_spot(ci + k * GRAND_GAP)
        if spot is not None and (spot[0] - x) ** 2 + (spot[1] - z) ** 2 < 20.0 ** 2:
            return "  ~ the lighthouse: in at the door to climb up ~"
    return ""


def gallery_hint(now):
    """For the HUD, up on the gallery: how to light a show, and how it went."""
    if _show is None:
        return "  ~ f lights a show over the bay ~"
    if not _show.over(now):
        return "  ~ your show over the bay ~"
    return "  ~ your show: %d, best %d ~" % (_show.score, _show_best)


def on_the_button(now, x, z):
    """The show you are firing, if you are up on the gallery to fire it."""
    if _show is None or _show.over(now) or near_lighthouse(x, z, FIRE_REACH) is None:
        return None
    return _show


def _put_sparks(ch, co, v, walls, sparks):
    for x, y, z, glyph, tone, b in sparks:
        if b <= 0.0:
            continue
        attr = (EMBER if tone == -1 else GOLD if tone == -2
                else NEON[tone % len(NEON)][0] if b > 0.35
                else NEON[tone % len(NEON)][1])
        put_point(ch, co, v, walls, x, y, z, glyph, attr)


def draw_fireworks(ch, co, v, walls, now, wet):
    """The show, if tonight is the night and the bay is in reach - and the one
    somebody is firing from the headland, whatever night it is."""
    if _show is not None and ((_show.bay[0] - v.x) ** 2 + (_show.bay[1] - v.z) ** 2
                              < FW_REACH ** 2):
        for t0, m, size, willow in _show.shots:
            if t0 <= now < t0 + FW_RISE + FW_LIFE:
                _put_sparks(ch, co, v, walls,
                            shell_sparks(_show.bay[0], _show.bay[1], t0, m, now,
                                         size, SHOW_SPREAD, willow))
    if not night(now)["fireworks"]:
        return
    ci = int(v.x / CELL + BIG) - BIG
    for k in range(-1, 2):
        bay = bay_centre(ci + k * GRAND_GAP)
        if bay is None or (bay[0] - v.x) ** 2 + (bay[1] - v.z) ** 2 > FW_REACH ** 2:
            continue
        for t0, m in shells(now):
            _put_sparks(ch, co, v, walls, shell_sparks(bay[0], bay[1], t0, m, now))


SHOW_BAR_W = 60         # the widest the cue bar gets, in columns


def draw_show_bar(ch, co, show, now):
    """The bar along the bottom while you are on the button: cues coming in
    from the left to the line on the right, the beats between them dotted,
    and under it how the show is going. Drawn over the view, on a cleared
    strip so it stays readable over the bay."""
    height, width = len(ch), len(ch[0])
    if width < 40 or height < 10:
        return
    tw = min(SHOW_BAR_W, width - 18)
    x0 = (width - tw - 14) // 2
    hit = x0 + 1 + tw                                # the line you fire on
    for y in (height - 4, height - 3, height - 2):
        for x in range(max(0, x0 - 2), min(width, hit + 14)):
            ch[y][x] = " "
    y = height - 3
    _text(ch, co, y, x0, "[", GOLD_DIM)
    _text(ch, co, y, hit + 1, "]", GOLD_DIM)
    fired = now - show.pressed < 0.15
    _text(ch, co, y, hit, "|", FLASH if fired else GOLD)

    def col(t):
        return int(round(hit - (t - now) / SHOW_AHEAD * tw))

    first = show.t0 + SHOW_COUNT * show.beat
    k = max(0, int((now - 0.5 - first) / show.beat))
    while True:
        t = first + k * show.beat
        if t > now + SHOW_AHEAD or t >= show.end:
            break
        x = col(t)
        if x0 < x < hit:
            _text(ch, co, y, x, ".", GOLD_DIM)
        k += 1
    for c in show.cues:
        x = col(c["t"])
        if not x0 < x <= hit:
            continue
        judged = {"great": ("*", FLASH), "good": ("+", GOLD), "miss": ("x", ROU_RED)}
        glyph, attr = judged.get(c["got"], ("O" if c["big"] else "o", BULB))
        if x == hit and c["got"] is None:
            attr = FLASH
        _text(ch, co, y, x, glyph, attr)
    word, attr = show.word(now)
    _text(ch, co, y, hit + 3, word, attr)
    t = show.tally
    _text(ch, co, height - 2, x0, "great %d  good %d  miss %d  streak %d  score %d" % (
        t["great"], t["good"], t["miss"], show.streak, show.score), GOLD_DIM)
    _text(ch, co, height - 4, x0, "f on the beat", GOLD_DIM)


def fireworks_near(x, z, now):
    """For the HUD: is there a show on, near enough to see."""
    if not night(now)["fireworks"]:
        return False
    ci = int(x / CELL + BIG) - BIG
    for k in range(-1, 2):
        bay = bay_centre(ci + k * GRAND_GAP)
        if bay is not None and (bay[0] - x) ** 2 + (bay[1] - z) ** 2 < 700.0 ** 2:
            return True
    return False


def near_lighthouses(v, reach):
    ci = int(v.x / CELL + BIG) - BIG
    for k in range(-1, 2):
        spot = lighthouse_spot(ci + k * GRAND_GAP)
        if spot is None:
            continue
        rx, rz = spot[0] - v.x, spot[1] - v.z
        if rx * v.dx + rz * v.dz < -CELL or rx * rx + rz * rz > reach * reach:
            continue
        yield spot


def draw_lighthouse(ch, co, v, walls, lx, lz, now, wet):
    """The tower, the lantern room, and the beam going round.

    The tower is a stack of rings in world space, white with red bands, so it
    tapers and stays round from wherever you see it. The beam is the thing: a
    line of points from the lantern out over the water, sweeping a full turn
    every BEAM_TURN seconds, bright near the lamp and fading with distance -
    and it goes over the bridge, the bay and the town without asking any of
    them, which is the point of one."""
    # Up on its gallery the tower is under your feet and the lantern at your
    # back: neither is drawn, and the rail round you is.
    mine = (v.roof is not None and v.roof.get("kind") == "lighthouse"
            and abs(v.roof["x"] - lx) < 0.5 and abs(v.roof["z"] - lz) < 0.5)
    if not mine:
        for k in range(int(LIGHT_H / 0.55)):
            y = k * 0.55
            r = 1.6 - 0.6 * y / LIGHT_H
            band = int(y / 3.5) % 2 == 0
            for a in range(8):
                ang = a * math.tau / 8.0
                put_point(ch, co, v, walls, lx + math.cos(ang) * r, y,
                          lz + math.sin(ang) * r, "|" if a % 2 else "#",
                          ROU_RED if band else MOON_DIM)
        # The lantern room and its roof.
        for a in range(8):
            ang = a * math.tau / 8.0
            put_point(ch, co, v, walls, lx + math.cos(ang) * 1.2, LIGHT_H + 0.6,
                      lz + math.sin(ang) * 1.2, "=", CONCRETE)
            put_point(ch, co, v, walls, lx + math.cos(ang) * 0.6, LIGHT_H + 2.0,
                      lz + math.sin(ang) * 0.6, "^", CONCRETE)
        put_lit(ch, co, v, walls, lx, LIGHT_H + 1.0, lz, "O", FLASH, max(wet, 0.4), now)

        # The door at the foot, lit, facing the landing - from that side.
        if v.z > lz:
            blit_sprite(ch, co, v, walls, ["[#]", "[#]", "[#]"], lx, lz + LIGHT_DOOR,
                        0.0, 2.1, 1.0, BULB)
    else:
        draw_gallery(ch, co, v, lx, lz)

    # The beam, and a fainter one the other way, the way a real lens throws.
    turn = now * math.tau / BEAM_TURN
    for side, far, attr in ((1.0, BEAM_REACH, BULB), (-1.0, BEAM_REACH * 0.5,
                                                      BULB_DIM)):
        dx, dz = math.cos(turn) * side, math.sin(turn) * side
        glyph = ("-" if abs(dx) > 0.85 else "|" if abs(dz) > 0.85
                 else "\\" if dx * dz > 0 else "/")
        d = 2.5
        while d < far:
            px, pz = lx + dx * d, lz + dz * d
            put_point(ch, co, v, walls, px, LIGHT_H + 1.0 - 0.012 * d, pz, glyph,
                      attr if d < far * 0.6 else BULB_DIM)
            # And where it passes over water, it lies on the water.
            if d > 8.0 and water_at(int(px / CELL + BIG) - BIG,
                                    int(pz / CELL + BIG) - BIG):
                put_point(ch, co, v, walls, px, 0.06, pz, ":", attr)
            d += 1.0 + d * 0.03

    # A bench at the point, facing the water, and a lamp by it.
    blit_sprite(ch, co, v, walls, BENCH, lx + 4.0, lz - 2.5, 0.0, 0.9, 1.6, CURB)
    for h in (1.0, 2.0, 2.8):
        put_point(ch, co, v, walls, lx + 6.5, h, lz - 2.5, "|", CONCRETE)
    put_lit(ch, co, v, walls, lx + 6.5, 3.3, lz - 2.5, "o", BULB, max(wet, 0.3), now)



def draw_gallery(ch, co, v, lx, lz):
    """The rail round the lighthouse's gallery, from on it: solved per screen
    column the way the sky deck's parapet is, so it is a solid line however
    near it is - where each column's ray meets the rail's circle, the top
    rail, the uprights every few columns, and the gallery's edge under them."""
    rail_r, top_y, floor_y = GALLERY_R + 1.4, LIGHT_H + 1.0, LIGHT_H
    px, pz = v.x - lx, v.z - lz
    c0 = px * px + pz * pz - rail_r * rail_r            # under nought: inside
    for sx in range(v.width):
        rdx, rdz = v.ray(sx)
        a = rdx * rdx + rdz * rdz
        b = rdx * px + rdz * pz
        t = (-b + math.sqrt(max(0.0, b * b - a * c0))) / a
        if t <= 0.05:
            continue
        top = int(round(v.horizon - (top_y - v.eye) * v.fy / t))
        foot = int(round(v.horizon - (floor_y - v.eye) * v.fy / t))
        for y in range(max(0, top), min(v.height, foot + 1)):
            if y == top:
                ch[y][sx], co[y][sx] = "=", ROU_RED
            elif y == foot:
                ch[y][sx], co[y][sx] = "-", CONCRETE
            elif sx % 4 == 0:
                ch[y][sx], co[y][sx] = "|", CONCRETE


BRIDGE_LAMP_GAP = 6.0    # world units between lamp posts along the parapet
BRIDGE_SEEN = 230.0      # how far off the end lamps are drawn from
LEANER_ODDS = 3          # one bridge in this many has somebody on it


def bridge_edges(i):
    """(x of one railing, x of the other, z at one bank, z at the other)."""
    lo, hi = river_span(i)
    span = road_span(i, XP, 91)
    wide = span[1] if span else 2
    return i * CELL, (i + wide) * CELL, (lo + 0.5) * CELL, (hi - 0.5) * CELL


def leaner_at(i):
    """Where somebody is leaning on this bridge's railing, or None."""
    m = _mix(i, 0, 733)
    if m % LEANER_ODDS or grand_at(i):
        return None
    xa, xb, z0, z1 = bridge_edges(i)
    x = xa if (m >> 4) & 1 else xb
    z = z0 + (z1 - z0) * (0.3 + ((m >> 5) & 7) / 17.0)
    return x, z, m


def put_halo(ch, co, v, walls, x, y, z, attr, wide):
    """A soft blob round a light, in screen space so it survives distance.

    A world-space halo collapses into the lamp's own cell from a hundred units
    off, which is exactly the range this is for."""
    pr = v.project(x, y, z)
    if pr is None:
        return
    sx, sy, d = int(round(pr[0])), int(round(pr[1])), pr[2]
    # Over whatever is behind it - the far bank's walls, usually - but never
    # over another light, which is what the glow is meant to be seen against.
    around = [(-1, 0), (1, 0), (0, -1), (0, 1)]
    if wide:
        around += [(-2, 0), (2, 0)]
    for dx, dy in around:
        tx, ty = sx + dx, sy + dy
        if not (0 <= tx < v.width and 0 <= ty < v.height):
            continue
        under = ch[ty][tx]
        if under.isalnum() or under in "*+@":
            continue
        put_cell(ch, co, v, walls, tx, ty, d, ".", attr)


def draw_bridge_ends(ch, co, v, walls, i, j, now, wet):
    """The four lamps at the banks, taller than the rest and with a glow round
    them, drawn from much further off than the bridge itself.

    They are what makes a crossing findable: walking the bank looking for one,
    the moment you can see a bridge is long before you can see the bridge -
    the same job the club's spill does for the club."""
    xa, xb, z0, z1 = bridge_edges(i)
    near = (i * CELL - v.x) ** 2 + (z0 - v.z) ** 2 < 60.0 ** 2
    for x in (xa, xb):
        for z in (z0, z1):
            for h in (1.4, 2.2, 3.0, 3.8):
                put_point(ch, co, v, walls, x, h, z, "|", CONCRETE)
            put_point(ch, co, v, walls, x, 4.9, z, "n", CONCRETE)
            put_halo(ch, co, v, walls, x, 4.5, z, BULB_DIM, not near)
            put_lit(ch, co, v, walls, x, 4.5, z, "o", BULB, max(wet, 0.3), now)


BRIDGE_ARCH = 7.5       # world units between the piers under a footbridge


def draw_bridge_body(ch, co, v, walls, xa, xb, z0, z1, arches=True):
    """What makes a bridge read as a thing standing over the water rather
    than as more water: a solid stone parapet down each side with a pale
    coping on top, and under it the arches and piers going down into the
    river.

    It used to be a thin grey rail at knee height over a deck of scattered
    dots, and from the bank it was lost in the ripples - reported as "it
    blends in with the water". Everything here is a structure glyph in a
    structure colour, so the reflection leaves it alone and it stays a hard
    band across the river with the lamps' light lying under it."""
    for x in (xa, xb):
        z = z0 - 0.5
        while z <= z1 + 0.5:
            put_point(ch, co, v, walls, x, 1.05, z, "=", ROOF)       # coping
            put_point(ch, co, v, walls, x, 0.7, z, "#", CURB)        # parapet
            put_point(ch, co, v, walls, x, 0.35, z, "#", CURB)
            put_point(ch, co, v, walls, x, 0.02, z, "_", ROOF)       # the deck's edge
            z += 0.5
        if not arches:
            # A suspension deck hangs from its cables: a girder under it, no
            # arches - a solid band from the deck down to the steel.
            z = z0 - 0.5
            while z <= z1 + 0.5:
                put_point(ch, co, v, walls, x, -0.4, z, "#", CONCRETE)
                put_point(ch, co, v, walls, x, -0.8, z, "=", CURB)
                z += 0.5
            continue
        # The arches: from pier to pier, the soffit rising to the crown.
        n = max(1, int(round((z1 - z0) / BRIDGE_ARCH)))
        span = (z1 - z0) / n
        for k in range(n + 1):
            zp = z0 + k * span
            for y in (-0.15, -0.5, -0.85):
                put_point(ch, co, v, walls, x, y, zp, "#", CURB)      # a pier
        for k in range(n):
            za = z0 + k * span
            for s in range(1, 12):
                t = s / 12.0
                y = -0.9 + 0.8 * math.sin(math.pi * t)
                put_point(ch, co, v, walls, x, y, za + t * span,
                          "-" if 0.3 < t < 0.7 else ("/" if t < 0.5 else "\\"),
                          CURB)


def draw_bridge(ch, co, v, walls, i, j, now, wet):
    """A footbridge worth crossing: a railing down each side, warm lamps on
    posts along it, and a string of small lights slung between the lamps.

    The lamps are the point. They are what you see from the bank, and on a
    wet night they are what lies on the water under the bridge, because the
    reflection carries lights and nothing else. They do not blink or flicker -
    the buoys and the club have that, and a bridge is where the city is
    quiet. The festoon between them sags the way the yokocho lanterns do, for
    the same reason: a straight line of dots reads as a fence."""
    xa, xb, z0, z1 = bridge_edges(i)
    draw_bridge_body(ch, co, v, walls, xa, xb, z0, z1)
    for side in (0, 1):
        x = xb if side else xa
        # The lamps, staggered so the two sides are not in step.
        lamps = []
        z = z0 + (BRIDGE_LAMP_GAP * 0.5 if side else 0.0)
        while z <= z1:
            for h in (1.4, 2.2, 3.0):
                put_point(ch, co, v, walls, x, h, z, "|", CONCRETE)
            put_point(ch, co, v, walls, x, 4.1, z, "n", CONCRETE)
            put_lit(ch, co, v, walls, x, 3.7, z, "o", BULB, max(wet, 0.3), now)
            lamps.append(z)
            z += BRIDGE_LAMP_GAP
        # And the festoon, lamp to lamp.
        for a, b in zip(lamps, lamps[1:]):
            steps = 8
            for k in range(1, steps):
                t = k / float(steps)
                y = 2.4 - 0.6 * math.sin(math.pi * t) + 0.05 * math.sin(now + k)
                zz = a + (b - a) * t
                if k % 2:
                    put_lit(ch, co, v, walls, x, y, zz, "o", EMBER_HOT,
                            max(wet, 0.2), now)
                else:
                    put_point(ch, co, v, walls, x, y, zz, ".", CURB)

    # Somebody leaning on the rail, looking down the river. A cigarette that
    # brightens when they draw on it, on a slow count, is the only movement.
    who = leaner_at(i)
    if who is not None:
        x, z, m = who
        blit_sprite(ch, co, v, walls, LEANER, x, z, 0.0, 1.75, 0.95, CURB)
        drag = (now * 0.25 + (m >> 8 & 15) / 16.0) % 1.0 < 0.18
        put_point(ch, co, v, walls, x + 0.4, 1.05, z, "*" if drag else ".",
                  EMBER_HOT if drag else EMBER)


def near_bridges(v, reach):
    """The middle of each crossing in front of you, one per site."""
    n = int(reach / CELL) + 1
    ci = int(v.x / CELL + BIG) - BIG
    cj = int(v.z / CELL + BIG) - BIG
    seen = set()
    for i in range(ci - n, ci + n + 1):
        lo0, hi0 = river_span(i)
        if i in seen or not bridge_at(i, int((lo0 + hi0) * 0.5)):
            continue
        rx = (i + 0.5) * CELL - v.x
        lo, hi = river_span(i)
        mid = (lo + hi) * 0.5
        rz = (mid + 0.5) * CELL - v.z
        if rx * v.dx + rz * v.dz < -CELL or rx * rx + rz * rz > reach * reach:
            continue
        # One per crossing, not one per cell of it.
        for k in range(i - 3, i + 1):
            if bridge_at(k, int(mid)) and not bridge_at(k - 1, int(mid)):
                if k not in seen:
                    seen.add(k)
                    yield k, int(mid)
                break


def near_lots(v, reach):
    """Solid cells within reach that are not behind you."""
    n = int(reach / CELL) + 1
    ci = int(v.x / CELL + BIG) - BIG
    cj = int(v.z / CELL + BIG) - BIG
    for i in range(ci - n, ci + n + 1):
        for j in range(cj - n, cj + n + 1):
            rx = (i + 0.5) * CELL - v.x
            rz = (j + 0.5) * CELL - v.z
            if rx * v.dx + rz * v.dz < -CELL:
                continue
            if not is_open(i, j):
                yield i, j, lot(i, j)


def cycle_crowd():
    global _crowd
    _crowd = (_crowd + 1) % len(CROWDS)
    return CROWDS[_crowd]


def crowd_name():
    return CROWDS[_crowd]


# Traffic. Only on the wide streets - three cells across - and only in two
# lanes down the middle, so the pavements are the walkers' and nothing comes
# down an alley or a narrow street. A lane is slots sliding along at its own
# pace, the way the walkers' are, so cars on a lane never run into each other
# and nothing is stored.
CAR_SLOT = 34.0        # world units between slots along a lane
CAR_REACH = 110.0
CAR_CLEAR = 3.0        # a car this close to you is not drawn: it never drives
                       # through your face, whatever the arithmetic says
TRAFFIC = ["some", "busy", "none"]
_traffic = 0
TRAFFIC_ODDS = {"some": 7, "busy": 3}  # one slot in this many has a car
TRIP_BLOCKS = 3        # a car in town drives this many blocks, then turns off
POLICE_ODDS = 23       # of the cars, one in this many is a police car
BUS_ODDS = 11          # and one in this many on an avenue is a bus

BUS = [
    " ______________ ",
    "|[][][][][][][]|",
    "|______________|",
    "'-oo--------oo-'",
]


def cycle_traffic():
    global _traffic
    _traffic = (_traffic + 1) % len(TRAFFIC)
    return TRAFFIC[_traffic]


def traffic_name():
    return TRAFFIC[_traffic]


def near_cars(v, now, reach=CAR_REACH, every=False):
    """(distance^2, x, z, (dx, dz), kind, seed) for every car in front of you,
    farthest first. kind is "car", "bus" or "police". With every=True, all
    of them in reach, including any too close to draw and any behind you -
    for the HUD and the menu."""
    odds = TRAFFIC_ODDS.get(TRAFFIC[_traffic])
    if odds is None:
        return []
    if night(now)["alien"]:
        now = int((now + _night_skip) / NIGHT_LENGTH) * NIGHT_LENGTH - _night_skip
    out = []
    n = int(reach / CELL) + 1
    ci = int(v.x / CELL + BIG) - BIG
    cj = int(v.z / CELL + BIG) - BIG
    seen = set()
    for axis, centre, period, salt in ((0, ci, XP, 91), (1, cj, ZP, 137)):
        for c in range(centre - n, centre + n + 1):
            span = road_span(c, period, salt)
            if span is None or span[1] < 3 or (axis, span[0]) in seen:
                continue
            seen.add((axis, span[0]))
            mid = (span[0] + span[1] * 0.5) * CELL
            for d in (1, -1):
                m = _mix(axis * 7919 + span[0], d, 2301)
                pace = (8.0 + (m & 7) * 0.5) * d
                off = mid + 2.0 * d * (1 if axis == 0 else -1)
                along0 = v.z if axis == 0 else v.x
                shift = now * pace + (m >> 3 & 1023) / 1023.0 * CAR_SLOT
                k0 = int(math.floor((along0 - reach - shift) / CAR_SLOT))
                ph = m >> 13 & 3
                for k in range(k0, k0 + int(2 * reach / CAR_SLOT) + 2):
                    along = k * CAR_SLOT + shift
                    trip = _trip_of(axis, along, ph)
                    g = _mix(axis * 7919 + span[0], (d * 100003 + k) * 977 + trip,
                             2303)
                    if g % odds or not _trip_ok(axis, span[0], off, trip, ph):
                        continue
                    x, z = (off, along) if axis == 0 else (along, off)
                    rx, rz = x - v.x, z - v.z
                    d2 = rx * rx + rz * rz
                    if d2 > reach * reach:
                        continue
                    if not every and (d2 < CAR_CLEAR ** 2
                                      or rx * v.dx + rz * v.dz < SPRITE_NEAR):
                        continue
                    i = int(x / CELL + BIG) - BIG
                    j = int(z / CELL + BIG) - BIG
                    if not road_at(i, j) or not dry_at(x, z):
                        continue                  # the river, the woods
                    kind = ("police" if (g >> 6) % POLICE_ODDS == 0 else
                            "bus" if axis == 0 and (g >> 11) % BUS_ODDS == 0
                            else "car")
                    dirv = (0.0, float(d)) if axis == 0 else (float(d), 0.0)
                    out.append((d2, x, z, dirv, kind, g))
    out.sort(reverse=True)
    return out


def _crossing(axis, b):
    """Where the cross road numbered b is along a lane on this axis - its
    middle, in world units - or None if it was built over."""
    period, salt = (ZP, 137) if axis == 0 else (XP, 91)
    for r in range(period):
        span = road_span(b * period + r, period, salt)
        if span is not None:
            return (span[0] + span[1] * 0.5) * CELL
    return None


def _trip_of(axis, along, ph):
    """Which trip a point along a lane is on. A trip is TRIP_BLOCKS blocks,
    from the middle of one crossing to the middle of another - so a car turns
    on and off at a junction, never out of thin air mid-block."""
    period = ZP if axis == 0 else XP
    b = int(math.floor(along / (period * CELL)))
    mid = _crossing(axis, b)
    if mid is not None and along < mid:
        b -= 1
    return (b + ph) // TRIP_BLOCKS


def _trip_ok(axis, a0, off, trip, ph):
    """Can a car drive this trip at all: both ends real crossings, and dry
    road the whole way - no river without a bridge for cars, no footbridge,
    no lake, no woods. Once a lane every street ran on into the water and
    the cars vanished at the bank and came up out of it on the far side.
    The big bridge is the one crossing that carries traffic."""
    key = (axis, a0, round(off, 1), trip)
    hit = _trip_cache.get(key)
    if hit is None:
        _evict(_trip_cache, 20000)
        b0 = trip * TRIP_BLOCKS - ph
        start, end = _crossing(axis, b0), _crossing(axis, b0 + TRIP_BLOCKS)
        hit = start is not None and end is not None
        along = start or 0.0
        while hit and along <= end:
            x, z = (off, along) if axis == 0 else (along, off)
            i = int(x / CELL + BIG) - BIG
            j = int(z / CELL + BIG) - BIG
            if not road_at(i, j) or (water_at(i, j)
                                     and not (bridge_at(i, j) and grand_at(i))):
                hit = False
            along += CELL * 0.5
        _trip_cache[key] = hit
    return hit


def hwy_span(k):
    """(first cell, width) of the avenue the highway runs over, if avenue k
    is one of those: one of the three-cell-wide ones, and not the El's or
    the big bridge's."""
    hit = _hwy_cache.get(k, 0)
    if hit == 0:
        hit = None
        if _mix(k, 0, 2501) % HWY_EVERY == 0 and el_span(k) is None:
            for r in range(XP):
                span = road_span(k * XP + r, XP, 91)
                if span is not None:
                    if span[1] >= 3 and not grand_at(span[0]):
                        hit = span
                    break
        _hwy_cache[k] = hit
    return hit


def hwy_at(i):
    span = hwy_span(i // XP)
    return span is not None and span[0] <= i < span[0] + span[1]


def near_hwys(v, reach):
    """(x0, x1) of each highway avenue within reach across."""
    k0 = int((v.x - reach) / (XP * CELL)) - 1
    for k in range(k0, k0 + int(2 * reach / (XP * CELL)) + 3):
        span = hwy_span(k)
        if span is None:
            continue
        x0, x1 = span[0] * CELL, (span[0] + span[1]) * CELL
        if abs((x0 + x1) * 0.5 - v.x) < reach:
            yield x0, x1


def hwy_lanes(x0, x1):
    """(lane x, direction) for the four lanes: two each way, driving on the
    right of the median as you look along them."""
    xm = (x0 + x1) * 0.5
    return ((xm + 1.6, 1), (xm + 4.0, 1), (xm - 1.6, -1), (xm - 4.0, -1))


def hwy_cars(x0, x1, z, reach, now):
    """(z, lane x, direction, seed) of every car on the highway within reach."""
    if TRAFFIC_ODDS.get(TRAFFIC[_traffic]) is None:
        return
    if night(now)["alien"]:
        now = int((now + _night_skip) / NIGHT_LENGTH) * NIGHT_LENGTH - _night_skip
    for n, (lx, d) in enumerate(hwy_lanes(x0, x1)):
        m = _mix(int(x0), n, 2503)
        fast = 2.5 if abs(lx - (x0 + x1) * 0.5) < 2 else 0.0   # the inside lane
        pace = (19.0 + (m & 7) * 0.8 + fast) * d
        shift = now * pace + (m >> 3 & 1023) / 1023.0 * HWY_SLOT
        k0 = int(math.floor((z - reach - shift) / HWY_SLOT))
        for k in range(k0, k0 + int(2 * reach / HWY_SLOT) + 2):
            g = _mix(int(x0) * 4 + n, k, 2505)
            if g % HWY_ODDS:
                continue
            yield k * HWY_SLOT + shift, lx, d, g


def hwy_near(x, z):
    """Close enough to the highway to hear it."""
    for x0, x1 in near_hwys(View(x, z, 0.0, 2, 2), 40.0):
        if x0 - 25.0 < x < x1 + 25.0:
            return True
    return False


def draw_hwy(ch, co, v, walls, x0, x1, now, wet):
    """The highway: piers down the median, a cross head on each, the deck's
    two edges and a parapet along them, tall lamps along the middle, and the
    traffic - headlights coming, tail lights going.

    Points laid only over the stretch in front of you, like the El. From
    right under it you see the deck and not the cars: they are on top of it."""
    xm = (x0 + x1) * 0.5
    dx0, dx1 = x0 + PAVE + 0.4, x1 - PAVE - 0.4
    reach = HWY_REACH if v.eye < 10.0 else ROOF_REACH
    zs = v.z - (reach if v.dz < 0 else CELL * 2)
    ze = v.z + (reach if v.dz >= 0 else CELL * 2)
    if abs(v.dx) > 0.3:
        zs, ze = v.z - reach * 0.6, v.z + reach * 0.6
    z = math.floor(zs / HWY_PIER) * HWY_PIER
    while z <= ze:
        for px in (xm - 0.4, xm + 0.4):
            y = 0.0
            while y < HWY_H - 0.6:
                put_point(ch, co, v, walls, px, y, z, "|", CONCRETE)
                y += 0.7
        x = dx0
        while x <= dx1:
            put_point(ch, co, v, walls, x, HWY_H - 0.5, z, "=", CONCRETE)
            x += 0.9
        z += HWY_PIER
    # The deck's edges: a solid band, not a dotted line - so the points are
    # spaced by how far off they are, close together near you, where a fixed
    # spacing left gaps the shop signs behind showed through.
    for gx in (dx0, dx1):
        z = zs
        while z <= ze:
            for y, g, a in ((HWY_H - 0.3, "=", CURB), (HWY_H, "=", CURB),
                            (HWY_H + 0.6, "-", CONCRETE)):
                put_point(ch, co, v, walls, gx, y, z, g, a)
            z += max(0.3, math.hypot(gx - v.x, z - v.z) * 0.018)
    z = math.floor(zs / HWY_LAMP) * HWY_LAMP
    while z <= ze:
        for y in (HWY_H + 1.2, HWY_H + 2.2):
            put_point(ch, co, v, walls, xm, y, z, "|", CONCRETE)
        put_point(ch, co, v, walls, xm, HWY_H + 3.0, z, "o", EMBER_HOT)
        z += HWY_LAMP
    if dx0 < v.x < dx1 and v.eye < HWY_H:
        return                                   # under the deck
    for cz, lx, d, g in hwy_cars(x0, x1, v.z, reach, now):
        if not zs - 5 < cz < ze + 5:
            continue
        coming = (v.z - cz) * d > 0.0
        y = HWY_H + 0.9
        if (cz - v.z) ** 2 + (lx - v.x) ** 2 < 900.0:
            paint = tone_colour(("mid", "far", "cold", "warm")[g >> 3 & 3], 0.7)
            for k in range(-2, 3):
                put_point(ch, co, v, walls, lx, y + 0.5, cz - d * k * 0.6, "_", paint)
        for hx in (lx - 0.45, lx + 0.45):
            put_point(ch, co, v, walls, hx, y, cz, "*" if coming else ".",
                      FLASH if coming else ROU_RED)


def police_light(now, seed):
    """Which colour the lightbar is showing: red, blue, red, blue, fast."""
    return ROU_RED if int(now * 6.0 + (seed & 7)) % 2 else NEON[2][0]


def draw_traffic(ch, co, v, walls, now, wet):
    """The cars, farthest first: the body, and the lights at whichever end is
    towards you - headlights coming, red tail lights going - and a police
    car's lightbar on top."""
    for _, x, z, (dx, dz), kind, g in near_cars(v, now):
        coming = (v.x - x) * dx + (v.z - z) * dz > 0.0
        paint = tone_colour(("mid", "far", "cold", "warm", "rust")[g >> 3 & 3],
                            (g >> 8 & 15) / 15.0)
        if kind == "bus":
            blit_sprite(ch, co, v, walls, BUS, x, z, 0.0, 2.8, 2.9, paint)
            half, h = 1.2, 0.7
            put_lit(ch, co, v, walls, x, 2.0, z, "o", BULB_DIM, wet, now)
        elif kind == "police":
            blit_sprite(ch, co, v, walls, CAR, x, z, 0.0, 1.35, 1.9, MOON_DIM)
            half, h = 0.75, 0.55
            bar = police_light(now, g)
            put_lit(ch, co, v, walls, x - 0.25 * dz, 1.55, z - 0.25 * dx, "=",
                    bar, max(wet, 0.5), now)
            put_lit(ch, co, v, walls, x + 0.25 * dz, 1.55, z + 0.25 * dx, "=",
                    NEON[2][0] if bar == ROU_RED else ROU_RED, max(wet, 0.5), now)
        else:
            blit_sprite(ch, co, v, walls, CAR, x, z, 0.0, 1.35, 1.9, paint)
            half, h = 0.75, 0.55
        end = 1.0 if coming else -1.0
        ex, ez = x + dx * end * 1.9, z + dz * end * 1.9
        for s in (-half, half):
            lx, lz = ex - dz * s, ez + dx * s
            put_lit(ch, co, v, walls, lx, h, lz, "o" if coming else "*",
                    FLASH if coming else ROU_RED, max(wet, 0.3), now)


def siren_near(x, z, now):
    """For the HUD: a police car within earshot."""
    v = View(x, z, 0.0, 2, 2)
    return any(kind == "police" and d2 < 140.0 ** 2
               for d2, _, _, _, kind, _ in near_cars(v, now, 140.0, every=True))


def near_walkers(v, now):
    """(x, z, phase, colour, umbrella) for everyone walking in front of you.

    Streets both ways - avenues run along z, cross streets along x - found by
    stepping across the view and asking road_span(), one lane per pavement.
    On the night the sky has something in it they have all stopped where they
    were when it started, and look up."""
    odds = CROWD_ODDS.get(CROWDS[_crowd])
    if odds is None:
        return
    nt = night(now)
    if nt["alien"]:
        now = int((now + _night_skip) / NIGHT_LENGTH) * NIGHT_LENGTH - _night_skip
    n = int(WALK_REACH / CELL) + 1
    ci = int(v.x / CELL + BIG) - BIG
    cj = int(v.z / CELL + BIG) - BIG
    seen = set()
    for axis, centre, period, salt, across in ((0, ci, XP, 91, v.x),
                                               (1, cj, ZP, 137, v.z)):
        for c in range(centre - n, centre + n + 1):
            span = road_span(c, period, salt)
            if span is None or (axis, span[0]) in seen:
                continue
            seen.add((axis, span[0]))
            for side in (0, 1):
                edge = (span[0] + (span[1] if side else 0)) * CELL
                off = edge + (-0.9 if side else 0.9)
                m = _mix(axis * 7919 + span[0], side, 1701)
                pace = (1.1 + (m & 7) * 0.08) * (1 if (m >> 3) & 1 else -1)
                along0 = (v.z if axis == 0 else v.x)
                shift = now * pace
                k0 = int(math.floor((along0 - WALK_REACH - shift) / WALK_SLOT))
                for k in range(k0, k0 + int(2 * WALK_REACH / WALK_SLOT) + 2):
                    g = _mix(axis * 7919 + span[0], side * 100003 + k, 1703)
                    if g % odds:
                        continue
                    along = k * WALK_SLOT + shift + (g >> 4 & 7) * 0.3
                    x, z = (off, along) if axis == 0 else (along, off)
                    rx, rz = x - v.x, z - v.z
                    if rx * v.dx + rz * v.dz < SPRITE_NEAR:
                        continue
                    if rx * rx + rz * rz > WALK_REACH ** 2:
                        continue
                    i = int(x / CELL + BIG) - BIG
                    j = int(z / CELL + BIG) - BIG
                    if not road_at(i, j) or not dry_at(x, z):
                        continue
                    phase = (along / 0.8) % 2.0
                    yield (rx * rx + rz * rz, x, z, phase, g,
                           nt["alien"])


def draw_walkers(ch, co, v, walls, now, wet):
    """Everyone out walking, farthest first. In the rain one in two has an
    umbrella up, and the coats are the warm and dim colours of the city."""
    people = sorted(near_walkers(v, now), reverse=True)
    for _, x, z, phase, g, stopped in people:
        coat = (CURB, BARK, tone_colour("warm", (g >> 8 & 15) / 15.0),
                tone_colour("cold", (g >> 12 & 15) / 15.0))[g >> 16 & 3]
        if stopped:
            blit_sprite(ch, co, v, walls, LOOK_UP, x, z, 0.0, SMOKER_H, SMOKER_W,
                        coat)
        elif wet > 0.25 and (g >> 18) & 1:
            blit_sprite(ch, co, v, walls, UMBRELLA, x, z, 0.0, SMOKER_H * 1.25,
                        SMOKER_W * 1.4, coat)
        else:
            blit_sprite(ch, co, v, walls, WALKER_A if phase < 1.0 else WALKER_B,
                        x, z, 0.0, SMOKER_H, SMOKER_W, coat)


_el_cache = {}
_hwy_cache = {}
_trip_cache = {}


def el_span(k):
    """(first cell, width) of the avenue the elevated runs over, if avenue
    k is one of those, else None."""
    hit = _el_cache.get(k, 0)
    if hit == 0:
        hit = None
        if _mix(k, 0, 1801) % EL_EVERY == 0:
            for r in range(XP):
                span = road_span(k * XP + r, XP, 91)
                if span is not None:
                    hit = span
                    break
        _el_cache[k] = hit
    return hit


def el_at(i):
    """Does the elevated run over this column of cells."""
    span = el_span(i // XP)
    return span is not None and span[0] <= i < span[0] + span[1]


def el_runs(x, z):
    """The line stops at the woods and at the headland, where the avenue does."""
    i = int(x / CELL + BIG) - BIG
    j = int(z / CELL + BIG) - BIG
    return not woods_at(i, j) and not headland_at(i, j)


def near_els(v, reach):
    """(x0, x1) of each elevated avenue within reach across."""
    k0 = int((v.x - reach) / (XP * CELL)) - 1
    for k in range(k0, k0 + int(2 * reach / (XP * CELL)) + 3):
        span = el_span(k)
        if span is None:
            continue
        x0, x1 = span[0] * CELL, (span[0] + span[1]) * CELL
        if abs((x0 + x1) * 0.5 - v.x) < reach:
            yield x0, x1


def el_trains(x0, x1, z, reach, now):
    """(z of the head, direction, track x) for each train within reach of z."""
    xm = (x0 + x1) * 0.5
    for d, tx in ((1, xm - 1.6), (-1, xm + 1.6)):
        off = (_mix(int(x0), d, 1803) & 1023) / 1023.0 * EL_SPACING
        head0 = d * EL_SPEED * now + off
        n0 = int(math.floor((z - reach - head0) / EL_SPACING)) - 1
        for n in range(n0, n0 + int(2 * reach / EL_SPACING) + 3):
            head = n * EL_SPACING + head0
            if abs(head - z) < reach + EL_CARS * EL_CAR:
                yield head, d, tx


def el_overhead(x, z, now):
    """Is a train passing over you, near enough to be heard."""
    for x0, x1 in near_els(View(x, z, 0.0, 2, 2), 30.0):
        if not x0 - 6.0 < x < x1 + 6.0:
            continue
        for head, d, _ in el_trains(x0, x1, z, 40.0, now):
            tail = head - d * EL_CARS * EL_CAR
            if min(head, tail) - 20.0 < z < max(head, tail) + 20.0:
                return True
    return False


def draw_el(ch, co, v, walls, x0, x1, now, wet):
    """The viaduct, and the trains on it.

    Columns stand on both kerbs every EL_COL units; the deck is two girders
    along the top with cross beams between, the rails on top of that. Points
    are laid along z only over the stretch in front of you, because a column
    of points down an avenue is cheap and an avenue is long."""
    xm = (x0 + x1) * 0.5
    cx0, cx1 = x0 + 0.5, x1 - 0.5
    ahead = v.dz
    span = EL_REACH
    zs = v.z - (span if ahead < 0 else CELL * 2)
    ze = v.z + (span if ahead >= 0 else CELL * 2)
    if abs(v.dx) > 0.3:                  # looking across it: the stretch in view
        zs, ze = v.z - span * 0.6, v.z + span * 0.6
    # Columns and cross beams.
    z = math.floor(zs / EL_COL) * EL_COL
    while z <= ze:
        if el_runs(xm, z):
            for cx in (cx0, cx1):
                y = 0.0
                while y < EL_H:
                    put_point(ch, co, v, walls, cx, y, z, "|", CONCRETE)
                    y += 0.7
            x = cx0
            while x <= cx1:
                put_point(ch, co, v, walls, x, EL_H - 0.4, z, "=", CONCRETE)
                x += 0.9
        z += EL_COL
    # The girders and rails, and the station canopies.
    z = math.floor(zs / 1.2) * 1.2
    while z <= ze:
        if el_runs(xm, z):
            for gx in (cx0, cx1):
                put_point(ch, co, v, walls, gx, EL_H, z, "=", CURB)
            for tx in (xm - 1.6, xm + 1.6):
                put_point(ch, co, v, walls, tx, EL_H + 0.25, z, "-", CONCRETE)
        z += 1.2
    gap = EL_STATION * CELL
    for k in range(int(zs / gap) - 1, int(ze / gap) + 2):
        sz = (k * EL_STATION + (_mix(int(x0), k, 1805) % 8)) * CELL
        if not el_runs(xm, sz) or not zs - 20 < sz < ze + 20:
            continue
        for dz in range(-6, 7, 2):
            for gx in (cx0 - 0.6, cx1 + 0.6):
                put_point(ch, co, v, walls, gx, EL_H + 3.2, sz + dz, "_", CURB)
            if dz % 4 == 0:
                put_lit(ch, co, v, walls, xm, EL_H + 3.0, sz + dz, "o", BULB,
                        max(wet, 0.3), now)
        for gx in (cx0 - 0.6, cx1 + 0.6):
            for y in (EL_H + 0.8, EL_H + 1.8, EL_H + 2.8):
                put_point(ch, co, v, walls, gx, y, sz - 6, "|", CONCRETE)
                put_point(ch, co, v, walls, gx, y, sz + 6, "|", CONCRETE)
    # The trains.
    for head, d, tx in el_trains(x0, x1, v.z, EL_REACH, now):
        for c in range(EL_CARS):
            front = head - d * c * EL_CAR
            back = front - d * (EL_CAR - 0.6)
            lo, hi = min(front, back), max(front, back)
            if not el_runs(xm, (lo + hi) * 0.5):
                continue
            z = lo
            while z <= hi:
                put_point(ch, co, v, walls, tx, EL_H + 3.0, z, "_", CURB)
                put_point(ch, co, v, walls, tx, EL_H + 0.6, z, "=", CURB)
                lit = int((z - lo) / 1.0) % 2 == 0
                put_lit(ch, co, v, walls, tx, EL_H + 1.9, z,
                        "o" if lit else "|", BULB if lit else CURB,
                        max(wet, 0.2), now)
                z += 0.5
            for edge in (lo, hi):
                for y in (EL_H + 1.0, EL_H + 1.9, EL_H + 2.7):
                    put_point(ch, co, v, walls, tx, y, edge, "|", CURB)
        # The headlights, and the sparks underneath now and then.
        for hx in (tx - 0.5, tx + 0.5):
            put_lit(ch, co, v, walls, hx, EL_H + 1.2, head, "*", FLASH,
                    max(wet, 0.3), now)
        if int(now * 7 + head) % 9 == 0:
            put_point(ch, co, v, walls, tx, EL_H + 0.1, head - d * 3.0, "*",
                      EMBER_HOT)


_tower_blocks = {}


def towers_in_block(bi, bj):
    """The sky-deck towers in city block (bi, bj), worked out once. Asked per
    cell, the hash over every cell in 150 units was four thousand calls a
    frame and a millisecond on every street, beacon or no beacon."""
    key = (bi, bj)
    hit = _tower_blocks.get(key)
    if hit is None:
        _evict(_tower_blocks, 4000)
        hit = []
        for i in range(bi * XP, bi * XP + XP):
            for j in range(bj * ZP, bj * ZP + ZP):
                if _mix(i, j, 1907) % TOWER_ODDS or is_open(i, j):
                    continue
                t = lot(i, j)["tower"]
                if t is not None:
                    hit.append(t)
        _tower_blocks[key] = hit
    return hit


def near_towers(v, reach):
    """Sky-deck towers in front of you, for their beacons."""
    b0, b1 = int((v.x - reach) // (XP * CELL)), int((v.x + reach) // (XP * CELL))
    c0, c1 = int((v.z - reach) // (ZP * CELL)), int((v.z + reach) // (ZP * CELL))
    for bi in range(b0, b1 + 1):
        for bj in range(c0, c1 + 1):
            for t in towers_in_block(bi, bj):
                rx = (t["i"] + 0.5) * CELL - v.x
                rz = (t["j"] + 0.5) * CELL - v.z
                if rx * v.dx + rz * v.dz < -CELL or rx * rx + rz * rz > reach * reach:
                    continue
                yield t


def draw_tower_beacon(ch, co, v, walls, t, now, wet):
    """A red light on the roof, blinking, and a mast under it - the thing you
    find a sky deck by from across town."""
    x, z = (t["i"] + 0.5) * CELL, (t["j"] + 0.5) * CELL
    for k in range(5):
        put_point(ch, co, v, walls, x, t["height"] + k * 0.8, z, "|", CONCRETE)
    on = int(now * 1.3 + t["i"]) % 2 == 0
    put_lit(ch, co, v, walls, x, t["height"] + 4.4, z, "*" if on else ".",
            ROU_RED if on else CONCRETE, max(wet, 0.3), now)


_cinema_blocks = {}


def cinemas_in_block(bi, bj):
    """The cinemas in city block (bi, bj), worked out once, for the reason
    towers_in_block() is: their searchlights are seen from a long way off."""
    key = (bi, bj)
    hit = _cinema_blocks.get(key)
    if hit is None:
        _evict(_cinema_blocks, 4000)
        hit = []
        for i in range(bi * XP, bi * XP + XP):
            for j in range(bj * ZP, bj * ZP + ZP):
                if _mix(i, j, 1961) % CLUB_ODDS or is_open(i, j):
                    continue
                c = lot(i, j)["cinema"]
                if c is not None:
                    hit.append(c)
        _cinema_blocks[key] = hit
    return hit


def near_cinemas(v, reach):
    b0, b1 = int((v.x - reach) // (XP * CELL)), int((v.x + reach) // (XP * CELL))
    c0, c1 = int((v.z - reach) // (ZP * CELL)), int((v.z + reach) // (ZP * CELL))
    for bi in range(b0, b1 + 1):
        for bj in range(c0, c1 + 1):
            for c in cinemas_in_block(bi, bj):
                rx = (c["i"] + 0.5) * CELL - v.x
                rz = (c["j"] + 0.5) * CELL - v.z
                if rx * rx + rz * rz > reach * reach:
                    continue
                yield c


def search_beam(cin, side, now):
    """(base, direction) of one of a cinema's two searchlights. They stand at
    the front corners of the roof and sweep mirror to mirror, so they cross
    over the street and open out again, the way a premiere's do."""
    nx, nz = FACES[cin["door"]]
    tx, tz = -nz, nx
    base = face_point(cin["i"], cin["j"], cin["door"], 1.0 if side < 0 else CELL - 1.0,
                      -0.8, cin["height"] + 0.4)
    swing = side * 1.2 * math.sin(now * 0.37 + cin["offset"])
    tilt = SEARCH_LEAN + 0.2 * math.sin(now * 0.23 + cin["offset"] * 0.5 + side)
    hx = nx * math.cos(swing) + tx * math.sin(swing)
    hz = nz * math.cos(swing) + tz * math.sin(swing)
    st = math.sin(tilt)
    return base, (hx * st, math.cos(tilt), hz * st)


def draw_searchlights(ch, co, v, walls, cin, now):
    """Two beams sweeping up off the roof - the thing you find the pictures
    by from across town. A line of points like the lighthouse's beam, each
    one's glyph taken from which way the beam runs on screen right there."""
    for side in (-1.0, 1.0):
        (bx, by, bz), (dx, dy, dz) = search_beam(cin, side, now)
        put_point(ch, co, v, walls, bx, by, bz, "o", FLASH)
        prev = v.project(bx, by, bz)
        s = 1.0
        while s < SEARCH_LONG:
            x, y, z = bx + dx * s, by + dy * s, bz + dz * s
            pr = v.project(x, y, z)
            if pr is not None and prev is not None:
                ax, ay = pr[0] - prev[0], (pr[1] - prev[1]) * 2.0
                glyph = ("|" if abs(ax) < 0.4 * abs(ay) else
                         "-" if abs(ay) < 0.4 * abs(ax) else
                         "/" if ax * ay < 0 else "\\")
                put_cell(ch, co, v, walls, int(round(pr[0])), int(round(pr[1])),
                         pr[2], glyph, BEAM if s < SEARCH_LONG * 0.4 else BEAM_DIM)
            prev = pr
            # About a cell apart on screen: close together near, further
            # apart in the world the further off the beam is.
            s += 0.8 + (0.012 * pr[2] if pr is not None else 2.0)


def party_light(now):
    """The roof party's lights this instant: white on the kick, the bar's
    colour for a little after, dark between - and the strobe let go for the
    last bar of every eight. On the strange night it plays to the sky, like
    the club."""
    sync = city_sync(now)
    if sync is not None:
        return FLASH if sync == "flash" else (None if sync == "off" else NEON[1][0])
    t = now * PARTY_BPM / 60.0
    if (int(t) // 4) % 8 == 7 and int(t * 8) % 2:
        return FLASH
    beat = t % 1.0
    if beat < 0.1:
        return FLASH
    if beat < 0.4:
        return NEON[(int(t) // 4) % len(NEON)][0]
    return None


def draw_spire(ch, co, v, walls, lm, now, wet):
    """The spire over the tower's roof: a tapering mast in the middle of it,
    banded, with the red light on top - and the party's lasers going out over
    the city from the booth, which is how you know from the street there is
    one."""
    x0, z0, x1, z1 = party_roof(lm)
    cx, cz = (x0 + x1) * 0.5, z0 + 1.2
    y = LANDMARK_H
    while y < LANDMARK_H + SPIRE_H:
        r = 1.4 * (1.0 - (y - LANDMARK_H) / SPIRE_H) + 0.15
        for a in range(6):
            ang = a * math.tau / 6.0
            put_point(ch, co, v, walls, cx + math.cos(ang) * r, y,
                      cz + math.sin(ang) * r, "|", MOON_DIM)
        y += 0.8
    on = int(now * 1.1) % 2 == 0
    put_lit(ch, co, v, walls, cx, LANDMARK_H + SPIRE_H + 0.5, cz, "*" if on else ".",
            ROU_RED if on else CONCRETE, max(wet, 0.3), now)
    # The lasers: four of them fanned out from the booth, sweeping, climbing
    # out over the city, a new colour every bar.
    t = now * PARTY_BPM / 60.0
    bx, by, bz = cx, LANDMARK_H + 3.2, z0 + 3.0
    for k in range(4):
        az = math.pi * 0.5 + 0.9 * math.sin(now * 0.6 + k * 1.6)
        el = 0.06 + 0.1 * math.sin(now * 0.45 + k)      # out over the city
        dx, dz = math.cos(az) * math.cos(el), math.sin(az) * math.cos(el)
        dy = math.sin(el)
        attr = NEON[(k * 2 + int(t) // 4) % len(NEON)][0]
        prev = v.project(bx, by, bz)
        d = 1.0
        while d < 150.0:
            pr = v.project(bx + dx * d, by + dy * d, bz + dz * d)
            if pr is not None and prev is not None:
                ax, ay = pr[0] - prev[0], (pr[1] - prev[1]) * 2.0
                glyph = ("|" if abs(ax) < 0.4 * abs(ay) else
                         "-" if abs(ay) < 0.4 * abs(ax) else
                         "/" if ax * ay < 0 else "\\")
                put_cell(ch, co, v, walls, int(round(pr[0])), int(round(pr[1])),
                         pr[2], glyph, attr)
            prev = pr
            d += 0.7 + (0.012 * pr[2] if pr is not None else 2.0)


def draw_party_floor(ch, co, v, lm, now):
    """Standing on the tower's roof: the parapet round it and the floor under
    your feet, solved per screen column the way the sky deck's parapet is -
    where each column's ray leaves the roof, the coping and the wall below
    it, and nearer than that the floor, a dance floor of tiles that light on
    the beat. The floor is what this needs that the sky decks never did: they
    stand you at the parapet, and from the middle of a roof the street a
    hundred units down showed straight through it."""
    x0, z0, x1, z1 = party_roof(lm)
    h = LANDMARK_H
    cap = h + 1.0
    t = now * PARTY_BPM / 60.0
    lamp = party_light(now)
    for sx in range(v.width):
        rdx, rdz = v.ray(sx)
        out = 1e9
        for d, lo, hi, p in ((rdx, x0, x1, v.x), (rdz, z0, z1, v.z)):
            if d > 1e-9:
                out = min(out, (hi - p) / d)
            elif d < -1e-9:
                out = min(out, (lo - p) / d)
        if out <= 0.05 or out > 80.0:
            continue
        top = int(round(v.horizon - (cap - v.eye) * v.fy / out))
        base = int(round(v.horizon + (v.eye - h) * v.fy / out))
        for y in range(max(0, top), v.height):
            if y <= base:
                if y == top:
                    ch[y][sx], co[y][sx] = "=", ROOF
                elif (y - top) % 2 == 0:
                    ch[y][sx], co[y][sx] = "-", CONCRETE
                else:
                    ch[y][sx], co[y][sx] = " ", 0
                continue
            d = (v.eye - h) * v.fy / max(1e-6, y - v.horizon)
            wx, wz = v.x + rdx * d, v.z + rdz * d
            tx, tz = int((wx - x0) / 2.0), int((wz - z0) / 2.0)
            dance = x0 + 4.0 < wx < x1 - 4.0 and z0 + 5.0 < wz < z1 - 4.0
            if dance and (tx + tz + int(t)) % 3 == 0:
                ch[y][sx] = "#"
                co[y][sx] = (lamp if lamp is not None
                             else NEON[(tx * 3 + tz) % len(NEON)][1])
            elif _mix(int(wx * 2.0), int(wz * 2.0), 2603) % 9 == 0:
                ch[y][sx], co[y][sx] = ".", CONCRETE
            else:
                ch[y][sx], co[y][sx] = " ", 0


def party_dancers(lm):
    """Where everybody at the party is standing, worked out from the
    landmark: a crowd on the dance floor in front of the booth."""
    x0, z0, x1, z1 = party_roof(lm)
    out = []
    for k in range(22):
        m = _mix(lm["seed"], k, 2605)
        out.append((x0 + 5.0 + (m & 255) / 255.0 * (x1 - x0 - 10.0),
                    z0 + 6.0 + ((m >> 8) & 255) / 255.0 * (z1 - z0 - 11.0), m))
    return out


def lift_hut(lm):
    """Where the lift comes up onto the roof: by the south parapet."""
    x0, z0, x1, z1 = party_roof(lm)
    return x0 + 4.0, z1 - 1.8


def draw_party(ch, co, v, walls, lm, now, wet):
    """The party on the roof: the booth at the north end with the DJ and the
    stacks either side, a lighting tower on every corner with a head turning
    on top, the crowd on the floor in front of the booth all going up on the
    kick, and the lift hut by the south parapet. The whole roof goes white
    on the strobe."""
    x0, z0, x1, z1 = party_roof(lm)
    h = LANDMARK_H
    lamp = party_light(now)
    t = now * PARTY_BPM / 60.0
    up = t % 1.0 < 0.5
    lit = lamp if lamp is not None else CURB
    cx = (x0 + x1) * 0.5
    blit_sprite(ch, co, v, walls, PARTY_BOOTH, cx, z0 + 2.6, h, h + 2.0, 6.0,
                lamp if lamp is not None else CONCRETE)
    blit_sprite(ch, co, v, walls, RAVER_UP if up else RAVER_DOWN, cx, z0 + 2.2,
                h + 1.2, h + 1.2 + SMOKER_H, SMOKER_W, lit)
    for side in (-1.0, 1.0):
        blit_sprite(ch, co, v, walls, PARTY_STACK, cx + side * 4.5, z0 + 2.4, h,
                    h + 3.0, 1.6, lamp if lamp is not None else CONCRETE)
    for px, pz in ((x0 + 1.0, z0 + 1.0), (x1 - 1.0, z0 + 1.0),
                   (x0 + 1.0, z1 - 1.0), (x1 - 1.0, z1 - 1.0)):
        y = h + 0.3
        while y < h + 5.0:
            put_point(ch, co, v, walls, px, y, pz, "|", CONCRETE)
            y += 0.6
        put_point(ch, co, v, walls, px, h + 5.3, pz, "V" if up else "v",
                  NEON[(int(t) + int(px)) % len(NEON)][0])
    for px, pz, m in party_dancers(lm):
        offset = (m >> 16) & 3
        arms = (t + offset * 0.08) % 1.0 < 0.5
        blit_sprite(ch, co, v, walls, RAVER_UP if arms else RAVER_DOWN, px, pz,
                    h + 0.05, h + SMOKER_H, SMOKER_W,
                    lamp if lamp is not None else
                    NEON[(m >> 20) % len(NEON)][1])
    hx, hz = lift_hut(lm)
    blit_sprite(ch, co, v, walls, LIFT_HUT, hx, hz, h, h + 2.8, 2.6, CONCRETE)


def draw_lobby(ch, co, v, walls, t, now):
    """The lit lobby door and SKY DECK over it, in screen space so it can be
    read - the casino marquee's reasoning, at a smaller size."""
    i, j, f = t["i"], t["j"], t["door"]
    w = face_point(i, j, f, CELL * 0.5, 0.15, 3.6)
    pr = v.project(w[0], w[1], w[2])
    if pr is None:
        return
    sx, sy, dist = int(round(pr[0])), int(round(pr[1])), pr[2]
    if dist > 60.0:
        return
    # In the crown's colour: the crown is seventy units up, over the top of
    # the screen from anywhere in the street, so the door carries it down.
    if t.get("kind") == "party":
        # The landmark's door: its name, and what is going on up there.
        for row, (word, attr) in enumerate(((t["landmark"]["name"], GOLD),
                                            ("ROOF PARTY TONIGHT",
                                             party_light(now) or NEON[1][1]))):
            for k, c in enumerate(word):
                put_cell(ch, co, v, walls, sx - len(word) // 2 + k, sy - 1 + row,
                         dist, c, attr)
        door = face_point(i, j, f, CELL * 0.5, 0.2, 0.0)
        blit_sprite(ch, co, v, walls, ["[|]", "[|]", "[|]"], door[0], door[2],
                    0.0, 2.4, 1.4, BULB)
        return
    word = "SKY DECK"
    for k, c in enumerate(word):
        put_cell(ch, co, v, walls, sx - len(word) // 2 + k, sy, dist, c,
                 v.crown if v.crown is not None else GOLD_DIM)
    door = face_point(i, j, f, CELL * 0.5, 0.2, 0.0)
    blit_sprite(ch, co, v, walls, ["[|]", "[|]", "[|]"], door[0], door[2],
                0.0, 2.4, 1.4, BULB)


LIFT_CAR = [
    ".-------------------.",
    "|                   |",
    "|                   |",
    "|                   |",
    "|                   |",
    "|                   |",
    "|                   |",
    "|                   |",
    "|                   |",
    "'-------------------'",
]


def climbable(i, j, f):
    """Does the fire escape on this face go all the way to the roof - the
    hash first, then that the face really gives onto a dark alley and the
    building really has an escape on it."""
    if _mix(i, j * 4 + f, 1931) % CLIMB_ODDS:
        return False
    nx, nz = FACES[f]
    if is_open(i, j) or not is_open(i + nx, j + nz):
        return False
    if road_at(i + nx, j + nz) or face_kind(i + nx, j + nz) is not None:
        return False
    if woods_at(i, j) or not dry_at((i + nx + 0.5) * CELL, (j + nz + 0.5) * CELL):
        return False
    b = lot(i, j)
    if not (b["faces"][f]["escape"] and b["height"] >= 3 * FLOOR_H
            and not b["tree"] and b["club"] is None
            and b["casino"] is None and b["tower"] is None
            and b["arcade"] is None and b["exchange"] is None
            and b["temple"] is None):
        return False
    # And only off a roof that is the high point of its corner: climbed from
    # an alley, the first ones put you face to face with the wall of a taller
    # building across the lane. Asking the neighbours' lots from here is safe -
    # lot() never asks climbable().
    h = b["height"] + 1.0
    return all(is_open(i + a, j + c) or lot(i + a, j + c)["height"] <= h
               for a in range(-2, 3) for c in range(-2, 3) if a or c)


def escape_roof(i, j, f):
    """The roof a climbable escape takes you to, in the shape a sky deck's
    roof has, so the same roof view serves both."""
    return {"i": i, "j": j, "door": f, "u": CELL * 0.5,
            "height": lot(i, j)["height"], "kind": "escape"}


def escape_at(x, z, yaw):
    """The climbable escape you are at the foot of and facing, or None.
    Facing matters: an alley is one cell wide, so anything you could reach
    by standing near it you would also walk past on the way down the lane -
    you climb by walking into the wall at the ladder, not by going by it."""
    ci = int(x / CELL + BIG) - BIG
    cj = int(z / CELL + BIG) - BIG
    dx, dz = math.sin(yaw), math.cos(yaw)
    for i in range(ci - 1, ci + 2):
        for j in range(cj - 1, cj + 2):
            for f in range(4):
                if not climbable(i, j, f):
                    continue
                px, _, pz = face_point(i, j, f, CELL * 0.5, 1.2, 0.0)
                if (px - x) ** 2 + (pz - z) ** 2 > CLIMB_REACH ** 2:
                    continue
                nx, nz = FACES[f]
                if dx * -nx + dz * -nz > 0.7:
                    return escape_roof(i, j, f)
    return None


def escape_near(x, z):
    """Is there a climbable escape within a few steps - for the HUD."""
    ci = int(x / CELL + BIG) - BIG
    cj = int(z / CELL + BIG) - BIG
    for i in range(ci - 1, ci + 2):
        for j in range(cj - 1, cj + 2):
            for f in range(4):
                if not climbable(i, j, f):
                    continue
                px, _, pz = face_point(i, j, f, CELL * 0.5, 1.2, 0.0)
                if (px - x) ** 2 + (pz - z) ** 2 < 4.0 ** 2:
                    return True
    return False


def climb_times(floors):
    """(off the ground, at the top, over the parapet) for a climb."""
    up = 0.4 + floors * CLIMB_FLOOR
    return 0.4, up, up + 0.7


def render_climb(up, floors, t, width, height, now):
    """On the fire escape, face to the bricks.

    The wall scrolls past - courses of brick, a window every storey with a
    light on behind one now and then - and the iron stairs zigzag across it
    in front of you, a landing at every floor. The count goes up in the
    corner; at the top you swing over the parapet and the sky opens out. Going
    down it all runs the other way."""
    ch = [[" "] * width for _ in range(height)]
    co = [[0] * width for _ in range(height)]
    start, top, over = climb_times(floors)
    p = min(1.0, max(0.0, (t - start) / max(1e-6, top - start)))
    climbed = p * floors if up else (1.0 - p) * floors
    floor = 1 + min(floors - 1, int(climbed))
    if width < 30 or height < 12:
        _text(ch, co, height // 2, 1, "on the fire escape  %d/%d" % (floor, floors),
              CURB)
        return ch, co
    rows_per_floor = 7
    scroll = int(climbed * rows_per_floor)
    cx = width // 2
    for y in range(height):
        wy = scroll + (height - 1 - y)                 # world row, up the wall
        storey, r = divmod(wy, rows_per_floor)
        for x in range(width):
            # Brick courses, staggered every other row.
            if r == 0:
                ch[y][x], co[y][x] = "=", BARK         # the landing, edge on
            elif (x + (wy % 2) * 2) % 5 == 0:
                ch[y][x], co[y][x] = "|", CONCRETE
            elif wy % 2 == 0:
                ch[y][x], co[y][x] = "_", CONCRETE
        # A window either side of the stairs, lit now and then.
        if 2 <= r <= 5:
            for wx in (cx - 18, cx + 12):
                lit = _mix(storey, wx, 1933) % 4 == 0
                for x in range(wx, wx + 7):
                    if 0 <= x < width:
                        ch[y][x] = "#" if lit else (" " if r < 5 else "_")
                        co[y][x] = tone_colour("warm", 0.4) if lit else CURB
        # The stairs: a flight going one way between landings, back the next.
        flight = storey % 2
        sx = cx - 6 + (r if flight == 0 else rows_per_floor - r)
        for x in (sx, sx + 1):
            if 0 <= x < width and r != 0:
                ch[y][x], co[y][x] = "/" if flight == 0 else "\\", BARK
        for x in (cx - 8, cx + 4):
            if 0 <= x < width:
                ch[y][x], co[y][x] = "|", BARK         # the rails
    # You: hands on the rail, mid-screen.
    for k, line in enumerate((" o ", "/|\\", "/ \\")):
        _text(ch, co, height // 2 - 1 + k, cx - 2, line, STAR)
    if t >= top:
        # Over the top: the sky opens out above the parapet.
        lift_ = int((t - top) / max(1e-6, over - top) * (height // 2))
        for y in range(min(height, lift_)):
            for x in range(width):
                ch[y][x] = "." if _mix(x, y, 1935) % 23 == 0 else " "
                co[y][x] = STAR
        if lift_ < height:
            _text(ch, co, lift_, 0, "=" * width, ROOF)
    panel = " floor %d / %d " % (floor, floors)
    for k in range(len(panel)):
        ch[0][1 + k], co[0][1 + k] = panel[k], GOLD_DIM
    say = (" climbing " if up else " climbing down ") if t < top else (
        " the roof " if up else " the alley ")
    for k, c in enumerate(say):
        x = cx - len(say) // 2 + k
        if 0 <= x < width:
            ch[height - 1][x], co[height - 1][x] = c, GOLD_DIM
    return ch, co


STAIR_STEPS = 96        # up the lighthouse, round and round


def render_stairs(up, floors, t, width, height, now):
    """Up the lighthouse's stair, round and round the post in the middle.

    The steps come down past you as you climb - each a slab from the post
    out to the wall, turning a little from one to the next, so they wind -
    with the wall's courses behind them and now and then a slit window going
    by, black sea and, when the beam is round this side, white. A count of
    the steps in the corner; at the top the lantern's light floods in."""
    ch = [[" "] * width for _ in range(height)]
    co = [[0] * width for _ in range(height)]
    start, top, over = climb_times(floors)
    p = min(1.0, max(0.0, (t - start) / max(1e-6, top - start)))
    climbed = p if up else 1.0 - p
    step = 1 + min(STAIR_STEPS - 1, int(climbed * STAIR_STEPS))
    if width < 30 or height < 12:
        _text(ch, co, height // 2, 1, "up the lighthouse  %d/%d" % (step, STAIR_STEPS),
              MOON_DIM)
        return ch, co
    cx = width // 2
    half = min(width // 2 - 2, 26)
    scroll = climbed * STAIR_STEPS * 2.0
    for y in range(height):
        wy = int(scroll) + (height - 1 - y)            # rows up the tower
        for x in (cx - half, cx + half):               # the curve of the wall
            ch[y][x], co[y][x] = ("(" if x < cx else ")"), MOON_DIM
        if wy % 2 == 0:
            for x in range(cx - half + 1, cx + half):
                if (x + wy) % 6 == 0:
                    ch[y][x], co[y][x] = ".", CONCRETE
        # A step every other row: from the post out to one side, the side
        # swinging round as you go up.
        if wy % 2 == 0:
            ang = (wy // 2) * 0.55
            reach = int(math.cos(ang) * (half - 3))
            a, b = sorted((cx, cx + reach))
            for x in range(a, b + 1):
                ch[y][x], co[y][x] = "_", BARK
        # A slit window every twenty rows, the beam crossing it.
        if wy % 20 in (8, 9, 10, 11):
            half_turn = BEAM_TURN / 2.0
            lit = int(now / half_turn) % 2 == 0 and now % half_turn < 0.6
            for x in range(cx + half - 6, cx + half - 2):
                ch[y][x], co[y][x] = ("#", FLASH) if lit else ("~", RAIN_FAR)
        ch[y][cx], co[y][cx] = "|", MOON_DIM          # the post
    for k, line in enumerate((" o ", "/|\\", "/ \\")):
        _text(ch, co, height // 2 - 1 + k, cx - 6, line, STAR)
    if t >= top:
        flood = int((t - top) / max(1e-6, over - top) * height)
        for y in range(min(height, flood)):
            for x in range(width):
                if _mix(x, y, 1937) % 5 == 0:
                    ch[y][x], co[y][x] = "*", BULB
    panel = " step %d / %d " % (step, STAIR_STEPS)
    for k in range(len(panel)):
        ch[0][1 + k], co[0][1 + k] = panel[k], GOLD_DIM
    say = (" climbing " if up else " climbing down ") if t < top else (
        " the gallery " if up else " the rock ")
    for k, c in enumerate(say):
        x = cx - len(say) // 2 + k
        if 0 <= x < width:
            ch[height - 1][x], co[height - 1][x] = c, GOLD_DIM
    return ch, co


def lift_times(floors):
    """(doors closed, arrived, doors open) as seconds from stepping in."""
    travel = 0.6 + floors * LIFT_FLOOR
    return LIFT_DOORS, LIFT_DOORS + travel, LIFT_DOORS * 2 + travel


def render_lift(up, floors, t, width, height, now):
    """Inside the lift, facing the doors.

    The doors slide shut from the sides, the indicator over them counts the
    floors with the arrow lit, the shaft goes by through the gap at the
    edge of the doors - floor slabs passing the other way to the ride - and
    the gauge on the wall shows the car climbing its shaft. Then a ding, and
    the doors open on wherever you were going."""
    ch = [[" "] * width for _ in range(height)]
    co = [[0] * width for _ in range(height)]
    shut, there, opened = lift_times(floors)
    if t < shut:
        closed = t / shut                         # 0 open .. 1 shut
    elif t < there:
        closed = 1.0
    else:
        closed = max(0.0, 1.0 - (t - there) / LIFT_DOORS)
    ride = min(1.0, max(0.0, (t - shut) / max(1e-6, there - shut)))
    ease = 0.5 - 0.5 * math.cos(ride * math.pi)
    floor = 1 + int(round(ease * (floors - 1))) if up else \
        floors - int(round(ease * (floors - 1)))
    cx = width // 2

    if width < 30 or height < 14:
        _text(ch, co, height // 2, 1, "in the lift  %s %d" % ("^" if up else "v",
                                                              floor), GOLD)
        return ch, co

    # The indicator over the doors.
    arrow = ("^" if up else "v") if 0.0 < ride < 1.0 and int(now * 4) % 2 == 0 \
        else " "
    panel = "[ %s %3d ]" % (arrow, floor)
    _text(ch, co, 1, cx - len(panel) // 2, panel, ROU_RED)
    if t >= there and t < there + 1.2:
        _text(ch, co, 1, cx + len(panel) // 2 + 2, "*ding*", GOLD)

    # The doors: two brushed-steel panels meeting in the middle.
    top, bot = 3, height - 3
    half = int((width // 2 - 4) * closed)
    left, right = 3, width - 4
    for y in range(top, bot + 1):
        _text(ch, co, y, left - 1, "#", CONCRETE)
        _text(ch, co, y, right + 1, "#", CONCRETE)
    _text(ch, co, top - 1, left - 1, "#" * (right - left + 3), CONCRETE)
    _text(ch, co, bot + 1, left - 1, "#" * (right - left + 3), CONCRETE)
    # What is behind the doors: the shaft while moving, the lobby or the
    # roof either end of the ride.
    for y in range(top, bot + 1):
        for x in range(left, right + 1):
            if left + half <= x <= right - half:
                if 0.0 < ride < 1.0:
                    # Floor slabs going past the gap, the other way.
                    slab = (y + int(ease * floors * 6) * (1 if up else -1)) % 6
                    ch[y][x] = "=" if slab == 0 else ("|" if x in (left + half,
                                                                    right - half)
                                                       else " ")
                    co[y][x] = CONCRETE
                elif t >= there and up:
                    ch[y][x] = "." if _mix(x, y, 1911) % 9 == 0 else " "
                    co[y][x] = STAR                  # sky, through the doors
                else:
                    ch[y][x] = "_" if y == bot else " "
                    co[y][x] = GOLD_DIM              # the lobby floor
            else:
                ch[y][x] = "|" if x in (cx - 1, cx) else ("." if (x + y) % 7 == 0
                                                         else " ")
                co[y][x] = CURB
    # The gauge: the car in its shaft, on the wall to the left of the doors.
    if left > 0 and height > 16:
        gy0, gy1 = top, bot
        car = gy1 - int(round(ease * (gy1 - gy0))) if up else \
            gy0 + int(round(ease * (gy1 - gy0)))
        for y in range(gy0, gy1 + 1):
            _text(ch, co, y, 0, "|" if y != car else "#", GOLD if y == car else BARK)
    say = ("going up" if up else "going down") if ride < 1.0 else (
        "the roof" if up else "the lobby")
    _text(ch, co, height - 1, cx - len(say) // 2, say, GOLD_DIM)
    return ch, co


def draw_roof_ledge(ch, co, v, walls, t, now, wet):
    """Your own roof: a parapet round the edge at waist height, a water tower
    on one corner and the mast with its red light on another. Drawn in world
    space, so it turns with you and frames whichever way you look."""
    if t.get("kind") in ("lighthouse", "party"):
        return                          # the gallery's rail, or the party's parapet
    h = t["height"]
    i, j = t["i"], t["j"]
    x0, z0 = i * CELL, j * CELL
    x1, z1 = x0 + CELL, z0 + CELL
    # The parapet is solved per screen column rather than drawn as points:
    # at arm's length a point every quarter-unit lands five columns from the
    # next, and the rows between came out as stripes. Each column's ray leaves
    # the roof square somewhere; the coping is at that distance, and below it
    # the wall hides whatever the city put there.
    cap = h + 1.0
    for sx in range(v.width):
        rdx, rdz = v.ray(sx)
        out = 1e9                        # how far along the ray it leaves the roof
        for d, lo, hi, p in ((rdx, x0, x1, v.x), (rdz, z0, z1, v.z)):
            if d > 1e-9:
                out = min(out, (hi - p) / d)
            elif d < -1e-9:
                out = min(out, (lo - p) / d)
        if out <= 0.05 or out > 50.0:
            continue
        top = int(round(v.horizon - (cap - v.eye) * v.fy / out))
        for y in range(max(0, top), v.height):
            if y == top:
                ch[y][sx], co[y][sx] = "=", ROOF
            elif (y - top) % 3 == 0:
                ch[y][sx], co[y][sx] = "-", CONCRETE        # the courses
            elif (y - top) % 6 in (1, 2) and (sx + (y - top) // 3 * 2) % 5 == 0:
                ch[y][sx], co[y][sx] = "|", CONCRETE        # and the joints
            else:
                ch[y][sx], co[y][sx] = " ", 0
    # The water tower, on legs, in the corner the mast is not in.
    wx, wz = x0 + 1.0, z0 + 1.0
    for y in (h + 0.3, h + 1.0):
        for dx, dz in ((-0.4, -0.4), (0.4, -0.4), (-0.4, 0.4), (0.4, 0.4)):
            put_point(ch, co, v, walls, wx + dx, y, wz + dz, "|", BARK)
    for y in (h + 1.6, h + 2.2, h + 2.8):
        for a in range(8):
            ang = a * math.tau / 8.0
            put_point(ch, co, v, walls, wx + 0.6 * math.cos(ang), y,
                      wz + 0.6 * math.sin(ang), "#", BARK)
    put_point(ch, co, v, walls, wx, h + 3.3, wz, "^", BARK)
    mx, mz = x1 - 0.8, z1 - 0.8
    if t.get("kind") == "escape":
        # An alley roof: a TV aerial and a chimney stack, and the top of the
        # fire escape you came up, over the parapet on its side.
        for y in range(4):
            put_point(ch, co, v, walls, mx, h + 0.5 + y * 0.8, mz, "|", CONCRETE)
        for dx in (-0.6, -0.3, 0.3, 0.6):
            put_point(ch, co, v, walls, mx + dx, h + 3.2, mz, "-", CONCRETE)
        for y in (h + 0.4, h + 1.0, h + 1.6):
            put_point(ch, co, v, walls, x1 - 0.8, y, z0 + 0.8, "#", BARK)
        ex, _, ez = face_point(i, j, t["door"], CELL * 0.5, 0.15, 0.0)
        for y in (h + 0.6, h + 1.2, h + 1.8):
            for k in (-0.4, 0.4):
                ax, az = -FACES[t["door"]][1], FACES[t["door"]][0]
                put_point(ch, co, v, walls, ex + ax * k, y, ez + az * k, "|", BARK)
        return
    for y in range(6):
        put_point(ch, co, v, walls, mx, h + 0.5 + y * 0.9, mz, "|", CONCRETE)
    on = int(now * 1.3 + i) % 2 == 0
    put_lit(ch, co, v, walls, mx, h + 5.8, mz, "*" if on else ".",
            ROU_RED if on else CONCRETE, max(wet, 0.3), now)


def roof_view(t, yaw, width, height):
    """The camera on a sky-deck roof: up at the parapet on whichever side you
    are facing, so you look over it and down into the street - in the middle
    of the roof the parapet hides everything nearer than the next district.
    Turning walks you round the inside of it."""
    x = (t["i"] + 0.5) * CELL + math.sin(yaw) * ROOF_STEP
    z = (t["j"] + 0.5) * CELL + math.cos(yaw) * ROOF_STEP
    return View(x, z, yaw, width, height, eye=t["height"] + 1.7,
                reach=ROOF_REACH)


CAR = [
    " .----. ",
    "/_|__|_\\",
    "'o----o'",
]
PAY_BOOTH = [
    " ____ ",
    "|[##]|",
    "|    |",
    "|____|",
]


def car_parks_near(v, reach):
    """Is any car-park block within reach - a handful of hashes, and the
    gate in front of everything else here: most of the city has none, and
    scanning every bay in sight for nothing was most of two milliseconds."""
    b0, b1 = int((v.x - reach) // (XP * CELL)), int((v.x + reach) // (XP * CELL))
    c0, c1 = int((v.z - reach) // (ZP * CELL)), int((v.z + reach) // (ZP * CELL))
    return any(car_park_block(bi, bj) for bi in range(b0, b1 + 1)
               for bj in range(c0, c1 + 1))


def near_park_lamps(v, reach):
    """The sodium lamps down the aisles of any car park in reach."""
    if not car_parks_near(v, reach):
        return
    n = int(reach / LAMP_GAP) + 1
    k0 = int(math.floor(v.z / BAY_ROW))
    g0 = int(math.floor(v.x / LAMP_GAP))
    for k in range(k0 - int(reach / BAY_ROW) - 1, k0 + int(reach / BAY_ROW) + 2):
        z = k * BAY_ROW + BAY_ROW * 0.5
        for g in range(g0 - n, g0 + n + 1):
            x = g * LAMP_GAP + LAMP_GAP * 0.5
            if (x - v.x) ** 2 + (z - v.z) ** 2 > reach * reach:
                continue
            if car_park_at(int(x / CELL + BIG) - BIG, int(z / CELL + BIG) - BIG):
                yield x, z


def near_parked_cars(v, reach):
    """(x, z, seed) for every occupied bay in front of you, farthest first.
    Two cars in three bays, by a hash of the bay: same cars every time."""
    out = []
    if not car_parks_near(v, reach):
        return out
    n = int(reach / PARK_BAY) + 1
    s0 = int(math.floor(v.x / PARK_BAY))
    k0 = int(math.floor(v.z / BAY_ROW))
    for k in range(k0 - int(reach / BAY_ROW) - 1, k0 + int(reach / BAY_ROW) + 2):
        for side, along in ((0, 2.5), (1, BAY_ROW - 2.5)):
            z = k * BAY_ROW + along
            for s in range(s0 - n, s0 + n + 1):
                m = _mix(s, k * 2 + side, 1953)
                if m % 3 == 0:
                    continue
                x = (s + 0.5) * PARK_BAY
                rx, rz = x - v.x, z - v.z
                if (rx * v.dx + rz * v.dz < SPRITE_NEAR
                        or rx * rx + rz * rz > reach * reach):
                    continue
                # Only where the whole bay is car park, so no car sits half in
                # the road or the next building.
                ok = all(car_park_at(int(px / CELL + BIG) - BIG,
                                     int(pz / CELL + BIG) - BIG)
                         for px, pz in ((x - 1.0, z - 2.0), (x + 1.0, z + 2.0)))
                if ok:
                    out.append((rx * rx + rz * rz, x, z, m))
    out.sort(reverse=True)
    return out


def draw_car_park(ch, co, v, walls, now, wet):
    """Parked cars in their bays, tall sodium lamps throwing orange over the
    tarmac, and at the corner nearest you a blue P on a pole and the pay
    booth with its light on. Now and then a car's alarm light winks."""
    if not car_parks_near(v, 75.0):
        return
    for lx, lz in near_park_lamps(v, 75.0):
        for h in range(7):
            put_point(ch, co, v, walls, lx, 0.5 + h * 0.85, lz, "|", CONCRETE)
        put_point(ch, co, v, walls, lx - 0.5, 6.4, lz, "_", CONCRETE)
        put_lit(ch, co, v, walls, lx - 0.9, 6.1, lz, "o", EMBER_HOT,
                max(wet, 0.4), now)
    for _, x, z, m in near_parked_cars(v, 60.0):
        paint = tone_colour(("mid", "far", "cold", "warm", "rust")[m >> 3 & 3],
                            (m >> 6 & 15) / 15.0)
        blit_sprite(ch, co, v, walls, CAR, x, z, 0.0, 1.35, 1.9, paint)
        if (m >> 11) % 17 == 0 and int(now * 1.5 + (m & 7)) % 2 == 0:
            put_lit(ch, co, v, walls, x + 0.4, 1.15, z, ".", ROU_RED, wet, now)
    # The sign and the booth, at the corners of each car park in reach.
    seen = set()
    n = int(70.0 / CELL) + 1
    ci = int(v.x / CELL + BIG) - BIG
    cj = int(v.z / CELL + BIG) - BIG
    for i in range(ci - n, ci + n + 1):
        for j in range(cj - n, cj + n + 1):
            if not car_park_at(i, j):
                continue
            west, east = not car_park_at(i - 1, j), not car_park_at(i + 1, j)
            north, south = not car_park_at(i, j - 1), not car_park_at(i, j + 1)
            if not ((west or east) and (north or south)) or (i, j) in seen:
                continue                       # only the corners, one sign each
            seen.add((i, j))
            x = i * CELL + (1.2 if west else CELL - 1.2)
            z = j * CELL + (1.2 if north else CELL - 1.2)
            if (x - v.x) * v.dx + (z - v.z) * v.dz < NEAR_Z:
                continue
            for h in range(6):
                put_point(ch, co, v, walls, x, 0.5 + h * 0.8, z, "|", CONCRETE)
            pr = v.project(x, 5.3, z)
            if pr is not None and pr[2] < 70.0:
                sx, sy = int(round(pr[0])), int(round(pr[1]))
                for k, c in enumerate("[P]"):
                    put_cell(ch, co, v, walls, sx - 1 + k, sy, pr[2], c,
                             NEON[2][0])
            blit_sprite(ch, co, v, walls, PAY_BOOTH, x + 2.6, z + 0.8, 0.0, 2.2,
                        1.5, CURB)
            put_lit(ch, co, v, walls, x + 2.6, 1.5, z + 0.8, "#", BULB,
                    max(wet, 0.3), now)


def draw_tunnel_ceiling(ch, co, v, walls, now, tunnels):
    """The underside of the deck, solved per screen row the way the ground is.

    Every row above the horizon is one distance to a plane at TUNNEL_H; where
    that point is over a tunnel and nearer than the wall in its column, the
    ceiling is what you see there - so it covers the sky, the stars and
    whatever is past the far mouth, and the mouth itself is the gap where the
    ceiling stops. Joints across it every two units, and lights down the
    middle of a long one, drawn after as lights so they hold at any range.

    It goes in v.ceiling as well, cell by cell with its distance, and
    put_cell() will not draw anything further away into those cells - so
    the rain past the mouth and the lights of the town beyond stay behind it,
    and someone walking through in front of you stays in front of it. It is
    drawn early, right after the ground, for the second half of that."""
    if v.eye >= TUNNEL_H or not tunnels:
        return
    width = v.width
    rdx0, rdz0 = v.dx - v.plx, v.dz - v.plz
    rdx1, rdz1 = v.dx + v.plx, v.dz + v.plz
    for y in range(0, v.horizon):
        d = (TUNNEL_H - v.eye) * v.fy / (v.horizon - y)
        if d > 120.0:
            continue
        wx, wz = v.x + rdx0 * d, v.z + rdz0 * d
        stepx = (rdx1 - rdx0) * d / (width - 1)
        stepz = (rdz1 - rdz0) * d / (width - 1)
        for sx in range(width):
            x, z = wx, wz
            wx += stepx
            wz += stepz
            wd = walls[0][sx]
            if wd is not None and wd < d:
                continue
            run = tunnel_run(int(x / CELL + BIG) - BIG, int(z / CELL + BIG) - BIG)
            if run is None:
                continue
            glyph, attr = " ", 0
            if (z % 2.0) < 0.12:
                glyph, attr = "=", CONCRETE
            ch[y][sx], co[y][sx] = glyph, attr
            v.ceiling[y * 4096 + sx] = d     # what is further is behind it


def tunnel_lining(ch, co, v, sx, dist, r_lo, r_hi, j_or_i, seed):
    """A side wall inside a tunnel, from the road to the deck: dark, tiled,
    grimy, a tag now and then. Laid over the facade the column drew - above
    the deck the building carries on as itself."""
    scale = v.fy / dist
    top = int(round(v.horizon - (TUNNEL_H - v.eye) * scale))
    foot = int(round(v.horizon + v.eye * scale))
    for y in range(max(r_lo, top), min(r_hi, foot) + 1):
        m = _mix(sx, y, 2207)
        if y == top:
            g, a = "_", CONCRETE
        elif m % 9 == 0:
            g, a = "|", CONCRETE
        elif m % 13 == 0:
            g, a = ".", BARK
        else:
            g, a = " ", 0
        ch[y][sx], co[y][sx] = g, a
    if (seed % 5 == 0 and r_lo <= top + 3 <= r_hi and dist < 30.0):
        tag = "%%&@"[seed % 4]
        ch[top + 3][sx], co[top + 3][sx] = tag, NEON[seed % len(NEON)][1]


def draw_headwall(ch, co, v, walls, x0, x1, z, outward):
    """The face of the deck over a tunnel mouth: brick from the top of the
    opening to the parapet, a railing along the top. Only from its own side:
    from inside the tunnel, or from in front of the other mouth, the deck is
    between you and it."""
    if (v.z - z) * outward <= 0.0:
        return
    x = x0
    while x <= x1:
        for y in (TUNNEL_H + 0.3, TUNNEL_H + 0.8, TUNNEL_H + 1.3, TUNNEL_H + 1.8):
            put_point(ch, co, v, walls, x, y, z, "#", CONCRETE)
        put_point(ch, co, v, walls, x, TUNNEL_H, z, "=", CURB)
        put_point(ch, co, v, walls, x, TUNNEL_H + 2.2, z, "=", ROOF)
        put_point(ch, co, v, walls, x, TUNNEL_H + 3.0, z, "-", CURB)
        x += 0.3


CAN_FIRE = [
    "|####|",
    "|####|",
    "|____|",
]
SITTER = [
    " ,-. ",
    "(   )",
    "/###\\",
    "~~~~~",
]
WARMER = [
    " ,-. ",
    " ( ) ",
    "-/#\\-",
    " |#| ",
    " / \\ ",
]
CART = [
    " ______ ",
    "|##=#=#|",
    " \\____/ ",
    "  o  o  ",
]


def camp_spot(x0, x1, z0, z1):
    """Where the fire is under a short tunnel: against one side wall, about
    halfway along."""
    return x0 + 1.6, (z0 + z1) * 0.5


def draw_camp(ch, co, v, walls, x0, x1, z0, z1, now, wet):
    """A can with a fire in it, the people round it, a blanket, a cart. The
    flames are the only light under here and everything else is lit by them."""
    fx, fz = camp_spot(x0, x1, z0, z1)
    people = [(fx + 0.4, fz - 1.4, SITTER, 1.0), (fx + 1.8, fz + 0.2, WARMER, 1.9),
              (fx + 0.3, fz + 1.5, SITTER, 1.0)]
    things = [(fx - 0.2, fz + 3.6, CART, 1.1, 1.6)]
    for px, pz, art, h in sorted(people, key=lambda p: -((p[0] - v.x) ** 2
                                                         + (p[1] - v.z) ** 2)):
        blit_sprite(ch, co, v, walls, art, px, pz, 0.0, h, h * 0.62, EMBER)
    for px, pz, art, h, w in things:
        blit_sprite(ch, co, v, walls, art, px, pz, 0.0, h, w, CURB)
    blit_sprite(ch, co, v, walls, CAN_FIRE, fx, fz, 0.0, 1.0, 0.75, BARK)
    for k in range(6):
        a = now * 7.0 + k * 1.7
        y = 1.05 + 0.18 * k + 0.08 * math.sin(a)
        glyph = "^" if k < 2 else ("(" if math.sin(a) > 0 else ")")
        put_lit(ch, co, v, walls, fx + 0.15 * math.sin(a * 1.3), y, fz,
                glyph, EMBER_HOT if k < 3 else GOLD, max(wet, 0.5), now)
    for k in range(4):                      # sparks going up into the dark
        t = (now * 0.8 + k * 0.27) % 1.0
        put_point(ch, co, v, walls, fx + 0.3 * math.sin(k * 2.0 + now),
                  1.6 + t * 2.8, fz, ".", EMBER_HOT)


def fire_near(x, z):
    """For the HUD: under a short tunnel, near its fire."""
    i = int(x / CELL + BIG) - BIG
    j = int(z / CELL + BIG) - BIG
    for di in range(-3, 4):
        for dj in range(-3, 4):
            run = tunnel_run(i + di, j + dj)
            if run is not None and run[0] == "short":
                return True
    return False


def draw_props(ch, co, v, walls, now, wet):
    """Everything hanging off a facade or standing in front of one, drawn
    farthest first so the near ones win."""
    props = []
    for i, j, b in near_lots(v, 62.0):
        if b["tree"]:
            continue                    # nothing is hung on a tree
        for f in range(4):
            nx, nz = FACES[f]
            if not is_open(i + nx, j + nz):
                continue
            if tunnel_at(i + nx, j + nz):
                continue                # nothing hangs inside a tunnel
            if b["diner"] is not None and f == b["diner"]["door"]:
                w = face_point(i, j, f, CELL * 0.5, 0.4, 3.9)
                props.append((_d2(v, w), "diner", b["diner"], w, (nx, nz)))
            if b["cinema"] is not None and f == b["cinema"]["door"]:
                w = face_point(i, j, f, CELL * 0.5, 0.4, 3.9)
                props.append((_d2(v, w), "cinema", b["cinema"], w, (nx, nz)))
            if b["tower"] is not None and f == b["tower"]["door"]:
                w = face_point(i, j, f, CELL * 0.5, 0.3, 0.0)
                props.append((_d2(v, w), "lobby", b["tower"], w, (nx, nz)))
            if b["exchange"] is not None:
                if f == b["exchange"]["door"]:
                    w = face_point(i, j, f, CELL * 0.5, 0.5, 2.0 * FLOOR_H + 1.2)
                    props.append((_d2(v, w), "exchange", b["exchange"], w, (nx, nz)))
                continue
            if b["temple"] is not None:
                if f == b["temple"]["door"]:
                    w = face_point(i, j, f, CELL * 0.5, 0.4, ROSE_Y)
                    props.append((_d2(v, w), "temple", b["temple"], w, (nx, nz)))
                continue
            if b["arcade"] is not None:
                if f == b["arcade"]["door"]:
                    w = face_point(i, j, f, CELL * 0.5, 0.5, FLOOR_H + 0.6)
                    props.append((_d2(v, w), "arcade", b["arcade"], w, (nx, nz)))
                continue
            if b["casino"] is not None:
                # It has to be obvious from down the street what this is.
                if f == b["casino"]["door"]:
                    cas = b["casino"]
                    w = face_point(i, j, f, CELL * 0.5, 0.6, 4.6)
                    props.append((_d2(v, w), "marquee", cas, w, (nx, nz)))
                    # The blade up the corner, out over the pavement.
                    w = face_point(i, j, f, BLADE_U, BLADE_OUT, FLOOR_H + 1.0)
                    props.append((_d2(v, w), "blade", (cas, i, j, f), w, (nx, nz)))
                    # The red carpet to the kerb, and the doorman beside it.
                    w = face_point(i, j, f, cas["u"], 0.9, 0.0)
                    props.append((_d2(v, w), "carpet", (cas, i, j, f), w, (nx, nz)))
                    side = 1.3 if cas["u"] < CELL * 0.5 else -1.3
                    w = face_point(i, j, f, cas["u"] + side, 0.45, 0.0)
                    props.append((_d2(v, w), "doorman", cas, w, (nx, nz)))
                continue
            if b["club"] is not None:
                # Nobody is getting in for a while. Some of them are dancing
                # anyway and the rest are smoking about it.
                if f == b["club"]["door"]:
                    for kind_, s_, w in club_line(i, j, f, b["club"], now):
                        props.append((_d2(v, w), kind_, s_, w, (nx, nz)))
                continue
            fc = b["faces"][f]
            if fc["lanterns"] is not None:
                w = face_point(i, j, f, CELL * 0.5, 0.6, 0.0)
                props.append((_d2(v, w), "lanterns", (fc["lanterns"], i, j, f),
                              w, (nx, nz)))
            lit = face_kind(i + nx, j + nz)
            if lit == "yokocho" and fc["pub"]:
                w = face_point(i, j, f, CELL * 0.5, 0.5, 3.4)
                ramen = ramen_at(i, j, f)
                props.append((_d2(v, w), "overdoor",
                              ("ラーメン" if ramen else fc["over"],
                               fc["lanterns"]), w, (nx, nz)))
                if ramen:
                    w = face_point(i, j, f, CELL * 0.5, 0.6, 0.0)
                    props.append((_d2(v, w), "noren", (i, j, f), w, (nx, nz)))
                    w = face_point(i, j, f, CELL * 0.5, 0.3, RAMEN_SIGN_Y)
                    props.append((_d2(v, w), "ramenfront", (i, j, f), w, (nx, nz)))
            if lit:
                if fc["hung"] is not None:
                    s = fc["hung"]
                    w = face_point(i, j, f, s["u"], s["out"], 0.0)
                    props.append((_d2(v, w), "hung", s, w, (nx, nz)))
                if fc["smoker"] is not None:
                    s = fc["smoker"]
                    w = face_point(i, j, f, s["u"], s["out"], 0.0)
                    props.append((_d2(v, w), "smoker", s, w, (nx, nz)))
            else:
                if fc["bulb"] is not None:
                    s = fc["bulb"]
                    w = face_point(i, j, f, s["u"], s["out"], s["y"])
                    props.append((_d2(v, w), "bulb", s, w, (nx, nz)))
                if fc["bin"] is not None:
                    w = face_point(i, j, f, fc["bin"], 0.9, 0.0)
                    props.append((_d2(v, w), "bin", None, w, (nx, nz)))
                if fc["escape"] and climbable(i, j, f):
                    w = face_point(i, j, f, CELL * 0.5, 0.35, 0.0)
                    props.append((_d2(v, w), "ladder", None, w, (nx, nz)))
    props.sort(key=lambda p: -p[0])

    for _, kind, s, world, normal in props:
        if kind == "noren":
            draw_noren(ch, co, v, walls, world, normal, now)
        elif kind == "ramenfront":
            draw_ramen_front(ch, co, v, walls, *s, now, wet)
        elif kind == "ladder":
            # The drop ladder down to the ground, which is what says this one
            # goes all the way up - the others stop at the first landing.
            blit_sprite(ch, co, v, walls, ["|-|", "|-|", "|-|", "|-|"],
                        world[0], world[2], 0.0, 2.8, 0.7, CURB)
        elif kind == "lobby":
            draw_lobby(ch, co, v, walls, s, now)
        elif kind == "cinema":
            draw_cinema_front(ch, co, v, walls, s, world, now)
        elif kind == "temple":
            draw_temple_front(ch, co, v, walls, s, world, now)
        elif kind == "arcade":
            draw_arcade_front(ch, co, v, walls, s, world, now)
        elif kind == "exchange":
            draw_exchange_front(ch, co, v, walls, s, world, now)
        elif kind == "diner":
            draw_diner_sign(ch, co, v, walls, s, world, now)
        elif kind == "overdoor":
            tone = s[1]["tone"] if s[1] else 0.44
            draw_over_door(ch, co, v, walls, s[0], world, now, tone)
        elif kind == "lanterns":
            draw_lanterns(ch, co, v, walls, s[0], s[1], s[2], s[3], now, wet)
        elif kind == "marquee":
            draw_marquee(ch, co, v, walls, s, world, now)
        elif kind == "blade":
            draw_blade(ch, co, v, walls, *s, now)
        elif kind == "carpet":
            draw_red_carpet(ch, co, v, walls, *s, now)
        elif kind == "doorman":
            blit_sprite(ch, co, v, walls, DOORMAN, world[0], world[2], 0.05,
                        SMOKER_H * 1.02, SMOKER_W * 1.15,
                        FLASH if jackpot_on(now, s) and int(now * 6) % 2 else GOLD)
        elif kind == "hung":
            draw_hung_sign(ch, co, v, walls, s, world, normal, now, wet)
        elif kind == "raver":
            s["world"] = world
            draw_raver(ch, co, v, walls, s, now, wet)
        elif kind == "leaver":
            blit_sprite(ch, co, v, walls,
                        WALKER_A if int(s["stride"] / 0.6) % 2 == 0 else WALKER_B,
                        world[0], world[2], 0.0, SMOKER_H, SMOKER_W,
                        (CURB, BARK, tone_colour("warm", 0.5),
                         tone_colour("cold", 0.5))[s["tone"]])
        elif kind == "bass":
            draw_bass(ch, co, v, walls, *s, now, wet)
        elif kind == "bouncer":
            blit_sprite(ch, co, v, walls, BOUNCER, world[0], world[2], 0.05,
                        SMOKER_H * 1.08, SMOKER_W * 1.4, CURB)
        elif kind == "rope":
            draw_rope(ch, co, v, walls, *s, now)
        elif kind == "clubdoor":
            draw_door_light(ch, co, v, walls, *s, now)
        elif kind == "smoker":
            draw_smoker(ch, co, v, walls,
                        {"world": world, "normal": normal, "phase": s["phase"]},
                        now, wet)
        elif kind == "bin":
            blit_sprite(ch, co, v, walls, BIN, world[0], world[2],
                        0.0, 1.3, 1.5, CURB)
        else:
            # A bare bulb over a back door. The failing ones stutter, and an
            # alley lit by one of those is worse than an alley lit by none.
            sync = city_sync(now)
            if sync is not None:
                on = sync != "off"
                attr = FLASH if sync == "flash" else BULB
            else:
                on = True
                if s["dying"]:
                    p = (now * 3.1 + s["phase"]) % 1.0
                    on = p > 0.22 or int(now * 11 + s["phase"]) % 3 == 0
                attr = BULB if on else BULB_DIM
            put_lit(ch, co, v, walls, world[0], world[1], world[2],
                    "o" if on else ".", attr if on else BULB_DIM, wet, now)


def _d2(v, w):
    return (w[0] - v.x) ** 2 + (w[2] - v.z) ** 2


# ---------------------------------------------------------------------------
# Weather
# ---------------------------------------------------------------------------

# The cheat menu can pin the weather. Index 0 hands it back to the sky.
# (name, rain to pin it at or None to let the sky decide, is it a storm)
WEATHER_STEPS = [("auto", None, False, 0.0), ("dry", 0.0, False, 0.0),
                 ("drizzle", 0.18, False, 0.0), ("rain", 0.5, False, 0.0),
                 ("downpour", 0.95, False, 0.0), ("storm", 0.98, True, 0.0),
                 ("snow", 0.0, False, 0.8)]
_weather_i = 0
_forced_strike = None       # when a strike was called for, rather than due


SKY_MODES = ["as it comes", "clear", "cloudy", "overcast"]
CLOUD_BASE = 0.05      # where the sky's own cloud sits before its waves
_sky_mode = 0               # the cheat menu's hold on the cloud


def cycle_clouds():
    """As it comes, then held clear, held cloudy, held overcast. Overcast is
    pitch black: no stars, no moon, no milky way, no meteors - and on the
    strange night nothing up there either. The weather goes on underneath."""
    global _sky_mode
    _sky_mode = (_sky_mode + 1) % len(SKY_MODES)
    return clouds_name()


def clouds_name():
    return SKY_MODES[_sky_mode]


def overcast_held():
    return _sky_mode == 3


def cloud_cover(now):
    """How much of the sky is cloud, 0..1.

    It comes and goes on its own - three slow waves, like the rain's, on
    their own periods - so some stretches of a night are clear, some broken
    and some overcast, and a stretch of overcast is a night with no stars in
    it at all. Rain and snow bring their own cloud with them."""
    if _sky_mode == 1:
        return 0.0
    if _sky_mode == 2:
        return 0.65                     # broken: a few stars through it
    if _sky_mode == 3:
        return 1.0
    c = (CLOUD_BASE + 0.55 * math.sin(now / 233.0 + 0.7)
         + 0.30 * math.sin(now / 89.0 + 2.1)
         + 0.10 * math.sin(now / 29.0 + 0.3))
    c = max(c, min(1.0, rain_intensity(now) / 0.55), min(1.0, snowfall(now) * 1.4))
    return max(0.0, min(1.0, c))


def crown_light(now, wet):
    """The colour the sky decks' crowns are lit this instant, or None in the
    dark half of a flash. The weather is the whole city's, so it is worked
    out once a frame and every tower agrees."""
    word = sky_word(now, wet)
    blink = int(now * CROWN_BLINK * 2.0) % 2 == 0
    if word == "storm":
        return CROWN_RED if int(now * 8.0) % 2 else FLASH
    if "snow" in word:
        return CROWN_RED if blink else None
    if word in ("drizzle", "rain", "downpour"):
        return CROWN_RED
    if word in ("cloudy", "overcast"):
        return CROWN_BLUE if blink else None
    return CROWN_BLUE


def sky_word(now, wet):
    """The HUD's weather, with the cloud when it is not raining or snowing."""
    w = weather_word(now, wet)
    if w != "dry":
        return w
    c = cloud_cover(now)
    return "overcast" if c > 0.8 else ("cloudy" if c > 0.4 else "clear")


def cycle_weather():
    global _weather_i
    _weather_i = (_weather_i + 1) % len(WEATHER_STEPS)
    return WEATHER_STEPS[_weather_i][0]


def weather_name():
    return WEATHER_STEPS[_weather_i][0]


def force_strike(now):
    global _forced_strike
    _forced_strike = now


def storm_window(now):
    """(start, length) of the storm overhead, or None.

    Storms sit on a slot the way strikes used to, but a long one: one slot in
    six has a storm in it and a slot is three and a half minutes, so they come
    round about every twenty. A storm can run past the end of its own slot, so
    the slot before this one has to be asked as well."""
    k = int(now / STORM_SLOT)
    for kk in (k, k - 1):
        m = _mix(kk, 0, 617)
        if m % STORM_ODDS:
            continue
        start = kk * STORM_SLOT + ((m >> 8) & 1023) / 1023.0 * STORM_SLOT * 0.5
        length = STORM_SHORT + ((m >> 19) & 255) / 255.0 * (STORM_LONG - STORM_SHORT)
        if start <= now < start + length:
            return start, length
    return None


def storming(now):
    """Is there a storm overhead - either because the sky says so, or because
    the cheat menu is holding one there."""
    lock, forced = WEATHER_STEPS[_weather_i][1:3]
    if lock is not None:
        return forced
    return storm_window(now) is not None


def snow_window(now):
    """(start, length) of the snowfall, or None. Same shape as a storm, on
    its own slots and longer odds, and a storm always wins."""
    k = int(now / SNOW_SLOT)
    for kk in (k, k - 1):
        m = _mix(kk, 0, 619)
        if m % SNOW_ODDS:
            continue
        start = kk * SNOW_SLOT + ((m >> 8) & 1023) / 1023.0 * SNOW_SLOT * 0.3
        length = SNOW_SHORT + ((m >> 19) & 255) / 255.0 * (SNOW_LONG - SNOW_SHORT)
        if start <= now < start + length and storm_window(now) is None:
            return start, length
    return None


def snowfall(now):
    """How hard it is snowing, 0..1 - easing in and off over fifteen seconds."""
    lock = WEATHER_STEPS[_weather_i][1]
    if lock is not None:
        return WEATHER_STEPS[_weather_i][3]
    w = snow_window(now)
    if w is None:
        return 0.0
    start, length = w
    t = now - start
    edge = min(1.0, t / 15.0, (length - t) / 15.0)
    return 0.35 + 0.55 * edge * (0.75 + 0.25 * math.sin(now / 9.0))


def snow_cover(now):
    """How much snow is lying, 0..1. It builds while it falls and melts after,
    so the city stays white for a while once the sky has cleared."""
    lock = WEATHER_STEPS[_weather_i][1]
    if lock is not None:
        return 1.0 if WEATHER_STEPS[_weather_i][3] > 0 else 0.0
    k = int(now / SNOW_SLOT)
    best = 0.0
    for kk in range(k - int(SNOW_MELT / SNOW_SLOT) - 2, k + 1):
        m = _mix(kk, 0, 619)
        if m % SNOW_ODDS:
            continue
        start = kk * SNOW_SLOT + ((m >> 8) & 1023) / 1023.0 * SNOW_SLOT * 0.3
        length = SNOW_SHORT + ((m >> 19) & 255) / 255.0 * (SNOW_LONG - SNOW_SHORT)
        if now < start:
            continue
        fell = min(now, start + length) - start
        lying = min(1.0, fell / SNOW_SETTLE)
        if now > start + length:
            lying *= max(0.0, 1.0 - (now - start - length) / SNOW_MELT)
        best = max(best, lying)
    return best


def rain_intensity(now):
    """It comes and goes. Three slow waves that never quite line up, so the
    weather swells to a downpour, eases off, and now and then stops - and a
    storm brings its own rain regardless of where those waves happen to be."""
    lock = WEATHER_STEPS[_weather_i][1]
    if lock is not None:
        return lock
    v = (0.42
         + 0.42 * math.sin(now / 41.0)
         + 0.26 * math.sin(now / 13.7 + 1.2)
         + 0.13 * math.sin(now / 5.3 + 2.6))
    if snow_window(now) is not None:
        return 0.0                      # what is falling is snow
    storm = storm_window(now)
    if storm is not None:
        start, length = storm
        t = now - start
        edge = min(1.0, t / 7.0, (length - t) / 7.0)    # it rolls in and off
        v = max(v, 0.55 + 0.43 * edge)
    return max(0.0, min(1.0, v))


def _strike_flash(t, twice):
    """The shape of one strike, as a brightness over time.

    Sub-flashes riding on a glow that does not go out until the strike is over.
    The flicker on its own measured as three isolated frames with dark gaps
    between them - at thirty frames a second that is a blink, and one you can
    easily sit through without noticing the city lit up at all. The glow
    underneath is what turns it into a single event you can see, and the tail
    is most of what you actually register.

    Shared, so a strike you asked for is the same strike the storm was going to
    have anyway."""
    if not 0.0 <= t < 1.7:
        return 0.0
    peak = 0.0
    for n, (delay, amp, span) in enumerate(((0.00, 1.00, 0.10),
                                            (0.16, 0.88, 0.09),
                                            (0.36, 0.62, 0.08))):
        if n == 2 and twice:
            break
        if 0.0 <= t - delay < span:
            peak = amp
    return max(peak, 0.78 * math.exp(-t * 2.3))


def lightning(now, wet):
    """How bright the sky is this instant, 0..1.

    Storms only happen in heavy rain, and even then only one slot in seven has
    a strike in it, so this is quiet for minutes at a time - which is the whole
    point of it."""
    if _forced_strike is not None:
        b = _strike_flash(now - _forced_strike, False)
        if b:
            return b                    # asked for, so it comes even when dry
    if not storming(now):
        return 0.0
    # Inside one they come thick and fast: every slot has a strike in it, and a
    # slot is under three seconds, so with a flash lasting most of two the sky
    # is rarely dark for long.
    k = int(now / STRIKE_EVERY)
    m = _mix(k, 0, 401)
    at = k * STRIKE_EVERY + ((m >> 8) & 1023) / 1023.0 * (STRIKE_EVERY - 1.6)
    # Not all of them are overhead. Scaling each strike gives the storm some
    # near ones and some away over the next district, which is the difference
    # between weather and a metronome.
    power = 0.45 + ((m >> 12) & 255) / 255.0 * 0.55
    return power * _strike_flash(now - at, bool((m >> 20) & 1))


def club_light(now, club):
    """What is coming out of the club this instant, or None while it is dark.

    Four to the floor at 134, with the strobe let off the leash at the end of
    every eighth bar - except on the one night a year the sky is doing
    something, when whoever is on gives up and mixes into it."""
    sync = city_sync(now)
    if sync is not None:
        if sync == "flash":
            return FLASH
        if sync == "off":
            return None
        return NEON[min(len(NEON) - 1, int(club["tone"] * len(NEON)))][0]
    if club_closing(now) is not None:
        return BULB                     # the house lights, and no beat at all
    t = now * CLUB_BPM / 60.0 + club["phase"]
    beat = t % 1.0
    if (int(t) // 4) % 8 == 7 and int(t * 8) % 2:
        return FLASH                    # the strobe run that ends a phrase
    if beat < 0.11:
        return FLASH                    # the kick
    if beat < 0.32:
        return NEON[min(len(NEON) - 1, int(club["tone"] * len(NEON)))][0]
    return None


NIGHT_LENGTH = 690.0    # how long one night lasts, before the next one

# Once in a great while the sky has something else going on in it. One night in
# forty, so about seven hours of walking between them - it is meant to be the
# thing you tell someone about, not a feature you get used to.
ALIEN_ODDS = 40
ALIEN_BPM = 141.0
_night_cache = {}
_night_skip = 0.0       # nights the menu has stepped over


def skip_to_alien(now):
    """Straight to the next night that has something in it.

    One night in forty is about seven hours of walking, and stepping there a
    night at a time is not much better - the menu exists to reach things."""
    global _night_skip
    for _ in range(ALIEN_ODDS * 8):
        _night_skip += NIGHT_LENGTH
        if night(now)["alien"]:
            return True
    return False


def dawn(now):
    """How far into the morning it is, 0..1: zero on every night without
    one and until its last DAWN_LEN seconds, then rising to one and held
    there for the last DAWN_HOLD."""
    if not night(now)["dawn"]:
        return 0.0
    t = (now + _night_skip) % NIGHT_LENGTH
    start = NIGHT_LENGTH - DAWN_LEN
    if t < start:
        return 0.0
    return min(1.0, (t - start) / (DAWN_LEN - DAWN_HOLD))


def skip_to_dawn(now):
    """To the next night that ends in a morning, and to a few seconds before
    the sky starts to go - a night is eleven minutes, and the dawn is the
    last two of them."""
    global _night_skip
    for _ in range(DAWN_ODDS * 8):
        _night_skip += NIGHT_LENGTH
        if night(now)["dawn"]:
            t = (now + _night_skip) % NIGHT_LENGTH
            _night_skip += (NIGHT_LENGTH - DAWN_LEN - 5.0) - t
            return night(now)["dawn"]
    return False


def skip_to_closing(now):
    """To a few seconds before the clubs close - on a night that is not the
    strange one, since they never close on that."""
    global _night_skip
    for _ in range(ALIEN_ODDS + 2):
        if not night(now)["alien"]:
            t = (now + _night_skip) % NIGHT_LENGTH
            _night_skip += (NIGHT_LENGTH - CLOSE_LEN - 3.0 - t) % NIGHT_LENGTH
            if not night(now)["alien"]:
                return True
        _night_skip += NIGHT_LENGTH
    return False


def skip_to_fireworks(now):
    """Straight to the next night with a show over the bay."""
    global _night_skip
    for _ in range(FIREWORK_ODDS * 8):
        _night_skip += NIGHT_LENGTH
        if night(now)["fireworks"]:
            return True
    return False


def skip_to_lanterns(now):
    """Straight to the next night with lanterns on the river."""
    global _night_skip
    for _ in range(LANTERN_ODDS * 8):
        _night_skip += NIGHT_LENGTH
        if night(now)["lanterns"]:
            return True
    return False


def skip_night():
    """On to the next one. Waiting eleven minutes to see whether the next sky
    is any different is not a way to look at anything."""
    global _night_skip
    _night_skip += NIGHT_LENGTH
    return int((_night_skip / NIGHT_LENGTH) % 1000)


def night(now):
    """What kind of night this is.

    Everything comes off a hash of the night's number, so it is the same night
    whenever you come back to it, and the next one is nothing like it. Keep the
    ranges narrow: a sky that changes a lot between nights stops reading as
    weather and starts reading as a different program."""
    k = int((now + _night_skip) / NIGHT_LENGTH)
    got = _night_cache.get(k)
    if got is None:
        if len(_night_cache) > 400:
            _night_cache.clear()
        m = _mix(k, 0, 613)
        got = {
            # Squared, so most nights are middling and a properly clear one is
            # worth staying out for.
            "clarity": 0.22 + (((m & 255) / 255.0) ** 1.7) * 0.78,
            "phase": ((m >> 8) & 255) / 255.0,        # 0 new, 0.5 full, 1 new
            "alt": 0.30 + ((m >> 16) & 31) / 31.0 * 0.55,
            "swing": ((m >> 21) & 255) / 255.0 * math.tau,
            "band": (m >> 4) % 3 == 0,                # the milky way is up
            "tilt": (((m >> 6) & 15) / 15.0 - 0.5) * 0.66,
            "warmth": 0.15 + ((m >> 11) & 15) / 15.0 * 0.4,
            "meteors": (m >> 29) & 7,
            "alien": (m >> 24) % ALIEN_ODDS == 0,
            "mist": ((m >> 27) & 7) / 7.0,         # how much comes off the water
            "mother": ((m >> 13) & 255) / 255.0,   # when the big one crosses
            "lands": ((m >> 2) & 255) / 255.0,     # and when one beam stops
            "lanterns": (m >> 19) % LANTERN_ODDS == 0 and (m >> 24) % ALIEN_ODDS,
        }
        # On its own hash, so it is not tied to any of the above; and never on
        # the strange night or the lantern night, which have the sky and the
        # river to themselves.
        got["fireworks"] = (_mix(k, 1, 613) % FIREWORK_ODDS == 0
                            and not got["alien"] and not got["lanterns"])
        # The strange night does not end in a morning. Whatever that was, it
        # is the one night the city never wakes up from.
        got["dawn"] = _mix(k, 2, 613) % DAWN_ODDS == 0 and not got["alien"]
        if got["alien"]:
            # Whatever the weather was going to be up there, the sky is lit by
            # what is in it tonight.
            got["clarity"] = 1.0
            got["band"] = True
        _night_cache[k] = got
    return got


def city_sync(now):
    """How the whole city is lit this instant, or None on an ordinary night.

    On the strange one everything electric in the place gives up its own
    schedule and takes the sky's: "flash" is the kick, and every sign, bulb and
    lantern in view goes white together; "on" and "off" are the half of the bar
    either side of it. Signs keep their own colours through it - one beat, not
    one colour, or the city flattens into a single wash and stops being a city.

    Cheap on purpose: it is asked once per sign per frame, so it is a dict
    lookup and two multiplies."""
    if not night(now)["alien"]:
        return None
    t = now * ALIEN_BPM / 60.0
    if (int(t) // 4) % 8 == 7 and int(t * 6) % 2:
        return "flash"
    beat = t % 1.0
    if beat < 0.13:
        return "flash"
    return "on" if beat < 0.52 else "off"


def alien_light(now, k):
    """What the sky is doing this instant on the night it is doing something.

    The same four-to-the-floor the club runs on, because that is what a beat
    looks like in this program, but the whole sky is the rig: k walks the
    colour round so the field shifts rather than blinking on and off in one
    colour, and the kick takes everything white at once."""
    t = now * ALIEN_BPM / 60.0
    beat = t % 1.0
    if (int(t) // 4) % 8 == 7 and int(t * 6) % 2:
        return FLASH                    # the run that ends a phrase
    if beat < 0.13:
        return FLASH
    return NEON[(k + int(t)) % len(NEON)][0 if beat < 0.55 else 1]


def draw_sky_beams(ch, co, v, tops, now, seen):
    """Beams swung across the whole sky from somewhere out past the horizon.

    Drawn on the sky only - they stop dead at the rooftops, which is what keeps
    it a thing happening above the city rather than a filter over the picture."""
    t = now * ALIEN_BPM / 60.0
    for k in range(4):
        a = math.sin(t * (0.09 + k * 0.031) + k * 2.1)
        col = int((0.5 + 0.5 * a) * (v.width - 1))
        attr = NEON[(k + int(t / 4)) % len(NEON)][0]
        glyph = "\\" if a > 0.25 else ("/" if a < -0.25 else "|")
        for y in range(v.horizon):
            x = col + int((v.horizon - y) * a * 1.9)
            # A beam washes over the stars rather than threading between them:
            # made to fit in the gaps it disappears entirely, because on this
            # night there are no gaps left. It still stops at the rooftops,
            # which is what keeps it a thing happening over the city.
            if 0 <= x < v.width and y < tops[x]:
                ch[y][x] = glyph
                co[y][x] = attr
                seen.add((y, x))


MOTHER = [
    "        __________________        ",
    "    ,-''                  ''-,    ",
    "  ,'   .   .   .   .   .   .   ', ",
    " /______________________________\\ ",
    " \\    o       o       o       o / ",
    "  '----------------------------'  ",
]

MOTHER_CROSS = 115.0    # seconds end to end, which is not fast


def draw_mother(ch, co, v, tops, now, seen):
    """The big one. Once a night, and it takes two minutes to go over.

    Placed by bearing rather than column, because something this size sliding
    about as you turn your head would give the whole thing away. Slow is the
    point: the little saucers dart, and this does not."""
    n = night(now)
    t = (now + _night_skip) % NIGHT_LENGTH
    at = n["mother"] * (NIGHT_LENGTH - MOTHER_CROSS)
    k = (t - at) / MOTHER_CROSS
    if not 0.0 <= k < 1.0:
        return
    bearing = n["swing"] + (k - 0.5) * 3.4
    x0 = v.sky_x(bearing)
    if x0 is None:
        return
    y0 = 1 + int(0.18 * v.horizon)
    lights = int(now * ALIEN_BPM / 60.0 * 2)
    for r, line in enumerate(MOTHER):
        y = y0 + r
        if not 0 <= y < v.horizon:
            continue
        for c, glyph in enumerate(line):
            x = x0 - len(line) // 2 + c
            if not (0 <= x < v.width and y < tops[x]):
                continue
            # Blanks are hull too, and they blot out the stars behind them.
            # Letting the sky show through a thing this size makes it read as a
            # pattern laid over the stars rather than as something in the way
            # of them, which is the whole of why it is worth drawing big.
            if glyph == " ":
                if r in (0, len(MOTHER) - 1) and line.strip():
                    continue
                ch[y][x] = " "
                seen.add((y, x))
                continue
            ch[y][x] = glyph
            co[y][x] = (NEON[(c + lights) % len(NEON)][0]
                        if glyph in "o." else MOON_DIM)
            seen.add((y, x))


def draw_landing_beam(ch, co, v, tops, now, seen):
    """One of them stops sweeping and stands still on a rooftop.

    No explanation offered. It holds for eight seconds, which is long enough
    that you notice it has stopped, and it goes all the way down to whatever it
    has picked out rather than fading into the sky."""
    n = night(now)
    t = (now + _night_skip) % NIGHT_LENGTH
    at = n["lands"] * (NIGHT_LENGTH - 40.0)
    k = t - at
    if not 0.0 <= k < 8.0:
        return
    bearing = n["swing"] + 1.1
    x0 = v.sky_x(bearing)
    if x0 is None:
        return
    # Fades up over the first second and out over the last, so it arrives
    # rather than being switched on.
    edge = min(1.0, k / 1.0, (8.0 - k) / 1.5)
    attr = FLASH if int(now * 6) % 2 else NEON[int(now) % len(NEON)][0]
    half = max(1, int(2 * edge))
    for x in range(x0 - half, x0 + half + 1):
        if not 0 <= x < v.width:
            continue
        for y in range(min(tops[x], v.horizon)):
            ch[y][x] = "|" if x == x0 else ":"
            co[y][x] = attr
            seen.add((y, x))


SAUCER = "<-o->"


def draw_saucers(ch, co, v, tops, now, seen):
    """Three of them, crossing slowly, lights going round the rim."""
    t = now * ALIEN_BPM / 60.0
    for k in range(3):
        m = _mix(k, 0, 991)
        drift = (now * (0.03 + k * 0.012) + (m & 255) / 255.0) % 1.0
        x0 = int(drift * (v.width + 12)) - 6
        y = 1 + (m >> 9) % max(1, v.horizon - 3)
        for i, c in enumerate(SAUCER):
            x = x0 + i
            if not (0 <= x < v.width and 0 <= y < tops[x] and y < v.horizon):
                continue
            ch[y][x] = c
            co[y][x] = (NEON[(i + int(t * 2)) % len(NEON)][0]
                        if c == "-" else MOON)
            seen.add((y, x))


def moon_dir(now):
    """Where the moon is: bearing in radians, and height up the sky.

    It crosses through the night rather than sitting still, which is most of
    what makes one night feel like a different night from the last."""
    n = night(now)
    t = ((now + _night_skip) % NIGHT_LENGTH) / NIGHT_LENGTH
    climb = 0.55 + 0.45 * math.sin(math.pi * t)
    return n["swing"] + (t - 0.5) * 1.6, n["alt"] * climb


def moon_face(phase):
    """The moon as one or two characters. New is nothing at all, which is a
    perfectly good night in its own right."""
    p = abs(phase - 0.5) * 2.0          # 0 full, 1 new
    if p > 0.88:
        return ""
    if p > 0.62:
        return ")" if phase < 0.5 else "("
    if p > 0.34:
        return "D" if phase < 0.5 else "C"
    if p > 0.12:
        return "O"
    return "()"


def weather_word(now, wet):
    if storming(now):
        return "storm"
    s = snowfall(now)
    if s > 0.0:
        return "light snow" if s < 0.5 else ("heavy snow" if s > 0.8 else "snow")
    if wet < 0.04:
        return "dry"
    if wet < 0.3:
        return "drizzle"
    if wet < 0.7:
        return "rain"
    return "downpour"


def draw_snow(ch, co, v, walls, now):
    """Flakes on a world-locked lattice like the rain, but slow, and each on
    its own sway, so the air is full of things drifting rather than falling.
    Near ones are stars, far ones dots."""
    if v.snow < 0.03:
        return
    gi = int(v.x / RAIN_LATTICE + BIG) - BIG
    gj = int(v.z / RAIN_LATTICE + BIG) - BIG
    top = v.eye + 9.0
    for a in range(gi - RAIN_REACH, gi + RAIN_REACH + 1):
        for b in range(gj - RAIN_REACH, gj + RAIN_REACH + 1):
            m = _mix(a, b, 331)
            if (m & 1023) > v.snow * 700:
                continue
            phase = ((m >> 10) & 255) / 256.0
            y = top - ((now * SNOW_SPEED + phase * top) % top)
            sway = 0.7 * math.sin(now * 0.8 + phase * 9.0)
            x = (a + ((m >> 18) & 63) / 64.0) * RAIN_LATTICE + sway
            z = (b + ((m >> 24) & 63) / 64.0) * RAIN_LATTICE
            if not open_at(x, z) or tunnel_at(int(x / CELL + BIG) - BIG,
                                              int(z / CELL + BIG) - BIG):
                continue                  # it is not snowing indoors
            pr = v.project(x, y, z)
            if pr is None:
                continue
            put_cell(ch, co, v, walls, int(round(pr[0])), int(round(pr[1])), pr[2],
                     "*" if pr[2] < 6.0 else ("'" if pr[2] < 14.0 else "."), SNOW)


def draw_rain(ch, co, v, walls, now, wet):
    """Drops on a world-locked lattice, so they hold still relative to the city
    while you walk and turn through them.

    Each is drawn as the short segment it fell through since the frame before,
    which is what gives the streak its slant - both the wind's and the
    perspective's - without any of it being faked in screen space."""
    if wet < 0.03:
        return
    wind = 0.5 * math.sin(now / 23.0) + 0.2 * math.sin(now / 7.1)
    gi = int(v.x / RAIN_LATTICE + BIG) - BIG
    gj = int(v.z / RAIN_LATTICE + BIG) - BIG
    fall = now * RAIN_SPEED / RAIN_TOP
    limit = PLANE * 1.25

    for a in range(gi - RAIN_REACH, gi + RAIN_REACH + 1):
        for b in range(gj - RAIN_REACH, gj + RAIN_REACH + 1):
            m = _mix(a, b, 313)
            if (m & 1023) > wet * 1023:
                continue
            x = (a + ((m >> 10) & 63) / 64.0) * RAIN_LATTICE
            z = (b + ((m >> 16) & 63) / 64.0) * RAIN_LATTICE
            rx, rz = x - v.x, z - v.z
            perp = rx * v.dx + rz * v.dz
            if perp < NEAR_Z:
                continue
            if abs(rx * v.dz - rz * v.dx) > perp * limit:
                continue
            if not open_at(x, z) or tunnel_at(int(x / CELL + BIG) - BIG,
                                              int(z / CELL + BIG) - BIG):
                continue                      # it is not raining indoors

            phase = ((m >> 22) & 255) / 256.0
            drop = (fall + phase) % 1.0
            y = RAIN_TOP * (1.0 - drop)
            y0 = min(RAIN_TOP, y + RAIN_SPEED * RAIN_STREAK)
            blow = wind * (RAIN_TOP - y)
            blow0 = wind * (RAIN_TOP - y0)
            p1 = v.project(x + blow, y, z)
            p0 = v.project(x + blow0, y0, z)
            if p0 is None or p1 is None:
                continue
            attr = FLASH if v.flash > 0.35 else (
                RAIN if perp < 9.0 else RAIN_FAR)
            _streak(ch, co, v, walls, p0, p1, attr)


def _streak(ch, co, v, walls, p0, p1, attr):
    x0, y0 = p0[0], p0[1]
    x1, y1 = p1[0], p1[1]
    steps = min(3, max(1, int(abs(y1 - y0))))
    glyph = "|" if abs(x1 - x0) < 0.9 else ("\\" if x1 > x0 else "/")
    for k in range(steps + 1):
        t = k / (steps + 1.0)
        put_cell(ch, co, v, walls,
                 int(round(x0 + (x1 - x0) * t)),
                 int(round(y0 + (y1 - y0) * t)),
                 p1[2], glyph, attr)


# ---------------------------------------------------------------------------

def render_street(v, now):
    ch = [[" "] * v.width for _ in range(v.height)]
    co = [[0] * v.width for _ in range(v.height)]
    wet = v.wet = rain_intensity(now)
    v.flash = lightning(now, wet)
    v.snow = snowfall(now)
    v.cover = snow_cover(now)
    v.dawn = dawn(now)
    v.crown = crown_light(now, wet)
    v.bass = bass_lots(v, now)

    rave = None
    if rave_window(now) is not None:
        hx, hz, hi_, hj_ = nearest_hollow(v.x, v.z)
        if (hx - v.x) ** 2 + (hz - v.z) ** 2 < 130.0 ** 2:
            m = _mix(hi_, hj_, 977)
            phase = (m & 255) / 255.0 * 6.0
            lamp = rave_light(now, phase, ((m >> 8) & 255) / 255.0)
            beat = (now * RAVE_BPM / 60.0 + phase) % 1.0
            rave = (hi_, hj_)
            if lamp is not None:
                v.rave = (lamp, hx, hz)
            v.hollow = (hx, hz + HOLLOW_RJ * CELL * 0.72, beat, lamp)

    v.tunnels = near_tunnels(v, 90.0)
    walls = draw_walls(ch, co, v, now)
    draw_sky(ch, co, v, walls, wet, now)
    draw_ground(ch, co, v, walls, collect_glow(v, now, wet), wet, now)
    tunnels = v.tunnels
    draw_tunnel_ceiling(ch, co, v, walls, now, tunnels)
    draw_flash(ch, co, v, walls, v.flash)
    # Before the props, so a sign out front is never painted over by a
    # beam going up behind it.
    for c_ in near_cinemas(v, SEARCH_REACH):
        draw_searchlights(ch, co, v, walls, c_, now)
    for d_ in near_diners(v, CUP_REACH):
        draw_diner_cup(ch, co, v, walls, d_, now)
    draw_props(ch, co, v, walls, now, wet)
    draw_manhole_steam(ch, co, v, walls, now)
    draw_car_park(ch, co, v, walls, now, wet)
    draw_walkers(ch, co, v, walls, now, wet)
    draw_traffic(ch, co, v, walls, now, wet)
    for ex0, ex1 in near_els(v, EL_REACH):
        draw_el(ch, co, v, walls, ex0, ex1, now, wet)
    for hx0, hx1 in near_hwys(v, HWY_REACH if v.eye < 10.0 else ROOF_REACH):
        draw_hwy(ch, co, v, walls, hx0, hx1, now, wet)
    for tx0, tx1, tz0, tz1, kind in tunnels:
        draw_headwall(ch, co, v, walls, tx0, tx1, tz0, -1.0)
        draw_headwall(ch, co, v, walls, tx0, tx1, tz1, 1.0)
        if kind == "short":
            draw_camp(ch, co, v, walls, tx0, tx1, tz0, tz1, now, wet)
        else:
            z = tz0 + TUNNEL_LAMP * 0.5
            while z < tz1:
                put_lit(ch, co, v, walls, (tx0 + tx1) * 0.5, TUNNEL_H - 0.15, z,
                        "o", EMBER_HOT, max(wet, 0.3), now)
                z += TUNNEL_LAMP
    for bb in near_billboards(v, BILL_SEEN if v.eye < 10.0 else ROOF_REACH):
        draw_billboard(ch, co, v, walls, bb, now, wet)
    for lm_ in near_landmarks(v, 320.0):
        draw_spire(ch, co, v, walls, lm_, now, wet)
        if v.roof is not None and v.roof.get("landmark") is lm_:
            draw_party_floor(ch, co, v, lm_, now)
        x0_, z0_, x1_, z1_ = party_roof(lm_)
        if (((x0_ + x1_) * 0.5 - v.x) ** 2 + ((z0_ + z1_) * 0.5 - v.z) ** 2
                < 160.0 ** 2 and v.eye > LANDMARK_H - 10.0):
            draw_party(ch, co, v, walls, lm_, now, wet)
    for t_ in near_towers(v, 150.0 if v.eye < 10.0 else ROOF_REACH):
        if v.roof is None or t_["i"] != v.roof["i"] or t_["j"] != v.roof["j"]:
            draw_tower_beacon(ch, co, v, walls, t_, now, wet)
    if v.roof is not None:
        draw_roof_ledge(ch, co, v, walls, v.roof, now, wet)
    for ci_, cj_ in near_dock_cranes(v, 95.0):
        draw_dock_crane(ch, co, v, walls, ci_, cj_, now, wet)
    for prun, pend in near_piers(v, 95.0):
        draw_pier(ch, co, v, walls, prun, pend, now, wet)
    if v.water and abs(v.z - river_centre(int(v.x / CELL)) * CELL) < 250.0:
        draw_gulls(ch, co, v, walls, now)      # the river's, not the lake's
    for bx, bz, bm in near_buoys(v, 90.0):
        draw_buoy(ch, co, v, walls, bx, bz, bm, now, wet)
    for c_ in near_carnivals(v, 170.0):
        draw_carnival(ch, co, v, walls, c_, now, wet)
    for s_ in near_promenades(v, 110.0):
        draw_promenade(ch, co, v, walls, s_, now, wet)
    for bx, bz in near_rowboats(v, now, 120.0):
        draw_rowboat(ch, co, v, walls, bx, bz, now, wet)
    ci_ = int(v.x / CELL + BIG) - BIG
    for k_ in range(-1, 2):
        fs = ferry_spot(now, ci_ + k_ * GRAND_GAP)
        if fs is not None and (fs[0] - v.x) ** 2 + (fs[1] - v.z) ** 2 < 220.0 ** 2:
            draw_ferry(ch, co, v, walls, fs[0], fs[1], fs[2], now, wet)
    draw_fireworks(ch, co, v, walls, now, wet)
    reflect_river(ch, co, v, walls, now, wet)
    if night(now)["lanterns"] and v.water:
        # After the reflection, or the far bank's windows lying on the water
        # are painted over the lanterns floating on it.
        draw_river_lanterns(ch, co, v, walls, now, wet)
    for i, j in near_yokocho(v, 55.0):
        draw_lantern_string(ch, co, v, walls, i, j, now)
    for i, j in near_bridges(v, GRAND_SEEN):
        if grand_at(i):
            draw_grand_bridge(ch, co, v, walls, i, j, now, wet)
    for lx, lz in near_lighthouses(v, 420.0):
        draw_lighthouse(ch, co, v, walls, lx, lz, now, wet)
    for i, j in near_bridges(v, BRIDGE_SEEN):
        if not grand_at(i):
            draw_bridge_ends(ch, co, v, walls, i, j, now, wet)
    for i, j in near_bridges(v, 85.0):
        if not grand_at(i):
            draw_bridge(ch, co, v, walls, i, j, now, wet)
    draw_river_mist(ch, co, v, walls, now, wet)
    if woods_depth(int(v.x / CELL + BIG) - BIG, int(v.z / CELL + BIG) - BIG) > -8.0:
        draw_woods_life(ch, co, v, walls, now, wet)
    if rave is not None:
        draw_drawn_in(ch, co, v, walls, rave[0], rave[1], now)
        draw_hollow_rave(ch, co, v, walls, rave[0], rave[1], now, wet)
    draw_rain(ch, co, v, walls, now, wet)
    draw_snow(ch, co, v, walls, now)
    return ch, co, wet


# ---------------------------------------------------------------------------
# Finding your way, and letting it find its own
# ---------------------------------------------------------------------------

def start_position():
    """Somewhere out in the open to begin, near the origin."""
    for r in range(0, 40):
        for i in range(-r, r + 1):
            for j in (-r, r):
                for a, b in ((i, j), (j, i)):
                    x, z = (a + 0.5) * CELL, (b + 0.5) * CELL
                    if can_stand(x, z):
                        return x, z
    return 0.0, 0.0


def probe(x, z, yaw, reach):
    """How far you could walk on this bearing before something stopped you."""
    dx, dz = math.sin(yaw), math.cos(yaw)
    d = 1.0
    while d < reach:
        if not can_stand(x + dx * d, z + dz * d):
            return d
        d += 1.2
    return reach


def wander(x, z, yaw, now):
    """Which way to lean, given what is open around you.

    Picking the single best-scoring direction makes the walk twitch, because
    the winner changes outright from one frame to the next. Blending all of
    them by score gives a heading that moves continuously instead, and one that
    sits between two equally good options rather than flipping between them."""
    acc = weight = 0.0
    for off in (-1.15, -0.75, -0.4, -0.15, 0.0, 0.15, 0.4, 0.75, 1.15):
        clear = probe(x, z, yaw + off, 22.0)
        score = clear + 5.0 * math.cos(off) + 7.0 * math.sin(now * 0.11 + off * 2.7)
        w = math.exp(score / 6.0)
        acc += w * off
        weight += w
    return acc / weight


# ===========================================================================
# THE CASINO - the one place in the city you can walk into
# ===========================================================================

# A single-zero wheel, in the order the pockets actually come in. That order is
# not decorative: it is what puts high next to low and red next to black all
# the way round, and you can see it turning.
WHEEL = [0, 32, 15, 19, 4, 21, 2, 25, 17, 34, 6, 27, 13, 36, 11, 30, 8, 23,
         10, 5, 24, 16, 33, 1, 20, 14, 31, 9, 22, 18, 29, 7, 28, 12, 35, 3, 26]
REDS = frozenset([1, 3, 5, 7, 9, 12, 14, 16, 18, 19, 21, 23, 25, 27, 30, 32,
                  34, 36])

DIGITS = {
    "0": ("###", "# #", "# #", "# #", "###"),
    "1": ("  #", "  #", "  #", "  #", "  #"),
    "2": ("###", "  #", "###", "#  ", "###"),
    "3": ("###", "  #", "###", "  #", "###"),
    "4": ("# #", "# #", "###", "  #", "  #"),
    "5": ("###", "#  ", "###", "  #", "###"),
    "6": ("###", "#  ", "###", "# #", "###"),
    "7": ("###", "  #", "  #", "  #", "  #"),
    "8": ("###", "# #", "###", "# #", "###"),
    "9": ("###", "# #", "###", "  #", "###"),
}

# The same three-by-five, for words: the cinema's title over the doors and
# the arcade's sign. Big enough to read across a street, which a row of
# ordinary letters a building wide is not.
LETTERS = {
    "A": (" # ", "# #", "###", "# #", "# #"),
    "B": ("## ", "# #", "## ", "# #", "## "),
    "C": (" ##", "#  ", "#  ", "#  ", " ##"),
    "D": ("## ", "# #", "# #", "# #", "## "),
    "E": ("###", "#  ", "## ", "#  ", "###"),
    "F": ("###", "#  ", "## ", "#  ", "#  "),
    "G": (" ##", "#  ", "# #", "# #", " ##"),
    "H": ("# #", "# #", "###", "# #", "# #"),
    "I": ("###", " # ", " # ", " # ", "###"),
    "J": ("  #", "  #", "  #", "# #", " # "),
    "K": ("# #", "# #", "## ", "# #", "# #"),
    "L": ("#  ", "#  ", "#  ", "#  ", "###"),
    "M": ("# #", "###", "# #", "# #", "# #"),
    "N": ("## ", "# #", "# #", "# #", "# #"),
    "O": (" # ", "# #", "# #", "# #", " # "),
    "P": ("## ", "# #", "## ", "#  ", "#  "),
    "Q": (" # ", "# #", "# #", "## ", " ##"),
    "R": ("## ", "# #", "## ", "# #", "# #"),
    "S": (" ##", "#  ", " # ", "  #", "## "),
    "T": ("###", " # ", " # ", " # ", " # "),
    "U": ("# #", "# #", "# #", "# #", "###"),
    "V": ("# #", "# #", "# #", "# #", " # "),
    "W": ("# #", "# #", "# #", "###", "# #"),
    "X": ("# #", "# #", " # ", "# #", "# #"),
    "Y": ("# #", "# #", " # ", " # ", " # "),
    "Z": ("###", "  #", " # ", "#  ", "###"),
    " ": ("   ",) * 5,
    "-": ("   ", "   ", "###", "   ", "   "),
    "!": (" # ", " # ", " # ", "   ", " # "),
    "?": ("## ", "  #", " # ", "   ", " # "),
    "'": (" # ", " # ", "   ", "   ", "   "),
    ".": ("   ", "   ", "   ", "   ", " # "),
}
BIG_FONT = dict(DIGITS, **LETTERS)


def big_width(text):
    """Columns a word takes in the big font: three a letter and one between."""
    return max(0, len(text) * 4 - 1)


def big_cells(text):
    """(column, row, which letter) of every lit cell of a word in the big font."""
    for k, c in enumerate(text):
        for row, line in enumerate(BIG_FONT.get(c, BIG_FONT["?"])):
            for dx, px in enumerate(line):
                if px != " ":
                    yield k * 4 + dx, row, k

# Everything else in this file is a hash of where you are, so that the city is
# the same city every time you walk back to it. This one thing is not, and must
# not be: a wheel you could predict is not a wheel.
_spin_rng = random.Random()

SPIN_TIME = 5.2        # seconds of ball before it drops
HOLD_TIME = 3.6        # and how long the number stays up afterwards


def pocket_colour(n):
    return ROU_GREEN if n == 0 else (ROU_RED if n in REDS else ROU_BLACK)


class Spin:
    """One throw of the ball.

    The result is drawn first and the flight is then solved to end on it: the
    ball eases to a stop over a whole number of turns plus exactly the offset
    that lands it in the right pocket, so the wheel is honest but the animation
    never has to guess where it is going."""

    def __init__(self, now, name):
        self.name = name
        self.t0 = now
        self.result = _spin_rng.randrange(37)
        self.idx = WHEEL.index(self.result)
        self.wheel0 = _spin_rng.uniform(0.0, math.tau)
        self.wheel_w = -0.55 - _spin_rng.random() * 0.25   # the wheel's own turn
        self.ball0 = _spin_rng.uniform(0.0, math.tau)
        turns = 7 + _spin_rng.randrange(4)
        end = self.wheel_at(SPIN_TIME) + self.idx * math.tau / 37.0
        # However far round that is from where the ball starts, plus whole turns.
        self.sweep = turns * math.tau + (end - self.ball0) % math.tau

    def wheel_at(self, t):
        return self.wheel0 + self.wheel_w * t

    def ball_at(self, t):
        if t >= SPIN_TIME:
            return self.wheel_at(t) + self.idx * math.tau / 37.0
        k = 1.0 - t / SPIN_TIME
        return self.ball0 + self.sweep * (1.0 - k * k * k)

    def settled(self, now):
        return now - self.t0 >= SPIN_TIME

    def done(self, now):
        return now - self.t0 >= SPIN_TIME + HOLD_TIME


# The slot machine by the table. Three reels, one payline, and the odds are
# in the weights: a 7 is rare, a cherry is not. Honest the same way the wheel
# is - the result is drawn first, the reels are then shown stopping on it.
SLOT_SYMBOLS = ["7", "$", "@", "*", "&", "%"]
SLOT_WEIGHTS = [1, 2, 3, 4, 5, 6]
SLOT_SPIN = 1.3        # seconds before the first reel stops
SLOT_STAGGER = 0.65    # and between one reel stopping and the next
SLOT_HOLD = 3.0        # how long the result stays up before it goes idle
SLOT_BETS = [1, 5, 10, 25]
# Three of a kind pays this many times the bet, by symbol; a pair gives the
# bet back. Worked out from SLOT_WEIGHTS it returns about 82 chips in 100 -
# the house wins slowly, which is what a slot machine is.
SLOT_PAYS = [100, 40, 20, 10, 6, 4]
SLOT_PAIR = 1
class Wallet:
    """Your money: one balance for the whole city. The slot and the table
    play out of it, the exchange trades with it, the arcade, the claw and
    the hammer take their dollar from it, and so do the films, the noodles,
    the coffee, the lifts and the fireworks. No house tops it up when it is
    gone - money that came back for nothing would not be money - but the
    menu can (`:`)."""

    def __init__(self, money=None):
        self.money = STARTING_MONEY if money is None else money

    def take(self, n):
        """Pay n, or False - and nothing taken - if you cannot."""
        if self.money + 1e-9 < n:
            return False
        self.money -= n
        return True

    def give(self, n):
        self.money += n


_rig_slot = False       # % in the menu: the next pull is 777, once


def rig_jackpot():
    """The one way to see a jackpot without nine thousand pulls - or, at the
    plinko machine, two thousand balls."""
    global _rig_slot, _rig_plinko, _rig_race
    _rig_slot = _rig_plinko = _rig_race = True


# The plinko machine: a ball dropped in at the top bounces left or right off
# every row of pegs, a fair coin each time, and lands in a bin. Most land in
# the middle, which pays least; the edges are a long way off and pay most.
PLINKO_ROWS = 12
PLINKO_PAYS = [120, 14, 3, 1.5, 1, 0.6, 0.3, 0.6, 1, 1.5, 3, 14, 120]   # ~94%
PLINKO_BETS = [1, 5, 10, 25, 100]
PLINKO_STEP = 0.16     # seconds a row
PLINKO_MAX = 6         # balls in the air at once
PLINKO_HOLD = 2.5      # how long a landed ball sits in its bin
_rig_plinko = False    # the menu's jackpot: the next ball goes all the way


class Plinko:
    """The machine. drop() pays the bet and lets a ball go, its bounces drawn
    there and then and the fall a timeline from them, so where() can say
    where it is at any moment; settle() pays each out once, as it lands."""

    def __init__(self, wallet=None):
        self.wallet = wallet if wallet is not None else Wallet()
        self.bet = PLINKO_BETS[1]
        self.balls = []
        self.last = None             # (bin, win, when) of the last to land
        self.short = False
        self.drops = 0

    def bet_up(self, step):
        k = PLINKO_BETS.index(self.bet) if self.bet in PLINKO_BETS else 1
        self.bet = PLINKO_BETS[max(0, min(len(PLINKO_BETS) - 1, k + step))]

    def drop(self, now):
        global _rig_plinko
        if sum(1 for b in self.balls if not b["paid"]) >= PLINKO_MAX:
            return False
        self.short = not self.wallet.take(self.bet)
        if self.short:
            return False
        if _rig_plinko:
            path, _rig_plinko = [_spin_rng.random() < 0.5] * PLINKO_ROWS, False
        else:
            path = [_spin_rng.random() < 0.5 for _ in range(PLINKO_ROWS)]
        self.balls.append({"t0": now, "path": path, "bet": self.bet, "paid": False})
        self.drops += 1
        return True

    @staticmethod
    def landed(ball, now):
        return now - ball["t0"] >= (PLINKO_ROWS + 1) * PLINKO_STEP

    @staticmethod
    def bin_of(ball):
        return sum(ball["path"])

    @staticmethod
    def where(ball, now):
        """(across, down): across in pegs from the middle, down in rows from
        the first peg - the ball sits on top of a peg at a whole row."""
        t = (now - ball["t0"]) / PLINKO_STEP
        r = int(min(PLINKO_ROWS, max(0.0, t)))
        f = min(1.0, max(0.0, t - r)) if r < PLINKO_ROWS else 0.0
        k = sum(ball["path"][:r])
        across = k - r / 2.0
        if r < PLINKO_ROWS:
            across += (0.5 if ball["path"][r] else -0.5) * f
        return across, r - 1 + f + (0.0 if f > 0.35 or r == 0 else -0.3 * (1 - f))

    def settle(self, now):
        """Pay out what has landed; returns the bins that landed just now."""
        hit = []
        for b in self.balls:
            if not b["paid"] and self.landed(b, now):
                b["paid"] = True
                k = self.bin_of(b)
                win = b["bet"] * PLINKO_PAYS[k]
                self.wallet.give(win)
                self.last = (k, win, now)
                hit.append(k)
        self.balls = [b for b in self.balls if not b["paid"]
                      or now - b["t0"] < (PLINKO_ROWS + 1) * PLINKO_STEP + PLINKO_HOLD]
        return hit


# The races: six horses round the track every RACE_CYCLE seconds. Each has a
# real chance of winning, drawn when the race is made up, and the odds on the
# board are that chance less the house's cut, rounded down onto the ladder
# a bookmaker uses - so the race is honest and the board is fair, and the
# house still wins slowly.
RACE_BET = 15.0        # seconds to get your bets on
RACE_RUN = 14.0        # the race
RACE_SHOW = 6.0        # the result, before the next card goes up
RACE_CYCLE = RACE_BET + RACE_RUN + RACE_SHOW
RACE_FIELD = 6
RACE_CUT = 0.98        # a fair price times this, rounded down onto the ladder:
                       # about 87% back, since the rounding takes its share
RACE_LADDER = [1, 2, 3, 4, 5, 6, 8, 10, 12, 16, 20, 25, 33, 50]
RACE_STAKES = [1, 5, 10, 25, 100]
RACE_NAMES = ["NEON DANCER", "LAST TRAIN", "RAIN CHECK", "MIDNIGHT OIL", "BACK ALLEY",
              "HIGH VOLTAGE", "SODIUM LAMP", "PAPER LANTERN", "SLOW BURN", "NIGHT BUS",
              "DOUBLE DOWN", "BLUE HOUR", "WET ASPHALT", "OPEN ALL HOURS",
              "FIRE ESCAPE",
              "STATIC", "ROOF PARTY", "STEAM VENT"]
HORSE = ("-/\\o>", "-\\/o>")   # galloping, the jockey in the silks colour
_rig_race = False      # the menu's jackpot: the longest shot wins the next one


class Races:
    """The track. update() puts up the next card when the last one is over,
    draws the finishing order at the off, and pays the winners once at the
    line; progress() is where a horse is, a timeline solved from the order
    so the one drawn to win does - with the lead changing on the way."""

    def __init__(self, wallet=None):
        self.wallet = wallet if wallet is not None else Wallet()
        self.stake = RACE_STAKES[1]
        self.race = None
        self.number = 0
        self.last = None             # (winner's name, odds, what you won)
        self.note = ""

    def stake_up(self, step):
        k = RACE_STAKES.index(self.stake) if self.stake in RACE_STAKES else 1
        self.stake = RACE_STAKES[max(0, min(len(RACE_STAKES) - 1, k + step))]

    def _card(self, t0):
        names = _spin_rng.sample(RACE_NAMES, RACE_FIELD)
        w = [_spin_rng.lognormvariate(0.0, 0.7) for _ in range(RACE_FIELD)]
        total = sum(w)
        horses = []
        for k in range(RACE_FIELD):
            q = w[k] / total
            fair = RACE_CUT / q - 1.0
            odds = max([o for o in RACE_LADDER if o <= fair] or [RACE_LADDER[0]])
            horses.append({"name": names[k], "q": q, "odds": odds,
                           "silk": NEON[(k * 3) % len(NEON)][0] if NEON else 0,
                           "phase": _spin_rng.random() * math.tau})
        self.number += 1
        self.race = {"t0": t0, "horses": horses, "order": None, "bets": {},
                     "paid": False, "n": self.number}

    def phase(self, now):
        dt = now - self.race["t0"]
        return ("bets" if dt < RACE_BET else "run" if dt < RACE_BET + RACE_RUN
                else "show" if dt < RACE_CYCLE else "next")

    def update(self, now):
        """Returns what this call paid out, so a long shot can light the place."""
        global _rig_race
        if self.race is None:
            self._card(now)
        elif self.phase(now) == "next":
            self._card(now)
        ph = self.phase(now)
        hs = self.race["horses"]
        if ph != "bets" and self.race["order"] is None:
            left = list(range(RACE_FIELD))
            order = []
            if _rig_race:
                _rig_race = False
                long_ = max(left, key=lambda k: hs[k]["odds"])
                order.append(long_)
                left.remove(long_)
            while left:                      # by their chances, one place at a time
                k = _spin_rng.choices(left, [hs[k]["q"] for k in left])[0]
                order.append(k)
                left.remove(k)
            self.race["order"] = order
        if ph == "show" and not self.race["paid"]:
            self.race["paid"] = True
            win = self.race["order"][0]
            got = self.race["bets"].get(win, 0) * (hs[win]["odds"] + 1)
            self.wallet.give(got)
            self.last = (hs[win]["name"], hs[win]["odds"], got)
            return got
        return 0

    def bet(self, k, now):
        if self.race is None or not 0 <= k < RACE_FIELD:
            return False
        if self.phase(now) != "bets":
            self.note = "bets are closed"
            return False
        if not self.wallet.take(self.stake):
            self.note = "not enough"
            return False
        self.race["bets"][k] = self.race["bets"].get(k, 0) + self.stake
        self.note = "$%d on %s" % (self.stake, self.race["horses"][k]["name"].lower())
        return True

    def progress(self, k, now):
        """How far round, 0 at the gate and 1 at the line."""
        if self.race["order"] is None:
            return 0.0
        u = (now - self.race["t0"] - RACE_BET) / RACE_RUN
        if u <= 0.0:
            return 0.0
        rank = self.race["order"].index(k)
        b = min(1.0, u / (0.86 + 0.025 * rank))
        if b >= 1.0:
            return 1.0
        h = self.race["horses"][k]
        wob = 0.05 * math.sin(math.pi * b) * math.sin(u * 4.5 + h["phase"])
        return min(0.999, max(0.0, b + wob))


def draw_races(ch, co, rc, x0, x1, y0, y1, now):
    """The board and the track between columns x0 and x1, rows y0 to y1: what
    race this is and how long to the off, a lane a horse - its number, name,
    odds and your money on it to the left, the horse galloping along the turf
    to the chequered line - what the commentator is saying, and how you did."""
    race = rc.race
    hs = race["horses"]
    ph = rc.phase(now)
    dt = now - race["t0"]
    head = ("RACE %d  -  BETS CLOSE IN %d" % (race["n"], int(RACE_BET - dt) + 1)
            if ph == "bets" else "RACE %d  -  AND THEY'RE OFF!" % race["n"]
            if ph == "run" else "RACE %d  -  RESULT" % race["n"])
    _text(ch, co, y0, int((x0 + x1 - len(head)) / 2), head,
          GOLD if ph != "bets" or int(now * 2) % 2 else GOLD_DIM)
    ts, te = x0 + 29, x1 - 2             # the turf, and the line at the end
    top = y0 + 2
    for x in range(ts - 1, te + 2):
        ch[top - 1][x], co[top - 1][x] = "=", CURB
        ch[top + RACE_FIELD][x], co[top + RACE_FIELD][x] = "=", CURB
    for k, h in enumerate(hs):
        y = top + k
        _text(ch, co, y, x0, "%d" % (k + 1), GOLD)
        _text(ch, co, y, x0 + 2, h["name"][:14], h["silk"])
        _text(ch, co, y, x0 + 17, "%d/1" % h["odds"], GOLD_DIM)
        mine = race["bets"].get(k, 0)
        if mine:
            _text(ch, co, y, x0 + 23, "$%d" % mine, GOLD)
        for x in range(ts, te):
            if (x + int(now * 12) * (ph == "run")) % 6 == 0:
                ch[y][x], co[y][x] = ".", GRASS
        ch[y][te], co[y][te] = ("#" if (y + int(now * 4)) % 2 else ":"), STAR
        f = rc.progress(k, now)
        if f >= 1.0:                     # past the post: where it came
            _text(ch, co, y, te + 1, "%d" % (race["order"].index(k) + 1),
                  GOLD if race["order"][0] == k else GOLD_DIM)
        hx = ts + int(round(f * (te - ts - len(HORSE[0]))))
        frame = HORSE[int(now * 10 + k) % 2] if ph == "run" and f < 1.0 else HORSE[0]
        win = ph == "show" and race["order"][0] == k
        for j, c in enumerate(frame):
            silk = FLASH if win and int(now * 6) % 2 else h["silk"]
            _text(ch, co, y, hx + j, c, silk if c == "o" else BARK)
    # The commentator.
    say = ""
    if ph == "bets":
        fav = min(range(RACE_FIELD), key=lambda k: hs[k]["odds"])
        say = "%s is the favourite at %d/1. 1-%d bets, +/- the stake ($%d)" % (
            hs[fav]["name"].title(), hs[fav]["odds"], RACE_FIELD, rc.stake)
    elif ph == "run":
        lead = max(range(RACE_FIELD), key=lambda k: rc.progress(k, now))
        u = (dt - RACE_BET) / RACE_RUN
        say = ("%s jumps out in front!" if u < 0.2 else "%s leads the field" if u < 0.6
               else "%s in front as they come into the straight!" if u < 0.85
               else "and it's %s at the line!") % hs[lead]["name"].title()
    else:
        name, odds, got = rc.last
        say = "WINNER: %s at %d/1  -  %s" % (name, odds, "you win $%d!" % got if got
                                             else "better luck next race")
    _text(ch, co, top + RACE_FIELD + 1, int((x0 + x1 - len(say)) / 2), say,
          GOLD if ph == "show" and rc.last[2] else HUD)
    if rc.note and y1 > top + RACE_FIELD + 2:
        _text(ch, co, top + RACE_FIELD + 2, int((x0 + x1 - len(rc.note)) / 2),
              rc.note, GOLD_DIM)


RACE_WIDE = 64         # columns the track needs
RACE_TALL = RACE_FIELD + 5


PLINKO_TALL = PLINKO_ROWS + 4    # rows the board needs, without its title
PLINKO_SX = 4          # columns between pegs: even, so a half step is a column,
                       # and wide enough for "120" under its bin
PLINKO_WIDE = (PLINKO_ROWS + 3) * PLINKO_SX + 2


def plinko_colour(k):
    edge = abs(k - PLINKO_ROWS // 2)
    return (GOLD if edge == 6 else ROU_RED if edge == 5 else EMBER_HOT if edge >= 3
            else CURB)


def draw_plinko(ch, co, pk, cx, y0, y1, now):
    """The board between rows y0 and y1, its middle at column cx: the slot at
    the top, the pegs in a triangle, the bins along the bottom with what each
    pays under it - lit hotter towards the edges - the balls on their way down,
    and the bet and the last win."""
    height, width = len(ch), len(ch[0])
    sx = PLINKO_SX
    title = y1 - y0 + 1 >= PLINKO_TALL + 1
    top = y0 + (1 if title else 0)
    peg0 = top + 1
    bins = peg0 + PLINKO_ROWS
    if title:
        _text(ch, co, y0, int(cx) - 5, "P L I N K O", GOLD)

    def col(across):
        return int(round(cx + across * sx))

    _text(ch, co, top, col(0) - 1, "\\v/", GOLD_DIM)
    for r in range(PLINKO_ROWS):
        for j in range(-1, r + 2):
            x = col(j - r / 2.0)
            if 0 <= x < width:
                ch[peg0 + r][x], co[peg0 + r][x] = ".", CURB
    mid = PLINKO_ROWS // 2
    fresh = pk.last is not None and now - pk.last[2] < PLINKO_HOLD
    for k in range(PLINKO_ROWS + 1):
        a = k - mid
        for side in (-0.5, 0.5):
            x = col(a + side)
            if 0 <= x < width:
                ch[bins][x], co[bins][x] = "|", GOLD_DIM
        label = "%g" % PLINKO_PAYS[k]
        attr = plinko_colour(k)
        if fresh and pk.last[0] == k and int(now * 8) % 2:
            attr = FLASH
        _text(ch, co, bins + 1, col(a) - (len(label) - 1) // 2, label, attr)
    for b in pk.balls:
        across, down = Plinko.where(b, now)
        x, y = col(across), peg0 + int(round(down))
        if Plinko.landed(b, now):
            y = bins
        if 0 <= x < width and 0 <= y < height:
            ch[y][x], co[y][x] = "O", FLASH
    if pk.short:
        say = "NOT ENOUGH"
    elif fresh:
        k, win, _ = pk.last
        say = "x%g  +$%s" % (PLINKO_PAYS[k], ("%.2f" % win).rstrip("0").rstrip("."))
    else:
        say = "p drops a ball"
    line = "BET $%d    %s    $%d" % (pk.bet, say, int(pk.wallet.money))
    _text(ch, co, bins + 2, int(cx - len(line) / 2), line,
          GOLD if fresh and abs(pk.last[0] - mid) >= 5 else GOLD_DIM)


class Slot:
    """One machine. pull() draws a result and starts the reels; reel_at()
    says what is showing in a reel this instant, and the payline is the
    middle row."""

    def __init__(self, wallet=None):
        self.t0 = None
        self.result = None
        self.pulls = 0
        self.wallet = wallet if wallet is not None else Wallet()
        self.bet = SLOT_BETS[1]
        self.won = 0             # what the last pull paid, once it settles
        self.paid = True
        self.short = False       # the last pull was refused: not enough chips

    def bet_up(self, step):
        k = SLOT_BETS.index(self.bet) if self.bet in SLOT_BETS else 1
        self.bet = SLOT_BETS[max(0, min(len(SLOT_BETS) - 1, k + step))]

    def pull(self, now):
        """Pay the bet and spin; refused, and it says so, if you cannot
        cover it."""
        self.short = not self.wallet.take(self.bet)
        if self.short:
            return False
        global _rig_slot
        if _rig_slot:
            picks, _rig_slot = [0, 0, 0], False     # the menu asked for 777
        else:
            picks = _spin_rng.choices(range(len(SLOT_SYMBOLS)), SLOT_WEIGHTS, k=3)
        self.result = picks
        self.t0 = now
        self.pulls += 1
        self.won = 0
        self.paid = False
        return True

    def settle(self, now):
        """Pay out once, when the last reel stops."""
        if self.paid or not self.settled(now):
            return
        a, b, c = self.result
        if a == b == c:
            self.won = self.bet * SLOT_PAYS[a]
        elif a == b or b == c or a == c:
            self.won = self.bet * SLOT_PAIR
        self.wallet.give(self.won)
        self.paid = True

    def stop_at(self, k):
        return SLOT_SPIN + k * SLOT_STAGGER

    def stopped(self, k, now):
        return self.t0 is not None and now - self.t0 >= self.stop_at(k)

    def settled(self, now):
        return self.stopped(2, now)

    def idle(self, now):
        return self.t0 is None or now - self.t0 >= self.stop_at(2) + SLOT_HOLD

    def reel_at(self, k, now):
        """The three symbols showing in reel k, top to bottom."""
        if self.t0 is None:
            base = int(now * 0.7) + k * 2          # the attract crawl, idle
        elif self.stopped(k, now):
            base = self.result[k] - 1
        else:
            base = int((now - self.t0) * (14.0 + k * 3)) + k * 5
        n = len(SLOT_SYMBOLS)
        return [SLOT_SYMBOLS[(base + r) % n] for r in range(3)]

    def payout(self, now):
        """What the payline says once it has stopped, or None."""
        if not self.settled(now):
            return None
        a, b, c = self.result
        if a == b == c:
            return "JACKPOT" if a == 0 else "THREE OF A KIND"
        if a == b or b == c or a == c:
            return "PAIR"
        return "NO LUCK"


SLOT_W = 19             # the cabinet's width, in columns
SLOT_H = 12             # and its height, without the pay table under it


def draw_slot(ch, co, slot, x0, y0, now, paytable=True):
    """The cabinet: reels in the middle with the payline marked, the verdict
    under them, and the chips, the bet and the last win on the panel below.
    The pay table goes under the cabinet when there is room for it."""
    w = SLOT_W
    bar = "|" + "=" * (w - 2) + "|"
    _text(ch, co, y0, x0, "." + "-" * (w - 2) + ".", GOLD_DIM)
    _text(ch, co, y0 + 1, x0, "|" + "L U C K Y  7".center(w - 2) + "|", GOLD)
    _text(ch, co, y0 + 2, x0, bar, GOLD_DIM)
    reels = [slot.reel_at(k, now) for k in range(3)]
    for r in range(3):
        row = " ".join("[%s]" % reels[k][r] for k in range(3))
        pay = r == 1
        y = y0 + 3 + r
        _text(ch, co, y, x0, ">" if pay else "|", GOLD if pay else GOLD_DIM)
        _text(ch, co, y, x0 + (w - len(row)) // 2, row,
              ROU_RED if pay else CONCRETE)
        _text(ch, co, y, x0 + w - 1, "<" if pay else "|", GOLD if pay else GOLD_DIM)
    _text(ch, co, y0 + 6, x0, bar, GOLD_DIM)
    verdict = slot.payout(now)
    if slot.short:
        say, attr = "NOT ENOUGH", ROU_RED
    elif verdict is not None:
        win = slot.won > slot.bet
        say = ("WIN %d" % slot.won) if win else verdict
        attr = (FLASH if int(now * 6) % 2 == 0 else GOLD) if win else GOLD_DIM
    elif slot.t0 is not None:
        say, attr = "* spinning *", GOLD_DIM
    else:
        say, attr = "p to pull", GOLD_DIM
    _text(ch, co, y0 + 7, x0, "|" + say[:w - 2].center(w - 2) + "|", attr)
    _text(ch, co, y0 + 8, x0, bar, GOLD_DIM)
    _text(ch, co, y0 + 9, x0,
          "|" + ("$%d" % slot.wallet.money).center(w - 2) + "|", GOLD)
    _text(ch, co, y0 + 10, x0,
          "|" + ("bet %-3d  - +" % slot.bet).center(w - 2) + "|", GOLD_DIM)
    _text(ch, co, y0 + 11, x0, "'" + "-" * (w - 2) + "'", GOLD_DIM)
    if paytable:
        lines = ["%s%s%s  x%d" % (s, s, s, p)
                 for s, p in zip(SLOT_SYMBOLS, SLOT_PAYS)]
        lines.append("any pair  bet back")
        for k, line in enumerate(lines):
            _text(ch, co, y0 + 13 + k, x0 + 1, line, GOLD_DIM)


# The blackjack table, on the other side of the room. One deck, dealer
# stands on 17, blackjack pays three to two. The dealer takes a card every
# BJ_DEAL seconds rather than all at once, because a hand that resolves in
# one frame is a number, not a game.
BJ_BET = 10
BJ_DEAL = 0.8
SUITS = "^v*o"          # spades, hearts, clubs, diamonds
RANKS = ["A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K"]


def hand_value(cards):
    """Best total, aces counting eleven where that does not bust."""
    total = sum(11 if r == "A" else 10 if r in "JQK" else int(r) for r, _ in cards)
    aces = sum(1 for r, _ in cards if r == "A")
    while total > 21 and aces:
        total -= 10
        aces -= 1
    return total


class Blackjack:
    def __init__(self, wallet=None):
        self.wallet = wallet if wallet is not None else Wallet()
        self.shoe = []
        self.player = []
        self.dealer = []
        self.phase = "idle"         # idle, player, dealer, done
        self.outcome = ""
        self.t_phase = 0.0

    def _draw(self):
        if len(self.shoe) < 15:
            self.shoe = [(r, s) for r in RANKS for s in SUITS]
            _spin_rng.shuffle(self.shoe)
        return self.shoe.pop()

    @property
    def money(self):
        return self.wallet.money

    @money.setter
    def money(self, n):
        self.wallet.money = n

    def deal(self, now):
        if self.phase in ("player", "dealer"):
            return
        if not self.wallet.take(BJ_BET):
            self.outcome = "NOT ENOUGH"
            return
        self.wallet.give(BJ_BET)         # only checking: it is settled at the end
        self.player = [self._draw(), self._draw()]
        self.dealer = [self._draw(), self._draw()]
        self.phase = "player"
        self.outcome = ""
        self.t_phase = now
        if hand_value(self.player) == 21:
            self._finish(now)

    def hit(self, now):
        if self.phase != "player":
            return
        self.player.append(self._draw())
        if hand_value(self.player) > 21:
            self._finish(now)

    def stand(self, now):
        if self.phase != "player":
            return
        self.phase = "dealer"
        self.t_phase = now

    def update(self, now):
        """The dealer's turn, a card at a time."""
        if self.phase != "dealer":
            return
        if hand_value(self.dealer) >= 17:
            self._finish(now)
        elif now - self.t_phase >= BJ_DEAL - 1e-6:
            self.dealer.append(self._draw())
            self.t_phase = now

    def _finish(self, now):
        p, d = hand_value(self.player), hand_value(self.dealer)
        natural = len(self.player) == 2 and p == 21
        if p > 21:
            self.outcome, win = "BUST", -BJ_BET
        elif natural and not (len(self.dealer) == 2 and d == 21):
            self.outcome, win = "BLACKJACK", BJ_BET * 3 // 2
        elif d > 21:
            self.outcome, win = "DEALER BUSTS", BJ_BET
        elif p > d:
            self.outcome, win = "YOU WIN", BJ_BET
        elif p < d:
            self.outcome, win = "DEALER WINS", -BJ_BET
        else:
            self.outcome, win = "PUSH", 0
        self.money += win
        self.phase = "done"
        self.t_phase = now


def _card(ch, co, y, x, card, hidden=False):
    if hidden:
        art, attr = (".---.", "|:::|", "'---'"), CONCRETE
    else:
        r, s = card
        face = (r + s).ljust(3) if len(r) == 1 else r + s
        art = (".---.", "|" + face + "|", "'---'")
        attr = ROU_RED if s in "vo" else ROU_BLACK
    for k, line in enumerate(art):
        _text(ch, co, y + k, x, line, attr)


def draw_blackjack(ch, co, bj, x0, y0, now):
    """The table: 40 columns by 13 rows. The dealer's second card stays face
    down until you stand."""
    w = 40
    _text(ch, co, y0, x0, "." + "-" * (w - 2) + ".", GOLD_DIM)
    for r in range(1, 12):
        _text(ch, co, y0 + r, x0, "|", GOLD_DIM)
        _text(ch, co, y0 + r, x0 + w - 1, "|", GOLD_DIM)
    _text(ch, co, y0 + 12, x0, "'" + "-" * (w - 2) + "'", GOLD_DIM)
    _text(ch, co, y0 + 1, x0 + 2, "BLACKJACK", GOLD)
    _text(ch, co, y0 + 1, x0 + w - 13, "$%-8d" % bj.money, GOLD)
    showing = bj.phase in ("dealer", "done")
    for row, (who, cards) in enumerate((("dealer", bj.dealer), ("you", bj.player))):
        y = y0 + 2 + row * 4
        _text(ch, co, y, x0 + 2, who, GOLD_DIM)
        if cards:
            seen = cards if (showing or who == "you") else cards[:1]
            _text(ch, co, y, x0 + w - 7, "(%2d)" % hand_value(seen), GOLD_DIM)
        for k, card in enumerate(cards[:6]):
            _card(ch, co, y + 1, x0 + 2 + k * 6, card,
                  hidden=(who == "dealer" and k == 1 and not showing))
    if bj.phase == "player":
        keys = "h hit   k stand"
    elif bj.phase == "dealer":
        keys = "dealer's turn"
    else:
        keys = "b deals a hand"
    _text(ch, co, y0 + 10, x0 + 2, keys, GOLD_DIM)
    if bj.outcome:
        win = bj.outcome in ("BLACKJACK", "YOU WIN", "DEALER BUSTS")
        flash = win and int(now * 6) % 2 == 0
        _text(ch, co, y0 + 11, x0 + (w - len(bj.outcome)) // 2, bj.outcome,
              FLASH if flash else GOLD if win else ROU_RED)


RAMEN_ODDS = 3         # one yokocho counter in this many is a ramen shop
RAMEN_SERVE = 4.5      # seconds from sitting down to the bowl in front of you
RAMEN_MENU = [("SHOYU", 850), ("MISO", 900), ("SHIO", 850),
              ("TONKOTSU", 980), ("TANTANMEN", 1050), ("GYOZA", 450)]


def ramen_at(i, j, f):
    """Is the place behind this face a ramen counter.

    A yokocho pub, one in RAMEN_ODDS, by a hash of the face - the hash first,
    because it is the cheap test and the lot is not."""
    if _mix(i, j * 4 + f, 1601) % RAMEN_ODDS:
        return False
    nx, nz = FACES[f]
    if not is_open(i + nx, j + nz) or face_kind(i + nx, j + nz) != "yokocho":
        return False
    return lot(i, j)["faces"][f]["pub"]


def ramen_door(i, j, f):
    """Where you stand to be at the counter: just out from the middle of it."""
    p = face_point(i, j, f, CELL * 0.5, 1.4, 0.0)
    return p[0], p[2]


def venue_at(x, z):
    """The club, casino or ramen counter you are standing in the doorway of,
    as (kind, dict), or None.

    These two are the only way into a building in the city. Both are a trigger
    at the door rather than somewhere you walk around inside, because a
    five-metre cell has no inside to walk around in - what you get instead is a
    room drawn around you."""
    ci = int(x / CELL + BIG) - BIG
    cj = int(z / CELL + BIG) - BIG
    c = carnival_over(ci)
    if c is not None:                           # the claw machine, on the fair
        bx, bz = claw_spot(c)
        if (bx - x) ** 2 + (bz - z) ** 2 < CASINO_REACH ** 2:
            return "claw", {"col": c}
        bx, bz = striker_spot(c)                # and the strength tester
        if (bx - x) ** 2 + (bz - z) ** 2 < CASINO_REACH ** 2:
            return "striker", {"col": c}
    for i in range(ci - 2, ci + 3):
        for j in range(cj - 2, cj + 3):
            if is_open(i, j):
                continue
            b = lot(i, j)
            for kind in ("casino", "club", "tower", "cinema", "diner", "arcade",
                         "temple", "exchange"):
                v = b[kind]
                if v is None:
                    continue
                nx, nz = FACES[v["door"]]
                if not is_open(i + nx, j + nz):
                    continue
                p = face_point(i, j, v["door"], v["u"], 1.4, 0.0)
                if ((p[0] - x) ** 2 + (p[2] - z) ** 2) < CASINO_REACH ** 2:
                    return kind, v
            for f in range(4):
                if not ramen_at(i, j, f):
                    continue
                dx, dz = ramen_door(i, j, f)
                if (dx - x) ** 2 + (dz - z) ** 2 < CASINO_REACH ** 2:
                    return "ramen", {"seed": _mix(i, j * 4 + f, 1603),
                                     "tone": b["tone"]}
    return None


def casino_at(x, z):
    got = venue_at(x, z)
    return got[1] if got is not None and got[0] == "casino" else None


def _text(ch, co, y, x, s, attr):
    for k, c in enumerate(s):
        if 0 <= y < len(ch) and 0 <= x + k < len(ch[0]) and c != " ":
            ch[y][x + k] = c
            co[y][x + k] = attr


def _big(ch, co, y, x, s, attr):
    """The winning number, twice as wide as the little font so it reads square."""
    for row in range(5):
        col = x
        for c in s:
            for px in DIGITS.get(c, ("   ",) * 5)[row]:
                if px != " ":
                    for d in (0, 1):
                        if 0 <= y + row < len(ch) and 0 <= col + d < len(ch[0]):
                            ch[y + row][col + d] = "#"
                            co[y + row][col + d] = attr
                col += 2
            col += 2


def render_casino_room(spin, width, height, now, slot=None, table=None, party=False,
                       plinko=None, races=None):
    """Inside.

    The wheel is the middle of a room rather than the whole screen: a ceiling
    with the lights chasing along it, a back wall of slot machines with their
    reels going, the table with people round it, and the way out behind you. A
    window with no space for the room gets the wheel on its own, and one with
    no space for that gets a line of text."""
    ch = [[" "] * width for _ in range(height)]
    co = [[0] * width for _ in range(height)]
    t = now - spin.t0
    cx = (width - 1) / 2.0
    top, floor = 1, height - 1
    roomy = width >= 46 and height >= 22

    if roomy:
        for x in range(width):                       # the ceiling, in lights
            lit = chase(x * 0.2, now) or party
            ch[top][x] = "o" if lit else "="
            co[top][x] = ((FLASH if int(now * 8 + x) % 2 else GOLD) if party
                          else GOLD if lit else GOLD_DIM)
        banner = "CASINO  %s" % spin.name
        _text(ch, co, top + 1, int(cx - len(banner) / 2), banner, GOLD)
        for x in range(2, width - 6, 9):             # a back wall of slots
            if abs(x + 2 - cx) < len(banner) / 2 + 3:
                continue
            reel = "".join("7$@&%"[(_mix(x, k, 53) + int(now * (3 + k))) % 5]
                           for k in range(2))
            _text(ch, co, top + 2, x, ".--.", GOLD_DIM)
            _text(ch, co, top + 3, x, "|" + reel + "|", ROU_RED)
        band_top, band_bot = top + 5, floor - 5
    else:
        band_top, band_bot = top, floor - 1

    cy = (band_top + band_bot) / 2.0
    rx = min(width * 0.36, 42.0)
    ry = min((band_bot - band_top) / 2.0 - 0.5, 10.0)
    # The slot machine stands to the right of the wheel and the blackjack
    # table to its left when there is room for them; the wheel moves over
    # and gives up some radius so that all three fit.
    # With the plinko machine up (`plinko`), it takes the wheel's place and
    # the slot machine stands aside for it.
    machine = (slot is not None and plinko is None and races is None and width >= 62
               and height >= SLOT_H + 3)
    cards = (roomy and table is not None and races is None
             and width >= (92 if plinko is None else 108))
    left = 43.0 if cards else 1.0
    right = width - SLOT_W - 3.0 if machine else width - 2.0
    if machine or cards:
        cx = (left + right) / 2.0
        rx = min(rx, (right - left) / 2.0 - 1.0)
    if machine:
        sy = band_top + 1 if roomy else 1
        draw_slot(ch, co, slot, width - SLOT_W - 1, sy, now,
                  paytable=sy + SLOT_H + 8 < height)
    if cards:
        draw_blackjack(ch, co, table, 1, band_top + 1, now)

    if races is not None:
        y1 = floor - 2
        y0 = band_top if roomy else top
        if y1 - y0 + 1 < RACE_TALL or right - left < RACE_WIDE:
            race = races.race
            ph = races.phase(now)
            _text(ch, co, height // 2, 1, "RACE %d: %s" % (race["n"], (
                "bets open" if ph == "bets" else "running" if ph == "run"
                else "won by " + races.last[0].lower())), GOLD)
            _text(ch, co, min(height - 1, height // 2 + 1), 1,
                  "1-%d bets, stake $%d" % (RACE_FIELD, races.stake), GOLD_DIM)
        else:
            y0 += max(0, (y1 - y0 - RACE_TALL) // 2)
            draw_races(ch, co, races, int(left) + 1, int(right), y0, y1, now)
        _text(ch, co, floor, max(1, int(cx) - 10), "-- the way out (s) --", GOLD_DIM)
        return ch, co

    if plinko is not None:
        y1 = floor - 2
        y0 = band_top if roomy else top
        if y1 - y0 + 1 < PLINKO_TALL or right - left < PLINKO_WIDE:
            last = plinko.last
            _text(ch, co, height // 2, 1, "PLINKO: " + (
                "x%g" % PLINKO_PAYS[last[0]] if last else "p drops a ball"), GOLD)
            _text(ch, co, min(height - 1, height // 2 + 1), 1, "bet $%d" % plinko.bet,
                  GOLD_DIM)
        else:
            y0 += max(0, (y1 - y0 - PLINKO_TALL) // 2)     # in the middle
            draw_plinko(ch, co, plinko, cx, y0, y1, now)
        _text(ch, co, floor, max(1, int(cx) - 10), "-- the way out (s) --", GOLD_DIM)
        return ch, co

    if rx < 12 or ry < 3.5:
        say = ("%s: %d" % (spin.name, spin.result) if spin.settled(now)
               else "%s: ..." % spin.name)
        _text(ch, co, height // 2, 1, say,
              pocket_colour(spin.result) if spin.settled(now) else GOLD)
        _text(ch, co, min(height - 1, height // 2 + 2), 1, "s to leave", GOLD_DIM)
        return ch, co

    wa = spin.wheel_at(t)
    for k, num in enumerate(WHEEL):
        a = wa + k * math.tau / 37.0
        label = str(num)
        x = int(round(cx + rx * math.cos(a))) - (len(label) - 1) // 2
        y = int(round(cy - ry * math.sin(a)))
        attr = pocket_colour(num)
        if spin.settled(now) and num == spin.result:
            attr = attr | curses.A_REVERSE
        _text(ch, co, y, x, label, attr)

    # The ball rides inside the numbers, and drops into the pocket at the end.
    ba = spin.ball_at(t)
    br = 0.72 if t < SPIN_TIME else 0.86
    bx = int(round(cx + rx * br * math.cos(ba)))
    by = int(round(cy - ry * br * math.sin(ba)))
    if 0 <= by < height and 0 <= bx < width:
        ch[by][bx] = "O" if spin.settled(now) else "o"
        co[by][bx] = FLASH

    mid = int(cy)
    if spin.settled(now):
        label = str(spin.result)
        w = len(label) * 8 - 2
        _big(ch, co, mid - 2, int(cx - w / 2), label, pocket_colour(spin.result))
        word = "ZERO" if spin.result == 0 else (
            "RED" if spin.result in REDS else "BLACK")
        if spin.result:
            word += "  %s  %s" % ("EVEN" if spin.result % 2 == 0 else "ODD",
                                  "1-18" if spin.result <= 18 else "19-36")
        _text(ch, co, mid + 4, int(cx - len(word) / 2), word,
              pocket_colour(spin.result))
    else:
        say = "RIEN NE VA PLUS" if t > SPIN_TIME * 0.45 else "FAITES VOS JEUX"
        _text(ch, co, mid, int(cx - len(say) / 2), say, GOLD_DIM)

    if roomy:
        edge = min(height - 4, int(cy + ry) + 2)     # the near lip of the table
        for x in range(max(0, int(cx - rx - 4)), min(width, int(cx + rx + 5))):
            ch[edge][x] = "="
            co[edge][x] = GOLD_DIM
        for k in range(-2, 3):                       # and who is round it
            px = int(cx + k * 15) - 2
            for r, line in enumerate((" ,-. ", "(- -)", "_/|\\_")):
                if edge + 1 + r < height:
                    _text(ch, co, edge + 1 + r, px, line, CURB)

    _text(ch, co, floor, max(1, int(cx) - 10), "-- the way out (s) --", GOLD_DIM)
    return ch, co


# The claw machine at the carnival. A front view through the glass: the
# rail across the top with the claw hanging off it, a heap of prizes, and the
# chute in the corner they come out of. What is in the heap is seeded from
# the carnival, so each one has its own; what you win you carry about.
CLAW_PRIZES = [
    ("cat", "^.^", "(_)"),
    ("bear", "o.o", "(Y)"),
    ("frog", "@-@", "(_)"),
    ("duck", "(o>", "/_)"),
    ("octopus", "(o)", "/|\\"),
    ("owl", "OvO", "(_)"),
]
CLAW_W = 29             # the cabinet's width, in columns
CLAW_H = CLAW_GLASS + 7  # and its height
CLAW_HOME = 2           # the column over the chute, where the claw waits
CLAW_FAR = CLAW_W - 4   # the furthest it goes
CLAW_REST = 3           # the row its fingers hang at, up on the rail
# The heap: (row up from the floor, first column), each prize three wide and
# two tall, every row sitting in the gaps of the one under it.
CLAW_PILE = ([(0, 7 + 4 * k) for k in range(5)] + [(1, 9 + 4 * k) for k in range(4)]
             + [(2, 11 + 4 * k) for k in range(3)])


class Claw:
    """One machine. press() puts a coin in, and pressed again drops the claw.

    The outcome is drawn the moment it drops and the rest is a timeline
    worked out from it, so claw_at() and moving() can say where everything is
    at any instant without anything being stepped frame by frame."""

    def __init__(self, col, arms=None, wallet=None):
        self.col = col
        self.arms = arms if arms is not None else []   # what you have won
        self.wallet = wallet if wallet is not None else Wallet()
        self.short = False       # the last go was refused: no money
        self.stocked = 0
        self.restock()
        self.t0 = None           # when the coin went in
        self.drop = None         # the plan, once the claw has been let go
        self.goes = 0

    def restock(self):
        seed = _mix(self.col, self.stocked, 1311)
        self.pile = []
        for n, (row, pos) in enumerate(CLAW_PILE):
            m = _mix(seed, n, 1313)
            self.pile.append({"row": row, "pos": pos, "gone": False,
                              "kind": m % len(CLAW_PRIZES), "colour": (m >> 8) % 8})
        self.stocked += 1

    def top(self, p):
        return CLAW_GLASS - 2 * (p["row"] + 1)

    def aiming(self, now):
        return self.t0 is not None and self.drop is None

    def idle(self, now):
        return self.t0 is None or (self.drop is not None
                                   and now - self.drop["t"] >= self.drop["done"])

    def press(self, now):
        if self.aiming(now):
            self.let_go(now)
        elif self.idle(now):
            self.short = not self.wallet.take(CLAW_COST)
            if self.short:
                return
            if all(p["gone"] for p in self.pile):
                self.restock()
            self.t0, self.drop = now, None
            self.goes += 1

    def sweep_x(self, now):
        """Across and back, and across again, while you make up your mind."""
        span = CLAW_FAR - CLAW_HOME
        d = (now - self.t0) * CLAW_SWEEP % (2 * span)
        return CLAW_HOME + (d if d <= span else 2 * span - d)

    def contact(self, x):
        """The prize the fingers come down on at column x: the highest one
        under them, and of those the one nearest square."""
        best = None
        for k, p in enumerate(self.pile):
            if p["gone"] or p["pos"] > x + 1 or p["pos"] + 2 < x - 1:
                continue
            key = (-p["row"], abs(p["pos"] + 1 - x))
            if best is None or key < best[0]:
                best = (key, k)
        return None if best is None else best[1]

    def covered(self, k):
        p = self.pile[k]
        return any(not q["gone"] and q["row"] == p["row"] + 1
                   and abs(q["pos"] - p["pos"]) <= 2 for q in self.pile)

    def let_go(self, now):
        x = int(round(self.sweep_x(now)))
        k = self.contact(x)
        slip = 0.0
        if k is None:
            depth, out = CLAW_GLASS - 1, "miss"
        else:
            depth = self.top(self.pile[k]) - 1
            off = abs(self.pile[k]["pos"] + 1 - x)
            if self.covered(k):
                out = "stuck"
            elif off >= len(CLAW_GRIP):
                out = "miss"             # the fingers only brushed it
            elif _spin_rng.random() < CLAW_GRIP[off]:
                out = "won"
            else:
                out, slip = "slip", _spin_rng.uniform(0.25, 0.9)
        travel = (depth - CLAW_REST) / CLAW_DROP
        d = {"t": now, "x": x, "k": k, "out": out, "depth": depth, "paid": False}
        d["down"] = travel
        d["shut"] = travel + CLAW_SHUT
        d["up"] = d["shut"] + travel
        d["slip"] = d["shut"] + travel * slip
        d["home"] = d["up"] + abs(x - CLAW_HOME) / CLAW_MOVE
        d["open"] = d["home"] + CLAW_SHUT
        d["landed"] = d["open"] + (CLAW_GLASS - CLAW_REST - 1) / CLAW_FALL
        if out == "slip":
            fell = depth - (depth - CLAW_REST) * slip
            d["landed"] = d["slip"] + (depth - fell) / CLAW_FALL
        reveal = {"won": d["landed"], "slip": d["slip"]}.get(out, d["shut"])
        d["reveal"] = reveal
        d["done"] = max(d["open"], reveal) + CLAW_HOLD
        self.drop = d

    def update(self, now):
        """Drop it if you ran out of time; hand the prize over once it is
        out of the chute."""
        if self.aiming(now) and now - self.t0 >= CLAW_TIME:
            self.let_go(self.t0 + CLAW_TIME)
        d = self.drop
        if (d is not None and d["out"] == "won" and not d["paid"]
                and now - d["t"] >= d["landed"]):
            p = self.pile[d["k"]]
            p["gone"] = True
            self.arms.append((p["kind"], p["colour"]))
            d["paid"] = True

    def claw_at(self, now):
        """(column, row of the fingers, shut) this instant."""
        if self.t0 is None or self.idle(now):
            return CLAW_HOME, CLAW_REST, False
        if self.drop is None:
            return int(round(self.sweep_x(now))), CLAW_REST, False
        d = self.drop
        t = now - d["t"]
        reach = d["depth"] - CLAW_REST
        if t < d["down"]:
            return d["x"], int(CLAW_REST + reach * t / d["down"]), False
        if t < d["shut"]:
            return d["x"], d["depth"], True
        if t < d["up"]:
            return d["x"], int(round(d["depth"] - reach * (t - d["shut"])
                                     / max(1e-6, d["up"] - d["shut"]))), True
        if t < d["home"]:
            k = (t - d["up"]) / max(1e-6, d["home"] - d["up"])
            return int(round(d["x"] + (CLAW_HOME - d["x"]) * k)), CLAW_REST, True
        return CLAW_HOME, CLAW_REST, t < d["open"]

    def moving(self, now):
        """The prize off the heap this instant, as (index, first column, top
        row), or None. Carried, it hangs under the fingers; let go, it falls -
        back onto the heap, or down the chute and out."""
        d = self.drop
        if d is None or d["out"] not in ("won", "slip") or d["paid"]:
            return None
        t = now - d["t"]
        if t < d["shut"] or t >= d["landed"]:
            return None
        p = self.pile[d["k"]]
        x, fy, _ = self.claw_at(now)
        if d["out"] == "won":
            if t < d["open"]:
                return d["k"], x - 1, fy + 1
            return d["k"], CLAW_HOME - 1, int(CLAW_REST + 1
                                              + (t - d["open"]) * CLAW_FALL)
        if t < d["slip"]:
            return d["k"], x - 1, fy + 1
        fell = d["depth"] - (d["depth"] - CLAW_REST) * (
            (d["slip"] - d["shut"]) / max(1e-6, d["up"] - d["shut"]))
        return d["k"], p["pos"], min(self.top(p),
                                     int(fell + 1 + (t - d["slip"]) * CLAW_FALL))

    def verdict(self, now):
        """What the panel says, and whether it is a win."""
        if self.aiming(now):
            return "p to drop  %d" % math.ceil(CLAW_TIME - (now - self.t0)), False
        d = self.drop
        if d is None or self.idle(now):
            return ("$%d A GO" % CLAW_COST if self.short else "p to play"), False
        if now - d["t"] < d["reveal"]:
            return "...", False
        if d["out"] == "won":
            return "WON A %s!" % CLAW_PRIZES[self.pile[d["k"]]["kind"]][0].upper(), True
        say = {"slip": "SO CLOSE", "stuck": "STUCK FAST"}.get(d["out"], "MISSED")
        return say, False


def draw_claw(ch, co, claw, x0, y0, now):
    """The cabinet: a sign in bulbs, the glass with the rail, the claw, the
    heap and the chute, and under it the flap the prize comes out of, the
    verdict, and how you are doing."""
    w, gw = CLAW_W, CLAW_W - 2
    gy = y0 + 3                                      # the first row of glass
    _text(ch, co, y0, x0, "." + "-" * gw + ".", GOLD_DIM)
    name = "GRAB-A-PAL"
    lo = (w - len(name)) // 2
    for x in range(1, w - 1):
        if lo <= x < lo + len(name):
            _text(ch, co, y0 + 1, x0 + x, name[x - lo], GOLD)
        elif x % 2 and not lo - 2 < x < lo + len(name) + 1:
            lit = chase(x * 0.3, now)
            _text(ch, co, y0 + 1, x0 + x, "o" if lit else ".",
                  GOLD if lit else GOLD_DIM)
    for y in (y0 + 1, y0 + 2):
        _text(ch, co, y, x0, "|", GOLD_DIM)
        _text(ch, co, y, x0 + w - 1, "|", GOLD_DIM)
    _text(ch, co, y0 + 2, x0 + 1, "=" * gw, GOLD_DIM)
    for r in range(CLAW_GLASS):
        _text(ch, co, gy + r, x0, "|", GOLD_DIM)
        _text(ch, co, gy + r, x0 + w - 1, "|", GOLD_DIM)
    _text(ch, co, gy, x0 + 1, "-" * gw, CONCRETE)        # the rail
    for r in range(CLAW_GLASS - 4, CLAW_GLASS):          # the chute's wall
        _text(ch, co, gy + r, x0 + 1 + CLAW_HOME + 3, "|", CONCRETE)

    moving = claw.moving(now)
    for k, p in enumerate(claw.pile):
        if p["gone"] or (moving is not None and moving[0] == k):
            continue
        _, head, body = CLAW_PRIZES[p["kind"]]
        colour = NEON[p["colour"] % len(NEON)][0]
        _text(ch, co, gy + claw.top(p), x0 + 1 + p["pos"], head, colour)
        _text(ch, co, gy + claw.top(p) + 1, x0 + 1 + p["pos"], body, colour)
    if moving is not None:
        k, px, py = moving
        p = claw.pile[k]
        colour = NEON[p["colour"] % len(NEON)][0]
        for r, line in enumerate(CLAW_PRIZES[p["kind"]][1:]):
            if py + r < CLAW_GLASS:
                _text(ch, co, gy + py + r, x0 + 1 + px, line, colour)

    x, fy, shut = claw.claw_at(now)
    cx = x0 + 1 + x
    _text(ch, co, gy, cx - 1, "[#]", GOLD_DIM)
    for r in range(1, fy - 1):
        _text(ch, co, gy + r, cx, "|", CONCRETE)
    _text(ch, co, gy + fy - 1, cx - 1, "-o-", CONCRETE)
    _text(ch, co, gy + fy, cx - 1, "\\_/" if shut else "/ \\", CONCRETE)

    base = gy + CLAW_GLASS
    _text(ch, co, base, x0, "|\\   /" + "=" * (gw - 5) + "|", GOLD_DIM)
    say, won = claw.verdict(now)
    attr = (FLASH if int(now * 6) % 2 == 0 else GOLD) if won else GOLD_DIM
    _text(ch, co, base + 1, x0, "|[   ]", GOLD_DIM)
    _text(ch, co, base + 1, x0 + w - 1, "|", GOLD_DIM)
    _text(ch, co, base + 1, x0 + 7, say[:gw - 7].center(gw - 7), attr)
    if won:                                          # out of the flap
        kind, colour = claw.arms[-1] if claw.arms else (0, 0)
        _text(ch, co, base + 1, x0 + 2, CLAW_PRIZES[kind][1],
              NEON[colour % len(NEON)][0])
    _text(ch, co, base + 2, x0, "|" + ("goes %d   won %d" % (
        claw.goes, len(claw.arms))).center(gw) + "|", GOLD)
    _text(ch, co, base + 3, x0, "'" + "-" * gw + "'", GOLD_DIM)


class Striker:
    """One strength tester. The meter beside the post swings for ever; p
    swings the hammer, which takes whatever the meter says that instant as
    the power, and the puck goes up that far and comes down. All of it is
    worked out at the swing, so the puck's height is a function of the time
    since, like the claw."""

    def __init__(self, col, arms=None, wallet=None):
        self.col = col
        self.arms = arms if arms is not None else []
        self.wallet = wallet if wallet is not None else Wallet()
        self.short = False
        self.hit = None              # (when, power)
        self.goes = self.rings = 0
        self.paid = True

    def meter(self, now):
        return 0.5 - 0.5 * math.cos(now * STRIKE_SWING)

    def ready(self, now):
        return self.hit is None or now - self.hit[0] >= 2 * STRIKE_UP + STRIKE_HOLD

    def swing(self, now):
        if not self.ready(now):
            return False
        self.short = not self.wallet.take(STRIKE_COST)
        if self.short:
            return False
        self.hit = (now, self.meter(now))
        self.goes += 1
        self.paid = False
        return True

    def puck(self, now):
        """How far up the post the puck is, 0..1."""
        if self.hit is None:
            return 0.0
        t = now - self.hit[0]
        top = self.hit[1]
        if t < STRIKE_UP:
            k = t / STRIKE_UP
            return top * (1.0 - (1.0 - k) ** 2)
        if t < 2 * STRIKE_UP:
            k = (t - STRIKE_UP) / STRIKE_UP
            return top * (1.0 - k * k)
        return 0.0

    def rang(self):
        return self.hit is not None and self.hit[1] >= STRIKE_BELL

    def update(self, now):
        """Hand the prize over once, when the puck hits the bell."""
        if not self.paid and now - self.hit[0] >= STRIKE_UP:
            self.paid = True
            if self.rang():
                self.rings += 1
                self.arms.append((_spin_rng.randrange(len(CLAW_PRIZES)),
                                  _spin_rng.randrange(8)))

    def verdict(self, now):
        if self.hit is None or self.ready(now):
            return ("$%d A SWING" % STRIKE_COST if self.short else "p to swing"), False
        if now - self.hit[0] < STRIKE_UP:
            return "...", False
        say = [w for at, w in STRIKE_SAYS if self.hit[1] >= at][-1]
        return say, self.rang()


def render_striker(st, width, height, now):
    """At the strength tester: the post up the middle with its scale marked
    on it and the bell on top, the puck going up it, the meter swinging
    beside it, and you with the hammer at the foot of it."""
    ch = [[" "] * width for _ in range(height)]
    co = [[0] * width for _ in range(height)]
    say, rang = st.verdict(now)
    if width < 36 or height < 16:
        _text(ch, co, height // 2, 1, "STRENGTH TEST: " + say, GOLD)
        _text(ch, co, min(height - 1, height // 2 + 2), 1, "s to leave", GOLD_DIM)
        return ch, co
    n = len(NEON)
    for x in range(width):                           # bulbs strung overhead
        lit = chase(x * 0.25, now)
        ch[1][x] = "o" if lit else "-"
        co[1][x] = NEON[(x // 6) % n][0] if lit else GOLD_DIM
    cx = width // 2
    top, foot = 4, height - 4                        # the bell's row, the base's
    ring = rang and now - st.hit[0] >= STRIKE_UP and now - st.hit[0] < STRIKE_UP + 1.5
    bell = (FLASH if int(now * 10) % 2 else GOLD) if ring else GOLD_DIM
    _text(ch, co, top - 1, cx - 3, " ___ ", bell)
    _text(ch, co, top, cx - 3, "( O )", bell)
    if ring:
        for k, d in enumerate((-9, -7, 7, 9)):
            _text(ch, co, top - 1 + k % 2, cx + d, "*", FLASH)
    span = foot - top - 1
    for r in range(1, span + 1):
        y = top + r
        _text(ch, co, y, cx - 2, "|" + ("=" if r % 2 else "-") + "|", CONCRETE)
    for at, word in STRIKE_SAYS[:-1]:                # the scale, on the left
        y = foot - 1 - int(round(at * (span - 1)))
        _text(ch, co, y, cx - 4 - len(word), word, GOLD_DIM)
    py = foot - 1 - int(round(st.puck(now) * (span - 1)))
    _text(ch, co, py, cx - 2, "[#]", FLASH if ring else ROU_RED)
    _text(ch, co, foot, cx - 5, "[_______]", CONCRETE)
    # The meter, on the right: a bar with the marker going up and down it.
    mx = cx + 13
    for r in range(span):
        y = foot - 1 - r
        hot = r >= int(STRIKE_BELL * (span - 1))
        _text(ch, co, y, mx, "|", ROU_RED if hot else GOLD_DIM)
    my = foot - 1 - int(round(st.meter(now) * (span - 1)))
    _text(ch, co, my, mx + 1, "<", FLASH)
    _text(ch, co, top, mx - 1, "BELL", ROU_RED)
    # You, with the hammer: up while it swings, down on the pad after.
    struck = st.hit is not None and now - st.hit[0] < 2 * STRIKE_UP
    for k, line in enumerate((("  o/", " /|", " / \\") if not struck
                              else ("  o", " /|\\_", " / \\"))):
        _text(ch, co, foot - 2 + k, cx + 3 if struck else cx + 4, line, STAR)
    if not struck:
        _text(ch, co, foot - 3, cx + 5, "=T", BARK)
    _text(ch, co, height - 3, max(1, cx - len(say) // 2), say,
          (FLASH if int(now * 6) % 2 else GOLD) if rang and say == "DING!" else GOLD)
    _text(ch, co, height - 2, max(1, cx - 9),
          "goes %d   bells %d" % (st.goes, st.rings), GOLD_DIM)
    if height > foot + 4:
        _text(ch, co, height - 1, max(1, cx - 10), "-- the way out (s) --", GOLD_DIM)
    return ch, co


def render_claw(claw, width, height, now):
    """At the claw machine: the cabinet in the middle, a string of bulbs
    over it, and what you have won so far beside it when there is room. A
    window too small for the cabinet gets a line of text."""
    ch = [[" "] * width for _ in range(height)]
    co = [[0] * width for _ in range(height)]
    if width < CLAW_W + 2 or height < CLAW_H + 1:
        say, _ = claw.verdict(now)
        _text(ch, co, height // 2, 1, "CLAW: " + say, GOLD)
        _text(ch, co, min(height - 1, height // 2 + 2), 1, "s to leave", GOLD_DIM)
        return ch, co
    y0 = 1
    if height >= CLAW_H + 4:
        for x in range(width):                       # bulbs strung overhead
            lit = chase(x * 0.25, now)
            ch[1][x] = "o" if lit else "-"
            co[1][x] = NEON[(x // 6) % len(NEON)][0] if lit else GOLD_DIM
        y0 = 2
    x0 = (width - CLAW_W) // 2
    draw_claw(ch, co, claw, x0, y0, now)

    ax = x0 + CLAW_W + 4
    if claw.arms and ax + 12 < width:
        _text(ch, co, y0 + 1, ax, "won tonight", GOLD_DIM)
        per = max(1, (width - ax) // 5)
        for n, (kind, colour) in enumerate(claw.arms):
            r, c = divmod(n, per)
            y = y0 + 3 + r * 3
            if y + 1 >= height - 1:
                break
            for k, line in enumerate(CLAW_PRIZES[kind][1:]):
                _text(ch, co, y + k, ax + c * 5, line, NEON[colour % len(NEON)][0])
    if y0 + CLAW_H < height - 1:
        _text(ch, co, height - 1, max(1, width // 2 - 10), "-- the way out (s) --",
              GOLD_DIM)
    return ch, co


# Inside the arcade. A row of cabinets across the back, each running a demo
# of the game it will be, the arcade's name over them in lights, the carpet
# every arcade has, and a couple of kids already at the machines.
CAB_W = 15              # one cabinet, in columns
CAB_H = 13              # and rows
CAB_SCREEN = (11, 5)    # its screen


def cabinet_demo(game, t):
    """One frame of a cabinet's demo, as CAB_SCREEN[1] strings - what the
    game will be, running on its own. Each is a function of the time alone."""
    w, h = CAB_SCREEN
    rows = [[" "] * w for _ in range(h)]

    def put(x, y, c):
        if 0 <= x < w and 0 <= y < h:
            rows[y][x] = c

    k = ARCADE_GAMES.index(game) if game in ARCADE_GAMES else 0
    if k == 0:                       # rooftop run: roofs going by, a jump
        for x in range(w):
            if (x + int(t * 8)) % 9 < 6:
                put(x, h - 1 - (((x + int(t * 8)) // 9) % 2), "=")
        hop = abs(math.sin(t * 3.0))
        put(3, h - 2 - int(hop * 2.5), "o")
    elif k == 1:                     # fix the neon: tubes turning
        for y in range(1, h - 1):
            for x in range(1, w - 1, 2):
                put(x, y, "-|+L"[(_mix(x, y, int(t * 2)) >> 4) % 4])
    elif k == 2:                     # late delivery: a grid, a scooter on it
        for y in range(h):
            for x in range(w):
                if x % 4 == 0 or y % 2 == 0:
                    put(x, y, ".")
        p = int(t * 6) % (2 * (w + h))
        put(min(p, w - 1), 0 if p < w else min(h - 1, p - w), "@")
    elif k == 3:                     # neon drift: a road going away
        for y in range(h):
            half = 1 + y
            mid = w // 2 + int(round(math.sin(t * 1.3 + y * 0.4) * (h - y) * 0.4))
            put(mid - half, y, "/")
            put(mid + half, y, "\\")
        put(w // 2 + int(math.sin(t * 2.0) * 2), h - 1, "A")
    elif k == 4:                     # sky show: a burst opening out
        r = (t * 2.5) % 3.0
        for a in range(8):
            put(w // 2 + int(round(math.cos(a * 0.785) * r * 2)),
                h // 2 + int(round(math.sin(a * 0.785) * r)), "*" if r < 2 else ".")
    else:                            # night owl: an owl, blinking
        put(w // 2 - 1, 1, "O" if int(t * 2) % 5 else "-")
        put(w // 2 + 1, 1, "O" if int(t * 2) % 5 else "-")
        put(w // 2, 2, "v")
        for x in range(w):
            put(x, h - 1, "~" if (x + int(t * 3)) % 3 else " ")
    return ["".join(r) for r in rows]


def draw_cabinet(ch, co, x0, y0, game, colour, now):
    """One cabinet: the game's name lit along the top, the screen running its
    demo with COMING SOON and INSERT COIN taking turns over it, the stick and
    the buttons, and the coin door."""
    w = CAB_W
    sw, sh = CAB_SCREEN
    _text(ch, co, y0, x0, "." + "-" * (w - 2) + ".", colour)
    _text(ch, co, y0 + 1, x0, "|" + game[:w - 2].center(w - 2) + "|", colour)
    _text(ch, co, y0 + 2, x0, "|" + "=" * (w - 2) + "|", GOLD_DIM)
    t = now + len(game) * 1.7
    demo = cabinet_demo(game, t)
    say = int(t / 3.0) % 3
    for r in range(sh):
        y = y0 + 3 + r
        _text(ch, co, y, x0, "||", GOLD_DIM)
        _text(ch, co, y, x0 + w - 2, "||", GOLD_DIM)
        line = demo[r]
        if say == 1 and r == sh // 2:
            line = "COMING SOON".center(sw)[:sw]
        elif say == 2 and r == sh // 2 and int(now * 2) % 2:
            line = "INSERT COIN".center(sw)[:sw]
        _text(ch, co, y, x0 + 2, line, colour if line in demo else FLASH)
    _text(ch, co, y0 + 3 + sh, x0, "|" + "=" * (w - 2) + "|", GOLD_DIM)
    _text(ch, co, y0 + 4 + sh, x0, "/  o   o o o  \\", CONCRETE)
    _text(ch, co, y0 + 5 + sh, x0, "|    [ $1  ]  |"[:w], GOLD_DIM)
    _text(ch, co, y0 + 5 + sh, x0 + 6, "[", FLASH if int(now * 1.5) % 2 else GOLD_DIM)
    _text(ch, co, y0 + 6 + sh, x0, "|" + "_" * (w - 2) + "|", CONCRETE)


def render_arcade(arc, width, height, now, sel=None):
    """In the arcade. The name across the top in the big font, the letters
    in every colour; a row of cabinets as wide as the window takes; the
    carpet; a couple of kids playing. A window too small for a cabinet gets
    the name and a line of text."""
    ch = [[" "] * width for _ in range(height)]
    co = [[0] * width for _ in range(height)]
    n = len(NEON)
    if width < CAB_W + 4 or height < CAB_H + 4:
        _text(ch, co, height // 2, 1, "%s ARCADE" % arc["name"], GOLD)
        _text(ch, co, min(height - 1, height // 2 + 1), 1, "the games are coming",
              GOLD_DIM)
        _text(ch, co, min(height - 1, height // 2 + 2), 1, "s to leave", GOLD_DIM)
        return ch, co
    for x in range(width):                           # the tube along the ceiling
        ch[1][x] = "="
        co[1][x] = NEON[(x // 4 + int(now * 6.0)) % n][0]
    y = 2
    name = arc["name"]
    if height >= CAB_H + 12 and big_width(name) <= width - 2:
        lx = (width - big_width(name)) // 2
        for dx, dy, k in big_cells(name):
            _text(ch, co, 3 + dy, lx + dx, "#", NEON[(k + int(now * 2.0)) % n][0])
        y = 9
    else:
        _text(ch, co, 2, (width - len(name)) // 2, name, GOLD)
        y = 4
    order = arcade_order(arc, width)
    count = len(order)
    span = count * (CAB_W + 2) - 2
    left = (width - span) // 2
    for k, game in enumerate(order):
        mine = sel is not None and k == sel % count
        draw_cabinet(ch, co, left + k * (CAB_W + 2), y, game,
                     (FLASH if int(now * 3) % 2 else GOLD) if mine
                     else NEON[(arc["seed"] + k * 3) % n][0], now)
        if mine:
            _text(ch, co, y - 1, left + k * (CAB_W + 2) + CAB_W // 2 - 1, "vvv",
                  FLASH)
    # The carpet: the loud one every arcade has, under everything else.
    for yy in range(y + CAB_H, height - 1):
        for x in range(width):
            m = _mix(x // 2, yy, 2511)
            if m % 7 == 0:
                ch[yy][x] = "*+o~^"[(m >> 4) % 5]
                co[yy][x] = NEON[(m >> 8) % n][1]
    # Two kids at the machines, from behind, and one of them is winning.
    for k in (0, count - 1) if count > 1 else (0,):
        px = left + k * (CAB_W + 2) + CAB_W // 2 - 2
        for r, line in enumerate((" ,-. ", "(   )", "/|#|\\", " | | ")):
            yy = y + CAB_H - 4 + r
            for dx, c in enumerate(line):         # solid: nothing shows through
                if yy < height - 1 and 0 <= px + dx < width:
                    ch[yy][px + dx], co[yy][px + dx] = c, CURB
        if k == 0 and int(now * 4) % 2:
            _text(ch, co, y + CAB_H - 5, px + 5, "!", FLASH)
    _text(ch, co, height - 1, max(1, width // 2 - 10), "-- the way out (s) --",
          GOLD_DIM)
    return ch, co


# ---------------------------------------------------------------------------
# The arcade's games. Each is a small class on a fixed-step clock with the same
# shape: key() takes one of "up", "down", "left", "right" or "act"; tick()
# catches the game up to now; draw() fills a GAME_W x GAME_H playfield. They
# are one or two keys and taps, never holds, because curses sees a key go down
# again and again while it is held and never sees it come up.
# ---------------------------------------------------------------------------

GAME_W, GAME_H = 40, 16   # the playfield, inside the cabinet's bezel
GAME_DT = 1.0 / 60.0      # the games' own clock, finer than the frame's


class ArcadeGame:
    name = "?"
    controls = ""

    def __init__(self, seed, now):
        self.rng = random.Random(seed)
        self.t = now
        self.score = 0
        self.over = False
        self.why = ""

    def tick(self, now):
        if now - self.t > 0.5:
            self.t = now - 0.5          # no catching up after a stall
        while not self.over and self.t + GAME_DT <= now:
            self.t += GAME_DT
            self.step(GAME_DT)

    def step(self, dt):
        pass

    def key(self, k):
        pass

    def status(self):
        return ""

    def blank(self):
        return ([[" "] * GAME_W for _ in range(GAME_H)],
                [[0] * GAME_W for _ in range(GAME_H)])


def _put(g, c, x, y, s, attr):
    for k, ch_ in enumerate(s):
        xx = int(x) + k
        if 0 <= int(y) < GAME_H and 0 <= xx < GAME_W and ch_ != " ":
            g[int(y)][xx], c[int(y)][xx] = ch_, attr


class RooftopRun(ArcadeGame):
    """Over the rooftops at night: the roofs come at you, you jump the gaps,
    and it goes faster the further you get. Miss a roof and you fall; run
    into the side of a taller one and that is it too."""
    name = "ROOFTOP RUN"
    controls = "p jumps"
    RUN_X = 8

    def __init__(self, seed, now):
        ArcadeGame.__init__(self, seed, now)
        self.x, self.speed = 0.0, 11.0
        self.y, self.vy, self.ground = 3.0, 0.0, True
        self.roofs = [(-10.0, 40.0, 3)]
        while self.roofs[-1][0] + self.roofs[-1][1] < 120:
            self.more()

    def more(self):
        x, n, h = self.roofs[-1]
        gap = self.rng.uniform(2.5, 4.0 + self.speed * 0.12)
        h2 = max(2, min(7, h + self.rng.choice((-2, -1, 0, 1, 1, 2))))
        # Longer as it gets faster: one jump carries you further, and a roof
        # shorter than a jump is one you come down off the end of.
        self.roofs.append((x + n + gap, self.rng.uniform(7.0, 16.0) + self.speed * 0.7,
                           h2))

    def roof_at(self, wx):
        for x, n, h in self.roofs:
            if x <= wx < x + n:
                return h
        return None

    def key(self, k):
        if k in ("act", "up") and self.ground:
            self.vy, self.ground = 23.0, False

    def step(self, dt):
        self.speed += 0.22 * dt
        self.x += self.speed * dt
        while self.roofs[-1][0] + self.roofs[-1][1] < self.x + 60:
            self.more()
        self.roofs = [r for r in self.roofs if r[0] + r[1] > self.x - 5]
        self.vy -= 62.0 * dt
        self.y += self.vy * dt
        h = self.roof_at(self.x + self.RUN_X)
        if h is not None and self.y < h:
            if self.y > h - 0.7 and self.vy <= 0.0:
                self.y, self.vy, self.ground = float(h), 0.0, True
            else:
                self.over, self.why = True, "ran into a wall"
        elif h is None:
            self.ground = False
        if self.y < -2.0:
            self.over, self.why = True, "fell"
        self.score = int(self.x / 2.0)

    def draw(self, now):
        g, c = self.blank()
        for k in range(14):                        # stars, slow
            sx = (k * 37 - int(self.x * 0.1)) % GAME_W
            _put(g, c, sx, k % 6, ".", STAR_DIM)
        for x, n, h in self.roofs:
            for wx in range(int(x - self.x), int(x + n - self.x)):
                if 0 <= wx < GAME_W:
                    top = GAME_H - 1 - h
                    _put(g, c, wx, top, "=", ROOF)
                    for yy in range(top + 1, GAME_H):
                        lit = (_mix(int(x), wx + int(self.x), yy) % 5 == 0)
                        _put(g, c, wx, yy, "#" if lit else ":",
                             tone_colour("warm", 0.7) if lit else CONCRETE)
        py = GAME_H - 1 - int(round(self.y))
        legs = "^" if not self.ground else ("/" if int(self.t * 10) % 2 else "\\")
        _put(g, c, self.RUN_X, py - 1, "o", FLASH)
        _put(g, c, self.RUN_X, py, legs, FLASH)
        return g, c

    def status(self):
        return "%dm" % self.score


class FixTheNeon(ArcadeGame):
    """A sign gone dark and the tubes to it turned every which way: move the
    cursor round the grid, turn the tubes with p until the power runs from
    the plug on the left all the way to the sign on the right, and the sign
    lights. Then the next one, with less time."""
    name = "FIX THE NEON"
    controls = "arrows move  p turns"
    GW, GH = 9, 4
    N, E, S, W = 1, 2, 4, 8
    STEP = {1: (0, -1), 2: (1, 0), 4: (0, 1), 8: (-1, 0)}
    BACK = {1: 4, 2: 8, 4: 1, 8: 2}

    def __init__(self, seed, now):
        ArcadeGame.__init__(self, seed, now)
        self.level = 0
        self.cx = self.cy = 0
        self.new_level()

    def new_level(self):
        self.level += 1
        self.left = max(20.0, 48.0 - self.level * 4.0)
        self.won_at = None
        gw, gh = self.GW, self.GH
        self.r0, self.r1 = self.rng.randrange(gh), self.rng.randrange(gh)
        # A path from the plug to the sign, eastwards with wandering.
        path = [(0, self.r0)]
        while path[-1] != (gw - 1, self.r1):
            x, y = path[-1]
            moves = []
            if x < gw - 1:
                moves += [(x + 1, y)] * 3
            for dy in (-1, 1):
                if 0 <= y + dy < gh and (x == gw - 1 or self.rng.random() < 0.5):
                    moves.append((x, y + dy))
            moves = [m for m in moves if m not in path]
            if x == gw - 1:
                moves = [(x, y + (1 if self.r1 > y else -1))]
            if not moves:
                path = [(0, self.r0)]
                continue
            path.append(self.rng.choice(moves))
        pieces = {}
        for k, (x, y) in enumerate(path):
            a = self.W if k == 0 else self.dir_to(path[k - 1], (x, y))
            b = self.E if k == len(path) - 1 else self.dir_to(path[k + 1], (x, y))
            pieces[(x, y)] = a | b
        self.answer = pieces            # the way round that lights it
        self.grid = {}
        for y in range(gh):
            for x in range(gw):
                m = pieces.get((x, y))
                if m is None:
                    m = self.rng.choice((self.N | self.S, self.N | self.E))
                for _ in range(self.rng.randrange(4)):
                    m = self.turn(m)
                self.grid[(x, y)] = m

    def dir_to(self, other, here):
        dx, dy = other[0] - here[0], other[1] - here[1]
        return {(0, -1): self.N, (1, 0): self.E, (0, 1): self.S,
                (-1, 0): self.W}[(dx, dy)]

    def turn(self, m):
        return ((m << 1) | (m >> 3)) & 15

    def lit(self):
        on, todo = set(), []
        if self.grid[(0, self.r0)] & self.W:
            todo.append((0, self.r0))
        while todo:
            p = todo.pop()
            if p in on:
                continue
            on.add(p)
            m = self.grid[p]
            for d, (dx, dy) in self.STEP.items():
                q = (p[0] + dx, p[1] + dy)
                if m & d and q in self.grid and self.grid[q] & self.BACK[d]:
                    todo.append(q)
        return on

    def solved(self):
        end = (self.GW - 1, self.r1)
        return end in self.lit() and self.grid[end] & self.E

    def key(self, k):
        if self.won_at is not None:
            return
        if k == "left":
            self.cx = max(0, self.cx - 1)
        elif k == "right":
            self.cx = min(self.GW - 1, self.cx + 1)
        elif k == "up":
            self.cy = max(0, self.cy - 1)
        elif k == "down":
            self.cy = min(self.GH - 1, self.cy + 1)
        elif k == "act":
            self.grid[(self.cx, self.cy)] = self.turn(self.grid[(self.cx, self.cy)])
            if self.solved():
                self.won_at = self.t
                self.score += 100 + int(self.left) * 5

    def step(self, dt):
        if self.won_at is not None:
            if self.t - self.won_at > 1.5:
                self.new_level()
            return
        self.left -= dt
        if self.left <= 0.0:
            self.over, self.why = True, "the sign stayed dark"

    def draw(self, now):
        g, c = self.blank()
        on = self.lit()
        x0, y0 = 4, 2
        lit, dark = NEON[(self.level * 3) % len(NEON)]
        for (x, y), m in self.grid.items():
            px, py = x0 + x * 3 + 1, y0 + y * 3 + 1
            attr = lit if (x, y) in on else CONCRETE
            mid = "+" if m not in (5, 10) else ("|" if m == 5 else "-")
            _put(g, c, px, py, mid, attr)
            if m & self.N:
                _put(g, c, px, py - 1, "|", attr)
            if m & self.S:
                _put(g, c, px, py + 1, "|", attr)
            if m & self.W:
                _put(g, c, px - 1, py, "-", attr)
            if m & self.E:
                _put(g, c, px + 1, py, "-", attr)
        cx, cy = x0 + self.cx * 3, y0 + self.cy * 3
        if int(self.t * 4) % 2 == 0 or self.won_at is not None:
            for dx, dy, s in ((0, 0, "."), (2, 0, "."), (0, 2, "'"), (2, 2, "'")):
                _put(g, c, cx + dx, cy + dy, s, FLASH)
        _put(g, c, 0, y0 + self.r0 * 3 + 1, "=]", GOLD)
        done = self.won_at is not None
        sx = x0 + self.GW * 3 + 1
        for k, ch_ in enumerate("OPEN"):
            _put(g, c, sx + k, y0 + self.r1 * 3 + 1, ch_,
                 (lit if int(self.t * 6) % 2 else FLASH) if done else dark)
        return g, c

    def status(self):
        return "sign %d  %ds" % (self.level, max(0, int(self.left)))


class LateDelivery(ArcadeGame):
    """A scooter and a bag of noodles, round a little grid of streets: it
    keeps going, the arrows steer it, and the door with the order is marked.
    Get there before the clock runs out; every delivery buys more time and
    the next order is somewhere else."""
    name = "LATE DELIVERY"
    controls = "arrows steer"
    DIRS = {"up": (0, -1), "down": (0, 1), "left": (-1, 0), "right": (1, 0)}

    def __init__(self, seed, now):
        ArcadeGame.__init__(self, seed, now)
        self.road = {(x, y) for x in range(GAME_W) for y in range(GAME_H)
                     if x % 5 == 1 or y % 4 == 1}
        self.pos, self.dir, self.want = (1, 1), (1, 0), (1, 0)
        self.left, self.move = 20.0, 0.0
        self.pick()

    def pick(self):
        doors = [p for p in self.road
                 if any((p[0] + dx, p[1] + dy) not in self.road
                        and 0 <= p[0] + dx < GAME_W and 0 <= p[1] + dy < GAME_H
                        for dx, dy in ((0, 1), (0, -1), (1, 0), (-1, 0)))
                 and abs(p[0] - self.pos[0]) + abs(p[1] - self.pos[1]) > 15]
        self.target = self.rng.choice(sorted(doors))

    def key(self, k):
        if k in self.DIRS:
            self.want = self.DIRS[k]

    def free(self, d):
        q = (self.pos[0] + d[0], self.pos[1] + d[1])
        return q in self.road

    def step(self, dt):
        self.left -= dt
        if self.left <= 0.0:
            self.over, self.why = True, "the noodles went cold"
            return
        self.move += dt
        every = max(0.06, 0.13 - self.score * 0.004)
        while self.move >= every:
            self.move -= every
            if self.free(self.want):
                self.dir = self.want
            if self.free(self.dir):
                self.pos = (self.pos[0] + self.dir[0], self.pos[1] + self.dir[1])
            if self.pos == self.target:
                self.score += 1
                self.left += max(5.0, 9.0 - self.score * 0.3)
                self.pick()

    def draw(self, now):
        g, c = self.blank()
        for y in range(GAME_H):
            for x in range(GAME_W):
                if (x, y) in self.road:
                    _put(g, c, x, y, ".", STREET)
                else:
                    _put(g, c, x, y, "#",
                         tone_colour("cold", ((x // 5 + y // 4) % 4) / 4.0))
        tx, ty = self.target
        _put(g, c, tx, ty, "X", FLASH if int(self.t * 5) % 2 else ROU_RED)
        _put(g, c, self.pos[0], self.pos[1], "@", GOLD)
        return g, c

    def status(self):
        return "%d delivered  %ds" % (self.score, max(0, int(self.left)))


class NeonDrift(ArcadeGame):
    """Down a neon highway at night, faster and faster, in and out of the
    traffic: left and right change lanes, and anything in your lane when you
    get to it is the end of the run."""
    name = "NEON DRIFT"
    controls = "left/right change lane"
    LANES = 5

    def __init__(self, seed, now):
        ArcadeGame.__init__(self, seed, now)
        self.lane, self.speed, self.dist = 2, 9.0, 0.0
        self.cars = []                 # [lane, y]
        self.next = 1.0

    def key(self, k):
        if k == "left":
            self.lane = max(0, self.lane - 1)
        elif k == "right":
            self.lane = min(self.LANES - 1, self.lane + 1)

    def lane_x(self, lane):
        return GAME_W // 2 - 8 + lane * 4

    def step(self, dt):
        self.speed += 0.35 * dt
        self.dist += self.speed * dt
        self.score = int(self.dist)
        self.next -= dt
        if self.next <= 0.0:
            free = [k for k in range(self.LANES)
                    if not any(cl == k and cy < 3 for cl, cy in self.cars)]
            if free:
                self.cars.append([self.rng.choice(free), -2.0])
            self.next = max(0.25, 1.1 - self.speed * 0.03) * self.rng.uniform(0.6, 1.2)
        for car in self.cars:
            car[1] += self.speed * dt * 0.8
            if car[0] == self.lane and GAME_H - 4 < car[1] < GAME_H:
                self.over, self.why = True, "crashed"
        self.cars = [c_ for c_ in self.cars if c_[1] < GAME_H + 2]

    def draw(self, now):
        g, c = self.blank()
        left, right = self.lane_x(0) - 2, self.lane_x(self.LANES - 1) + 4
        scroll = int(self.dist)
        for y in range(GAME_H):
            on = (y + scroll) % 4 < 2
            _put(g, c, left, y, "|", NEON[2][0] if on else NEON[2][1])
            _put(g, c, right, y, "|", NEON[1][0] if on else NEON[1][1])
            for k in range(1, self.LANES):
                if (y + scroll) % 3 == 0:
                    _put(g, c, self.lane_x(k) - 1, y, ":", CONCRETE)
            for x in range(0, left):
                if _mix(x, y - scroll, 7) % 23 == 0:
                    _put(g, c, x, y, ".", STAR_DIM)
            for x in range(right + 1, GAME_W):
                if _mix(x, y - scroll, 9) % 23 == 0:
                    _put(g, c, x, y, ".", STAR_DIM)
        for k, (cl, cy) in enumerate(self.cars):
            attr = NEON[(cl * 3 + 1) % len(NEON)][0]
            _put(g, c, self.lane_x(cl), cy, "[#]", attr)
            _put(g, c, self.lane_x(cl), cy + 1, " V ", ROU_RED)
        px = self.lane_x(self.lane)
        _put(g, c, px, GAME_H - 3, " A ", FLASH)
        _put(g, c, px, GAME_H - 2, "[#]", GOLD)
        return g, c

    def status(self):
        return "%d km/h" % int(self.speed * 9)


class SkyShow(ArcadeGame):
    """Rockets go up and p bursts them: on the line is a big one, near it a
    small one, and one that goes off the top without bursting is a miss.
    Three misses and the show is over."""
    name = "SKY SHOW"
    controls = "p bursts on the line"
    LINE = 4

    def __init__(self, seed, now):
        ArcadeGame.__init__(self, seed, now)
        self.rockets, self.bursts = [], []     # [x, y, speed]; (x, y, t0, big)
        self.misses, self.next, self.rate = 0, 0.6, 1.2

    def key(self, k):
        if k != "act":
            return
        near = [r for r in self.rockets if abs(r[1] - self.LINE) < 1.6]
        if not near:
            self.score = max(0, self.score - 10)
            return
        r = min(near, key=lambda r_: abs(r_[1] - self.LINE))
        big = abs(r[1] - self.LINE) < 0.6
        self.score += 100 if big else 40
        self.bursts.append((r[0], r[1], self.t, big))
        self.rockets.remove(r)

    def step(self, dt):
        self.next -= dt
        if self.next <= 0.0:
            self.rockets.append([self.rng.randrange(3, GAME_W - 3), float(GAME_H - 1),
                                 self.rng.uniform(5.0, 7.0)
                                 + min(5.0, self.score * 0.002)])
            self.rate = max(0.45, self.rate * 0.985)
            self.next = self.rate * self.rng.uniform(0.7, 1.3)
        for r in self.rockets:
            r[1] -= r[2] * dt
        gone = [r for r in self.rockets if r[1] < 0.0]
        for r in gone:
            self.rockets.remove(r)
            self.misses += 1
        if self.misses >= 3:
            self.over, self.why = True, "three went up dark"
        self.bursts = [b for b in self.bursts if self.t - b[2] < 1.2]

    def draw(self, now):
        g, c = self.blank()
        for x in range(0, GAME_W, 2):
            _put(g, c, x, self.LINE, "-", GOLD_DIM)
        for x in range(GAME_W):
            _put(g, c, x, GAME_H - 1, "~", RAIN_FAR)
        for x, y, _ in self.rockets:
            _put(g, c, x, y, "|", EMBER_HOT)
            _put(g, c, x, y + 1, ".", EMBER)
        for x, y, t0, big in self.bursts:
            age = self.t - t0
            r = age * (6.0 if big else 3.0)
            attr = NEON[int(x) % len(NEON)][0 if age < 0.6 else 1]
            for k in range(12 if big else 6):
                a = k * math.tau / (12 if big else 6)
                _put(g, c, x + math.cos(a) * r * 2.0, y + math.sin(a) * r,
                     "*" if age < 0.5 else ".", attr)
        return g, c

    def status(self):
        return "misses %d/3" % self.misses


class NightOwl(ArcadeGame):
    """An owl on a branch at the bottom, moths coming down through the dark:
    left and right move it along the branch to catch them. Three that get
    past and it goes hungry."""
    name = "NIGHT OWL"
    controls = "left/right move"

    def __init__(self, seed, now):
        ArcadeGame.__init__(self, seed, now)
        self.x, self.moths, self.lost = GAME_W // 2, [], 0
        self.next = 0.8

    def key(self, k):
        if k == "left":
            self.x = max(1, self.x - 2)
        elif k == "right":
            self.x = min(GAME_W - 2, self.x + 2)

    def step(self, dt):
        self.next -= dt
        if self.next <= 0.0:
            self.moths.append([float(self.rng.randrange(2, GAME_W - 2)), 0.0,
                               self.rng.uniform(0.0, math.tau),
                               2.5 + self.score * 0.05])
            self.next = max(0.5, 1.6 - self.score * 0.03) * self.rng.uniform(0.7, 1.3)
        for m in self.moths:
            m[1] += m[3] * dt
            m[2] += dt * 3.0
            m[0] = min(GAME_W - 1.0, max(0.0, m[0] + math.sin(m[2]) * dt * 3.0))
        caught = [m for m in self.moths
                  if GAME_H - 3.5 < m[1] < GAME_H - 1.5 and abs(m[0] - self.x) < 2.0]
        for m in caught:
            self.moths.remove(m)
            self.score += 1
        gone = [m for m in self.moths if m[1] >= GAME_H - 1]
        for m in gone:
            self.moths.remove(m)
            self.lost += 1
        if self.lost >= 3:
            self.over, self.why = True, "three got away"

    def draw(self, now):
        g, c = self.blank()
        _put(g, c, 34, 1, "( )", MOON_DIM)
        for x in range(GAME_W):
            _put(g, c, x, GAME_H - 1, "=", BARK)
        for x, y, _, _ in self.moths:
            _put(g, c, x, y, "*" if int(self.t * 8 + x) % 2 else "+", BULB)
        blink = int(self.t * 0.7) % 7 == 0
        _put(g, c, self.x - 1, GAME_H - 3, "-v-" if blink else "OvO", GOLD)
        _put(g, c, self.x - 1, GAME_H - 2, "/_\\", BARK)
        return g, c

    def status(self):
        return "%d caught, %d got away" % (self.score, self.lost)


GAMES = {g.name: g for g in (RooftopRun, FixTheNeon, LateDelivery, NeonDrift,
                             SkyShow, NightOwl)}


def arcade_order(arc, width):
    """The cabinets in the row, as many as the window has room for."""
    count = max(1, min(len(ARCADE_GAMES), (width - 2) // (CAB_W + 2)))
    return [ARCADE_GAMES[(arc["seed"] + k) % len(ARCADE_GAMES)] for k in range(count)]


def render_game(game, hi, width, height, now):
    """Playing one: the cabinet's screen filling the window - the game's name
    lit along the top, the playfield in the bezel, the score and the high
    score under it, and GAME OVER over it when it is."""
    ch = [[" "] * width for _ in range(height)]
    co = [[0] * width for _ in range(height)]
    if width < GAME_W + 4 or height < GAME_H + 6:
        _text(ch, co, height // 2, 1, "%s: the window is too small to play" % game.name,
              GOLD)
        _text(ch, co, min(height - 1, height // 2 + 1), 1, "x leaves the cabinet",
              GOLD_DIM)
        return ch, co
    x0 = (width - GAME_W) // 2
    y0 = max(2, (height - GAME_H - 4) // 2 + 1)
    _text(ch, co, y0 - 2, x0 + (GAME_W - len(game.name)) // 2, game.name,
          NEON[len(game.name) % len(NEON)][0])
    _text(ch, co, y0 - 1, x0 - 1, "." + "-" * GAME_W + ".", GOLD_DIM)
    _text(ch, co, y0 + GAME_H, x0 - 1, "'" + "-" * GAME_W + "'", GOLD_DIM)
    for y in range(GAME_H):
        _text(ch, co, y0 + y, x0 - 1, "|", GOLD_DIM)
        _text(ch, co, y0 + y, x0 + GAME_W, "|", GOLD_DIM)
    g, c = game.draw(now)
    for y in range(GAME_H):
        for x in range(GAME_W):
            if g[y][x] != " ":
                ch[y0 + y][x0 + x], co[y0 + y][x0 + x] = g[y][x], c[y][x]
    line = "SCORE %d   HI %d   %s" % (game.score, max(hi, game.score), game.status())
    _text(ch, co, y0 + GAME_H + 1, x0 + (GAME_W - len(line)) // 2, line, GOLD)
    if game.over:
        flash = FLASH if int(now * 3) % 2 else GOLD
        for k, (s, attr) in enumerate((("GAME OVER", flash),
                                       (game.why, GOLD_DIM),
                                       ("p plays again  x leaves", GOLD_DIM))):
            _text(ch, co, y0 + GAME_H // 2 - 1 + k, x0 + (GAME_W - len(s)) // 2,
                  " %s " % s, attr)
    else:
        hint = game.controls + "   x leaves"
        _text(ch, co, y0 + GAME_H + 2, x0 + (GAME_W - len(hint)) // 2, hint, GOLD_DIM)
    return ch, co


# ===========================================================================
# CHEATS
#
# None of this generates anything. The city is a pure function of its
# coordinates, so the menu searches for what is already out there and moves you
# to it: a club is exactly as rare after you have teleported to one as it was
# before, and CLUB_ODDS is only ever read, never leaned on. A jump is precisely
# equivalent to having walked there.
# ===========================================================================

CHEAT_KEY = ord("`")
CHEAT_SKIP = 40.0      # ignore what is already underfoot, so a repeat moves on
CHEAT_RINGS = 200      # cells of search before giving up and saying so

CHEAT_PLACES = [
    # Letters where they can be the place's own (r ramen, d diner, c casino),
    # never a key that is another one's other case. Kinds that are not here
    # any more - inside a casino, a dead end, far away - are still found by
    # find_place(), for the tests, but the panel is for going somewhere.
    ("c", "casino", "casino"),
    ("k", "club", "club"),
    ("p", "roof party", "roofparty"),
    ("v", "woods rave", "rave"),
    ("g", "arcade", "arcade"),
    ("m", "cinema", "cinema"),
    ("f", "carnival", "carnival"),
    ("j", "claw machine", "claw"),
    ("h", "strength test", "striker"),
    ("x", "a manhole", "manhole"),
    ("r", "ramen", "ramen"),
    ("d", "diner", "diner"),
    ("^", "sky deck", "tower"),
    ("i", "lighthouse top", "lighthousedoor"),
    ("b", "big bridge", "grand"),
    ("$", "billboard", "billboard"),
    ("e", "stock exchange", "exchange"),
    ("*", "the temple", "temple"),
    ("y", "lit alley", "yokocho"),
    ("=", "under the el", "el"),
    ("|", "fire escape", "escape"),
    ("_", "car park", "carpark"),
    ("<", "police car", "police"),
    (")", "highway", "highway"),
    ("o", "the woods", "woods"),
    ("~", "the lake", "lake"),
    ("t", "riverbank", "bank"),
]

# The panel's groups, by what you would go there for.
CHEAT_GROUPS = [
    ("NIGHTLIFE", ["casino", "club", "roofparty", "rave"]),
    ("FUN", ["arcade", "cinema", "carnival", "claw", "striker", "manhole"]),
    ("EAT", ["ramen", "diner"]),
    ("VIEWS", ["tower", "lighthousedoor", "grand", "billboard"]),
    ("MONEY", ["exchange"]),
    ("AROUND TOWN", ["temple", "yokocho", "el", "escape", "carpark", "police",
                     "highway"]),
    ("OUT OF TOWN", ["woods", "lake", "bank"]),
]


def _rings(ci, cj, limit):
    """Cells outward from (ci, cj), nearest ring first."""
    yield ci, cj
    for r in range(1, limit):
        for d in range(-r, r):
            yield ci + d, cj - r
            yield ci + r, cj + d
            yield ci - d, cj + r
            yield ci - r, cj - d


def best_view(x, z):
    """Whichever way you can see furthest from here, and how far that is."""
    best, ang = -1.0, 0.0
    for k in range(8):
        a = k * math.tau / 8.0
        d = probe(x, z, a, 45.0)
        if d > best:
            best, ang = d, a
    return ang, best


def best_yaw(x, z):
    return best_view(x, z)[0]


def _door_spot(i, j, salt, key):
    """A club or a casino, and somewhere to stand looking at its door.

    The hash is tested before is_open(), because it throws out 1199 cells in
    1200 for the price of one multiply, and lot() - which builds a whole
    building - is only ever reached on an actual hit."""
    if _mix(i, j, salt) % CLUB_ODDS or is_open(i, j):
        return None
    place = lot(i, j)[key]
    if place is None:
        return None
    f = place["door"]
    nx, nz = FACES[f]
    if not is_open(i + nx, j + nz):
        return None
    # Far enough back to see the whole front of it. Standing on the doorstep
    # puts your nose against a facade and shows you nothing.
    for back in (9.0, 7.0, 11.0, 5.5, 13.0, 4.0, 3.0):
        p = face_point(i, j, f, place["u"], back, 0.0)
        if can_stand(p[0], p[2]):
            return p[0], p[2], math.atan2(-nx, -nz)
    return None


def _alley_spot(i, j, dead, want_lit=None):
    if not is_open(i, j) or road_at(i, j):
        return None
    if want_lit is not None and yokocho_at(i, j) != want_lit:
        return None
    if dead:
        # A dead end is an alley cell walled on three sides. Stand in the cell
        # in front of it and look in, which is the view worth having.
        ways = [(a, b) for a, b in ((i - 1, j), (i + 1, j), (i, j - 1), (i, j + 1))
                if is_open(a, b)]
        if len(ways) != 1:
            return None
        a, b = ways[0]
        x, z = (a + 0.5) * CELL, (b + 0.5) * CELL
        if not can_stand(x, z):
            return None
        return x, z, math.atan2(float(i - a), float(j - b))
    x, z = (i + 0.5) * CELL, (j + 0.5) * CELL
    if not can_stand(x, z):
        return None
    # A one-cell courtyard walled in on every side is technically an alley and
    # is no use to look at, so insist on being able to see down it.
    yaw, clear = best_view(x, z)
    if clear < 9.0:
        return None
    return x, z, yaw


def _crossroads_spot(i, j):
    if not (_is_road(i, XP, 91) and _is_road(j, ZP, 137)) or not is_open(i, j):
        return None
    x, z = (i + 0.5) * CELL, (j + 0.5) * CELL
    if not can_stand(x, z):
        return None
    return x, z, best_yaw(x, z)


def _long_street(x, z):
    """The longest clear run of street nearby. Stops as soon as it finds one
    worth looking down, because probing every road cell for a hundred units is
    far more work than the rest of the menu put together."""
    ci = int(x / CELL + BIG) - BIG
    cj = int(z / CELL + BIG) - BIG
    best = None
    for i, j in _rings(ci, cj, 26):
        if not (is_open(i, j) and road_at(i, j)):
            continue
        px, pz = (i + 0.5) * CELL, (j + 0.5) * CELL
        if (px - x) ** 2 + (pz - z) ** 2 < CHEAT_SKIP ** 2 or not can_stand(px, pz):
            continue
        for k in range(4):
            a = k * math.tau / 4.0
            run = probe(px, pz, a, 110.0)
            if best is None or run > best[0]:
                best = (run, px, pz, a)
        if best is not None and best[0] >= 90.0:
            break
    return None if best is None else (best[1], best[2], best[3])


def _far_away(x, z):
    a = _mix(int(x), int(z), 733)
    ang = (a & 0xFFFF) / 65535.0 * math.tau
    dist = 3000.0 + (a >> 16) % 5000
    ci = int((x + math.sin(ang) * dist) / CELL + BIG) - BIG
    cj = int((z + math.cos(ang) * dist) / CELL + BIG) - BIG
    for i, j in _rings(ci, cj, 60):
        if not is_open(i, j):
            continue
        px, pz = (i + 0.5) * CELL, (j + 0.5) * CELL
        if can_stand(px, pz):
            return px, pz, best_yaw(px, pz)
    return None


def _district_spot(x, z, want):
    """Somewhere to stand well inside the nearest patch of this part of town.

    Well inside matters: land on the edge of a district and half of what you
    can see belongs to the one next door, which is no use for looking at."""
    ci = int(x / CELL + BIG) - BIG
    cj = int(z / CELL + BIG) - BIG
    skip = CHEAT_SKIP ** 2
    for i, j in _rings(ci, cj, CHEAT_RINGS):
        if district_at(i, j) != want or not is_open(i, j):
            continue
        if sum(district_at(i + a, j + b) == want
               for a, b in ((-5, 0), (5, 0), (0, -5), (0, 5))) < 3:
            continue
        px, pz = (i + 0.5) * CELL, (j + 0.5) * CELL
        if (px - x) ** 2 + (pz - z) ** 2 < skip or not can_stand(px, pz):
            continue
        yaw, clear = best_view(px, pz)
        if clear >= 12.0:
            return px, pz, yaw
    return None


def _water_spot(x, z, kind):
    """Somewhere on, or looking at, the river.

    Not a ring search like the rest of the menu: there is one river and it is
    at a known place, so walking outward looking for it fails from anywhere
    more than a couple of hundred cells away in j - which is most of an
    infinite city. Go straight to the channel at this x and work along it.

    The bank faces across the water; the pier puts you at the far end of one
    looking back at the city, which is the view it exists for; a bridge
    stands you on the road up to it with the lamps in front of you."""
    ci = int(x / CELL + BIG) - BIG
    if kind == "lighthouse":
        # Where the bridge lands on the headland, looking out to the point.
        for k in range(-1, 3):
            home = headland_home(ci + k * GRAND_GAP)
            if home is None:
                continue
            li, lj = home
            for back in range(0, 8):
                px, pz = (li + 0.5) * CELL, (lj + 4 - back + 0.5) * CELL
                if (px - x) ** 2 + (pz - z) ** 2 < CHEAT_SKIP ** 2:
                    break
                if can_stand(px, pz) and headland_at(li, lj + 4 - back):
                    return px, pz, math.pi
        return None
    if kind == "grand":
        # On the deck at the near end, looking across: the cables rising to
        # the towers either side of you, which is the view it exists for.
        for k in range(-1, 3):
            span = grand_avenue(ci + k * GRAND_GAP)
            if span is None:
                continue
            gi = span[0] + span[1] // 2
            _, hi = river_span(gi)
            px, pz = (gi + 0.5) * CELL, (int(hi) - 0.5) * CELL
            if (px - x) ** 2 + (pz - z) ** 2 < CHEAT_SKIP ** 2:
                continue
            if can_stand(px, pz):
                return px, pz, math.pi
        return None
    if kind == "carnival":
        # On the fairground, near the water, looking down the length of it.
        for k in range(-1, 3):
            c = carnival_col(ci + k * CARNIVAL_GAP)
            # Looking down the length of it, from whichever end has room:
            # the bank slopes, and looking the way it runs out you look
            # into the river two steps on.
            for end, yaw in ((c, math.pi * 0.5), (c + FAIR_LONG - 1, -math.pi * 0.5)):
                for back in (1.2, 2.0, 2.8):
                    px, pz = (end + 0.5) * CELL, bank_z(end) + back * CELL
                    if (px - x) ** 2 + (pz - z) ** 2 < CHEAT_SKIP ** 2:
                        continue
                    if can_stand(px, pz) and probe(px, pz, yaw, 60.0) >= 20.0:
                        return px, pz, yaw
        return None
    for step in range(0, CHEAT_RINGS * 3):
        i = ci + (step + 1) // 2 * (1 if step % 2 else -1)
        lo, hi = river_span(i)
        if kind == "pier":
            # The last plank, whichever it is: a pier is cut short on a narrow
            # stretch, so counting a fixed number out from the bank lands in
            # the water as often as not.
            end = None
            for k in range(int(lo), int(lo) + PIER_LEN + 2):
                if pier_at(i, k):
                    end = k
            if end is None:
                continue
            px, pz = (i + 0.5) * CELL, (end + 0.5) * CELL
            if (px - x) ** 2 + (pz - z) ** 2 < CHEAT_SKIP ** 2:
                continue                    # the one you are on: move on
            if can_stand(px, pz):
                return px, pz, 0.0          # looking back up the pier
            continue
        if kind in ("bridge", "leaner"):
            mid = int((lo + hi) * 0.5)
            if not (bridge_at(i, mid) and not bridge_at(i - 1, mid)):
                continue
            if kind == "leaner" and leaner_at(i) is None:
                continue
            for back in range(2, 16):
                px, pz = (i + 1.5) * CELL, (hi + back) * CELL
                if (px - x) ** 2 + (pz - z) ** 2 < CHEAT_SKIP ** 2:
                    break                   # the one you are at: move on
                if can_stand(px, pz):
                    return px, pz, math.pi
            continue
        # The bank: on the promenade, at the rail, facing the water.
        if not prom_at(i, shore_j(i)):
            continue
        for out in (1, 2):
            j = shore_j(i) + out - 1
            px, pz = (i + 0.5) * CELL, (j + 0.5) * CELL
            if (px - x) ** 2 + (pz - z) ** 2 < CHEAT_SKIP ** 2:
                break
            if not river_at(i, j) and can_stand(px, pz):
                return px, pz, math.pi
    return None


def _woods_spot(x, z, kind):
    """The woods: at a gate, on the road that runs up to it, looking in. The
    rave: on the path down into the hollow, a few cells short of it, facing
    the altar. Only takes you there - the menu starts one when you arrive, or
    eighteen times in twenty you would be looking at an empty hollow."""
    hx, hz, hi, hj = nearest_hollow(x, z)
    ci, cj = woods_home(hi, hj)
    if kind == "lake":
        # On the shore path, on the side nearest the hollow, facing the water.
        li, lj = lake_centre(ci, cj)
        step = 1 if hi > li else -1
        for i in range(li, li + step * 16, step):
            px, pz = (i + 0.5) * CELL, (lj + 0.5) * CELL
            if not lake_at(i, lj) and can_stand(px, pz):
                return px, pz, math.atan2(-step, 0.0)
        return None
    if kind == "rave":
        for back in range(int(HOLLOW_RJ) + 1, int(HOLLOW_RJ) + 14):
            px, pz = hx, (hj - back + 0.5) * CELL
            if can_stand(px, pz):
                return px, pz, 0.0
        return None
    for step in range(0, 60):
        i = ci + (step + 1) // 2 * (1 if step % 2 else -1)
        if not _is_road(i, XP, 91):
            continue
        j = cj
        while woods_at(i, j):
            j -= 1
        for out in range(2, 6):
            px, pz = (i + 0.5) * CELL, (j - out + 0.5) * CELL
            if can_stand(px, pz):
                return px, pz, 0.0
    return None


def _temple_spot(x, z):
    """Across the street from the nearest temple, looking at its front: the
    rose window and the door are what it is. Walking in is a few steps."""
    ci = int(x / CELL + BIG) - BIG
    cj = int(z / CELL + BIG) - BIG
    for i, j in _rings(ci, cj, CHEAT_RINGS):
        if _mix(i, j, 3201) % TEMPLE_ODDS or is_open(i, j):
            continue
        tp = lot(i, j)["temple"]
        if tp is None:
            continue
        nx, nz = FACES[tp["door"]]
        for back in (9.0, 8.0, 10.0, 7.0, 11.0):
            p = face_point(i, j, tp["door"], tp["u"], back, 0.0)
            if (p[0] - x) ** 2 + (p[2] - z) ** 2 < CHEAT_SKIP ** 2:
                break
            if can_stand(p[0], p[2]):
                return p[0], p[2], math.atan2(-nx, -nz)
    return None


def _doorway(x, z, salt, key, odds=CLUB_ODDS):
    """Standing in the door of the nearest one of these, which is what puts you
    inside it. No skipping the one underfoot here: if you are outside a club
    and ask to go in, you mean that club."""
    ci = int(x / CELL + BIG) - BIG
    cj = int(z / CELL + BIG) - BIG
    for i, j in _rings(ci, cj, CHEAT_RINGS):
        if _mix(i, j, salt) % odds or is_open(i, j):
            continue
        v = lot(i, j)[key]
        if v is None:
            continue
        nx, nz = FACES[v["door"]]
        if not is_open(i + nx, j + nz):
            continue
        p = face_point(i, j, v["door"], v["u"], 1.4, 0.0)
        if can_stand(p[0], p[2]):
            return p[0], p[2], math.atan2(-nx, -nz)
    return None


_clock = [0.0]          # the main loop's time, for the one cheat that needs it


def now_hint():
    return _clock[0]


def _police_spot(x, z, now):
    """On the pavement of a wide street with a police car coming towards you,
    some way off: look up the street and it is there, lights going. Searched
    a widening square at a time, so the nearest is the one you get."""
    if TRAFFIC_ODDS.get(TRAFFIC[_traffic]) is None:
        return None
    for reach in (150.0, 400.0, 900.0):
        v = View(x, z, 0.0, 2, 2)
        best = None
        later = {g for *_, k_, g in near_cars(v, now + 2.5, reach + 30.0, every=True)
                 if k_ == "police"}
        for d2, cx, cz, (dx, dz), kind, g in near_cars(v, now, reach, every=True):
            if kind != "police" or g not in later:
                continue                  # turning off before it gets to you
            # Stand eighteen units ahead of it, on the pavement beside its lane:
            # at thirty it was three columns wide and lost among the shops.
            px, pz = cx + dx * 18.0, cz + dz * 18.0
            i = int(px / CELL + BIG) - BIG
            j = int(pz / CELL + BIG) - BIG
            span = road_span(i if dx == 0.0 else j, XP if dx == 0.0 else ZP,
                             91 if dx == 0.0 else 137)
            if span is None:
                continue
            edge = span[0] * CELL + 1.3
            if dx == 0.0:
                px = edge
            else:
                pz = edge
            if can_stand(px, pz) and (best is None or d2 < best[0]):
                best = (d2, px, pz, math.atan2(-dx, -dz))
        if best is not None:
            return best[1:]
    return None


def _diner_door(x, z):
    """In the diner's doorway - its own odds, so not _doorway()'s."""
    ci = int(x / CELL + BIG) - BIG
    cj = int(z / CELL + BIG) - BIG
    for i, j in _rings(ci, cj, CHEAT_RINGS):
        if _mix(i, j, 2401) % DINER_ODDS or is_open(i, j):
            continue
        dn = lot(i, j)["diner"]
        if dn is None:
            continue
        nx, nz = FACES[dn["door"]]
        p = face_point(i, j, dn["door"], dn["u"], 1.4, 0.0)
        if (p[0] - x) ** 2 + (p[2] - z) ** 2 < CHEAT_SKIP ** 2:
            continue
        if can_stand(p[0], p[2]):
            return p[0], p[2], math.atan2(-nx, -nz)
    return None


def _claw_spot(x, z, where=None):
    """Stood at the claw machine - or whatever else on the fair where says -
    at the next carnival along the river."""
    ci = int(x / CELL + BIG) - BIG
    for k in range(-1, 3):
        c = carnival_col(ci + k * CARNIVAL_GAP)
        bx, bz = (where or claw_spot)(c)
        px, pz = bx, bz - 1.2
        if (px - x) ** 2 + (pz - z) ** 2 < CHEAT_SKIP ** 2:
            continue
        if can_stand(px, pz):
            return px, pz, 0.0
    return None


def _roof_party_spot(x, z):
    """Outside the landmark's lobby, facing the door: one step in and you are
    in the lift up to the party."""
    ti, tj = int(x // (LANDMARK_TILE * CELL)), int(z // (LANDMARK_TILE * CELL))
    best = None
    for a in range(ti - 2, ti + 3):
        for b in range(tj - 2, tj + 3):
            lm = landmark_of(a, b)
            if lm is None:
                continue
            li, lj = lm["lobby"]
            px, _, pz = face_point(li, lj, 3, CELL * 0.5, CASINO_REACH + 2.4, 0.0)
            d = (px - x) ** 2 + (pz - z) ** 2
            if d < CHEAT_SKIP ** 2 or not can_stand(px, pz):
                continue
            if best is None or d < best[0]:
                best = (d, px, pz)
    return None if best is None else (best[1], best[2], math.pi)


def landmark_hint(x, z):
    """For the HUD, outside the landmark: what is on up there."""
    ti, tj = int(x // (LANDMARK_TILE * CELL)), int(z // (LANDMARK_TILE * CELL))
    lm = landmark_of(ti, tj)
    if lm is None:
        return ""
    li, lj = lm["lobby"]
    dx, dz = (li + 0.5) * CELL - x, (lj + 1.0) * CELL - z
    if dx * dx + dz * dz < 30.0 ** 2:
        return "  ~ %s: roof party, lift in the lobby ~" % lm["name"].lower()
    return ""


def _pleasure_pier_spot(x, z):
    """On the bank beside the pleasure pier, looking along the shore at it:
    the drop tower, the coaster and the wheel side by side."""
    ci = int(x / CELL + BIG) - BIG
    for k in range(-1, 3):
        span = grand_avenue(ci + k * GRAND_GAP)
        if span is None:
            continue
        c = carnival_col(span[0])
        tx, tz = (c + 7.0) * CELL, (pier_tip(c, k=7) + 2.0) * CELL
        for d in (12, 16, 9, 20):
            for col in (c - d, c + FAIR_LONG + d):
                px, pz = (col + 0.5) * CELL, (shore_j(col) + 1.2) * CELL
                if (px - x) ** 2 + (pz - z) ** 2 < CHEAT_SKIP ** 2:
                    continue
                if can_stand(px, pz):
                    return px, pz, math.atan2(tx - px, tz - pz)
    return None


def _lighthouse_door_spot(x, z):
    """Outside the lighthouse's door, facing it: one step in and you are on
    the stair, the way the sky deck's cheat leaves you at its lobby."""
    ci = int(x / CELL + BIG) - BIG
    for k in range(-1, 3):
        lh = lighthouse_info(ci + k * GRAND_GAP)
        if lh is None:
            continue
        px, pz, _ = lh["exit"]
        if (px - x) ** 2 + (pz - z) ** 2 < CHEAT_SKIP ** 2:
            continue
        if can_stand(px, pz):
            return px, pz, math.pi
    return None


def claw_near(x, z):
    """Within sight of a claw machine, but not at it."""
    ci = int(x / CELL + BIG) - BIG
    c = carnival_over(ci, 3)
    if c is None:
        return False
    bx, bz = claw_spot(c)
    # Anywhere on the fair, or out on its pier.
    return (bx - x) ** 2 + (bz - z) ** 2 < 40.0 ** 2


def _billboard_spot(x, z):
    """Across the wide street from a billboard, looking up at it."""
    ci = int(x / CELL + BIG) - BIG
    cj = int(z / CELL + BIG) - BIG
    for i, j in _rings(ci, cj, CHEAT_RINGS):
        if _mix(i, j, 2405) % BILL_ODDS or is_open(i, j):
            continue
        bb = lot(i, j)["billboard"]
        if bb is None:
            continue
        # Down the street from it, in the road's middle, far enough back to
        # have the whole board on the screen: it faces along the street.
        f = bb["face"]
        mx, _, mz = face_point(i, j, f, CELL * 0.5, 0.0, 0.0)
        tx, tz = -FACES[f][1], FACES[f][0]          # along the street
        nx, nz = FACES[f]
        a, c = i + nx, j + nz
        span = road_span(a, XP, 91) if nx else road_span(c, ZP, 137)
        mid_out = (span[1] * CELL * 0.5) if span else 6.0
        for out in (mid_out, mid_out - 3.0, mid_out + 3.0):
            for along in (40.0, -40.0, 34.0, -34.0, 28.0, -28.0):
                px = mx + nx * out + tx * along
                pz = mz + nz * out + tz * along
                if (px - x) ** 2 + (pz - z) ** 2 < CHEAT_SKIP ** 2:
                    continue
                if can_stand(px, pz):
                    return px, pz, math.atan2(mx - px, mz - pz)
    return None


def _tunnel_spot(x, z, kind):
    """On the avenue a little way short of the mouth, looking in. Avenue by
    avenue outwards, the block hash first."""
    a0 = int(x / (XP * CELL))
    b0 = int(z / (ZP * CELL))
    for r in range(0, 80):
        for a in {a0 - r, a0 + r}:
            for b in range(b0 - r, b0 + r + 1):
                for i in range(a * XP, a * XP + XP):
                    span = road_span(i, XP, 91)
                    if span is None or span[0] != i:
                        continue
                    run = tunnel_run(i, b * ZP + 5)
                    if run is None or run[0] != kind:
                        continue
                    px = (span[0] + span[1] * 0.5) * CELL
                    pz = (run[1] - 2.5) * CELL
                    if (px - x) ** 2 + (pz - z) ** 2 < CHEAT_SKIP ** 2:
                        continue
                    if can_stand(px, pz):
                        return px, pz, 0.0
    return None


def _car_park_spot(x, z):
    """At the edge of the nearest car park, on the street, looking in across
    it. The block hash first: one in PARK_ODDS, before anything costs."""
    bi0, bj0 = int(x / (XP * CELL)), int(z / (ZP * CELL))
    for r in range(0, 60):
        for bi in range(bi0 - r, bi0 + r + 1):
            for bj in (bj0 - r, bj0 + r) if r else (bj0,):
                if not car_park_block(bi, bj):
                    continue
                for i in range(bi * XP, bi * XP + XP):
                    j = bj * ZP + ZP // 2
                    if not car_park_at(i, j) or car_park_at(i - 1, j):
                        continue
                    px, pz = (i - 0.5) * CELL, (j + 0.5) * CELL
                    if (px - x) ** 2 + (pz - z) ** 2 < CHEAT_SKIP ** 2:
                        break
                    if can_stand(px, pz):
                        return px, pz, math.pi * 0.5
                    break
    return None


def _escape_spot(x, z):
    """In the alley at the foot of a fire escape that goes all the way up,
    a couple of steps back and facing it: walk forward and you are climbing."""
    ci = int(x / CELL + BIG) - BIG
    cj = int(z / CELL + BIG) - BIG
    for i, j in _rings(ci, cj, CHEAT_RINGS):
        for f in range(4):
            if _mix(i, j * 4 + f, 1931) % CLIMB_ODDS or not climbable(i, j, f):
                continue
            px, _, pz = face_point(i, j, f, CELL * 0.5, 2.4, 0.0)
            if (px - x) ** 2 + (pz - z) ** 2 < CHEAT_SKIP ** 2:
                continue
            if can_stand(px, pz):
                nx, nz = FACES[f]
                return px, pz, math.atan2(-nx, -nz)
    return None


def _tower_spot(x, z):
    """Outside the lobby of the nearest sky deck, a few steps back, facing
    the door: one step forward and you are in the lift."""
    ci = int(x / CELL + BIG) - BIG
    cj = int(z / CELL + BIG) - BIG
    for i, j in _rings(ci, cj, CHEAT_RINGS):
        if _mix(i, j, 1907) % TOWER_ODDS or is_open(i, j):
            continue
        t = lot(i, j)["tower"]
        if t is None:
            continue
        px, _, pz = face_point(i, j, t["door"], t["u"], CASINO_REACH + 2.4, 0.0)
        if (px - x) ** 2 + (pz - z) ** 2 < CHEAT_SKIP ** 2:
            continue
        if can_stand(px, pz):
            nx, nz = FACES[t["door"]]
            return px, pz, math.atan2(-nx, -nz)
    return None


def _el_spot(x, z):
    """Under the elevated, on the pavement by a column, looking along it.
    The next press goes to the next elevated avenue over."""
    k0 = int(x / (XP * CELL))
    for step in range(0, 400):
        k = k0 + (step + 1) // 2 * (1 if step % 2 else -1)
        span = el_span(k)
        if span is None:
            continue
        px = span[0] * CELL + 1.3
        if abs(px - x) < CHEAT_SKIP:
            continue
        for back in range(0, 60):
            pz = z + back * CELL
            if can_stand(px, pz) and el_runs(px, pz) and road_at(
                    int(px / CELL + BIG) - BIG, int(pz / CELL + BIG) - BIG):
                return px, pz, 0.0
    return None


def _hwy_spot(x, z):
    """Out on a cross street, forty units from the highway, looking down the
    street at it going over: the deck a band across the gap between the
    buildings, the traffic sliding along the top of it. From right beside
    it, looking along, it is a wall of beams overhead and reads as nothing;
    at much of an angle the buildings hide it. The next press, the next
    highway over."""
    k0 = int(x / (XP * CELL))
    b0 = int(z / (ZP * CELL))
    for step in range(0, 600):
        k = k0 + (step + 1) // 2 * (1 if step % 2 else -1)
        span = hwy_span(k)
        if span is None:
            continue
        xm = (span[0] + span[1] * 0.5) * CELL
        if abs(xm - x) < CHEAT_SKIP + 30.0:
            continue
        for b in range(b0, b0 + 12):
            cz = _crossing(0, b)
            if cz is None:
                continue
            for side in (-1.0, 1.0):
                px = xm + side * 40.0
                if can_stand(px, cz):
                    return px, cz, math.atan2(xm - px, 6.0)
    return None


def _ramen_spot(x, z):
    """Across the lane from the nearest ramen shop, facing it - a step or two
    in is the counter. Skips the one you are at, so a second press finds
    another."""
    ci = int(x / CELL + BIG) - BIG
    cj = int(z / CELL + BIG) - BIG
    for i, j in _rings(ci, cj, CHEAT_RINGS):
        if is_open(i, j):
            continue
        for f in range(4):
            if _mix(i, j * 4 + f, 1601) % RAMEN_ODDS or not ramen_at(i, j, f):
                continue
            px, pz = ramen_door(i, j, f)
            if (px - x) ** 2 + (pz - z) ** 2 < CHEAT_SKIP ** 2:
                continue
            # Back across the lane, to see the front: two steps from the
            # counter, which is the way in.
            nx, nz = FACES[f]
            for back in (4.0, 3.8, 3.6):
                q = face_point(i, j, f, CELL * 0.5, back, 0.0)
                if can_stand(q[0], q[2]):
                    return q[0], q[2], math.atan2(-nx, -nz)
    return None


def _manhole_spot(x, z):
    """Back along the street from the nearest steaming manhole, looking at
    it. Skips the one at hand, so a second press finds another."""
    ci = int(x / CELL + BIG) - BIG
    cj = int(z / CELL + BIG) - BIG
    for i, j in _rings(ci, cj, CHEAT_RINGS):
        if _mix(i, j, 3101) % MANHOLE_ODDS:
            continue
        mh = manhole_at(i, j)
        if mh is None or not mh[2]:
            continue
        if (mh[0] - x) ** 2 + (mh[1] - z) ** 2 < CHEAT_SKIP ** 2:
            continue
        # Seven back: nearer and the cover is under the bottom of the screen,
        # since the camera cannot look down.
        for back in (7.0, 6.0):
            for ax, az in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                sx, sz = mh[0] - ax * back, mh[1] - az * back
                if can_stand(sx, sz) and road_at(int(sx / CELL + BIG) - BIG,
                                                 int(sz / CELL + BIG) - BIG):
                    return sx, sz, math.atan2(ax, az)
    return None


def find_place(x, z, kind):
    """Somewhere of this kind to stand, and which way to face. None if there is
    none within reach - the panel says so rather than the search running on."""
    if kind == "start":
        sx, sz = start_position()
        return sx, sz, best_yaw(sx, sz)
    if kind == "street":
        return _long_street(x, z)
    if kind == "far":
        return _far_away(x, z)
    if kind == "inside":
        return _doorway(x, z, 911, "casino")
    if kind == "clubdoor":
        return _doorway(x, z, 909, "club")
    if kind == "ramen":
        return _ramen_spot(x, z)
    if kind == "manhole":
        return _manhole_spot(x, z)
    if kind == "highway":
        return _hwy_spot(x, z)
    if kind == "el":
        return _el_spot(x, z)
    if kind == "tower":
        return _tower_spot(x, z)
    if kind == "escape":
        return _escape_spot(x, z)
    if kind == "carpark":
        return _car_park_spot(x, z)
    if kind == "cinema":
        return _doorway(x, z, 1961, "cinema")
    if kind == "diner":
        return _diner_door(x, z)
    if kind == "arcade":
        return _doorway(x, z, 2501, "arcade", ARCADE_ODDS)
    if kind == "temple":
        return _temple_spot(x, z)
    if kind == "exchange":
        return _doorway(x, z, 2701, "exchange", EXCHANGE_ODDS)
    if kind == "billboard":
        return _billboard_spot(x, z)
    if kind == "claw":
        return _claw_spot(x, z)
    if kind == "striker":
        return _claw_spot(x, z, striker_spot)
    if kind == "roofparty":
        return _roof_party_spot(x, z)
    if kind == "lighthousedoor":
        return _lighthouse_door_spot(x, z)
    if kind == "pleasurepier":
        return _pleasure_pier_spot(x, z)
    if kind == "police":
        return _police_spot(x, z, now_hint())
    if kind in ("tunnel", "longtunnel"):
        return _tunnel_spot(x, z, "short" if kind == "tunnel" else "long")
    if kind in ("woods", "rave", "lake"):
        return _woods_spot(x, z, kind)
    if kind in ("bank", "pier", "bridge", "leaner", "carnival", "grand",
                "lighthouse"):
        return _water_spot(x, z, kind)
    if kind.startswith("@"):
        return _district_spot(x, z, int(kind[1:]))

    ci = int(x / CELL + BIG) - BIG
    cj = int(z / CELL + BIG) - BIG
    skip = CHEAT_SKIP ** 2
    for i, j in _rings(ci, cj, CHEAT_RINGS):
        if kind == "club":
            hit = _door_spot(i, j, 909, "club")
        elif kind == "casino":
            hit = _door_spot(i, j, 911, "casino")
        elif kind == "crossroads":
            hit = _crossroads_spot(i, j)
        elif kind == "yokocho":
            hit = _alley_spot(i, j, False, True)
        else:
            hit = _alley_spot(i, j, kind == "deadend", False)
        if hit is not None and (hit[0] - x) ** 2 + (hit[1] - z) ** 2 >= skip:
            return hit
    return None


def draw_cheats(ch, co, note):
    """The panel, drawn over the live frame rather than instead of it, so that
    what you change to the weather happens in front of you.

    Four columns, by what you go somewhere for - CHEAT_GROUPS - then the
    parts of town, and the weather, the sky and the nights. It was once one
    long column that grew taller than the terminal and quietly stopped
    opening at all. There is a test that it opens at 80x24."""
    height, width = len(ch), len(ch[0])
    names = {kind: (k, name) for k, name, kind in CHEAT_PLACES}
    groups = {g: [("", g)] + [names[kind] for kind in kinds]
              for g, kinds in CHEAT_GROUPS}
    gap = [("", "")]
    left = groups["NIGHTLIFE"] + [("/", "closing time")] + gap + groups["FUN"] \
        + gap + groups["EAT"]
    middle = groups["MONEY"] + [("+", "+$1000"), ("%", "jackpot next")]
    middle += gap + [("", "PARTS OF TOWN")] + [(d["key"], d["name"]) for d in DISTRICTS]
    right = groups["AROUND TOWN"] + gap + groups["OUT OF TOWN"] + gap + groups["VIEWS"]
    sky = [("", "WEATHER & SKY"),
           ("w", weather_name()), ("L", "strike now"),
           ("s", "sky " + clouds_name()), ("a", "people " + crowd_name()),
           (">", "traffic " + traffic_name()),
           ("", ""), ("", "NIGHTS"),
           ("n", "the next one"), ("u", "a strange night"),
           ("z", "a lantern night"), ("!", "fireworks night"), ("@", "dawn"),
           ("", ""), ("`", "close")]
    columns = (left, middle, right, sky)

    col = 18
    rows = max(len(c) for c in columns)
    w, h = col * 4 + 3, rows + (3 if note else 2)
    if width < w + 4 or height < h + 2:
        return                          # no room; the city is more use
    x0, y0 = 2, 1
    for r in range(h):
        for c in range(w):
            corner = r in (0, h - 1) and c in (0, w - 1)
            side = r in (0, h - 1) or c in (0, w - 1)
            ch[y0 + r][x0 + c] = ("+" if corner else
                                  "-" if r in (0, h - 1) else
                                  "|" if side else " ")
            co[y0 + r][x0 + c] = GOLD_DIM if side else 0
    for n, column in enumerate(columns):
        cx = x0 + 2 + n * col
        for r, (k, label) in enumerate(column):
            y = y0 + 1 + r
            if k:
                _text(ch, co, y, cx, k, GOLD)
                _text(ch, co, y, cx + 2, label[:col - 3], HUD)
            elif label:
                _text(ch, co, y, cx, label[:col - 1], GOLD)
    if note:
        _text(ch, co, y0 + h - 2, x0 + 2, note[:w - 4], FLASH)


def _beam(ch, co, x0, y0, ang, y1, attr):
    """One laser, from a moving head on the truss down into the crowd."""
    height, width = len(ch), len(ch[0])
    dx = math.tan(ang) * 2.0
    glyph = "\\" if dx > 0.7 else ("/" if dx < -0.7 else "|")
    for y in range(y0, min(y1, height)):
        x = int(round(x0 + (y - y0) * dx))
        if 0 <= x < width and ch[y][x] == " ":
            ch[y][x] = glyph
            co[y][x] = attr


COOK = [
    " ___ ",
    "(___)",
    " (o) ",
    "/|=|\\",
    " |=| ",
]
DINER = [
    " ,-. ",
    "(   )",
    "/|#|\\",
]
BOWL = [
    "\\~~~~~~~~/",
    " \\______/ ",
]


def render_ramen(shop, width, height, now, since):
    """Sat at the counter.

    The noren over the door behind you is at the top of the picture, then the
    menu board, the back wall with the pots going and the cook between them,
    the counter, the others along it with their heads down, and your own
    place in front of you - empty when you sit, and a bowl a few seconds
    later. Everything steams. Nothing here is on a beat: this is the one room
    in the city that is quiet."""
    ch = [[" "] * width for _ in range(height)]
    co = [[0] * width for _ in range(height)]
    t = now - since
    m = shop["seed"]
    warm = tone_colour("warm", shop["tone"])
    cx = (width - 1) // 2
    served = t >= RAMEN_SERVE

    if width < 44 or height < 18:
        _text(ch, co, height // 2, 1, "~ at the ramen counter ~", warm)
        _text(ch, co, min(height - 1, height // 2 + 1), 1,
              "a bowl, steaming" if served else "irasshaimase!", BULB)
        _text(ch, co, min(height - 1, height // 2 + 3), 1, "s to leave", GOLD_DIM)
        return ch, co

    # The noren: split cloth panels across the top, moving a little.
    for x in range(width):
        k = x // 7
        sway = int(1.5 * math.sin(now * 0.9 + k))
        edge = (x + sway) % 7 == 0
        for y in (0, 1, 2):
            if not edge:
                ch[y][x] = "#" if y < 2 else "~"
                co[y][x] = ROU_RED
    _text(ch, co, 1, cx - 4, " RAMEN ", FLASH)

    # The menu board, the prices in yen, and a lantern either side of it.
    items = RAMEN_MENU
    bw = max(len("%-10s %5d" % it) for it in items) + 4
    bx = cx - bw // 2
    _text(ch, co, 4, bx, "." + "-" * (bw - 2) + ".", BARK)
    for r, (name, yen) in enumerate(items[:3]):
        _text(ch, co, 5 + r, bx, "|", BARK)
        _text(ch, co, 5 + r, bx + 2, "%-10s %5d" % (name, yen), STAR)
        _text(ch, co, 5 + r, bx + bw - 1, "|", BARK)
    _text(ch, co, 8, bx, "'" + "-" * (bw - 2) + "'", BARK)
    for lx in (bx - 6, bx + bw + 4):
        if 0 <= lx < width - 3:
            _text(ch, co, 4, lx + 1, "|", BARK)
            _text(ch, co, 5, lx, "(o)", EMBER_HOT)
            _text(ch, co, 6, lx, "(o)", EMBER_HOT)
            _text(ch, co, 7, lx + 1, "v", EMBER)

    # The back wall: the stock pots, the cook between them, and steam off
    # everything - drifting up and thinning, a column at a time.
    bar = height - 6
    wall = max(13, bar - 9)      # the back wall sits just behind the counter
    pots = (cx - 22, cx + 14)
    for px in pots:
        if 0 <= px and px + 9 < width:
            _text(ch, co, wall - 1, px, "(________)", CONCRETE)
            _text(ch, co, wall, px, "|________|", CONCRETE)
    cook_x = cx - 2 + int(round(3.0 * math.sin(now * 0.6 + (m & 7))))
    for r, line in enumerate(COOK):
        _text(ch, co, wall - 4 + r, cook_x, line, STAR if r < 2 else CURB)
    ladle = int(now * 2.0) % 4
    _text(ch, co, wall - 1, cook_x + (5 if ladle < 2 else -2), "o~" if ladle < 2
          else "~o", CONCRETE)

    def steam(x, y0, n, seed):
        for k in range(n):
            y = y0 - k
            drift = int(round(1.2 * math.sin(now * 1.3 + k * 0.9 + seed)))
            if 0 <= y < height and 0 <= x + drift < width:
                if (int(now * 4) + k + seed) % 5 == 0:
                    continue
                ch[y][x + drift] = "(" if k % 2 else ")"
                co[y][x + drift] = HAZE if k > 1 else STAR_DIM

    for px in pots:
        for s in range(3):
            steam(px + 2 + s * 3, wall - 2, 4, px + s)

    # The counter, the others along it, heads down over their bowls, each
    # slurping on their own count.
    for x in range(width):
        ch[bar][x] = "="
        co[bar][x] = BARK
        ch[bar + 1][x] = "_" if x % 9 else "|"
        co[bar + 1][x] = BARK
    for k, sx in enumerate(range(3, width - 6, 12)):
        if abs(sx + 2 - cx) < 10:
            continue                     # your place
        bob = 1 if math.sin(now * 2.1 + k * 1.7) > 0.6 else 0
        for r, line in enumerate(DINER):
            _text(ch, co, bar - 3 + r + bob, sx, line, warm if r == 0 else CURB)
        _text(ch, co, bar - 1, sx + 5, "u", CONCRETE)
        steam(sx + 5, bar - 2, 2, k * 3)

    # Your place. Chopsticks first; the bowl when it comes.
    if served:
        for r, line in enumerate(BOWL):
            _text(ch, co, bar - 2 + r, cx - 5, line, STAR if r == 0 else CONCRETE)
        _text(ch, co, bar - 3, cx - 1, "@", EMBER_HOT)     # the egg
        _text(ch, co, bar - 3, cx + 2, "=", GRASS)          # and the nori
        for s in range(3):
            steam(cx - 2 + s * 2, bar - 4, 4, s * 5)
        say = "o-machi-dou sama!" if t < RAMEN_SERVE + 2.5 else ""
    else:
        _text(ch, co, bar - 1, cx - 1, "||", CONCRETE)
        say = "irasshaimase!" if t < 2.5 else "..."
    if say:
        _text(ch, co, wall - 6, cx - len(say) // 2, say, BULB)

    _text(ch, co, height - 1, max(1, cx - 10), "-- the way out (s) --", GOLD_DIM)
    return ch, co


FILM_SCENES = 6
SCENE_LEN = 9.0         # seconds a scene
FILM_LINES = [("SHE", "You came back."), ("HIM", "I never left."),
              ("SHE", "The rain won't stop."), ("HIM", "It never does, here."),
              ("SHE", "Where will you go?"), ("HIM", "Wherever the last train goes.")]


def film_frame(title, t, w, h):
    """One frame of the picture: a list of h strings of w characters, and how
    bright it is overall (0..1) - which is what lights the audience. Six
    scenes on a loop: the title, rain on a window, a night drive, two people
    talking, the city, and THE END. An action title is the other picture."""
    if title in ACTION_TITLES:
        return action_frame(title, t, w, h)
    g = [[" "] * w for _ in range(h)]

    def put(x, y, c):
        if 0 <= x < w and 0 <= y < h:
            g[y][x] = c

    def text(y, s):
        for k, c in enumerate(s):
            put((w - len(s)) // 2 + k, y, c)

    t = t % (FILM_SCENES * SCENE_LEN)        # a loop, so it is the same film
    scene, s = divmod(t, SCENE_LEN)
    scene = int(scene) % FILM_SCENES
    bright = 0.3
    if scene == 0:                        # the title, on black, with grain
        text(h // 2 - 1, title)
        text(h // 2 + 1, "-" * len(title))
        for k in range(w * h // 40):
            m = _mix(k, int(t * 12), 1971)
            put(m % w, (m >> 8) % h, ".")
        bright = 0.2
    elif scene == 1:                      # rain on a window, a lamp outside
        mx, my = w // 2, h // 2
        for y in range(h):
            put(mx, y, "|")
        for x in range(w):
            put(x, my, "-")
        put(w - 6, 2, "o")
        for k in range(w // 2):
            m = _mix(k, 0, 1973)
            x = m % w
            y = int((t * (6 + m % 5) + (m >> 8) % h)) % h
            put(x, y, "'")
            put(x, y - 1, ":")
        bright = 0.35
    elif scene == 2:                      # a night drive
        hz = h // 3
        for y in range(hz + 1, h):
            spread = (y - hz) * w // (2 * max(1, h - hz)) + 1
            put(w // 2 - spread, y, "/")
            put(w // 2 + spread, y, "\\")
            if int(y * 2 - t * 8) % 4 < 2:
                put(w // 2, y, "|")
        for k in range(w // 3):
            m = _mix(k, 1, 1975)
            put((m % w), hz - (m >> 8) % 2, "." if m % 3 else "o")
        drift = int(2 * math.sin(t * 0.6))
        put(w // 2 - 2 + drift, hz + 2, "o")
        put(w // 2 + 2 + drift, hz + 2, "o")
        bright = 0.45
    elif scene == 3:                      # two of them, and what they say
        for (cx, face) in ((w // 3, ">"), (2 * w // 3, "<")):
            for r, line in enumerate([" ___ ", "(   )", "|" + face * 3 + "|",
                                      " | | ", "/   \\"]):
                for k, c in enumerate(line):
                    if c != " ":
                        put(cx - 2 + k, h // 2 - 3 + r, c)
        who, said = FILM_LINES[int(s / (SCENE_LEN / len(FILM_LINES)))
                               % len(FILM_LINES)]
        text(h - 2, said)
        bright = 0.4
    elif scene == 4:                      # the city, a window going out
        for x in range(w):
            top = h // 2 + (_mix(x // 3, 0, 1977) % (h // 2))
            for y in range(top, h):
                lit = _mix(x, y, 1979) % 7 == 0 and (_mix(x, y, 1981)
                                                     + int(t)) % 9
                put(x, y, "o" if lit else "#")
            put(x, top, "_")
        put(w - 8, 2, "(")
        put(w - 7, 2, ")")
        bright = 0.5
    else:                                 # THE END, fading
        text(h // 2, "THE END")
        if s > SCENE_LEN * 0.6:
            g = [[" "] * w for _ in range(h)]
        bright = 0.15
    flicker = 0.85 + 0.15 * math.sin(t * 23.0) * math.sin(t * 7.0)
    return ["".join(r) for r in g], bright * flicker


def _film_pick(i, j):
    """What a cinema is showing: the drama or, one in two, the action."""
    titles = ACTION_TITLES if _mix(i, j, 1971) % 2 else FILM_TITLES
    return titles[_mix(i, j, 1967) % len(titles)]


ACTION_TAGS = {"OVERDRIVE": "ONE NIGHT. ONE CITY. NO BRAKES.",
               "BURN ZONE": "THIS TIME IT'S PERSONAL. AGAIN.",
               "STEEL NERVE": "HE DOESN'T DO SEQUELS. UNTIL NOW.",
               "ZERO HOUR": "THE CLOCK IS TICKING. SO IS HE."}
ACTION_QUIPS = ["Guess the party's over.", "I was off duty anyway.",
                "Somebody call a tow truck.", "That was my favourite car.",
                "Told you. No brakes."]
ACTION_BLOWS = ["POW!", "WHAM!", "KRAK!", "BIFF!", "THUD!"]
# What the screen shows in colour, when an action picture is on - the
# drama is black and white, and this is not.
ACTION_INK = {"@": "fire", "%": "fire", "*": "spark", "!": "spark"}

HERO_CAR = ["  ____   ", " /|__|\\_ ", "(o)---(o)"]
VAN = [" ______  ", "|[]  []|>", "(o)--(o) "]
RUN = ([" o ", "/|\\", "/ \\"], [" o ", "<|-", " |\\"])
LEAP = [" o/", "/| ", "/  "]
COPTER = (["----+----", " __|__   ", "(__[]_>==", " '  '    "],
          ["  --+--  ", " __|__   ", "(__[]_>==", " '  '    "])


def action_frame(title, t, w, h):
    """One frame of the action picture, the drama's other half: the title
    slammed up in big letters, a car chase with the van shooting, a leap
    between rooftops under a helicopter's searchlight, a fist fight with the
    blows written up in the air, an explosion the hero walks away from
    without looking back, and the sequel. Six scenes on the drama's loop, so
    one cinema's film and another's keep the same time."""
    g = [[" "] * w for _ in range(h)]

    def put(x, y, c):
        x, y = int(x), int(y)
        if 0 <= x < w and 0 <= y < h:
            g[y][x] = c

    def text(y, s_, x=None):
        x0 = (w - len(s_)) // 2 if x is None else int(x)
        for k, c in enumerate(s_):
            put(x0 + k, y, c)

    def sprite(x, y, rows):
        for r, line in enumerate(rows):
            for k, c in enumerate(line):
                if c != " ":
                    put(x + k, y + r, c)

    t = t % (FILM_SCENES * SCENE_LEN)
    scene, s_ = divmod(t, SCENE_LEN)
    scene = int(scene) % FILM_SCENES
    seed = _mix(len(title), ord(title[0]), 2911)
    bright = 0.4
    shake = 0
    if scene == 0:                        # the title, slammed up
        if s_ > 0.4:
            word = title.replace(" ", "  ")
            if len(word) * 4 <= w and h >= 9:
                x0 = (w - len(word) * 4) // 2
                for dx, dy, _ in big_cells(word):
                    put(x0 + dx, h // 2 - 4 + dy, "#")
            else:
                text(h // 2 - 2, title)
            if s_ < 1.3:
                shake = 1 if int(s_ * 20) % 2 else -1
                for k in range(w // 2):          # sparks off the slam
                    m = _mix(k, int(s_ * 10), 2913)
                    r = (s_ - 0.4) * 30.0
                    a = (m % 628) / 100.0
                    put(w / 2 + math.cos(a) * r * ((m >> 9) % 100) / 100.0,
                        h / 2 + math.sin(a) * r * 0.4 * ((m >> 9) % 100) / 100.0,
                        "*")
                bright = 0.9 - (s_ - 0.4) * 0.5
        if s_ > 2.5:
            text(h - 2, ACTION_TAGS.get(title, "NO BRAKES."))
    elif scene == 1:                      # the chase
        road = h - 2
        for x in range(w):
            put(x, road - 4, "_")
            if (x + int(s_ * 30)) % 8 < 4:
                put(x, road, "-")
            top = road - 5 - _mix((x + int(s_ * 6)) // 5, 0, 2915) % max(1, h // 3)
            if (x + int(s_ * 6)) % 5 == 0:
                for y in range(top, road - 4):
                    put(x, y, "|")
            put(x, top, "_")
        for k in range(4):                # lamp posts, going past fast
            x = (k * w / 4.0 - s_ * 55.0) % (w + 10) - 5
            for y in range(road - 7, road - 3):
                put(x, y, "|")
            put(x, road - 8, "o")
        bounce = int(s_ * 9) % 2
        hx = w * 0.55 + 4 * math.sin(s_ * 1.2)
        vx = w * 0.12 + 5 * math.sin(s_ * 0.9 + 1.0)
        sprite(hx, road - 3 - bounce, HERO_CAR)
        sprite(vx, road - 3 - (1 - bounce), VAN)
        if (s_ * 1.7) % 1.0 < 0.3:        # the van shooting
            put(vx + 10, road - 2, "*")
            for x in range(int(vx) + 11, int(hx) - 1, 3):
                put(x, road - 2, "-")
            put(hx - 1, road - 3, "*")
            bright = 0.6
        for k in range(6):                # speed lines, in the sky over it
            m = _mix(k, int(s_ * 4), 2917)
            y = 1 + m % max(1, road - 6 - h // 3)
            x = (m >> 8) % w
            for d in range(5):
                put(x + d, y, "-")
    elif scene == 2:                      # rooftops, and the leap
        gap0, gap1 = int(w * 0.42), int(w * 0.58)
        r1, r2 = h - 5, h - 6
        for x in range(w):
            top = r1 if x < gap0 else (r2 if x >= gap1 else None)
            if top is None:
                continue
            put(x, top, "_")
            for y in range(top + 1, h):
                put(x, y, "|" if x in (gap0 - 1, gap1) else
                    "o" if (x % 4 == 1 and y % 2 == 0 and _mix(x, y, 2919) % 3 == 0)
                    else " ")
        p = s_ / SCENE_LEN
        if p < 0.4:
            x, y, rows = 2 + (gap0 - 4) * p / 0.4, r1 - 3, RUN[int(s_ * 8) % 2]
        elif p < 0.6:
            q = (p - 0.4) / 0.2
            x = gap0 - 2 + (gap1 - gap0 + 3) * q
            y = r1 - 3 - math.sin(q * math.pi) * 4 + (r2 - r1) * q
            rows = LEAP
            text(1, "* * *  s l o w   m o t i o n  * * *") if 0.3 < q < 0.7 else None
        else:
            q = (p - 0.6) / 0.4
            x, y, rows = gap1 + 1 + (w - gap1 - 5) * q, r2 - 3, RUN[int(s_ * 8) % 2]
        cx = w * 0.3 + w * 0.4 * math.sin(s_ * 0.4)
        sprite(cx, 1, COPTER[int(s_ * 10) % 2])
        for k in range(1, h):              # its searchlight, down on him
            f = k / float(h)
            for dx in (-1, 1):
                if _mix(k, dx, int(s_ * 5)) % 3:
                    put(cx + 3 + (x + 1 - cx - 3) * f + dx * f * 3,
                        5 + (y - 5) * f, ".")
        sprite(x, y, rows)
        bright = 0.45
    elif scene == 3:                      # the fight
        floor = h - 2
        beat = int(s_ / 1.2)
        hit = (s_ % 1.2) < 0.45
        cx = w // 2
        gone = s_ > 7.2
        hero = [" o ", "/|\\", "/ \\"]
        if hit and beat % 2 == 0 and not gone:
            hero = [" o ", "/|--", "/ \\"]
        sprite(cx - 5, floor - 3, hero)
        if gone:                          # sent flying
            q = (s_ - 7.2) / 1.8
            sprite(cx + 2 + q * w * 0.4, floor - 3 - math.sin(q * math.pi) * 4,
                   ["\\o/", " | ", "/ \\"])
            text(2, "K . O .")
        else:
            villain = [" @ ", "/|\\", "/ \\"] if not (hit and beat % 2) else \
                [" @ ", "--|\\", "/ \\"]
            sprite(cx + 2, floor - 3, villain)
            if hit:
                blow = ACTION_BLOWS[(beat + seed) % len(ACTION_BLOWS)]
                bx = cx - 2 - len(blow) // 2 + (beat % 3 - 1) * 3
                text(floor - 7, "\\" + "/" * (len(blow)) + "/", bx - 1)
                text(floor - 6, "> " + blow + " <", bx - 2)
                text(floor - 5, "/" + "\\" * (len(blow)) + "\\", bx - 1)
                bright = 0.55
        for x in range(w):
            put(x, floor, "=")
    elif scene == 4:                      # the explosion, and the walk away
        ground = h - 2
        bx = w // 2
        boom = s_ - 1.5
        if boom < 0:
            sprite(bx - 4, ground - 3, HERO_CAR)
            text(1, "3 . . . 2 . . . 1" if s_ > 0.4 else "")
        else:
            r = min(boom * w * 0.16, w * 0.45)
            for k in range(int(80 + r * 6)):     # the fireball
                m = _mix(k, int(boom * 8), 2921)
                a = (m % 628) / 100.0
                d = r * math.sqrt(((m >> 10) % 1000) / 1000.0)
                c = "@" if d < r * 0.5 else "%" if d < r * 0.85 else "*"
                if boom > 3.5 and (m >> 4) % 3 == 0:
                    c = "."                       # smoke now
                put(bx + math.cos(a) * d, ground - 3 - abs(math.sin(a)) * d * 0.45, c)
            for k in range(14):                  # bits of car, coming down
                m = _mix(k, 3, 2923)
                vx_ = ((m % 200) - 100) / 100.0 * w * 0.12
                vy = 3.0 + (m >> 8) % 5
                put(bx + vx_ * boom, ground - 3 - (vy * boom - 1.5 * boom * boom), "#")
            if boom < 1.2:
                shake = 1 if int(boom * 20) % 2 else -1
            bright = max(0.45, 1.0 - boom * 0.25)
        # Him, walking towards you, not looking back.
        q = min(1.0, s_ / SCENE_LEN * 1.4)
        big = ([" ___ ", "[=_=]", "/|#|\\", " | | "] if q > 0.5
               else [" o ", "/|\\", "/ \\"])
        sprite(bx + w * 0.18 - len(big[0]) // 2 + (int(s_ * 3) % 2),
               ground - len(big) + 1, big)
        if s_ > 5.0:
            text(h - 1, ACTION_QUIPS[seed % len(ACTION_QUIPS)])
    else:                                 # the end, and the sequel
        if s_ < 3.5:
            text(h // 2, "THE END")
        elif s_ < 5.5:
            text(h // 2, "...OR IS IT?")
        else:
            text(h // 2 - 1, title + " 2")
            text(h // 2 + 1, "COMING SOON")
            if int(s_ * 2) % 2:
                text(h // 2 + 3, "!!!")
        bright = 0.2
    if shake:
        g = [row[-shake:] + row[:-shake] if shake > 0 else row[1:] + row[:1]
             for row in g]
    flicker = 0.9 + 0.1 * math.sin(t * 23.0) * math.sin(t * 7.0)
    return ["".join(r) for r in g], min(1.0, bright * flicker)


DINER_MENU = ["REAL COFFEE ...... 9 CR", "SYNTH-PIE ........ 4 CR",
              "NOODLES, VAT ..... 6 CR", "EGGS, PRINTED .... 3 CR"]


def render_diner(width, height, now, since):
    """On a stool at the counter, some decades on.

    Neon strip along the ceiling, one tube on the blink; the window onto a
    wet street of holo-ads with the odd car going over; the menu board,
    glitching, priced in credits; the coffee machine, all chrome and little
    lights; a robot arm working the grill along its rail; three others along
    the counter keeping to themselves, one in a visor and one with an eye
    that is not an eye. A few seconds after you sit down the drone comes over
    with the pot, and says what diners have always said."""
    ch = [[" "] * width for _ in range(height)]
    co = [[0] * width for _ in range(height)]
    t = now - since
    n = len(NEON)
    cyan, magenta = NEON[2], NEON[1]
    if width < 44 or height < 18:
        _text(ch, co, height // 2, 1, "~ at the diner, 24/7 ~", cyan[0])
        _text(ch, co, height // 2 + 1, 1, "coffee's coming" if t < DINER_POUR
              else "a cup of coffee, steaming", GOLD_DIM)
        return ch, co
    cx = width // 2
    # The ceiling: strip lights, one of them going.
    for x in range(1, width - 1):
        seg = x // 9
        if x % 9 == 8:
            continue
        dead = seg == 3 and _mix(seg, int(now * 12), 2419) % 4 == 0
        ch[1][x], co[1][x] = "=", cyan[1] if dead else cyan[0]
    # The window, the left third: towers, holo-ads, a car going over, rain.
    wx1 = width // 3
    for y in range(2, height - 6):
        _text(ch, co, y, wx1, "|", CONCRETE)
    for x in range(1, wx1):
        top = 4 + _mix(x // 5, 0, 2421) % 7          # a tower every five columns
        for y in range(top, height - 8):
            if x % 5 == 0 or y == top:
                ch[y][x], co[y][x] = ("|" if x % 5 == 0 else "_"), HAZE
            elif y % 2 == 0 and _mix(x, y, 2425) % 5 == 0:
                ch[y][x], co[y][x] = ".", NEON[_mix(x, y, 2427) % n][1]
    for k, ad in enumerate(("NOODLE", "SYNTH", "EAT")):
        ax = 2 + (k * 7) % max(1, wx1 - 8)
        ay = 5 + k * 3
        if ay < height - 9 and _mix(k, int(now * 3), 2423) % 7:
            _text(ch, co, ay, ax, ad[:max(0, wx1 - ax - 1)], NEON[(k * 3 + 1) % n][0])
    car = (now * 14.0) % (wx1 * 3)
    if car < wx1 - 3:
        _text(ch, co, 3, 1 + int(car), "=o", FLASH)
    for y in range(2, height - 6):
        if y == height - 8:
            for x in range(1, wx1):
                ch[y][x], co[y][x] = "_", STREET        # the kerb outside
    if rain_intensity(now) > 0.1:
        for k in range(wx1 * 2):
            m = _mix(k, 0, 2413)
            x = 1 + m % (wx1 - 1)
            y = 2 + int(now * (5 + m % 4) + (m >> 8) % height) % (height - 9)
            ch[y][x], co[y][x] = "'", RAIN
    # The menu board, glitching every few seconds.
    mx = wx1 + 3
    glitch = (now % 4.0) < 0.15
    _text(ch, co, 3, mx - 1, "+" + "-" * (len(DINER_MENU[0]) + 2) + "+", cyan[1])
    for r, line in enumerate(DINER_MENU):
        shift = (1 if r % 2 else -1) if glitch else 0
        _text(ch, co, 4 + r, mx - 1, "|", cyan[1])
        _text(ch, co, 4 + r, mx + 1 + shift, line, magenta[0] if glitch else cyan[0])
        _text(ch, co, 4 + r, mx + len(line) + 2, "|", cyan[1])
    _text(ch, co, 4 + len(DINER_MENU), mx - 1,
          "+" + "-" * (len(DINER_MENU[0]) + 2) + "+", cyan[1])
    # The coffee machine: chrome, pipes, little lights, a puff now and then.
    ux = width - 18
    for r, line in enumerate(("[=======]", "| [] [] |", "|_o_o_o_|", " |  |  | ")):
        _text(ch, co, 4 + r, ux, line, CONCRETE)
    for k in range(3):
        _text(ch, co, 6, ux + 2 + k * 2, "o", NEON[(k + int(now * 2)) % n][0])
    if int(now * 2) % 3 == 0:
        _text(ch, co, 3, ux + 4, "(", HAZE)
    # The robot arm, along its rail over the grill.
    bar = height - 6
    rail = bar - 6
    for x in range(wx1 + 2, width - 2):
        ch[rail][x], co[rail][x] = "=", CONCRETE
    ax = wx1 + 6 + int(round((width - wx1 - 16) * (0.5 + 0.5 * math.sin(now * 0.5))))
    _text(ch, co, rail, ax, "[o]", magenta[0])
    _text(ch, co, rail + 1, ax + 1, "\\", CONCRETE)
    _text(ch, co, rail + 2, ax + 2, "\\_", CONCRETE)
    if int(now * 6) % 5 == 0:
        _text(ch, co, rail + 3, ax + 3, "*", EMBER_HOT)
    # The counter, chrome with a cyan glow under it, and the stools.
    for x in range(wx1 + 1, width):
        ch[bar][x], co[bar][x] = "=", CONCRETE
        ch[bar + 1][x], co[bar + 1][x] = "-", cyan[1]
        if (x - wx1) % 7 == 3:
            _text(ch, co, bar + 2, x, "T", CONCRETE)
    # The three others: a visor, a hood, and the one with the eye.
    for k, sx in enumerate((wx1 + 4, wx1 + 18, width - 12)):
        head = (",-.", "/^\\", ",-.")[k]
        _text(ch, co, bar - 2, sx, head, BARK)
        _text(ch, co, bar - 1, sx - 1, "(   )", BARK)
        if k == 0:
            _text(ch, co, bar - 1, sx, "===", cyan[0])
        if k == 2:
            _text(ch, co, bar - 1, sx + 1, "o", ROU_RED)
        _text(ch, co, bar - 1, sx + 4, "u", CONCRETE)
    # Your place, and the drone coming round with the pot.
    ccx = (wx1 + width) // 2
    _text(ch, co, bar - 1, ccx, "(_)", STAR)
    if t >= DINER_POUR:
        if t < DINER_POUR + 2.0:
            hover = int(now * 4) % 2                 # under the arm's rail
            _text(ch, co, bar - 5 + hover, ccx, "-=o=-", magenta[0])
            _text(ch, co, bar - 4 + hover, ccx, " _[]_", CONCRETE)    # the pot
            _text(ch, co, bar - 3, ccx + 1, "|", GOLD_DIM)
            _text(ch, co, bar - 2, ccx + 1, "|", GOLD_DIM)
            say = "there you go, hon."
            _text(ch, co, bar - 8, ccx - len(say) // 2, say, cyan[0])
        for k in range(2):
            if int(now * 3 + k) % 3:
                _text(ch, co, bar - 2 - k, ccx + 1, "(" if k % 2 else ")", HAZE)
    elif t < 2.5:
        say = "be right with you."
        _text(ch, co, bar - 8, ccx - len(say) // 2, say, cyan[0])
    way = "-- the way out (s) --"
    for k, c in enumerate(way):
        x = max(1, cx - 10) + k
        if x < width:
            ch[height - 1][x], co[height - 1][x] = c, GOLD_DIM
    return ch, co


SEWER_EAT = 7.0        # seconds between one of them finishing a slice
SEWER_SAY = [("dude. close the lid.", 0), ("you want a slice?", 1),
             ("pineapple? no way.", 2), ("extra cheese. obviously.", 3),
             ("shh. someone's up there.", 0), ("this one's got anchovies!", 2)]
# Each one's headband, and the turtle sprite: head, band, shell, legs.
SEWER_BANDS = ("red", "blue", "orange", "purple")


def render_sewer(width, height, now, since, taken):
    """Down the manhole: a brick tunnel with the water going by, the ladder
    you came down with the light from the street at the top of it, pipes
    dripping - and somebody has made it home. An old couch, a television on
    the blink, fairy lights, and four turtles round a pizza box on a crate,
    eating. They look up when you come down. It is cool. Pizza?"""
    ch = [[" "] * width for _ in range(height)]
    co = [[0] * width for _ in range(height)]
    t = now - since
    band = {"red": ROU_RED, "blue": CROWN_BLUE, "orange": EMBER_HOT,
            "purple": NEON[6][0]}
    left = sewer_slices(t, taken)
    if width < 44 or height < 16:
        _text(ch, co, height // 2 - 1, 1, "~ down the sewer ~", ROU_GREEN)
        _text(ch, co, height // 2, 1, "four turtles, one pizza", GOLD_DIM)
        _text(ch, co, height // 2 + 1, 1, "%d slices left" % left, GOLD_DIM)
        return ch, co
    cx = width // 2
    floor = height - 6                       # the ledge they sit on
    # The arch, in brick, and the brick of the back wall, faintly.
    for y in range(0, floor):
        for x in range(width):
            arch = abs(x - cx) / float(cx) > 0.92 - 0.25 * (1 - y / float(floor)) ** 3
            if arch or y == 0:
                ch[y][x] = "_" if y % 2 == 0 else ("|" if (x + (y // 2) * 3) % 6 == 0
                                                   else "_")
                co[y][x] = CURB
            elif (x + (y // 2) * 3) % 6 == 0 and y % 2:
                ch[y][x], co[y][x] = "|", CONCRETE
            elif y % 2 == 0 and x % 2 == 0:
                ch[y][x], co[y][x] = "_", CONCRETE
    # A pipe along the top, dripping.
    for x in range(2, width - 2):
        ch[2][x], co[2][x] = "=", STREET
    for k in range(5):
        dx = 6 + _mix(k, 0, 3105) % max(1, width - 12)
        dy = 3 + int((now * 6 + k * 3.3) % max(1, floor - 3))
        if dy < floor:
            ch[dy][dx], co[dy][dx] = "'", RAIN
    # The ladder you came down, and the street light at the top of it.
    lx = max(3, width // 8)
    for y in range(1, height - 3):
        _text(ch, co, y, lx, "|-|" if y % 2 else "| |", CURB)
    _text(ch, co, 0, lx - 2, "(   )", BULB)
    for y in range(1, floor - 2):
        if (y + int(now * 4)) % 3 == 0:
            _text(ch, co, y, lx - 1, ".", BULB_DIM)
            _text(ch, co, y, lx + 3, ".", BULB_DIM)
    # The water going by under the ledge.
    for x in range(width):
        ch[floor][x], co[floor][x] = "=", CURB
        for y in range(floor + 1, height - 1):
            h = _mix(x - int(now * 5.0), y, 3107)
            if h % 3 == 0:
                ch[y][x], co[y][x] = "~", RAIN_FAR
            elif h % 7 == 0:
                ch[y][x], co[y][x] = "-", ROU_GREEN if h % 2 else STREET
    # Fairy lights strung along the wall over them.
    for x in range(lx + 6, width - 4):
        y = 5 + int(1.5 * math.sin((x - lx) * 0.25))
        ch[y][x], co[y][x] = "-", CONCRETE
        if x % 4 == 0:
            ch[y + 1][x] = "o"
            co[y + 1][x] = NEON[(x // 4 + int(now * 1.5)) % len(NEON)][0]
    # The couch at the back, and the television on a crate, on the blink.
    tvx = width - 18
    for r, line in enumerate((" ________ ", "|.:.:.:.:|", "|:.:.:.:.|", "|________|",
                              "  [====]  ")):
        _text(ch, co, floor - 9 + r, tvx, line, CONCRETE if r in (0, 3, 4) else
              (STAR if (r + int(now * 9)) % 3 else HAZE))
    couch = ("  ______________ ", " (______________)", "(|              |)",
             " '--------------' ")
    for r, line in enumerate(couch):
        _text(ch, co, floor - 4 + r, cx - 26, line, BARK)
    # The pizza, in its box, on a crate in the middle.
    px = cx - 6
    _text(ch, co, floor - 6, px, " __________ ", CURB)
    pie = " (" + "".join("o" if k < left else " " for k in range(8)) + ") "
    _text(ch, co, floor - 5, px, "|" + pie + "|", GOLD_DIM)
    for k in range(8):
        if k < left:
            _text(ch, co, floor - 5, px + 3 + k, "o" if k % 2 else "*",
                  ROU_RED if k % 2 else GOLD)
    _text(ch, co, floor - 4, px, "|__________|", CURB)
    _text(ch, co, floor - 3, px + 1, "[ PIZZA! ]", BARK)
    _text(ch, co, floor - 2, px + 1, "[________]", BARK)
    _text(ch, co, floor - 1, px + 1, "|        |", BARK)
    # The four of them round it, each eating on their own count.
    looking = t < 3.0
    spots = (cx - 22, cx - 13, cx + 9, cx + 18)
    for n, (x, name) in enumerate(zip(spots, SEWER_BANDS)):
        phase = (t * 0.8 + n * 0.37) % 1.0
        bite = not looking and phase < 0.35
        y = floor - 5
        eyes = "o o" if looking else ("- -" if bite else "o o")
        _text(ch, co, y, x, " ___ ", ROU_GREEN)
        _text(ch, co, y + 1, x, "=", band[name])
        _text(ch, co, y + 1, x + 1, "(" + eyes + ")", ROU_GREEN)
        _text(ch, co, y + 1, x + 2, "=" if not looking else "o", band[name])
        _text(ch, co, y + 1, x + 4, "=" if not looking else "o", band[name])
        _text(ch, co, y + 1, x + 6, "=", band[name])
        _text(ch, co, y + 1, x + 2, eyes[0], STAR)
        _text(ch, co, y + 1, x + 4, eyes[2], STAR)
        _text(ch, co, y + 2, x + 1, " \\" + ("O" if bite else "_") + "/ ", ROU_GREEN)
        _text(ch, co, y + 3, x, "/", ROU_GREEN)
        _text(ch, co, y + 3, x + 1, "[###]", GOLD_DIM)
        _text(ch, co, y + 3, x + 6, "\\", ROU_GREEN)
        _text(ch, co, y + 4, x + 1, "_| |_", ROU_GREEN)
        # The slice in hand: up at the mouth on the bite, down in the lap
        # otherwise, a string of cheese when it comes away.
        sx = x + 6 if n < 2 else x - 1
        if bite:
            _text(ch, co, y + 1, sx, "V", GOLD)
            if phase > 0.25:
                _text(ch, co, y + 2, sx, "~", GOLD_DIM)
        elif not looking:
            _text(ch, co, y + 3, sx, ">" if n < 2 else "<", GOLD)
    # What they say.
    if looking:
        say, who = ("...", 0) if t < 1.5 else ("it's cool, it's cool. pizza?", 1)
    else:
        say, who = SEWER_SAY[int(t / 4.0) % len(SEWER_SAY)]
        if (t % 4.0) > 3.0:
            say = ""
    if say:
        bx = spots[who] + 3 - len(say) // 2
        _text(ch, co, floor - 8, max(1, min(width - len(say) - 1, bx)), say, STAR)
    _text(ch, co, height - 1, max(1, cx - 15), "-- the ladder up (s) - a slice (p) --",
          GOLD_DIM)
    return ch, co


def sewer_slices(t, taken):
    """Slices left in the box: eight, less one every SEWER_EAT seconds
    they have been at it (they leave two), less what you took."""
    eaten = min(6, int(max(0.0, t - 3.0) / SEWER_EAT))
    return max(0, 8 - eaten - taken)


# The word of God, the way Terry A. Davis had TempleOS give it: the moment
# you ask is the random number, and the number picks the words. His list was
# his own; this one is the city's.
GOD_WORDS = """
light behold river neon rain night city bridge lantern moon star dawn street
gate door window stone fire water bread salt wine oil lamp candle mercy grace
peace wrath glory kingdom servant shepherd sheep lion lamb dove raven serpent
mountain valley desert garden vine fig olive cedar harvest seed field storm
thunder lightning cloud wind dust ash gold silver iron brass crown throne
temple altar scroll word song psalm trumpet harp bell silence voice echo
wanderer stranger king prophet fool child elder widow orphan builder fisher
walk run rest wait listen remember forget forgive return arise behold shine
burn sleep wake dream watch build break heal sing weep laugh pray seek find
lost found open closed first last always never soon tomorrow yesterday today
mighty humble holy hidden faithful broken whole small great quiet loud bright
dark narrow wide deep high low far near beloved blessed weary new old true
yes no amen hallelujah verily therefore behold lo selah forever
taxi ferry tram pizza noodles coffee arcade jackpot elevator billboard pigeon
umbrella puddle siren antenna circuit compiler pixel kernel keyboard sixteen
""".split()
GOD_WORDS = list(dict.fromkeys(GOD_WORDS))   # each word once, or "behold" is likelier
GOD_KEEP = 6           # verses kept on the screen
GOD_PAUSE = 6.0        # seconds without a word, and the next one starts a new verse
GOD_VERSE = 24         # or a verse this long


def god_word(gap_ns):
    """One word, for the time since the last one was asked for, in
    nanoseconds. Each word is its own draw: no generator stands between the
    moment you pressed and the word - which is what made twelve at a time
    only one random number's worth - and nobody, the program included, can
    say what the low digits of that gap will be."""
    return GOD_WORDS[gap_ns % len(GOD_WORDS)]


def syllables(word):
    """A word cut up for singing: mer-cy, hal-le-lu-jah, a-men."""
    v = "aeiouy"
    word = re.sub(r"([%s])([^%s])([^%s])(?=[%s])" % (v, v, v, v), r"\1\2-\3", word)
    return re.sub(r"([%s])([^%s-])(?=[%s])" % (v, v, v), r"\1-\2", word)


CHOIR_BPM = 66         # slow
CHOIR_NOTES = "dJb."   # notes going up, in ASCII


def draw_choir(ch, co, x0, y0, width, now, sung):
    """The choir on its risers: two rows in white robes, mouths opening on
    the beat a breath apart, the director's hands going, notes floating up
    and away - and the words over them are whatever the terminal last said,
    sung; until it has said anything, a long a-men."""
    n = max(3, min(7, (width - x0 - 3) // 4))
    beat = now * CHOIR_BPM / 60.0
    word = syllables(sung) if sung else "a-a-a-men"
    lyric = "~ " + word + " ~"
    _text(ch, co, y0, x0 + max(0, (n * 4 - len(lyric)) // 2), lyric,
          GOLD if int(beat) % 2 == 0 else GOLD_DIM)
    for k in range(6):                              # notes going up
        age = (beat * 0.25 + k / 6.0) % 1.0
        nx = x0 + 2 + (k * 5) % max(1, n * 4 - 2) + int(math.sin(beat + k) * 1.5)
        ny = y0 + 2 - int(age * 3)
        if age < 0.85 and ny > y0:
            _text(ch, co, ny, nx, CHOIR_NOTES[k % len(CHOIR_NOTES)],
                  GOLD if age < 0.4 else GOLD_DIM)
    for row, (dy, shift) in enumerate(((2, 2), (5, 0))):
        for k in range(n - row):
            x = x0 + shift + k * 4
            y = y0 + dy
            phase = (beat + k * 0.15 + row * 0.4) % 1.0
            mouth = "o" if phase < 0.6 else ("O" if phase < 0.75 else "-")
            _text(ch, co, y, x, "(" + mouth + ")", STAR)
            _text(ch, co, y + 1, x - 1, "/|H|\\", STAR)
            _text(ch, co, y + 2, x - 1, "\"\"\"\"\"", BARK)  # the riser under them
    # The director, side on, hands going.
    up = int(beat * 2) % 2
    _text(ch, co, y0 + 4, x0 - 4, "\\o/" if up else "_o_", CURB)
    _text(ch, co, y0 + 5, x0 - 3, "|", CURB)
    _text(ch, co, y0 + 6, x0 - 4, "/ \\", CURB)


# The confession booth. The priest listens for the words he knows, and the
# city tells him the rest.
SINS = [
    (("die", "suicide", "kill myself", "end it", "hurt myself"),
     "You matter more than you know. If you are hurting, please talk to someone"
     " you trust, or a helpline near you, tonight."),
    (("steal", "stole", "rob", "shoplift"),
     "What was taken can still be given back."),
    (("lie", "lied", "lying", "liar"),
     "The truth is lighter to carry. Put the rest down."),
    (("bet", "gamble", "casino", "slot", "plinko", "horse", "race", "roulette",
      "jackpot", "blackjack"),
     "The house always wins, my child. But the house is not God."),
    (("stock", "shares", "market", "exchange", "money", "rich", "greed"),
     "Treasure on earth goes up and down every thirty seconds."),
    (("pizza", "ate", "eat", "ramen", "noodle", "coffee", "hungry", "food"),
     "Hunger is no sin. I hear there are four down a manhole who would agree."),
    (("hate", "angry", "anger", "rage", "mad"),
     "Anger is a fire you hold by the hot end."),
    (("cheat", "cheated", "menu", "teleport"),
     "Some of us walk the city. Some of us press a key."),
    (("love", "lonely", "alone", "miss"),
     "Nobody walks this city alone, even at four in the morning."),
    (("kill", "killed", "murder", "hurt"),
     "That is heavier than this booth can hold. Tell someone who can help you"
     " carry it."),
]
PENANCES = [
    "walk to the lighthouse without the menu",
    "buy a stranger a bowl of ramen",
    "sit through a whole film, the end included",
    "put one dollar in the plinko machine, and let it go",
    "say the word of God three times, whatever it turns out to be",
    "stand in the rain for a minute and think about it",
    "tip the doorman",
    "watch the lanterns go down the river on the next lantern night",
    "climb a fire escape and look at the city you are part of",
]
CONFESS_WAIT = 2.0     # seconds the priest thinks before he answers
CONFESS_LONG = 60      # the most you can type at once


def absolve(text, seed, ledger):
    """What the priest says to this. The first sin he recognises, if any;
    what the city has told him, now and then; a penance; and peace."""
    low = " ".join(re.findall(r"[a-z']+", text.lower()))
    tokens = low.split()

    def heard(w):
        # Whole words, or the start of one - "cheat" has "eat" in it, and a
        # man confessing to the menu was told hunger is no sin.
        if " " in w:
            return " " + w + " " in " " + low + " "
        return any(t == w or (len(w) >= 4 and t.startswith(w)) for t in tokens)

    said = "The city has heard worse, my child. So have I."
    for words, line in SINS:
        if any(heard(w) for w in words):
            said = line
            break
    rng = random.Random(seed)
    extra = ""
    if ledger.get("jumps", 0) and rng.random() < 0.5:
        extra = (" And the city tells me you crossed it %d time%s tonight without"
                 " walking." % (ledger["jumps"], "" if ledger["jumps"] == 1 else "s"))
    elif (ledger.get("money", STARTING_MONEY) < STARTING_MONEY - 50
          and rng.random() < 0.6):
        extra = (" You came in with a thousand dollars, I hear, and you have $%d."
                 % int(ledger["money"]))
    return "%s%s For your penance, %s. Go in peace." % (
        said, extra, PENANCES[rng.randrange(len(PENANCES))])


def render_confession(width, height, now, booth):
    """In the booth: dark wood, the lattice between you, a candle somewhere
    behind it and the shape of the priest against it, the panel sliding open
    when you sit down - and what has been said, both ways, with what you are
    typing under it."""
    ch = [[" "] * width for _ in range(height)]
    co = [[0] * width for _ in range(height)]
    t = now - booth["t0"]
    lines = []
    for who, line, at in booth["said"]:
        if who == "priest" and now < at:
            lines.append(("priest", "..."))
            continue
        words, cur = line.split(), ""
        wrap = max(10, width - 6)
        for w in words:
            if len(cur) + len(w) + 1 > wrap:
                lines.append((who, cur))
                cur = ""
            cur = (cur + " " + w).strip()
        lines.append((who, cur))
    typing = "> " + booth["text"] + ("_" if int(now * 2) % 2 else " ")
    if width < 40 or height < 14:
        _text(ch, co, 0, 1, "~ the confession booth ~", BARK)
        for r, (who, line) in enumerate(lines[-max(1, height - 4):]):
            _text(ch, co, 2 + r, 1, line[:width - 2], STAR if who == "priest" else HUD)
        _text(ch, co, height - 2, 1, typing[-(width - 2):], GOLD)
        _text(ch, co, height - 1, 1, "enter: confess  esc: out", GOLD_DIM)
        return ch, co
    # The booth round you: wood, top and sides.
    for x in range(width):
        ch[0][x], co[0][x] = "=", BARK
    for y in range(1, height - 1):
        for x in (0, 1, width - 2, width - 1):
            ch[y][x], co[y][x] = "|", BARK
    # The grille, and behind it, as the panel slides back, the priest.
    gx0, gx1 = width // 2 - 14, width // 2 + 14
    gy0, gy1 = 2, min(height // 2, 12)
    opened = min(1.0, t / 1.2)
    edge = int(gx0 + (gx1 - gx0) * opened)
    for y in range(gy0, gy1 + 1):
        for x in range(gx0, gx1 + 1):
            if y in (gy0, gy1) or x in (gx0, gx1):
                ch[y][x], co[y][x] = "#", BARK
            elif x > edge:
                ch[y][x], co[y][x] = "|", BARK              # the panel
            elif (x + y) % 2 == 0:
                ch[y][x], co[y][x] = ("+" if (x - y) % 4 == 0 else "x"), CURB
    if opened >= 1.0:
        flick = _mix(0, int(now * 7), 3301) % 4
        px, py = width // 2, gy0 + 3
        for r, part in enumerate(("  ___  ", " (   ) ", " /| |\\ ", "/ | | \\")):
            for k, c in enumerate(part):
                x, y = px - 3 + k, py + r
                if c != " " and gy0 < y < gy1 and gx0 < x < gx1:
                    ch[y][x], co[y][x] = c, STREET     # dark against the light
        cx_ = gx1 - 4
        if gy0 < gy1 - 2:
            _text(ch, co, gy1 - 2, cx_, "*'.,"[flick], EMBER_HOT)
            _text(ch, co, gy1 - 1, cx_, "|", STAR)
    # The kneeler, and what has been said.
    top = gy1 + 2
    room = height - 3 - top
    for r, (who, line) in enumerate(lines[-room:] if room > 0 else []):
        _text(ch, co, top + r, 3, line, STAR if who == "priest" else HUD)
    _text(ch, co, height - 3, 3, typing[-(width - 6):], GOLD)
    for x in range(2, width - 2):
        ch[height - 2][x], co[height - 2][x] = "_", BARK
    _text(ch, co, height - 1, max(1, width // 2 - 22),
          "-- type, enter to confess  -  esc steps out --", GOLD_DIM)
    return ch, co


def render_temple(tp, width, height, now, said, sung=None):
    """Inside: the nave going away from you between its pillars, the pews in
    rows, the stained glass down both sides throwing its colours, candles
    flickering along the altar - and on the altar an old terminal, a blue
    one, on which you can ask for the word of God."""
    ch = [[" "] * width for _ in range(height)]
    co = [[0] * width for _ in range(height)]
    n = len(NEON)
    if width < 50 or height < 18:
        _text(ch, co, 1, 1, "~ in %s ~" % tp["name"].lower(), GOLD)
        for r, line in enumerate(said[-max(1, height - 5):]):
            _text(ch, co, 3 + r, 1, line[:width - 2], CROWN_BLUE)
        _text(ch, co, height - 1, 1, "g: the word of god - s: out", GOLD_DIM)
        return ch, co
    cx = width // 2
    vy = height // 3                          # where the nave meets the altar
    # The vault: ribs from the sides up to the ridge.
    for x in range(width):
        d = abs(x - cx) / float(cx)
        y = int(vy * (d ** 1.6))
        if 0 <= y < height:
            ch[y][x], co[y][x] = ("-" if d < 0.15 else "/" if x < cx else "\\"), CURB
    # Pillars, nearer ones wider apart, and the glass between them.
    for k in range(4):
        f = (k + 1) / 5.0
        for side in (-1, 1):
            x = int(cx + side * (cx - 2) * (1.0 - f * 0.75))
            top = int(vy * ((1.0 - f * 0.75) ** 1.6)) + 1
            bot = int(vy + (height - 3 - vy) * (1.0 - f * 0.7))
            for y in range(top, min(height - 2, bot)):
                if 0 <= x < width:
                    ch[y][x], co[y][x] = "|", MOON_DIM
            gx = x - side * 2
            for y in range(top + 1, top + 1 + max(2, int(6 * (1 - f * 0.6)))):
                if 0 <= gx < width and 0 <= y < height:
                    hue = NEON[(k * 2 + y + (side > 0)) % n]
                    ch[y][gx] = "#"
                    co[y][gx] = hue[0] if _mix(gx, y, int(now * 3)) % 7 else hue[1]
    # The pews, in rows down the nave either side of the aisle.
    for r in range(5):
        y = height - 3 - r * 2
        if y <= vy + 6:
            break
        half = int((cx - 6) * (1.0 - r * 0.13))
        for side in (-1, 1):
            a, b_ = sorted((cx + side * 4, cx + side * half))
            _text(ch, co, y, a, "[" + "_" * max(0, b_ - a - 1) + "]", BARK)
    # The altar, with its candles, and the terminal on it.
    ay = vy + 5
    _text(ch, co, ay, cx - 16, "=" * 33, GOLD_DIM)
    for k in range(-14, 15, 4):
        flick = _mix(k, int(now * 8), 3211) % 3
        _text(ch, co, ay - 1, cx + k, "|", STAR)
        _text(ch, co, ay - 2, cx + k, "*'."[flick], EMBER_HOT)
    sw = min(width - 8, 60)
    sx0 = cx - sw // 2
    sy0 = max(1, vy - 7)
    rows = max(2, ay - 3 - sy0 - 1)
    _text(ch, co, sy0 - 1, sx0, "+" + "-" * (sw - 2) + "+", CONCRETE)
    for y in range(sy0, sy0 + rows):
        _text(ch, co, y, sx0, "|", CONCRETE)
        _text(ch, co, y, sx0 + sw - 1, "|", CONCRETE)
        for x in range(sx0 + 1, sx0 + sw - 1):
            ch[y][x], co[y][x] = " ", 0
    _text(ch, co, sy0 + rows, sx0, "+" + "-" * (sw - 2) + "+", CONCRETE)
    _text(ch, co, sy0, sx0 + 2, "GOD SAYS:", GOLD)
    lines = []
    for said_ in said[-GOD_KEEP:]:
        words, line = said_.split(), ""
        for w in words:
            if len(line) + len(w) + 1 > sw - 4:
                lines.append(line)
                line = ""
            line = (line + " " + w).strip()
        lines.append(line)
        lines.append("")
    for r, line in enumerate(lines[-(rows - 2):]):
        newest = r >= len(lines[-(rows - 2):]) - 3
        _text(ch, co, sy0 + 1 + r, sx0 + 2, line, CROWN_BLUE if newest else HAZE)
    if not said:
        _text(ch, co, sy0 + 2, sx0 + 2, "press g, a word at a time", CROWN_BLUE)
    if int(now * 2) % 2:
        _text(ch, co, sy0 + rows - 1, sx0 + 2, "_", CROWN_BLUE)   # the cursor
    # The choir, on the other side from the booth.
    qy = height - 10
    if qy > vy + 6 and width >= 70:
        qx = width - 30
        for y in range(qy, height - 2):
            for x in range(qx - 5, width - 1):
                ch[y][x], co[y][x] = " ", 0
        draw_choir(ch, co, qx, qy, width, now, sung)
    # The confession booth, against the wall at the side of the nave.
    bx, by = 2, height - 9
    if by > vy + 6:
        for y in range(by, by + 7):             # it stands in front of the pews
            for x in range(bx, min(width, bx + 14)):
                ch[y][x], co[y][x] = " ", 0
        for r, line in enumerate((" ___________ ", "|  _     _  |", "| |#|   |#| |",
                                  "| |#|   |#| |", "| |_|   |_| |", "|___________|")):
            _text(ch, co, by + r, bx, line, BARK)
        _text(ch, co, by + 2, bx + 5, "#", CURB)
        _text(ch, co, by + 6, bx, "c: confess", GOLD_DIM)
    _text(ch, co, height - 1, max(1, cx - 22),
          "-- g: the word of god  -  the way out (s) --", GOLD_DIM)
    return ch, co


TURNED = {
    "cinema": ["the usher holds out a hand.", "$%d a seat." % FEES["cinema"]],
    "club": ["the bouncer doesn't move.", "twenty at the door. not tonight."],
    "ramen": ["the cook taps the sign: cash only.", "$%d a bowl." % FEES["ramen"]],
    "diner": ["the drone hovers over your cup.", "$%d a coffee, hon." % FEES["diner"]],
}


def render_turned_away(kind, width, height, now):
    """What you get instead when you cannot pay for it."""
    ch = [[" "] * width for _ in range(height)]
    co = [[0] * width for _ in range(height)]
    for k, line in enumerate(TURNED[kind] + ["", "s walks back out"]):
        _text(ch, co, height // 2 - 2 + k, max(1, (width - len(line)) // 2), line,
              GOLD if k < 2 else GOLD_DIM)
    return ch, co


def render_cinema(cin, width, height, now):
    """In the back rows.

    The screen fills the top of the room between red curtains, the film on it
    in black and white; the projector's beam comes over your head, dust in it;
    and the audience sits in rows of silhouettes in front of you, lit by
    whatever is on the screen - a bright scene throws its light on them, a
    dark one leaves them as shapes."""
    ch = [[" "] * width for _ in range(height)]
    co = [[0] * width for _ in range(height)]
    t = now + cin["offset"]
    if width < 40 or height < 16:
        frame, _ = film_frame(cin["title"], t, max(10, width - 2), 3)
        _text(ch, co, 1, 1, cin["title"], GOLD)
        for r, line in enumerate(frame):
            _text(ch, co, 3 + r, 1, line, STAR)
        _text(ch, co, height - 1, 1, "s to leave", GOLD_DIM)
        return ch, co
    sx0, sx1 = 6, width - 7
    sy0, sy1 = 1, int(height * 0.6)
    fw, fh = sx1 - sx0, sy1 - sy0
    frame, bright = film_frame(cin["title"], t, fw, fh)
    colour = cin["title"] in ACTION_TITLES
    ink = {"fire": EMBER_HOT, "spark": GOLD}
    for r, line in enumerate(frame):
        for k, c in enumerate(line):
            if c != " ":
                ch[sy0 + r][sx0 + k] = c
                co[sy0 + r][sx0 + k] = (
                    ink[ACTION_INK[c]] if colour and c in ACTION_INK
                    else FLASH if bright > 0.42 else STAR)
    for x in range(sx0 - 1, sx1 + 1):            # the screen's edge
        ch[sy0 - 1][x], co[sy0 - 1][x] = "_", CONCRETE
        ch[sy1][x], co[sy1][x] = "-", CONCRETE
    for y in range(0, sy1 + 3):                  # the curtains
        for x in list(range(0, sx0 - 1)) + list(range(sx1 + 1, width)):
            ch[y][x] = "|" if (x + y // 3) % 2 else "("
            co[y][x] = ROU_RED
    # The beam, from behind you up to the screen, with dust turning in it.
    px, py = width // 2, height - 1
    for k in range(70):
        m = _mix(k, int(now * 3.0), 1983)
        corner = (sx0 + (m % fw), sy1)
        f = ((m >> 10) % 100) / 100.0
        x = int(round(px + (corner[0] - px) * f))
        y = int(round(py + (corner[1] - py) * f))
        if sy1 < y < height and ch[y][x] == " ":
            ch[y][x], co[y][x] = ".", HAZE
    # The audience: three rows of heads, nearer ones bigger, lit by the film.
    lit = FLASH if bright > 0.42 else (CURB if bright > 0.25 else BARK)
    rows = [(sy1 + 3, 9, ["(_)"]), (sy1 + 5, 11, [" ,-. ", "(   )"]),
            (height - 4, 14, ["  ,--.  ", " (    ) ", "/      \\"])]
    for k, (y, gap, art) in enumerate(rows):
        off = (k * 5) % gap
        for x in range(off, width - len(art[0]), gap):
            if _mix(x, k, 1985) % 5 == 0:
                continue                         # an empty seat
            for r, line in enumerate(art):
                if 0 <= y + r < height:
                    _text(ch, co, y + r, x, line, lit if k < 2 else BARK)
    way = "-- the way out (s) --"
    for k, c in enumerate(way):
        x = max(1, width // 2 - 10) + k
        if x < width:
            ch[height - 1][x], co[height - 1][x] = c, GOLD_DIM
    return ch, co


def render_rave(club, width, height, now):
    """Inside the club.

    Every moving thing in here runs off club_light() and the same 134 BPM the
    front of the building does, so the room you walked into is on the beat you
    could hear from the pavement. Lights on the truss, lasers sweeping down
    into it, a crowd that goes up on the kick, and the strobe taking the whole
    room at the end of every eighth bar."""
    ch = [[" "] * width for _ in range(height)]
    co = [[0] * width for _ in range(height)]
    cx = (width - 1) / 2.0
    t = now * CLUB_BPM / 60.0 + club["phase"]
    up = t % 1.0 < 0.5
    lamp = club_light(now, club)
    neon = NEON[min(len(NEON) - 1, int(club["tone"] * len(NEON)))]
    shut = club_closing(now)
    if shut is not None:
        # Closing time: the lights up, the rig off, nobody dancing, and the
        # floor emptying as the minutes go.
        lamp, up = None, False
    gone = 0 if shut is None else int(100 * min(1.0, shut / LEAVE_FOR))

    if width < 40 or height < 16:
        _text(ch, co, height // 2, 1, "*** in the club ***",
              lamp if lamp is not None else neon[1])
        _text(ch, co, min(height - 1, height // 2 + 2), 1, "s to leave", GOLD_DIM)
        return ch, co

    truss, floor = 1, height - 1

    # The truss, and the moving heads hanging off it.
    for x in range(width):
        ch[truss][x] = "="
        co[truss][x] = CONCRETE
    heads = [int(cx + k * width * 0.21) for k in (-2, -1, 0, 1, 2)]
    for n, hx in enumerate(heads):
        if 0 <= hx < width:
            ch[truss][hx] = "V"
            co[truss][hx] = neon[0] if lamp is not None else neon[1]

    booth = truss + 4
    if lamp is not None:
        for n, hx in enumerate(heads):
            ang = math.sin(t * (0.7 + n * 0.19) + n * 1.7) * 0.95
            _beam(ch, co, hx, truss + 1, ang, height - 5,
                  NEON[(n + int(t / 4)) % len(NEON)][0])

    # The booth at the back, and whoever is behind it.
    _text(ch, co, booth - 1, int(cx - 1), ",-.", CURB)
    _text(ch, co, booth, int(cx - 7), "[==== DJ ====]",
          neon[0] if lamp is not None else CONCRETE)

    # Stacks either side, which move when the kick does.
    for side in (-1, 1):
        sx = int(cx + side * width * 0.44) - 1
        for r in range(5):
            _text(ch, co, booth - 2 + r, sx,
                  "|OO|" if lamp is None else "[**]",
                  CONCRETE if lamp is None else neon[0])

    # The crowd, in three depths: heads at the back, bodies in the middle,
    # and the people you are actually standing among at the front.
    far = booth + 2
    for x in range(1, width - 1, 2):
        if _mix(x, 0, 7) % 3 == 0 or _mix(x, 5, 13) % 100 < gone:
            continue
        y = far + _mix(x, 1, 9) % 2 - (1 if up ^ (x % 4 < 2) else 0)
        if truss < y < height:
            ch[y][x] = "o" if up ^ (x % 4 < 2) else "."
            co[y][x] = CURB

    mid = far + 3
    for x in range(2, width - 5, 7):
        if _mix(x, 6, 13) % 100 < gone:
            continue
        arms = up ^ (_mix(x, 2, 3) % 2 == 0) if shut is None else False
        for r, line in enumerate(("\\o/", " | ") if arms else ("(o)", "/|\\")):
            if mid + r < height:
                _text(ch, co, mid + r, x, line, CURB)

    near = height - 8
    for k in (-1, 0, 1):
        if shut is not None and _mix(k, 7, 13) % 100 < gone:
            continue
        px = int(cx + k * width * 0.29) - 2
        dancing = up ^ (k == 0) if shut is None else False
        for r, line in enumerate(RAVER_UP if dancing else RAVER_DOWN):
            if near + r < floor:
                _text(ch, co, near + r, px, line, CURB)

    # Glow sticks, up in the air and moving with everyone else.
    span = max(1, height - far - 5)
    for k in range(16 if shut is None else 0):
        m = _mix(k, int(t * 2), 71)
        gx = int((m & 1023) / 1023.0 * width)
        gy = far + (m >> 10) % span - (1 if up else 0)
        if 0 <= gy < floor and 0 <= gx < width:
            ch[gy][gx] = "*"
            co[gy][gx] = NEON[(m >> 18) % len(NEON)][0]

    # And the strobe, which takes the room.
    if lamp == FLASH:
        for y in range(truss + 1, floor):
            row, rowc = ch[y], co[y]
            for x in range(width):
                if row[x] == " " and _mix(x, y, 41) % 100 < 58:
                    row[x] = ":"
                    rowc[x] = FLASH

    if shut is not None:
        say = "the lights are up. time to go home."
        _text(ch, co, booth + 2, int(cx - len(say) / 2), say, BULB)
    _text(ch, co, floor, max(1, int(cx) - 10), "-- the way out (s) --", GOLD_DIM)
    return ch, co


# ---------------------------------------------------------------------------
# Main loop
# ---------------------------------------------------------------------------

ARROWS = (curses.KEY_LEFT, curses.KEY_RIGHT, curses.KEY_UP, curses.KEY_DOWN)

SKYLINE_HUD = " x=%-6d %s  tab view  arrows/hl walk  HL run  space wander  ` cheats "
STREET_HUD = " %d,%d %s, %s%s  ws walk  ad turn  ,. step  tab view  ` cheats "
ROULETTE_HUD = (" inside the %s casino at %d,%d  -  p slot  +/- bet  b/h/k"
                " blackjack  o plinko  r races  -  s walks out  -  q quit ")
RACES_HUD = (" at the races, %s casino, %d,%d  -  1-6 bet on a horse  +/- stake"
             "  r back to the wheel  -  s walks out ")
PLINKO_HUD = (" at the plinko machine, %s casino, %d,%d  -  p drops a ball  +/- bet"
              "  o back to the wheel  -  s walks out ")
RAVE_HUD = " inside the club at %d,%d  -  s walks back out  -  q quit "
RAMEN_HUD = " at the ramen counter at %d,%d  -  s walks back out  -  q quit "
LIFT_HUD = " in the lift, going %s "
DINER_HUD = " at the diner, open 24/7, at %d,%d  -  s walks back out  -  q quit "
CINEMA_HUD = " at the pictures: %s, at %d,%d  -  s walks back out  -  q quit "
TEMPLE_HUD = (" in %s  -  g asks for the word of god  -  c the confession booth"
              "  -  s walks out  -  q quit ")
CONFESS_HUD = " in the confession booth  -  type, enter to confess  -  esc steps out "
EXCHANGE_HUD = (" on the trading floor  -  b buys, n sells, arrows pick, l lists  -"
                "  s walks out  -  q quit ")
ARCADE_HUD = (" in the %s arcade  -  ad choose a game  -  p plays  -  s walks out"
              "  -  q quit ")
GAME_HUD = " playing %s  -  %s  -  x leaves the cabinet  -  q quit "
STRIKER_HUD = (" at the strength tester at %d,%d  -  p swings the hammer  -  s walks"
               " back out  -  q quit ")
CLAW_HUD = (" at the claw machine at %d,%d  -  p plays, p again drops  -  s walks"
            " back out  -  q quit ")
CLIMB_HUD = " on the fire escape, climbing %s "
STAIRS_HUD = " on the lighthouse stair, climbing %s "
TURNED_HUD = " turned away  -  s walks back out  -  q quit "
SEWER_HUD = " down the sewer  -  p takes a slice  -  s climbs back up  -  q quit "
PARTY_HUD = (" on the roof of %s, %s  -  ws walk  ad turn  -  into the lift hut to go"
             " down  -  q quit ")
GALLERY_HUD = " up the lighthouse, %s  -  ad round  -  s down  -  q quit "
ESCAPE_ROOF_HUD = (" on a roof in the alleys, %d floors up, %s  -  ad look round  -"
                   "  s climbs down  -  q quit ")
ROOF_HUD = (" on the roof, %d floors up, %s  -  ad look round  -  s takes the"
            " lift down  -  q quit ")


def main(stdscr):
    global WIDE_OK
    init_colors()
    WIDE_OK = wide_chars_work(stdscr)
    curses.curs_set(0)          # hide the cursor
    stdscr.nodelay(True)        # don't block waiting for a keypress
    stdscr.keypad(True)         # decode arrow keys into KEY_LEFT / KEY_RIGHT
    if hasattr(curses, "set_escdelay"):
        # A bare esc is seen at once, not a second later: curses waits that
        # long to see whether it starts an arrow key, and in the confession
        # booth - where every other key is a letter - esc is the way out.
        curses.set_escdelay(25)

    street = True               # which view we are in
    sky_x = 0.0                 # the two views keep their own cameras, so
    sky_v = 0.0                 # switching back and forth loses neither
    cam_x, cam_z = start_position()
    yaw = 0.0
    fwd = side = spin = 0.0
    last = {"sky": 0.0, "f": 0.0, "s": 0.0, "t": 0.0}
    steer = 0.0                 # the autopilot's heading, eased not snapped
    blocked = False             # did the last step run into something
    wheel = None                # the roulette, while you stand in a casino
    wallet = Wallet()           # your money: one balance for the whole city
    visit, visit_ok = None, True    # what you have paid to be in, this visit
    slot = Slot(wallet)         # the machine beside the wheel
    plinko = Plinko(wallet)     # and the plinko machine, o to go over to it
    at_plinko = False
    races = Races(wallet)       # and the race track, r
    at_races = False
    # The temple's terminal: the verses so far, when the last word was asked
    # for (to the nanosecond - it is what picks the next) and when.
    oracle = {"said": [], "last_ns": time.perf_counter_ns(), "at": -1e9, "sung": None}
    booth = None                # in the confession booth: {"t0", "text", "said"}
    ledger = {"jumps": 0}       # what the city has seen you do, for the priest
    jackpot_pull = None         # the pull that last paid 777, so it is had once
    table = Blackjack(wallet)   # and the table on the other side
    arms = []                   # what the claw machines have given you
    claw = None                 # the last claw machine you stood at
    at_claw = False             # and are you standing at it now
    play = {"arc": None, "sel": 0, "game": None, "hi": {}}   # at the arcade
    broker = Broker(wallet)     # your account at the exchange
    at_exchange = False
    at_arcade = False
    at_temple = False
    striker = None              # the last strength tester you stood at
    at_striker = False
    seated = None               # (which ramen counter, since when)
    lift = None                 # riding a sky-deck lift: {"up", "t0", "t"}
    sewer = None                # down a manhole: {"t0", "taken"}
    on_roof = None              # the tower whose roof you are standing on
    roof_x = roof_z = 0.0       # where you are on the landmark's roof
    wheel_at = 0.0
    cheats = False              # is the cheat panel up
    note = ""                   # and what did it last do
    note_at = -1e9              # when, so the HUD can show it after the panel closes
    autopilot = False
    frame_time = 1.0 / FPS

    while True:
        now = time.monotonic()
        _clock[0] = now

        # --- input -----------------------------------------------------
        key = stdscr.getch()
        while key != -1:
            if key == curses.KEY_RESIZE:
                _cache.clear()
            elif cheats and key not in ARROWS:
                # The letters belong to the panel while it is up. The arrows
                # do not, so you can still walk about with it open, which is
                # the whole reason it is drawn over the view.
                if key in (CHEAT_KEY, 27):
                    cheats, note = False, ""
                elif key == ord("q"):
                    return
                elif key == ord("w"):
                    note = "weather: " + cycle_weather()
                elif key == ord("L"):
                    force_strike(now)
                    note = "lightning"
                elif key == ord("u"):
                    note = ("the sky is busy tonight"
                            if skip_to_alien(now) else "no such night near")
                elif key == ord(">"):
                    note = "traffic: " + cycle_traffic()
                elif key == ord("a"):
                    note = "people: " + cycle_crowd()
                elif key == ord("s"):
                    note = "sky: " + cycle_clouds()
                elif key == ord("@"):
                    note = ("the night is nearly over"
                            if skip_to_dawn(now) else "no such night near")
                elif key == ord("!"):
                    note = ("fireworks over the bay tonight"
                            if skip_to_fireworks(now) else "no such night near")
                elif key == ord("+"):
                    wallet.give(1000)
                    note = "+$1000"
                elif key == ord("%"):
                    rig_jackpot()
                    note = "next pull 777, next plinko ball to the edge"
                elif key == ord("/"):
                    skip_to_closing(now)
                    note = "closing time - k for a club"
                elif key == ord("z"):
                    note = ("lanterns on the river tonight"
                            if skip_to_lanterns(now) else "no such night near")
                elif key == ord("n"):
                    skip_night()
                    nt = night(now)
                    note = "night: %s, %s moon" % (
                        "hazy" if nt["clarity"] < 0.4 else
                        "clear" if nt["clarity"] > 0.75 else "middling",
                        moon_face(nt["phase"]) or "no")
                else:
                    jumps = [(k, name, kind) for k, name, kind in CHEAT_PLACES]
                    jumps += [(d["key"], d["name"], "@%d" % n)
                              for n, d in enumerate(DISTRICTS)]
                    for k, name, kind in jumps:
                        if key != ord(k):
                            continue
                        spot = find_place(cam_x, cam_z, kind)
                        if spot is None:
                            note = "no " + name + " near"
                        else:
                            cam_x, cam_z, yaw = spot
                            fwd = side = spin = steer = 0.0
                            autopilot = False
                            wheel = None
                            sewer = None
                            booth = None
                            ledger["jumps"] += 1
                            street = True
                            note = "-> " + name
                            # And the panel closes: you jumped somewhere to
                            # look at it, and with the panel still up the
                            # next key you press is a district or another
                            # jump - p in the casino was the park.
                            cheats, note_at = False, now
                            if kind == "rave":
                                # Taking you to where one sometimes happens is
                                # no use: eighteen times in twenty there is
                                # nothing on and you are looking at trees. The
                                # menu exists to reach the thing, so it starts
                                # one, the way L calls down a strike.
                                force_rave(now)
                                note = "-> the woods rave (starting)"
                                note_at = now
                        break
            elif booth is not None and key != CHEAT_KEY:
                # Every key is a letter in here, q included; esc steps out.
                if key == 27:
                    booth = None
                elif key in (10, 13, curses.KEY_ENTER):
                    said_ = booth["text"].strip()
                    if said_:
                        booth["said"].append(("you", said_, now))
                        reply_ = absolve(said_, int(now * 1e6),
                                         dict(ledger, money=wallet.money))
                        booth["said"].append(("priest", reply_, now + CONFESS_WAIT))
                        booth["said"] = booth["said"][-12:]
                    booth["text"] = ""
                elif key in (8, 127, curses.KEY_BACKSPACE):
                    booth["text"] = booth["text"][:-1]
                elif 32 <= key < 127 and len(booth["text"]) < CONFESS_LONG:
                    booth["text"] += chr(key)
            elif key in (ord("q"), 27):
                return
            elif key == CHEAT_KEY:
                cheats, note = True, ""
            elif sewer is not None:
                if key in (ord("s"), ord("S"), ord("e"), ord("E"), curses.KEY_DOWN):
                    sewer = None                # up the ladder, onto the cover
                    note, note_at = "back up in the street", now
                elif key in (ord("p"), ord("P")):
                    if sewer_slices(now - sewer["t0"], sewer["taken"]):
                        sewer["taken"] += 1
                        note, note_at = "you take a slice. still warm.", now
                    else:
                        note, note_at = "the box is empty. they look at you.", now
            elif key in (ord("\t"), ord("v")):
                street = not street
                sky_v = fwd = side = spin = 0.0
            elif key == ord(" ") and not at_arcade:
                autopilot = not autopilot
            elif at_temple and key in (ord("c"), ord("C")):
                booth = {"t0": now, "text": "", "said": [
                    ("priest", "Bless you. Tell me what is on your mind.", now + 1.4)]}
            elif at_temple and key in (ord("g"), ord("G")):
                # The time since the last word, to the nanosecond, picks this
                # one. Nobody can choose that.
                ns_ = time.perf_counter_ns()
                word_ = god_word(ns_ - oracle["last_ns"])
                oracle["last_ns"] = ns_
                said_ = oracle["said"]
                if (not said_ or now - oracle["at"] > GOD_PAUSE
                        or len(said_[-1].split()) >= GOD_VERSE):
                    said_.append(word_)             # a new verse
                else:
                    said_[-1] += " " + word_
                oracle["said"] = said_[-20:]
                oracle["at"], oracle["sung"] = now, word_
            elif wheel is not None and key in (ord("o"), ord("O")):
                at_plinko, at_races = not at_plinko, False
            elif wheel is not None and key in (ord("r"), ord("R")):
                at_races, at_plinko = not at_races, False
            elif (wheel is not None and at_races
                  and ord("1") <= key < ord("1") + RACE_FIELD):
                races.bet(key - ord("1"), now)
            elif wheel is not None and at_races and key in (ord("+"), ord("=")):
                races.stake_up(1)
            elif wheel is not None and at_races and key in (ord("-"), ord("_")):
                races.stake_up(-1)
            elif wheel is not None and at_plinko and key in (ord("p"), ord("P")):
                plinko.drop(now)
            elif wheel is not None and at_plinko and key in (ord("+"), ord("=")):
                plinko.bet_up(1)
            elif wheel is not None and at_plinko and key in (ord("-"), ord("_")):
                plinko.bet_up(-1)
            elif wheel is not None and key in (ord("p"), ord("P")):
                if slot.t0 is None or slot.settled(now):
                    slot.settle(now)
                    slot.pull(now)
            elif wheel is not None and key in (ord("+"), ord("=")):
                slot.bet_up(1)
            elif wheel is not None and key in (ord("-"), ord("_")):
                slot.bet_up(-1)
            elif wheel is not None and key in (ord("b"), ord("B")):
                table.deal(now)
            elif wheel is not None and key in (ord("h"), ord("H")):
                table.hit(now)
            elif wheel is not None and key in (ord("k"), ord("K")):
                table.stand(now)
            elif at_exchange and key in (ord("b"), ord("n")):
                (broker.buy if key == ord("b") else broker.sell)(
                    broker.sel % len(STOCKS), now)
            elif at_exchange and key in (ord("l"), ord("L")):
                broker.listing = not broker.listing
            elif at_exchange and key in ARROWS:
                # Up and down the list, or left and right between charts -
                # either way it is the next stock or the last one.
                broker.sel += -1 if key in (curses.KEY_UP, curses.KEY_LEFT) else 1
            elif at_exchange and key in (ord("+"), ord("="), ord("-"), ord("_")):
                step = 1 if key in (ord("+"), ord("=")) else -1
                broker.lot = (broker.lot + step) % len(LOTS)
            elif at_arcade and play["game"] is not None:
                # Playing: the keys are the game's, but for x, which leaves.
                g_ = play["game"]
                if key in (ord("x"), ord("X")):
                    play["game"] = None
                elif g_.over and key in (ord("p"), ord("P")):
                    if wallet.take(ARCADE_COST):
                        play["game"] = type(g_)(_spin_rng.randrange(1 << 30), now)
                    else:
                        note, note_at = "a game is $%d" % ARCADE_COST, now
                else:
                    g_.key({curses.KEY_UP: "up", ord("w"): "up", ord("W"): "up",
                            curses.KEY_DOWN: "down", ord("s"): "down",
                            ord("S"): "down", curses.KEY_LEFT: "left",
                            ord("a"): "left", ord("A"): "left",
                            curses.KEY_RIGHT: "right", ord("d"): "right",
                            ord("D"): "right", ord("p"): "act",
                            ord("P"): "act"}.get(key, ""))
            elif at_arcade and key in (curses.KEY_LEFT, ord("a"), curses.KEY_RIGHT,
                                       ord("d")):
                play["sel"] += -1 if key in (curses.KEY_LEFT, ord("a")) else 1
            elif at_arcade and key in (ord("p"), ord("P")):
                name = arcade_order(play["arc"], stdscr.getmaxyx()[1])[
                    play["sel"] % len(arcade_order(play["arc"], stdscr.getmaxyx()[1]))]
                if wallet.take(ARCADE_COST):
                    play["game"] = GAMES[name](_spin_rng.randrange(1 << 30), now)
                else:
                    note, note_at = "a game is $%d" % ARCADE_COST, now
            elif at_striker and key in (ord("p"), ord("P")):
                striker.swing(now)
            elif at_claw and key in (ord("p"), ord("P")):
                claw.press(now)
            elif lift is not None:
                pass                            # nothing to do but ride
            elif (street and on_roof is None and key in (ord("e"), ord("E"))
                  and manhole_under(cam_x, cam_z) is not None):
                sewer = {"t0": now, "taken": 0}  # lift the cover, down the ladder
                fwd = side = spin = 0.0
                autopilot = False
            elif (on_roof is not None and on_roof.get("kind") == "lighthouse"
                  and key in (ord("f"), ord("F"))):
                # Up on the gallery: light a show, or fire the one going up.
                show = on_the_button(now, on_roof["x"], on_roof["z"])
                if show is not None:
                    show.press(now)
                elif wallet.money >= SHOW_FEE and light_show(now, on_roof["x"],
                                                             on_roof["z"]):
                    wallet.take(SHOW_FEE)
                else:
                    note, note_at = "a show is $%d" % SHOW_FEE, now
            elif (on_roof is not None and on_roof.get("kind") != "party"
                  and key in (curses.KEY_DOWN, ord("s"), ord("S"))):
                lift = {"up": False, "t0": now, "t": on_roof}
            elif (on_roof is not None and on_roof.get("kind") != "party"
                  and key in (curses.KEY_UP, ord("w"), ord("W"))):
                pass                            # the parapet is right there
            elif street:
                if key in (curses.KEY_UP, ord("w"), ord("W")):
                    fwd = WALK * (RUN_MULTIPLIER if key == ord("W") else 1.0)
                    last["f"], autopilot = now, False
                elif key in (curses.KEY_DOWN, ord("s"), ord("S")):
                    fwd = -WALK * (RUN_MULTIPLIER if key == ord("S") else 1.0)
                    last["f"], autopilot = now, False
                elif key in (curses.KEY_LEFT, ord("a")):
                    spin, last["t"], autopilot = -TURN, now, False
                elif key in (curses.KEY_RIGHT, ord("d")):
                    spin, last["t"], autopilot = TURN, now, False
                elif key == ord(","):
                    side, last["s"], autopilot = -SIDESTEP, now, False
                elif key == ord("."):
                    side, last["s"], autopilot = SIDESTEP, now, False
            else:
                if key in (curses.KEY_LEFT, ord("h")):
                    sky_v, last["sky"], autopilot = -WALK_SPEED, now, False
                elif key in (curses.KEY_RIGHT, ord("l")):
                    sky_v, last["sky"], autopilot = WALK_SPEED, now, False
                elif key in (ord("H"), ord("L")):
                    run = WALK_SPEED * RUN_MULTIPLIER
                    sky_v = -run if key == ord("H") else run
                    last["sky"], autopilot = now, False
            key = stdscr.getch()

        # A held-down key repeats, but with gaps. Rather than moving once per
        # keypress (jerky), we keep moving for a moment after each one.
        if autopilot:
            # Ease towards the heading rather than jumping onto it, and slow
            # down through a turn the way you would walking round a corner -
            # but turn away smartly when the last step got you nowhere.
            steer += ((wander(cam_x, cam_z, yaw, now) - steer)
                      * min(1.0, frame_time * (7.0 if blocked else 3.0)))
            spin = max(-TURN, min(TURN, steer * 2.0))
            want = WALK * (0.66 - 0.30 * min(1.0, abs(steer)))
            fwd += (want - fwd) * min(1.0, frame_time * 2.5)
            side = 0.0
            sky_v += (WALK_SPEED * 0.6 - sky_v) * min(1.0, frame_time * 2.5)
        else:
            if now - last["sky"] > KEY_GRACE:
                sky_v = 0.0
            if now - last["f"] > KEY_GRACE:
                fwd = 0.0
            if now - last["s"] > KEY_GRACE:
                side = 0.0
            if now - last["t"] > KEY_GRACE:
                spin = 0.0

        party = (on_roof if on_roof is not None and on_roof.get("kind") == "party"
                 else None)
        if party is not None and lift is None:
            # On the landmark's roof you can walk about: inside the parapet,
            # and back into the lift hut to go down.
            x0_, z0_, x1_, z1_ = party_roof(party["landmark"])
            ddx = math.sin(yaw) * fwd + math.cos(yaw) * side
            ddz = math.cos(yaw) * fwd - math.sin(yaw) * side
            roof_x = min(x1_ - 1.2, max(x0_ + 1.2, roof_x + ddx * frame_time))
            roof_z = min(z1_ - 1.2, max(z0_ + 1.2, roof_z + ddz * frame_time))
            hx_, hz_ = lift_hut(party["landmark"])
            # Into the hut, which ever way you are facing: from where the lift
            # leaves you it is right behind you, and s backs you into it.
            if ((roof_x - hx_) ** 2 + (roof_z - hz_) ** 2 < 1.6 ** 2
                    and (hx_ - roof_x) * ddx + (hz_ - roof_z) * ddz > 0.0):
                lift = {"up": False, "t0": now, "t": party}
        if (lift is not None or on_roof is not None or sewer is not None
                or booth is not None):
            fwd = side = 0.0            # on the roof you can only look round
            autopilot = False
            if lift is not None or sewer is not None or booth is not None:
                spin = 0.0
        sky_x += sky_v * frame_time
        yaw += spin * frame_time
        # Move on each axis in turn, so running into a wall at an angle slides
        # you along it instead of stopping you dead.
        dx = math.sin(yaw) * fwd + math.cos(yaw) * side
        dz = math.cos(yaw) * fwd - math.sin(yaw) * side
        nx = cam_x + dx * frame_time
        moved = False
        if can_stand(nx, cam_z):
            cam_x, moved = nx, True
        nz = cam_z + dz * frame_time
        if can_stand(cam_x, nz):
            cam_z, moved = nz, True
        blocked = not moved and (fwd or side)

        # Walking into a casino doorway is the one way into a building in
        # this city. Walk back out and the wheel goes away; stand there and it
        # deals you another, because that is what a casino is for.
        venue = venue_at(cam_x, cam_z) if street and sewer is None else None
        # The sky deck: walking into the lobby is stepping into the lift.
        if lift is not None:
            venue = None
            floors = max(2, int(lift["t"]["height"] / FLOOR_H))
            times = (climb_times(floors)
                     if lift["t"].get("kind") in ("escape", "lighthouse")
                     else lift_times(floors))
            if now - lift["t0"] >= times[2]:
                if lift["up"]:
                    on_roof = lift["t"]
                    if on_roof.get("kind") == "party":
                        # Out of the lift hut, facing the booth.
                        hx_, hz_ = lift_hut(on_roof["landmark"])
                        roof_x, roof_z, yaw = hx_, hz_ - 2.4, math.pi
                elif lift["t"].get("kind") == "lighthouse":
                    cam_x, cam_z, yaw = lift["t"]["exit"]   # out of the door
                    on_roof = None
                else:
                    t_ = lift["t"]
                    out = 2.6 if t_.get("kind") == "escape" else CASINO_REACH + 1.8
                    ox, _, oz = face_point(t_["i"], t_["j"], t_["door"],
                                           t_["u"], out, 0.0)
                    if can_stand(ox, oz):
                        cam_x, cam_z = ox, oz
                    nx_, nz_ = FACES[t_["door"]]
                    yaw = math.atan2(nx_, nz_)       # facing out, to the street
                    on_roof = None
                lift = None
        elif on_roof is not None:
            venue = None
        elif street and fwd > 0.0 and escape_at(cam_x, cam_z, yaw) is not None:
            lift = {"up": True, "t0": now, "t": escape_at(cam_x, cam_z, yaw)}
            venue = None
        elif venue is not None and venue[0] == "tower":
            fee = LIFT_FEES.get(venue[1].get("kind"), 0)
            if wallet.take(fee):
                lift = {"up": True, "t0": now, "t": venue[1]}
            else:
                note, note_at = "the lift is $%d" % fee, now
            venue = None
        elif street and fwd > 0.0 and lighthouse_door(cam_x, cam_z) is not None:
            # In at the lighthouse's door is on to its stair.
            lift = {"up": True, "t0": now, "t": lighthouse_door(cam_x, cam_z)}
            venue = None
        if venue is None or venue[0] not in ("ramen", "diner"):
            seated = None               # stood up: the next visit is a new bowl
        # Paying for what you came in for, once a visit: a seat at the
        # pictures, the club's cover, the bowl, the coffee.
        here = None
        if venue is not None and venue[0] in FEES:
            here = (venue[0],) + tuple(sorted(
                (k_, v_) for k_, v_ in venue[1].items()
                if isinstance(v_, (int, float, str))))
        if here != visit:
            visit = here
            visit_ok = here is None or wallet.take(FEES[venue[0]])
        if venue is not None and venue[0] == "exchange" and not at_exchange:
            broker.sel = venue[1]["stock"]          # its own stock, on the way in
        at_exchange = (venue[1] if venue is not None and venue[0] == "exchange"
                       else False)
        at_arcade = venue is not None and venue[0] == "arcade"
        at_temple = venue is not None and venue[0] == "temple"
        if not at_temple:
            booth = None                # out of the temple is out of the booth
        if not at_arcade:
            play["game"] = None
        elif play["arc"] is None or play["arc"]["seed"] != venue[1]["seed"]:
            play.update(arc=venue[1], sel=0, game=None)
        at_striker = venue is not None and venue[0] == "striker"
        if at_striker and (striker is None or striker.col != venue[1]["col"]):
            striker = Striker(venue[1]["col"], arms, wallet)
        at_claw = venue is not None and venue[0] == "claw"
        if at_claw and (claw is None or claw.col != venue[1]["col"]):
            claw = Claw(venue[1]["col"], arms, wallet)
        if venue is None or venue[0] != "casino":
            wheel = None
        elif wheel is None or (wheel.done(now)
                               and now - wheel_at > CASINO_AGAIN):
            wheel = Spin(now, venue[1]["name"])
            wheel_at = now + SPIN_TIME + HOLD_TIME

        if _show is not None:
            _show.update(now)

        # --- draw ------------------------------------------------------
        height, width = stdscr.getmaxyx()
        if sewer is not None and street:
            ch, co = render_sewer(width, height, now, sewer["t0"], sewer["taken"])
            hud = SEWER_HUD
        elif lift is not None:
            floors = max(2, int(lift["t"]["height"] / FLOOR_H))
            if lift["t"].get("kind") == "lighthouse":
                ch, co = render_stairs(lift["up"], floors, now - lift["t0"],
                                       width, height, now)
                hud = STAIRS_HUD % ("up" if lift["up"] else "down")
            elif lift["t"].get("kind") == "escape":
                ch, co = render_climb(lift["up"], floors, now - lift["t0"],
                                      width, height, now)
                hud = CLIMB_HUD % ("up" if lift["up"] else "down")
            else:
                ch, co = render_lift(lift["up"], floors, now - lift["t0"], width,
                                     height, now)
                hud = LIFT_HUD % ("up" if lift["up"] else "down")
        elif on_roof is not None and on_roof.get("kind") == "party":
            lm_ = on_roof["landmark"]
            v = View(roof_x, roof_z, yaw, width, height, eye=LANDMARK_H + 1.7,
                     reach=ROOF_REACH)
            v.roof = on_roof
            v.skip = {(a, b) for a in range(lm_["i0"], lm_["i1"] + 1)
                      for b in range(lm_["j0"], lm_["j1"] + 1)}
            ch, co, wet = render_street(v, now)
            hud = PARTY_HUD % (lm_["name"].lower(), sky_word(now, wet))
        elif on_roof is not None and on_roof.get("kind") == "lighthouse":
            v = gallery_view(on_roof, yaw, width, height)
            v.roof = on_roof
            ch, co, wet = render_street(v, now)
            show = on_the_button(now, on_roof["x"], on_roof["z"])
            if show is not None:
                draw_show_bar(ch, co, show, now)
            hud = GALLERY_HUD % sky_word(now, wet) + gallery_hint(now)
        elif on_roof is not None:
            v = roof_view(on_roof, yaw, width, height)
            v.roof = on_roof
            ch, co, wet = render_street(v, now)
            hud = (ESCAPE_ROOF_HUD if on_roof.get("kind") == "escape"
                   else ROOF_HUD) % (int(on_roof["height"] / FLOOR_H),
                                     sky_word(now, wet))
        elif wheel is not None:
            slot.settle(now)
            table.update(now)
            if any(abs(k_ - PLINKO_ROWS // 2) == PLINKO_ROWS // 2
                   for k_ in plinko.settle(now)):
                hit_jackpot(now, venue[1])      # all the way to the edge
            paid_ = races.update(now)
            if paid_ and races.last[1] >= 20:
                hit_jackpot(now, venue[1])      # a long shot came in
            if slot.payout(now) == "JACKPOT" and slot.pulls != jackpot_pull:
                # 777: this casino goes up in gold, inside and out.
                hit_jackpot(now, venue[1])
                jackpot_pull = slot.pulls
            ch, co = render_casino_room(wheel, width, height, now, slot, table,
                                        jackpot_on(now, venue[1]),
                                        plinko if at_plinko else None,
                                        races if at_races else None)
            hud = (PLINKO_HUD if at_plinko else RACES_HUD if at_races
                   else ROULETTE_HUD) % (wheel.name, cam_x, cam_z)
        elif venue is not None and venue[0] in FEES and not visit_ok:
            ch, co = render_turned_away(venue[0], width, height, now)
            hud = TURNED_HUD
        elif venue is not None and venue[0] == "club":
            ch, co = render_rave(venue[1], width, height, now)
            hud = RAVE_HUD % (cam_x, cam_z)
        elif venue is not None and venue[0] == "diner":
            if seated is None or seated[0] != ("diner", cam_x // 10, cam_z // 10):
                seated = (("diner", cam_x // 10, cam_z // 10), now)
            ch, co = render_diner(width, height, now, seated[1])
            hud = DINER_HUD % (cam_x, cam_z)
        elif at_striker:
            striker.update(now)
            ch, co = render_striker(striker, width, height, now)
            hud = STRIKER_HUD % (cam_x, cam_z)
        elif at_claw:
            claw.update(now)
            ch, co = render_claw(claw, width, height, now)
            hud = CLAW_HUD % (cam_x, cam_z)
        elif venue is not None and venue[0] == "exchange":
            ch, co = render_exchange(venue[1], broker, width, height, now)
            hud = EXCHANGE_HUD
        elif venue is not None and venue[0] == "temple" and booth is not None:
            ch, co = render_confession(width, height, now, booth)
            hud = CONFESS_HUD
        elif venue is not None and venue[0] == "temple":
            ch, co = render_temple(venue[1], width, height, now, oracle["said"],
                                   oracle["sung"])
            hud = TEMPLE_HUD % venue[1]["name"].lower()
        elif venue is not None and venue[0] == "arcade":
            g_ = play["game"]
            if g_ is not None:
                g_.tick(now)
                key_ = (venue[1]["seed"], g_.name)
                if g_.over:
                    play["hi"][key_] = max(play["hi"].get(key_, 0), g_.score)
                ch, co = render_game(g_, play["hi"].get(key_, 0), width, height, now)
                hud = GAME_HUD % (g_.name.lower(), g_.controls)
            else:
                ch, co = render_arcade(venue[1], width, height, now, play["sel"])
                hud = ARCADE_HUD % venue[1]["name"].lower()
        elif venue is not None and venue[0] == "cinema":
            ch, co = render_cinema(venue[1], width, height, now)
            hud = CINEMA_HUD % (venue[1]["title"].lower(), cam_x, cam_z)
        elif venue is not None and venue[0] == "ramen":
            if seated is None or seated[0] != venue[1]["seed"]:
                seated = (venue[1]["seed"], now)    # sat down just now
            ch, co = render_ramen(venue[1], width, height, now, seated[1])
            hud = RAMEN_HUD % (cam_x, cam_z)
        elif street:
            v = View(cam_x, cam_z, yaw, width, height)
            ch, co, wet = render_street(v, now)
            hud = STREET_HUD % (
                cam_x, cam_z,
                district(int(cam_x / CELL + BIG) - BIG,
                         int(cam_z / CELL + BIG) - BIG)["name"],
                sky_word(now, wet),
                show_hint(now, cam_x, cam_z)
                or landmark_hint(cam_x, cam_z)
                or rave_hint(v, now)
                or ("  ~ something over the city ~" if night(now)["alien"]
                    else "")
                or ("  ~ a train overhead ~" if el_overhead(cam_x, cam_z, now)
                    else "")
                or ("  ~ the hum of the highway ~" if hwy_near(cam_x, cam_z)
                    else "")
                or ("  ~ a manhole: e lifts the cover ~"
                    if manhole_under(cam_x, cam_z) else "")
                or ("  ~ a manhole: stand on it, e lifts the cover ~"
                    if manhole_near(cam_x, cam_z) else "")
                or ("  ~ a fire escape: walk into it to climb ~"
                    if escape_near(cam_x, cam_z) else "")
                or ("  ~ a claw machine: walk up to it to play ~"
                    if claw_near(cam_x, cam_z) else "")
                or ("  ~ fireworks over the bay ~"
                    if fireworks_near(cam_x, cam_z, now) else "")
                or ("  ~ dawn ~" if dawn(now) > 0.0 else "")
                or ("  ~ a fire going under the road ~"
                    if fire_near(cam_x, cam_z) else "")
                or ("  ~ a siren somewhere ~"
                    if siren_near(cam_x, cam_z, now) else ""))
        else:
            ch, co = render_skyline(sky_x, width, height, now)
            hud = SKYLINE_HUD % (sky_x, sky_word(now, rain_intensity(now)))
        hud = " $%d " % int(wallet.money) + hud       # what you have, everywhere
        if cheats:
            draw_cheats(ch, co, note)
        elif now - note_at < 4.0 and note:
            hud = hud.rstrip() + "  " + note.strip() + " "

        wide = v.wide if (street and wheel is None and venue is None
                          and lift is None) else ()
        stdscr.erase()
        for y in range(height):
            row_ch, row_co = ch[y], co[y]
            x = 0
            while x < width:
                c = row_ch[x]
                # The very last cell of the screen can't be written to, and
                # a wide glyph needs the one after it as well.
                corner = y == height - 1 and x >= width - 2
                # Trust but verify: a later pass - rain, usually - can paint
                # over the glyph after its column was claimed, and stepping
                # over two cells for a leftover reservation would swallow a
                # column of the picture.
                if (y, x) in wide and not corner and is_wide(c):
                    # A double-width glyph owns the column after it as well, so
                    # step over that one rather than painting into its far half.
                    try:
                        stdscr.addstr(y, x, c, row_co[x])
                    except curses.error:
                        pass
                    x += 2
                    continue
                if c != " " and not (y == height - 1 and x == width - 1):
                    try:
                        stdscr.addch(y, x, c, row_co[x])
                    except curses.error:
                        pass
                x += 1

        try:
            stdscr.addstr(0, 0, hud[:width - 1], HUD)
        except curses.error:
            pass

        stdscr.refresh()
        time.sleep(max(0.0, frame_time - (time.monotonic() - now)))


if __name__ == "__main__":
    curses.wrapper(main)
