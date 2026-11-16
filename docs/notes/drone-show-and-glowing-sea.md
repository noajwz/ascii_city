# The drone show over the sea, and glowing-sea nights

Both asked for on 2026-11-16, for the beach: "A drone light show over the sea. Hundreds of
coloured points would rise off the water and form shapes in the sky: a rocket, a heart, the
big wheel, a word. Drone show is rare." And: "Glowing-sea nights ... the breaking waves would
light up blue and the foam would sparkle where you wade. It only changes the surf."

## The drone show

**When**: one night in `DRONE_ODDS` (13; about one in eighteen once the exclusions are taken
off), on its own hash (`night()["drones"]`) - never the strange night (the sky is busy), fog
(nothing would show) or the fireworks' night (one show a night). All night, a show every
`DRONE_CYCLE` (130 s): `DRONE_RISE` up off the water, four shapes each held `DRONE_HOLD` with
`DRONE_MORPH` between, `DRONE_FALL` back down onto the sea, then dark till the next. `y` on the
panel goes to the next such night and starts a show in a few seconds (`_drone_shift`).

**Where** (`drone_sites()`): one show off every ocean pier, `DRONE_OUT` (260) off the beach and
`DRONE_UP_COAST` (230) up the coast from the pier - beside the big wheel from the beach, not
behind it. Piers are 1800 apart, so a show is never more than about 900 off along the coast;
seen to `DRONE_REACH`. The shapes stand in a plane facing the shore.

**What** (`drone_pose()`): `DRONE_N` (300) drones, each a world point (`put_point()`), so
buildings hide them and `reflect_river()` lays them on the water like the fireworks. Every
shape is a list of points in its own frame - along the coast and up - fitted to the drone count
(`_drone_fit()`), and drone `i` goes from point `i` of one shape to point `i` of the next, which
makes the swirl between them. The rocket (white body, red nose and fins, a porthole, a flame
that flickers gold and orange) climbs as it is held; the heart beats; the wheel turns, its rim
chasing in the neon colours like the pier's; the word is in `BIG_FONT`, each lit dot four drones,
the letters taking turns in colour (`DRONE_WORDS`, one a show). `o`, or `.` past 600.

**Sizes**: the camera cannot look up, so everything is held under about 115 over the water: at
260 off, from the boardwalk, that is the top of a 36-row window. At 120 columns the shapes are
small but read; at 300x90 the wheel has its spokes and the word is easily read.

**The HUD** says `~ a drone show over the sea ~` in reach - above the coast's own hint, under a
launch's commentary.

## Glowing-sea nights

**When**: one night in `GLOWSEA_ODDS` (7), its own hash (`night()["glowsea"]`), not the strange
night; fading out with the dawn. `j` on the panel goes to the next one.

**What** (`glowsea_surf()`, from `coast_ground()`; `v.glowsea`): only the surf. Inside
`GLOWSEA_REACH` (26) of the water's edge the crests coming in are cyan, brightest at the beach
with white sparkles; behind each a few specks of what it left; the foam at the edge sparkles
cyan and white; and when you are standing in the surf (`v.wading`) the water round your feet
lights up. Further out the sea is drawn as it always is - a check holds it. The glowing coves
of the dark nights (`bio_glow()`) are a different thing and unchanged.

**The surf is wholly `glowsea_surf()`** on those nights (it returns `False` outside it, for "as usual"): letting its quiet points fall through to the ordinary sea worked every one of them out twice, 6 ms a frame at 300x90 looking along the beach; 2 ms now.

**Sparkles are per screen cell**, not per world point: close up, half a unit of foam or a stretch
of crest is a block of cells, and one hash lit the whole block white - a slab of `*`. Twinkling
six times a second, they need not hold still in the world.

The HUD says `~ the surf is glowing tonight ~` on the sand, the boardwalk and in the surf.
