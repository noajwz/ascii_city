# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working in this repository.

An endless procedurally generated ASCII city, walked through in the terminal. Written for fun.
**No package, no dependencies, no config files** — it is one stdlib-only Python script
(`curses`, `math`, `random`, `unicodedata`) and nothing else — plus the library's Wikipedia reader and
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

## Notes by area

Each part of the city has its own design notes in **`docs/notes/`** - why it looks and
behaves the way it does, the gotchas, what was tried and rejected. **Read an area's note
before changing that area**, and update it (or add a note and list it here) when you build
or change something. Notes cross-reference each other by title ("see The university").

- `skyline-is-a-waterfront.md` - The skyline is a waterfront
- `street-view-is-a-grid-raycaster.md` - The street view is a grid raycaster
- `parts-of-town.md` - Parts of town
- `night-sky.md` - The night sky
- `dawn.md` - Dawn
- `fog-nights.md` - Fog nights
- `blackout.md` - The blackout
- `night-the-sky-has-something-in-it.md` - The night the sky has something in it
- `river.md` - The river
- `what-is-on-the-river.md` - What is on the river
- `promenade.md` - The promenade, and what is on the water
- `coast.md` - The coast
- `space-centre.md` - The space centre, its launch pad out on the sea, and the launches
- `fireworks-over-the-bay.md` - Fireworks over the bay
- `carnival-on-the-bank.md` - The carnival on the bank
- `big-bridge.md` - The big bridge
- `headland.md` - The headland, and the lighthouse
- `bridges.md` - The bridges
- `woods.md` - The woods
- `rave-in-the-hollow.md` - The rave in the hollow
- `factories.md` - The factories
- `suburbs.md` - The suburbs
- `strip.md` - The Strip
- `airport.md` - The airport
- `university.md` - The university
- `metro.md` - The metro
- `pokemon-center.md` - The Pokemon Center
- `arcade-big.md` - The arcade, big
- `casino-big.md` - The casino, big
- `people-walking.md` - People walking
- `elevated-line.md` - The elevated line
- `tunnels.md` - Tunnels
- `car-parks.md` - Car parks
- `traffic.md` - Traffic
- `highway.md` - The highway, and keeping cars out of the water
- `diner.md` - The diner, and the billboards
- `rain-and-lightning.md` - Rain and lightning
- `club.md` - The club
- `casino.md` - The casino, and the one door in the city that opens
- `ramen-counter.md` - The ramen counter
- `vending-machines.md` - Vending machines
- `manholes.md` - Manholes, and the tunnels under the streets
- `case-of-the-last-slice.md` - The case of the last slice
- `temple.md` - The temple, and the word of God
- `sky-deck.md` - The sky deck
- `landmark.md` - The landmark, and the party on its roof
- `bowling-alley.md` - The bowling alley
- `karaoke-bar.md` - The karaoke bar
- `minigolf-course.md` - The minigolf course
- `rooftop-bar.md` - The rooftop bar
- `up-the-fire-escapes.md` - Up the fire escapes
- `pictures.md` - The pictures
- `stock-exchange.md` - The stock exchange
- `arcade.md` - The arcade
- `inside-the-club.md` - Inside the club
- `a-yokocho-is-a-kind-of-alley.md` - A yokocho is a kind of alley, not a part of town
- `cheat-menu.md` - The cheat menu
- `taxi.md` - The taxi
- `money.md` - Money

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

**`checks.py` runs with the sea switched off** (`ac.COAST = False`, first thing) down to its
last section, "the coast", which turns it on: everything before that is about the endless city
and walks east as readily as west. A check of something near the coast goes in that section.

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
