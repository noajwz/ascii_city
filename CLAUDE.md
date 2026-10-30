# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working in this repository.

An endless procedurally generated ASCII city, walked through in the terminal. Written for fun.
**No package, no dependencies, no config files** — it is one stdlib-only Python script
(`curses`, `math`, `random`, `unicodedata`) and nothing else. Adding a third-party import would be
a departure from the premise; prefer stdlib.

```bash
python3 ascii_city.py
```

It came out of `noajwz/TUI` (formerly `TUI-CLAUDE`), where it lived alongside a handful of smaller terminal programs
until it outgrew them. The history came with it.

Ruff is the linter, run with defaults (`ruff check . && ruff format .`) — there is no
pyproject/ruff.toml, and ruff is not installed on the machine this was written on. Keep lines under
89 characters; that is the one rule the code has actually been held to.


An endless procedural city with **two renderers** over one screen loop. Both `render_skyline()` and
`render_street()` fill the same `(ch, co)` pair of character/colour grids, so the blit loop, the HUD
and the input handling in `main()` serve either; `tab` switches, and each view keeps its own camera
so switching back and forth loses neither position.

They also share one weather clock. Both call `rain_intensity(now)` and `lightning(now, wet)`
themselves rather than being handed a number, so the downpour you tab out of is the downpour falling
on the skyline, and a strike lights both. This is worth a test, and has one: tabbing used to land you
in a dry, still postcard, which is exactly the kind of break that no amount of looking at one view
will show you.

`wander()`, behind the spacebar, blends every direction it probes by score instead of picking the
best one. Picking the winner outright makes the walk twitch, because the winner changes from one
frame to the next: measured over eighty seconds that was 395 hard snaps, some of them a full
3.8-radian flip. Blending gives a heading that moves continuously and sits between two equally good
options rather than flapping between them; `main()` then eases towards it and slows down through
the turn, which takes the frame-to-frame change from 0.28 rad to 0.01.

Nothing about the city is stored. The skyline is cut into chunks seeded by name
(`f"city|{layer}|{i}"`); the street's every question is answered by a hash of the cell's own
coordinates. Caches (`_cache`, `_open_cache`, `_lots`, `_road_cache`) are throughput, not state —
clearing them changes nothing you can see, and there is a test that proves it. They evict through
`_evict()`, which drops the oldest third rather than wiping the lot: a full wipe makes the next
frame rebuild every cell in sight at once, and on a long enough walk that is a visible hitch. Dicts
keep insertion order, and while you are moving the oldest entries are the ones behind you. Generation stores a
**`tone` float rather than a curses colour**, because the palettes differ between an 8-colour and a
256-colour terminal and a building has to be the same building in both.

## The skyline is a waterfront

Three parallax layers of chunk-generated buildings standing on the far bank, and the water in front
of them. `dens` falling away with distance is most of what separates the layers — the far bank is a
dim shape, the near one is a lit building — and `gap` widening as it comes forward is what keeps the
near layer a row of towers with sky between them instead of a wall across the bottom. Both were the
fix for a view that had become an unreadable mash of glyphs with no silhouette in it.

The street has the matching pair. `road_span()` gives back where a road starts and how wide it is,
not merely whether a cell is one, and that is what lets `draw_ground()` find the middle of a street
to paint a dashed `'` line down — on the wider ones only, and never through a junction, which is how
it works outside too. With the kerb already marking where pavement meets road, that is enough to
tell street from building at a glance even with the neon going.

`reflect()` mirrors everything above the waterline into the water. An ASCII reflection lives or dies
on being broken up: same glyphs, displaced sideways by a swell that changes with depth and time, and
thinned out with depth until it is gone in eight rows or so. Let it survive further down and it
stops reading as water and starts reading as the picture having been printed twice. Rain roughens
the surface, so the harder it comes down the less of the city you can read in it.

## The street view is a grid raycaster

It did not start that way: when you could only walk up and down one avenue, the facades were two
planes at fixed `x` and a column could solve directly for what it saw. Free turning killed that.
`cast()` now runs a DDA over cells of `CELL = 5.0` world units, in cell units so the arithmetic
stays the standard form, and returns the walls a column meets nearest-first. Because the ray is
built as `dir + plane * cam`, the distance that falls out is already measured along `dir`, so
there is no fisheye to correct at the edges.

- **No depth buffer.** Three per-column arrays — distance, top row, base row — are the whole of the
  depth information, because a facade is a vertical plane. That is why the sky is drawn *after* the
  walls: an unlit window is a blank cell, so `wall_top` is the only thing that knows a building is
  in the way, and `hidden()` is the test every prop, drop and reflection uses.
- **Casting does not stop at the first wall**, because a tall building behind a short one still
  shows over its roof. Hits are drawn near-first, each clipped to the rows above everything already
  drawn, and the loop breaks once the cover reaches row 0.
- **A ray that hits nothing** is looking out of the city down a cross street. `draw_sky()` gives
  those columns a taller haze silhouette; without it the vanishing point is a hole.
- A horizontal line on a facade is a **slope on screen**, so roofs, awnings and footings go through
  `facade_line()`, which fills from the previous column's row to this one's. One cell per column
  instead and the line breaks into dashes.
- **The roofline gets its own colour**, brighter than anything else on the building, through
  `roof_colour()`. It used to take the same near-black trim as the awning and the balcony banding
  below it, which on a *low* building — the only kind whose roof is on screen at all, since a tall
  one's is off the top — meant the top edge lost to its own balconies. It fades in one step rather
  than dropping straight into the fog, because the rooflines you can actually see are the
  middle-distance ones. And no district's roof glyph may be the same mark as its own banding, which
  is asserted: Chinatown's `~` upturned eave exists because its balconies were already `=`.
- **A tower's dark windows are drawn, faintly.** Reported: "hard to make out a skyscraper because
  of the night sky". Measured first, and it was not the outline — 87% of the cells where a tower
  meets the sky already had a corner bar. It was the face: an unlit window was a blank cell, so a
  tower with few lights on was black with scattered points, which is exactly what the sky is.
  Unlit windows on buildings `TOWER_GRID` tall and up are now a `.` in the darkest grey, on the
  window grid — regular, which stars never are. Only on the tall ones: a low building is outlined
  by its own roof, and putting the same grey dots on everything made the districts measurably
  more alike (the docks/Chinatown/financial pairs dropped under their 0.40 bar).
- **Three lines make a building read as a building**: the roof, the awning over the shopfronts, and
  the footing where the wall meets the ground. The footing is the one that does the most work and
  was the last to arrive — with enough neon and lit windows in frame the eye stops being able to
  tell where a building stops and the street starts, and a line along the bottom settles it
  instantly. It is drawn last in the column so nothing paints over the join, and it is `CURB`
  rather than the building's own trim, which puts it in the same visual language as the kerb: this
  is ground level, everything below it is street.
- **Corner bars are only for real corners.** Every cell is its own building, so a naive "the face
  changed, draw a bar" test puts a picket fence down every street. `draw_walls()` first checks
  whether the column to the left was the building *next door on the same plane*; that is a terrace,
  and the step in the roof line is the only edge actually there.
- Windows get the middle of their bay or a near facade smears into horizontal stripes; a flat sign
  letter gets exactly one column, the first of its bay, or the word stutters as `CCCLLLUUUBBB`.
  `draw_hung_sign()` lays its letters out **in rows, not world units** — spacing them by a true
  height makes two of them round onto the same row as the sign recedes, and a HOTEL with the T
  missing is worse than one slightly the wrong size.
- **A painted sign has to be read left to right on screen, and `u` does not run that way.**
  `cast()` measures `u` with +z along an x-facing wall and +x along a z-facing one whichever
  side you stand on, which is right for two faces and mirrored for the other two — OPEN read as
  NEPO on every building whose front faced -x or +z, and nothing else on the facade noticed,
  because a row of windows reads the same both ways. `sign_u()` flips it for those faces, and it
  was found by looking at a screenshot, not by any test: the test came afterwards.
- A projecting sign hangs **perpendicular to the wall**, and its two edges are projected as world
  points rather than stepped out in screen columns. Framing it in screen space makes it a billboard
  that turns to face you wherever you stand, so walking along the pavement swings it out into the
  road and it reads as something you walked straight through. Done properly it foreshortens to a
  strip when you are square in front of it and opens out as you come along the street — which is
  when a sign like that is meant to be read anyway. Drawn edge-on the two sides land in the same
  column, so the frame is suppressed rather than burying the letters behind itself.
- **One sign per frontage.** Reported as "too many lights to make the buildings out". In
  Chinatown a five-metre shopfront could carry a flat neon, a hanging sign and a string of
  lanterns at once, and hanging signs alone were 84% of the lit cells in those streets. A face
  with a hanging sign now drops its flat sign (one in five keeps it) and its lanterns (one in four
  keeps them), decided off values already drawn so nothing else moves; Chinatown hangs signs on
  half its frontages instead of 85%, the market a third. Past `SIGN_LIT_FAR` a hanging sign is
  drawn in its unlit tube colour, so the near ones stand out and the far end of the street goes
  quiet. Measure "lights" as the *lit* tube colours and bulbs only — counting the dark tube colour
  as a light made the first measurement say nothing had changed.
- **A sign hangs from its top and reads downwards, so where it ends is what matters.** Constraining
  the top alone guarantees nothing: a quarter of them used to finish below eye level and one in
  thirty ran into the pavement. `SIGN_CLEAR` is the floor the last letter has to clear, and a
  building too short for the whole word does not get a sign at all (which costs about 1% of them).
  There is a ceiling too — hang it anywhere in the building's height and every sign on a tall block
  ends up in the sky where nobody in the street is looking.

## Parts of town

`DISTRICTS` is a table and `district_at()` picks a row from it. Everything a building is — how tall,
how lit, whether it carries neon and in which of the eight tubes, whether its frontage is strung
with lanterns — comes from that row, so a district is one line of data rather than special cases
scattered through the generator. `scale` multiplies the block's own base height and `lo`/`hi` clamp
it, which keeps a block's internal coherence inside a district's range.

