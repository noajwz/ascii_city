# Rain and lightning

`rain_intensity()` is three slow sines that never line up, so the weather swells to a downpour,
eases and occasionally stops; the HUD says which. Everything else scales off that one number —
drop count, the `~` standing on the road, how far neon spills, whether stars are out at all.

**A storm is a weather in its own right**, not something that happens to a downpour, and it is by
some distance the rarest of them: measured over a thousand simulated minutes it is about 4% of the
time against dry's 16%, the next rarest. `storm_window()` puts them on a slot the way strikes used
to be — one slot in six, a slot being three and a half minutes — so one rolls through roughly every
twenty minutes and lasts about a minute. A storm can outlast its own slot, so the slot before this
one has to be asked as well.

While one is overhead it is **violent**. It brings its own rain regardless of where the sines
happen to be, ramping in and off over seven seconds at the edges, and `lightning()` gives every
strike slot a strike — a slot being under three seconds — so one lands every 2.7s and the sky is lit
about 60% of the time. Each is scaled by a per-strike `power`, which is the difference between
weather and a metronome: 9% of them are faint things away over the next district, 23% right
overhead. Outside a storm there is no lightning at all, and there is a test that says so — a
downpour on its own is now just rain.

A flash is the only thing in the program that reaches across every pass at once, through `v.flash`:
the sky fills pale, every corner and roof line goes white, the rain lights up, and `wall_colour()`
promotes alley faces from the `dark` palette to `far`, which for half a second shows you what is
down there.

It took two goes to get this right, and both problems were only findable by measuring.

**How much** it lights. Lighting only the sky leaves every facade exactly the dark shape it already
was, so in a street — where there is barely any sky in frame — a strike lit 7% of the screen and
read as *the rain went white*. `draw_flash()` fixes it by filling the blank parts of every wall, so
the buildings become lit surfaces for the tenth of a second they are lit for, with their windows and
neon still showing through. That takes a strike from 7% of the street to about 52%, and the skyline
to 42%. Density matters: fill the walls as hard as the sky and the silhouette disappears into a
whiteout, so the walls go to roughly half what the sky does.

**How long** it lights, which is the half that was still wrong afterwards. `_strike_flash()` was
three sub-flashes with nothing in between, and driving the real program through a pty and counting
bytes per frame showed exactly what that means: three isolated repaints at 0.00s, 0.10s and 0.26s
and then a dead screen. At thirty frames a second that is a blink, and one you can sit through
without noticing the city lit up at all. The flicker now rides on a glow that does not go out until
the strike is over, with a tail decaying across about a second — 19 repainted frames over 1.1s
instead of 3 over 0.3s. The tail is most of what you actually register.

Both of those were reported as "lightning doesn't work", twice, and neither was visible from
reading the code or from a single rendered frame. Counting output per frame through a pty is the
tool for anything whose defect is *when* it happens rather than *what* it draws.

**Snow is the rarest weather of all** — about 2% of the time against a storm's 4.5%, a fall every
two hours or so, two to five minutes long (`snow_window()`, on its own slots, and a storm always
wins). While it falls it is the whole sky's weather: `rain_intensity()` is zero, so the streets are
dry and nobody has an umbrella up, the cloud takes the stars, and the mist off the river goes. It
**settles** — `snow_cover()` builds over `SNOW_SETTLE` seconds of falling and melts over
`SNOW_MELT` after it stops, so the city stays white a while once the sky has cleared. Lying snow
covers the ground ahead of anything else the ground would draw, bare road included, except the kerb
line, which is how you still tell street from pavement; every roofline goes white through
`roof_colour()`, the canopy whitens from the top down, and on the waterfront the top of every
building on the far bank. Flakes are on the rain's world-locked lattice but slow and each on its
own sway. `w` in the menu has a `snow` step, which also lays a full cover at once.

Drops sit on a **world-locked lattice** so they hold still relative to the city while you walk and
turn through them, and each is drawn as the segment it fell through since the last frame, which is
what gives the streak its slant — the wind's and the perspective's — without faking anything in
screen space. Reflections are exact rather than approximated: a mirror plane at `y = 0` puts the
image of a thing at height `h` in the same column, which is all `View.reflect_row()` is.
