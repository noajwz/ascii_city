# Fishing, and the tackle shops

Asked for on 2026-11-15, from the coast ideas list ("fishing off the pier"): a fishing mechanic
with different fish depending on where you fish, a fishing store with rods, bait and bobbers,
and fishing anywhere you are carrying a rod and near water.

**Carry a rod, stand by water, `f`.** In the street (not on a roof, in a doorway or down a
manhole) `f` checks `fish_ready()`: a rod in hand, and water to cast into within the rod's
reach in front of you (`water_ahead()`, three bearings either side of where you face).
**Not off the speedboat** - that went in first and was taken out on 2026-11-15: the speedboat
is for driving, and the open sea is the fishing boat's (below). `Fishing` is the state,
`render_fishing()` the view - the ordinary `render_street()` from where you stand with the
rod, the line, the float and the meters over it. It counts in `elsewhere()`, so you do not
walk or go through doors while fishing; `x` packs up.

**What bites is decided by where the float goes in, not where you stand.** `fish_water(x, z)`:
the river (and the moat round the headland) is `"river"`, the woods' lake `"lake"`, the
fountain on the Strip `"fountain"`, the river's last `MOUTH_REACH` cells and its water across
the beach `"mouth"`, and the sea by how far out from the waterline the float is: `"surf"` under
`FISH_SURF` (22 units), `"inshore"` to `FISH_INSHORE` (110 - off the ocean pier), `"deep"` to
`FISH_DEEP` (400 - from the pier's head out), `"offshore"` past that, which only the fishing
boat reaches. Water round a quay is `"harbour"`. Decks, land, the docked cruise ship: `None`,
and the cast "lands on dry ground". `WATER_NAMES` are the words for them.

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

## The fishing boat, and expeditions

Asked for on 2026-11-15, in place of fishing off the speedboat: "an actual fishing boat. We can go
aboard for a fishing expedition but we don't drive the fishing boat ourselves we have a funny
pirate like captain that asks where we want to go. We pay him ofcourse. A fishing expedition can
only go to one of the destinations at a time. Right now we only have 1 destination and that is
your open ocean but I plan on having more expeditions added later on."

**The Salty Herring** (`HERRING_NAME`) lies off the end of every harbour's quay, bow out
(`herring_berth()`, `HERRING_GAP` from it). She went alongside on the boat hire's side first,
and a speedboat just hired, opened up, ran straight into her - the checks' speedboat run caught
it; off the end she is clear of that lane and of the cruise ship's way out. `draw_herring()`
(from `draw_harbour()`): a red hull, a white wheelhouse with lit windows, a mast and its light,
her name in lights on the hull, a gangplank from the end of the quay, and by it **Cap'n Redgill**
(`CAPTAIN`, the `PIRATE` sprite) under FISHING TRIPS. The names go up with the tackle shops'
(`v.tackle_signs`). She is solid to the speedboat (`herring_in()` in `boat_water()`) while she
is moored. A taxi goes to "the fishing boat"; ctrl-a `v` for the checks.

**Talking to him** (`p` at the plank, `herring_near()`): `trip` in `main()`, phase `"talk"`,
`render_captain()` - the quay behind, him big (`CAPTAIN_ART`, coloured by `captain_colours()`:
hat and skull, eye patch, the red beard, the parrot, the coat with its gold), what he says, and
**where to** - `EXPEDITIONS`. `w`/`s` choose, `p` or enter pays and casts off, `x` walks away.
No rod and he will not go ("ye'd be fishin' with yer teeth"); not the fee, he says so; without
the rod an expedition wants (`"rod"`) he goes anyway and tells you.

**`EXPEDITIONS` is where the next ones go.** One dict each: `name`, `fee`, where she anchors
(`out` units off the beach, `along` the coast from the harbour), `sail` (seconds out; home is
0.7 of it), `water` (a `WATER_NAMES` key for the fish there - `None` is whatever `fish_water()`
says of the sea where she anchors), the `rod` it wants, what he `says` and the `fish` the list
shows. One for now: **the open ocean**, 700 off and 160 down the coast, $45, 24 s out. A new
destination with fish of its own wants a new water key in `WATER_NAMES` and the fish that live
in it in `FISH`; `Fishing(..., water=)` forces it (`self.force`). Only one expedition at a time:
she is either at the quay or out with you (`_herring_out`).

**The trip.** `expedition_route()`: along the quay, past its end, out and along the coast, through
`_catmull()`; `route_pose()` eases along it. Phase `"out"`, `render_voyage()`: the view from her
deck, the bow out in front, her mast and its light, and along the bottom what the captain says
(`CAP_AWAY`) and now and then the parrot (`PARROT`); `a`/`d` look round, space leans on the
throttle (three seconds on). There: anchored, `fishing` is a `Fishing` with `deck=HerringDeck()`
(its eye rides the swell, her side runs along the bottom of the view) and the aim goes all the
way round. He has something to say when one is on, landed or lost (`CAP_HOOKED`, `CAP_LANDED`,
`CAP_LOST`, over the top of the view). `x` - and he weighs anchor and takes you home the same
way back, phase `"home"`, and you are down the gangplank facing the town.

## The captain's cabin

Asked for on 2026-11-15: "when fishing there's a button to go inside the captains cabin. We can
give it the same kind of full circle view as the skybar has. In here you can talk to the
captain, the captain also sells drinks and bait."

**`c` at anchor** (aiming or waiting - a line in the water is reeled in; not with a fish on)
goes in: `trip["cabin"]` (`new_cabin()`), `render_cabin()`, and `x` or `c` is back on deck with
the rod. **It is the rooftop bar's way of doing it** (see The rooftop bar): `render_street()`
from her wheelhouse, `CABIN_EYE`, so the sea, the moon on it and the ships out there are the
real ones through her windows; then the cabin over it **in screen space, by bearing** from her
bow (`bar_col()`, `_bar_sprite()` - solid, `k` times over), so it holds still as you turn
(`a`/`d`). Beams over, planking under the windows (seams by bearing, `_col_bearing()`), posts
between the windows at the sixteenths - half way between the things in the cabin, which stand
at the eighths. A post at the eighths put a bar straight through the captain.

**Round the cabin**: forward the wheel (`CABIN_WHEEL`) and binnacle; to starboard the captain
(`CABIN_CAPTAIN`) behind his counter, the bottles on a shelf, his chalkboard, what he says; aft
the door, and over it **your biggest fish yet** on a plaque (`tackle.book`, the best by weight
and fight); to port the chart table with **a chart of where you really are** (`draw_chart()`:
the coast, the harbours as H, an X where she lies) and the parrot on his perch, squawking; the
bait barrel, the hammock and a ship in a bottle between; a lantern swinging overhead; and the
whole cabin rising and falling a row with the swell.

**Facing him** (`cabin_facing()`, within 0.7 rad of starboard) `1`-`4` a drink (`CABIN_DRINKS`,
off the wallet, `CABIN_MIX` of him pouring, `CABIN_LIMIT` and it is water; past two the view
sways, as at the rooftop bar), `5`-`8` bait off his shelf at sea prices (`CABIN_BAIT` - dearer
than the shop's: you are a long way from it), `t` a tale (`CAB_TALES`: tips for the open sea's
fish, lore, nonsense). Turned away, the top bar tells you he is to starboard.

**Words stay words on a big window**: `_bar_sprite()` blows a drawing up `k` times, so the
shelf's label and the barrel's came out GGRROOGG; they are `_label()`s now, plain text on a
blank of its own (the planking showed between the words).