The nine: **downtown** (the tall neon one, still the commonest), **residential** (low, banded with
balconies, no signs at all), **old town** (pitched roofs), **chinatown** and **market**
(lantern-strung, and restricted to warm tubes), **financial** (enormous, cold, and dark but for the
occasional whole floor left on), **docks** (low corrugated sheds, roller doors), **yokocho** (the
alleys are the point — signs and warm light down a back lane where everywhere else has a bare bulb
and the dark palette), and **park**.

**Height and window density are nearly useless as district markers, and finding that out took a
measurement.** From the street you see four storeys of frontage and hardly any roofline, and the
facade is 60–80% structure — corners, roofs, awnings, bands — with lit windows under a seventh of
it. So the things that actually separate a district are, in order:

1. **Its palette.** `wall_colour()` picks the family named by the district, and this carries more
   than everything else combined. Amber housing against cold blue glass against rust-lit sheds is
   obvious at a glance in a way that a different window *glyph* never is.
2. **Its structure** — `band` draws a line at every storey (balconies in Chinatown, ribbing on a
   corrugated shed), `roof` varies the roofline, `ground` and `gap` decide what the shopfronts are
   made of, and `whole_floors` is the financial district's alone: a glass tower is not lit window by
   window, it is black with one floor on because the cleaners are there. That one is keyed on
   `b["block"]` rather than the cell, or the lit floor is five metres wide and stops reading as a
   floor at all.
3. **Its props** — lanterns, and `alley_lit`.

There is a test for exactly the thing that was reported, and it is worth keeping honest: a histogram
of what gets drawn on the facade, compared pairwise between districts. Measured on **glyphs alone**
the worst pair scored 0.08 — indistinguishable, matching the report. With the colour of each cell
included and the palettes in, the worst pair is 0.43 and the median 0.69. Count only the rows above
the horizon, or road, footings and rain — identical everywhere — swamp the comparison.

The grid of districts is offset a different amount on each row so the boundaries stagger like
brickwork rather than lining up into one seam across the city. Note that a district is 180 units
across and you can see 130, so from the middle of the financial district you will still catch the
neon of whatever is next door down a long street — which is correct, and worth not mistaking for a
bug.

**The park is the one that changes the world model**, not just its parameters: `is_open()` returns
true for park cells, so it is ground you walk on, except for the quarter of them that are a clump of
trees. Making a clump *solid* is what makes it free — the raycaster and the collision already know
what a solid cell is, and `draw_tree_column()` just draws it with no roof line, no corner and no
footing, its canopy height wandering along the clump so the top comes out ragged. Clubs and casinos
are barred from parks: the cell would be a clump of trees and would be drawn as one, so the venue
would exist and be invisible. Nothing is hung on a tree either — `draw_props()` skips tree lots,
because the alley's bins and bulbs were turning up against the trunks.

The parks are small and stay small. The big wood is a different thing — see *The woods*.

## The night sky

The city is always at night, so the sky is the one thing you look at that is not made of buildings.
`night()` gives each night its own character off a hash of its number — clarity, the moon's phase and
altitude, whether the milky way is up and at what tilt, how warm the starlight runs, how many
meteors. Same night whenever you come back to it, and nothing like the next one.

Two things about it are worth keeping:

- **A star has to clear every roof in its column, not the nearest one.** `draw_walls()` returns
  `wall_top` for the *nearest* wall — which is what occlusion wants — and a fourth array `sky_top`
  holding the highest roofline of anything in the column. They differ the moment a tall building
  stands behind a short one, which is most of a city, and the sky wants the second: using `wall_top`
  drew stars straight into the part of a far tower showing above a near roof.
- **The waterfront draws the city first and the sky around it.** Stars-then-buildings looks
  equivalent and is not: `blit()` leaves blanks alone, so every unlit window becomes a hole with a
  star in it. The silhouette is what a star must clear, not the lit parts of it.
- **Stars go on visible cells, not over the hemisphere.** The first pass scattered them by bearing
  with a random altitude, and from a street that put five in six behind a building: you got one or
  two stars and no sense of a sky at all. They are keyed on `(bearing, row)` instead, which still
  pins them to the compass so they hold still while you turn — there is a test that turns the camera
  and checks not one of them moved.
- **Most of them are faint, and there are fewer than there were.** The sky was reported as "too
  distracting and too much": measured, a clear night with the milky way up was a seventh of
  everything above the roofs, and a fifth of the stars were bright. `STAR_RATE` and `BAND_RATE`
  are half what they were and `STAR_TIERS` makes nine in ten `.` or `'` — a typical night is now
  under 2% of the sky, the clearest under 7%, and one star in ten is bright. A sky where every star
  is bright reads as static and the bright ones stop counting for anything. The colour
  works the same way: mostly grey, a few warm and a few cold, and the milky way in its own dim blue.

Clarity is the whole range from 0.22 to 1.0 with a median around 0.43, so a properly clear night is
worth staying out for and most nights are not one.

**Cloud comes and goes on its own.** `cloud_cover()` is three slow waves on their own periods, like
the rain's, and rain and snow raise it to cover the sky as they come; the sky is
`clarity * (1 - cloud)`, so it goes by degrees rather than at a threshold. Of the time it is not
raining the sky is clear about three quarters of it, cloudy a fifth, overcast one stretch in twenty
— `CLOUD_BASE` sets that, and it was half clear at first, which was "too often" — and the HUD says
which (`sky_word()`). Under cloud the stars and moon go, and nothing is drawn in their place. There
was a faint drifting texture of `~` and `-` for a while, meant as cloud lit from below; it was
reported as noisy, twice, and it is gone — a cloudy night is a night with fewer stars, which is what
one looks like. There is a test that a cloudy frame draws nothing the same frame held clear does
not. Natural cloud never hides the strange night — that sky is
lit by what is in it — but the held overcast does. `s` in the menu cycles the sky: as it comes,
held clear, held cloudy (a few stars through it), held overcast. The moon crosses through the night rather than sitting still, and at new
moon there is simply no moon, which is a perfectly good night in its own right.

`s` in the cheat menu cycles the sky (`_sky_mode`): as it comes, held clear, held cloudy, held
overcast. Held
overcast is a pitch-black sky — no stars, moon, milky way or meteors, from the street or the water,
and on the strange night nothing up there either, though the city still pulses to it. It is a sky
setting, not a weather: the rain, snow and lightning go on underneath it, and a strike still lights
the cloud from below. Held clear is how the star tests look at the stars.

`n` in the cheat menu steps to the next night. Nights are eleven minutes long, and waiting one out to
see whether the next sky differs is not a way to look at anything.

## Dawn

The city is always at night — except that one night in `DAWN_ODDS` ends. `night()` sets `dawn`
(never on the strange night: whatever that was, it is the one night the city does not wake up
from), and `dawn()` is how far into the morning it is: zero until the night's last `DAWN_LEN`
seconds, then rising to one and held there for `DAWN_HOLD` before the next night comes round as
every night does. One number drives all of it:

- **The sky pales from the horizon up** (`dawn_glow()`): an orange line where the sun is coming,
  peach above it, a pale blue climbing higher as it gets lighter, the dark at the top last —
  dithered, so it is a gradient and not stripes. The stars and the moon go with it. On the
  waterfront it is drawn before the reflection, so the morning lies on the river.
- **The city switches off.** `neon_attr()` puts each sign out when the morning passes its own
  `phase`, so they go one by one rather than all at once; window density falls to a tenth, and
  because a window is lit by the same hash against that density, the same windows go out in the
  same order every time. The far bank's windows go too — they are the skyline's own buildings,
  which the street's renderer never built, so they are thinned separately. What is left is the
  towers as black shapes against the light.

`@` in the menu goes to the next such night, five seconds before the sky starts to turn. The
cheat panel's special nights — the next night, the strange one, lanterns, fireworks, dawn — are a
**NIGHTS** group under OUT OF TOWN now; dawn's entry was the one that pushed the panel past 80x24
again, and the test caught it.

## The night the sky has something in it

One night in forty — about seven hours of walking between them — the sky is not stars. `night()`
sets `alien`, which forces clarity to 1.0 and the milky way up (whatever the weather was going to
do up there, the sky is lit by what is in it), and then `alien_light()` runs the whole field on the
same four-to-the-floor the club does: the stars pulse through the neon palette, the kick takes all
of them white at once, `draw_sky_beams()` swings beams across from somewhere past the horizon, and
three craft drift over with their rim lights going round.

Two things worth keeping:

- **A beam washes over the stars, it does not thread between them.** The first version only drew
  into blank cells, which works on an ordinary night and vanishes completely on this one, because
  there are no blank cells left. It still stops dead at the rooftops, which is what keeps it a thing
  happening *over* the city rather than a filter laid on the picture.
- **The density has to go up, not just the colour.** Recolouring a clear night's starfield left the
  sky filling 11% of itself either way — the same picture in different paint. It goes to about a
  quarter, which is what makes it read from a street, where you only ever see a strip of sky between
  the rooftops.

`SkyBox` exists so the sky effects can draw into the waterfront view too: they want a width and a
horizon, and the street's `View` carries a camera the skyline has no use for.

**The city gives up its own rhythms and takes the sky's.** `city_sync()` returns `flash`, `on` or
`off` on that night and `None` on every other, and `neon_attr()`, `club_light()`, the bare bulbs and
the lantern strings all consult it — so every sign in view breathes together, the kick takes the
whole city white at once, and whoever is playing the club gives up 134 BPM and mixes into it. Even
the dead tubes are cured for the night. Signs keep **their own colours** through it: one beat, not
one colour, or the city flattens into a single wash and stops being a city.

Everyone on the pavement stops as well — the smokers and the queue outside the club both switch to
`LOOK_UP` and stand still. It is the stillness that reads more than the figure: a street where
nobody is doing anything is a street where everyone is looking at the same thing.

Two things happen once a night rather than continuously. `draw_mother()` brings the big one over,
thirty-four cells wide and two minutes end to end, placed **by bearing** like everything else hung in
the sky — something that size sliding about as you turn your head would give the whole thing away.
Its blanks are hull and blot out the stars behind them; letting the sky through a shape this big
makes it read as a pattern laid over the stars rather than as something in the way of them.
`draw_landing_beam()` stops one of the sweeping beams dead over a rooftop and holds it there for
eight seconds, fading up and out so it arrives rather than switching on. No explanation offered.

