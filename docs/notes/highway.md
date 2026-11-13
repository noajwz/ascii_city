# The highway, and keeping cars out of the water

Traffic first went everywhere a wide street went, which was into the river: every avenue meets it
sooner or later, most with no bridge, and the cross streets wander in and out of it with the
meanders — so cars vanished at the bank and came up out of the water on the far side, and drove
over the footbridges. And there were too many, two hundred within 400 units.

So a car in town drives a **trip** of `TRIP_BLOCKS` blocks, from the middle of one crossing to the
middle of another (`_crossing()`, `_trip_of()`), and only if the whole trip is dry road with real
crossings at both ends (`_trip_ok()`, cached) — the big bridge is the one water crossing that takes
cars. A car turning on or off at a junction reads as turning; one appearing mid-block reads as a
bug. The slots stay what they were, so the no-collision guarantee is untouched; presence is decided
per (slot, trip), so the same slot is a different car, or none, on its next trip. `TRAFFIC_ODDS`
went from 3 to 7: about 45 cars within 400 units.

Most of the traffic is on **the highway** instead: one wide avenue in `HWY_EVERY` (not the El's,
not the big bridge's, and no tunnel under it) carries an elevated deck at `HWY_H` on piers down the
median — over the river, the woods, everything, so it never has to stop at the water. Four lanes,
cars every `HWY_SLOT` one in `HWY_ODDS`, at 19-27 units a second: headlights one way, tail lights
the other. The deck's edges are spaced by distance (`max(0.3, dist * 0.018)`), not a fixed step: at
1.2 units the near stretch was a dotted line the shop signs showed through. From under the deck
the cars are not drawn — they are on top of it. ctrl-a `)` in the checks' menu stands you on a cross street forty
units off, looking at it nearly square on: from beside it looking along it is a wall of beams, and
at an angle the buildings hide it. The HUD says `~ the hum of the highway ~` near one.
