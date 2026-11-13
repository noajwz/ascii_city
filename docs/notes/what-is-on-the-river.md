# What is on the river

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