`A` in the cheat menu goes straight to one, and the HUD says `~ something over the city ~`. Both
matter — one night in forty is unreachable by waiting, and from a street you might not look up.

## The river

**Water is the first cell in this city that is neither open nor solid.** `is_open()` used to answer
both "can you see through it" and "can you be here"; those two questions come apart at the water's
edge. `is_open()` is now the sight test and says yes to water — you can see clean across a river —
and `dry_at()` is the footing test that `can_stand()` is built from. Anything that means "a building
stands here" keys off `not is_open()` and so ignores water for free. Anything that means "you can
be here" has to ask `dry_at()`, or a bank cell passes its tests.

`river_centre(i)` is three sines, so the channel **meanders across the grid** and cuts blocks off
mid-street — it swings about 330 world units side to side. `river_span(i)` widens the band by the
slope of the meander, and that is not a nicety: `|j - centre|` is measured straight across, so on a
bend the band is a slanted strip and the channel would pinch to about half its width *exactly where
it turns*, which is the one place a river gets wider. Measured, bends now come out 6.7 cells across
against 6.8 on the straights.

**Crossings are one avenue in four** (`BRIDGE_ODDS`). Every avenue would be a crossing every 45
units, and a river you can step over anywhere is a boardwalk with a puddle under it. There is a test
that you can still walk from one bank to the other, because a river that cuts the city in half is a
bug however good it looks.

**Piers** reach out from the near bank and stop — at most half way over, never a fixed length. The
channel narrows to under five cells on some stretches, and a fixed seven-cell pier there quietly
spans it: you would have built a footbridge and called it a pier. The point of one is that it *ends*,
and you stand at the end with the whole city behind you — a view the street view does not otherwise
have.

The cheat menu reaches water differently from everywhere else: **not a ring search**. There is one
river, at a known place, so walking outward looking for it fails from anywhere more than a couple of
hundred cells away in j — which is most of an infinite city. `_water_spot()` goes straight to the
channel at your x and works along it.

## What is on the river

`reflect_river()` is a **planar mirror in one line**: a facade point drawn at row `r` reflects to
`2*horizon - r`, pushed down by twice the waterline offset for that building's distance. It falls
straight out of the projection — the height that put a point at `r` puts its mirror the same
distance the other side of the horizon, and the eye being *above* the water rather than on it is
the whole of the correction. It draws only into cells the river was actually drawn into (`v.water`),
so the reflection stops at the bank instead of running up the road.

**Only the lights cross the water.** Windows, neon and bulbs — anything alphanumeric or `*+@` —
and never the walls, roofs and corners around them, and past the first three rows a light becomes
a `:` with a short streak of `:` under it. The first version mirrored every glyph, thinned a
little with depth, and it was reported as "everything is mirrored": from a pier, where the water
is the bottom half of the screen, it was a second readable copy of the city with the signs still
legible in it. Lights alone are sparse — thirty-odd candidates from a bank — which is why the
streak exists: lamplight on water is a smear, and the smear is what makes it read as a
reflection rather than a dot. Measured from the bank it is about 75 cells, from a pier 40.

The pier deck is the same lesson: scattering `=` over it at random reads as noise, and at your
feet — where one cell is most of the screen — it was the loudest thing in the view. It is drawn
as plank *seams*, a `-` at intervals along the pier and dark timber between.

There was a barge. It went — asked for, and it was the biggest single thing cluttering the water.
If something moving on the river is ever wanted again, the shape it had was right: a line of them
spaced evenly along the channel, position a pure function of time so nothing is remembered.

**Buoys** blink on their own count and on a different one from their neighbour — a row of lights in
step reads as decoration, and the whole point of a channel marker is that it is not part of the
town. **Piers** get bollards, a lamp, a gull that shuffles but does not leave, and somebody fishing
off the end; a pier with nothing on it reads as unfinished rather than quiet. **Gulls** go round
over the water, the one thing out here on no clock at all.

**Mist** comes off the water on a clear dry night — `night()["mist"]` against clarity, killed
outright by rain, so you never get both. It is drawn *upward from the furthest water in each
column*, which is the one place it reads as depth rather than as dirt on the screen: the far bank
stands out of it instead of the whole river fogging.

**Cranes** stand on docks lots that touch the water, with no extra thinning — the docks are 7% of
the city and the river a narrow band, so their overlap is already about one lot in thirteen hundred.
Thinning that again (the first attempt used one in five) leaves no cranes at all, which is how it
was caught.

## The promenade, and what is on the water

**The bank is a walk now, most of the way.** `prom_at()` leaves the two cells nearest the water
open along two stretches in three of the near bank — a railing that follows the bank cell by cell
(a straight one walks into the river and out again on the meander), a lamp every three cells,
benches, someone leaning at the rail. It exists because everything else on the river — the piers,
the carnival, the big bridge — could only be seen from the deck or from across the water: the
buildings ran straight down to the bank. The promenade is where the river gets looked at from,
and `t` puts you on it. On the docks' stretch it is a quay: the cranes stand on lots that touch
the water *or the promenade* (`quay_at()`), or the promenade would have taken every quayside.

**Small things on the water, not a barge.** The barge went because a big hull at twenty units is
porridge. A **ferry** crosses the bay beside the big bridge and back every `FERRY_PERIOD` seconds,
easing off and on and waiting at each end, lit windows and a light on top, a wake while it moves;
**rowing boats** with a lantern in them drift down the channel with the current, one every
`ROWBOAT_GAP` cells. Both are functions of time and nothing is stored, the way the barge was.

**The lantern night.** One night in `LANTERN_ODDS` (never the alien night), lanterns by the
hundred go down the river with the current — a lattice along the channel, four to six a cell,
each on its own bob, the whole field sliding downstream, in three warm colours. Two things about
them: they are drawn **after** `reflect_river()`, or the far bank's windows lying on the water are
painted over them; and the ones beyond ~36 units land on rows the ground pass never textures
(`GROUND_FAR`), which is fine — they read as a line of lights receding along the river, which is
what they are. `z` in the menu skips to the next such night.

## Fireworks over the bay

One night in `FIREWORK_ODDS` — on its own hash, and never the strange night or the lantern night,
which have the sky and the river to themselves — there is a show over the big bridge's bay all
night. `shells()` is the schedule: a launch every `FW_SLOT`, three in four slots, and in the last
twenty seconds before every `FW_FINALE` three a slot. `shell_sparks()` is one shell: a trail going
up off the water for `FW_RISE`, then a sphere of sparks spread by the golden angle, slowing,
falling and fading over `FW_LIFE` — `*` then `+` then `.` — in one neon tube per shell, and one
in five a gold willow that droops. All of it is world points, so buildings hide the shells behind
them and the reflection lays them on the bay.

The burst height is the thing that needed tuning: at seventy units they went off above the top of
the screen from anywhere near enough to see them properly, so they burst just over the bridge's
towers. On the waterfront they are rings in screen space along the far bank, drawn before the
reflection. Near the bay the HUD says `~ fireworks over the bay ~`, and `!` in the menu skips to
the next such night — then `u` or `h` for somewhere to watch from.

## The carnival on the bank

A small fairground every `CARNIVAL_GAP` cells along the river, on the near bank: `fair_at()` is a
strip of open ground nothing is built on — `is_open()` says yes before the district gets a say, the
way it does for water — and `carnival_spots()` lays the wheel, the carousel and the stalls out
along it at the depth of the bank's *middle* column, so the meander cannot put one of them in the
river. There is a test that they all stand on dry ground.

**The wheel is world points, not a sprite**, and its plane faces the water. A ring of 56 bulbs
chasing round it in the neon colours, eight spokes, eight cabins that hang from the rim and stay
upright as it turns, an A-frame under the hub. From the far bank and the pier you see the whole
circle and, because the bulbs are `o`, the reflection pass carries it onto the water; from the
bank you are on it comes up edge-on as you walk towards it, which is how a real one does. It is
big on purpose — radius 10, twenty-odd units tall — because at radius 7 it was a squat little
ring against the buildings behind it. Everything else on the ground is a billboard: the carousel
with riders going round it on their own, four stalls in four colours, a string of bulbs the length
of the ground sagging between the poles, and a few people looking up. `i` in the menu.

## The big bridge

Once every `GRAND_GAP` cells along the river the channel opens into a **bay** and a suspension
bridge crosses it. `grand_avenue()` picks the avenue — the nearest one to a hashed spot that has
not been built over, so there is exactly one per stretch — and `river_span()` widens the channel
under it by a Gaussian bulge (`BAY_WIDEN`, `BAY_REACH`): a suspension bridge over a 35-unit
channel is a footbridge with pretensions, and 90 units is water worth spanning. No piers in the
bay; the bay is the bridge's. The crossing is forced (`bridge_at()` says yes for the grand avenue
whatever `BRIDGE_ODDS` said), and there is a test that you can walk over it to the far bank.

`draw_grand_bridge()` is all world points. Two towers standing in the water at 27% and 73% of the
span, each a pair of legs with the portal bracing between them that makes a suspension tower read
as one, in `EMBER_HOT` — the orange those bridges are painted; a red light on each top, blinking.
The legs stand `TOWER_OUT` outside the deck's edges, because the deck passes *between* the legs of
a real one, and with the legs on the deck edge the whole thing was squeezed into the avenue's
fifteen units. The main cables are three parabolas meeting at the tower tops (`_cable_y()`), drawn
dim, and it is the **bulbs along them** that draw the curve — which is what you actually see of
one at night, and the thing anyone would recognise it by. Suspenders every couple of units down to
the deck, lamps along it. It is drawn from `GRAND_SEEN` (340 units), because the towers are what
you see first.

**Where you can see it from is limited, and that is the city's doing, not the bridge's.** The
bank is not a promenade — buildings run right down to the water — so from beside the bridge you
are looking through a block. The views that exist are the avenue approach, where the tower stands
over the end of the street like a gate, and the deck itself, which is where `u` in the menu puts
you: the bracing across the sky ahead, the cables coming down either side, the far bank beyond.

