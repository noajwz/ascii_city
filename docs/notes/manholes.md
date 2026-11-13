# Manholes, and the tunnels under the streets

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
