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

`u` in the cheat menu goes straight to one, and the HUD says `~ something over the city ~`. Both
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
the next such night — then `b` or `i` for somewhere to watch from.

## The carnival on the bank

A small fairground every `CARNIVAL_GAP` cells along the river, on the near bank: `fair_at()` is a
strip of open ground nothing is built on — `is_open()` says yes before the district gets a say, the
way it does for water — and `carnival_spots()` lays the wheel, the carousel and the stalls out
along it at the depth of the bank's *middle* column, so the meander cannot put one of them in the
river. There is a test that they all stand on dry ground.

**Each thing stands back from the bank of its own column** (`bank_z()`), not the middle one's: the
bank slopes as much as half a cell a column along the meander, and more beside the bay, which over
the eleven columns of a fair is five cells — the middle column's depth put stalls at one end in the
river, and the test for it only ever looked at one carnival. Columns from world units go through
`int(x + BIG) - BIG`, not `int()`: the first try truncated a stall at column -280.5 to -280 and
stood it back from the wrong bank.

**Every big bridge has the carnival beside it, as near the headland as the bay allows.** In the
big bridge's stretch of river, `carnival_col()` puts the fair wherever along the near bank, within
45 cells of the bridge, its wheel comes nearest the headland's rock (`_by_the_headland()`, cached
by bridge), kept `CARNIVAL_BESIDE` clear of the bridge and off the ferry's landing. It belongs to
the bridge's whole 600-cell stretch rather than one of the 200-cell ones: it is the carnival of
the stretch with the bridge in it and of the one it starts in, replacing the hashed one in both,
and `carnival_over()` asks the stretch before as well, since it may run across the boundary.

And there **the fair is out on a pier**, the way a pleasure pier's is: `fair_pier_at()` is a deck
over the water across the width of the fair, `FAIR_PIER` cells out from the bank in each column
and never more than `FAIR_PIER_MAX` of the way over (`pier_tip()`, per column — a straight end was
held to a cell or two by the narrowest column). It is in `deck_at()`, so you walk on it and the
ground pass planks it like any other pier, and everything is laid out from its end: the wheel out
at the tip, the carousel and the stalls and the claw machine back towards the shore, bulbs along
the rails with posts down to the water, and PLEASURE PIER over the way on (`draw_pier_sign()`).

**Two rides stand on the pier with the wheel.** `draw_drop_tower()` is a mast near the pier's end
`DROP_H` tall, half again the wheel's height, so it is the first thing you see of the carnival from
the headland: bulbs up the front of it, a red light on top, and a car of riders round it whose
height is `drop_car()` — waiting at the bottom, a slow climb, a hang at the top, a drop that falls
rather than eases, the brakes — on `DROP_CYCLE`. Climbing, the lights creep up after it; falling,
they race down with it in white. `draw_coaster()` is a roller coaster over the east half of the
deck, the drop tower in the middle of its loop: `coaster_point()` is an oval that climbs and dives
as it goes round (never under 2.2, clear of the stalls), drawn through `draw_tube()` with chasing
bulbs on it and legs down to the deck, and a train of `COASTER_CARS` with a light on the front.
`coaster_at()` slows it up the climbs and speeds it down the dips as a function of where it is on
the lap rather than anything integrated, so nothing is stored. Both are only on the pier by the big
bridge; between them they cost about 1.6 ms a frame near it. `f` in the menu stands you on the bank
beside the pier, looking along it at them.

**Behind it the town is kept low** (`seafront_cap()`, applied in `lot()` before the faces are
made): six units at the water, rising a unit and a half a row inland for `SEAFRONT_DEEP` rows.
That is the reason for the pier as much as the distance is. With towers right behind it the
wheel's lights were lost in their windows; kept under the line from the headland over the top of
the wheel, the town leaves it the sky. The height test exempts those lots, as it does the venues.

Measured, wheel to rock: at a fixed place west of the bridge it was 64 to 214 units, because the
river meanders away from the headland in some stretches; at the nearest place on the bank, a
median of 78; on a short jetty, 58; out at the end of the pier, 54, and 31 at the closest. Laying
the fair out mirrored, wheel at the end nearer the rock, was tried and changed nothing — the
search already finds the nearest bank, and the wheel lands on it either way. There are tests of
the distance, of walking out along the pier to the wheel, of the town behind being kept low, and
of the bridge and the wheel being in the one view from the rock.

**Where the dry land starts is `shore_j()`**: `ceil(hi)`, because a row is river while it is under
`hi`. It used to be `int(hi) + 1` in the fair, the promenade and everything drawn along them, which
is the same thing for a positive `hi` and a row too far for a negative one — so in every stretch
whose bank was below row zero a building a cell wide stood between the water and the promenade or
the fair. A stall standing on that sliver is what found it.

### The strength tester

The hammer and the bell, at the west end of the row the stalls are in (`striker_spot()`), on every
carnival, bank or pier; walk up to it the way you do the claw machine (`venue_at()` asks for both).
It is one key for the claw's reason. `Striker.meter()` swings up and down beside the post for ever,
and `p` swings the hammer, taking whatever the meter says that instant as the power; the puck goes
up the post that far and comes back (`puck()`, a function of the time since the swing), and from
`STRIKE_BELL` up the bell rings and a prize goes into the same `arms` the claw machine fills,
handed over once, when the puck reaches it. `STRIKE_SAYS` is the scale marked on the post. You
cannot swing again until the puck is down and the verdict has been up a moment. `h` in the menu.

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
over the end of the street like a gate, and the deck itself, which is where `b` in the menu puts
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

