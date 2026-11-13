# The airport

Beside every Strip, on the Strip's own hash so it is always the same distance off its side
(`ZONES["airport"]`, salt shared with the strip's): open tarmac (`is_open()` yes, `road_at()` no,
so no walkers or traffic), with a glass **terminal** down the west side, **hangars** beyond it and
a **control tower** (`airport_part()`, built by `lot()` and drawn by `draw_airport_column()`:
glass lit cold with a mullion every bay; ribbed metal with the great door lit; a shaft with the
cab at the top all window). `AIRPORT_NAME` goes up over the terminal's front. The ground pass
paints the **runway** (`runway()`, `RUNWAY_W` either side of the middle, `RUNWAY_HALF` cells each
way): edge lines, dashes down the middle, piano keys at both ends, and the taxiway's yellow line.
`draw_airport()` lights it — white down the edges, green across the end they land at and red
across the other, the approach lights out beyond it with a strobe running in towards the runway
— turns the tower's beacon, and parks four airliners nose-in at the gates with the jet bridges
out to them.

**Planes on a timetable** (`plane_states()`, a function of time on `APT_CYCLE`): one comes in
from the north down the glide slope, landing lights blazing, touches down, brakes and turns off
for the gates; half a cycle on, another lines up, rolls, rotates and climbs away south.
`draw_plane()` is world points at `PLANE_SCALE`: fuselage white with its windows lit, wings,
engines, fin and tailplane, red and green on the wingtips, the strobe and the beacon, the
landing lights at the nose and the beam they throw ahead and down. While one is on the ground
**the next is already out there**, high, coming in to join the approach — lights only past 700
units, which is all you would see of one. It came in low at first and was behind the far city's
towers the whole way; up there it is a light in the sky the whole cycle. The HUD hears them.

