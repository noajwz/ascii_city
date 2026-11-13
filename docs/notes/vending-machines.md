# Vending machines

Asked for on 2026-11-12: "some vending machines maybe in the alleys". **One stretch of alley in
`VEND_LANES` (4) has one** (`vending_pick()`), lit lane or dark, against the plain front with the
lowest hash - never a pub's window, a venue's front or a face on a street - at whichever end of
the front the bin is not. One to a stretch for the reason the ramen counters are: a lit thing on
its own hash per front turns up in pairs. `vending_at(i, j, f)` is the cached per-face answer
`draw_props()` and `collect_glow()` ask, and only of alley faces.

`draw_vending()` is two kinds of sprite on one spot: the cabinet (`VENDING`) in the machine's own
neon colour, and three rows of cans (`VENDING_ROWS`), each row its own colour, blitted over the
top part of the same box so the rows line up. It is `VEND_H` 2.4 tall, a head over the people.
One in six stutters. It stays lit past dawn, when the signs go off, and in a blackout it is a
dark box (it is not in `LIGHT_PROPS`, which would make it vanish). Its light lies on the ground
whatever the weather, like a bare bulb's.

`p` beside one (`vending_near()`, within `VEND_REACH` - it looks at the cells next door too, a
machine stands a unit from the end of its front) **takes you up to the glass**, asked for the
same day: "when interacting with the vending machine it shows the inside of the vending machine
with snacks and drinks inside". `vendor` in `main()` is a `Vending`, `elsewhere()` counts it,
and it has a key branch of its own before the Pokemon Center's, so `z` is in that branch. `d`
in the menu stands you **down the alley** from the nearest, not across from it: the camera
cannot tilt, and from two units away you look straight over the top of the thing.

- **What is in it** is the machine's own, by its seed: ten of `VEND_SNACKS` on the top two
  shelves and ten of `VEND_DRINKS` under them, each a name, a shape (`VEND_ART`, five by three,
  the name's first letter on it), a price and a line about what it is like; a few start sold
  out. How many are left is kept for the session (`vendors` in `main()`, by seed) and nowhere
  else - no saving.
- **Buying** (`Vending.buy()`): the price comes off the wallet, the thing turns on its coil
  (`VEND_TURN`), falls (`VEND_FALL`) and lies in the tray till `VEND_TAKE`. One sale in
  `VEND_STUCK` **hangs on the coil** - paid for, not delivered - and the next one of the same
  brings both down; one in `VEND_TWO` drops two for the price of one. The mystery capsule has
  one of `VEND_CAPSULES` in it. What it says goes in the side panel, under the buttons.
- **`render_vending()`** is on the big-window system: `vend_size(k)` is the layout, the things
  on the shelves are `_blow_up()` k times over, the title and the chosen code and price are in
  `_blocks()`, the names and what it says stay words. At scale 1 the machine is 58 by 23, so it
  fits an 80x24 terminal; under that it is two lines of words. `_text()` skips spaces, so the
  labels on the shelf edges go through `plain()`, or the shelf showed through them.
