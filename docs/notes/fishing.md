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
bridges painted over them. Walking up to the counter (`tackle_near()`, `TACKLE_REACH`) goes in -
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

**Talking to him** (walking up to the plank, `herring_near()`): `trip` in `main()`, phase `"talk"`,
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

## Walked into, not p

Asked for on 2026-11-15: "the tackleshop, fishing boat, cruise all need me to press P in order
to interact. Please make it so walking inside it does the interaction like most other things."
All three are in `venue_at()` now, first thing - `"tackle"` (the counter), `"herring"` (the
gangplank) and `"gangway"` (the cruise ship's) - and `main()` turns them into the shop, the
captain and the cruise the way it does the airport's gate and the library. So they go by the
door rules: walk up and you are in, hurry past and you are not (see the hurrying rule in
CLAUDE.md). **Everywhere they leave you is a step short**, or you would be straight back in:
`tackle_back()` (`TACKLE_BACK` back from the counter, away from the hut) where a jump puts you and
where you come out of a shop; `HERRING_BACK` along the quay from the plank for the jump, walking
away from the captain and coming home from a trip; and `_gangway_spot()` 5.5 back on the quay
for the jump and where the cruise sets you down. The top bar says what is there from further
off than the trigger (`reach` on `tackle_near()`, `herring_near()`, `gangway_near()`). The pty
cases walk in with `w`: one press for a counter (a second would be a key in the shop), two for
the rest. The speedboat hire, the pier's big wheel and the vending machines are still `p`.

## The wreck

The second expedition, asked for on 2026-11-15 from a list of seven (the wreck, the glowing
sea, the launch pad, the deep trench, the storm front, the ice floes, Treasure Island - the rest
are the owner's to pick from next). **The Mary Ellen** (`WRECK_NAME`) lies off every harbour,
`out` 380 off the beach and `along` 260 up the coast, `WRECK_AHEAD` on from where the Herring
anchors to fish her and broadside on, so she is in front of you (`wreck_site()`, cached in
`_wreck_cache`, which `coast_reset()` clears). `draw_sea_wreck()`: two masts leaning out of the
water with their yards and slack rigging, a gull on the tall one, her bow up out of it with her
name in rust (a sign with a colour of its own: `v.tackle_signs` takes one now), surf breaking
on her, and her buoy off her side, two short red flashes - from the beach her masts are a
mark on the horizon. The speedboat stops at her (`wreck_in()` in `boat_water()`). $60, 20 s
out, the surf caster at least (`"rod": 2` - the captain's warning is now each expedition's
`"short"`, said when your rod is less than it wants), and he has his own line on arrival
(`"there"`).

**Her water** is `"wreck"`: `fish_water()` says so for sea more than 250 out within
`WRECK_REACH` of a wreck - cast the other way from her and it is the open sea's. **Her fish**:
wreck pollock, black bream, cuckoo wrasse, wolffish, lobster ($30 a kilo), conger and ling
(which live off the pier's head too), the giant grouper (legendary: 40-180 kg, squid or the big
lure), and her rubbish - the ship's bell ($40), a porthole, a rusty chain, and now and then a
treasure chest ($350).

**The snag** (`Fishing.wreck()`, every frame of a fight there): the fish makes for her - `snag`
climbs by how strong and how fresh it is, fastest when it is let alone between runs, slower
while it runs (a run goes away, not down, and easing off at "it turns" is no fault), and
reeling lifts it, faster on a heavier reel. At 1 it is **SNAGGED**: give it slack for
`WRECK_FREE` and it swims back out (snag back to 0.55); hold on for `WRECK_HOLD` and the line
parts on her iron (reel against the snag and it snaps sooner); `WRECK_WEAR` snags in one fight
and the line is frayed through. The view has a WRECK meter beside the tension (filling down,
blue, gold, red, flashing when snagged), how many frays, and the words: "it is diving for the
wreck - reel it up!", "SNAGGED ON THE WRECK - s gives it slack!". The captain shouts too
(`CAP_SNAG`). **Tuned with the simulated player**: quick (0.45 s) - bream and lobster in 7 s,
pollock, wolffish, ling never lost, a conger lost one time in sixteen, the grouper six in sixteen
on the big game rod; slower (0.9 s) - a pollock lost three in sixteen. The first try made the
fish dive while you gave it line in a run, and the grouper could not be landed at all.

**Three name clashes, caught**: `_seg` (the launch site's), `draw_wreck` (the crashed plane's
windscreen - it would have broken crashing the plane) and `_label` (the cabin's copy of the
cockpit's, harmless). checks.py now asserts no top-level name is defined twice (`GOD_WORDS` is
on purpose).

## The glowing sea

The third expedition, asked for on 2026-11-15: "a cove where the water lights up blue-green with
plankton on still nights. Every wave, the boat's wake and your float leave trails of light ...
only runs on nights with little moon. Your line and the fish you're fighting glow, so you can see
a fight happening underwater."

**The cove** (`bio_site()`, cached in `_bio_cache`): where the Herring anchors, `out` 260 off the
beach and `along` 620 down the coast from every harbour - far enough out that a cast from the
sand does not reach it, clear of the piers either side and of the space centre. Its water is
`"bio"` within `BIO_REACH` (150). Rocks stand out of the water round it on the land's side
(`bio_rocks()`, `ROCK`; `draw_bio()`), black against it, and the speedboat stops at them
(`bio_in()` in `boat_water()`).

**A dark night** (`dark_night()`): the moon less than `BIO_MOON` of full (`moon_light()`, off
the night's phase) and no morning coming up - about one night in three. The captain will not go
on any other (`CAP_TOO_BRIGHT`; his list says "not tonight - too much moon"); `"when": "dark"`
on the expedition. **`e` on the panel** (`skip_to_dark()`) goes on to the next dark night - in
AND THE REST, since WEATHER & SKY's NIGHTS was full: one more row there and the panel no
longer opened on 80x24, which its check caught.

**The glow** (`bio_glow()`, from `coast_ground()`): on a dark night `render_street()` lists the
coves in reach (`v.bio`), and every point of the sea inside one is drawn lit instead - the
crests as they come in, cyan and green, dim far off (the first try lit every crest at full and
the sea was a sheet of light that hid the float); a few dim dots behind each crest; sparks. The
float leaves rings of light going out from it, its cast leaves a trail hanging in the air, the
line glows cyan, the Herring's bow wave sparkles as she comes in (`render_voyage()`), and in a
fight **the fish shows under the water** (`draw_lit_fish()`): a lit shape pointing the way it
swims, sparks round it, and a trail of where it has been (`Fishing.trail`, a point every 0.08 s,
the last sixteen).

**Its fish**: lanternfish (lights down its sides), flashlight fish, firefly squid (both worth a
lot by the kilo, and weigh nothing), moonfish (5-40 kg, a proper fight), the oarfish (legendary:
a silver sea-serpent with a red crest, 20-80 kg), and the glowing jellyfish, rubbish that stings.
$50, 22 s out, the spinning rod at least.

## The deep trench, and the ice floes

The fourth and fifth expeditions, asked for together on 2026-11-15. Both anchor where
`exp_anchor(h, site)` says (the end of the route, cached in `_anchor_cache`), and
`near_anchors(x, z, reach, site)` finds them; their water is black and still
(`still_water()`, from `coast_ground()` through `v.still`).

**The deep trench**: 1900 off the beach and 150 up the coast, past the shipping lanes - the
ships' lights are all there is (`draw_ships()` already puts them 650-1500 out). $90, 32 s out,
the big game rod (nothing less has the line: a fish comes up from `TRENCH_DEPTH`). Its water,
`"trench"`, is within `TRENCH_REACH` of the anchorage and more than 1200 out. **The twist**: the
lead takes `TRENCH_SINK` (15-25 s) to get to the bottom - SINKING ... and the depth along the
bottom of the view, then "on the bottom, wait for it" - and nothing bites on the way down (the
bite and the nibbles are put back by the sink). Hooked, the line is `TRENCH_DEPTH` and more,
it comes up `TRENCH_REEL` slower, and the line goes straight down by her side: the fish shows
(`fish_at()`) only in the last 14 units, with bubbles where the line goes in till then, and "it
is coming up from a long way down". An anglerfish took 97 s with the simulated player. Its fish:
grenadier, black scabbardfish, anglerfish (**its lure lit on the card**: a `*` in a drawing is
drawn in FIREFLY), barreleye ($120 a kilo), frilled shark, the giant squid (legendary), and a
brass diving helmet ($80).

**The ice floes**: 2500 up the coast and 1100 off the beach - out that far because the piers come
every 1800 units all along the coast and the first try, 300 off, had an ocean pier's lights and
wheel right beside the ice; a cold fog to hide them buried the floes in grain and was dropped.
`ice_floes()`: sixteen floes going slowly round on the current, one in five a berg
(`ICE_FLOE`, `ICE_BERG`, `draw_ice()`); the speedboat stops at them (`ice_in()`), the Herring
noses through. It always snows there (`v.snow` at least 0.55 within 500). $70, 38 s out, the
spinning rod. **The twist**: `Fishing.chill` (the expedition's `"cold": True`), and `cold`
climbs from 0 to 1 over `ICE_COLD` (150 s) - the strike window shrinks with it (to a third at
numb) and the reel slows. `draw_cold()`: HANDS, a bar along the top going gold, blue, numb, the
words, and your breath going up from the bottom of the picture. In his cabin his stove warms you
faster than it is getting cold; **the hot cocoa (4) warms you right through**. The captain
shouts when your hands go blue (`CAP_COLD`). Its fish: arctic char, halibut (20-150 kg, `heavy`:
it never tires below 0.7 - it is just heavy), cod (off the pier too), snow crab, the unicorn
fish (legendary; he insists it is real), and a chunk of ice.

## The launch pad, and Treasure Island

The sixth and seventh expeditions, asked for together on 2026-11-15 (the seventh is the payoff
for the treasure map, an idea from the cabin). Both are appended to `EXPEDITIONS`, so the pty
cases' counts down his list still hold.

**The launch pad**: $55, 30 s, the spinning rod. Harbours and space centres have the same gap
(720 cells) and the pads fall half-way between harbours, so one fixed `along` (1670) reaches the
pad from every harbour: she anchors 330 off the beach, about 170 short of it. On arrival she
turns to face it (`"face": "pad"`, `nearest_pad()`) and the clock of that pad is moved
(`_launch_shift`, as the menu's launch does) so it lifts off `PAD_LIFT` (40 s) after she
anchors - "Timed it, I did". **The twist**: at liftoff `Fishing.scare()` puts any bite and the
nibbles back past `PAD_SCARE` (60 s), and nothing new is chosen to bite before then
(`scared_until`), and he shouts `CAP_SCARED`. Its water, `"pad"`, is within `PAD_FISH` (220)
of any pad and more than 60 out - so the causeway is a place to fish from too. Its fish: the
three-eyed flounder (art `flat3`), the rocket fish, orange mackerel, plain mackerel, and the
booster fragment ($200 flat: the space centre buys them back).

**Treasure Island**: $80, 34 s, the spinning rod; 1700 off the beach (past the shipping lanes,
650-1500, so no ship sails through it) and 2200 down the coast. On his list only once you have
had a map (`"needs": "chart"`, `expeditions_for(tackle)`): `cabin_talk()` counts his tales on
`Tackle.tales`, and the sixth (`MAP_TALES`) is `CAP_MAP` and a map (`Tackle.map`, 4-11 paces;
`Tackle.charted` keeps the island on the list after). The island (`draw_island()`): a mound
of sand, one palm, a lagoon, and the skull rock with its lantern guttering on top. It stands
`ISLAND_AHEAD` on from where she anchors; the speedboat stops at its sand (`island_in()`), and
its water `"island"` is within `ISLAND_SEA`. The route out passes the floes of the harbour to
the south; she noses through them, as she does there. Its fish: parrotfish ("the captain's
parrot is deeply insulted"), lagoon barracuda, the golden fish (legendary, found nowhere else),
and coconuts. **The twist**: at anchor, `g` rows you ashore to the beach (`render_dig()`, a
drawn screen, not cast: the sea with the Herring lying off, the lagoon, the palm, the skull
rock): a d walk along it, space digs. The map says how many paces from the skull toward the
palm (`DIG_PACE` of the screen each); the line under the map's words counts your paces. A wrong
hole turns up something (`DIG_FINDS`) and the parrot calls WARMER! or COLDER!; the right one is
the chest, `TREASURE` ($1200), and the map is used up - six more tales for the next.

Fixed with these: the halibut never had its `heavy` flag (`_sp()` had no such argument), and
cod were not under the ice.

## The sea cave

The eighth expedition, asked for on 2026-11-15 (pitched as under the headland's lighthouse,
but the headland is on the river, where the Herring cannot go - so it is a rock of its own off
the coast). $65, 30 s, the spinning rod; last on `EXPEDITIONS`, so seventh on his list before a
map and eighth after. The rock (`draw_cave_rock()`, `CAVE_ARCH_ART`, pitted grey with the arch
in its foot, the dark through it the dark behind) stands `CAVE_AHEAD` on from where she anchors,
420 off the beach and 950 up the coast; the speedboat stops at it (`cave_in()`).

On arrival you are not on her deck: he rows you in, and you fish from the dinghy
(`DinghyDeck`, low) at the middle of the chamber, facing in, the arch behind you.
`Fishing.cave` is `(x, z, mouth)`, and `render_fishing()` asks `render_cave()` for the picture
instead of `render_street()`. **It is black** - the owner asked for it "completely dark" the
day it was built, and the first version's glowworms on the roof, the texture on the wall, and a
moonbeam down through a hole in the roof all came out again. What is left: the wall is still
there by screen column (`cave_wall()`, round and not quite, `CAVE_R`) - it makes `v.walls`, so
it hides what is behind it and `put_point()` and the rest work as on the street - but nothing on
it is drawn; **behind you**, the arch at the `mouth` bearing with the night, the moonlit sea and
the Herring's mast light through it, and **the moon on the water coming in under it**
(`cave_moonlit()`: fanning in from the arch `CAVE_MOON` units, fading the further in and as the
tide closes the arch); your lantern's ring of lit water round the dinghy (`CAVE_LAMP`) and the
lantern itself at the bow; and drips - a falling drop and a ring inside the lantern's light,
the word "drip" where you cannot see them. 2 ms a frame at 160x45, 5 at 300x90.

**The dark.** `cave_seen()`: the lantern's ring and the moonlight by the arch are seen,
the rest is not. Cast
out there (`cave_dark()`) and the float is not drawn at all: the line goes from the rod to the
edge of the lantern's ring and off into the black (`cave_end()`, for `draw_rod()`), the rod
tip knocks at a nibble and a bite as with no float, and `cave_cues()` writes what you hear
where the float is - plip at a nibble, PLOP! when it goes under, splash in a fight. The water
there is `"cavedark"`, the seen water `"cave"`: **the Old One bites only in `"cavedark"`.**

**The tide.** `Fishing.tide` (0 to 1 over `CAVE_TIDE`, 180 s, from `trip["cave_t0"]`) lowers
the arch (`CAVE_ARCH`) and fills the ARCH bar along the top (`draw_tide()`). He warns you at
half and at 0.8 (`CAP_TIDE`); at 1 he rows you out whatever is on: a fish on the line is cut
loose (`Fishing.key("stop")`: the rig with it, as cutting one loose always does), a card on the
screen is kept, and she goes home (`trip_home()`, which the x key now uses too).

There is no cabin in the cave: `c` gets `CAP_CAVE_CABIN`. Everything he says in there comes back
off the rock (`cave_echo()`: "matey... atey... tey...").

Its fish: blind cave fish (no eye on its card, art `blind`), the cave eel (`cracks=True`: the
wreck's snag, `Fishing.wreck()`, works for it in the cave - it pulls for a crack, IN A CRACK,
s gives it slack; the gauge says CRACK), the cave lobster ($45 a kilo, squid only), the Old One
(legendary, 30-90 kg, art `catfish`), and the smuggler's rum keg ($60), a rusty lantern and a
skeleton's boot.