**Where to watch from was the work.** Side on, a hundred units off, a landing was a few
characters at the horizon, and from sixty it was off either edge of the view. So `'` in the menu
stands you at the end of the runway, off its edge, looking up the approach — where plane
spotters stand — and the next one comes in straight at you and over your head. That only works
because **the town under the approach is kept low** (`approach_cap()`, applied in `lot()`, the
way `seafront_cap()` keeps the carnival's sky clear): rising with the glide slope from inside the
fence on, a corridor either side of the centre line. Before it the city's financial district
stood forty units off the end of the runway and hid the plane until it was overhead; the cap
had to start a few rows inside the airport's edge, because the edge wanders and left one row of
towers standing. Far out you see the landing lights, which is all you would.


**A flight.** The terminal has doors in the middle of its front (`gate_cell()`, `gate_door()`,
the `gate` lot flag, drawn lit in `draw_airport_column()`); walking through them is a venue
(`gate`) that opens the gate screen (`render_gate()`: a departures board — AC 101 boarding, AC 404
NOT FOUND cancelled — and the jet at the window). Enter pays `FLIGHT_FARE`, and then it is a
window seat on the right, once round the town, about 80 s:

- **The route** (`flight_legs()`, `flight_pose(home, s)` by distance `s`, `flight_s(t)` by time
  — accelerate, cruise, brake): lined up at the north end, down the runway and away south; a
  half circle west; north past the Strip; a half circle east onto the approach; down the glide
  slope from the north onto the runway. Every turn is to the right, the side you sit on, so the
  Strip is in your window both ways past it. `FLIGHT_R` is set from the airport–Strip spacing so
  the leg north passes 150 units west of the Strip, near enough for its lights.
- **The height** is a profile, not a cruise level (`flight_profile()`, cached per airport, 0.2 s
  once): over the tallest roof within 300 units either way plus `FLIGHT_CLEAR`, never under
  `FLIGHT_LOW`, smoothed by a max then a mean so it climbs before a tower and not at it. A flat
  130 cleared everything and showed nothing: **the camera cannot tilt**, so from that high
  everything within two hundred units was under the bottom of the window, and the Strip, flown
  past, was its car park. The take-off climbs steeply and eases off at the top, and
  `approach_cap()` now keeps the town low off the **south** end of every runway too, under the
  climb-out, where at first it is only just over the roofs. The check walks the whole route and
  asserts no roof within two cells comes within 2 units of the wheels.
- **The view** is `render_street()` from the plane with the horizon raised as it climbs
  (`FLIGHT_SKY`): that is how a raycaster looks down, and it is what puts the town under you in
  the window rather than off the bottom of it. `draw_window()` draws the right wing in world
  points (so it stays put as you look round) — filled row by row from the root to the tip, the
  seat `WING_BEHIND` ahead of the root so its leading edge runs diagonally rather than straight
  up — with its green light and strobe, then the cabin wall and the window's rounded frame, and
  the seatbelt sign. The HUD has what the captain would say (`flight_stage()`), what you are over
  (`place_below()`), and the height in feet. Arrows lean you to look forward or back; `x` dozes
  off and wakes you on the approach. Landed and stopped, you come out of the terminal's doors.
  Frame time over a whole flight at 30 fps: a median of 21 ms.
- `.` in the menu stands you in front of the terminal's doors.

**Flying it yourself** (`Cockpit`, `flight["phase"] == "pilot"`). `c` at the desk, `PILOT_FARE`, or
`f` in the menu, free, straight onto the runway. It is not on rails: `step()` is thrust against drag on
the square of the speed, a climb costs speed, a bank turns you (`PILOT_TURN`), and under `PILOT_STALL`
it sinks and the nose drops. **Curses sees no key go up, so the controls are the kind that stay put**:
`s`/`w` set where the nose is held, like a trim wheel - the way a stick works, back for up, as
the owner asked - `+`/`-` the throttle, and a wing stays down only
as long as the key keeps repeating (`PILOT_GRACE`) and comes back level by itself. `b` brakes, `x` hands
it back. Touchdown is graded on sink rate (`PILOT_GRADES`), and pays; a tilted wing, too hard, off a
runway or into a building is a wreck, then you wake up at the terminal. Any airport will do
(`nearest_airport()`): you come out of the doors of the one you landed at.

`render_cockpit()` is the real city out of the windscreen. The horizon goes with the nose, which is how
a raycaster looks up and down, and `roll_picture()` tilts it with the wings by sliding columns up one
side and down the other, never further than the panel can hide. `draw_runway_lights()` is what makes it
possible to find your way back: edge lights, approach strobes and the four lights beside the touchdown
that read white over the slope and red under it, seen from 3500 units. The panel (`draw_cockpit()`) has
speed, throttle, an artificial horizon, a compass, the way to the airport, and needles for the centre
line and the slope inside 2500. About 30 ms a frame at 300x90.

**Help with the landing, asked for after the first ones were hard.** `guide()` is a real approach,
a step at a time in `ck.leg`: out to an entry point off to the side unless you are already ahead of
the runway, then to the fix `PILOT_FIX` out on the centre line, where the slope starts at cruise
height, then down the slope along the line, and round again if you are blown off it. It keeps one
airport (`goal()`, `PILOT_KEEP`): **airports are only a tile apart**, so going out to one's entry
point brings you nearer the next, and switching to whichever was nearest turned you round half way,
for ever; it took three tries and a trace to see. Everything reads `guide()`: **the tower** (`r`,
`radio_key()`, `_radio_tick()`: take-off clearance, headings and heights, the localiser, cleared
to land, high or low or off the line, `PILOT_RADIO_LAG` before it answers, the last three lines up
in the windscreen), **the flight director** (`commands()`, the `(+)` on the artificial horizon:
put the wings on it), and **the autopilot** (`p`, `_fly_itself()`: it flies the guide down to
`PILOT_AP_FLOOR` on final and gives you the landing; any hand on the controls takes it off). From
80 random starts round an airport the autopilot got all 80 down, NICE with nobody flaring. `f` is
flaps (`stall()` comes down, drag goes up). The runways are lit out to `PILOT_LIGHTS` for every
airport about (`airports_about()`), with the tower's beacon going green and white up over the
town; the strobes and the slope lights within `PILOT_NEAR_LIGHTS`. `nearest_airport()` looked a
fifth of a tile away for the next airport, not a whole one, until this - which the first pilot
commit shipped with.

**Gear, wind and a flight plan.** Every flight from the gate or the menu has a `dest`
(`flight_plan()`: another airport one to three tiles off, from the seed), and then `goal()` is that
airport however far, so the panel's nav (`TO ...`), the tower and the autopilot all go there;
`PILOT_ENROUTE` out it is "proceed direct", and coming inside it the tower hands you over to the
next (`tower_name()`). Landing anywhere still counts; landing at `dest` adds `PILOT_DEST_PAY`.
Airports have names now (`airport_name()`; the menu's own is always `AIRPORT_NAMES[0]`, on its
terminal too). `g` is the gear (`gear`/`gear_set`, `PILOT_GEAR_TIME` to move, a quarter more drag
down; a `GEAR` warning low, a word from the tower) and landing with it up is `BELLY`: down, unpaid.
`air_wind(now)` is the wind, each night its own up to `PILOT_WIND_MOST`, more in rain; it only
moves you in the air (no wind on the roll, and on the wheels you straighten up with the runway).
Touch down crabbed past 0.18 and it is a grade worse, past 0.35 a wreck. `commands()` lays off the
nose into it so the guide's headings are tracks, which is what kept the autopilot landing in a
gale. Two things a crosswind showed: final was caught at 220 from the fix but given up at 160 off
the line, so a wind could put you on final and off it in one go, round and round (now 150 and
250); and floating past the end in the last few feet counted as overflown and went round. Checks
that want still air set `ck.calm`; `pk_at()` and the robot circuit do. Flown: 80 starts in each
night's wind, 40 in a 9-unit crosswind, 30 whole flights to their plans, all landed NICE.

**The view from outside, the landing light, and thunderstorms you can fly into.** `v` is
`render_outside()`: a camera `CHASE_BACK` behind and `CHASE_UP` over, swinging round after the
heading a moment late (`ck.cam`), the world level and the jet banking. `draw_jet()` is a dozen 3D
points turned by `plane_frame()` and joined by `_plane_seg()` as stairs (flat runs of `-`/`|`
with the slope glyph only at the steps; plain runs of slashes read as hatching) with a black edge
round it. **`draw_plane` was already taken** by the planes in the sky: defining it again
silently replaced that one. `l` is the light (on at the start): `draw_landing_light()` works a
row at a time like the ground, solving for the interval of each row the beam falls on instead of
testing every cell, and paints what it finds (`runway_paint()`: piano keys, aiming point,
touchdown bars, centre line, edges; grass round the field). It only reaches `PILOT_LIGHT_REACH`,
so from cruise it lights nothing, which is right. Storms: `air_cells()` puts one in some squares of
an `AIR_CELL_TILE` grid each night, building and dying with it, drifting on `night_wind()` -
**not** `air_wind(now) * t`, which went backwards whenever the gusts eased. `ck.weather()` is how
far in you are (`PILOT_TOWN_STORM` everywhere when `storming()`): turbulence in `step()`, gusts in
`wind()`, the murk, rain on the glass, the jolt; from outside one, `draw_air_storms()`. **The
first version looked silly** - a cylinder, so every strike filled a box with `:` from base to top
and a ruler-straight curtain of `|` hung under it - and was redone the way a night storm is seen:
`storm_profile()` gives each column across it (`u`, in radii) a billowing tower over a ragged base
and an anvil leaning downwind (`_billow()` is the smooth per-storm noise); between strikes it only
puts the stars out; a strike (`air_strike()`, now with a height and a ground-or-not) lights the
cloud round where it went off, with faint speckle tracing the rest of the outline; one in three
comes to the ground as a bolt with a branch; the rain is dots and short streaks, thick in the
middle, slanting with the wind, not all of it reaching the ground. Cheaper than the box, too. From the plane `v.air` stops the old by-bearing far storm, which was not anywhere. The guide
goes round a storm across the way (`_round_weather()`, one side per storm, not one you are in or one
on the destination), so the tower warns you and the autopilot takes you round; flying in is yours
to do by hand. Two things the weather showed: the director gave no bank under 12 so a gust on short
final drifted you off the runway (a little is allowed now), and **the autopilot turned straight off
the runway into a tower** - it now climbs out along the runway (`climb_out`) to `PILOT_CLEAR`, over
the tallest roof, first. Flown: 40 whole flights in all weathers, 30 with a storm put across the
route (all went round, all warned), 24 with one on the airport, all landed. Storms cost about 2 ms
a frame at 300x90; the street is untouched (frames identical).

**Other traffic.** `airway_traffic()`: airways every `AIRWAY_GAP` each way, flights along them
every `AIRWAY_EVERY` (with gaps), stateless; east-west and north-south on different
`AIRWAY_LEVELS`, so they never meet each other, and none at `PILOT_CRUISE`, so the autopilot never
meets them either. `traffic_about()` adds every airport's `plane_states()` - which now take
`arrive`/`depart`, because **your jet starts exactly where the departures line up, and the
arrivals touch down on top of it**: `ck.held()` is the tower holding that traffic for you (the
airport you are on, any you are low over, and your destination; the street's `draw_airport` reads
it off `v.held`). The exception is the one thing to do: landing on 18, the same way they take off,
the departures carry on, and `runway_busy()` against `ck.eta()` (ground speed: a headwind made you
late and a clearance turned into a go-around) gets you "number two", a late clearance, or sent
round by `_sequence()` on short final, radio or not; it only clears you with 4 s spare either side.
`draw_air_traffic()`: the street's airliner within 900, lights beyond (the side you see, the tail,
landing lights, strobe, beacon). `nearest_traffic()` feeds the TFC line, the `TRAFFIC` warning
(level and converging) and the tower's calls (`TRAFFIC_CALL`, once each - at 15 km it never
stopped talking); flying into one is a crash (`TRAFFIC_HIT`). `key()` now sets `ck.clock`: a key
before the first step judged the runway at the wrong moment. **`draw_plane` had its sides swapped**
all along (its "right" was its left), so red was on the right wing in the street view too.