## The headland, and the lighthouse

The far side of the bay is not the city. `headland_home()` puts a rocky promontory at the bridge's
far landing — centred six cells beyond the **bay's** bank, not the channel's, which was the first
bug: the centre sat in the water. `headland_at()` is rock: open ground with nothing built on it, no
street, `the headland` on the HUD. `moat_at()` is the water round the other three sides, the third
kind of water in the city and, like the lake, free — `water_at()` is river-or-lake-or-moat and
nothing downstream asks which. The far city's avenue stops at the moat, so the only way onto the
rock is over the bridge, and there is a test for both directions: you can walk off the deck to the
foot of the lighthouse, and you cannot walk there from the far bank.

`draw_lighthouse()` is world points: a stack of rings, white with red bands, so it tapers and stays
round from wherever you see it; the lantern room on top with a light that is never off; a bench
at the point and a lamp by it. The **beam** is the reason the headland exists — a line of points
from the lantern out to `BEAM_REACH`, with a fainter one thrown the other way the way a real lens
does, going round once every `BEAM_TURN` seconds. It goes over the bridge, the bay and the town
without asking any of them, and where it passes over water it is drawn on the water too: a beam
that only exists in the air reads as a stick. Drawn from 420 units, further than the bridge,
because a moving light is the first thing the eye finds. `h` in the menu puts you at the landing
looking out to the point.

## The bridges

The crossings were building sites for a while — hoardings, a hazard board, a crane — as a
placeholder, and were asked to be made cosier. `draw_bridge()` is a footbridge: a railing down
each side, lamp posts along it with a warm bulb on each, and a festoon of small amber lights slung
from lamp to lamp, sagging the way the yokocho lanterns do. The lamps are staggered between the
two sides so they are not in step, and nothing on it blinks — the buoys and the club have that,
and a bridge is where the city is quiet.

The lamps are what you see from the bank, and on the water under the bridge, because the
reflection now carries lights and nothing else — so the bridge and the reflection were designed
as one thing. Three tiers, railing / festoon / lamps, at heights that stay separate rows from
thirty units away; with the lamps at the festoon's height the two merged into one row of `o`.

**It has to stand out from the water**, and for a while it did not — a thin grey rail at knee
height over a deck of scattered dots, reported as "it blends in with the water". `draw_bridge_body()`
gives every footbridge a solid stone parapet with a pale `ROOF`-coloured coping on top, a kerbed
and paved deck, and under it the arches and piers going down into the river. All of it is
structure glyphs in structure colours, so the reflection — which carries only lights — leaves it
alone, and from the bank it is a hard band across the water with the lamplight lying under it. The
big bridge gets the same parapet with a girder underneath instead of arches, since its deck hangs
from the cables.

Two things were added on top, and both are about the bridge being *somewhere* rather than a
fixture. **Somebody is leaning on the rail** on one bridge in three (`leaner_at()`, hashed on the
crossing), looking down the river with a cigarette that flares on a slow count — the same job the
angler does for the pier. And **the four end lamps are drawn from 230 units** with a screen-space
halo round them (`draw_bridge_ends()`, `put_halo()`), against a bridge drawn from 85: walking the
bank looking for a crossing, you should see the lamps long before you can see the bridge. The halo
is in screen space because a world-space one collapses into the lamp's own cell from a hundred
units off, which is exactly the range it is for; and it paints over the far bank's walls but
never over another light, because that is what it is meant to be seen against.

The water cheats did not skip what was underfoot the way the ring search does, so `j` and `b`
returned the same pier and bridge every press. They move along the river now, and `B` goes to a
bridge with someone on it — the leaner is one in three, and a thing you cannot reach cannot be
checked.

**No key may differ from another only by case unless it is a variant of it.** The woods went in as
`W` next to `w` weather, and the rave as `R` next to `r` residential, and the report back was "W is
already weather" and "the rave cheat teleports me to just city" — lowercase pressed, weather cycled,
a housing district reached. Both were working. `b`/`B` (a bridge, the same bridge with someone on
it) is the one pair that earns it.

**The rig in the trees knew.** Whoever carried a sound system into the woods on the one night in
forty that the sky has something in it was not guessing: `rave_window()` is on from dusk to dawn on
that night, and `rave_light()` gives up 168 BPM and takes the sky's beat through `city_sync()`, the
way the club does. That was the theory kept alive through the rewrite, and it is now the rule.

## The woods

Not a park. The parks are the small green squares the city has everywhere; the woods are one great
dark block of trees a few districts across — Central Park sized, 700 by 420 units — with trails
through it, a hollow in the middle, and no street, light or building in it at all. There is one per
`WOODS_TILE` (2400 units) in each direction, jittered inside its tile, so from anywhere the nearest
is a long walk. `g` in the menu takes you to a gate.

**It is placed, not picked.** `WOODS` is a district row that is not in `DISTRICTS`: `district()`
returns it for any cell `woods_at()` says yes to, so `lot()` builds a tree there with no changes of
its own, and the HUD says *the woods*. The trees are taller than a park's and the leaf tone is
scaled down to the dark end of the palette — by multiplying the *same* random draw, so nothing else
about the city moves.

**No street runs through it.** `road_at()` says no inside the woods, so an avenue stops dead at the
trees; what continues it is a **gate** in `trail_at()` — the cells where a road meets the edge are
open through to a **ring trail** that runs a couple of cells inside the edge all the way round.
Three long trails and two cross trails wander through the interior and run into the ring, and a
straight path goes down into the hollow. The trails are two or three cells wide — one cell was
reported as "hard to walk through", and it was: `BODY` leaves a cell and a bit of slack, so any
drift in your heading is a bump. Off the trails the wood is `WOODS_OPEN` percent open, held under
the percolation threshold on purpose: you get some way in and have to turn round, which is what
being lost in a wood is. There is a test that every gate reaches the hollow on foot, and a second
that a good part of the wood is *not* on the way — both matter. At 46% open two thirds of it was
off limits; at 54% it is a third, which is the balance that feels right.

The edge wanders (`woods_depth()`), and its slope is held under a cell per cell so the ring trail
that follows it cannot break: a band two cells wide shifted by more than two cells between one
column and the next would come apart into diagonal steps, which `can_stand()` does not walk.

**What is in there with you.** `draw_woods_life()` runs whenever you are in or near the woods:
fireflies over the open ground on a dry night — mostly over the trail you are on, because the rest
of the wood is behind the nearest trees — and now and then two points of light low under a tree
that go out if you look for long enough. They sit just clear of the trunk on the side facing you,
in the next cell over, and only if that cell is open; inside the tree's own cell the tree hides
its own eyes, which is how the first version showed none at all. Nothing is ever drawn attached
to them. Rain puts the fireflies out.

**The lake** lies off towards one end of the wood, away from the hollow — two different places to
end up, and between them is where you get lost. `lake_at()` is the second kind of water in the
city, and it cost almost nothing: `water_at()` is river-or-lake, and `is_open()`, `dry_at()` and the
ground pass ask that instead of `river_at()`. Everything else the river has — `v.water`, the mist,
the reflection — works off the cells that were drawn as water and never asks which water it is.
Any trail that reaches the shore joins the **shore path** that runs round it, because a trail that
simply ran into the lake would end in it. The gulls stay the river's.

The reflection pass reflects **the sky now, not only the facades** — it used to start at the
roofline, and over a lake ringed with trees that left nothing to mirror but black. Above the
roofline anything drawn is a light (stars, the moon, the beams on the strange night), and a canopy
lit by the rig counts as one too; on the facades it is still only the lights that cross. `e` in the
menu stands you on the shore.

## The rave in the hollow

The Samurai Jack episode is the reference — *Jack and the Rave* — and the thing taken from it is
not the lights, it is the crowd. In the club the queue is *in time*, each dancer a fraction of a
beat off the next. In the hollow they are **in step**: hoods up, and every one of `CROWD` figures
does the same thing at the same instant with no offset at all, arms up on one half of the beat
and down on the other, all facing the altar with their backs to you. That is what makes it not a
party. Between the kicks the hollow goes dark, and what is left is their eyes.

The **booth** stands at the far end — a stack with the decks on it — and **Aku is on the decks**.
In the episode it is one of his minions with headphones shaped like his horns, and Jack mistakes
him for Aku; here it is the real thing. He is the one sprite in the city that is not one colour:
four layers blitted at the same anchor (`AKU_BODY`, `AKU_FACE`, `AKU_BROW`, `AKU_WHITE`), which
works because `blit_sprite()` paints only the non-blank cells — the crest and horns in the dark
purple the rig leaves on things between hits (white when the strobe takes everything), the face a
filled green, the brows red, the eyes and the grin white. He stands up behind the booth, which hides
whatever he has for feet, towers over it, and bobs on the kick. The beams are drawn *before* him so
they come up from behind; drawn after, they were painted across his face. Beams go up out of the
booth into the canopy, which is what you see from far off; and on the ground `draw_ground()`
paints **rings** of light pulsing outward from the altar on every beat, keyed on `v.hollow`, which is
the one thing in the city meant to look like it is doing something to you. On the trails near the
hollow stand the ones still on their way, hoods up, facing it, not moving (`draw_drawn_in()`).

The rig's palette is `RAVE_TONES` — magenta, purple, green, cyan — never the full neon rainbow,
which is the club's. `rave_light()` is 168 BPM with no colour wash between kicks, just dark. On the
alien night it takes the sky's beat instead.

**And the one who is awake.** Jack stands at the near edge of the hollow, off to one side of the
path in, with his back to the altar and facing whoever comes down the path — topknot, white gi, the
sword at his hip. Everything about him is the crowd inverted: pale (`MOON_DIM`) where they are
dark, still where they move, and no light in his eyes between the kicks. Stand within seven units
and the HUD gives you his line instead of the bearing. He is only there while the rig is on; he
came for it.

