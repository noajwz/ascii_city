# The space centre

Asked for on 2026-11-13: "At the beach I would like to build a space agency with a rocket
launchpad that goes onto the sea." **One every `LAUNCH_GAP` (720) rows of coast**, the first at
`LAUNCH_ROW0` (250) - 900 units north of the ocean pier, halfway to the next, so from the pier's
head the rocket and its tower stand over the water up the coast. None within 60 rows of the
river's mouth. It is the coast's, so `COAST` off (or `~`) and there is none.

**What is there.** `launch_site(j)` / `_launch_at(r0)` give (first row, the pad's first column,
its last), like `sea_pier()`. `_launch_kind()` makes two coast kinds, asked for after the pier
in `coast_kind()`: `"jetty"`, the causeway, `LAUNCH_BROAD` cells across, from the first cell of
sand out over the water; and `"pad"`, `LAUNCH_PAD` square at its end, `LAUNCH_OUT` cells past
the waterline. Both are water underneath (`water_at()`), so you see across them; only the
causeway is a deck (`deck_at()`), so **you can walk - and drive - out to the fence at the end
of it and no further**: the pad is not somewhere a foot goes, and the fence is drawn where it
stops you. `coast_ground()` draws them in concrete: a yellow line down the causeway, and on
the pad a painted ring and cross round where the rocket stands, the mark the booster lands on.
Along the front behind it, `LAUNCH_HQ` rows either way, the hotel row is `SPACE_HQ` (`district()`):
cold glass, mullions, SPACE / MISSION / CONTROL / COSMOS and the rest in cyan and violet neon.

**`draw_launch_site()`**, from `render_street()` for every site within `LAUNCH_SEEN` (6000),
which is mostly an early return: the pad's own things are drawn inside `LAUNCH_NEAR` (1500,
the lattice inside 700), and further than that only while a rocket is in the air. Lamps and a
rail down both sides of the causeway, SPACE AGENCY in lights over the way on (`LAUNCH_NAME`),
the fence with DANGER on it (read from close up only - from the beach it ran together), four
floodlight masts with faint beams on the rocket, the service tower (`_draw_gantry()`: a lattice
of `_seg()` lines, a red light on its mast, the arm to the second stage that swings back
at T-45), and the rocket (`draw_rocket_up()`, white, a dark band between the stages, ASCII down
the side in gold).

**A launch every `LAUNCH_EVERY` (300) seconds**, each pad on its own clock (`launch_t()`: -130
to 170). From -60 the countdown, venting from -40; at 0 ignition - fire out sideways along the
pad and `_launch_cloud()` rolling out across it and the sea, orange from inside for the first
seconds, grey after, drifting, gone in a couple of minutes. Held two seconds, then up.

**The camera cannot look up, and that shaped the flight.** The screen shows about 25 degrees
of sky over the horizon, and from the boardwalk a straight climb was off the top in ten
seconds. `ROCKET_PATH` (worked out once, a tenth of a second a step) goes straight up for 20
units and then turns out over the sea hard enough that from the boardwalk it peaks at about
21 degrees and sinks towards the horizon after, as a launch does seen from down the coast. It
is quick to lean - 70 degrees by T+20 - and that was the price; tried slower turns were 26 to
34 degrees, off the top for half a minute. `_launch_trail()` leaves smoke along the way it
went, sampled at fixed times on the path so it holds still as the rocket goes on. The flame
(`_plume()`) is drawn in screen cells, so far off it comes down to one bright point and never
to nothing, and while it is low its light lies on the sea in its column (`_flame_on_water()`).

MECO at 45, separation at 48; the second stage goes on along the same path with a small flame.
**The booster comes back** (`booster_at()`): a curve out and round and back in *low* over the
sea - low on purpose, so its burns are in sight from the beach - to 110 units over the pad at
`LAUNCH_HOME`, then straight down, slowing to nothing, onto the ring at `LAUNCH_DOWN` (110),
legs out for the last four seconds. Its burns (`LAUNCH_BURNS`) light; between them it is dark,
as it is. A small cloud when it lands. It stands there, booster only, till the next rocket is on
the pad at -130.

**The top bar** (`launch_hint()`, inside `LAUNCH_HEARD`, 900): between launches "next launch in
m:ss" near the pad; the countdown T-60 to T-1; then the commentary - `LAUNCH_CALLS`, liftoff,
max q, MECO, separation, the burns, touchdown, the sonic boom. It was 2500 at first and took
the bar from every other hint in town for more than half of every five minutes.

**Getting there**: the taxi, "the launch pad" (`_launch_spot()`: the road at the causeway's foot,
looking out along it, the sign over you). `^` on the panel - it looks like a rocket - launches
the nearest in fifteen seconds (`launch_now()`, which moves every pad's clock: `_launch_shift`).
ctrl-a `4` for the checks. `^` is also a ctrl-a key (the sky deck), so it stands aside for it.

**Other launches show.** Two sites are 3600 units apart and on different clocks; from the beach
another one's rocket going up far down the coast is in the sky now and then. That is right.

**What it costs**, at 300x90: 1 to 2 ms on the beach and at the causeway's foot (20 to 24 ms a
frame there), up to 5 ms at the fence, where the tower's lattice is the whole screen (26).