**The landing report and the moving map.** `_touch_down()` keeps `ck.report` (sink, centre-line
offset to your right, how far past the threshold, crab, speed, bank, nose), and the roll and the
runway left are added when you stop. `landing_lines()` turns it into rows with a verdict and a
severity, `draw_landing_report()` boxes them up in the windscreen (either view) with a tip for the
worst (`TIPS`) - pick the worst by the severity, not the colour: in the checks every colour is the
same number. Stopped, it waits `PILOT_READ` or for Enter (and `x` now pays you too - it used to
hand the plane back unpaid). `draw_nav_map()` is heading-up, you at 78% down, and shows **one page
of `MAP_PAGES` at a time** - asked for, to make flying harder than one map with everything on
it. There were three (route, weather, traffic); the route and the traffic were then asked to be
one, so there are two: DIRECTION (the river and the woods, every runway - yours green, its line
in - the guide's way, `guide()`'s `"to"`, an arrow at the edge to your destination, and traffic as
arrows with their height in hundreds of feet) and WEATHER (storms as radar, the wind along the
foot). From `MAP_WIDE` columns it has the panel's second section (the panel sets `ck.map_wide`)
and `m` goes between the pages; narrower, `m` goes words, DIRECTION, WEATHER, words. The
title is the page and the range, the heading only where there is room for it (on a 21-column map
it covered the page's name). `[` `]` step
`MAP_RANGES`.

**A second runway, and the wind picks.** `runways(ci, cj)` is every runway as (middle, along,
half length): the long one north-south and a crosswind one east-west, `RUNWAY2_DJ` cells north
of the field. **Not across the middle**: the Strip stands 50 cells west of every airport, alongside
it, so an east-west approach through the field went straight over its hotels, and the approach
corridor would have cut them down. Out past the north end its corridor (`approach_cap()`, a band
of 8 cells) passes north of the Strip's last row. `airport_at()` takes in that north field.
`approaches(home)` is each end of each runway (`name` 18/36/09/27, `course`, `thr`eshold, `out`
along the approach, `rw`); `active_approach()` is the one most into the wind, or in still air the
nearer end of the long one, and `ck.pick_approach()` asks it (or the end a check set in `ck.end`).
`guide()`, `nav()`, the report, `on_runway()` (`runway_under()`), the alignment on the wheels
(`runway_course()`), the climb-out and the map all work in that runway's frame - right of the line
is positive now, for every way in. `taxi_net()` lays out the taxiways and holds; `field_cell()`
caches per cell which runways, taxiways and hold bars touch it, so `field_point()` - grass, tarmac
or paint - is cheap enough for the ground pass (about 2.5 ms more standing on the airport).
Two things it showed: **`approach_cap()` only looked in its own column of tiles** - the crosswind
approaches run east and west into the next - **and returned the first corridor it found**, not the
lowest, so a cell far out under one airport's approach and close in under another's kept a tower
the second needed gone. And a go-around turned for the entry point at a thousand feet, out of the
corridor and into one: it climbs straight ahead (`climb_out`) like a departure now. The Chinatown
lantern check was held to 60% by the luck of its first 250 buildings; the rate is 55%.

**Taxiing, gate to gate.** `Cockpit(..., gate=n)` - which the desk and the menu use - starts at
stand n (`taxi_net()["stands"]`, nose in, state `gate`); the checks and the robot still start on
the runway. `+`, `r` or `p` starts `_push()`: `PUSH_BACK` back over `PUSH_TIME`, turned to face
east, then state `ground` with `ck.taxi` (points still to go) from `_taxi_out()` to the hold and
the line-up for the runway the wind gives (`ck.dep`). `_taxi_progress()` pops points, tells you
at the hold and lined up (`lined`); landed and under 12, `_taxi_in()` picks the next turn-off
ahead and a gate, and on the stand you are `parked` and `ended`. Enter or `x` while landed skips
it (a tug). `p` on the ground is `_taxi_itself()`: `PILOT_TAXI`, slow for corners, stopping
lined up or on the stand. **Lining up took three goes**: aiming at the line-up point turned it
back round when it rolled past, aiming down the line converged too slowly; it steers on how far
off the line it is now. Off the runways `PILOT_TAXI_DRAG` (one step of throttle used to settle
at fifty knots), grass `PILOT_GRASS` and a wreck at speed, `GRASS`/`TAXI SPEED` warnings, and
the wheels straighten up with the runway on the take-off roll too - **a line-up 8 degrees out
drifted off the crosswind runway, whose field was a narrow strip, into a building**; the north
field is wider now and starts inside the main one's wavy edge, where taxiway A ran over a gap.
`draw_taxi_greens()` lights the way; the panel (`taxi_words()`), the outside strip and the map's
ROUTE page show it; `ck.gate_on()` / `v.my_gate` keep the parked jet off your own stand. Flown
from gate to gate with the autopilot: 50 of 50 parked, bar one blown off the runway by a storm.

**The control tower, with its radar.** `draw_atc_tower()` draws over the one-cell shaft `lot()`
builds (`ATC_TOP` tall): a cab wider than it, a ring of lit glass with a catwalk and a roof, a
mast, and the radar going round once every `RADAR_TURN` - long, edge on, long again, which is
what reads as turning; the beacon is on top of the mast now. `draw_airport()` draws it in the
street; `draw_runway_lights()` from the plane, unless the street already has. **`TOWER_TOP` was
taken** - the sky decks' height - and redefining it for this shrank every sky deck in town; four
sky-deck checks caught it.

**Taxiing by hand never got the take-off**, reported, and the checks had only ever taxied with
the autopilot. Three things: the route moved on only within 9 units of each point, so a corner cut
by hand stuck it; lined up wanted 3 degrees and 2.5 units, which only the autopilot does; and `r`
with the route not done always said "taxi to holding point". Now a point is passed once you are
beyond it along the next leg (`_taxi_progress()`), `on_departure()` is lined up by hand at 11
degrees and 8 units (the autopilot is held to the old figures, `tight`), and `r` on the runway
you were given clears you whatever the route says - at the hold it is "line up and wait", on the
wrong runway the tower tells you. And **the grass was a trap**: a fixed `PILOT_GRASS` drag
bigger than a few steps of throttle held a jet still where it stood, power on; it is per unit of
speed now. `ht_taxi()` in the checks taxis on the keys alone, corners cut, the way a person does.
**Height callouts, and when it goes wrong.** `_callouts()` calls `PILOT_CALLOUTS` on the way
down (1000, 500, 100, then every ten feet from 50), each once until you are well back above it,
and `draw_flight_words()` puts the last one up big in the sky over the runway for a second. The
low ones come fast - the game's sink is about 100 ft a second against a real 12 - so unflared
they are three frames each; the speed of the countdown is itself the cue. **Trouble**:
`flight_trouble(seed)` gives one flight in `PILOT_TROUBLE_ODDS` something, which the gate and
the menu's `f` pass in (`Cockpit(..., trouble=)`; the checks and the robot never get one), and
`t` at the desk is a **check ride**, `check_ride()` going down `PILOT_TROUBLES`. `_trouble()`
fires it: **engine** in the cruise, 40 s and more after lift-off (`up_at`); **birds** at
`PILOT_BIRDS_AT` on the climb out - `draw_birds()` past the windscreen for `BIRD_PAST`, a jolt,
and at `BIRD_HIT` one engine, or one time in four both; **blocked** on final 120 to 450 out -
`_block()` puts a truck on the touchdown zone (`blocker_at()`, driving out over `BLOCK_ROLL`,
amber streaks so it shows from a mile, `draw_blocker()`), shuts that runway (`closed`, which
`active_approach(..., shut=)` honours and the map draws in red `x`), and sends you round to the
other. `_lose_engines()`: thrust goes by `engines / 2`, one out swings the nose to it
(`PILOT_YAW`, held off with a little bank), the mayday, the radio on, `dest` the nearest
airport; with none the autopilot will not take it. **The dual failure was measured before it
was tuned**: at 175 ft there are about 350 units of runway still ahead, and the game's lift is
in the pitch, so with no power you float level until the speed goes - which is what killed the
first robot, floating past the end. Nose straight down and back on it gets down, 36 of 36 in
crosswinds; that is what the windscreen tells you. Landing gently on water is now a ditching
(`_ditch()`, `DITCHED`), and getting it down after trouble pays `PILOT_SAVE_PAY`. `em_fly()` in
the checks is fp_fly with trouble: engine, birds both ways and the truck all landed, 20 of 20
each in five winds when measured.

**Fuel, and the pad at every airport.** `ck.fuel` is the tank, of a full one: `_burn()` takes
`PILOT_BURN` times (`PILOT_IDLE` + throttle) a second per pair of engines, `PILOT_TAXI_BURN` of
that on the wheels - a long flight plan is about half a tank, a short one a quarter, taxiing two
per cent. The gate and the menu start you with `gate_fuel()`, a quarter to three quarters, and
say so when it will not reach the flight plan; checks and robots get a full tank (`fuel=None`),
so nothing they fly changed. `fuel_range()` is the cruise range the panel shows (`FUEL 45% 39km`,
gold when short of where you are going, red under `PILOT_LOW_FUEL`), and the tower warns once in
the air. Dry, `_run_dry()` is both engines gone, as the birds do. **The pad**: `taxi_net()`'s
`pad` and `padbox`, south of the stands on the line of the z0-150 turn-off, a lead-in to taxiway
A, painted in `field_point()` as a yellow box; `draw_fuel_farm()` puts two tanks, a FUEL sign
and the bowser by it (street and plane both), `draw_hose()` while filling, and the map an `F`.
`k` (`_fuel_key()`) on the ground routes you there (`taxi_to` `("fuel", None)`), on it starts
and stops the hose (`PILOT_FILL`, billed at `PILOT_FUEL_PRICE` a tank in `fuel_bill`, taken off
the pay at the end), and full, `_fuelled()` makes it `ground` again with a route out - so a
landing on the way is a fuel stop, and landings now add to `pay` (the destination's pay once,
`dest_paid`). **Taxiing from the pad found a hole in the hand-taxi fix**: a point counted as
passed by being beyond it along the next leg anywhere, and from off to one side of the route
every point was, so it cut across the grass into a hangar on 09 - passed only counts within 45
units now. Measured: from all four gates in five winds, to the pad and out, 20 of 20 lined up.
 **The panel's gauges, asked for on 2026-11-08**: the fuel is a vertical red bar at the right
of the first section (`2 * k` wide inside its rails, from under the compass row to the foot,
emptying from the top, blinking under `PILOT_LOW_FUEL`, the % under it), and the words wrap
short of it; the range it gives is still a word, `[RANGE 39km]`, gold or red as the gauge's
word was. The thrust bar is `k` rows deep and up to `22 * k` wide, and on a big window the
flaps are a block-letter 0, 1 or 2 beside the airspeed, under FLAPS, and leave the words. At
scale 1 the bar and the flaps word are as they were. **Wipers**: with water on the glass
(`WIPER_ON`) two blades sweep it from pivots at the foot of the windscreen a third of the way in
from each side, in step and mirrored, over and back every `WIPER_PERIOD` (`wiper_arms()`,
`draw_wipers()`), and `wiped()` keeps the drops and streaks off the glass a blade has been over
in the last `WIPER_CLEAN`. Dry, they are parked and the frame is what it was; a check says so.
Under half a millisecond at 300x90.

 **Keys moved, and the wings got heavy** (asked for, 2026-11-08): the throttle is `W` and
`S` - shift and the nose keys - and `+` `-` (with `=` `_`) zoom the map and the radar, in place
of `[` `]`; at the gate `W` is the push back. a/d rolled you in at a `PILOT_ROLL_IN` then
(gone now, see below) and the wings came back level slower, so a second of `d` was under half
a full bank. That broke `pk_fly()`, the keys-only robot, three
ways, and each was the robot's, not the plane's: it turned onto its next heading as late as
before and overshot (it looks ahead by `PK_LEAD`, the time the wings take to come level, now);
it circled a turn point for ever, the wider turns never coming within 90 of it (`PK_NEAR` is
170); and it swung wide onto final and started down over the town's roofs (it holds its
height till it is within 60 of the line). 25 airports of 25 landed, NICE or better. **The
frequency you are on is in block letters** on a big window, the size of the altitude over it,
with COM and its station over it and STBY at the end of that row, and the radio's lines under.

