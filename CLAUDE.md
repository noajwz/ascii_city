# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working in this repository.

An endless procedurally generated ASCII city, walked through in the terminal. Written for fun.
**No package, no dependencies, no config files** — it is one stdlib-only Python script
(`curses`, `math`, `random`, `unicodedata`) and nothing else — plus the library's two readers and
the Pokemon Center's type chart, copied in under `library/` and run as programs of their own, stdlib-only too (see The
university). Adding a third-party import would be a departure from the premise; prefer stdlib.

```bash
python3 ascii_city.py
```

It came out of `noajwz/TUI` (formerly `TUI-CLAUDE`), where it lived alongside a handful of smaller terminal programs
until it outgrew them. The history came with it.

Ruff is the linter, run with defaults (`ruff check . && ruff format .`) — there is no
pyproject/ruff.toml, and ruff is not installed on the machine this was written on. Keep lines under
89 characters; that is the one rule the code has actually been held to.

**`IDEAS.md`** holds what the owner has asked to have done later, by name - check it when they
ask for "the rooftops", "the skyline shapes" and the like, and take an idea out once it is built.

## Big windows: one scaling system

**This is the system for every screen that gets bigger on a big window, not just the casino.**
The owner plays zoomed out on a MacBook (3024x1964), and there the screens that are fixed
drawings - the casino's games, the interiors - were tiny islands in the middle. The casino was the
first to scale (see The casino, big), then the arcade (see The arcade, big) and the Pokemon
Center (see The Pokemon Center); the cinema was looked at and does not need it. More venues are
to follow, and they all work the same way:

The night sky goes by the same scale. Stars are not scaled but fixed: a star is drawn only in the
first column of its bearing (90 to the radian, about 132 across the screen), because on a wide
window one bearing covers two or three columns and each star came out as a dash. That is at every
width, not only big ones - below about 90 columns no bearing is shared and nothing changes - and
the number of stars and where they are stay as they were. The moon has a second drawing
(`MOON_BIG`) and a meteor twice the cells, so both come out the size and the angle they are on a
small window.

- **One threshold, in characters, for everything.** The scale is `min(width // 150,
  height // 44)`, capped at 3 (`big_scale()`, `BIG_W`, `BIG_H`, `BIG_MAX`): 2 from a
  300x88 window up, 3 from 450x132. The game never sees the zoom level or the screen - only the
  terminal's columns and rows - so where the switch lands depends on the screen, the window, the
  font and its size. **On the owner's MacBook, full screen, in Fixedsys Excelsior, it switches at
  exactly 5x zoomed out, and they want it kept there.** Do not change `BIG_W` / `BIG_H`
  without asking; there, the 300 columns are what decide it, the rows are already past 88.
- **Every screen uses that same scale: `big_scale(width, height)`.** No screen gets thresholds
  of its own, or two screens would switch at different zooms. `_big_screens` is the one `z`
  switch for all of them; `z` is handled with the casino's keys and the arcade's (`(wheel is not
  None or at_arcade)`), so a newly scaled venue adds itself to that condition - unless, like the
  Pokemon Center, it has a key branch of its own that catches every key first, in which case `z`
  goes in that branch. Watch for a
  loop variable called `k` in the function you scale - `k` is the scale everywhere here, and an
  old `for k in` loop overwrites it; it has happened in three functions so far, and only the
  frame comparison at scale 1 caught it.
- **At scale 1 nothing changes.** A screen on an ordinary window - 1920x1080 and the like -
  stays exactly what it was. Prove it: render it from the old code and the new at several sizes
  below the threshold, with each colour given its own number, and compare frame for frame (as was
  done for the casino at 60x20 to 299x87, through every phase of its games, and the arcade's
  room and six games at the same sizes).
- **How a screen scales:** shapes worked out from maths (the wheel, pegs, a track, a graph) grow
  by raising their caps and spacing - redrawn, never stretched. Fixed ASCII drawings get a second,
  bigger version (`draw_slot_big()`, `draw_blackjack_big()`), with a size helper (`slot_size(k)`,
  `table_size(k)`) the layout uses in place of the old fixed numbers. Numbers, titles and short
  words go in block letters with `_blocks()` (`BIG_FONT` plus `CASINO_FONT`), each dot `sx`
  columns by `sy` rows; `sx = sy = k - 1` for lettering has kept things in proportion so far.
  **Ordinary text stays small** - a terminal cannot draw a letter bigger than its font, and a
  sentence in block letters is four columns a letter. Keep cells about twice as wide as tall
  (sx = 2 * sy for something meant to look square). **A grid of shapes** - an arcade game's
  playfield, a cabinet's demo - is the one thing drawn k times over cell by cell (`_blow_up()`):
  every character a k by k block of itself, the way arcade games are scaled. Never words that
  way: "BET" would come out "BBEETT".
