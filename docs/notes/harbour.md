# The harbour, and the cruise ship

Asked for on 2026-11-13, from a list of coast ideas: "a harbor where the cruiseship docks and
where you can get on", and where you get on the speedboat to drive it (see the speedboat, below,
when it is in).

**Where**: one every `HARBOUR_GAP` (720) rows, the first at `HARBOUR_ROW0` (610) - so with the
piers every 360 rows from 70 and the space centres every 720 from 250 the three never crowd:
180 rows from a pier either side, 360 from a space centre. The one nearest the start is at row
-110, 550 units south of it. None within 60 rows of the river's mouth. `harbour_site(j)`,
`_harbour_at(r0)`: (first row, last column).

**The quay** (`_quay_kind()`, coast kind `"quay"`, asked after the pier and the launch pad in
`coast_kind()`): `QUAY_BROAD` cells across, from the first cell of sand `QUAY_OUT` cells past
the waterline. A deck (`deck_at()`), so you walk it and the cab drives it. `coast_ground()`:
concrete, a kerb along both edges, a yellow line in from the edge the ship lies against.
`draw_harbour()`: lamps down both sides, bollards along the ship's edge, HARBOUR in lights over
the way on, a green light on the end, the gangway up to her side.

**The ship** (`draw_liner()`, the MIDNIGHT STAR): `LINER_L` long, moored along the quay's north
side bow out (`liner_berth()`). She is drawn, not built - points, lines and filled faces, not
cells - so that she can sail. **Each face is filled on the screen** (`_face()`: a convex polygon,
scanline-filled with `put_cell()` at its mean distance) or the sea and the far coast showed
through her between the windows; and each face is cut into 12-unit pieces along her, so the
part alongside you still draws when the rest of her runs out past the edge of sight - a face
with a corner behind the camera is skipped. Only the side, the end and the decks that face you
are drawn. Hull plating `=` in the darkest grey, portholes; the decks `:` above, cabins lit
warm deck over deck, a balcony rail under each (drawn first, or the rails hid the windows); the
red funnel with gold bands; dressing lights bow to mast to stern, chasing; her name at the bow
in neon, laid out along her whichever way reads left to right from where you are (it came out
INGTSAR at first). From further than 700 only her lights; to `LINER_SEEN`.

**Aboard** (`p` at the gangway, `LINER_FEE`; `cruise` in `main()`, counted by `elsewhere()`):
`liner_sail()` lays out her way (`liner_route()`: a Catmull-Rom line through waypoints set
off the coast's own line, `shore_x()`, a point every 20 units) - out past the quay, south,
past the ocean pier's head and its wheel, past the space centre half a gap down **nearly 500
units off the pad**, round, and back up further out - and she follows it at `LINER_SPEED`,
easing off and in over `LINER_EASE`. About three minutes and a quarter. `render_cruise()` is
`render_street()` from her top deck's rail on the side towards the land, `a`/`d` to look round,
her rail along the bottom and her lights along the top; she is not drawn round you
(`_aboard`). `x`: a tender takes you back, and she is alongside again.

**The rocket, as she passes**: `liner_sail()` moves the space centre's clock
(`_launch_shift`) so the rocket is off the pad ten seconds before she is abeam. That was found
by tracing the pad and the rocket through the view: at 150 units off, or lifting off as she
came abeam, it was over the top of the picture - the camera cannot look up - while ten seconds
early and 500 off it is ahead and to the side, the ignition, the cloud, the climb and its fire
on the water, in sight until she turns for home. The top bar has the launch's commentary while
it is going (`launch_hint()` at her rail).

**Getting there**: the taxi, "the harbour" (`_harbour_spot()`: the road at the quay's foot).
ctrl-a `6` the harbour, `7` the gangway, for the checks.

**What it costs**, at 300x90: on the beach with her in view 26 ms; from her rail 29 to 36 -
it is a view from 26 units up, roof-like, all coast; a ride, nothing to steer, so left as is.
