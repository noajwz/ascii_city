# The bridges

The crossings were building sites for a while — hoardings, a hazard board, a crane — as a
placeholder, and were asked to be made cosier. `draw_bridge()` is a footbridge: a railing down
each side, lamp posts along it with a warm bulb on each, and a festoon of small amber lights slung
from lamp to lamp, sagging the way the yokocho lanterns do. The lamps are staggered between the
two sides so they are not in step, and nothing on it blinks — the buoys and the club have that,
and a bridge is where the city is quiet.

The lamps are what you see from the bank, and on the water under the bridge, because the
reflection now carries lights and nothing else — so the bridge and the reflection were designed
as one thing. Three tiers, railing / festoon / lamps, at heights that stay separate rows from
thirty units away; with the lamps at the festoon's height the two merged into one row of `o`.

**It has to stand out from the water**, and for a while it did not — a thin grey rail at knee
height over a deck of scattered dots, reported as "it blends in with the water". `draw_bridge_body()`
gives every footbridge a solid stone parapet with a pale `ROOF`-coloured coping on top, a kerbed
and paved deck, and under it the arches and piers going down into the river. All of it is
structure glyphs in structure colours, so the reflection — which carries only lights — leaves it
alone, and from the bank it is a hard band across the water with the lamplight lying under it. The
big bridge gets the same parapet with a girder underneath instead of arches, since its deck hangs
from the cables.

Two things were added on top, and both are about the bridge being *somewhere* rather than a
fixture. **Somebody is leaning on the rail** on one bridge in three (`leaner_at()`, hashed on the
crossing), looking down the river with a cigarette that flares on a slow count — the same job the
angler does for the pier. And **the four end lamps are drawn from 230 units** with a screen-space
halo round them (`draw_bridge_ends()`, `put_halo()`), against a bridge drawn from 85: walking the
bank looking for a crossing, you should see the lamps long before you can see the bridge. The halo
is in screen space because a world-space one collapses into the lamp's own cell from a hundred
units off, which is exactly the range it is for; and it paints over the far bank's walls but
never over another light, because that is what it is meant to be seen against.

The water cheats did not skip what was underfoot the way the ring search does, so `j` and `b`
returned the same pier and bridge every press. They move along the river now, and `B` went to a
bridge with someone on it (both off the panel now) — the leaner is one in three, and a thing you cannot reach cannot be
checked.

**No key may differ from another only by case unless it is a variant of it.** The woods went in as
`W` next to `w` weather, and the rave as `R` next to `r` residential, and the report back was "W is
already weather" and "the rave cheat teleports me to just city" — lowercase pressed, weather cycled,
a housing district reached. Both were working. `b`/`B` (a bridge, the same bridge with someone on
it) was the one pair that earned it, and both have since left the panel; there are no pairs now
(`a` people and `A` a strange night was one that slipped in — the strange night is `u` now).

**The rig in the trees knew.** Whoever carried a sound system into the woods on the one night in
forty that the sky has something in it was not guessing: `rave_window()` is on from dusk to dawn on
that night, and `rave_light()` gives up 168 BPM and takes the sky's beat through `city_sync()`, the
way the club does. That was the theory kept alive through the rewrite, and it is now the rule.
