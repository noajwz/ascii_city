# The blackout

One night in `BLACKOUT_ODDS` (on its own hash, never the strange night) **the power goes**.
`power_off(i, j, now)` is the whole of it, per city block and a function of the block and the
time like everything else: from `BO_START` the blocks go out one by one in no order over
`BO_SPREAD`, each with a last flicker; they stay out; and from `BO_BACK` of the way through the
night the power comes back as a **wave** crossing the city — the block's x along a `BO_WAVE_W`
stretch sets when, `BO_WAVE` seconds to cross it — each block flickering `BO_FLICKER` before it
holds.

It is done once, generically, rather than in every light in the city. `draw_walls()` draws a dark
building's column as it always would and then runs `unpowered()` over it: everything that is a
light — windows, neon, bulbs, a casino's chase, the arcade's wall, the club's slits — goes out,
the structure stays in `CONCRETE`, and here and there where a window was there is a **candle**.
So every venue goes dark with no venue knowing. `draw_props()` drops the `LIGHT_PROPS` of a dark
lot (signs, lanterns, marquees, the ramen bowl, the club's door), `collect_glow()` spills nothing
from one, and the searchlights, the diner's cup and the billboards are skipped for theirs. What
is left is what has no mains: car headlights, the moon, the bridges and the carnival, and **the
temple**, lit by its candles anyway, which is the brightest thing on its street that night. With
the town dark the sky over you is clearer (`draw_sky()`), so there are more stars. The HUD says
the lights are going, the power is out, the lights are coming back. `&` in the menu skips to a
few seconds before it starts.
