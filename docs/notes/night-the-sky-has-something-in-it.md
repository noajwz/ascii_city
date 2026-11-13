# The night the sky has something in it

One night in forty — about seven hours of walking between them — the sky is not stars. `night()`
sets `alien`, which forces clarity to 1.0 and the milky way up (whatever the weather was going to
do up there, the sky is lit by what is in it), and then `alien_light()` runs the whole field on the
same four-to-the-floor the club does: the stars pulse through the neon palette, the kick takes all
of them white at once, `draw_sky_beams()` swings beams across from somewhere past the horizon, and
three craft drift over with their rim lights going round.

Two things worth keeping:

- **A beam washes over the stars, it does not thread between them.** The first version only drew
  into blank cells, which works on an ordinary night and vanishes completely on this one, because
  there are no blank cells left. It still stops dead at the rooftops, which is what keeps it a thing
  happening *over* the city rather than a filter laid on the picture.
- **The density has to go up, not just the colour.** Recolouring a clear night's starfield left the
  sky filling 11% of itself either way — the same picture in different paint. It goes to about a
  quarter, which is what makes it read from a street, where you only ever see a strip of sky between
  the rooftops.

`SkyBox` exists so the sky effects can draw into the waterfront view too: they want a width and a
horizon, and the street's `View` carries a camera the skyline has no use for.

**The city gives up its own rhythms and takes the sky's.** `city_sync()` returns `flash`, `on` or
`off` on that night and `None` on every other, and `neon_attr()`, `club_light()`, the bare bulbs and
the lantern strings all consult it — so every sign in view breathes together, the kick takes the
whole city white at once, and whoever is playing the club gives up 134 BPM and mixes into it. Even
the dead tubes are cured for the night. Signs keep **their own colours** through it: one beat, not
one colour, or the city flattens into a single wash and stops being a city.

Everyone on the pavement stops as well — the smokers and the queue outside the club both switch to
`LOOK_UP` and stand still. It is the stillness that reads more than the figure: a street where
nobody is doing anything is a street where everyone is looking at the same thing.

Two things happen once a night rather than continuously. `draw_mother()` brings the big one over,
thirty-four cells wide and two minutes end to end, placed **by bearing** like everything else hung in
the sky — something that size sliding about as you turn your head would give the whole thing away.
Its blanks are hull and blot out the stars behind them; letting the sky through a shape this big
makes it read as a pattern laid over the stars rather than as something in the way of them.
`draw_landing_beam()` stops one of the sweeping beams dead over a rooftop and holds it there for
eight seconds, fading up and out so it arrives rather than switching on. No explanation offered.

`u` in the cheat menu goes straight to one, and the HUD says `~ something over the city ~`. Both
matter — one night in forty is unreachable by waiting, and from a street you might not look up.