**Icing, fog approaches and holding patterns** (asked for together, 2026-11-08).
- **Ice** (`ck.ice`, 0..1, `_ice()` every step): it comes on at `PILOT_ICE_RATE` times
  `icing()` - the storm's cloud (`weather()`), falling snow (`snowfall()`), and a little in
  a fog night's fog below `PILOT_FOG_TOP`; never in calm air. **Not in plain rain**: the first
  version iced rain at the cruise, it rains a third of the time, and every flight iced up. Ice
  raises `stall()` by up to `PILOT_ICE_STALL` and the drag by `PILOT_ICE_DRAG`, so left alone
  it stalls you; ICE on the panel past `PILOT_ICE_WARN`, an `[ICE 40%]` word, the tower once,
  and `draw_frost()` frosts the windscreen in from the frame (the wipers do not touch it).
  `e` is the de-icer (`ck.deice`): it takes it off at `PILOT_DEICE_RATE` and drinks
  `PILOT_DEICE_BURN` of idle more. The autopilot does not switch it on - that is yours - so
  the checks' robot pilots (`fp_fly()`, `em_fly()`, the anywhere-round-an-airport test) put it
  on when ICE shows, as a pilot would; a town-wide storm iced one solid before they did.
- **Fog from the air**: `render_street()` leaves the street's fog off for `v.air`, and
  `render_cockpit()` runs `draw_fog()` with a reach of its own (`PILOT_FOG_NEAR`,
  `PILOT_FOG_FAR`, the street's breathing kept) and a `scale`: in the layer (below
  `PILOT_FOG_TOP`, 350 ft) every distance counts; over it only the fraction of the way down
  that is fog, `top / alt`, so the ground is there but thinner. The runway's lights bloom out
  of it close in. **`draw_ils()`** puts the localiser along the foot of the horizon and the
  glide slope up its side, as diamonds, within `ILS_REACH` of the runway coming at it
  (`ILS_LINE`, `ILS_SLOPE` a full swing): the needles the words section used to have, where a
  real PFD has them. MINIMUMS is called at `PILOT_MINIMUMS`, and on a fog night the landing
  clearance gives the visibility. **Checks of the cockpit's view must put the plane where a
  plane is**: one at 300 ft 500 out was inside a building, every frame blank, fog or not.
