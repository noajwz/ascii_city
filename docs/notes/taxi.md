# The taxi

**`t` on any street hails a cab** — a proper street (`road_at()`), dry, not in a venue, the sewer
or on a roof; anywhere else the HUD says to stand in a street. `taxi` in `main()` is a state like
the lift's, and nothing moves you while it is set. `hail`: `draw_taxi_coming()` brings it along
the street's own axis towards you over `TAXI_ARRIVE`, slowing - a sprite in the world the size
of a car (`TAXI_COMING`, its sign `TAXI_SIGN` in red, headlights), where it was three fixed little
drawings and asked on 2026-11-13 to be bigger: on a big window it was a few characters wide - and
stops **6.5 units off** — at 3.2 it pulled up under the bottom of the screen, the camera not being
able to look down. `menu`: you are in, and `taxi_dests()` has found the nearest of each of
`TAXI_DESTS` with `find_place()` (about 60 ms, once) and priced it, `FARE_BASE` plus `FARE_PER`
a unit as the crow flies; `draw_taxi_menu()` puts WHERE TO? in the windscreen, `w`/`s` or the
arrows choose, enter or `t` goes, `x` or esc gets out. The fare comes out of the wallet up front;
short of it, the driver shakes his head. `ride`: the camera, at a seated `eye`, goes along the
nearest avenue towards where you are going for as far as it runs open (`taxi_route()`,
`taxi_ride_at()`, eased at both ends) while `render_street()` draws the real city past it and
`draw_cab()` puts the back seat round it — roof, pillars, the mirror with dice swinging, wipers
when it is wet, the driver's headrest, a line from him (`DRIVER_SAYS`), the meter counting up to
the fare in red. **It is the city going by the window, not a map of the way**: the route is one
straight avenue, and at the end you are set down at the place, facing it. Six to fourteen
seconds a ride, by distance.

### Driving it yourself

**`d` in WHERE TO? and the driver gets out**: "All yours. I'll be in the diner." `cab` in
`main()` is a `Cab`, and `elsewhere()` counts it. There is no cheat key for it - the panel has
none left - and it needs none: `t` works on any street, so the way in is two keys from anywhere.

