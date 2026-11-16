# Flying the rocket

Asked for on 2026-11-16: "It's time to make the rocket fly-able. Take your time it's literally
rocket science ;) . Also I'd love it if I was able to fly to the moon as an easter egg."

**Getting in**: out along the causeway to the fence at the end; in the fence is the crew gate
(`crew_gate()`, CREW in green over it while there is a seat) - walk into it, like any door
(`venue_at()`, so the hurry rule and the panel's shut doors apply), and you are strapped in on
top of the rocket (`Spacecraft`). `i` on the panel puts you straight there. While you are in it
that pad's own rocket is not drawn (`_crewed`): it would stand under you or go up beside you.
Whatever happens, `x` at the end puts you back at the foot of the causeway (`_launch_spot()`),
paid if you earned it (`RK_PAY`: home from orbit, home from the Moon).

## The physics

**Real orbital mechanics on a small world**, the way games about rockets do it, so orbit is a few
minutes of flying and not an hour: an Earth `RK_R` (600 km) in radius with the real pull at the
surface (`RK_MU`), air that thins out exponentially (`RK_RHO`, `RK_SCALE`) and ends at `RK_ATM`
(70 km), a Moon `RK_MOON_D` (12,000 km) out going round it (`rk_moon()`, clockwise, the way you
go) with its own pull and its own sphere of influence (`RK_SOI`). In a plane: the Earth's centre
at the origin, the launch site up the y axis, east along +x; z only exists for the views. Metres
and seconds throughout. `rk_gravity()` is the Earth's pull, the Moon's, and less the Earth's own
fall towards the Moon (everything is measured from the Earth).

**Three stages** (`RK_STAGES`): the booster, the upper stage, the lander - each its dry mass,
fuel, thrust, Isp and drag area. The rocket equation is the game: what is left decides what you
can do. As built, the booster all but makes orbit, the upper stage does the rest and the burn to
the Moon and the landing, and the lander's own tank is spare - the guidance computer has
never touched it.

**Integration** (`_integrate()`): kick-drift-kick, the thrust, gravity and drag together, with a
step that is short while burning or in the air and longer the further from anything you are
(`_h()`), so time can be warped (`RK_WARPS`, to 10,000x) without the orbit creeping: a check
coasts twenty orbits at full warp and the periapsis moves 0.005%. A plain step with a changing
size let it creep. **The burn's own total** is kept (`burned`): a trim stops when the engine
has given what was asked, not when the speed has changed by it - falling away from the Earth
the speed drops by itself, and the first trims overshot by hundreds of metres a second.

**Heat** (`RK_HEAT`, `RK_COOL`): the shield takes rho v^3, coming down, and only if it faces the
way you go (nose back: retrograde); going up the rocket is built for it - an earlier version
burned up beginners' climbs. Measured in from the Moon's distance with the shield first: a
periapsis of 27 to 45 km comes home, 24 and under burns up (`RK_HOME_AIM`, 34, is the
middle). **The chutes**: armed by space on the last stage, open under `RK_CHUTE_OPEN`; under
them you come down at nine metres a second and hit the sea under `RK_SPLASH`.

**Touching down on the Moon** (`_touch_moon()`): under `RK_LANDS` metres a second and upright,
you are down - standing on it from then on (`_stand()`), going round with it, on the same spot
of it (it keeps one face to the Earth). Faster is a new crater.

## Flying it

**The plane's keys** (asked for, after "in some places S is leaving and in others it's X"):
`w` tips the nose over to the east and `s` brings it back up (a tap a nudge, held a steady turn
- the wing's way, `RK_TAP`, `RK_GRACE`), `W` and `S` the throttle a tenth at a time, `c` cuts
it, `space` lights it, stages, then arms the chutes; `h` the holds (prograde, retrograde, off);
`>` and `<` (or `.` and `,`) time, up to what is safe (`max_warp()`: 4 while burning, 10 in the
air with the engine off, all of it in space); `m` the map, `+` and `-` its zoom; `v` the view
from outside; `p` the guidance computer; `x` twice to abort (the escape motor in the air,
"mission control brings you home" elsewhere), and once more to get out.

**Mission control talks you through it** (`rk_advice()`, the dash's last line): the pitch the
climb wants (`rk_pitch_target()`: straight up to 1 km, then over, level by `RK_TURN_ALT`), max
Q, staging, cutting the engine at an 80 km apoapsis, coasting up to it and burning level till
the periapsis clears the air, the way home from orbit. In orbit it says how to come home - and,
not asking, that the Moon is up there and when its window opens (`rk_tli()`). Things it says
once go across the top (`call()`). "...where are you going?" when you burn for it.

**The guidance computer** (`rk_autopilot()`, `p`): from wherever you are, it works out what you
want (`rk_goal()`: orbit from the pad, home from orbit, a landing about the Moon, home from it)
and does it with your keys (`hand=False`), and any key of yours takes her back. It flies the
gravity turn; coasts to apoapsis and circularises (keeps burning once started, nosed up if it is
sinking - it gave up halfway once, when the time to apoapsis jumped to a whole orbit); waits for
the Moon's window and burns; **trims** on the way out to a signed miss distance (`_ap_trim()`:
tries 2 m/s and works out the burn; the plain distance is a V and the trim went off the wrong
side of it); brakes into the Moon's orbit or straight in; lands by a suicide burn and a slow
last 100 m; lifts off, makes orbit, and burns for home where leaving the Moon's sphere sends you
backwards against its way round (the way out turns about 50 degrees from the burn); trims to
`RK_HOME_AIM` - by the Kepler periapsis once clear of the Moon (`rk_predict()`'s "peri"), since
a path into the ground stops the prediction at the ground and the trim had nothing to steer by;
drops the stages, rides in on the shield, arms the chutes. **It is the test**: checks.py has it
fly to orbit, home from orbit, and the whole way to the Moon and back.

**Warping, the computer's way** (`_ap_warp()`): as fast as leaves three real seconds before
whatever is next. A whole Moon mission is about eighteen minutes on the clock, most of it the
climb and the landing, which are the parts to watch.

## What you see

`render_spaceflight()`: the window, the outside, or the map, the dash under it.

- **Low down** (under `RK_STREET`, 900 m, near the pad) the window is the city itself, from the
  capsule, looking back west at the land - mission control's onboard camera. The outside view
  here is the street renderer from beside the rocket, at her height (a camera on the ground
  loses her above twenty degrees: it cannot look up).
- **Above that**, `rk_scene()`: every cell a ray, tried against the Earth and the Moon as
  spheres, with what does not change across a row or down a column worked out once. The Earth
  (`_rk_earth()`) lit by `RK_SUN`, which is behind it from the city: the night side with the
  coast - the hotels' line of light - the city's lights thinning inland, the dark sea, clouds; the
  day side, round the far side of an orbit, blue sea, land, white cloud; dusk between. The air's
  edge is a thin blue line - only rays through the lowest 20 km glow, and only from over it (from
  inside it the whole sky lit). The sun, the stars by direction so they hold still. The Moon
  (`_rk_moon_surface()`): grey, seas, craters, its night lit faintly by the Earth - without that
  you came down on nothing.
- **The camera** (`rk_camera()`): round the Earth, back along the way you came and down at it
  more the higher you are; about the Moon, along the ground towards the Earth, down at the
  horizon from up there and up a little at the Earth once down; between them, at the Moon on the
  way out and the Earth on the way home.
- **Outside** (`v`): beside her, near enough that what is left of her is a good part of the
  picture; `rk_draw_rocket()` draws the stack turned to her pitch - white, dark bands at the
  joins, ASCII down the booster - the flame (longer and wider the thinner the air), the chutes,
  and coming in the air on fire round the shield.
- **The map** (`rk_map()`): the body you are about and its air, your orbit from the elements
  with A and P and their heights, the Moon and its path when they are in it, the prediction
  (`rk_forecast()`, a few thousand steps, worked out every second or so) when it leaves the orbit,
  and MOON ENCOUNTER with how close. Its title is on the second row: the top bar covers the first,
  and a pty case caught the map "never drawing" because of it.
- **The dash** (`rk_dash()`): height, speed, climb, mission time; apoapsis and periapsis and the
  time to the high point; the stage, its fuel, the throttle, the pitch and what the climb wants,
  the hold, the warp; Q or the heat. On a big window height and speed in block letters.

**What it costs**, at 300x90: 15 to 23 ms a frame, every view, all the way through.

The Moon is not on the panel and mission control never sends you: it is there to be found by
flying on.
