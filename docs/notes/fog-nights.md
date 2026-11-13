# Fog nights

One night in `FOG_ODDS` (on its own hash, never the strange night) the fog comes in.
`draw_fog()` runs over the finished street picture, before the rain, and it works because **every
cell already has a distance**: the wall in its column (`walls`), the ground at its row, the sky
past everything — and anything drawn above the nearest roof is something further off. Past
`fog_reach()`'s near distance a cell is taken by the fog with a chance that rises to certainty at
the far one: structure goes to nothing, or to a grain of `.` in `HAZE`, and goes grey on the way
out; **a light goes soft instead** — `o`, then `*`, then `.` — and spills a blur in its own colour
round itself, wider the further off it is (`FOG_LIGHTS` is what counts as a light: letters and
the bright symbols), which is what neon does in fog. The sky shows no stars (`draw_sky()`), just
the grain drifting. The near and far distances breathe on two slow sines (`FOG_ROLL`) as banks
roll in and out. The lighthouse beam becomes a **shaft**: a band of lit fog either side of the
line, widening as it goes. From a roof you are above it. About 1 ms a frame at 100x30, 6 at
240x70. `#` in the menu skips to the next one.

Its hash salt is 7 and not 4 for a reason worth keeping: on 4, night 0 was a fog night, and night
0 is the one the whole test suite runs on — the billboards, the El, the bridges and the district
histograms all went into the fog and failed at once. The fog is its own grey, `FOG` and `FOG_DIM` (248
and 243, or white on eight colours): in `HAZE`, which is nearly black, it read as specks on the
night rather than as fog, and it is thicker the deeper in.