- **Tests for each scaled screen:** the scale at a few sizes either side of the threshold; the big
  version has its block letters and big drawings and the small one does not; nothing big overlaps
  its neighbours (the wheel's rim got into the slot machine once); every mode of the screen draws
  without error at several big sizes, odd ones too; `z` gives the small screen back on a big
  window; and a pty case played in a 300x90 window.


An endless procedural city with **two renderers** over one screen loop. Both `render_skyline()` and
`render_street()` fill the same `(ch, co)` pair of character/colour grids, so the blit loop, the HUD
and the input handling in `main()` serve either; `tab` switches, and each view keeps its own camera
so switching back and forth loses neither position.

They also share one weather clock. Both call `rain_intensity(now)` and `lightning(now, wet)`
themselves rather than being handed a number, so the downpour you tab out of is the downpour falling
on the skyline, and a strike lights both. This is worth a test, and has one: tabbing used to land you
in a dry, still postcard, which is exactly the kind of break that no amount of looking at one view
will show you.

**Pace.** `+` and `-` in the street step how fast you walk through `PACES`, from a walk to three
and a half times one; running (`W`/`S`) is the pace times `RUN_MULTIPLIER`, sidestepping and the
autopilot go with it, turning does not. At the top that is about five units a frame — a whole
cell — so the move is cut into steps of `STEP_MAX` and each tested with `can_stand()`: one test
a frame would carry you clean through the corner of a block. Measured through a pty, running at
the top pace into the wall ahead of the start stops you at it, nothing crossed.

**Hurrying past a door does not take you in.** At a fast pace every doorway on the pavement was
a casino, a lift up a sky deck at $15, a cinema ticket — reported as "really annoying". So in
`main()` a doorway that `venue_at()` offers is refused while you are moving faster than a walk
(`WALK` or `SIDESTEP` with a little slack) **unless it is the one you were already in last frame**
(`same_venue()`, by kind and place, since the ramen counter's dict is made fresh every call); the
lighthouse door the same. Slow to a walk or stop at a door and in you go, as before. Measured
through a pty along the pavement past a casino door: walking takes you in, hurrying and running do
not.

**The autopilot** (spacebar, `auto_step()`) holds a heading **in the world** and eases onto it,
slowing through the corner. It used to be `wander()`, which blended every direction it probed by
score *relative to your nose*, plus a slow sine bias stronger than its pull to go straight: for
half a minute at a time the bias leaned the same way, so it walked circles — about 4 to 5
radians of turning every hundred units. Now `auto_heading()` picks a heading in eighths of a
turn from the old one (so on a grid street it is the street, and in the woods or on a lawn the
diagonal can go between the trees), only when the way ahead closes within 9 units or the last
step got nowhere. At a junction with 35 units open to one side it sometimes takes it
(`AUTO_TURN_ODDS`, at least `AUTO_TURN_GAP` s apart) and **never the same way twice running** —
right, right, right, right is once round the block. It also drops a crumb every two seconds
(`trail`, the last eighty seconds) and a heading leading back to one scores 30 worse: without it,
it went round the quad for ever, the same four turns, because the same walls gave the same
answers each time. Junction choices hash `int(now / 7)`, not the frame. Measured on a headless
three-minute walk from five starts: turning down to 0.9–2.4 rad per hundred units, and two to
five times as far from where it started. The check in `tests/checks.py` (`walk_auto()`) is
that same walk.

**Turning by key** goes through `turn_rate()`: a tap turns at `TURN_TAP` of `TURN`, holding
ramps to `TURN_HELD` over `TURN_RAMP` s, and `main()` eases `spin` to it (`TURN_EASE`) rather than
snapping. A fresh press holds for `TURN_FIRST` (0.32 s), not `KEY_GRACE`: the keyboard waits about
that long before it repeats a held key, and with the 0.15 s grace a held arrow turned, stopped,
then turned again — which is what made aiming hard.

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
**NIGHTS** group under WEATHER & SKY now; dawn's entry was the one that pushed the panel past 80x24
again, and the test caught it.

## Fog nights

One night in `FOG_ODDS` (on its own hash, never the strange night) the fog comes in.
`draw_fog()` runs over the finished street picture, before the rain, and it works because **every
cell already has a distance**: the wall in its column (`walls`), the ground at its row, the sky
past everything — and anything drawn above the nearest roof is something further off. Past
`fog_reach()`'s near distance a cell is taken by the fog with a chance that rises to certainty at
the far one: structure goes to nothing, or to a grain of `.` in `HAZE`, and goes grey on the way
out; **a light goes soft instead** — `o`, then `*`, then `.` — and spills a blur in its own colour
round itself, wider the further off it is (`FOG_LIGHTS` is what counts as a light: letters and
the bright symbols), which is what neon does in fog. The sky shows no stars (`draw_sky()`), just
the grain drifting. The near and far distances breathe on two slow sines (`FOG_ROLL`) as banks
roll in and out. The lighthouse beam becomes a **shaft**: a band of lit fog either side of the
line, widening as it goes. From a roof you are above it. About 1 ms a frame at 100x30, 6 at
240x70. `#` in the menu skips to the next one.

Its hash salt is 7 and not 4 for a reason worth keeping: on 4, night 0 was a fog night, and night
0 is the one the whole test suite runs on — the billboards, the El, the bridges and the district
histograms all went into the fog and failed at once. The fog is its own grey, `FOG` and `FOG_DIM` (248
and 243, or white on eight colours): in `HAZE`, which is nearly black, it read as specks on the
night rather than as fog, and it is thicker the deeper in.

## The blackout

One night in `BLACKOUT_ODDS` (on its own hash, never the strange night) **the power goes**.
`power_off(i, j, now)` is the whole of it, per city block and a function of the block and the
time like everything else: from `BO_START` the blocks go out one by one in no order over
`BO_SPREAD`, each with a last flicker; they stay out; and from `BO_BACK` of the way through the
night the power comes back as a **wave** crossing the city — the block's x along a `BO_WAVE_W`
stretch sets when, `BO_WAVE` seconds to cross it — each block flickering `BO_FLICKER` before it
holds.

It is done once, generically, rather than in every light in the city. `draw_walls()` draws a dark
building's column as it always would and then runs `unpowered()` over it: everything that is a
light — windows, neon, bulbs, a casino's chase, the arcade's wall, the club's slits — goes out,
the structure stays in `CONCRETE`, and here and there where a window was there is a **candle**.
So every venue goes dark with no venue knowing. `draw_props()` drops the `LIGHT_PROPS` of a dark
lot (signs, lanterns, marquees, the ramen bowl, the club's door), `collect_glow()` spills nothing
from one, and the searchlights, the diner's cup and the billboards are skipped for theirs. What
is left is what has no mains: car headlights, the moon, the bridges and the carnival, and **the
temple**, lit by its candles anyway, which is the brightest thing on its street that night. With
the town dark the sky over you is clearer (`draw_sky()`), so there are more stars. The HUD says
the lights are going, the power is out, the lights are coming back. `&` in the menu skips to a
few seconds before it starts.

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
and ctrl-a `t` in the checks' menu puts you on it. On the docks' stretch it is a quay: the cranes stand on lots that touch
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
bridge; between them they cost about 1.6 ms a frame near it. ctrl-a `f` in the checks' menu stands you on the bank
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
cannot swing again until the puck is down and the verdict has been up a moment. ctrl-a `h` in the checks' menu.

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
over the end of the street like a gate, and the deck itself, which is where ctrl-a `b` in the checks' menu puts
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
because a moving light is the first thing the eye finds. ctrl-a `i` in the checks' menu puts you at the landing
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
is a long walk. ctrl-a `o` in the checks' menu takes you to a gate.

**It is placed, not picked.** `WOODS` is a district row that is not in `DISTRICTS`: `district()`
returns it for any cell `woods_at()` says yes to, so `lot()` builds a tree there with no changes of
its own, and the HUD says *the woods*. The trees are much taller than a park's — `WOODS` builds 18 to 30, a park 5 to 10 — and `draw_tree_column()` starts their canopy half way up and draws the trunks under it as whole columns a bay apart, with undergrowth at their feet, so in among them you see the wood and not only the leaves; a park's clump stays low and bushy to the ground. The leaf tone is
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
lit by the rig counts as one too; on the facades it is still only the lights that cross. ctrl-a `~` in the checks'
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

## The factories

**Placed, like the woods, not picked**: `ZONES` holds the industrial zone's place in every
`WOODS_TILE` square — between the river and the woods, a wandering rectangle (`zone_home()`,
`zone_depth()`, cached) — so adding it moved nothing that was already in the city; `district()`
returns `INDUSTRIAL` for its cells the way it returns `WOODS`, the street grid runs through it
as everywhere, and the landmark keeps clear of it. The district row is low rust sheds — `lo`
5.5, `hi` 9.5, sparse windows high up for the night shift, roller doors, bare bulbs and somebody
on a break — and **low on purpose**: at 7 to 13 the near façades took the whole sky in a street
and the chimneys were 20 cells of a frame; at 5.5 to 9.5 they are 80 to 110.

- **Chimneys** (`chimney_at()`, one shed in `CHIMNEY_ODDS`, found per block and cached like the
  sky decks' beacons, `near_chimneys()` out to 260): world points, a banded tapering stack 22 to
  34 over its roof, filled dark so nothing shows through, the lip glowing orange, a red light on
  top. Its points are spaced by distance, no closer than a cell on screen — at a fixed half unit
  a frame with forty stacks in it took 56 ms. Two in three are going: smoke rolls off downwind,
  lit from below where it comes out, thinning to haze, and only within 170 — it filled the sky
  when every stack in reach smoked.
- **Sodium lamps** (`near_ind_lamps()`, `v.ind_lamps`) at the kerb every few cells of road, and
  their orange on the ground through `collect_glow()`.
- **A building site** (`zone_site()`: three cells by two, no road in it, near the middle;
  `site_at()` makes them open in `is_open()`): mud on the ground with lit puddles, a hoarding
  round it with KEEP OUT on it and a gap for the gate, a steel frame three storeys up and a
  fourth half done with work lights on it, two floodlights, and a yellow tower crane whose jib
  turns slowly with a girder swinging off the hook. `]` in the menu stands you on a road with a
  clear view of it (`probe()` — the first try had a building in the way).
- **Empty plots, fenced** (`zone_plots()`, `plot_at()`): the building site is the first of a
  zone's plots, and the rest are empty — one city block in three gets one, grown out from the
  middle of the block until it meets a road, as far as its size (`PLOT_SIZES`, up to six by
  four) lets it, so the big ones take most of a block. Placing them as random rectangles first
  found one plot in a zone: nearly every rectangle caught a road. Each has a chain-link fence on
  posts or a plywood hoarding, a gate on the road side with a sign on it (`PLOT_SIGNS`), weeds
  through the mud, and what was left there (`PLOT_JUNK`): a skip, a burnt-out car, tyres,
  pallets, a lamp that works now and then, a fire in a barrel throwing its light about. `}` in
  the menu stands you looking at the biggest one.
- **The old factory with the rave in it** (`zone_warehouse()`: a solid cell beside the site with
  a street front — it must be solid, the first one was an alley gap and had no door to walk
  into). `draw_warehouse_column()`: dark brick, rows of broken iron windows, a few of them lit
  from inside in the beat's colour (`warehouse_light()`, `WAREHOUSE_BPM`) and all of them by the
  strobe, paint on the brick, and a roller door stuck a third of the way up with the light
  pouring out under it onto the street. Near it the HUD has the bass line. It is a venue like
  the club's; `render_warehouse()` is inside: roof trusses and broken skylights, a stage of
  pallets with the DJ and the stacks, lasers through the smoke, and the crowd in three depths.
  Free; nobody is in charge. `[` in the menu stands you out front.

`9` in the menu stands you on a factory street, facing whichever way along it has the most stacks
at the end — in among the sheds the near walls hide the rest. (Fog moved to `#` and the
blackout to `&` to give the zones the digits after the districts.)

## The suburbs

The other placed zone in `ZONES`, beyond the woods in every tile; `district()` returns `SUBURBS`
— one storey or two, warm windows, a pitched roof, nothing lit but the porch and the television.
**It has its own streets, and they curve**: `road_at()` asks `suburb_road()` in there instead of
the grid — a ring road just inside the edge, following its wobble, three streets winding along
x and three across, two cells wide; and through the edge band the city's own grid carries on in
to the ring, so every street joins up with the way in (a test floods from the edge and reaches
all of them). Deeper in, the grid is gone: under half its cells are still road, against all of
them anywhere else.

`suburb_rank()` is how far a cell is from the road: 1 is the front lawn along it, 2 where the
houses stand, every other cell so each stands on its own (`suburb_house()`), 3 the back gardens
with a tree in one in five (`suburb_tree()`, a solid cell `lot()` marks as a tree, so
`draw_tree_column()` draws it with nothing else learning anything). `is_open()` says yes to all
of it but the houses and the trees; the ground pass mows the lawns closer than a park and paints
no centre line down the curves; `face_kind()` calls a lawn a street, so a house faces over its
lawn the way a shop faces the road. No venues out here, no El, no tunnels, no walkers and no
traffic — the cars' trips need straight road the length of a few blocks, and in here there is
none, which is why the quiet came almost free.

`draw_suburb()` is what it is close to, from `v.suburb` (`near_suburb()`, within 48): a **white
picket fence** along every front lawn where it meets the road, pickets with points, a rail; a
gate in it up to each house, with a letterbox, and a wider gap for a drive where one house in
four has a car on it; and on each house the porch light (`porches()`, spilling on the lawn
through `collect_glow()`) and the blue flicker of the television in one window in three. Now and
then the HUD hears a dog. `0` in the menu stands you on a street in the middle, facing the way
it runs furthest before it bends.

**And two things you would not expect** (`suburb_eggs()`, one of each per suburb, found once).
**A lemonade stand at 3am** on a front lawn by the road, where the fence would be: a kid behind a
home-made sign, LEMONADE $1. Walk up from the road (`egg_points()`: where it stands, and where
you stand to be served, which is what `venue_at()` checks) and `render_lemonade()` is the close-up
— the house dark behind with its porch light on, the fence either side, the kid blinking over
the jug and the cups, and what the kid says (`KID_LINES`, unsettling). `p` buys a glass for a
dollar out of the wallet, and the thanks get stranger (`KID_THANKS`) until, at five, you live
here now; after that the kid just looks at you. `lemon` in `main()` counts them for the session.

**The stargazer**: an old man on a lawn between two houses with a telescope on a tripod. Walk
up beside him and `render_telescope()` is the eyepiece: a round field, its columns twice its rows,
stars in it, and the moon close up — craters, and the side the sun is not on in earthshine, in
the night's real phase — and then, on a `SCOPE_LOOP` from when you put your eye to it
(`scope_at`), it does something: comes into focus, a lander comes down on it and somebody gets
out, plants a flag and waves, a cow goes over it, and it winks. On the strange night a saucer
crosses it instead of the cow. Step back and it starts again. `;` and `?` in the menu, under
NIGHTS where there was room.

## The Strip

The third placed zone in `ZONES`, at the edge of every tile clear of the woods, and a different
shape from the others: not a wandering rectangle but a boulevard. `strip_at()` is twelve cells
across and `STRIP_HALF` either way along z; the middle four are the boulevard (`strip_road()`,
which keeps the city's cross streets through it, so the hotels come in blocks and you can get
in and out), and the four either side are hotel — `is_open()` says no to all of it but the road,
and the avenues that run into it stop at the hotels. `district()` gives `STRIP`; `lot()` makes
every hotel cell part of one hotel per side per block (`strip_hotel()`), the same height (28 to
56) and name (`STRIP_NAMES`, made up) right through it, and gives the cell at the middle of its
frontage a casino — door on the boulevard, so **every hotel is a casino you walk into**, the
whole room and all six games. The doors faced away from the road at first: `FACES[0]` is -x, not
+x, and that is worth remembering.

`draw_strip_column()` is the façade: every window gold, a band of bulbs chasing round every
fourth floor in the hotel's own colour, neon trim up every bay, the crown lit solid. Nothing
hangs on the walls (`flat`, `hung` 0): each hotel's sign is a **pylon at the kerb**
(`strip_signs()`, `draw_strip_sign()`), the name in the big font in the hotel's colour within 55
units and on a lit board further off, bulbs chasing round it, flashing now and then — screen
space, for the marquee's reason. Down the median `draw_strip_median()` alternates **palms**, lit
from below, and **fountains**: a pool with a row of jets rising and falling in a wave. And
`draw_strip_traffic()` cruises two lanes each way, a car in most slots and a stretch limousine
now and then, headlights coming and tail lights going, never through you. `:` in the menu stands
you at one end in the middle of the boulevard, looking up it.

**The fountain show.** In front of the hotel at the middle of the east side, its first two cells
are a lake (`strip_lake()`, `fountain_rows()`) — in `water_at()`, so it is water the way the
river is: open to see across, not to stand on, and the ground pass and the reflection lay the
hotel and the show on it with nothing told. Every `FOUNTAIN_PERIOD` seconds, for
`FOUNTAIN_LEN`, `draw_fountains()` puts two rows of jets up out of it, lit blue from below, white
up the column, spray at the top, and `fountain_heights()` is the choreography: the lights coming
up, the jets rising together, a wave running down the lake, the rows sweeping side to side
against each other, a chase, the shooters going up forty units on the beat with mist hanging
after them, the finale, and down. Points are spaced by distance, the chimney's lesson. The HUD
says when it is on and when it is about to be. `(` in the menu stands you across the boulevard
facing it and shifts the show (`_fountain_shift`) to start in three seconds, the way the rave is
started when you ask for it.

## The airport

Beside every Strip, on the Strip's own hash so it is always the same distance off its side
(`ZONES["airport"]`, salt shared with the strip's): open tarmac (`is_open()` yes, `road_at()` no,
so no walkers or traffic), with a glass **terminal** down the west side, **hangars** beyond it and
a **control tower** (`airport_part()`, built by `lot()` and drawn by `draw_airport_column()`:
glass lit cold with a mullion every bay; ribbed metal with the great door lit; a shaft with the
cab at the top all window). `AIRPORT_NAME` goes up over the terminal's front. The ground pass
paints the **runway** (`runway()`, `RUNWAY_W` either side of the middle, `RUNWAY_HALF` cells each
way): edge lines, dashes down the middle, piano keys at both ends, and the taxiway's yellow line.
`draw_airport()` lights it — white down the edges, green across the end they land at and red
across the other, the approach lights out beyond it with a strobe running in towards the runway
— turns the tower's beacon, and parks four airliners nose-in at the gates with the jet bridges
out to them.

**Planes on a timetable** (`plane_states()`, a function of time on `APT_CYCLE`): one comes in
from the north down the glide slope, landing lights blazing, touches down, brakes and turns off
for the gates; half a cycle on, another lines up, rolls, rotates and climbs away south.
`draw_plane()` is world points at `PLANE_SCALE`: fuselage white with its windows lit, wings,
engines, fin and tailplane, red and green on the wingtips, the strobe and the beacon, the
landing lights at the nose and the beam they throw ahead and down. While one is on the ground
**the next is already out there**, high, coming in to join the approach — lights only past 700
units, which is all you would see of one. It came in low at first and was behind the far city's
towers the whole way; up there it is a light in the sky the whole cycle. The HUD hears them.

**Where to watch from was the work.** Side on, a hundred units off, a landing was a few
characters at the horizon, and from sixty it was off either edge of the view. So `'` in the menu
stands you at the end of the runway, off its edge, looking up the approach — where plane
spotters stand — and the next one comes in straight at you and over your head. That only works
because **the town under the approach is kept low** (`approach_cap()`, applied in `lot()`, the
way `seafront_cap()` keeps the carnival's sky clear): rising with the glide slope from inside the
fence on, a corridor either side of the centre line. Before it the city's financial district
stood forty units off the end of the runway and hid the plane until it was overhead; the cap
had to start a few rows inside the airport's edge, because the edge wanders and left one row of
towers standing. Far out you see the landing lights, which is all you would.


**A flight.** The terminal has doors in the middle of its front (`gate_cell()`, `gate_door()`,
the `gate` lot flag, drawn lit in `draw_airport_column()`); walking through them is a venue
(`gate`) that opens the gate screen (`render_gate()`: a departures board — AC 101 boarding, AC 404
NOT FOUND cancelled — and the jet at the window). Enter pays `FLIGHT_FARE`, and then it is a
window seat on the right, once round the town, about 80 s:

- **The route** (`flight_legs()`, `flight_pose(home, s)` by distance `s`, `flight_s(t)` by time
  — accelerate, cruise, brake): lined up at the north end, down the runway and away south; a
  half circle west; north past the Strip; a half circle east onto the approach; down the glide
  slope from the north onto the runway. Every turn is to the right, the side you sit on, so the
  Strip is in your window both ways past it. `FLIGHT_R` is set from the airport–Strip spacing so
  the leg north passes 150 units west of the Strip, near enough for its lights.
- **The height** is a profile, not a cruise level (`flight_profile()`, cached per airport, 0.2 s
  once): over the tallest roof within 300 units either way plus `FLIGHT_CLEAR`, never under
  `FLIGHT_LOW`, smoothed by a max then a mean so it climbs before a tower and not at it. A flat
  130 cleared everything and showed nothing: **the camera cannot tilt**, so from that high
  everything within two hundred units was under the bottom of the window, and the Strip, flown
  past, was its car park. The take-off climbs steeply and eases off at the top, and
  `approach_cap()` now keeps the town low off the **south** end of every runway too, under the
  climb-out, where at first it is only just over the roofs. The check walks the whole route and
  asserts no roof within two cells comes within 2 units of the wheels.
- **The view** is `render_street()` from the plane with the horizon raised as it climbs
  (`FLIGHT_SKY`): that is how a raycaster looks down, and it is what puts the town under you in
  the window rather than off the bottom of it. `draw_window()` draws the right wing in world
  points (so it stays put as you look round) — filled row by row from the root to the tip, the
  seat `WING_BEHIND` ahead of the root so its leading edge runs diagonally rather than straight
  up — with its green light and strobe, then the cabin wall and the window's rounded frame, and
  the seatbelt sign. The HUD has what the captain would say (`flight_stage()`), what you are over
  (`place_below()`), and the height in feet. Arrows lean you to look forward or back; `x` dozes
  off and wakes you on the approach. Landed and stopped, you come out of the terminal's doors.
  Frame time over a whole flight at 30 fps: a median of 21 ms.
- `.` in the menu stands you in front of the terminal's doors.

**Flying it yourself** (`Cockpit`, `flight["phase"] == "pilot"`). `c` at the desk, `PILOT_FARE`, or
`f` in the menu, free, straight onto the runway. It is not on rails: `step()` is thrust against drag on
the square of the speed, a climb costs speed, a bank turns you (`PILOT_TURN`), and under `PILOT_STALL`
it sinks and the nose drops. **Curses sees no key go up, so the controls are the kind that stay put**:
`s`/`w` set where the nose is held, like a trim wheel - the way a stick works, back for up, as
the owner asked - `+`/`-` the throttle, and a wing stays down only
as long as the key keeps repeating (`PILOT_GRACE`) and comes back level by itself. `b` brakes, `x` hands
it back. Touchdown is graded on sink rate (`PILOT_GRADES`), and pays; a tilted wing, too hard, off a
runway or into a building is a wreck, then you wake up at the terminal. Any airport will do
(`nearest_airport()`): you come out of the doors of the one you landed at.

`render_cockpit()` is the real city out of the windscreen. The horizon goes with the nose, which is how
a raycaster looks up and down, and `roll_picture()` tilts it with the wings by sliding columns up one
side and down the other, never further than the panel can hide. `draw_runway_lights()` is what makes it
possible to find your way back: edge lights, approach strobes and the four lights beside the touchdown
that read white over the slope and red under it, seen from 3500 units. The panel (`draw_cockpit()`) has
speed, throttle, an artificial horizon, a compass, the way to the airport, and needles for the centre
line and the slope inside 2500. About 30 ms a frame at 300x90.

**Help with the landing, asked for after the first ones were hard.** `guide()` is a real approach,
a step at a time in `ck.leg`: out to an entry point off to the side unless you are already ahead of
the runway, then to the fix `PILOT_FIX` out on the centre line, where the slope starts at cruise
height, then down the slope along the line, and round again if you are blown off it. It keeps one
airport (`goal()`, `PILOT_KEEP`): **airports are only a tile apart**, so going out to one's entry
point brings you nearer the next, and switching to whichever was nearest turned you round half way,
for ever; it took three tries and a trace to see. Everything reads `guide()`: **the tower** (`r`,
`radio_key()`, `_radio_tick()`: take-off clearance, headings and heights, the localiser, cleared
to land, high or low or off the line, `PILOT_RADIO_LAG` before it answers, the last three lines up
in the windscreen), **the flight director** (`commands()`, the `(+)` on the artificial horizon:
put the wings on it), and **the autopilot** (`p`, `_fly_itself()`: it flies the guide down to
`PILOT_AP_FLOOR` on final and gives you the landing; any hand on the controls takes it off). From
80 random starts round an airport the autopilot got all 80 down, NICE with nobody flaring. `f` is
flaps (`stall()` comes down, drag goes up). The runways are lit out to `PILOT_LIGHTS` for every
airport about (`airports_about()`), with the tower's beacon going green and white up over the
town; the strobes and the slope lights within `PILOT_NEAR_LIGHTS`. `nearest_airport()` looked a
fifth of a tile away for the next airport, not a whole one, until this - which the first pilot
commit shipped with.

**Gear, wind and a flight plan.** Every flight from the gate or the menu has a `dest`
(`flight_plan()`: another airport one to three tiles off, from the seed), and then `goal()` is that
airport however far, so the panel's nav (`TO ...`), the tower and the autopilot all go there;
`PILOT_ENROUTE` out it is "proceed direct", and coming inside it the tower hands you over to the
next (`tower_name()`). Landing anywhere still counts; landing at `dest` adds `PILOT_DEST_PAY`.
Airports have names now (`airport_name()`; the menu's own is always `AIRPORT_NAMES[0]`, on its
terminal too). `g` is the gear (`gear`/`gear_set`, `PILOT_GEAR_TIME` to move, a quarter more drag
down; a `GEAR` warning low, a word from the tower) and landing with it up is `BELLY`: down, unpaid.
`air_wind(now)` is the wind, each night its own up to `PILOT_WIND_MOST`, more in rain; it only
moves you in the air (no wind on the roll, and on the wheels you straighten up with the runway).
Touch down crabbed past 0.18 and it is a grade worse, past 0.35 a wreck. `commands()` lays off the
nose into it so the guide's headings are tracks, which is what kept the autopilot landing in a
gale. Two things a crosswind showed: final was caught at 220 from the fix but given up at 160 off
the line, so a wind could put you on final and off it in one go, round and round (now 150 and
250); and floating past the end in the last few feet counted as overflown and went round. Checks
that want still air set `ck.calm`; `pk_at()` and the robot circuit do. Flown: 80 starts in each
night's wind, 40 in a 9-unit crosswind, 30 whole flights to their plans, all landed NICE.

**The view from outside, the landing light, and thunderstorms you can fly into.** `v` is
`render_outside()`: a camera `CHASE_BACK` behind and `CHASE_UP` over, swinging round after the
heading a moment late (`ck.cam`), the world level and the jet banking. `draw_jet()` is a dozen 3D
points turned by `plane_frame()` and joined by `_plane_seg()` as stairs (flat runs of `-`/`|`
with the slope glyph only at the steps; plain runs of slashes read as hatching) with a black edge
round it. **`draw_plane` was already taken** by the planes in the sky: defining it again
silently replaced that one. `l` is the light (on at the start): `draw_landing_light()` works a
row at a time like the ground, solving for the interval of each row the beam falls on instead of
testing every cell, and paints what it finds (`runway_paint()`: piano keys, aiming point,
touchdown bars, centre line, edges; grass round the field). It only reaches `PILOT_LIGHT_REACH`,
so from cruise it lights nothing, which is right. Storms: `air_cells()` puts one in some squares of
an `AIR_CELL_TILE` grid each night, building and dying with it, drifting on `night_wind()` -
**not** `air_wind(now) * t`, which went backwards whenever the gusts eased. `ck.weather()` is how
far in you are (`PILOT_TOWN_STORM` everywhere when `storming()`): turbulence in `step()`, gusts in
`wind()`, the murk, rain on the glass, the jolt; from outside one, `draw_air_storms()`. **The
first version looked silly** - a cylinder, so every strike filled a box with `:` from base to top
and a ruler-straight curtain of `|` hung under it - and was redone the way a night storm is seen:
`storm_profile()` gives each column across it (`u`, in radii) a billowing tower over a ragged base
and an anvil leaning downwind (`_billow()` is the smooth per-storm noise); between strikes it only
puts the stars out; a strike (`air_strike()`, now with a height and a ground-or-not) lights the
cloud round where it went off, with faint speckle tracing the rest of the outline; one in three
comes to the ground as a bolt with a branch; the rain is dots and short streaks, thick in the
middle, slanting with the wind, not all of it reaching the ground. Cheaper than the box, too. From the plane `v.air` stops the old by-bearing far storm, which was not anywhere. The guide
goes round a storm across the way (`_round_weather()`, one side per storm, not one you are in or one
on the destination), so the tower warns you and the autopilot takes you round; flying in is yours
to do by hand. Two things the weather showed: the director gave no bank under 12 so a gust on short
final drifted you off the runway (a little is allowed now), and **the autopilot turned straight off
the runway into a tower** - it now climbs out along the runway (`climb_out`) to `PILOT_CLEAR`, over
the tallest roof, first. Flown: 40 whole flights in all weathers, 30 with a storm put across the
route (all went round, all warned), 24 with one on the airport, all landed. Storms cost about 2 ms
a frame at 300x90; the street is untouched (frames identical).

**Other traffic.** `airway_traffic()`: airways every `AIRWAY_GAP` each way, flights along them
every `AIRWAY_EVERY` (with gaps), stateless; east-west and north-south on different
`AIRWAY_LEVELS`, so they never meet each other, and none at `PILOT_CRUISE`, so the autopilot never
meets them either. `traffic_about()` adds every airport's `plane_states()` - which now take
`arrive`/`depart`, because **your jet starts exactly where the departures line up, and the
arrivals touch down on top of it**: `ck.held()` is the tower holding that traffic for you (the
airport you are on, any you are low over, and your destination; the street's `draw_airport` reads
it off `v.held`). The exception is the one thing to do: landing on 18, the same way they take off,
the departures carry on, and `runway_busy()` against `ck.eta()` (ground speed: a headwind made you
late and a clearance turned into a go-around) gets you "number two", a late clearance, or sent
round by `_sequence()` on short final, radio or not; it only clears you with 4 s spare either side.
`draw_air_traffic()`: the street's airliner within 900, lights beyond (the side you see, the tail,
landing lights, strobe, beacon). `nearest_traffic()` feeds the TFC line, the `TRAFFIC` warning
(level and converging) and the tower's calls (`TRAFFIC_CALL`, once each - at 15 km it never
stopped talking); flying into one is a crash (`TRAFFIC_HIT`). `key()` now sets `ck.clock`: a key
before the first step judged the runway at the wrong moment. **`draw_plane` had its sides swapped**
all along (its "right" was its left), so red was on the right wing in the street view too.

**The landing report and the moving map.** `_touch_down()` keeps `ck.report` (sink, centre-line
offset to your right, how far past the threshold, crab, speed, bank, nose), and the roll and the
runway left are added when you stop. `landing_lines()` turns it into rows with a verdict and a
severity, `draw_landing_report()` boxes them up in the windscreen (either view) with a tip for the
worst (`TIPS`) - pick the worst by the severity, not the colour: in the checks every colour is the
same number. Stopped, it waits `PILOT_READ` or for Enter (and `x` now pays you too - it used to
hand the plane back unpaid). `draw_nav_map()` is heading-up, you at 78% down, and shows **one page
of `MAP_PAGES` at a time** - asked for, to make flying harder than one map with everything on
it. There were three (route, weather, traffic); the route and the traffic were then asked to be
one, so there are two: DIRECTION (the river and the woods, every runway - yours green, its line
in - the guide's way, `guide()`'s `"to"`, an arrow at the edge to your destination, and traffic as
arrows with their height in hundreds of feet) and WEATHER (storms as radar, the wind along the
foot). From `MAP_WIDE` columns it has the panel's second section (the panel sets `ck.map_wide`)
and `m` goes between the pages; narrower, `m` goes words, DIRECTION, WEATHER, words. The
title is the page and the range, the heading only where there is room for it (on a 21-column map
it covered the page's name). `[` `]` step
`MAP_RANGES`.

**A second runway, and the wind picks.** `runways(ci, cj)` is every runway as (middle, along,
half length): the long one north-south and a crosswind one east-west, `RUNWAY2_DJ` cells north
of the field. **Not across the middle**: the Strip stands 50 cells west of every airport, alongside
it, so an east-west approach through the field went straight over its hotels, and the approach
corridor would have cut them down. Out past the north end its corridor (`approach_cap()`, a band
of 8 cells) passes north of the Strip's last row. `airport_at()` takes in that north field.
`approaches(home)` is each end of each runway (`name` 18/36/09/27, `course`, `thr`eshold, `out`
along the approach, `rw`); `active_approach()` is the one most into the wind, or in still air the
nearer end of the long one, and `ck.pick_approach()` asks it (or the end a check set in `ck.end`).
`guide()`, `nav()`, the report, `on_runway()` (`runway_under()`), the alignment on the wheels
(`runway_course()`), the climb-out and the map all work in that runway's frame - right of the line
is positive now, for every way in. `taxi_net()` lays out the taxiways and holds; `field_cell()`
caches per cell which runways, taxiways and hold bars touch it, so `field_point()` - grass, tarmac
or paint - is cheap enough for the ground pass (about 2.5 ms more standing on the airport).
Two things it showed: **`approach_cap()` only looked in its own column of tiles** - the crosswind
approaches run east and west into the next - **and returned the first corridor it found**, not the
lowest, so a cell far out under one airport's approach and close in under another's kept a tower
the second needed gone. And a go-around turned for the entry point at a thousand feet, out of the
corridor and into one: it climbs straight ahead (`climb_out`) like a departure now. The Chinatown
lantern check was held to 60% by the luck of its first 250 buildings; the rate is 55%.

**Taxiing, gate to gate.** `Cockpit(..., gate=n)` - which the desk and the menu use - starts at
stand n (`taxi_net()["stands"]`, nose in, state `gate`); the checks and the robot still start on
the runway. `+`, `r` or `p` starts `_push()`: `PUSH_BACK` back over `PUSH_TIME`, turned to face
east, then state `ground` with `ck.taxi` (points still to go) from `_taxi_out()` to the hold and
the line-up for the runway the wind gives (`ck.dep`). `_taxi_progress()` pops points, tells you
at the hold and lined up (`lined`); landed and under 12, `_taxi_in()` picks the next turn-off
ahead and a gate, and on the stand you are `parked` and `ended`. Enter or `x` while landed skips
it (a tug). `p` on the ground is `_taxi_itself()`: `PILOT_TAXI`, slow for corners, stopping
lined up or on the stand. **Lining up took three goes**: aiming at the line-up point turned it
back round when it rolled past, aiming down the line converged too slowly; it steers on how far
off the line it is now. Off the runways `PILOT_TAXI_DRAG` (one step of throttle used to settle
at fifty knots), grass `PILOT_GRASS` and a wreck at speed, `GRASS`/`TAXI SPEED` warnings, and
the wheels straighten up with the runway on the take-off roll too - **a line-up 8 degrees out
drifted off the crosswind runway, whose field was a narrow strip, into a building**; the north
field is wider now and starts inside the main one's wavy edge, where taxiway A ran over a gap.
`draw_taxi_greens()` lights the way; the panel (`taxi_words()`), the outside strip and the map's
ROUTE page show it; `ck.gate_on()` / `v.my_gate` keep the parked jet off your own stand. Flown
from gate to gate with the autopilot: 50 of 50 parked, bar one blown off the runway by a storm.

**The control tower, with its radar.** `draw_atc_tower()` draws over the one-cell shaft `lot()`
builds (`ATC_TOP` tall): a cab wider than it, a ring of lit glass with a catwalk and a roof, a
mast, and the radar going round once every `RADAR_TURN` - long, edge on, long again, which is
what reads as turning; the beacon is on top of the mast now. `draw_airport()` draws it in the
street; `draw_runway_lights()` from the plane, unless the street already has. **`TOWER_TOP` was
taken** - the sky decks' height - and redefining it for this shrank every sky deck in town; four
sky-deck checks caught it.

**Taxiing by hand never got the take-off**, reported, and the checks had only ever taxied with
the autopilot. Three things: the route moved on only within 9 units of each point, so a corner cut
by hand stuck it; lined up wanted 3 degrees and 2.5 units, which only the autopilot does; and `r`
with the route not done always said "taxi to holding point". Now a point is passed once you are
beyond it along the next leg (`_taxi_progress()`), `on_departure()` is lined up by hand at 11
degrees and 8 units (the autopilot is held to the old figures, `tight`), and `r` on the runway
you were given clears you whatever the route says - at the hold it is "line up and wait", on the
wrong runway the tower tells you. And **the grass was a trap**: a fixed `PILOT_GRASS` drag
bigger than a few steps of throttle held a jet still where it stood, power on; it is per unit of
speed now. `ht_taxi()` in the checks taxis on the keys alone, corners cut, the way a person does.
**Height callouts, and when it goes wrong.** `_callouts()` calls `PILOT_CALLOUTS` on the way
down (1000, 500, 100, then every ten feet from 50), each once until you are well back above it,
and `draw_flight_words()` puts the last one up big in the sky over the runway for a second. The
low ones come fast - the game's sink is about 100 ft a second against a real 12 - so unflared
they are three frames each; the speed of the countdown is itself the cue. **Trouble**:
`flight_trouble(seed)` gives one flight in `PILOT_TROUBLE_ODDS` something, which the gate and
the menu's `f` pass in (`Cockpit(..., trouble=)`; the checks and the robot never get one), and
`t` at the desk is a **check ride**, `check_ride()` going down `PILOT_TROUBLES`. `_trouble()`
fires it: **engine** in the cruise, 40 s and more after lift-off (`up_at`); **birds** at
`PILOT_BIRDS_AT` on the climb out - `draw_birds()` past the windscreen for `BIRD_PAST`, a jolt,
and at `BIRD_HIT` one engine, or one time in four both; **blocked** on final 120 to 450 out -
`_block()` puts a truck on the touchdown zone (`blocker_at()`, driving out over `BLOCK_ROLL`,
amber streaks so it shows from a mile, `draw_blocker()`), shuts that runway (`closed`, which
`active_approach(..., shut=)` honours and the map draws in red `x`), and sends you round to the
other. `_lose_engines()`: thrust goes by `engines / 2`, one out swings the nose to it
(`PILOT_YAW`, held off with a little bank), the mayday, the radio on, `dest` the nearest
airport; with none the autopilot will not take it. **The dual failure was measured before it
was tuned**: at 175 ft there are about 350 units of runway still ahead, and the game's lift is
in the pitch, so with no power you float level until the speed goes - which is what killed the
first robot, floating past the end. Nose straight down and back on it gets down, 36 of 36 in
crosswinds; that is what the windscreen tells you. Landing gently on water is now a ditching
(`_ditch()`, `DITCHED`), and getting it down after trouble pays `PILOT_SAVE_PAY`. `em_fly()` in
the checks is fp_fly with trouble: engine, birds both ways and the truck all landed, 20 of 20
each in five winds when measured.

**Fuel, and the pad at every airport.** `ck.fuel` is the tank, of a full one: `_burn()` takes
`PILOT_BURN` times (`PILOT_IDLE` + throttle) a second per pair of engines, `PILOT_TAXI_BURN` of
that on the wheels - a long flight plan is about half a tank, a short one a quarter, taxiing two
per cent. The gate and the menu start you with `gate_fuel()`, a quarter to three quarters, and
say so when it will not reach the flight plan; checks and robots get a full tank (`fuel=None`),
so nothing they fly changed. `fuel_range()` is the cruise range the panel shows (`FUEL 45% 39km`,
gold when short of where you are going, red under `PILOT_LOW_FUEL`), and the tower warns once in
the air. Dry, `_run_dry()` is both engines gone, as the birds do. **The pad**: `taxi_net()`'s
`pad` and `padbox`, south of the stands on the line of the z0-150 turn-off, a lead-in to taxiway
A, painted in `field_point()` as a yellow box; `draw_fuel_farm()` puts two tanks, a FUEL sign
and the bowser by it (street and plane both), `draw_hose()` while filling, and the map an `F`.
`k` (`_fuel_key()`) on the ground routes you there (`taxi_to` `("fuel", None)`), on it starts
and stops the hose (`PILOT_FILL`, billed at `PILOT_FUEL_PRICE` a tank in `fuel_bill`, taken off
the pay at the end), and full, `_fuelled()` makes it `ground` again with a route out - so a
landing on the way is a fuel stop, and landings now add to `pay` (the destination's pay once,
`dest_paid`). **Taxiing from the pad found a hole in the hand-taxi fix**: a point counted as
passed by being beyond it along the next leg anywhere, and from off to one side of the route
every point was, so it cut across the grass into a hangar on 09 - passed only counts within 45
units now. Measured: from all four gates in five winds, to the pad and out, 20 of 20 lined up.
 `_label()` writes text over a frame spaces and all; `_text()` leaves spaces
see-through, which is how the first titles came out `--MAP-6-km--`. The key hint has a short form
(`PILOT_KEYS_SHORT`) for windows under 118 columns. About 2-3 ms a frame at 300x90.

**The approach had to be made flyable.** `approach_cap()` claimed to keep the town low but sky decks and
landmarks ignored it, and it stopped 550 units out, under a slope that only cleared the tallest thing at
1050: the first robot flight hit a building on final. Now it runs `APPROACH_LONG` cells off each end, no
tower or landmark stands in it, and no venue where the cap is under 18, so a `PILOT_GLIDE` slope clears
everything at both ends of every runway, which a check walks. That moved a few tall buildings near
airports. **`pk_fly()` in `checks.py` is a robot pilot on nothing but the keys**: take-off, circuit,
landing. If you change the handling and it can no longer land, neither can anyone. It flew 36 airports
out of 36 when this went in.

## The university

Another placed zone, in each tile between the factories and the next Strip. Old brick halls
(`UNIVERSITY`, the red palette, pitched roofs) drawn by `draw_campus_column()`: tall windows with
arched heads, warm light in about half of them, and ivy up one bay in three, thick at the foot
and thinning upwards. In the middle **the quad** (`quad_at()`, `QUAD_HI` by `QUAD_HJ`): open lawn,
`road_at()` no — the city's streets stop at it — mown like the suburbs' lawns, with paths
corner to corner and across it (`quad_path()`, in the ground pass), old lamps where they cross,
a bench with two students on it and their laptops glowing (`draw_quad()`). **The library** runs
down its west side, every window lit, LIBRARY over the door and bikes against the railings in
front; **the clock tower** stands in the middle of its north side (`clock_tower()`), over
everything round it. Both are `campus_solid()`: buildings whatever the street grid says, because
the grid ran a street through the library and left three of its seven cells open.

`draw_clock()` is the face, on whichever sides of the tower look at you: in screen space, lit
cream, ringed in gold, 12 / 3 / 6 / 9, and the hands at **the real time where you are**
(`time.localtime()`, the one thing in the city on your clock rather than its own). Its size has a
floor, for the signs' reason: true to scale it was two rows across the quad. And where it sits was
measured: at 42 the face was off the top of the screen from the far side of a seven-cell quad (the
camera's vertical focal length is bigger than it looks — 27.5 at 30 rows), so the tower is 30 and
the quad eleven cells deep. On the hour the HUD has it striking (`clock_hint()`). `{` in the menu
stands you at the south end of the quad looking at it.

**The library's doors** are open, lit, in the middle of its quad side (`library_door()`, the
cell with `libdoor`), and walking in — a venue in `venue_at()`, so the hurry rule applies — is
**the reading room** (`render_reading_room()`, the `reading` flag in `main()`): the stacks, green
lamps on the long tables, and `LIBRARY_BOOKS` to choose from — `w` Wikipedia, `p`
PsychonautWiki (the restricted section), `x` back out onto the quad, three steps out and facing
away, or the doorway would take you straight back in.

**The two readers are copies**, in `library/`: `wiki_tui.py` and `psychonaut_tui.py` from the TUI
repo (noajwz/TUI, as of its `b65ec95`), byte for byte, so the city carries its own and does not
need that checkout beside it. They are **run, not imported** — `run_program()` hands one the
terminal (`def_prog_mode` / `endwin`, a plain `subprocess.run` with the same Python), then takes it
back (`reset_prog_mode`, `flushinp` so keys typed there do not walk you, nodelay and keypad
again) and you are in the reading room again. They are stdlib-only and self-contained, like the
city. A fix to one in the TUI repo does not reach here by itself: copy the file over again (and
the reverse). A missing file is "that shelf is empty", not a crash.

Both readers open on their search prompt, so from a test it is Esc, then q. And walk in with the
arrow, not `w`: in the room `w` is Wikipedia. The pty harness sends the city's `q` last and then
`waitpid`s on it, so a test that leaves you inside a reader hangs. `"` in the menu stands you in
front of the doors.

**The menu has a column for the rest**, AND THE REST (`CHEAT_MORE`). It was a fifth column
with Tab paging it in on an 80-column window until the panel was trimmed to four.

## The metro

One city block in `METRO_ODDS` has a station (`station_of_block()`, cached): its entrance on
the pavement in front of a building with a street front, named from `STATION_WORDS` for its part
of town. Never in the woods, a park or a placed zone, and only where `can_stand()` — one landed
on a pier. `draw_station_entrances()` puts up the lit red M on its post, the railings round the
stairs, the light coming up out of them and `(M) NAME` once you are near enough to read it;
the HUD says `e` goes down (checked before the manhole, which also takes `e`).

Down the stairs is a screen of its own, like the taxi's (`metro`, `render_platform()`): tiles,
the name on a blue band, the board with the next train and the destinations
(`metro_dests()`: the nearest station in each other part of town first, then the nearest
others, eight at most, never one with this station's own name), people at the yellow line.
`train_phase()` runs each station's train on its own `METRO_EVERY` cycle — in out of the tunnel,
doors open for `METRO_DWELL`, away. `w`/`s` choose, Enter pays `METRO_FARE` from the wallet and
waits; when the doors are open you board and `render_ride()` takes over: the line map with you
moving along it, the tunnel's lights streaking past the windows (slowing at both ends), the
platform sliding in, "Next stop" then "This is". Six to fourteen seconds by distance. You come up
the destination's stairs facing the street. `x` or Esc goes back up without riding.
`metro_dests()` costs a third of a second cold — once, going down — and nothing per frame.
`-` in the menu stands you in front of an entrance.

## The Pokemon Center

A joke, and a useful one. One city block in `CENTER_ODDS` has a Pokemon Center
(`center_of_block()`, hashed per block like the metro stations, and like them never asking
`lot()` — `lot()` asks it, through `center_at()`, and turns the cell into one over whatever it
was going to be). Out of the parks, the woods and the placed zones, on a building with a real
street front. `draw_center_column()`: white walls, the red roof band all the way round, lit
windows, sliding glass doors; `draw_center_signs()` puts POKEMON CENTER on the band and the ball
(`CENTER_BALL`) lit over the doors. The ball was on the roof first, and from across a street —
as far back as you can stand — the roof is over the top of the screen.

Walking in (a venue, so the hurry rule applies) is `render_center()`, the `poke` state in
`main()`: the tiled floor, Nurse Joy (`JOY`) at the counter with her lines (`CENTER_SAYS`),
the healing machine with its six balls, and the PC in the corner. `h` and she takes them —
the balls light one by one, flash, the chime — then she bows and hopes to see you again
(`CENTER_DONE`); free, as it should be. `c` is the PC: **`library/pokemon_types_tui.py`**, a
byte-for-byte copy of the TUI repo's type chart (as of its `fdffd17`), run through the same
`run_program()` hand-over as the library's readers, so the same rules hold — it is run, not
imported; a fix there does not reach here without copying it over again. `q` quits the chart.
`x` steps you back out the way you came, facing the street. `,` in the menu stands you across
the street from the nearest one.

**Big** (`render_center_big()`, on the big-window system when `center_size(k)` fits): POKEMON
CENTER across the back wall in block letters; Nurse Joy and the healing machine drawn small and
blown up `k` times (`_blow_up()`) - they are shapes - so the balls light up big; the PC a bigger
monitor with PC on it in block letters, since blowing the small one up would read PPCC; the
counter and the floor tiles `k` times as wide. What she says, the chime and the keys stay plain.
`_center_state()` works out the moment (what she says, balls lit, the bow) once for both sizes.
`z` is in the Center's own key branch, which catches every key before the shared one. The fifth menu column is AND THE REST now.

## The arcade, big

The second screen on the big-window system. `render_arcade()` puts the arcade's name up in bigger
block letters (`k` columns by `k - 1` rows a dot, a colour a letter) and draws each cabinet with
`draw_cabinet_big()` at `cab_size(k)` - the screen `k` times over, its demo blown up with
`_blow_up()`, the game's name and COMING SOON / INSERT COIN left in plain letters so they stay
words. `arcade_order(arc, width, height)` counts the cabinets that fit at that size, and `main()`
passes it the height, or the cabinet you pick and the one you get would disagree on a big
window. Playing (`render_game()` hands over to `render_game_big()` when `game_size(k)` fits):
the playfield every cell a `k` by `k` block of itself - the games themselves are untouched and
still draw their 40 by 16 - the name and SCORE / HI in block letters, GAME OVER across the
middle in block letters on a cleared band with the reason under it, the controls in plain
letters. At scale 1 the room and all six games are frame for frame what they were.

## The casino, big

Zoomed out, a window can be three hundred columns across, and the casino was drawn for a third of
that: the wheel stopped growing at 42 columns by 10 rows, and the slot machine and the blackjack
table are fixed drawings, so on a big window it was an island in the middle. `big_scale()`
gives a scale of 2 on a window with room for two rooms (`BIG_W` by `BIG_H`, 150 by 44 —
so 300 by 88) and 3 on one with room for three; anything smaller is scale 1, and **at scale 1 the
room is exactly what it was** — checked frame for frame against the old code at five sizes up to
299 by 87.

At scale 2 or 3 `render_casino_room()` draws the banner in block letters (`_blocks()`, the 3x5
`BIG_FONT` plus `CASINO_FONT` for `$ @ * & %` and the suits), lets the wheel grow into the room —
with a rim and an inner cone (`RIM`) so a wheel that size reads as a wheel and not a ring of
numbers, and a little taller than the small one's flatness, or a tall window's bottom third was
empty — and puts the winning number and FAITES VOS JEUX in block letters. The machine and the
table are drawn again by `draw_slot_big()` and `draw_blackjack_big()` (`slot_size()`,
`table_size()` give their footprints, which the room's layout uses in place of `SLOT_W` and the
table's 40): the payline's three symbols big in their own windows with the rows above and below
small, the cards with their ranks in block letters and the suit in two corners, the money, the
win and the outcome in block letters. **Ordinary text stays small** — the paytable, the keys,
"dealer" — because a terminal cannot draw a letter bigger than its font, and a sentence in block
letters is four columns a letter. `z` in the casino turns the big room off and on (`_big_screens`), for comparing the two on one
window.

**Plinko, the races and High Flyer** scale too, each at the biggest scale that fits it in the
room (`kp`, `kr` in `render_casino_room()`) - in practice the room's. Plinko (`draw_plinko(...,
k)`, `plinko_tall(rows, k)`, `plinko_wide(rows, k)`, `plinko_title(k)`) spreads its pegs k times
both ways, puts PLINKO over it and the last win under it in block letters. The races
(`draw_races_big()`, `race_size(k)`) give each horse a lane five rows deep: its number in block
letters in its silks, name and odds beside it, and a three-row horse and jockey (`HORSE_BIG`)
galloping. High Flyer (`draw_flyer(..., k)`) was already as big as the room - its graph is drawn
from the space it is given - so only the words grow: HIGH FLYER, the multiplier (very big) and
FLEW AWAY in block letters, and the plane (`FLY_PLANE_BIG`). **Watch for `k` as a loop
variable**: `draw_plinko()` and `draw_flyer()` both had `for k in` loops, and once `k` was the
scale those loops overwrote it - the normal-size frame comparison caught it (balls in the wrong
row, the big plane at scale 1). They loop over `n` now. This
is the first screen of the scaling system described near the top of this file - follow that for
the next ones.

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
putting it on the parallax would make it slide with the town as you pan, which it does not yet. ctrl-a `=` in the checks' menu
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
with its light on. ctrl-a `_` in the checks' menu stands you on the street at its edge looking in.

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
HUD says `~ a siren somewhere ~`. ctrl-a `<` in the checks' menu stands you on the pavement eighteen units ahead
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
the cars are not drawn — they are on top of it. ctrl-a `)` in the checks' menu stands you on a cross street forty
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
pot and says what diners have always said. The seat is remembered the way the ramen bowl's is. ctrl-a `d` in the checks' menu.

**Billboards** are ads (`ADS`, made-up brands, soda and a few others) hung out over the wide streets from low roofs
(8-12 units: on a tall one it is off the top of the screen from anywhere you can stand) in the busy
districts, one in `BILL_ODDS`. They stand at right angles to the frontage, out over the road like a
gantry board, so they face along the street: flat against the frontage they could only be read from
straight across the road, and no street is wide enough to stand back that far — and set over their
own roof they hid behind the roofline of every building that side. Found per city block and cached
(`bills_in_block()`), like the sky decks' beacons. The trap: drawing each letter as a world point on
the board's plane looked right and could not be read — from any way back the brand and the slogan
rows project onto the same screen rows and overwrite each other. So the corners are projected in the
world (with the depth per column for occlusion) and the lettering laid out in screen space across
what they cover, and the board's blank cells are blanked so the city does not show through it. **What is on them is a picture, not words**: each ad has three (`ADS`: big, small and a tiny
one for far off), the biggest that fits goes up, and past the big one it is blown up a whole
number of times. At 300x90 from forty units off a board is about 47 by 12; on a small window, 16 by 5. `$`
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
somewhere you should not go. It is cached per cell (`_road_at_cache`), like
`is_open()`: each placed part of town added a check in front of the answer, and before the cache
it was a sixth of the frame. `zone_home()` keeps each zone's centre per map tile for the same
reason.

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
(and the next plinko ball an edge, the next race the long shot's, the next flight a
hundred), once —
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
`plinko_wide()` x `plinko_tall()` for it gets a line of text.

**Bigger and harder are yours to set**: `[`/`]` step the rows through `PLINKO_ROW_SET` (8 to 16)
and `1`/`2`/`3` the risk (`PLINKO_RISKS`). `plinko_table()` makes every one of the fifteen tables
rather than anybody typing them: the edge is set by the risk and grows with the rows, since an
edge on sixteen is one ball in 32768 (high risk tops out at 1000x), the middle is 0.5, 0.3 or
0.2, and the curve between is solved by bisection so the table pays `PLINKO_BACK`; rounding to
what a machine would print (`_nice()`) leaves them between 92 and 97%, and a test holds all
fifteen to it. Each ball carries its own path and table, and the machine refuses to change while
any are falling. A board too tall for the room goes up over the ceiling and the back wall; 1000
is printed 1k under its bin, or it runs into the 180 next to it. A ball to the edge sets the building
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

**High Flyer** is the crash game, the sixth, on `f`. A round every so often: `FLY_BET` seconds of
bets (`p` puts the stake on, `+`/`-` step it), then a plane takes off and the multiplier is
`fly_mult()` — e to `FLY_GROW` times the seconds flown — until it flies away; `p` again cashes
you out at whatever it says, and the plane gone first is the stake gone. `Flyer._start()` draws
where it goes when the round starts, `FLY_BACK / (1 - u)` to the cent and capped at `FLY_TOP`, so
the chance it gets past m is `FLY_BACK / m` for every m: whatever you cash out at, the game pays
back 97%, which the tests measure both ways (the distribution, and six thousand rounds at 2x).
Truncating to the cent puts one round in 25 on 1.00x, off the ground before it leaves. `u` cycles
an automatic target (`FLY_AUTO`), which `update()` cashes the moment the multiplier passes it —
whether or not you are looking. `draw_flyer()` is the graph: a log scale up the side, the curve
drawn behind the plane, a burst where it went, the figure in the big font, green while it flies
and red when it has gone, what your stake is worth, four others at the table cashing out or not
(`FLY_PEOPLE`), and where the last ones went. Cashing out at 20x or better lights the building;
`%` sends the next one to a hundred.

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
`v.wide` bookkeeping, so the Japanese stays on the sign outside. ctrl-a `r` in the checks' menu stands you
across the lane from a shop, looking at the front — a step or two in is the counter — and a
second press finds another.

## Manholes, and the tunnels under the streets

One street cell in `MANHOLE_ODDS` has a manhole in it (`manhole_at()`: a proper street only,
never on a bridge or in the water, hash first), off the middle of the roadway along the street -
about one every 170 units of street, which is "some, not too many". `draw_ground()` paints the
cover per point the way it paints everything on the ground: a rim of `o`, the grip pattern cast
into it, and before the snow, because what comes up from under it melts it. One in three
**steams** (`draw_manhole_steam()`): puffs off the cover that grow and thin from white to haze as
they rise, which is what you find one by from down the street.

You go down with **`e`**, standing on it (`manhole_under()`, within `MANHOLE_ON`) - a key and not
a step, because the autopilot walks the roadway and would otherwise drop you down every manhole it
crossed. `MANHOLE_ON` is wider than the cover on purpose: a tap of `w` carries you 2.3 units, and
at 0.8 you could tap straight over it without ever being on it. ctrl-a `x` in the checks' menu stands you seven
units back along the street from a steaming one - nearer and the cover is under the bottom of the
screen, since the camera cannot look down.

**Down there is a tunnel system, and it is under the real streets** (`sewer` in `main()`,
`new_sewer()`): `sewer_cell()` is the middle cell of every street, and from there across to any
manhole in the same street, so all of them join up and walking along down here is walking along
up there. **It runs under the river too** - an avenue that stops at the water carries on below,
or half the manholes were cut off from the other half. `e` at any ladder (`sewer_ladder()`) comes
up on that cover, so it is a way across town. `render_tunnels()` is a little raycaster of its own:
brick, a pipe, a walkway, water down the middle, lamps, rats, a ladder with the streetlight on it,
and dark at `SEWER_SEE`. It has its own walking (`sewer_step()`, `SEWER_GRACE`), since nothing up
here applies. About 10 ms a frame at 300x90. Mind the status lines: they are long enough that a note
gets cut off, which has happened at the bar, the loft and here.

**The turtles are an easter egg now.** Their lair used to be what was under every manhole. It is a
door in a tunnel wall, in one `LAIR_TILE` square in `LAIR_ODDS` (`lair_in_tile()`, hashed, kept in
that square), lit green round the edges; the status line says you can smell pizza inside
`LAIR_SMELL`, and that is all the help you get. Walking into it is `render_sewer()`, the lair: a
brick arch, a pipe dripping, fairy lights, an old couch and a television on the blink - and **four
turtles round a pizza box** on a crate, each in their own coloured headband (`SEWER_BANDS`), eating
on their own counts: a slice up at the mouth on the bite, a string of cheese as it comes away. For
the first few seconds they all freeze and look at you; then it is cool, and they talk (`SEWER_SAY`).
They get through a slice every `SEWER_EAT` seconds and leave two (`sewer_slices()`), and `p` takes
one - until the box is empty. They have no names. `t` in the menu stands you in front of the door.

## The case of the last slice

A mystery, one to a sitting (`case` in `main()`, `new_case()`; nothing kept when you quit). It
ties the city together: `CASE_TRAIL` is where to go, in order, what to call it, how to find it
(`find_place()`), and what they say there. A note starts it: in your pocket after `CASE_AFTER` of
play, with your first drink at a bar, on the pigeon you sent off, or `m` in the menu. Each step is
just **being there**: `main()` works out where you are each frame and `case_arrive()` moves on if
it is the next place. So there is no case logic in any of the venues.

`draw_case()` puts what they said in the middle for `CASE_SHOW`, on a board of its own, and all the
time a small line at the foot with who to ask next, which way relative to where you are facing, and
roughly how far (`case_line()`), the rave's reasoning: a fact you cannot walk on is no help. `j`
hides the line, and it stays off while you are inside somewhere. `c` in the menu jumps to the next
clue, for testing and for the impatient. **Spoilers are in `CASE_TRAIL`.** It ends on a low roof, and
pays `CASE_REWARD`, which is the one time money comes to you for nothing: somebody earned it.

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
candlelight, a candle either side, and the name over it (`TEMPLE_NAMES`). ctrl-a `*` in the checks' menu stands
you across the street from one, the way the casino's does; a few steps in is the door.

Inside (`render_temple()`): the vault, the pillars going away down the nave with stained glass
between them, pews either side of the aisle, candles along the altar — and on the altar a
terminal, on which `g` asks for **the word of God** — one word a press. It is Terry A. Davis's
oracle from TempleOS, done his way: the random number is the time since the last word was asked
for, in nanoseconds (`oracle["last_ns"]`, `time.perf_counter_ns()`), and `god_word()` is that
gap modulo `GOD_WORDS` — a list of the city's own, not his, each word once (it had duplicates,
which made "behold" likelier). It gave twelve words a press at first, a generator seeded with
the gap; that was asked to change "so it's truly random", and rightly: twelve words from one
seed are one random number's worth, the other eleven decided by the generator. Now nothing
stands between the moment you press and the word. Words build up into a verse; `GOD_PAUSE`
without one, or `GOD_VERSE` words, and the next starts a new verse. The last few verses stay on the screen, the newest bright. Free to go in; nothing to pay.

**The choir** (`draw_choir()`) stands on risers across the nave from the booth: two rows in white
robes, mouths opening on `CHOIR_BPM` a breath apart along the row, a director side on with his
hands going, ASCII notes (`CHOIR_NOTES`) floating up and fading — and over them, in gold on the
beat, **the last word the terminal gave, sung**, cut up by `syllables()` (hal-le-lu-jah, mer-cy);
until it has given one they hold a long a-men. Visual only: the standard library has no sound
but the terminal bell.

**The confession booth** stands against the side of the nave; `c` steps into it (`booth` in
`main()`, cleared when you leave the temple or jump). `render_confession()` is the inside: dark
wood, the lattice, the panel sliding back and the priest's shape behind it with a candle, and
what has been said both ways. **Every key is a letter in there**, `q` and `s` included — you type
your confession, Enter gives it, backspace works, and **esc** steps out. That needed
`curses.set_escdelay(25)` in `main()`: by default curses holds a bare esc for a second to see
whether an arrow key follows, so esc-then-anything was read as one meta key and the booth never
let you go — and the pty harness, which ends every run with `q`, hung on it. `absolve()` is the
priest: the first of `SINS` whose words he hears — **whole words or their starts**, matched on
tokens, because "cheat" has "eat" in it and a confession about the menu was first told hunger is
no sin — and otherwise that the city has heard worse; now and then what the city told him
(`ledger`: how many times you jumped across it from the menu tonight, or what is left of your
thousand dollars); a penance from `PENANCES`, all of them things to go and do in the city; and
peace. He takes `CONFESS_WAIT` to answer. Someone saying they are hurting is told, plainly, to
talk to someone.

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
went in. On a roof the eye is seventy-odd units up, rays go `ROOF_REACH` (520 - at 260 the town stopped short of the
horizon), walls twenty-two deep, and
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
you straight back up. ctrl-a `^` in the checks' menu stands you outside a lobby; one step in and you are riding.

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
the sky-deck crowns' trouble again. ctrl-a `p` in the checks' menu stands you outside the lobby. About 9 ms a
frame on the roof at 110x34, 19 at 240x70.

## The bowling alley

One lot in `BOWL_ODDS`, on a street, not in the residential or financial parts of town or a park, held
low (`b["bowling"]`). `draw_bowling_column()`: dark, two bands of neon chasing in opposite directions,
glass along the bottom; `draw_bowling_front()` the BOWLING board, a neon pin and a ball. Walk in
(a venue; no fee at the door, `BOWL_COST` a game). `k` in the menu stands you in a doorway.

**It is really played.** `Bowling` is ten frames, in inches, on a lane of real size: `step()` moves the
ball and the pins as circles at `BOWL_STEP` and `_hit()` knocks them apart, and a pin that has been hit
has fallen. So a strike is what a hooked ball in the pocket does and a split is what one on the nose
does, and nobody decides. Measured over random throws: about 6 pins, strikes 2%. It costs well under a
millisecond a frame. `bowl_scores()` is the scoring, and it waits for a strike's two balls and a
spare's one, as the rules do. Curses sees no key go up, so nothing asks you to hold one: `a`/`d` line
you up, `p` stops the spin meter, `p` the power meter. The hand wobbles a little (`bowl()`'s caller),
or a good line would strike for ever. `x` stops playing; `s` only walks you out when you are not.

`render_bowling()` is three lanes going away from you under the black light. The last stretch to the
pins is drawn longer than it is (`place()`): true to scale, four rows of pins land on one row of the
screen. Big windows go by the one system: the maths grows, the pins and people `_bar_sprite()` them,
the name, the sum and STRIKE in `_blocks()`, and the frames and meters stay plain.

## The rooftop bar

One sky-deck tower in `BAR_ODDS` is a bar instead (`kind: "bar"`, a name from `BAR_NAMES`, and
`bar_yaw`, which way the bar stands; decided on its own hash in `lot()`, off the same towers, so
nothing else about the building or the city moves). From the street: a neon glass over the door,
ROOFTOP BAR and the name, one step in and the lift, `LIFT_FEES["bar"]`. From other roofs and the
plane it has no mast, but a string of warm bulbs round the roofline (`draw_tower_beacon()`). `s`
goes back down, as on any roof. `b` in the menu stands you outside; the sky deck's jump skips bars
(`_tower_spot(x, z, bar)`).

The roof is `roof_view()`, so the skyline is the real city with everything out there in it. Over it
`draw_rooftop_bar()` draws the terrace **in screen space but by bearing** (`bar_col()`), so things
slide on and off the side as you turn and hold still as they should: at arm's length, world points
come out as stripes - the parapet's lesson. A rail with the city showing through under it, a deck
that hides the nearest street, bulbs sagging across the top, and round you the bar at `bar_yaw`,
tables, heaters, a trio and some people at the rail (`BAR_SPOTS`). Straight behind the bar is left
empty: that is the view. Sprites are solid (`_bar_sprite()`: a blank inside a row hides the city).

`1`-`4` order, facing it (`bar_facing()`), off the wallet (`BAR_DRINKS`): `BAR_MIX` of the bartender
shaking it, then the glass on the counter and a line from `BAR_SERVED`. After `BAR_LIMIT` it is
water, free. Past two drinks the view sways, a very little, off `at_bar["n"]`: the tab is for the
visit and goes when you leave. **Big windows go by the one system**: the art `k` times over, the
name in `_blocks()` on its own board, the menu and what is said in plain letters, `z` in `main()`.
Don't put the name directly on the city: its lights ran through the letters.

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
roof climbs you back down into the alley. ctrl-a `|` in the checks' menu stands you at the foot of one.

**The loft can be played with** (`at_loft` in `main()`, `new_loft()`, for the visit): `f` feed, the
flock flutters down and pecks at seed on the gravel for `FEED_LEN`; `r` lets them out, once round on
`FLOCK_LAP`; `n` sends one off, and `POST_TRIP` later it is back with a line from `PIGEON_NOTES`.
Each is only *when it was done*, and `draw_loft_visit()` works out the rest from the time. `loft_key()`
is what says no. You have to be facing it, near enough.

(The back of a giant neon sign, letters reversed, was tried too, and was not interesting enough.)

**Most of these roofs are plain, and that is the point** (the owner asked for it). One in
`LOW_ROOF_ODDS` has somebody's something on it, by a hash of the cell (`low_roof()`): a **pigeon loft**
that sends its flock round over the street on a lap of the clock; **washing lines** that sway harder
in the rain; or
**someone's garden**, with pots, tomatoes, two deck chairs, a string of bulbs and a radio. One roof
in `ROOF_CAT_ODDS`, of any kind, has **the cat**: on the parapet (`v.roof_edge`), and every forty seconds
it walks along it to somewhere else, a function of the time like everything that moves. You come up
facing what is there (`low_roof_yaw()`). `draw_low_roof()` runs in `main()` after `render_street()`,
in screen space by bearing with the bar's helpers (`bar_col()`, `_bar_sprite()`), so a far beam never
cuts across something at arm's length, and the big-window scale comes with them. The loft and the
garden stand on `draw_roof_floor()`, a wall and gravel: without it they hung in the air over the city,
and were reported as not looking great. Keep each scene together and big, not scattered. `r` in the menu goes
to the next kind round; `|` still finds any escape at all.

### Washing lines

The owner liked the washing on the low roofs enough to want it off them too. In the residential
parts of town, one street cell in `WASH_ODDS` has a line across it, building to building
(`wash_lines_at()`: both ends on a real building, under both roofs, at most four cells across, and
now and then a second a floor up); and one low building in `WASH_ROOF_ODDS` has one on its roof, on
posts, seen only from up high. Found per city block and cached (`washing_in_block()`), hash first.
`draw_washing()` is **world points, one screen cell apart**, so nothing bunches at arm's length: you
walk under it, buildings hide it, and it swings from the peg, most at the hem and more in rain. Set
low on purpose, 5 to 8 units: the camera cannot tilt, and from a little way off that is in frame. About
2 ms a frame on a street that has them at 300x90, nothing elsewhere. `h` in the menu stands you down
the street from one.

## The pictures

A cinema is as rare as a club — `CLUB_ODDS` on its own hash, a street front required — and from
the pavement it is a marquee over lit doors: NOW SHOWING and the title in a ring of chasing bulbs,
in screen space for the casino marquee's reason. ctrl-a `m` in the checks' menu stands you in the doorway, and
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
columns, in block letters where they fit on screen, and **the tickers cover the wall under it**
(`draw_ticker()`, from `draw_exchange_column()`, so on all four sides and behind anything in front):
rows of the market between gold rails, every other row the other way - every stock, its price, and
the last tick's move in green `^` or red `v`. One letter a column, counted from the middle of that
wall (`v.ticker_anchor`), so it reads at any distance. Block letters were tried first: a wall is one
lot wide, and two or three of them fitted and no stock's name. The columns are lit from the foot and
the pavement takes the colour of its own stock's last tick. It was asked to be more apparent. ctrl-a `e` in the checks' menu stands you on the
floor (a taxi goes there, so it is off the panel).

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
plays it, `s` walks you out. ctrl-a `g` in the checks' menu stands you in the door.

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

**On a keyboard where `` ` `` is a dead key it used to misbehave**, reported as "it doesn't
open when I press the button, and then when I close it again it does the cheat". On
US-International - the usual layout on Windows in the Netherlands - `` ` `` sends nothing
until the next key and then both together: a second `` ` `` gave two, so the panel opened and
shut in one frame; a letter after it gave `` ` `` and the letter, so the panel opened and jumped
at once; a vowel came out as one accented letter (UTF-8, `0xC3` and one of `CHEAT_GRAVES`),
which was no key at all. `read_key()` reads every key in `main()` and takes whatever came in
the same read as a `` ` `` to be the dead key letting go - by hand two keys are never in one
frame - so each of those is one press of the panel's key and nothing else. F1 opens it as well,
a key that is never dead. There are checks of each with a stand-in `getch()`, and a pty case.

`` ` `` opens a panel over the live view — over, not instead of, so that weather you change happens
in front of you. **A jump closes it** — you went somewhere to look at it, and with the panel still
up the next key is a district or another jump; the `-> where` note shows on the HUD for four
seconds instead.

**Nowhere a taxi goes is on the panel.** Asked for on 2026-11-08: "everywhere I can get with a
taxi can be thrown away", and the FUN, EAT and AROUND TOWN groups with it. So the casino, the
club, the pictures, the arcade, ramen, the diner, the temple, the exchange, a sky deck, the roof
party, the carnival, the lighthouse, the big bridge, the bank, the woods and the lake (all of
`TAXI_DESTS`), and the claw, the hammer, a manhole, a lit alley, the El, a fire escape, a car
park, a police car and the highway went. **Do not put a taxi destination back on the panel**, and
a new place the taxi will go to does not get a key: adding it to `TAXI_DESTS` is its way in.
They are not gone for the checks: `CHEAT_HIDDEN` keeps them, and with `ASCII_CITY_TEST` set
(`pty_checks.py` sets it) ctrl-a and a key from it jumps there - the pty cases walk into
casinos and up fire escapes from a jump, and a taxi would cost each a minute. Nobody playing
can reach them that way, so the keys are free for anything new on the panel; visible keys
are matched first anyway. `checks.py` looks at both tables for everything that is about where a
jump lands.

**Trimming it found a bug that had been there a while**: the rooftop bar, a low roof, washing
lines, bowling, the turtles and flying were on `1` `2` `3` `4` `5` `8`, and the mystery on `6`
and `7` - the parts of town's digits. Places are matched first, so downtown, residential, old
town, chinatown, market, park and financial could not be reached at all, and docks only when no
case was open. They are on letters now (`b` `r` `h` `k` `t` `f`, the mystery `m` and its next
clue `c`), and a check asserts that no key on the panel does two things and none are a case
pair.

**Four columns** (`draw_cheats()`): NIGHTLIFE, MONEY, VIEWS and THE MYSTERY; the PARTS OF TOWN
(the digits, `1`–`9` and `0`, with the placed zones); AND THE REST; then WEATHER & SKY and
NIGHTS. A new place goes into a group, not on the end of a list. It was once grouped by where things were — the city, the streets, out of town —
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

## The taxi

**`t` on any street hails a cab** — a proper street (`road_at()`), dry, not in a venue, the sewer
or on a roof; anywhere else the HUD says to stand in a street. `taxi` in `main()` is a state like
the lift's, and nothing moves you while it is set. `hail`: `draw_taxi_coming()` brings it along
the street's own axis towards you over `TAXI_ARRIVE`, slowing, three sprites by distance, and
stops **6.5 units off** — at 3.2 it pulled up under the bottom of the screen, the camera not being
able to look down. `menu`: you are in, and `taxi_dests()` has found the nearest of each of
`TAXI_DESTS` with `find_place()` (about 60 ms, once) and priced it, `FARE_BASE` plus `FARE_PER`
a unit as the crow flies; `draw_taxi_menu()` puts WHERE TO? in the windscreen, `w`/`s` or the
arrows choose, enter or `t` goes, `x` or esc gets out. The fare comes out of the wallet up front;
short of it, the driver shakes his head. `ride`: the camera, at a seated `eye`, goes along the
nearest avenue towards where you are going for as far as it runs open (`taxi_route()`,
`taxi_ride_at()`, eased at both ends) while `render_street()` draws the real city past it and
`draw_cab()` puts the back seat round it — roof, pillars, the mirror with dice swinging, wipers
when it is wet, the driver's headrest, a line from him (`DRIVER_SAYS`), the meter counting up to
the fare in red. **It is the city going by the window, not a map of the way**: the route is one
straight avenue, and at the end you are set down at the place, facing it. Six to fourteen
seconds a ride, by distance.

### Driving it yourself

**`d` in WHERE TO? and the driver gets out**: "All yours. I'll be in the diner." `cab` in
`main()` is a `Cab`, and `elsewhere()` counts it. There is no cheat key for it - the panel has
none left - and it needs none: `t` works on any street, so the way in is two keys from anywhere.

- **The controls stay put, the plane's way**, because curses sees no key go up: `w`/`s` step
  the speed held (`CAB_STEP`, a cruise control, up to `CAB_TOP`, down to `CAB_BACK` in
  reverse), space or `b` brakes to a stop, and a steering key holds the wheel over only while it
  keeps repeating (`TURN_FIRST` for a fresh press, then `CAB_GRACE`) and it comes back by itself.
  The wheel turns you by how fast you are going (`CAB_R` plus `CAB_R_FAST` a unit of speed), so
  standing still it turns nothing. Wet roads (rain or lying snow) brake at `CAB_WET_GRIP`.
  **The steering was "way too sharp"** at first, reported after the first drive: the wheel
  went to full lock in a quarter of a second, so one tap was full lock, and the circle widened
  so little with speed that the faster you went the faster you turned - 2.8 rad/s flat out. Now
  `CAB_STEER` takes the wheel over in most of a second (a tap is about a third of lock, five
  degrees of heading at speed) and `CAB_R_FAST` widens the circle enough that it turns at about
  1.1 to 1.3 rad/s from 16 up; a check holds it there. Slower steering needs feeding in rather
  than banging from lock to lock - the robot below weaved off the walls until it steered by how
  far the bend needed - and it wants corners taken slowly, which is what a cab does anyway.
- **Walls and cars.** `_move()` steps the way `main()` walks, with `can_stand()`: into a wall at
  an angle it slides along it, and only if the wall took more than `0.45` of the step is that a
  bump - the first version called every graze one, and the robot driver was bumping three times
  a fare. Head on, under `CAB_DENT` is a bump and over it a crash. The traffic does not see you:
  within `CAB_CAR` of a car in `near_cars()` you have hit it - unless you are stopped, since the
  cars would drive through a cab at the kerb every two seconds. Note that the traffic is not
  drawn within `CAR_CLEAR`, so the car vanishes as you hit it.
- **The fares** (`_fares()`): dispatch (`_dispatch()`) finds somebody `CAB_NEAR` cells off, on
  a road cell beside a building, a step out from the wall (`_kerb_spot()`), and only if the
  satnav can get you there. They wave (`WAVER`) with TAXI! flashing over them
  (`draw_cab_world()`). Stop within `CAB_PICKUP` and they get in, and `_board()` picks where
  to: the nearest of a shuffle of `CAB_KINDS`, `CAB_DEST` off, put down at the road cell
  nearest it (`_drop_cell()`), with [ HERE ] over it once you are close. The meter is
  `CAB_FLAG` and `CAB_PER` a unit driven, not as the crow flies; the tip is up to `CAB_TIP` of
  it by their `mood`, which bumps, crashes, cars and the grass (`cab_ground()` "rough": a park,
  the quad, the tarmac) take from. A quarter are in a hurry and tip double inside `eta`, a
  quarter are nervous and do not like `CAB_LIMIT`; drive them round the houses and they ask
  if you are lost. At `mood` -0.6 they get out and walk, unpaid. What they say is `CAB_SAYS`.
  **This is the first money in the city that is not the `+` cheat**: `cab.pay` goes into the
  wallet each frame. `x` stopped pulls over and you are standing there; a fare still in the back
  gets out with you, unpaid.
- **The satnav** (`cab_route()`) is A* over road cells - streets, alleys, car parks, bridges
  (`cab_ground()` "road", cached) - with its state the cell *and* the way in, so a turn can
  cost something (0.6) and there is no turning round in the road: without that the way across
  a wide junction was a staircase and "left in 10 m" came every other cell. An alley costs 2.5.
  `CAB_GREED` weights the straight line: plain A* took 110 ms on a long fare, and at 1.3 it is
  11. Off the way for a second, it looks again (`_satnav()`); `directions()` says the next turn
  from the way. `draw_satnav()` is heading up, a cell two columns by a row, the way in gold, an
  arrow on the edge when the fare is off the map. `m` puts it away.
- **The view** is `render_street()` at `eye=2.4` with `draw_driver()` over it: the roof and
  pillars, the mirror and dice, wipers in the wet, the dashboard with the speed, the meter and
  HIRED / FOR HIRE, the wheel (`draw_wheel()`, in front of the dash, turning with `steer`), and
  dispatch and the fare along the dash. On the big-window system the speed and the fare go in
  block letters and the satnav and the wheel are worked out from the window's size anyway.
  About 16 ms a frame at 120x36 and 20 to 26 at 300x90, the mirror included.

- **The handbrake and drifting** (`e`, held while it repeats, like the wheel). The cab has a
  `slip`: the way it goes, less the way it points. The nose turns with the wheel; the way it is
  going does not, and the tyres pull it round after the nose at `CAB_GRIP` (times the wet grip)
  - so in ordinary driving slip is a tenth of a radian at full lock, and nothing changed for the
  robot. With the handbrake on the grip is `CAB_HB_GRIP`, the wheel turns you `CAB_HB_YAW`
  more, the power is off and it slows at `CAB_HB_DRAG`; going sideways slows you too
  (`CAB_SLIDE_DRAG`, by the sine of the slip), and the slip stops at `CAB_SLIP_MOST`. Let go
  and the grip straightens it in a few tenths and the speed held pulls you out. `_drift()`:
  past `CAB_DRIFT` and moving is a drift - a screech, marks on the road behind the back wheels
  (`skids`, `CAB_SKIDS` of them, drawn by `draw_cab_world()` with `put_cell()`, so buildings
  hide them), and the fare's say at the end (hurried ones like it, nervous ones do not).
  `_move()` goes along `heading + slip`, so a slide into a wall is still a wall. Measured on
  open ground, full lock at 20 for 1.2 s: 0.97 rad round without, 1.63 with, slip 0.92.
- **The police** (`_police()`). The traffic's police cars are where they always were; one
  within `COP_SEES` that can see you (`cab_sight()`, nothing built between) while you are over
  `COP_LIMIT_MPH`, or just after you hit a car, or while you are known (`heat_until`), puts its
  lights on and comes after you. **It follows the road you drove**, a breadcrumb a unit with
  your speed at each (`cop["path"]`), so it can never go through a building, needs no route of
  its own and takes a corner as fast as you took it, a little more (`* 1.1 + 3`) - and on a
  straight it is held to `COP_TOP`, under your top speed, so the straights are yours and the
  corners are its. Its traffic slot is put out (`_cars_off`, which `near_cars()` skips) and the
  car is handed back through `_cars_extra`, so `draw_traffic()` and `collect_glow()` draw it and
  light the street round it with no new code - and `_traffic()` does not count it as a car hit.
  Stopped with it within `COP_CATCH` for a second (a bump is not pulling over) is a ticket:
  the officer's lines in the dash, `COP_FINE` and `COP_PER_MPH` over at your fastest in the
  chase, `COP_RAN` if it went on 20 s, taken from the wallet through `cab.fine`; then
  `COP_REST` of peace. `COP_LOSE` behind along your road, or out of its sight `COP_HIDE` and
  35 back, and you have lost it - and every police car knows the cab for `COP_HEAT`. On your
  bumper `COP_BOX` and it boxes you in. While it chases, the roof and the pillars take its
  lights and the dash says WEE-OO; `x` will not get you out. A robot getting away flat out on
  the satnav's way, chased from the start, lost it five times in twelve and was caught once;
  the robot corners worse than a person, and a person has the handbrake.
- **The mirror** (`draw_mirror()`, `mirror_size()`, from 60 by 24 up) is a second
  `render_street()` looking back, every row turned round, at half the field of view and twice
  the size (a police car twenty back was a row of it otherwise) and the horizon high so it
  looks down the road. It is about 5 ms whatever its size - the fixed cost of a frame - so it
  is redrawn `MIRROR_FPS` times a second and kept between (`cab.mirror`). That is where you see
  the police coming: the chase is behind you, and the camera cannot look back.

`cab_robot()` in the checks drives six shifts of three fares on the keys alone, following the
satnav, all delivered and paid. If you change the handling and it cannot, neither can anyone.

## Money

**One balance for the whole city.** `main()` owns a `Wallet` — `STARTING_MONEY`, a thousand
dollars — and everything that costs anything takes from it: the slot and the blackjack table
(which used to have their own chips), the exchange (`Broker.cash` is the wallet's), the claw
machine (`CLAW_COST` a go), the strength tester (`STRIKE_COST` a swing), the arcade
(`ARCADE_COST` a game), and the city's buildings, by `FEES`: a seat at the pictures and the club's
cover are paid on the way in, the bowl and the coffee when you sit down — once a visit, keyed on
the venue, so walking out and back in is another ticket. Can't pay, and `render_turned_away()` is
what you get instead: the usher, the bouncer, the cook's sign, the drone. The lifts cost
(`LIFT_FEES`: a sky deck, the roof party; the fire escapes and the lighthouse stair are free), a
taxi by the fare, and
a show from the lighthouse is `SHOW_FEE`; refused, the HUD says what it costs. The balance leads
the HUD everywhere. Nothing tops it up for nothing — the casino's old stake when you were broke
would have been money for nothing — but you can earn it driving a cab (see Driving it
yourself), and `+` in the menu is `+$1000`. Like everything else you carry, it is
for the session and nowhere else.

## Testing it

```bash
python3 tests/checks.py       # everything that needs no terminal; about 40 s
python3 tests/pty_checks.py   # ordinary play, driven through a real pty; about 2 min
```

The pty cases are 51 separate games that mostly wait — 630 seconds of it end to end — so
`pty_checks.py` plays them **six at a time** (`PTY_JOBS`, 1 for one at a time). The cases live in
`cases(run, report)` and it runs that twice: a quiet dry pass with a `run()` that only records
what it is asked for, then all of those played in a thread pool, then the real pass handed the
results in order, reporting as it goes. A case written the old way — `ok &= report(name,
*run(keys))`, or using the output straight after — works unchanged. Its keys must not depend on
another case's output, since in the dry pass every output is empty. Give a case's last steps
some slack (a second, not a third of one): six games at once are slower to draw.

Both exit 0 or 1, so `&&` them. No test framework and nothing to install — `tests/harness.py`
imports the module with its colours stubbed and the other two are plain scripts.

`checks.py` also asserts that **every name the code reads is defined somewhere** in the file.
`py_compile` does not catch a list renamed by accident, and nothing draws it until you are on
the roof it belongs to; one came within a commit of shipping that way.

**For a refactor, compare frames, not just tests.** Render a fixed set of views (streets in every
part of town at two times, a roof, the skyline, the flight, the interiors) with each colour given
its own number — the harness stub makes them all one — and the clock tower's `time.localtime()`
pinned, pickle them from the old code and the new, and compare. The cleanup that cached
`road_at()` passed every check and changed 194 cells of the street plan: the new cache had
reused the name `_road_cache`, which `_is_road()` already had for keys of another kind, so the
two overwrote each other. Only the frame comparison showed it.

**Add to them.** Nearly every bug in this thing was found by measuring rather than looking, and
almost all of them came back as a regression test: stars drawn inside buildings, a sign that
swung out into the road, a cheat that took you to where a rave sometimes happens, a pier that
quietly spanned the river. The suite is the reason those stayed fixed.

Stub the module globals `init_colors()` would have set (`PALETTES`, `NEON`, `STAR`, `CURB`, `RAIN`,
`BULB`, …) with plain integers and call `render_street(View(x, z, yaw, w, h), now)` directly — it
returns a grid of characters to print or assert on, no terminal needed. That covers geometry,
determinism (render a spot, walk far enough to evict every cache, render it again, compare), and
navigation: the autopilot walked headless (`walk_auto()` in the checks). A quick ASCII dump of
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

**High up on a big window** is the other worst case. Zoomed out to 300x90 (27,000 cells, nine
times 100x30) a roof and the plane took 50 ms a frame, the ground over half of it. From up there
every ground point is a different cell, so `draw_ground()`'s twenty-odd questions per cell were
asked per point. `ground_cell()` keeps every cell's answers (all of them a function of where,
none of when - the hollow comes back as the cell's own and the caller adds tonight's rave), and
`cabin_wall()` works out the plane's window frame once per window size instead of a hypot per
cell per frame. Both change nothing on screen - checked at 300x90 against the code before them,
character for character. Result at 300x90: the roof 50 -> 33 ms, the plane 50 -> 34 (median of
a flight). Then the see-through fix below took both to 21 ms.

**Up high, things showed through buildings** - rain, smoke, people, the far city's lights, the
ground's specks in a dark tower's front - and it had been so all along. Two causes in
`draw_walls()`: it kept only the *nearest* facade per column for `hidden()`, so anything behind a
tall building rising over a nearer low one was drawn through it; and it kept the *first hit*,
which from a roof is often off the bottom of the screen or the building you stand on - skipped -
leaving the column with no wall at all, so `hidden()` hid nothing in it and `draw_ground()`
painted over every building in it. Now every facade drawn in a column is kept, as (distance, top
row, bottom row) runs in `walls[4]` - nearest first, each further one only above the last, so
they never overlap and one answers - and `hidden()` asks all of them; and `wall_d` / `wall_top` /
`wall_base` are the nearest facade actually drawn. On the street a few cells a view changed (a
chimney or a sign that had been drawn through a building in front); from a roof or the plane a
few hundred, the far city's lights no longer showing through the dark buildings before them.
It also made the high views faster - the ground no longer painted over those columns - roof and
plane at 300x90 both 21 ms.

**From up high the city past the nearest streets was dark** - a black band under the horizon and
a black blob over the middle of the plane's window, its edge sliding along the roofs - and it had
been so before; showing things through buildings had only hidden it. Two parts:
- **Past what is drawn** (`v.reach`), the ground had nothing at all. `far_lights()` fills those
  rows with a carpet of the haze's dots and the odd warm light, thicker towards the horizon, by
  each column's bearing and the row's distance - the way the skyline over the horizon is done -
  so it holds still as you fly. Done in screen terms on purpose: at that range nothing should
  move, and anything worked out from world cells per point flickers.
- **Inside it**, at night the streets are black past the 60 units the street's own lights reach,
  and they stay that way. `draw_far_lamps()` once put a street light every 15 units along both
  kerbs of every street out to `v.reach`, and the owner took it out again: they did not like the
  lights filling up all the black space. Do not fill the dark between the buildings without
  asking.

**Buildings blinked in and out from the plane**, and from a roof. `cast()` stopped at
`v.depth` (22) walls, and up high a ray meets a wall in every cell of every block it passes over
- most of them hidden behind the nearer ones - so the 22 were used up two or three blocks off.
Further buildings were drawn only where a ray ran down a street, which changed as the plane
moved: whole buildings went and came back from one frame to the next (up to 4.4% of the
building cells in a frame of level flight). It also left the middle of the plane's window half
empty, which was most of "the black blob". Up high now (`v.eye >= 10`) `cast()` is a generator
taken to `v.high_walls` (`WALL_REACH_ROOF` 250, `WALL_REACH_PLANE` 200; 170 for both at first) with no count at all - a distance holds still where a count did
not - and a wall whose roof line falls under what is already drawn in the column is skipped
before any of the rest of the work. Past that the ground and `far_lights()`
carry on to `ROOF_REACH`. Tried and dropped: every wall to 520 (65 ms a frame), every wall to
200 (35), and all to 170 plus only the tall ones beyond (worse: looking up every block to 520 to
find the tall ones cost more than drawing them). The check
in `checks.py` flies twelve frames level and asserts the building cells never change by 2% in
one. `far_lights()` is keyed on the row's place under the horizon, not its distance: keyed on
distance it reshuffled itself whenever the plane climbed or came down. On the street nothing of
this applies: `cast(v, ..., v.depth)` as ever.

**The far city, one shape a block** (`draw_far_blocks()`, `far_block()`): up high, past
`v.high_walls` and out to `FAR_BLOCK_REACH` (2000), each city block is 2-4 buildings of
different heights with a faint edge, its district's roof and the odd lit window, so the far
distance is a skyline and not a black void. The owner asked for no void at the horizon and no
filling of the dark with dots: the fronts stay mostly dark. One flat slab a block ran together
into long ruled lines, and edges down the full height made a wall of lines; the edge goes two rows
down from the roof. The blocks are found by scanning the view's triangle over the block grid,
not by rays, and a block's height comes from the numbers `lot()` uses (`base * 1.4 * scale`,
clamped, capped) rather than from `lot()`, which would build 81 buildings per block and push the
near ones out of its cache. Each is drawn only above what its column has (`sky_top`) and added
to `walls[4]`, so the near walls stand in front and rain and the sky respect them. About 4 ms at
300x90: roof 22, plane 30 (30% of the plane's frames over 33 ms; 4% without). Reach hardly matters
to the cost. `far_lights()` fills the last rows at the horizon.

**The cars' lights, a long way off** (`draw_far_traffic()`): up high, one light a car, white
coming and red going. The highway past `ROOF_REACH`, in the same slots as `hwy_cars()` so the
stream runs on unbroken; the wide streets out to `FAR_CAR_REACH`, sparse and only on `road_at()`
cells. The owner loved these and asked for more; they did not like the far street lights, so
this has to stay moving traffic and not a carpet. Past `FAR_CAR_CLEAR` only real buildings hide
a light (one loop over `walls[4]`, stopping at `v.high_walls`): a far block's shape is one
solid mass and a real block is not, and with the shapes hiding them hardly any far car showed
(13 more lights on screen, against a couple of hundred now). A highway crossing the view far off packed its cars into one solid ruled line
of lights, so the far ones are thinned by distance, by each car's own hash (`FAR_CAR_THIN`).
About 2 ms at 300x90.

**Out on the horizon** (`draw_far_sky()`, up high only, not fog or the strange night), by compass
bearing like the stars, and only into cells above everything in the column (`tops`), so the
skyline stands black against them. **A far storm** (`far_storm()`, `far_strike()`): a slot of
`FAR_STORM_SLOT` in `FAR_STORM_ODDS` has one on one bearing, while nothing is falling overhead;
every `FAR_STRIKE_EVERY` or so a strike lights a patch of sky over the horizon, thinning upward and
to the sides, with a stutter in it and half the time a bolt. Silent, and unrelated to the storm
overhead (`storm_window()`). `\\` in the menu starts one straight ahead - `yaw`, or out of the
plane's window - for looking at. **Flights** every `FAR_PLANE_EVERY` round the compass, each
crossing for `FAR_PLANE_LIFE`: a white light, red and green taking turns, a strobe, at 3 to 10%
of `v.fy` over the horizon; one in four is coming down, brighter, and sinks behind the skyline.
Nothing at street level changes. They cost well under a millisecond.

**The two reaches are one number each, and tuned by measuring.** At 300x90, with the far blocks
and the far traffic in, turning slowly on three roofs: 200 is 26 ms a frame and never over 33;
250 is 30 and over for 15-24% of frames; 300 is 34-36 and over for 50-95%. So the roof is 250.
The plane, over a whole flight: 170 is a median of 32 with 44% of frames over 33, 200 is 35 with
53%. The owner chose to have them split, roof further out than plane.

**Proper rooftops** (`roof_over()` inside `draw_walls()`, up high only). The renderer knows only
fronts, and a roof was faked by the thin slices of the fronts behind it: stripes up close. Now, from
above a building (and not a tree), the stretch of the ray from the front it came in by to where it
leaves the cell (`cast()` hands over that `out` too) is a roof: its rows go in the column's `runs`
at distance `out` and raise the cover, so those fronts behind are never drawn. It is left dark, with
only its back edge drawn, in the roof glyph, where the next cell is open or lower - don't fill the
dark. `draw_roof_things()` then puts an air conditioner, water tank or lit stairwell hut on about
half of those nearer than `ROOF_THINGS_FAR`, world points, so they hold still. It hides a third of
the slices (2423 to 1659 a frame) and costs that back in roof work: break-even, about 1 ms on a roof
at 300x90. The test that does most is the one in the main loop: most of what a ray meets up high is
wholly under the cover, and the far edge of the roof is its highest part (`roofed`, `out`).

**How far the street goes.** `MAX_VIEW` (buildings) was 130 and `GROUND_FAR` (road) 80, and the
owner saw the street suddenly cut off in the distance. Raising the road alone did nothing they could
see - a dark road is mostly blank - so buildings go to 260 and the road to 270, for about 0.3 ms at
300x90: with `v.depth` still 4, only the rays that run down a street go any further. Past
`WALL_BARS` (130) a street-level building gets no corner bar, because there each column is a new
building and the bars made a solid wall. Far block shapes past that were tried and dropped: 3 ms,
and messy. Cars and people still stop at about 110.

**The river as a line of moonlight**, up high only. `draw_moon_river()` follows the middle of the
channel (`river_centre()`) out to `RIVER_LINE_CELLS` either way, on grid points further apart
further off so that they hold still, brightest towards the moon's bearing, with a bit of glitter;
`hidden()` puts buildings in front of it. It needs a moon: none on a new one, nor through cloud
(`v.clear`, set by `draw_sky()`). A big warm moon rising on the horizon was built with it and the
owner did not like it (2026-11-05): the moon keeps its one small shape and its path, up high too.

**Do not draw the ground at half resolution to buy more.** It was tried: every other row and
column worked out and the rest copied from a neighbour. It was faster (roof 28, plane 32), and
the owner tried it and said no - the flight looked blurry; and copying into cells nothing had
drawn in put ground texture where a building's front should have been dark, which read as fog
particles on the roofs and as see-through buildings from the plane. What is left of the frame up
there is the per-point texture hashes (`_mix()` in `draw_ground()` and the Strip's lit windows),
which are the look itself, and the walls at `depth = 22`. Ask before trading any of it.

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