**The big bridge is the only way on.** `bridge_at()` gives no ordinary crossing to any avenue within
the headland's reach of the big one (`HEAD_RI * HEAD_MOAT` cells): one avenue in four used to get a
footbridge wherever it was, and the ones near the bay landed on the rock or in the water round it.
And **the water reaches further behind the point than at the sides** — `HEAD_MOAT` at the sides,
`HEAD_BACK` behind, through `headland_r()`'s `back` stretch — so the far town stands back across
the water instead of crowding up behind the lighthouse; from the landing, looking out to the
point, the middle of the view is sky now and not a wall of buildings. Not stretched on the bay
side: that way it would flood the near bank. Even unstretched it did: away from the bridge the
bay narrows, and the ellipse reached over it and put a strip of the near bank under water — found
when the carousel turned out to be standing in it — so `moat_at()` stops at the river's near edge. `HEAD_BACK` is held where it is by `near_river()`:
the water's furthest edge, wobble and all, has to stay inside its 48 cells of the river's centre,
and at 2.7 it went over.

`draw_lighthouse()` is world points: a stack of rings, white with red bands, so it tapers and stays
round from wherever you see it; the lantern room on top with a light that is never off; a bench
at the point and a lamp by it. The **beam** is the reason the headland exists — a line of points
from the lantern out to `BEAM_REACH`, with a fainter one thrown the other way the way a real lens
does, going round once every `BEAM_TURN` seconds. It goes over the bridge, the bay and the town
without asking any of them, and where it passes over water it is drawn on the water too: a beam
that only exists in the air reads as a stick. Drawn from 420 units, further than the bridge,
because a moving light is the first thing the eye finds. `i` in the menu puts you at the landing
looking out to the point.

### Up the lighthouse, and firing your own show from it

The lighthouse has a door at its foot, facing the bridge's landing (`LIGHT_DOOR` out from the
middle), and walking into it is on to the stair: `lighthouse_door()` starts the same lift state
the sky decks use, with `kind: "lighthouse"`, `climb_times()` for its timing and `render_stairs()`
for the climb — the steps winding down past you round the post in the middle, slit windows going
by with the beam crossing them, a count of `STAIR_STEPS`. At the top you are on the gallery:
`gallery_view()` puts the camera `GALLERY_R` from the middle and `LIGHT_H + 1.5` up, and turning
walks you round the lantern. `lighthouse_info()` is the one description of all of it — where it
stands, the door, where you come out again, and where a show goes up. `+` in the menu stands you
outside the door; one step in and you are climbing; `s` on the gallery climbs back down.

From the gallery, `draw_lighthouse()` draws neither the tower under your feet nor the lantern at
your back, and `draw_gallery()` draws the rail round you, solved per screen column against the
rail's circle the way the sky deck's parapet is solved against its square. **You stand nearer the
lantern than the rail on purpose**: at the rail itself the rail is under your chin and off the
bottom of the screen; a step in, it frames the bottom of the view.

`f` on the gallery lights a `Show`; it used to be a firing box down on the rock, which is gone.
The show goes up over the bay between the bridge and the carnival's wheel (`lighthouse_info()`'s
`show`), so from the gallery the three are in the one view, and at that height the bursts are at
eye level rather than over your head — every spark on screen, measured, where from the rock a
third went off the top. Anybody on the bridge or the far bank sees it too, since
`draw_fireworks()` draws the show's shells over its bay whatever night it is.

**The game is a beat bar**, `draw_show_bar()`, over the bottom of the view while you are up on
the gallery: cues come in from the left to a line on the right at `SHOW_BPM`, after a
count-in. The cues are laid out when the show is lit, a bar at a time from `SHOW_BARS_EASY` for the
first two and `SHOW_BARS_ALL` after; `2` is a big cue and puts a gold willow up as well. `press()`
judges against the nearest cue still waiting, `SHOW_GREAT` or `SHOW_GOOD` either side, and puts a
shell up straight away: a great one at 1.25 size, a good one smaller, and a press with no cue near
it a fizzle that breaks the streak. `update()` marks the cues that went by as misses, and once the
last has gone lays out a finale of 3 to 24 shells by how near the score came to `best`, the score
of a perfect run. A press during the finale does nothing; it is the show's own.

It is one key on purpose, the same reason the claw machine is: curses sees key repeats and never a
key going up, so nothing here can ask you to hold one. And frames are 1/30 s apart, which is why
`SHOW_GREAT` is as wide as 0.09: a press is only seen at the start of the next frame.

`shell_sparks()` grew `size`, `spread` and `willow` for this, all defaulting to what the night show
already did.

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
returned the same pier and bridge every press. They move along the river now, and `B` went to a
bridge with someone on it (both off the panel now) — the leaner is one in three, and a thing you cannot reach cannot be
checked.

**No key may differ from another only by case unless it is a variant of it.** The woods went in as
`W` next to `w` weather, and the rave as `R` next to `r` residential, and the report back was "W is
already weather" and "the rave cheat teleports me to just city" — lowercase pressed, weather cycled,
a housing district reached. Both were working. `b`/`B` (a bridge, the same bridge with someone on
it) was the one pair that earned it, and both have since left the panel; there are no pairs now
(`a` people and `A` a strange night was one that slipped in — the strange night is `u` now).

**The rig in the trees knew.** Whoever carried a sound system into the woods on the one night in
forty that the sky has something in it was not guessing: `rave_window()` is on from dusk to dawn on
that night, and `rave_light()` gives up 168 BPM and takes the sky's beat through `city_sync()`, the
way the club does. That was the theory kept alive through the rewrite, and it is now the rule.