- **Holds**: one gate flight in `PILOT_HOLD_ODDS` (and the desk's check ride, `CHECK_RIDES`,
  not the random troubles) has `hold_due`. In `guide()` a pending hold sends the `fix` leg to a
  holding fix `PILOT_HOLD_OUT` past the final fix, then the `hold` leg is a racetrack of four
  corners on the right of the inbound line (`PILOT_HOLD_W` by `PILOT_HOLD_L`), till the time
  is up and you are back over the fix inbound; then `hold_left`, the tower's "leave the hold,
  cleared for the approach", and on. The fix leg's own steering must wait while a hold is
  pending, or it overwrote the hold's target and only planes coming straight in ever held.
  The tower says hold, right turns, maintain, and when to expect more (keyed on the minutes
  left); the panel counts `HOLD 0:40` down; the guide wants `PILOT_HOLD_SPEED` in it. **It is
  short on purpose**: a tank is about four minutes at the cruise, and the first, two-minute
  hold ran half the test flights dry. 9 of 9 held and landed NICE on the autopilot.

**Heavier again, and a bank can kill you** (asked for): a/d are a roll *rate* now,
`PILOT_ROLL_RATE` a second while held, not a bank they ease to - there is no stop at
`PILOT_MAX_BANK` (which only the autopilot and the director still use), so holding on is how
you overbank. Let go and the wings come level at `PILOT_ROLL_OUT`, but not past
`PILOT_BANK_UPSET` (70 degrees): on its side it rolls on over at `PILOT_ROLL_OVER` and the nose
goes down, and only the other key held gets it back - `PILOT_ROLL_OVER` is under the roll rate
on purpose; the first try had it faster, and an upset could not be flown out of. A bank costs
lift: `PILOT_BANK_SINK` times (1/cos - 1) off the climb, and `stall()` goes up by the root of
the load factor. Over `PILOT_BANK_WARN` (35) the panel shouts BANK ANGLE and the NOSE/BANK row
goes red. Out of calm air, with the autopilot off, the wind knocks the wings
(`PILOT_GUST_ROLL`, by the wind's strength over `PILOT_WIND_MOST`, a few sines and a hash), up
to about 0.16 rad in a strong wind with nobody on the controls. **The rudder is A and D**
(shift): `ck.rudder` eases to the key and back, and yaws the nose `PILOT_RUDDER` a second in
the air with the wings level, `PILOT_RUDDER_GROUND` on the wheels - for the last of a crab on
final, and the taxiways; RUD has a gauge after BANK. The keys-only robot needed nothing new
for the rate, it was already looking ahead by the time the wings take to come level: 25 of 25.

 **The runways' numbers are on the way's screen** (asked for): each end's name off its
threshold, out along the approach - 18 at the north end, where you land heading south - in
green for where you are going, red for a closed runway, gold for the rest. **What the radio
says is under the frequencies** (`draw_radio_log()`), newest at the foot, wrapped to the room,
the station gold and you plain, and the wrong-frequency line there too - when there are
`RADIO_LOG_W` columns and `RADIO_LOG_ROWS` rows for it; `ck.radio_right` tells
`draw_flight_words()` not to put it at the top left of the windscreen as well, which is where
it stays on a small window and in the view from outside.

 **Two radios, and the tower is not the only one talking** (asked for, 2026-11-08). Every
call goes through `call()`, and "TWR" there means whichever station has you
(`ck.station`, `_station_at()`): the tower of the nearest airport down low, and up at the cruise
the center of the `CENTER_SECTOR` square you are in (`center_of()`, six made-up names, 124.00
to 135.95; towers 118.00 to 121.95, `tower_freq()`). **By height, not distance** - airports are
only a tile apart, so nowhere is far from one, and the first version, which went by distance,
never reached the center and swapped towers whenever the nearest airport changed: climbing past
`PILOT_CENTER` the tower hands you on, coming down past `PILOT_TOWER` the center gives you to the
tower where you are landing (`goal()`), and in the air a tower keeps you till the center has you.
`_handover()` (every step) has the old station say "contact ... on 132.45" and puts it in
`ck.standby`; `c` (`flip_radio()`) swaps `tuned` and `standby`, and on the right one you check in
("with you") and it starts afresh. `ck.radio` keeps everything said, with its frequency, as
`(t, who, text, freq)` - read `r_[2]`, the checks do - and `heard()` only what was said on the
frequency you are on; on the wrong one the radio corner says "...nothing on 119.15. Night Center
is on 130.65 - c" for a while (`missed_at`). The old en-route to tower "contact X. Good night."
in `_radio_tick()` is the handover's now. The two frequencies are under the altitude, COM and
STBY, green when you are on the right one, the waiting one gold when it is. Flown with the
checks' `fp_fly()`, flipping as soon as told: Night Center at 111, Harbour Center at the next
square, Uptown Tower at 100, landed.

**`i` is the wipers' switch** (`ck.wipers`, `[WIPERS]` on the panel): on to start with if it is
raining, and they sweep whether there is water on the glass or not, the way a switch does.

**Three screens on a wide panel** (`MAP_WIDE` up), asked for after the map and the horizon
were tried the other way round: the way (`draw_nav_map(..., "DIRECTION")`) in the second
section, the horizon in the middle, and the weather radar (`"WEATHER"`) in the fourth, with
`draw_wind_arrow()` in its top right corner - the way the wind blows, heading up, longer the
harder - and the wind in words along its foot. The words about the way that were in the fourth
section (TO, the distance, LINE and SLOPE, WIND, WX, TFC) are gone there, asked for: the map
says it (the wind arrow was made bigger after: a shaft up to half the radar deep, two strokes
wide when there is room, and two barbs swept back from the head, its glyphs picked for cells
twice as tall as wide) - but on the ground the taxi words (`taxi_words()`, TAXI to runway 36, FUELLING)
are kept, along the foot of the way's screen. `m` has nothing to turn there and says so; `[` `]` zoom both. On a narrow panel it is
as it was: the horizon in the middle, and `m` puts one page over the words at the right.
The narrow key hint is `key:word` now (`PILOT_KEYS_SHORT`), held to 110 columns by a check: with
the frequencies and the wipers added the old spacing ran off a 110-column window.

 `_label()` writes text over a frame spaces and all; `_text()` leaves spaces
see-through, which is how the first titles came out `--MAP-6-km--`. The key hint has a short form
(`PILOT_KEYS_SHORT`) for windows under 118 columns. About 2-3 ms a frame at 300x90.

**The approach had to be made flyable.** `approach_cap()` claimed to keep the town low but sky decks and
landmarks ignored it, and it stopped 550 units out, under a slope that only cleared the tallest thing at
1050: the first robot flight hit a building on final. Now it runs `APPROACH_LONG` cells off each end, no
tower or landmark stands in it, and no venue where the cap is under 18, so a `PILOT_GLIDE` slope clears
everything at both ends of every runway, which a check walks. That moved a few tall buildings near
airports. **`pk_fly()` in `checks.py` is a robot pilot on nothing but the keys**: take-off, circuit,
landing. If you change the handling and it can no longer land, neither can anyone. It flew 36 airports
out of 36 when this went in.