**Rare and unreachable are different things, and the menu has to reach it.** `x` calls
`force_rave()` and stands you at the edge of the hollow facing the altar; the HUD gives a bearing
and a rough distance from up to 700 units (`rave_hint()`), because a wood is disorienting on purpose
and a fact you cannot walk on is no help.

## People walking

The streets used to be empty but for smokers and queues. `near_walkers()` puts a **lane down each
pavement of every street** in view — avenues along z, cross streets along x, found by stepping
across the view and asking `road_span()` — with slots `WALK_SLOT` apart sliding along it at the
lane's own pace and direction, and one slot in `CROWD_ODDS` filled. That shape is the whole
design: position is a function of time so nothing is stored and a walker is where they should be
whether or not you were looking; and because everyone on a lane moves at the lane's pace, two of
them can never walk through each other, which per-walker speeds would do within a minute. A
walker is drawn only where the cell is a street and dry — so they stop at the river where there
is no bridge, cross where there is one, and never go into the woods or onto the headland.

Two stride frames swapped on distance walked, not time, so the legs match the ground going by.
In the rain one in two has an umbrella up. Coats are the city's own colours. On the alien night
they all stop where they were when it began and look up — `now` is pinned to the start of the
night for them — which is what the smokers and the queue already do. `a` in the menu cycles
`some` / `busy` / `none`, a condition rather than a place, like the weather. They cost about
0.3 ms a frame.

## The elevated line

One avenue in `EL_EVERY` carries a steel viaduct down its middle (`el_span()`, keyed on the
avenue index and only on avenues that actually exist). It is all world points: columns on both
kerbs every `EL_COL` units, cross beams, two girders along the top and two tracks on them, and a
station every `EL_STATION` cells with a canopy and lamps. Points are laid along z only over the
stretch in front of you — an avenue is endless and a column of points down it is not free.

Trains run both ways, `EL_CARS` cars of lit windows, headlights, and a spark underneath now and
then, at `EL_SPEED` with `EL_SPACING` between them on a track; position a function of time, as
everything that moves here. Side-on is where they read best — roof line, a row of windows, the
deck under them; head-on from under the line they are a pair of headlights coming at you through
the steel. Within earshot the HUD says `~ a train overhead ~`. The line stops where the avenue
does, at the woods and the headland (`el_runs()`).

On the waterfront it is a dotted track across the middle layer — its ties on that layer's
parallax, so it sits in the town rather than on the glass — and every 48 seconds a train slides
across the screen along it, one way then the other, drawn before the reflection so it lies on
the water too. The train itself is in screen space, not on the layer's parallax — a simplification;
putting it on the parallax would make it slide with the town as you pan, which it does not yet. `=` in the menu
stands you under it, on the pavement by the columns, looking along.

## Tunnels

The first thing in the city with a roof over the road. A tunnel is a stretch of avenue under a road
deck `TUNNEL_H` up (`tunnel_run()`): **short** ones, two cells in the middle of a block clear of the
cross streets, one avenue-block in `SHORT_ODDS`; and **long** ones, from the middle of one block to
the middle of the next, only where the cross street between was built over — so nothing crosses
them, because a tunnel with a side street opening off it halfway is not a tunnel. Not on the
elevated's avenues, the big bridge's, in the woods or over water.

Four pieces make one, and the ceiling is the one that changed the renderer:

- **The ceiling** is solved per screen row the way the ground is — every row above the horizon is
  one distance to a plane at `TUNNEL_H` — and drawn where that point is over a tunnel and nearer
  than the wall in its column: blank, with a joint every two units. It also goes into `v.ceiling`
  with its distance, and **`put_cell()` will not draw anything further into those cells.** That is
  the general fix, and it took two goes: drawn last, the ceiling painted over a walker inside the
  tunnel in front of you; drawn before the rain, the rain past the far mouth painted straight over
  it. It is drawn right after the ground now and acts as depth for everything after.
- **The lining.** A face whose front cell is a tunnel is drawn as its building as usual and then,
  from the road to the deck, overwritten with dark tiles, grime and the odd tag — above the deck the
  building carries on as itself. Nothing is hung on it: no signs, smokers or bulbs.
- **The headwalls** — brick over each mouth, a railing on top — drawn only from their own outer
  side, or they showed through the ceiling from inside.
- **What is in it.** Under a short one, a fire in a can against one wall with three people round it,
  a blanket, a shopping cart, flames and sparks going up, and its light on the road through
  `collect_glow()`; the HUD says `~ a fire going under the road ~` near one. A long one is lit down
  the middle (`TUNNEL_LAMP`) and otherwise bare: it is being kept for something.

No rain or snow falls in a tunnel and no snow lies there. `[` and `]` in the menu stand you on the
avenue short of the mouth of a short or a long one, looking in. The nearby tunnels are found once a
frame (`v.tunnels`) before the walls, so the side-wall check is skipped wherever there are none;
they cost about 0.3 ms a frame on an ordinary street.

The cheat panel is **four columns** now — IN THE CITY; STREETS with PARTS OF TOWN under it; OUT OF
TOWN; WEATHER & SKY with NIGHTS under it — eighteen wide each, inside 80x24.

## Car parks

One block in `PARK_ODDS`, in the parts of town listed in `PARK_DISTRICTS`, is a car park instead
of buildings (`car_park_block()` on the block index, `car_park_at()` per cell). `is_open()` says yes
to it the way it does to the fairground, so the buildings round it face in across the open ground.
The ground pass paints it: a white line between every bay, a line across their ends, the aisle
down the middle bare, double rows `BAY_ROW` apart. Two bays in three have a car in them, by a hash
of the bay — the same cars every time, and only where the whole bay is car park, so none sits half
in the road; the odd one has its alarm light winking. Sodium lamps down every aisle spill orange
on the tarmac through `collect_glow()`, and each corner has a blue `[P]` on a pole and a pay booth
with its light on. `_` in the menu stands you on the street at its edge looking in.

`PARK_BAY` is the bay width. It was `BAY_W` for about a minute, which is already the facades'
window spacing — defined again further down the module, it would have quietly respaced every
window in the city. Everything here is gated on `car_parks_near()`, a few block hashes, because
scanning every bay in sight where there is no car park was most of two milliseconds a frame.

**Nothing vanishes as you walk up to it.** Sprites used to stop drawing at 1.6 units, and the walkers
and parked cars were dropped earlier still, on the theory that a six-row sprite blown up to forty
rows is porridge. It is not — it is a big, perfectly readable figure — and what read badly was
people and cars popping out of existence at arm's length, reported as "things disappear when I get
close". `SPRITE_NEAR` (0.7) is the cut-off for all of them now. A larger terminal makes the old
behaviour more obvious, because the same distance is more rows of figure.

## Traffic

Cars, on one condition that matters more than anything about how they look: **they must not
ruin the walking.** So they drive only on the wide streets — three cells across, `road_span()`
width 3 — and only in two lanes down the middle, two units either side of the centre line, well
clear of the pavements the walkers have; nothing comes down an alley, a lane or a narrow street.
A car that would pass within `CAR_CLEAR` of you is not drawn, so crossing the road is never a car
driving through your face. `near_cars()` is the walkers' design again: each lane is slots
`CAR_SLOT` apart sliding along at the lane's own pace and direction, one in `TRAFFIC_ODDS` filled,
so two cars on a lane can never collide and nothing is stored. They stop at the river where
there is no bridge (`dry_at()`), drive through the tunnels, and on the strange night stop where
they were with everyone else.

What you see is the end of the car facing you: two white headlights coming, two red tail lights
going, and a pool of light on the road ahead of each. One in `BUS_ODDS` on an avenue is a bus with
its windows lit. One in `POLICE_ODDS` is a **police car**: the lightbar going red, blue, red, blue,
and the street round it washed in the same colours through `collect_glow()`; within earshot the
HUD says `~ a siren somewhere ~`. `<` in the menu stands you on the pavement eighteen units ahead
of one coming towards you — at thirty it was three columns wide and lost among the shopfronts —
and `>` sets the traffic: some, busy, none. About 0.3 ms a frame.

## The highway, and keeping cars out of the water

Traffic first went everywhere a wide street went, which was into the river: every avenue meets it
sooner or later, most with no bridge, and the cross streets wander in and out of it with the
meanders — so cars vanished at the bank and came up out of the water on the far side, and drove
over the footbridges. And there were too many, two hundred within 400 units.

So a car in town drives a **trip** of `TRIP_BLOCKS` blocks, from the middle of one crossing to the
middle of another (`_crossing()`, `_trip_of()`), and only if the whole trip is dry road with real
crossings at both ends (`_trip_ok()`, cached) — the big bridge is the one water crossing that takes
cars. A car turning on or off at a junction reads as turning; one appearing mid-block reads as a
bug. The slots stay what they were, so the no-collision guarantee is untouched; presence is decided
per (slot, trip), so the same slot is a different car, or none, on its next trip. `TRAFFIC_ODDS`
went from 3 to 7: about 45 cars within 400 units.

