# The coast

Asked for on 2026-11-12: a coastline one way only - "the other 3 directions remain being
endless" - with a beach, beach bars, a giant pier, and the river running out to the ocean, and
"easily revertable in case I don't like it". **East of the start the city ends at the sea.**

**One switch: `COAST`.** `False`, and none of it exists - every function answers as it did
before, and the checks prove it two ways: the whole of `checks.py` above its coast section runs
with it off, and a frame comparison against the commit before (99 views, 22 of them where the
coast now is) came out identical. `~` on the cheat panel is the same switch while playing
(`toggle_coast()`, which also `coast_reset()`s every cache - most of them depend on it). So:
`~`, or `COAST = False`, or `git revert` of the one commit.

**West of `COAST_LAND` nothing changes with it on** - 16,000 cells compared in the checks. The
few things that do differ far off are all "you can see to the horizon": from a roof or the
plane the far block shapes and the carpet of far lights stop at the shore.

**Where, and why there.** `COAST_I = 368` cells, 1840 units east. The owner's example was
500-1000, and that is where the first plan put it - on top of the nearest big bridge, with
its bay, headland, lighthouse and pleasure pier (its avenue is at cell 180), and through the
nearest woods, factories and suburbs. At 368 everything in the first map tile stays but the
university (another is 300 units west of the start). It is one number; moving it nearer works
(everything east is dropped by rule), it just costs those.

**The shape** (`coast_kind(i, j)`, cached, `None` west of `COAST_LAND` on one compare):
`coastline(j)` is the waterline's column in row j, three sines, under half a cell a row. From
it inland: `"sea"`; `"surf"`, the cell the waterline is in, which you can wade into;
`BEACH_DEEP` cells of `"sand"`; `"walk"`, the boardwalk; two cells of `"road"`, the road along
the front, which every cross street runs into. Where the river comes through, `"mouth"` is its
water across the beach and `"bridge"` the road and the boards carried over it; the river
opens out over its last `MOUTH_REACH` cells (`river_span()`). `"pier"` and `"hall"` are below.
`is_open()`, `road_at()`, `water_at()`, `deck_at()`, `district()`, `ground_cell()` and
`cab_ground()` each ask it first.

**Placed things do not stand in the sea, and are not cut off at it: one that would reach the
coast is not there.** `woods_home()` and `zone_home()` say such a thing's home is at
`DROWNED`, a long way west, so every question about it comes back "not here" with no caller
changed (38 of them use `zone_home()`); `flight_plan()` skips them. `grand_avenue()` gives no
big bridge whose bay would reach, `carnival_col()` no fair (`DROWNED` again: the two menu
searches skip it), `landmark_of()` no tower - and the tile gets no other, so nothing moves -
`hwy_span()` / `el_span()` no viaduct, `tunnel_run()`, `station_of_block()`,
`car_park_at()`, `yokocho_at()` nothing on coast cells. `near_river()` is false past
`COAST_LAND`, which stops the promenade and its kin; `river_at()` is false past the waterline,
and `past_mouth()` is where the things that go down the river stop: the buoys 14 cells out,
the rowing boats 18, the lanterns 40, the line of moonlight at the mouth.

**The sea and the sand are drawn by `shore_x(z)`, the waterline as a curve, not by the
cell** (`coast_ground()`, a branch at the top of the ground pass). The water's edge runs up the
sand and back (`v.shore`, per z, per frame): foam at the edge, wet sand where it has been -
which takes the glow map, so a fire lies on it - dry sand above. Out from it, waves: crests
in lines along the shore, coming in, each numbered so its gaps come in with it; white inside
18 units, grey to 70, a dash to 160, nothing past that but glints. The moon's light lies down
it in the moon's column (`v.moon_sx`, set by `draw_sky()`), and at dawn the sun comes up out
of it due east - two rows of it, deliberately small: a big rising moon was turned down once.
`draw_sky()` leaves the haze of far roofs off any column looking out to sea, and
`sea_row()` tells `far_lights()` which columns of a far row are water. `draw_river_mist()`
does not write over what stands on the sand when the sea is in the frame.

**The camera is low, and that decides what you see.** Eye height is 3.2: from the boardwalk,
25 units of sand away, the sea is five rows under the horizon on a 44-row window. That is
right, and it is why you can wade: from the surf it is the whole lower half.

