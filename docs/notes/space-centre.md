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

## Mission control

Asked for once the launch was in ("very cool"): a building near the pad to launch it from,
and a viewer "like how SpaceX livestreams always show statistics of the launch - speed, what
booster is being used", with cameras to switch between, on the pad and on the rocket.

**The building**: a coast kind of its own, `"control"`, on the sand just north of the causeway
(`LAUNCH_CTRL`: rows 7 to 3 north of it, from the second cell of sand back to the boardwalk), so
the beach between it and the water stays open. Built like the pier's hall - not open,
`lot()` builds it from `MISSION_CTRL` (glass, mullions, three or four storeys, MISSION /
CONTROL / FLIGHT / LAUNCH on its walls); `face_kind()` calls the sand and boardwalk in front of
it a street, or its walls were a dark alley's. `_draw_control()`: MISSION CONTROL on a frame on
the roof, and the door lit, in the middle of the side that faces the boardwalk
(`control_door()`). Walk in at the door (`mission_near()`, in `venue_at()` after the beach bar);
the top bar says "mission control: walk in" near it.

**Inside** (`render_mission()`): the big screen on the wall and the room under it.
- The picture is `render_street()` from one of `MISSION_CAMS` (`mission_cam_view()`), `c` or
  `1`-`4`: **PAD CAM** on a mast out past the pad's far corner, the coast and the town behind
  the rocket; **TRACKING** down the beach, turning to follow the rocket and, after 70 s, the
  booster home; **ONBOARD** on the second stage looking back at the land, the hull down the
  right of the picture and the engines' fire coming up from under it; **BOOSTER CAM** the same
  on the booster, looking at the coast as it comes in and down. The camera cannot look up or
  down, which is why the on-rocket ones look back at the land rather than down the side.
  Their height is capped at 900 units; above that the world is not drawn for it.
- Over it, the webcast: LIVE and the camera top left; the rocket (`MISSION_ROCKET`), the
  payload, and the booster and which flight of it top right (`mission_info()`: four boosters a
  site, flown in turn); each stage's speed and height in a box bottom left and right; the clock
  in the middle and under it a line of `MISSION_EVENTS` going by, the names stepping down a row
  where two would run into each other; what just happened across the top. All of it on dark
  boxes (`_panel()`): over the smoke at liftoff the clock could not be read.
- **The numbers are not the world's** (`telemetry()`, `TELEM_ONE`, `TELEM_TWO`): a launch here
  is a couple of kilometres of sky, so they are what a launch's numbers look like - 8,100 km/h
  at MECO, 27,400 to orbit - keyed to the same events, eased between them.
- The room: a desk for each of `MISSION_DESKS`, someone at it, STBY until the flight
  director's poll from T-38, then GO.
- `l`: the poll and a 40-second count when there is no launch on; in a countdown, on to T-10;
  only in the air, nothing (`launch_from_control()`). It was refused through the whole of a
  launch at first - more than half of every five minutes - so it mostly said no.
- On the big-window system: speeds and the clock in block letters (`_clock_blocks()`, with a
  "+" and a ":" the font has not got), the desks `_blow_up()`'d, `z` gives the small one.

**What it costs**, at 300x90, warm: 13 to 27 ms a frame, the pad camera dearest.
ctrl-a `5` for the checks: the boardwalk a few steps from the door.