- **The controls stay put, the plane's way**, because curses sees no key go up: `w`/`s` step
  the speed held (`CAB_STEP`, a cruise control, up to `CAB_TOP`, down to `CAB_BACK` in
  reverse), space or `b` brakes to a stop, and a steering key holds the wheel over only while it
  keeps repeating (`TURN_FIRST` for a fresh press, then `CAB_GRACE`) and it comes back by itself.
  The wheel turns you by how fast you are going (`CAB_R` plus `CAB_R_FAST` a unit of speed), so
  standing still it turns nothing. Wet roads (rain or lying snow) brake at `CAB_WET_GRIP`.
  **The steering was "way too sharp"** at first, reported after the first drive: the wheel
  went to full lock in a quarter of a second, so one tap was full lock, and the circle widened
  so little with speed that the faster you went the faster you turned - 2.8 rad/s flat out. Now
  `CAB_STEER` takes the wheel over in most of a second (a tap is about a third of lock, five
  degrees of heading at speed) and `CAB_R_FAST` widens the circle enough that it turns at about
  1.1 to 1.3 rad/s from 16 up; a check holds it there. Slower steering needs feeding in rather
  than banging from lock to lock - the robot below weaved off the walls until it steered by how
  far the bend needed - and it wants corners taken slowly, which is what a cab does anyway.
  **Then "the controls still feel a bit clunky and I wasn't able to properly drift"**
  (2026-11-12), and both were the keyboard, not the car. **A terminal repeats only the last
  key held, after a wait** (375 ms on the owner's Mac, 500 by default on Windows), and the
  checks had been pressing two keys every frame, which no keyboard does:
  - *A held turn started, let go and started again.* A fresh press held the wheel for
    `TURN_FIRST` (0.32), shorter than the wait, so it went back to the middle before the
    repeats came. Now a fresh press pushes the wheel over briefly (`steer_push`) and then it
    **waits where it is** until the keyboard would have started repeating (`_bridge()`); a
    shorter push the longer the wait, so a tap is `CAB_TAP` lock-seconds, five or six degrees,
    on any keyboard. The wait is learned from the first key held (`_press()`, `_key_wait`).
  - *Any second key killed the steering*: brake, handbrake or speed in a bend and the
    steering key went quiet under your finger. Now a key pressed while the wheel is over
    keeps it there while that key is down - and with the handbrake the wheel keeps going
    over, which is what makes `d` then `e` a drift.
  - **Shift and a steering key** (`A`, `D`, shift-arrows: "drift left/right") is the wheel
    and the handbrake on one key.
  `cab_keys()` and `held()` in the checks drive on a keyboard's real key stream; use them,
  not a key every frame, for anything about how the controls feel.
- **Walls and cars.** `_move()` steps the way `main()` walks, with `can_stand()`: into a wall at
  an angle it slides along it, and only if the wall took more than `0.45` of the step is that a
  bump - the first version called every graze one, and the robot driver was bumping three times
  a fare. Head on, under `CAB_DENT` is a bump and over it a crash. The traffic does not see you:
  within `CAB_CAR` of a car in `near_cars()` you have hit it - unless you are stopped, since the
  cars would drive through a cab at the kerb every two seconds. Note that the traffic is not
  drawn within `CAR_CLEAR`, so the car vanishes as you hit it.
- **The fares** (`_fares()`): dispatch (`_dispatch()`) finds somebody `CAB_NEAR` cells off, on
  a road cell beside a building, a step out from the wall (`_kerb_spot()`), and only if the
  satnav can get you there. They wave (`WAVER`) with TAXI! flashing over them
  (`draw_cab_world()`). Stop within `CAB_PICKUP` and they get in, and `_board()` picks where
  to: the nearest of a shuffle of `CAB_KINDS`, `CAB_DEST` off, put down at the road cell
  nearest it (`_drop_cell()`), with [ HERE ] over it once you are close. The meter is
  `CAB_FLAG` and `CAB_PER` a unit driven, not as the crow flies; the tip is up to `CAB_TIP` of
  it by their `mood`, which bumps, crashes, cars and the grass (`cab_ground()` "rough": a park,
  the quad, the tarmac) take from. A quarter are in a hurry and tip double inside `eta`, a
  quarter are nervous and do not like `CAB_LIMIT`; drive them round the houses and they ask
  if you are lost. At `mood` -0.6 they get out and walk, unpaid. What they say is `CAB_SAYS`.
  **This is the first money in the city that is not the `+` cheat**: `cab.pay` goes into the
  wallet each frame. `x` stopped pulls over and you are standing there; a fare still in the back
  gets out with you, unpaid.
- **The satnav** (`cab_route()`) is A* over road cells - streets, alleys, car parks, bridges
  (`cab_ground()` "road", cached) - with its state the cell *and* the way in, so a turn can
  cost something (0.6) and there is no turning round in the road: without that the way across
  a wide junction was a staircase and "left in 10 m" came every other cell. An alley costs 2.5.
  `CAB_GREED` weights the straight line: plain A* took 110 ms on a long fare, and at 1.3 it is
  11. Off the way for a second, it looks again (`_satnav()`); `directions()` says the next turn
  from the way. `draw_satnav()` is heading up, a cell two columns by a row, the way in gold, an
  arrow on the edge when the fare is off the map. `m` puts it away.
- **The view** is `render_street()` at `eye=2.4` with `draw_driver()` over it: the roof and
  pillars, the mirror and dice, wipers in the wet, the dashboard with the speed, the meter and
  HIRED / FOR HIRE, the wheel (`draw_wheel()`, in front of the dash, turning with `steer`), and
  dispatch and the fare along the dash. On the big-window system the speed and the fare go in
  block letters and the satnav and the wheel are worked out from the window's size anyway.
  About 16 ms a frame at 120x36 and 20 to 26 at 300x90, the mirror included.

- **The handbrake and drifting** (`e`, held while it repeats, like the wheel). The cab has a
  `slip`: the way it goes, less the way it points. The nose turns with the wheel; the way it is
  going does not, and the tyres pull it round after the nose at `CAB_GRIP` (times the wet grip)
  - so in ordinary driving slip is a tenth of a radian at full lock, and nothing changed for the
  robot. With the handbrake on the grip is `CAB_HB_GRIP`, the wheel turns you `CAB_HB_YAW`
  more, the power is off and it slows at `CAB_HB_DRAG`; going sideways slows you too
  (`CAB_SLIDE_DRAG`, by the sine of the slip), and the slip stops at `CAB_SLIP_MOST`. Let go
  and the grip straightens it in a few tenths and the speed held pulls you out. `_drift()`:
  past `CAB_DRIFT` and moving is a drift - a screech, marks on the road behind the back wheels
  (`skids`, `CAB_SKIDS` of them, drawn by `draw_cab_world()` with `put_cell()`, so buildings
  hide them), and the fare's say at the end (hurried ones like it, nervous ones do not).
  `_move()` goes along `heading + slip`, so a slide into a wall is still a wall. Measured on
  open ground, full lock at 20 for 1.2 s: 0.97 rad round without, 1.63 with, slip 0.92.
- **The police** (`_police()`). The traffic's police cars are where they always were; one
  within `COP_SEES` that can see you (`cab_sight()`, nothing built between) while you are over
  `COP_LIMIT_MPH`, or just after you hit a car, or while you are known (`heat_until`), puts its
  lights on and comes after you. **It follows the road you drove**, a breadcrumb a unit with
  your speed at each (`cop["path"]`), so it can never go through a building, needs no route of
  its own and takes a corner as fast as you took it, a little more (`* 1.1 + 3`) - and on a
  straight it is held to `COP_TOP`, under your top speed, so the straights are yours and the
  corners are its. Its traffic slot is put out (`_cars_off`, which `near_cars()` skips) and the
  car is handed back through `_cars_extra`, so `draw_traffic()` and `collect_glow()` draw it and
  light the street round it with no new code - and `_traffic()` does not count it as a car hit.
  Stopped with it within `COP_CATCH` for a second (a bump is not pulling over) is a ticket:
  the officer's lines in the dash, `COP_FINE` and `COP_PER_MPH` over at your fastest in the
  chase, `COP_RAN` if it went on 20 s, taken from the wallet through `cab.fine`; then
  `COP_REST` of peace. `COP_LOSE` behind along your road, or out of its sight `COP_HIDE` and
  35 back, and you have lost it - and every police car knows the cab for `COP_HEAT`. On your
  bumper `COP_BOX` and it boxes you in. While it chases, the roof and the pillars take its
  lights and the dash says WEE-OO; `x` will not get you out. A robot getting away flat out on
  the satnav's way, chased from the start, lost it five times in twelve and was caught once;
  the robot corners worse than a person, and a person has the handbrake.
- **The mirror** (`draw_mirror()`, `mirror_size()`, from 60 by 24 up) is a second
  `render_street()` looking back, every row turned round, at half the field of view and twice
  the size (a police car twenty back was a row of it otherwise) and the horizon high so it
  looks down the road. It is about 5 ms whatever its size - the fixed cost of a frame - so it
  is redrawn `MIRROR_FPS` times a second and kept between (`cab.mirror`). That is where you see
  the police coming: the chase is behind you, and the camera cannot look back.

- **The highway, by cab** (asked for). `ramp_at(i, j)` is the whole of the ramps: in the
  outer column of each side of a highway avenue, every `HWY_RAMP_EVERY` blocks an on-ramp each
  way just past a cross street, and half way between them an off-ramp each way, `HWY_RAMP_L`
  cells long, only where the lane under it is dry road; `(kind, way, x0, x1, low, high)`, and
  `ramp_height()` along it. The cab has `h` and `ramp`: on the street a ramp's cell is a wall
  (`clear()` in `_move()`, so you slide along its side - stopping dead on it left the checks'
  robot wedged for good) except at its foot, where you mount it; `_move_up()` keeps you in a
  ramp's lane by its rails and sets `h` by how far along, and off the top you are on the deck,
  held between the rail and the median on your own side (`hwy_deck()`); in the outside lane
  over an off-ramp you go down it. Fares are only picked up or put down on the street, and no
  police start a chase up there. **The deck's traffic** (`_deck_traffic()`): your lane, not a
  circle round you - the lanes are 2.4 apart and `CAB_CAR` caught the car beside you - and
  coming up gently behind a slower car you follow it at its `hwy_pace()` (BRAKE LIGHTS AHEAD)
  till you change lanes; `CAB_HWY_DENT` faster, or into its side, is a crash. A chasing police
  car's breadcrumbs carry the height, `_cars_lift` holds it by the car's seed, and
  `draw_lifted_police()` draws it there. **The satnav** has deck nodes `(i, j, 1)`, one a side
  in its outer column going that side's way (`cab_steps()`): on-ramps up from the cell short of
  the foot, the deck on, off-ramps down; `CAB_DECK_COST` a cell against a street's 1, so a long
  way along a highway takes it, and A* is quicker for it too (6 ms against 147 for 300 cells).
  `cab_node()` is where the cab is in those terms, `route_point()` where to steer - the inside
  lane on the deck, because the outside one goes down every exit, till yours is near - and
  `directions()` says on-ramp, exit, keep left. **The view**: the eye is `h` up, and
  `draw_deck()` paints the deck's surface (rails, median, dashed lane lines) over the street
  below wherever a row's ray meets it first - solving each row's run of columns rather than
  testing every cell, and asking `hidden()` only where a facade is nearer - then the
  highway's cars and the police on it again. From the street `draw_ramps()` draws each ramp's
  edges climbing to the deck and a board at the foot, HWY ^ or EXIT. About 33 ms a frame on
  the deck at 300x90, the street from that height being 23 of it.
- **Headlights** (`l`: on to start, high beam, off; `draw_headlights()`): a pool of light on
  whatever you are driving on, the beam's columns solved per row, fading with distance and to
  its edges, further and narrower on high beam - only the road ahead, never the dark beyond.

`cab_robot()` in the checks drives six shifts of three fares on the keys alone, following the
satnav (`route_point()`), all delivered and paid. If you change the handling and it cannot, neither can anyone.