**Along the front.** The row of buildings that faces the sea is `SEAFRONT_ROW` (`district()`
gives it for the first `HOTEL_DEEP` cells behind the road, parks excepted): hotels of four to
ten storeys, balconies, every one with a name from `SEA_WORDS` in neon (`make_face()` takes a
district's own `words`). `draw_seafront()`: a lamp every third cell of boardwalk, a string of
coloured bulbs sagging from lamp to lamp, a palm on the road's side lit from under, benches,
someone at the edge; rails and lamps on the bridge over the mouth; from up high only the lamps,
out to 420 - the line the coast makes from the plane. `near_strollers()` walks people along it
both ways, by the menu's crowd setting. `draw_mouth_lights()`: a red light and a green one
either side of the river's mouth. `draw_ships()`: a ship's lights on the horizon, one place in
three along the coast, red or green by which side it shows you.

**On the sand** (`beach_block(k)`: stretches of `BEACH_BLOCK` rows, a third of them bare, and
bare wherever the river or the pier cuts in): a **bar** under a thatched roof, a **fire** with
people round it, rows of **parasols** shut for the night, a **lifeguard's tower**. The bar is
three sprites on one spot, roof, body and bulbs, like the vending machine.

**The beach bar is a venue** (`beach_bar_near()`, first thing in `venue_at()`): walk up to the
counter and `render_tiki()` is the view from a stool - the thatch, the bulbs, the sea coming in
beyond the counter, whoever is behind it shaking, the list (`TIKI_DRINKS`, a number orders),
your glass. `tiki` in `main()` is the tab; after `TIKI_LIMIT` it is water. On the big-window
system: everything is laid out from the window's size, the drawings `_blow_up()`'d (`stamp()`
clears behind them, or the waves showed through the barman), the name in `_blocks()`; `z` works.
**`BAR_NAMES` and `SEAFRONT_DEEP` were both already taken** - the rooftop bars' names, and the
depth of the low town behind the carnival's pier. The first put LOOK DOWN over a beach bar; the
second was caught by the carnival's own check. Hence `TIKI_NAMES` and `HOTEL_DEEP`.

**The pier** (`sea_pier(j)`, one every `PIER_GAP` rows, never across the mouth): `PIER_BROAD`
cells wide, over the sand and `PIER_OUT` cells out to sea, with a head `PIER_HEAD` wider at
the end. It was 60 cells out at first, and from its foot the wheel was two rows tall; the
wheel has to be seen from the beach. `draw_sea_pier()`: lamps and bulbs down both rails and
round the head, OCEAN PIER in lights over the way on, two stalls, people fishing; from far
along the coast the lamps and the wheel's ring alone. On the head's north half **the hall**
(`"hall"`, the one coast kind that is not open): `lot()` builds it as `PIER_HALL`, so it has
lit windows and ARCADE, DANCE, BINGO in neon with nothing new (`face_kind()` calls the pier's
boards a street, or its walls were a dark alley's). On the south half **the wheel**
(`draw_sea_wheel()`, `SEA_WHEEL_R` 18, nearly twice the carnival's), facing the shore, so
from the sand it is the whole circle over the water with the pier's lights lying under it.
**It is timber, brown** (`WOOD`, `WOOD_LIT`: xterm 94, the boards dimmed (`A_DIM`) and the
joints and rails at full strength; plain yellow on eight colours, which is the brown it was on
the old terminals). It was 94 and 130 at first and asked to be "slightly darker": the darker
cube colours are maroon (52) or olive (58), not brown, so it is the same brown, dimmed. A
terminal that cannot dim shows the boards as plain 94 - asked for on 2026-11-13, to stand out from the
sea: grey boards over grey water read as more water. The deck is boards edge to edge (`=` and
`-` in `WOOD`, the joints in `WOOD_LIT`), the rails are wood, and under both edges **piles** go
down into the water (`|` below the deck, at `y` under zero): from the sand along the coast,
where the deck itself is edge on, the row of piles is what marks the pier out.

**A ride on the wheel** (`p` at its foot, `SEA_WHEEL_FEE`; `ride` in `main()`, counted by
`elsewhere()`): `render_wheel_ride()` is `render_street()` from your cabin (`wheel_seat()`) -
once round in `SEA_WHEEL_RIDE` seconds, up to 38 units - with a cabin's frame over it; `a`/`d`
look round. It hands its `View` back, for the double-width glyphs' bookkeeping.

**Which way you face is on the top bar** (`compass_word()`, `HEADINGS`): "facing east" in the
street, on the roofs, at the rooftop bar and the loft, and in the cab - eighths of a turn, north
being +z and east +x, as the cockpit's compass has it. Asked for with the brown pier. The rave's
hint has its own short table, `COMPASS` - the name was taken, and reusing it broke the hint.

**Getting there.** The taxi: "the beach" (the boardwalk by a bar, `_beach_spot()`) and "the
pier" (its foot, back on the road so the name reads). ctrl-a `1`, `2`, `3` for the checks: the
beach, the pier, the wheel's foot. **A ctrl-a key must not be one the panel takes as a
command**: the panel's own keys are matched before the jump list, so the first tries (`s`,
`w`, `u`) cycled the sky and the weather - and the karaoke bar's `a` had been cycling the crowd
all along, its pty case passing without ever going there (`a` and `~` now stand aside for
ctrl-a, as `m` did). From the coast `find_place()` looks twice as far (`cheat_rings()`): half
of every ring is sea, and from the beach the nearest diner was past the limit.

**What it costs**, at 300x90: on the sand looking out 25 ms, the boardwalk 20, the pier 16 to
18, the wheel ride 25, the plane along the coast 20; the start is what it was.