Most of the traffic is on **the highway** instead: one wide avenue in `HWY_EVERY` (not the El's,
not the big bridge's, and no tunnel under it) carries an elevated deck at `HWY_H` on piers down the
median — over the river, the woods, everything, so it never has to stop at the water. Four lanes,
cars every `HWY_SLOT` one in `HWY_ODDS`, at 19-27 units a second: headlights one way, tail lights
the other. The deck's edges are spaced by distance (`max(0.3, dist * 0.018)`), not a fixed step: at
1.2 units the near stretch was a dotted line the shop signs showed through. From under the deck
the cars are not drawn — they are on top of it. `)` in the menu stands you on a cross street forty
units off, looking at it nearly square on: from beside it looking along it is a wall of beams, and
at an angle the buildings hide it. The HUD says `~ the hum of the highway ~` near one.

## The diner, and the billboards

**The diner** is the *Nighthawks* picture: `DINER_ODDS` on its own hash, wanting a wide street
out front (`_wide_face()`), the building cut down to two storeys. From the street the whole ground
floor is one lit window (`diner_window()`, in the wall pass) with the counter across it and three
people sat well apart, dark against the light, which is the point; `DINER` in pink neon over the
door, `24 HRS` under it, `OPEN` blinking, in screen space like the cinema's sign. Inside
(`render_diner()`) you are on a stool: lamps over the counter, the menu, the urns, the pie case, a
jukebox going through its colours, the cook moving behind the counter, the window onto the empty
street with the rain on it if it is raining, and `DINER_POUR` seconds after you sit down she comes
round with the pot. The seat is remembered the way the ramen bowl's is. `(` in the menu.

**Billboards** are soda ads (`ADS`, made-up brands) hung out over the wide streets from low roofs
(8-12 units: on a tall one it is off the top of the screen from anywhere you can stand) in the busy
districts, one in `BILL_ODDS`. They stand at right angles to the frontage, out over the road like a
gantry board, so they face along the street: flat against the frontage they could only be read from
straight across the road, and no street is wide enough to stand back that far — and set over their
own roof they hid behind the roofline of every building that side. Found per city block and cached
(`bills_in_block()`), like the sky decks' beacons. The trap: drawing each letter as a world point on
the board's plane looked right and could not be read — from any way back the brand and the slogan
rows project onto the same screen rows and overwrite each other. So the corners are projected in the
world (with the depth per column for occlusion) and the lettering laid out in screen space across
what they cover, and the board's blank cells are blanked so the city does not show through it. `$`
in the menu stands you down the middle of the street from one, forty units off.

## Getting lost is the feature

The layout is deliberately irregular, because the point is to be able to lose yourself in it.
`_is_road()` puts avenues on a period but varies their width and offset and drops roughly one in
thirteen entirely, so two blocks merge into a long one — **but never two in a row**. Left to chance
they clump, and three missing avenues in a row leaves a 180-unit stretch with no cross street
anywhere in it. That is rare enough that you only meet one after wandering for a while, which is
exactly what made it hard to pin down when it was reported as "the streets change when walking for a
long time": it stops reading as a long block and starts reading as the city having quietly turned
into somewhere else. `_built_over()` gating on its own predecessor caps the run at one and holds the
worst gap to 90 units, while still merging as many blocks as before. `_is_alley()` cuts a one-cell passage
through a block and then breaks it into stretches, one in five missing — that is what makes a dead
end you have to back out of.

`road_at()` is the switch everything hangs off: a face on a proper street gets neon, the lit
palette and someone smoking outside it; a face on an alley gets the `dark` palette at any range,
a third of the lit windows, a fire escape, a dumpster and a bare bulb over the door. No awning
either — an alley has no shopfronts to put one over. That single boolean is why an alley reads as
somewhere you should not go.

## Rain and lightning

`rain_intensity()` is three slow sines that never line up, so the weather swells to a downpour,
eases and occasionally stops; the HUD says which. Everything else scales off that one number —
drop count, the `~` standing on the road, how far neon spills, whether stars are out at all.

**A storm is a weather in its own right**, not something that happens to a downpour, and it is by
some distance the rarest of them: measured over a thousand simulated minutes it is about 4% of the
time against dry's 16%, the next rarest. `storm_window()` puts them on a slot the way strikes used
to be — one slot in six, a slot being three and a half minutes — so one rolls through roughly every
twenty minutes and lasts about a minute. A storm can outlast its own slot, so the slot before this
one has to be asked as well.

While one is overhead it is **violent**. It brings its own rain regardless of where the sines
happen to be, ramping in and off over seven seconds at the edges, and `lightning()` gives every
strike slot a strike — a slot being under three seconds — so one lands every 2.7s and the sky is lit
about 60% of the time. Each is scaled by a per-strike `power`, which is the difference between
weather and a metronome: 9% of them are faint things away over the next district, 23% right
overhead. Outside a storm there is no lightning at all, and there is a test that says so — a
downpour on its own is now just rain.

A flash is the only thing in the program that reaches across every pass at once, through `v.flash`:
the sky fills pale, every corner and roof line goes white, the rain lights up, and `wall_colour()`
promotes alley faces from the `dark` palette to `far`, which for half a second shows you what is
down there.

It took two goes to get this right, and both problems were only findable by measuring.

**How much** it lights. Lighting only the sky leaves every facade exactly the dark shape it already
was, so in a street — where there is barely any sky in frame — a strike lit 7% of the screen and
read as *the rain went white*. `draw_flash()` fixes it by filling the blank parts of every wall, so
the buildings become lit surfaces for the tenth of a second they are lit for, with their windows and
neon still showing through. That takes a strike from 7% of the street to about 52%, and the skyline
to 42%. Density matters: fill the walls as hard as the sky and the silhouette disappears into a
whiteout, so the walls go to roughly half what the sky does.

**How long** it lights, which is the half that was still wrong afterwards. `_strike_flash()` was
three sub-flashes with nothing in between, and driving the real program through a pty and counting
bytes per frame showed exactly what that means: three isolated repaints at 0.00s, 0.10s and 0.26s
and then a dead screen. At thirty frames a second that is a blink, and one you can sit through
without noticing the city lit up at all. The flicker now rides on a glow that does not go out until
the strike is over, with a tail decaying across about a second — 19 repainted frames over 1.1s
instead of 3 over 0.3s. The tail is most of what you actually register.

Both of those were reported as "lightning doesn't work", twice, and neither was visible from
reading the code or from a single rendered frame. Counting output per frame through a pty is the
tool for anything whose defect is *when* it happens rather than *what* it draws.

**Snow is the rarest weather of all** — about 2% of the time against a storm's 4.5%, a fall every
two hours or so, two to five minutes long (`snow_window()`, on its own slots, and a storm always
wins). While it falls it is the whole sky's weather: `rain_intensity()` is zero, so the streets are
dry and nobody has an umbrella up, the cloud takes the stars, and the mist off the river goes. It
**settles** — `snow_cover()` builds over `SNOW_SETTLE` seconds of falling and melts over
`SNOW_MELT` after it stops, so the city stays white a while once the sky has cleared. Lying snow
covers the ground ahead of anything else the ground would draw, bare road included, except the kerb
line, which is how you still tell street from pavement; every roofline goes white through
`roof_colour()`, the canopy whitens from the top down, and on the waterfront the top of every
building on the far bank. Flakes are on the rain's world-locked lattice but slow and each on its
own sway. `w` in the menu has a `snow` step, which also lays a full cover at once.

Drops sit on a **world-locked lattice** so they hold still relative to the city while you walk and
turn through them, and each is drawn as the segment it fell through since the last frame, which is
what gives the streak its slant — the wind's and the perspective's — without faking anything in
screen space. Reflections are exact rather than approximated: a mirror plane at `y = 0` puts the
image of a thing at height `h` in the same column, which is all `View.reflect_row()` is.

## The club

One building in `CLUB_ODDS` is not offices — roughly one every 265 world units, so you come across
one every few minutes of wandering. It is decided last in `lot()`, after the faces are made, so that
being a club changes nothing about the building it was otherwise going to be.

It carries **no sign of any kind**, which is the point: `draw_club_column()` replaces the whole
normal facade path, so there is no neon, no hung sign, no awning and no window grid — just a squat
windowless slab, speckled rather than filled so it reads as a mass instead of a hole in the street.
What gives it away is `club_light()`: four to the floor at 134 BPM, white on the kick, holding a
laser colour for a fifth of a beat after it, and the strobe let off the leash for the whole of every
eighth bar. That one function drives the slit windows under the roof, the door, how far the
light spills across the wet pavement — `collect_glow()` calls it too, so the puddles pulse in time —
and the five people outside, who go white together on the kick.

Three of those five are ravers and the rest are smoking about it. `draw_raver()` puts them on the
same clock as the sound system, offset by a fraction of a beat each so the pavement is in time
without being in lockstep, and gives them a glow stick in each hand. A stick is drawn as a short
trail of its own past positions: one moving cell reads as a speck, three read as a light. Keep the
swing tight — at arm's length the trails of five dancers overlap into noise.

## The casino, and the one door in the city that opens

Same odds as the club (`CLUB_ODDS`, different salt) and mutually exclusive with it, so a building is
never both — but a building with **no street frontage does not get to be one**. `_road_face()` is
what enforces that, and it is not fussiness: a casino down a five-foot alley can never be stood far
enough back from to read, its marquee lands off the top of the screen, and reporting "the casino
doesn't work" is the only possible outcome. It also gives the city a division of labour worth
having — the casinos out on the main roads shouting about it, the club down a back street with no
sign at all. It costs about a fifth of them (one every 335 units against the club's 265).

Asking about the neighbours from inside `lot()` is safe, and worth understanding: `is_open()` and
`road_at()` are pure functions of *their own* coordinates and never call `lot()`, so there is no
circle. Determinism is untouched.

`draw_casino_column()` is the club's opposite in every respect: bulbs chasing round the roof and the
door canopy, and every window in the place lit. `chase()` is the running-bulb pattern — a function
of where the bulb is and what time it is, so the whole building agrees without anything being
stored. Space those bulbs by half a world unit and at arm's length one bulb covers eight columns,
which reads as a lit stripe and not as lights; they sit close together on purpose.

`draw_marquee()` is what actually says *casino*. It is laid out in **screen space, letters side by
side**, unlike everything else on a facade. A marquee that shrank with distance is a smear long
before you can stand far enough back to see the whole building — and on a fifteen-foot street you
never can — so it is a stylised fixed size. Unreadable is worse than the wrong size, which is the
same call the hung signs make about their rows.

**It is one of the two buildings you can enter.** `venue_at()` is the trigger for both: stand in a
doorway and the room is drawn around you. Neither is an interior you walk about in, because a
five-metre cell has no inside to walk about in — what you get is a room drawn around where you are
standing, and `s` walks you back out of it.

Going into a casino gets you a room rather than a screenful of wheel. `render_casino_room()` puts the wheel in the middle of one: a ceiling with the lights chasing
along it, a back wall of slot machines with their reels going, the table with five people round it,
and the way out behind you. It degrades twice — no room for the furniture gets you the bare wheel,
no room for that gets you a line of text — because it has to survive a 20x8 window like everything
else. Everything else in the city is a solid cell that
`can_stand()` keeps you out of; the casino is a proximity trigger instead of an interior.
`casino_at()` scans the 5x5 cells around you for a door within `CASINO_REACH`, and while you are
standing in one, `main()` renders the wheel instead of the street. Walk back out and it is gone.
Stand there and it deals you another after `CASINO_AGAIN` seconds, which is the joke and also
correct. Movement keys stay live throughout — `s` is how you leave.

`Spin` draws the result first and then solves the flight to end on it: the ball eases to a stop over
a whole number of turns plus exactly the offset that lands it in the right pocket. So the wheel is
honest — a uniform `randrange(37)` — but the animation never has to guess where it is going, and
there is a test that casts 2000 spins back from the final angle and checks they agree.

`WHEEL` is the real single-zero pocket order, which is not decorative: it is what puts high next to
low and red next to black the whole way round, and you can watch it turn. `_spin_rng` is the one
random source in this file that is deliberately **not** seeded from position — everything else is a
hash of where you are so the city is the same city every time, but a wheel you could predict is not
a wheel.

**The slot machine** stands to the right of the wheel from 62 columns and 15 rows — it used to
need 78 columns and a full room, and on an ordinary terminal it simply was not there, so a request
to "add a slot machine" arrived for one that existed. `Slot` is honest the way `Spin` is: the result
is drawn first from `SLOT_WEIGHTS` (a 7 is rare, a `%` is not) and the reels are then shown stopping
on it, left to right, `SLOT_STAGGER` apart.

It is played for chips. A `Purse` is the pocket you carry round the room — the slot and the
blackjack table play out of the same one, so a win at one is chips at the other. `p` pays the bet
and pulls, `+`/`-` step the bet through `SLOT_BETS`; three of a kind pays `SLOT_PAYS` times the bet
by symbol (777 is a hundred), a pair gives the bet back, and `settle()` pays out once, when the
last reel stops. Against `SLOT_WEIGHTS` that returns about 82 chips in 100, which there is a test
for — the house wins slowly. A pull you cannot cover is refused and says `NOT ENOUGH`; at zero the
house stakes you `STAKE` again, because nobody is turned away from a casino for having lost. It no
longer pulls itself: a machine that spent your chips while you stood there would be a bug.

The one trap from before still holds: `9` puts you in the casino, and the panel used to stay open
so `p` was the park. A jump closes the panel now.

**Blackjack** is on the other side of the wheel, from 92 columns; the wheel moves over and gives
up radius so all three fit (`left`/`right` in `render_casino_room()` — the wheel's `cx` is not the
screen's centre once the tables are in). One deck, reshuffled under fifteen cards, dealer stands
on 17, blackjack pays three to two, `BJ_BET` a hand out of the shared purse. `b` deals, `h`
hits, `k` stands — `s` is taken, it walks you out. The dealer's second card stays face down until
you stand, and the dealer then takes a card every `BJ_DEAL` seconds rather than all at once: a
hand that resolves in one frame is a number, not a game. The one thing that bit: `now - t >= 0.8`
is false at `t + 0.8` in floating point, so the timer compares with an epsilon.

## The ramen counter

The third way into a building. One yokocho pub in `RAMEN_ODDS` is a ramen shop (`ramen_at()`,
hash of the face first because the lot is the expensive test), and from the lane it says so: the
sign over the door reads ラーメン instead of the pub's usual word, a split red **noren** hangs over
the door, and steam comes out from under it. `venue_at()` treats its door like the casino's —
stand within `CASINO_REACH` and `render_ramen()` draws the room round you.

Inside is the one room in the city that is **not on a beat**: the noren across the top, the menu
board with prices in yen and a lantern either side, the cook moving between two stock pots, the
others along the counter heads down and slurping on their own counts, and steam off everything.
You sit down to chopsticks; the bowl arrives `RAMEN_SERVE` seconds later — egg, nori, steam — and
the cook calls it. `seated` in `main()` is what remembers when you sat, keyed on the shop, so
walking out and back in is a new bowl. It is all ASCII inside: the room is drawn without the
`v.wide` bookkeeping, so the Japanese stays on the sign outside. `v` in the menu puts you at a
counter, and a second press finds another.

## The sky deck

One building `TOWER_MIN` tall in `TOWER_ODDS` with a street front has a lobby — `SKY DECK` over a
lit revolving door, and a mast with a blinking red light on the roof that is drawn from 150 units
off, so you can find one from across town. It is made `TOWER_TOP` tall, over everything else in the
city: the first ones were often hemmed in by taller neighbours and the view from the top was the
side of the next tower.

**The roof is the real city, rendered from up there.** `View` carries `eye` (how high the camera
is), `reach` (how far a wall ray goes) and `depth` (how many walls deep it keeps casting); at street
level they are `EYE_Y`, `MAX_VIEW` and four, and nothing about the street changed when every
`EYE_Y` in the renderer became `v.eye` — the whole suite passed untouched before anything else
went in. On a roof the eye is seventy-odd units up, rays go `ROOF_REACH`, walls fourteen deep, and
`draw_ground()` runs as far as the view does, because from that height the nearest ground on
screen is a hundred units away and the street's `GROUND_FAR` cut all of it. What you get is the
grid falling away under you, rooftops at every height, the river, the haze of the far city on the
horizon and the sky over it — about 19 ms a frame at 240x70.

Two things it took to make it read. **You stand at the parapet, not in the middle of the roof**:
`roof_view()` puts you `ROOF_STEP` out towards wherever you are looking, so you see over it and
down — from the middle, the parapet hid everything nearer than the next district — and turning
walks you round the inside of it. And **the parapet is solved per screen column**: each column's
ray leaves the roof square somewhere, the coping goes at that distance and the wall below it hides
whatever the city drew there. As world points, at arm's length a point every quarter-unit landed
five columns from the next and the rows between came out as stripes. A water tower and the mast
stand on the corners.

**The lift** (`render_lift()`) is the way up and down: facing the doors, they slide shut from the
sides, the indicator counts the floors with the arrow blinking, floor slabs go past the gap in the
doors the other way to the ride, a gauge on the wall shows the car in its shaft, and at the top a
ding and the doors open on stars; at the bottom, the lobby. `lift_times()` sets the pace from the
number of floors. In `main()` the lift is a state, not a room: walking into the lobby starts it,
nothing moves you while it runs, on the roof `a`/`d` look round and `s` calls it, and coming down
puts you back outside the door facing the street, a step beyond `CASINO_REACH` so it does not take
you straight back up. `^` in the menu stands you outside a lobby; one step in and you are riding.

## Up the fire escapes

One fire escape in `CLIMB_ODDS` down the dark alleys goes all the way to the roof, and says so
with a drop ladder at the bottom (`climbable()`: a real alley face, a real escape on it, three
storeys at least). The roof is the sky deck's roof view with `kind: "escape"` — an aerial and a
chimney stack instead of the mast, and the top of the escape over the parapet — so everything
about seeing the city from up there came for free.

Two things it took. **You climb by walking into the wall at the ladder, not by being near it**
(`escape_at()` wants you within `CLIMB_REACH` *and* facing the wall): an alley is one cell wide,
so a trigger by distance alone would have had you halfway up a building every time you walked
down a lane. The HUD says `~ a fire escape: walk into it to climb ~` when you are near one. And
**only off a roof nothing near overtops** — every solid cell within two has to be no taller —
because the first ones put you face to face with the wall of a taller building across the lane.
That still leaves about one climbable escape every 65 units of alley.

`render_climb()` is the ride: face to the bricks, the wall scrolling down past you with a window
every storey and a light on behind one now and then, the iron stairs zigzagging across it, a
landing at every floor and the count in the corner; at the top the sky opens out over the
parapet. It shares `main()`'s lift state — the same ride, a different picture — and `s` on the
roof climbs you back down into the alley. `|` in the menu stands you at the foot of one.

## The pictures

A cinema is as rare as a club — `CLUB_ODDS` on its own hash, a street front required — and from
the pavement it is a marquee over lit doors: NOW SHOWING and the title in a ring of chasing bulbs,
in screen space for the casino marquee's reason. `*` in the menu stands you in the doorway, and
`venue_at()` does the rest the way it does for the casino.

Inside you are in the back rows: the screen between red curtains, the projector's beam coming over
your head with dust turning in it, and three rows of the audience in silhouette — lit by the film,
so a bright scene throws light on them and a dark one leaves them as shapes. `film_frame()` is the
picture: a black-and-white short of six scenes, `SCENE_LEN` each — the title on grainy black, rain
on a window with a lamp outside, a night drive, two of them talking with subtitles (`FILM_LINES`),
the city with its windows going out, THE END — on a loop, and on the city's clock plus a per-cinema
offset, so you walk in on whatever is showing. Everything in the frame is keyed on the time within
the loop, grain and flicker included, so it really is the same film every time round; there is a
test that one loop on is the same frame.

The marquee's NOW SHOWING was in the star colour at first, and the stars-inside-buildings test
counted its letters as stars drawn inside a building. Anything in screen space on a facade needs a
colour that is not a star's.

## Inside the club

`render_rave()` is the club's answer to the casino room, and it runs off `club_light()` and the same
134 BPM the front of the building does — so the room you walk into is on the beat you could hear
from the pavement, and the strobe you saw leaking out of the door is the strobe that now has the
whole room. Truss across the top with the moving heads on it, lasers sweeping down out of them into
the crowd, the booth at the back, stacks either side that change on the kick, and a crowd in three
depths: heads at the back, bodies in the middle, and at the front the people you are actually
standing among, drawn with the same `RAVER_UP`/`RAVER_DOWN` art as the ones queueing outside.

The three depths are what sells it. One band of figures reads as a row of dolls; three at different
sizes reads as a room with people in it, and costs nothing but three loops.

## A yokocho is a kind of alley, not a part of town

It was a district for a while and that was wrong: a yokocho is not an area, it is *one lane*, the
same one-cell width as any other alley but lit and lined with places too small to have a front on
the street. `yokocho_at()` decides it per alley cell, keyed on the same run the alley itself is cut
into so a lit lane is a whole stretch rather than a few cells — about one alley in five.

Three things make it feel like somewhere rather than a gap between two buildings:

- **Lanterns strung across it**, wall to wall, by `draw_lantern_string()` — not hung off one facade,
  which is what a shopfront does. The wire sags in the middle and drifts, because a dead straight
  line of dots reads as a fence, and they only go over every other cell or the lane gets a ceiling.
- **Places you can see into.** A `pub` face draws its counter and the backs of the people at it
  through the window. Stacked in *rows* off the counter, not at true heights: half a metre between
  someone's shoulders and their head is a dozen rows when you are stood right outside, and they come
  apart into unrelated marks. One column a person, too, or a seat slot wider than a cell smears them
  into a row of Ms — the same trick the sign letters use.
- **Japanese neon over the door**, `draw_over_door()`, drawn in screen space with `put_wide()` so
  the characters sit side by side, stepping two columns at a time.

That means **what goes on a facade is not the district's business** when the facade gives onto an
alley. `face_kind()` returns `"road"`, `"yokocho"` or `None`, and it is passed around in place of the
old is-it-lit boolean, because a yokocho is lit but is not a street and must not look like one — its
walls take the red palette whatever district they stand in. A yokocho running behind a residential
block turns those back faces into bars, which is exactly what one is, so a test that "residential has
no neon" has to count street frontages only.

## Chinese and Japanese signs, and the one place the grid stops being one char per cell

Chinatown's hung signs are Chinese — 酒吧, 麵館, 火鍋 — and a yokocho's are Japanese — 居酒屋, 焼鳥,
寿司. Vertical stacking suits both, because that is how those signs are actually written.

**Only the hung signs.** Flat signs stay Latin everywhere, and that is not squeamishness: a flat sign
is painted along the wall, squashed by perspective to one column a letter, and the facade path writes
single cells with no way to reserve the column a wide glyph spills into — it corrupts the row. The
vertical signs are also the only ones you can read at a glance. Everything else in the city stays
ASCII.

The terminal is not the obstacle; the renderer is. A CJK glyph is **double-width**, and this is a
strict one-character-per-cell grid, so the cell to the right of one has to be claimed or the blit
loop paints straight over the character's far half. `put_wide()` writes the glyph, blanks the next
cell and records the position in `v.wide`; the blit loop steps over two columns for those and uses
`addstr` rather than `addch`.

Three things that only turned up by testing it:

- **Verify at blit time, don't trust the reservation.** A later pass — rain, usually — can paint
  over the glyph after its column was claimed, and stepping over two cells for a leftover
  reservation swallows a column of the picture. The loop checks `is_wide()` on what is actually
  there.
- **Two signs can overlap on the same row.** That leaves two double-width glyphs one column apart
  and the blit loop eats the second one whole. `put_wide()` clears anything already claiming those
  columns, so the nearer sign — drawn last — wins.
- **Ask the terminal, don't assume.** `wide_chars_work()` writes one into a corner at startup and
  checks whether ncurses moved the cursor two columns, the same way `termimage` asks about the
  graphics protocol rather than reading `$TERM`. A curses built without wide support moves it one,
  and every row with a sign in it would come out a column short. Without support, Chinatown falls
  back to the Latin word list, and it draws from the same `rng` call either way so the city itself
  is identical on both.

Testing this through a pty has a trap of its own: writing `\x1b[C` for an arrow key can be read as a
bare ESC, which quits. Two dead-end investigations started that way — the program was fine and the
harness was killing it.

## The cheat menu

**Anything new in the city gets an entry here, in the same commit that adds it.** This is a standing
instruction, not a nicety: everything worth looking at is deliberately rare, so a feature with no way
to reach it cannot be checked by the person who asked for it, and will not be. If what you added is a
place, give it a row in `CHEAT_PLACES` and a predicate for `find_place()`; if it is a condition —
weather, time, a mode — give it a key that sets it, the way `w` and `L` do. Both are a few lines.
Adding the feature and leaving the menu alone is an unfinished job.

`` ` `` opens a panel over the live view — over, not instead of, so that weather you change happens
in front of you. **A jump closes it** — you went somewhere to look at it, and with the panel still
up the next key is a district or another jump; the `-> where` note shows on the HUD for four
seconds instead.

Three columns: **IN THE CITY**, then **PARTS OF TOWN** with **SKY AND STREETS** (weather, strikes,
nights, the overcast, people) under it, then **OUT OF TOWN** (`OUT_OF_TOWN`: the river and the
woods). It was two, every new place went into the first, and it quietly grew past a 24-row terminal
and then a 30-row one — `draw_cheats()` draws nothing when there is no room, so the symptom is the
panel simply not opening. There is a test that it opens at 80x24. Letters belong to the panel while
it is up; the arrow keys do not, so you can still walk about with it open.

**It generates nothing.** The city is a pure function of its coordinates, so `find_place()` searches
for what is already out there and moves the camera to it. `CLUB_ODDS` and the rest are only ever
read. A jump is exactly equivalent to having walked there, and the test for it censuses every club
and casino cell in a patch, uses every cheat, and asserts the two sets are identical — the point
being that a debug tool that quietly made the rare things common would be worse than no tool.

The search rings outward from where you stand and skips anything within `CHEAT_SKIP`, so pressing
the same key twice hops to the next one rather than landing you back where you are. The woods and
the river are not ring searches: there is one of each per tile, at a known place, so they go
straight there. Order the
predicates by cost: `_door_spot()` tests the hash **before** `is_open()`, because it throws out 1199
cells in 1200 for one multiply and means `lot()` — which builds a whole building — is only reached
on a real hit. That is the difference between 7 ms and something you would notice. `_long_street()`
is the one that cannot be cheap, since it has to `probe()`, so it stops as soon as it finds a run
worth looking down.

Two traps worth remembering. Stand a teleport **back** from what it found — three units from a
facade is a nose against a wall — and make the alley search insist on being able to see somewhere,
or it happily drops you in a one-cell walled courtyard that is technically an alley and no use at
all. Both were caught by asserting on `probe()` distance at the landing spot rather than by looking.

Weather is two module-level overrides beside the weather functions: `WEATHER_STEPS` with an index
that `rain_intensity()` consults, and `_forced_strike`, which `lightning()` checks before its own
schedule so a strike can be had on demand even when dry. The flash envelope came out into
`_strike_flash()` so the one you asked for is the same strike the storm would have had. A test
compares 400,000 samples of both functions on `auto` against the formulas they replaced and requires
zero drift.

## Testing it

```bash
python3 tests/checks.py       # everything that needs no terminal; takes a minute
python3 tests/pty_checks.py   # ordinary play, driven through a real pty
```

Both exit 0 or 1, so `&&` them. No test framework and nothing to install — `tests/harness.py`
imports the module with its colours stubbed and the other two are plain scripts.

**Add to them.** Nearly every bug in this thing was found by measuring rather than looking, and
almost all of them came back as a regression test: stars drawn inside buildings, a sign that
swung out into the road, a cheat that took you to where a rave sometimes happens, a pier that
quietly spanned the river. The suite is the reason those stayed fixed.

Stub the module globals `init_colors()` would have set (`PALETTES`, `NEON`, `STAR`, `CURB`, `RAIN`,
`BULB`, …) with plain integers and call `render_street(View(x, z, yaw, w, h), now)` directly — it
returns a grid of characters to print or assert on, no terminal needed. That covers geometry,
determinism (render a spot, walk far enough to evict every cache, render it again, compare), and
navigation: 4000 `wander()` steps that never end up inside a wall. A quick ASCII dump of
`is_open()` over a few hundred cells is the fastest way to judge whether the street plan is
interesting. For the curses half, fork a pty and set the size with `TIOCSWINSZ` as with `wiki_tui`.

Rarity is worth asserting on rather than eyeballing, because these are rare enough that you will
not see one by accident in a test run: measure the gap between strikes over a simulated few hundred
minutes, and the mean spacing of clubs and casinos over a few hundred cells. Watch out for one trap
— the colour stub gives every colour the same id, so a test that counts "cells lit white" has to
give `FLASH` a distinct sentinel first or it matches the whole screen.

The casino is the one thing here that headless rendering cannot check, because it lives in
`main()`'s loop rather than in a render function. Drive it through a pty with `start_position()`
monkeypatched to a spot outside a casino whose door faces -z, walk in with `w`, and look for
`FAITES VOS JEUX` then a result then a second spin then `tab view` on the way out. Slice the **raw**
bytes and strip ANSI per segment — stripping first and then slicing by byte offset silently reads
the wrong window and will tell you a working feature is broken. That test earned its keep
immediately: `spin` was already the yaw rate in `main()`, and the wheel shadowing it was invisible
to every headless check.

A complete frame — render, `addch` loop and `refresh` — costs about 18 ms at 240x70 on a street
against a 33 ms budget, and about 30 on the riverbank, which is the worst view there is: open
ground means ground *points* outnumber cells fifty to one, and `draw_ground()` is per point. The
kerb test used to ask `is_open()` of the four neighbours per point and that alone was 46 ms on the
bank; it is asked once per cell now. If it ever slips again, the levers in order are the per-point
`_mix()` texture hashes in `draw_ground()`, `near_lots()` reach, `RAIN_REACH` and `MAX_VIEW`.

**Anything keyed on where the river is must be cheap, because `road_at()` and `is_open()` ask it
for every cell.** The promenade, the fairground, the headland and the moat all went in keyed on
`river_span()`, which was nine sines, uncached, and a street walk went from 4.5 to 6.2 ms a frame
without anything on screen changing — reported as "slower than it used to be". `river_centre()`
and `river_span()` are cached per column now, `near_river()` gates every bank test, and
`headland_r()` does its box test before its trig. The same thing happened again with the sky
decks: `near_towers()` hashed every cell in 150 units to find the beacons, four thousand calls a
frame on every street, and a walk went from 4.8 to 6.0 ms. `towers_in_block()` caches each city
block's towers once. Benchmarking every commit since the last good number is what found it. `tools/`-less rule of thumb: benchmark a
40-frame walk with the caches cleared (the profile in the session log) before and after anything
that touches `is_open()`'s path.
