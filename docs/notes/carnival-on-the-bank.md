# The carnival on the bank

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
