# Fishing, and the tackle shops

Asked for on 2026-11-15, from the coast ideas list ("fishing off the pier"): a fishing mechanic
with different fish depending on where you fish, a fishing store with rods, bait and bobbers,
and fishing anywhere you are carrying a rod and near water.

**Carry a rod, stand by water, `f`.** In the street (not on a roof, in a doorway or down a
manhole) `f` checks `fish_ready()`: a rod in hand, and water to cast into within the rod's
reach in front of you (`water_ahead()`, three bearings either side of where you face). Off the
speedboat, stopped (`FISH_SLOW`), `f` fishes from her side: the view rides her swell and her
gunwale runs along the bottom. `Fishing` is the state, `render_fishing()` the view - the
ordinary `render_street()` from where you stand with the rod, the line, the float and the
meters over it. It counts in `elsewhere()`, so you do not walk or go through doors while
fishing; `x` packs up.

**What bites is decided by where the float goes in, not where you stand.** `fish_water(x, z)`:
the river (and the moat round the headland) is `"river"`, the woods' lake `"lake"`, the
fountain on the Strip `"fountain"`, the river's last `MOUTH_REACH` cells and its water across
the beach `"mouth"`, and the sea by how far out from the waterline the float is: `"surf"` under
`FISH_SURF` (22 units), `"inshore"` to `FISH_INSHORE` (110 - off the ocean pier), `"deep"` to
`FISH_DEEP` (400 - from the pier's head out), `"offshore"` past that, which only the boat
reaches. Water round a quay is `"harbour"`. Decks, land, the docked cruise ship: `None`, and the
cast "lands on dry ground". `WATER_NAMES` are the words for them.

**The fish** (`FISH`, made with `_sp()`): 44 kinds for the book and 13 kinds of rubbish. Each
has the waters it is in, the baits it takes, a weight range, how hard it pulls (`power`), how
common it is (`odds`), $ a kilo, a colour, a drawing (`FISH_ART`, by shape: round, long, pike,
eel, cat, flat, ray, shark, bill, tuna, gar, squid, crab, glow, and one each for the rubbish),
what the card says, and what it likes: rain (eels, conger, the catfish), a full moon (bass, sole,
cod, swordfish), dawn (trout, sea trout, bass, mackerel) double or so its odds. `bite_pool()` is
what could take this bait in this water tonight. Rubbish bites on anything, less on a lure.
Legendary: the old one (a carp in the woods' lake, bread only), the blue marlin (offshore), and
the jackpot token in the fountain. "Something that glows" is only there on the strange night.
The checks assert every fish can be caught somewhere on some bait.

**The tackle.** `ROD_KINDS`: how far each casts, what its line holds (tension, 1.0 being a
middling fish pulling hard), its reel speed, and how much line is on the reel: the willow pole,
the spinning rod, the surf caster, the big game rod. `BAIT_KINDS`: bread, worms, lugworm, squid
strips (a pack of ten; one goes with every fish, every missed bite and a strike too soon a
third of the time), and two lures, the spinner and the big game lure, which come back unless
the line goes. **The big game lure goes on the big game rod only** ("too heavy for this rod"),
and the tuna and the swordfish take nothing else: that, not a rule, is what keeps the open
sea's giants for the big rod. `FLOAT_KINDS`: none (you watch the rod's tip knock), the cork,
the waggler, the glow float (lit green, you see it go under at night). The float is the time
you have to strike (`window()`: 0.45 s with none to 0.95, a lure's take 0.2 s longer); a lost
line takes the float with it. `Tackle` holds the lot - for the session, like the money.

**A cast** (`phase` "aim"): the meter swings there and back over `FISH_SWING`; the spot it would
land on is marked in the world, a cross across the line of the cast with dots along its arc,
**green over water and red over land**; `a`/`d` swing the aim, `r` `b` `o` change rod, bait,
float. `f` casts: "flight", the float on its arc for `FISH_FLIGHT`. **The wait** ("wait"):
`schedule()` picks the bite - when (an exponential round `FISH_WAIT`, quicker in rain and at
dawn, slower where little takes that bait) and who (by odds) - and a few nibbles before it.
Nothing in that water takes that bait: after twenty seconds it says so. `f` inside the
float's moment hooks it; too soon, during a nibble, "it lets go"; too late, "it took the bait".

**The fight** (`fight()`, every frame): the fish pulls by its power (by its weight within its
range), harder while it runs and less as it tires. `w` reels (each press holds `FISH_GRACE`,
past the wait before a held key repeats), `s` gives line, `a`/`d` hold the rod over - against
the way it pulls, it tires faster. The tension eases towards what that adds up to; over what the
line holds for `FISH_SNAP` it snaps, and more out than the reel holds and it is gone. It runs
now and then, **"it turns..." first** (`FISH_WARN`), and reeling against a run, or even holding
on, takes most rods past their line - give it line. A run done, now and then (`FISH_CHARGE`) it
**swims at you**: no pull, the line goes slack, and slack for `FISH_SLACK` it throws the hook
- reel it in. In at your feet (1.6 units of line) it is landed: `draw_catch()`, the card, its
drawing in its colour blown up on a big window, its weight and what it will fetch, "new in the
book" or "your biggest yet", what it says (a bottle has a note in it, `BOTTLE_NOTES`); `f`
keeps it in the cool box (`FISH_BOX` of them), `l` lets it go.

**Tuned by playing it out, not by feel.** A simulated player - pressing what a person would,
0.45 s behind what is on the screen, held keys repeating after 0.4 s - over twelve fights of
each fish on each rod: roach and perch land on anything in 3 to 10 s; carp, pike, bass, cod in
12 to 25 s; conger, salmon, mahi-mahi 20 to 40; the catfish 4 in 12 on the willow pole and
every time on the surf caster; the old one 0 on the willow, 2 in 12 on the spinning rod, 9 on
the surf caster, all on the big game rod in about 50 s; a marlin on the big game rod about a
minute. Someone just holding `w` loses half the perch on a willow pole and every pike. The
checks keep the shape of it: a roach any old way, a pike only if you give it line, the old one
never on the willow, tuna and marlin on the big game rod. The slack rule went in after the
first round of tuning and made everything easier (the fish swimming in brought in too much
line); the swim-in was slowed and giving line made to take half the pull, not a third.

**The shops.** One on every ocean pier (`pier_tackle()`: on the boards `TACKLE_OUT` out, the
side away from the stalls), and a bait kiosk on river piers (`river_kiosk()`: on the first row
of boards all three columns have, at the east column, and only where a column has ground you
can stand on behind it - a third of the river's piers have a building at the land end, and a
kiosk there was out of reach; one every 700 units or so, cached in `_kiosk_cache`, which
`coast_reset()` clears). `draw_tackle_hut()`: a hut with a lit hatch, a neon fish on a pole,
its tail going, and the name in neon over the roof. **The names go up at the end of the frame**
(`v.tackle_signs`, `draw_tackle_signs()`): drawn with the pier, the river's lights and the
bridges painted over them. `p` at the counter (`tackle_near()`, `TACKLE_REACH`) goes in -
`shop` in `main()`, `render_tackle()`: the name in neon, floats on a string, rods in a rack, the
live bait fridge, the man with his pipe, and the shelves: RODS, BAIT, FLOATS, SELL, BOOK, `a`/`d`
between them, `w`/`s` along one, `p` buys, `c` sells the cool box anywhere in the shop, with a
picture of what you are pointing at (`ROD_ART`, `BAIT_ART`, `FLOAT_ART`, the fish). The book
lists every kind, a row of question marks and the water it is in till you have one. `x` steps
back out **turned to the water** (`water_yaw()`), so `f` works at once - from a kiosk facing
along the bank, the cast landed on the next column's bank, where the shore wanders. On the
big-window system: the name in block letters, the drawings `_blow_up()`'d, the words small;
`z` works. `"the tackle shop"` is in `TAXI_DESTS` (the nearer of the two kinds), so it has no
panel key; ctrl-a `9` and `0` (the pier's shop, a kiosk) are for the checks.

**The panel's `g`**: the next bite is the rarest thing in that water on that bait, big, three
seconds after the float goes in (`_fish_rare`) - for looking at the legendary ones.

**Drawing it.** The rod comes up from the bottom right to the horizon, bending towards the fish
under tension, its glyph by the curve's slope (by the step from one cell to the next it was all
`-` and `|`); the blank light grey, the cork handle gold, rings up it, the reel turning while you
reel. **The line stops one cell short of the float**, or its last dot covered the float. On a
big window the gauges and the rod thicken, RUNS and STRIKE go in block letters.

**What it costs**: the water check for the top bar's "f casts a line" is a tenth of a
millisecond, and only with a rod. The fishing view is the street view plus a few hundred cells:
22 to 29 ms at 300x90.
