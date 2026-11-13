# Dawn

The city is always at night — except that one night in `DAWN_ODDS` ends. `night()` sets `dawn`
(never on the strange night: whatever that was, it is the one night the city does not wake up
from), and `dawn()` is how far into the morning it is: zero until the night's last `DAWN_LEN`
seconds, then rising to one and held there for `DAWN_HOLD` before the next night comes round as
every night does. One number drives all of it:

- **The sky pales from the horizon up** (`dawn_glow()`): an orange line where the sun is coming,
  peach above it, a pale blue climbing higher as it gets lighter, the dark at the top last —
  dithered, so it is a gradient and not stripes. The stars and the moon go with it. On the
  waterfront it is drawn before the reflection, so the morning lies on the river.
- **The city switches off.** `neon_attr()` puts each sign out when the morning passes its own
  `phase`, so they go one by one rather than all at once; window density falls to a tenth, and
  because a window is lit by the same hash against that density, the same windows go out in the
  same order every time. The far bank's windows go too — they are the skyline's own buildings,
  which the street's renderer never built, so they are thinned separately. What is left is the
  towers as black shapes against the light.

`@` in the menu goes to the next such night, five seconds before the sky starts to turn. The
cheat panel's special nights — the next night, the strange one, lanterns, fireworks, dawn — are a
**NIGHTS** group under WEATHER & SKY now; dawn's entry was the one that pushed the panel past 80x24
again, and the test caught it.
