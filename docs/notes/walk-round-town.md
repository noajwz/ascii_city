# The walk round town, and the long walk

Asked for on 2026-11-16: keep the spacebar's autopilot as it is, and add "a set route where the
character goes through all the districts basically walking in a circle (emphasis on downtown) but
still lot of scenery change without it being distracting". The model was `History/2.py`, the old
one-street screensaver, whose walk the owner liked because it was smooth and never got stuck:
it was a straight line at a steady pace, with nothing decided as it went. So this walk is
planned, not chosen frame by frame. **`j`** in the street starts it, **`J`** starts the long walk
(below), `j` or `J` again (or space, or any walking key) stops either. Space is the wander,
unchanged (see the autopilot in CLAUDE.md). The owner liked it, and that it still works at a fast
pace, then asked for the drift and the long walk the same day.

**The plan** (`tour_plan()`, at the keypress, under a millisecond): the district squares
(`DISTRICT_CELLS`, with their brickwork offset - `_square_cells()`, `_square_of()`) within
`TOUR_SQUARES` (6) of you, keeping only squares that are one of the eight `DISTRICTS` rows (not
under the woods, the Strip, the airport or another placed part of town, nor near the sea: those
are hours of walking off). The **hub** is the nearest downtown; the stops are the nearest square
of each of the other seven, **in order round the middle of them all**, starting from the hub's
side - round the hub itself gave a fan when the hub was at the edge. Between two stops, a
downtown square near the middle of the leg (within half the leg) is put in. Each stop is a
proper street in the middle of its square that is that part of town (`_tour_spot()`): the middle
of a square is often a building. Measured over a lap from four starts: all eight parts of town,
**27-33% of the time downtown**, against an eighth for an even share. A lap is 2000-4000 units,
four to eight minutes at the normal pace. After the last stop it goes round again.

**The long walk** (`J`, `grand_plan()`): "a route that goes by everything". The walk round
town's stops, and the nearest of each of `GRAND_SIGHTS` - the Strip, the airport, the space
centre, the beach, the pier, the harbour, the woods (by the lake), the suburbs, the factories, the
university, the carnival, the big bridge, the lighthouse, the river, the temple, Chinatown's
square - found the panel's way (`find_place()`), nothing up a lift or out on the water. Put in a
ring: nearest first from downtown, then 2-opt until no two legs cross. From the start that is 26
stops, 22,000 units, **42 minutes a lap at the normal pace** and 17 at the fastest. The HUD says
which stop of how many is next.

**The way** (`tour_search()`): a search over cells, state cell plus the way it came in, so a
turn can cost. On a proper street 2 a step downtown and 3 elsewhere, and `TOUR_TURN` (12) a turn:
the cost of turning is what makes it hold a street the way the old screensaver did - without it
the path zigzagged through every block on the diagonal. An alley 8 a step, and a turn costs there
too; **open ground - the woods, a lawn, the sand - 4 a step and 1 a turn.** At first a turn cost
12 everywhere, and the long walk could not find the woods: their trails wind, every bend was a
street's turn, and the search gave up after 164,000 steps on a way that is 425 cells long. Never
a tunnel. Leaving a stop straight back the way it came costs 80, so a stop is not a U-turn. A
leg over 120 cells is searched greedier (`TOUR_GREEDY`, 4 times the distance left instead of 2)
and allowed `400 *` its length in steps: 3 took 500 slices over the woods, 4 takes 150, for ways
no longer. `tour_points()` then pulls the path straight: each point to the furthest one still in
sight (`can_stand()` every 0.8 along), so an avenue is one line.

**Working it out without a pause.** The first leg is found at the keypress (it is short: to the
nearest downtown). Every other leg is worked out by `_tour_work()` **in order round the whole loop,
a slice a frame** - `TOUR_STEPS` (250) search steps or one corner pulled straight (`_pulled()`,
`tour_way()`), 2-5 ms - and kept in `tour["ways"]`, so the second lap costs nothing. One leg ahead
was not enough on the long walk: at the fastest pace a three-second leg came before a long one
was found, and the rest of that search ran in one frame (350 ms); and pulling a 600-cell leg
straight at once was 47 ms. A leg found ahead is used from up to 10 units off the stop (3 threw
them away whenever the drift had put you to one side, and searched again: 200 ms).

**Following it** (`tour_step()`, the same `(turn, walk)` as `auto_step()`, so the main loop's
autopilot block serves both): steer at the point `TOUR_LOOK` (3) along the path when a corner is
near and `TOUR_LOOK_FAR` (8) on a straight. 3 everywhere wove - a change of direction every three
seconds and twice the turning the path needed; 5 at the corners cut them into the building. It
slows *before* a corner (how sharply the path bends within `8 * pace` units) and not only once
turned, and above the normal pace brakes to a walk for the corner: the pace multiplies walking but
not turning, and at 3.5 it ran wide and hit the wall eight times a lap. If it is blocked or gets
nowhere along the path for `TOUR_STUCK` (2 s), it finds a way back on to the path a little way
along (at most 1500 search steps), and only failing that a new way to the stop - which on the
long walk could be a search of seconds. A stop with no way to it is skipped.

**The drift** (`tour_lane()`): asked for next - "swerves a bit to left and right on the middle of
the street. Sometimes I walk on the sidewalk or too straight." The pulled-straight path can run
along one side of a wide avenue (on average 2.5 units off its middle), so the point it steers at
is moved: to the **middle of the road**, the median of the street's middle at five points along it
(walls found across it, `_across()`, out to `TOUR_ACROSS`) - one point jumped at every alley and
gap between buildings, which doubled the turning - eased slowly; and a **slow drift** either side
of that, by distance walked (`TOUR_WAVE`, 110 units, and a second wave at 2.7 times that), as wide
as the road allows past the pavements up to `TOUR_SWERVE` (1.8): about nothing on a one-cell
street, all of it on an avenue. Both go to nothing near a corner, or it carried them into the
inside of the corner and hit it at speed. In a junction or on open ground, where there are not
walls both sides, the middle eases back to the path, which is clear: holding the last street's
middle there walked it into a wall. Never past the pavement where it steers.

Measured headless (`walk_tour()` in the checks, a lap as the main loop runs it): the walk round
town turns 1.4-2.5 radians per hundred units with the drift (0.9-1.9 without), against the
wander's 0.9-3.1; drifts up to 1.2-1.5 either side; 1-3% of the time on the pavement; never blocked
for a frame at either pace. The long walk at the fastest pace: every stop, no bumps.

**It goes past every door.** At under a walk the hurry rule would let every casino, lift, fire
escape and the lighthouse take you in, so while `tour` is set `venue_at()` is not asked and
neither are the fire escapes or the lighthouse door. The HUD says where it is going next
(`tour_name()`) and that `j` stops it. Nothing of it is in `is_open()`'s path, and the plan holds
cells and world points only, never a cached object, because a lap churns every cache.
