# The walk round town

Asked for on 2026-11-16: keep the spacebar's autopilot as it is, and add "a set route where the
character goes through all the districts basically walking in a circle (emphasis on downtown) but
still lot of scenery change without it being distracting". The model was `History/2.py`, the old
one-street screensaver, whose walk the owner liked because it was smooth and never got stuck:
it was a straight line at a steady pace, with nothing decided as it went. So this walk is
planned, not chosen frame by frame. **`j`** in the street starts it, `j` again (or space, or any
walking key) stops it. Space is the wander, unchanged (see the autopilot in CLAUDE.md).

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

**The way** (`tour_search()`): a search over cells, state cell plus the way it came in, so a
turn can cost: `TOUR_TURN` (12) a turn, 2 a step on a downtown street, 3 on another street, 8
through an alley or a lawn, never a tunnel. The cost of turning is what makes it hold a street
the way the old screensaver did - without it the path zigzagged through every block on the
diagonal. Leaving a stop straight back the way it came costs 80, so a stop is not a U-turn.
`tour_points()` then pulls the path straight: each point to the furthest one still in sight
(`can_stand()` every 0.8 along), so an avenue is one line. A leg is 40-200 cells and takes 2-70
ms, so the first is found at the keypress and **each next one is found while the current one is
walked**, `TOUR_STEPS` (250) steps a frame, 2-5 ms - at 1500 a slice was 12 ms, too much on top
of a 300x90 frame.

**Following it** (`tour_step()`, the same `(turn, walk)` as `auto_step()`, so the main loop's
autopilot block serves both): steer at the point `TOUR_LOOK` (3) along the path when a corner is
near and `TOUR_LOOK_FAR` (8) on a straight. 3 everywhere wove - a change of direction every three
seconds and twice the turning the path needed; 5 at the corners cut them into the building. It
slows *before* a corner (how sharply the path bends within `8 * pace` units) and not only once
turned, and above the normal pace brakes to a walk for the corner: the pace multiplies walking but
not turning, and at 3.5 it ran wide and hit the wall eight times a lap. If it gets nowhere along
the path for `TOUR_STUCK` (2 s), or is blocked, it finds a new way from where it stands; a stop
with no way to it is skipped.

Measured headless (`walk_tour()` in the checks, a lap as the main loop runs it): turning 0.9-1.9
radians per hundred units against the wander's 0.9-3.1, never blocked for even one frame at the
normal pace (one at 3.5), back within two units of the stop it set off from.

**It goes past every door.** At under a walk the hurry rule would let every casino, lift, fire
escape and the lighthouse take you in, so while `tour` is set `venue_at()` is not asked and
neither are the fire escapes or the lighthouse door. The HUD says where it is going next
(`tour_name()`) and that `j` stops it. Nothing of it is in `is_open()`'s path, and the plan holds
cells and world points only, never a cached object, because a lap churns every cache.
