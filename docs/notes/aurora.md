# The aurora

Asked for on 2026-11-16: "the very rare Aurora: green and violet curtains moving over the sea
and the skyline, very rare, with people on the beach looking up."

**When**: one night in `AURORA_ODDS` (45), on its own hash (`night()["aurora"]`). Never with
anything else in the sky (the strange night, fireworks, a drone show, the lanterns, the
blimp) and never in fog, so it is about one night in sixty. A check holds it between one in
ninety and one in thirty-five. Its night is a clear one (`clarity` at least 0.85), but the
cloud still comes and goes over it: `aurora_out()` is how much of it shows this instant, less
through cloud, none through overcast, going with the dawn. `(` on the panel goes to the next
one; the AND THE REST column has the room the NIGHTS column has not.

**Where**: over the sea. It hangs at bearing `AURORA_EAST` and reaches `AURORA_ARC` either way
round the sky, thinning. It is placed by compass bearing like the stars, so it holds still as
you turn and only its folds move. From a street you see it in the strip of sky over the roofs,
the half of the sky facing the sea. From the beach, looking out, you have the whole of it, down
to a few degrees off the water.

**How** (`aurora_curtain()`, `aurora_cell()`): at each bearing, a brightness, a foot and a
height in radians of elevation. Three folds drift along it at different speeds, and the fold's
square gives dark gaps between the curtains. The rays are whole columns lit or not, so it reads
as streaks hanging down. The foot wavers, and the whole of it waxes and wanes over minutes.
Each cell is a streak glyph (`|`, `!`, `:`, `'`), brightest and green at the foot and violet
above the middle. It only goes into cells nothing is in, under every roof's top
(`walls[3]`), so the city stands black against it and the stars stay. Under it, in the columns
that look at the sea, a few of the sea's own glyphs take its colour (a glimmer, not a
reflection). **The first try was too faint**: at a cell's chance of the brightness, the
curtains came out as speckles and read as more stars. The streaks and the higher density are
what made them curtains.

**Over the skyline** (`draw_skyline_aurora()`): `reflect()` only mirrors the rows just over
the water, the town, so the sky never reaches it; `draw_skyline_aurora_water()` puts the same
glimmer on the water after `draw_water()` as the beach has. The
elevation is measured up from a high roofline (a third of the columns are taller), not the
water: measured from the water, its foot hung behind the buildings and nothing showed. The
bearings swing across the window (`1.5 * sin`) so a screen has several folds in it and never
one dark trough.

**The colours**: four new pairs in 256 colours (48 and 29 green, 135 and 97 violet). In 8
colours there are no pairs to spare (xterm gives 64, the rest use 62), so it borrows the
fireflies' green, the grass and the purple neon.

**The people** (`near_gazers()`, `draw_gazers()`): on its night, out on the dry sand in ones,
twos and threes, a place every `AURORA_SLOT` along the beach, two in five empty. They stand and
look up, some sit on a blanket, and every now and then one points. From the sea side you see
their faces. They are out all night, cloud or not, waiting for it.

The top bar says `~ the aurora is out - look east, over the sea ~` while it is showing well,
above the drone show and the coast's own hints.

**Cost**: about 4 ms of a 25 ms frame at 300x90 on the beach looking out to sea, where the
whole sky is it, and nothing on any other night. The elevation is worked out once a row.
