# The river

**Water is the first cell in this city that is neither open nor solid.** `is_open()` used to answer
both "can you see through it" and "can you be here"; those two questions come apart at the water's
edge. `is_open()` is now the sight test and says yes to water — you can see clean across a river —
and `dry_at()` is the footing test that `can_stand()` is built from. Anything that means "a building
stands here" keys off `not is_open()` and so ignores water for free. Anything that means "you can
be here" has to ask `dry_at()`, or a bank cell passes its tests.

`river_centre(i)` is three sines, so the channel **meanders across the grid** and cuts blocks off
mid-street — it swings about 330 world units side to side. `river_span(i)` widens the band by the
slope of the meander, and that is not a nicety: `|j - centre|` is measured straight across, so on a
bend the band is a slanted strip and the channel would pinch to about half its width *exactly where
it turns*, which is the one place a river gets wider. Measured, bends now come out 6.7 cells across
against 6.8 on the straights.

**Crossings are one avenue in four** (`BRIDGE_ODDS`). Every avenue would be a crossing every 45
units, and a river you can step over anywhere is a boardwalk with a puddle under it. There is a test
that you can still walk from one bank to the other, because a river that cuts the city in half is a
bug however good it looks.

**Piers** reach out from the near bank and stop — at most half way over, never a fixed length. The
channel narrows to under five cells on some stretches, and a fixed seven-cell pier there quietly
spans it: you would have built a footbridge and called it a pier. The point of one is that it *ends*,
and you stand at the end with the whole city behind you — a view the street view does not otherwise
have.

The cheat menu reaches water differently from everywhere else: **not a ring search**. There is one
river, at a known place, so walking outward looking for it fails from anywhere more than a couple of
hundred cells away in j — which is most of an infinite city. `_water_spot()` goes straight to the
channel at your x and works along it.
