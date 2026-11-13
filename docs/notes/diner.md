# The diner, and the billboards

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