## The woods

Not a park. The parks are the small green squares the city has everywhere; the woods are one great
dark block of trees a few districts across — Central Park sized, 700 by 420 units — with trails
through it, a hollow in the middle, and no street, light or building in it at all. There is one per
`WOODS_TILE` (2400 units) in each direction, jittered inside its tile, so from anywhere the nearest
is a long walk. `o` in the menu takes you to a gate.

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
lit by the rig counts as one too; on the facades it is still only the lights that cross. `~` in the
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

**Rare and unreachable are different things, and the menu has to reach it.** `v` calls
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

`[` and `]` are not on the panel any more (see *The cheat menu*); `find_place()` still finds
tunnels for the tests.

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

**The diner** used to be the *Nighthawks* picture and is now a few decades on from the rest of
the street: `DINER_ODDS` on its own hash, wanting a wide street out front (`_wide_face()`), cut down
to `DINER_H` whatever its district — like the club and the casino it ignores the district's
heights, and the height test exempts it for the same reason. It has its own wall column,
`draw_diner_column()`: gunmetal, a cyan seam up every corner, a magenta strip under the roof, and
over the shopfront a cyan band with a bright packet running along it now and then, like data down
a line; upstairs is panelling with a purple window in each bay. The ground floor of the front is
still one long window (`diner_window()`, in the wall pass), now lit cold and lined like a screen,
with the counter across it and three people dark against the light, one with a red eye. Its name
(`DINER_NAMES`, hashed per diner) is over the window in cyan, `OPEN 24/7` under it, and every few
seconds the sign glitches — the name jumps a column and its letters go to noise for a frame or
two (`draw_diner_sign()`).

**The cup on the roof** is the thing you find one by. `draw_diner_cup()` draws a coffee cup in neon
tube standing on the front edge of the roof — a tapering body, a handle, a saucer with its ends
turned up, the coffee in amber — and three strands of magenta steam curling up off it in pulses
that climb them, drifting to one side as they go. It is world points, through `draw_tube()`, which
picks each cell's glyph from which way the tube runs on screen there (the searchlights' trick), and
it is filled dark first, or the facade of whatever stands behind shows through the tube and the
outline is lost. Every `CUP_GLITCH` seconds or so the tube flickers. Diners are found per city
block and cached (`diners_in_block()`), like the cinemas, for `CUP_REACH`.

**Where it can be seen from was measured, and it drove the design.** The street camera does not
tilt, so a sign on a roof is only in frame from far enough back — and from far enough back down the
street the diner's taller neighbours are in the way. At two storeys a good view of the cup came
from 7 of 277 street spots nearby; a pylon to lift it over the neighbours did not help (8 of 277),
because from anywhere near it went off the top of the screen instead. Cut to one tall storey and
the cup a little smaller, it sits whole in frame from across the street in an ordinary terminal,
which is the one view a wide street guarantees, with the steam rising off the top of it.

Inside (`render_diner()`) you are on a stool: strip lights along the ceiling with one tube on the
blink, the window onto a wet street of towers and holo-ads with the odd car going over, the menu
board (`DINER_MENU`, in credits) glitching, a chrome coffee machine with its little lights, a
robot arm working the grill along its rail, three others along the counter — a visor, a hood, an
eye that is not an eye — and `DINER_POUR` seconds after you sit down a drone comes round with the
pot and says what diners have always said. The seat is remembered the way the ramen bowl's is. `d`
in the menu.

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

**They are a queue now**, and the door opens. `club_door()` swings it open once every `CLUB_DOOR`
seconds, at a hashed moment within each, for `CLUB_OPEN`: shut, the steel door shows only the beat
leaking under it; open, it is solid light, a wedge of it lies across the street
(`draw_door_light()`), and `collect_glow()` throws a second pool of it further out. `club_line()`
is everything outside. Every person has a number, and their place in the line is that number less
how many have gone in — a count that rises smoothly while the door stands open — so the one at the
front walks in at the door, the rest shuffle up a place, and somebody new joins the back, with
nothing stored. Who they are, raver or smoker, is a hash of the number, so the same person moves up
the line rather than turning into someone else, and there is a test that says so. A `BOUNCER` in
shades stands the other side of the door, arms folded, not dancing; three brass posts and a red
rope (`draw_rope()`) stand between the line and the street. The line runs whichever way along the
wall has more room from the door.

**Closing time** is the last `CLOSE_LEN` of every night but the strange one (`club_closing()`),
and runs on into the dawn on a night that has one. `club_light()` returns the house lights — a
steady `BULB`, no beat — so the slit windows, the door and the pool on the pavement all go flat and
warm at once; `club_door()` stands open and the count stops where it was; and `club_line()` gives
no queue but `going_home()`: one out of the door every `LEAVE_GAP` for `LEAVE_FOR` seconds, onto the
pavement and off down the street one way or the other, each a number whose place is a function of
how long ago they came out, until the street is empty. The bouncer stays. Inside, the rig is off,
nobody dances, the floor empties as the minutes go and the lights are up. `/` in the menu goes to
a few seconds before it.

