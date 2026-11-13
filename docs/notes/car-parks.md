# Car parks

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
