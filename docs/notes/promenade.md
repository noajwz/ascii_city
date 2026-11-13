# The promenade, and what is on the water

**The bank is a walk now, most of the way.** `prom_at()` leaves the two cells nearest the water
open along two stretches in three of the near bank — a railing that follows the bank cell by cell
(a straight one walks into the river and out again on the meander), a lamp every three cells,
benches, someone leaning at the rail. It exists because everything else on the river — the piers,
the carnival, the big bridge — could only be seen from the deck or from across the water: the
buildings ran straight down to the bank. The promenade is where the river gets looked at from,
and ctrl-a `t` in the checks' menu puts you on it. On the docks' stretch it is a quay: the cranes stand on lots that touch
the water *or the promenade* (`quay_at()`), or the promenade would have taken every quayside.

**Small things on the water, not a barge.** The barge went because a big hull at twenty units is
porridge. A **ferry** crosses the bay beside the big bridge and back every `FERRY_PERIOD` seconds,
easing off and on and waiting at each end, lit windows and a light on top, a wake while it moves;
**rowing boats** with a lantern in them drift down the channel with the current, one every
`ROWBOAT_GAP` cells. Both are functions of time and nothing is stored, the way the barge was.

**The lantern night.** One night in `LANTERN_ODDS` (never the alien night), lanterns by the
hundred go down the river with the current — a lattice along the channel, four to six a cell,
each on its own bob, the whole field sliding downstream, in three warm colours. Two things about
them: they are drawn **after** `reflect_river()`, or the far bank's windows lying on the water are
painted over them; and the ones beyond ~36 units land on rows the ground pass never textures
(`GROUND_FAR`), which is fine — they read as a line of lights receding along the river, which is
what they are. `z` in the menu skips to the next such night.