**The bass you can see.** `club_kick()` is how far through the beat a club is (none at closing
time; the sky's on the strange night). On the kick, `bass_lots()` — found per frame by
`near_clubs()`, which tests the hash before building a lot, so it costs a few hundred multiplies —
is every building within `BASS_REACH` of the sound system, and `draw_wall_column()` drops their
windows a row while it lasts: the windows next door shake. The lot dict carries its own `ij` now
for that. And when it has rained, `draw_bass()` sends a ring of ripples out across the wet pavement
from the door on every kick, with the last one fainter behind it. The kick's window was a single
frame at 30 a second at first and easy to miss; it is a fifth of a beat now.

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

**From the street it has three more things.** `draw_blade()` puts the name up the front corner on
a blade sign, the old Las Vegas way: a tall board standing `BLADE_OUT` out of the wall at right
angles, from over the canopy to `BLADE_RISE` above the roofline, the letters stacked down it and
bulbs chasing down both edges. Its edges are projected from the world like a hung sign's, so it is
edge-on from straight across the road and opens out as you come down the street — which is when a
blade is meant to be read, and when the marquee over the door is hardest to. The letters are in
screen rows spread down the whole board, closed up under the top of the screen when its top is
above it (the name with its first letters gone is worse than the name a little squeezed), and in
the big font once the board is wide and tall enough to take them. The first try capped their
spacing at a hung sign's and they bunched at the foot of the board. They light one at a time from
the top, flash, and hold. `draw_red_carpet()` runs a red carpet from the door across the pavement
to the kerb between brass posts and a red rope, and a `DOORMAN` in braid stands beside it.

**And it celebrates.** A 777 on the slot (`main()` sees the payout and calls `hit_jackpot()`) puts
that casino — by its cell, which the casino dict now carries — into `jackpot_on()` for
`JACKPOT_LONG`: every bulb on, every window lit, the blade, the marquee and the doorman flashing gold
and white, and inside the room's ceiling all lit. Walk out and the building is still going. A 777 is
about one pull in nine thousand, so `%` in the menu (`rig_jackpot()`) makes the next pull one
(and the next plinko ball an edge, and the next race the long shot's), once —
the one place the slot is not honest, and only when asked.

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

It is played for dollars, out of the one `Wallet` (see *Money*), so a win at the slot is money
at the table, at the exchange and everywhere else. `p` pays the bet
and pulls, `+`/`-` step the bet through `SLOT_BETS`; three of a kind pays `SLOT_PAYS` times the bet
by symbol (777 is a hundred), a pair gives the bet back, and `settle()` pays out once, when the
last reel stops. Against `SLOT_WEIGHTS` that returns about 82 dollars in 100, which there is a
test for — the house wins slowly. A pull you cannot cover is refused and says `NOT ENOUGH`. The
house used to stake you again at zero; with one balance for the whole city that was free money,
so it does not. It no longer pulls itself: a machine that spent your money while you stood there
would be a bug.

The one trap from before still holds: the casino jump (`c`, then a few steps in), and the panel used to stay open
so `p` was the park. A jump closes the panel now.

**Blackjack** is on the other side of the wheel, from 92 columns; the wheel moves over and gives
up radius so all three fit (`left`/`right` in `render_casino_room()` — the wheel's `cx` is not the
screen's centre once the tables are in). One deck, reshuffled under fifteen cards, dealer stands
on 17, blackjack pays three to two, `BJ_BET` a hand out of the shared purse. `b` deals, `h`
hits, `k` stands — `s` is taken, it walks you out. The dealer's second card stays face down until
you stand, and the dealer then takes a card every `BJ_DEAL` seconds rather than all at once: a
hand that resolves in one frame is a number, not a game. The one thing that bit: `now - t >= 0.8`
is false at `t + 0.8` in floating point, so the timer compares with an epsilon.

**The plinko machine** is the casino's fourth game, and `o` goes over to it: it takes the
wheel's place in the room, the slot machine stands aside, and blackjack stays if the window is
108 wide. `Plinko` is honest the way `Spin` and `Slot` are: `drop()` pays the bet and draws every
bounce there and then — `PLINKO_ROWS` fair coins off `_spin_rng` — and the fall is a timeline from
them, so `where()` says where the ball is at any moment and `settle()` pays it once, as it lands,
`PLINKO_PAYS[rights]` times the bet. The pays are symmetric and climb to the outside, 120x at the
edges against 0.3x in the middle, which is where the binomial puts most of them: an edge is one
ball in 2048, and the machine gives back 94% (a test works that out from the table, and another
drops six thousand). Up to `PLINKO_MAX` balls in the air at once. `draw_plinko()` lays the pegs
`PLINKO_SX` apart — even, so a half step is a whole column, and wide enough for "120" under its
bin; at three the pegs jumbled and the labels ran together — and a window without
`PLINKO_WIDE` x `PLINKO_TALL` for it gets a line of text. A ball to the edge sets the building
off the way a 777 does (`hit_jackpot()`), and `%` in the menu, now *jackpot next*, rigs the next
ball to go all the way as well as the next pull.

**The races** are the fifth, on `r`, taking the middle of the room the way plinko does (the slot
machine and the table stand aside). `Races` puts up a card of `RACE_FIELD` horses every
`RACE_CYCLE`: `RACE_BET` seconds of betting — `1`-`6` puts the stake on a horse, `+`/`-` step it
through `RACE_STAKES`, out of the one wallet — then `RACE_RUN` of race and `RACE_SHOW` of result.
Each horse's real chance (`q`) is drawn when the card is made, and the board's odds are a fair
price times `RACE_CUT` rounded **down** onto `RACE_LADDER`, so the board is honest and pays back
about 87% (the rounding takes more than you would think: at a cut of 0.88 it was 79%). At the off
`update()` draws the whole finishing order from those chances, one place at a time, and
`progress()` is solved from it — each horse's line time set by where it finishes, with a wobble
that vanishes at the gate and the post, small enough that nobody runs backwards and big enough
that the lead changes in nearly every race (there are tests of all three). Winners are paid once
at the result; a winner at 20/1 or longer lights the building, and `%` in the menu brings the
longest shot home in the next race. `draw_races()` is the board and the track: number, name in
the silks' colour, odds and your money, the horse galloping to a chequered line, where it came
once it is past the post, and the commentator; a window without `RACE_WIDE` x `RACE_TALL` gets a
line of text.

## The ramen counter

The third way into a building. One yokocho pub in `RAMEN_ODDS` is a ramen shop (`ramen_at()`,
hash of the face first because the lot is the expensive test), and from the lane it says so: the
sign over the door reads ラーメン instead of the pub's usual word, a split red **noren** hangs over
the door, and steam comes out from under it. `venue_at()` treats its door like the casino's —
stand within `CASINO_REACH` and `render_ramen()` draws the room round you.

**The front** (`draw_ramen_front()`) is made to be found from down the lane, and all of it is
steam and red light: a **neon bowl** over the name — red tube, an orange band round it, chopsticks
lifting and dipping with yellow noodles swinging off them, three strands of steam climbing off
the top in pulses — a **vent** at one end of the front puffing steam out over the lane, puffs that
grow, rise faster as they go and thin from white through grey to haze, more steam **rolling out
under the noren**, a swaying red **lantern** each side of the door, and the cyan **ticket
machine** by it. Where it sits is set by what the camera can see: it cannot tilt, and from
across a five-unit lane nothing above about five is on screen, so the bowl is small and sits at
`RAMEN_SIGN_Y` just over the name, and the vent is at 4.1, not up at the roof — at the roof it
was a plume nobody standing in front of the shop would ever see. Down the lane, further off, the
plume is what you find it by. About 0.3 ms a frame.

Inside is the one room in the city that is **not on a beat**: the noren across the top, the menu
board with prices in yen and a lantern either side, the cook moving between two stock pots, the
others along the counter heads down and slurping on their own counts, and steam off everything.
You sit down to chopsticks; the bowl arrives `RAMEN_SERVE` seconds later — egg, nori, steam — and
the cook calls it. `seated` in `main()` is what remembers when you sat, keyed on the shop, so
walking out and back in is a new bowl. It is all ASCII inside: the room is drawn without the
`v.wide` bookkeeping, so the Japanese stays on the sign outside. `r` in the menu stands you
across the lane from a shop, looking at the front — a step or two in is the counter — and a
second press finds another.

## Manholes, and who is down there

One street cell in `MANHOLE_ODDS` has a manhole in it (`manhole_at()`: a proper street only,
never on a bridge or in the water, hash first), off the middle of the roadway along the street —
about one every 170 units of street, which is "some, not too many". `draw_ground()` paints the
cover per point the way it paints everything on the ground: a rim of `o`, the grip pattern cast
into it, and before the snow, because what comes up from under it melts it. One in three
**steams** (`draw_manhole_steam()`): puffs off the cover that grow and thin from white to haze as
they rise, which is what you find one by from down the street.

You go down with **`e`**, standing on it (`manhole_under()`, within `MANHOLE_ON`) — a key and not
a step, because the autopilot walks the roadway and would otherwise drop you down every manhole it
crossed. `MANHOLE_ON` is wider than the cover on purpose: a tap of `w` carries you 2.3 units, and
at 0.8 you could tap straight over it without ever being on it. The HUD says when you are near
one and when you are on it. Down there is `sewer` in `main()` — a state like the lift: nothing
moves you, `s` (or `e`) climbs back up onto the cover, a jump clears it.

`render_sewer()` is the lair: a brick arch, a pipe dripping, the ladder you came down with the
street light at the top of it, the water going by under the ledge, fairy lights, an old couch and
a television on the blink — and **four turtles round a pizza box** on a crate, each in their own
coloured headband (`SEWER_BANDS`), eating on their own counts: a slice up at the mouth on the
bite, a string of cheese as it comes away. For the first few seconds they all freeze and look at
you; then it is cool, and they talk (`SEWER_SAY`). They get through a slice every `SEWER_EAT`
seconds and leave two (`sewer_slices()`), and `p` takes one — until the box is empty. They have no
names. `x` in the menu stands you seven units back along the street from a steaming one — nearer
and the cover is under the bottom of the screen, since the camera cannot look down.

## The temple, and the word of God

`TEMPLE_ODDS` on its own hash, a street front required, never in the financial district, and
`TEMPLE_H` tall whatever its district — low, so the rose window over the door is in sight from
across the road, which is the one view a street guarantees. `draw_temple_column()` is pale stone
with a buttress at every bay's edge and between them tall **pointed windows of stained glass**,
lit from inside by candles: panes in the city's neon colours with the lead between, flickering,
narrowing to a point at the top. The front comes up into a gable (the roofline is `/`, `^`, `\`
over the door face, and the column returns that higher roof, so it occludes properly). The middle
bay of the front is `draw_temple_front()`: the **rose window** — a ring of stone, twelve spokes of
glass turning their colours slowly, a gold eye in the middle — the arched door standing open on
candlelight, a candle either side, and the name over it (`TEMPLE_NAMES`). `*` in the menu stands
you across the street from one, the way the casino's does; a few steps in is the door.

Inside (`render_temple()`): the vault, the pillars going away down the nave with stained glass
between them, pews either side of the aisle, candles along the altar — and on the altar a
terminal, on which `g` asks for **the word of God**. It is Terry A. Davis's oracle from TempleOS,
and done his way: the random number is the time since the last time you asked, to the
microsecond (`oracle["last"]` in `main()`), so nobody chooses it, not even the program, and
`god_words()` turns it into `GOD_SAY` words off `GOD_WORDS` — a list of the city's own, not his.
The last few utterances stay on the screen, the newest bright. Free to go in; nothing to pay.

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

### The crown

The top `CROWN_FLOORS` of every sky-deck tower are a weather beacon, by the old rhyme: steady blue,
clear view; flashing blue, clouds due; steady red, rain ahead; flashing red, snow instead — and in a
storm, red and white as fast as it goes. `crown_light()` reads `sky_word()` once a frame into
`v.crown`, so every tower agrees, and the window loop in `draw_wall_column()` fills those floors
solid, every column, so it reads as one band of light rather than lit windows. The blue is its own
colour (`crown_blue`, 33, or plain blue on eight colours): nothing in the palette was blue.

**It cannot be seen from the street, and that was measured, not assumed.** The camera does not
tilt, and a top floor seventy units up only drops onto a thirty-row screen from further off than
`MAX_VIEW` follows a wall — zero of 192 street views around a tower saw it. From another sky deck's
roof it is everywhere: 28 of 32 views, every tower in reach telling you the weather. So the street
gets it at the door instead: SKY DECK over the lobby is lit in the crown's colour.

## The landmark, and the party on its roof

One skyscraper a whole city block wide in every `LANDMARK_TILE` square — 48 tiles in 49 have one —
an Art Deco wedding cake: a broad base `LANDMARK_BASE` high round the edge, the tower set back from
it to `LANDMARK_H`, over every sky deck in town, and a spire over that with a red light. A
`LANDMARK_NAMES` name over the lobby with ROOF PARTY TONIGHT under it in the beat's colours.

**It is the first building that is more than one cell.** `landmark_of()` picks a block per tile —
away from the river, the woods and the parks, wide enough, and held against its south and west
streets so the lobby (`lobby`, the middle of the south edge, door `+z`) fronts a road — working out
the block's bounds from `_is_road()`, which is pure, so asking it from inside `is_open()` is safe.
`is_open()` says every cell of it is solid, alleys and all, and `lot()` gives each cell the base's
height or the tower's by `landmark_ring()` and marks it `landmark`; the raycaster does the rest,
the tower showing over the base the way any tall building does over a short one.
`draw_landmark_column()` is pale stone with a pier up every bay, lit windows between, lights along
every roofline, and the tower's top floors floodlit in a colour that changes every eight seconds.

**The roof is the first one you walk about on**, and that needed two things the sky decks never
did. They stand you at the parapet, which hides that the renderer has no floors; from the middle of
a 25-unit roof the street a hundred units down showed straight through. `draw_party_floor()` draws
the floor the way the ground is drawn, per screen row: where each column's ray leaves the roof the
parapet goes up, and nearer than that is floor — a dance floor of tiles lit on the beat. And from
inside it the building's own cells were walls in front of everything on the roof, so `View.skip`
holds the landmark's cells and `draw_walls()` passes over them. In `main()` the lobby is a lift
like a sky deck's, `kind: "party"`; at the top you step out of the lift hut and `roof_x`/`roof_z`
walk you about inside the parapet, and walking back into the hut (`lift_hut()`, forwards or
backwards) takes you down.

On it (`draw_party()`), at `PARTY_BPM` off `party_light()`: the booth at the north end with the DJ
and the stacks, a lighting tower at every corner with a head on top, a crowd of 22 on the floor
going up on the kick a fraction of a beat apart, and the strobe the last bar of every eight. Its
lasers (in `draw_spire()`) fan out from the booth over the city, nearly level, a new colour every
bar — seen from across town at 250 units from about half the streets round it, and from nearer
not at all, because they are over the top of the screen: the street camera does not tilt, which is
the sky-deck crowns' trouble again. `p` in the menu stands you outside the lobby. About 9 ms a
frame on the roof at 110x34, 19 at 240x70.

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
in screen space for the casino marquee's reason. `m` in the menu stands you in the doorway, and
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

**Half the cinemas are showing the action picture** instead (`_film_pick()`: `ACTION_TITLES`,
one in two on its own hash). `film_frame()` hands an action title to `action_frame()`, the
drama's other half on the same six-scene loop: the title slammed up in `BIG_FONT` with the screen
shaking and sparks off it, then the tagline (`ACTION_TAGS`); a car chase, side on, the hero's car
ahead and the van behind shooting, lamp posts going by and speed lines over the skyline; a leap
between rooftops in slow motion under a helicopter's searchlight; a fist fight with the blows
written up in the air (`ACTION_BLOWS`) until the villain is sent flying, K.O.; a countdown and an
explosion, fireball, debris coming down, the screen shaking, and him walking towards you without
looking back, with a line (`ACTION_QUIPS`); and THE END, ...OR IS IT?, the sequel. The explosion is
the brightest thing either film puts up, so it lights the audience the way nothing in the drama
does. And it is **in colour**: `render_cinema()` inks the fire (`@`, `%`) and the sparks (`*`, `!`)
by `ACTION_INK`, where the drama is all black and white. Its sprites are ASCII for the same reason
as the ramen room's.

The marquee's NOW SHOWING was in the star colour at first, and the stars-inside-buildings test
counted its letters as stars drawn inside a building. Anything in screen space on a facade needs a
colour that is not a star's.

**The title goes up in big letters** within `CINEMA_BIG`: the three-by-five `BIG_FONT` (the
roulette's `DIGITS` plus `LETTERS`, drawn through `big_cells()`), white, on a dark board blanked
behind it, NOW SHOWING over it and the bulbs chasing round the lot. `_title_lines()` breaks a title
too wide for the window at the space nearest the middle, and if even that will not go it is the
small sign; further off than `CINEMA_BIG` it is always the small one, because a seven-row sign on
a building a block away is bigger than the building.

**Two searchlights sweep the sky from the roof**, at the front corners, mirror to mirror, so they
cross over the street and open out again (`search_beam()`). `SEARCH_LEAN` off the vertical is what
makes them read: nearly upright they went straight off the top of the screen from anywhere near,
and from far off the nearer roofs hid them. Leant over, they cross the strip of sky over a street.
They are found per city block and cached (`cinemas_in_block()`), like the sky decks' beacons, and
drawn from `SEARCH_REACH` - and drawn *before* the props, so a sign out front is never painted over
by a beam going up behind it. Measured, a cinema's beams are in sight from about a sixth of the
street views round it, and there is a test that holds that. They are `BEAM`/`BEAM_DIM`, which are
the lamp colours under their own names: first time round they were the moon's colours, and the
star tests counted every beam cell as the moon drawn inside a building - the marquee lesson again.

## The stock exchange

In the financial district only: `EXCHANGE_ODDS` of its street fronts, about two to a district —
one in 900 left some districts without one and the menu's search came back empty from one start
in 96. Low and old among the glass towers: `draw_exchange_column()` is pale stone with a column in
every bay, a cornice, and steps at the foot; `draw_exchange_front()` puts STOCK EXCHANGE over the
columns and the **ticker** under it, the market scrolling by in screen space — every stock, its
price, and the last tick's move in green `^` or red `v`. `e` in the menu stands you on the floor
(it is listed under the parts of town: the first column of the panel was a row past 80x24).

**The market is a function of time.** Sixteen made-up `STOCKS`, four to each of the `SECTORS`,
and `stock_price(s, t)` for each is four things added in log space: the **market's tide**
(`market()`: slow waves for the long bulls and bears, and a quick term that every stock feels on
the same tick), times the stock's own beta; its **sector's current**, slow and quick, shared with
the other three in it; its **own** swings and noise; and its **mode**. Every `EPOCH` ticks each
stock draws one of `MODES` off a hash — stable, rising, falling, hot, crash, chaotic, in Cookie
Clicker's spirit — and a mode's move rises across its epoch and fades back out across the next,
so a hot streak is followed by the air coming out of it, and only two epochs ever overlap: the
price at any moment is a closed form and nothing is stored. Chaotic is in the noise, not the
drift; the wildness eases over a couple of ticks at an epoch's start so the price does not jump.
Measured over 3000 ticks, tick moves correlate 0.23 across the market and 0.32 within a sector —
the quick shared terms are what made that so; with only slow ones it was 0.02, nothing you could
see — and hot epochs are a median x1.9, with runs of fourteen ticks up. The price you trade at
steps every `TICK_LEN` (`stock_now()`), and a `candle()` is one tick: its open and close are the
two prices, its high and low the extremes of the path between.

Inside (`render_exchange()`): the ticker along the top, the market's `mood()` and the seconds to
the next price, and then the chart — the picked stock's candles, green up, red down — or, with `l`,
the list of all sixteen: price, last move, what you hold and its worth, and `HOT!` or `SLIDE` for
a `streak()` of `STREAK` ticks one way. The arrows pick a stock in either (the list scrolls to
keep it in view); you come in on the exchange's own. `Broker` is the account, one for the night
whichever exchange you are in, its cash the one `Wallet`'s; shares held and what they
cost, profit or loss. `b` buys and `n` sells the picked stock at the current price, `+`/`-` step
the size through `LOTS` (0 is as many as you can).

## The arcade

`ARCADE_ODDS` on its own hash, a street front required (`_road_face()`), never in the financial
district, and cut down to no more than eleven units unless its district builds higher: the light
wall and the sign over the door have to be where you are looking from across the street. It is
the third building with its own wall column, after the club and the casino.

`draw_arcade_column()`: above the shopfront the whole face is a wall of coloured panes, solid
across each bay with a dark line between so it reads as a screen of big pixels and not as lit
windows. `arcade_pixel()` runs it, one pattern every `ARCADE_MODE` seconds - a rainbow rolling
across, a chequer flipping, a bar sweeping, a sparkle - with each arcade starting the cycle
somewhere else so two in one street are not in step. The sparse ones were made fuller after a
measurement: the sweep lit two bays in seven and the wall went nearly dark between passes. Bulbs
in every colour chase round the roof and the canopy, the corners change colour, and the ground
floor is dark glass with a cabinet's screen glowing in each bay. The pavement takes the colour of
the wall (`collect_glow()`).

`draw_arcade_front()` is the sign: ARCADE in the big font on a blanked board (letters made of the
same blocks as the wall behind them were lost in it), ringed with rainbow bulbs, the arcade's name
under it, and INSERT COIN blinking on the canopy. `arcade_letter()` gives the letters their
routine - dark, on one at a time, the word flashing, then each in its own colour turning slowly.
Within `ARCADE_BIG`; further off, the word in ordinary letters. It hangs just over the canopy: an
early one higher up went off the top of the screen from across a narrow street.

Inside (`render_arcade()`) is a row of cabinets, as many as the window takes (`arcade_order()`),
each with its game's name lit on top and a demo of it running on the screen (`cabinet_demo()`, a
function of time alone); the arcade's name across the top in the big font, the carpet every arcade
has, and two kids at the machines. `a`/`d` pick a cabinet (it lights and gets a `vvv` over it), `p`
plays it, `s` walks you out. `g` in the menu stands you in the door.

**The games** are `GAMES`, one class each on `ArcadeGame`'s fixed-step clock (`GAME_DT`, and no
catching up more than half a second after a stall): `key()` takes `up`/`down`/`left`/`right`/`act`,
`tick()` advances, `draw()` fills a `GAME_W` x `GAME_H` playfield that `render_game()` puts in the
cabinet's bezel with the score, the high score and the controls under it. All of them are taps,
never holds, for the claw machine's reason. While one is going `main()` gives it every key — `w`
and `s` with the rest, so you do not walk out mid-game — except `x`, which leaves the cabinet, and
`q`; space is kept from the autopilot while you are in an arcade, or it walked you out. High scores
are per arcade per game for the session (`play["hi"]`). The six:

- **ROOFTOP RUN** — roofs come at you, `p` jumps, faster and faster. Roofs get longer as it does:
  one jump carries you further, and the bot that tests it once came down off the end of a roof
  shorter than its jump.
- **FIX THE NEON** — turn the tubes until the power runs from the plug to the sign. Each puzzle is
  dealt by walking a path from one to the other and scrambling everything (`answer` keeps the way
  round, so there is a test that every one can be lit), against a clock that shortens.
- **LATE DELIVERY** — a scooter that keeps going on a grid of streets, arrows steer it, deliver to
  the `X`; every delivery buys time.
- **NEON DRIFT** — lanes, traffic, left and right, faster.
- **SKY SHOW** — rockets go up and `p` bursts them on the line; three up dark and it is over. Their
  speed is capped: uncapped, by five thousand points they were a blur nobody could time.
- **NIGHT OWL** — move along the branch and catch the moths; three got away and it is over.

Each has a test in which a simple bot plays it properly and gets somewhere (and, where it makes
sense, one in which doing nothing loses), which is the test that found both of those.

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

Testing this through a pty has a trap of its own: with the keypad on, which `main()` asks for,
xterm sends an arrow as `\x1bOC`, not `\x1b[C`; write the second and curses reads a bare ESC, which
quits. Two dead-end investigations started that way, with the program fine and the harness killing
it, and the arrow tests in `pty_checks.py` passed for months by quitting at the first arrow — "no
crash" was true. They send the keypad form now; buying from the exchange's list is what showed it.

## The cheat menu

**Anything new in the city gets an entry here, in the same commit that adds it.** This is a standing
instruction, not a nicety: everything worth looking at is deliberately rare, so a feature with no way
to reach it cannot be checked by the person who asked for it, and will not be. If what you added is a
place, give it a row in `CHEAT_PLACES` and a predicate for `find_place()`; if it is a condition —
weather, time, a mode — give it a key that sets it, the way `w` and `L` do. Both are a few lines.

**The panel is for going somewhere, not for testing the generator.** It was pruned of everything
that was the latter — inside a casino and inside the club (the jump to the door is one step from
it), the pleasure pier (the carnival is on it), the lighthouse's foot (its top is the one you want),
back to start, far away, someone leaning, a bridge, the end of a pier, and the streets: a dark
alley, a dead end, a crossroads, a long street, the tunnels. Their kinds are still in
`find_place()`, which the tests use; they are just not keys. Ask before putting one back.
Adding the feature and leaving the menu alone is an unfinished job.

`` ` `` opens a panel over the live view — over, not instead of, so that weather you change happens
in front of you. **A jump closes it** — you went somewhere to look at it, and with the panel still
up the next key is a district or another jump; the `-> where` note shows on the HUD for four
seconds instead.

**Grouped by what you would go there for** (`CHEAT_GROUPS`): NIGHTLIFE, FUN, EAT; MONEY and the
PARTS OF TOWN (on the digits, `1`–`8`); AROUND TOWN, OUT OF TOWN, VIEWS; then WEATHER & SKY and
NIGHTS. Places get their own letter where they can (`r` ramen, `d` diner, `c` casino, `m` the
movies), which is why the districts moved to the digits. A new place goes into a group, not on the
end of a list. It was once grouped by where things were — the city, the streets, out of town —
every new place went into the first, and it quietly grew past a 24-row terminal and then a 30-row
one — `draw_cheats()` draws nothing when there is no room, so the symptom is the
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

## Money

**One balance for the whole city.** `main()` owns a `Wallet` — `STARTING_MONEY`, a thousand
dollars — and everything that costs anything takes from it: the slot and the blackjack table
(which used to have their own chips), the exchange (`Broker.cash` is the wallet's), the claw
machine (`CLAW_COST` a go), the strength tester (`STRIKE_COST` a swing), the arcade
(`ARCADE_COST` a game), and the city's buildings, by `FEES`: a seat at the pictures and the club's
cover are paid on the way in, the bowl and the coffee when you sit down — once a visit, keyed on
the venue, so walking out and back in is another ticket. Can't pay, and `render_turned_away()` is
what you get instead: the usher, the bouncer, the cook's sign, the drone. The lifts cost
(`LIFT_FEES`: a sky deck, the roof party; the fire escapes and the lighthouse stair are free), and
a show from the lighthouse is `SHOW_FEE`; refused, the HUD says what it costs. The balance leads
the HUD everywhere. Nothing tops it up — the casino's old stake when you were broke would have
been money for nothing — except `+` in the menu, `+$1000`. Like everything else you carry, it is
for the session and nowhere else.

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
