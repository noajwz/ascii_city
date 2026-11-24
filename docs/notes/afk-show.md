# Away from the keyboard: the show

Asked for on 2026-11-23: "some sort of screensaver ... I want it to have an AFK option and when
on idle it does things". What the owner settled:

- **Only the idle timer starts it** - no key. `AFK_IDLE`, two minutes without a key
  (`ASCII_CITY_AFK` in the environment overrides it: the pty case gets 3 s).
- **No walking in it.** "The set routes j & J and any autowalking is not part of AFK."
- Nothing of the game's screens in it: no WHERE TO?, meter, fare or key hints.
- The first version was six separate scenes. "The six scenes are pretty cool, but please remove
  the skyline an the metro. Also do you think it's possible to make the scenes fade into
  eachother better like the taxi driving to the airport or something?" (2026-11-24). So **the
  skyline and the metro are out; do not bring them back unasked**, and the rest is one journey.

The two minutes, and "any key puts you back exactly where you were", were my defaults.

**The journey** (`Afk`, just before `main()`): a taxi from where you are to the airport, the
flight, a taxi from there to the harbour, the cruise, a taxi to the el, a train, a taxi from the
station it stops at to the airport, and round again (`AFK_RIDES`; where in the ring it starts is
the clock's). Each really goes there and starts where the last ended. Anything further than
`AFK_FAR` is left out - far west, the harbour - and a ride no cab can get to is dissolved to
without one. About twelve minutes round from the start of the city.

- **The cab's way** (`afk_way()`): out to the nearest street, along the streets, in to the door,
  three `tour_search()`es. The middle one has `roads=True`, which makes anything but a street cost
  12 a step; off, it is the search `j` uses, unchanged. One search all the way, keeping to the
  streets, flooded the whole city before it would cross the apron, and gave up. It is **not** the
  walk round town's route any more (the first version's was), only its steering, `tour_step()`,
  with a tour of one stop. The pace is picked so a drive takes about `AFK_DRIVE`. It eases away
  late in the dissolve, eases up to the door, and stands `AFK_REST`. It hit nothing on any
  drive measured. It crosses no runway: the airport's door is the gate side, where the planes
  and the sign are, reached round the end of the terminal - the street side is a blank wall.
- **No pauses**: `prepare()` works out the next cab ride `AFK_WORK` a frame while a ride is on
  (`_plan()`, a generator), since where a flight or a cruise leaves you is known. Where the train
  does is known when it stops; its doors are held while the way is found. At the start it is
  worked out over a few frames of ordinary play, and only then does the show come on.
- **The dissolve** (`fade()`, `AFK_FADE`): the last frame of one scene turning cell by cell into
  the next, from your own last frame at the start. It can be a still of the last one because
  each ends at rest: the cab stopped, the plane on the runway, the doors open. The ship alone is
  still coming in - her way ends off the quay, so it goes over before that. Double-width glyphs:
  the column after one that came through is cleared. A window that changed size is a cut.
- **Flight**: standing at the threshold through the dissolve. About 83 s.
- **Cruise**: `liner_sail()`, the whole trip (195 s). `close()` calls `liner_home()` and puts back
  `_launch_shift`, which sailing moves to have a rocket go up as she passes.
- **El**: a real `Train`; `el_autodrive()` sets the handle each frame - power up to what lets
  it stop at `AFK_EL_DECEL` before the next mark, red signal or `danger()` - and you get off at
  the first stop after `AFK_EL`. It waits at reds like anyone: one station in five the train
  ahead is held. `_el_drive` is set only while drawing.

**How it hangs together.** `main()` skips its input, simulation and drawing while `afk` is set,
and the key that ends it is spent on that. It does not start while something of yours is on (`elsewhere()`,
a doorway, the wheel, a lift, the booth, a walk), and the idle time counts from the end of
those: without that, a cruise you had sat through for three minutes ended in the show the same
frame. The blit loop is the `blit()` closure in `main()`, shared by both.

**Cost** at 300x90: 27 ms a frame in a dissolve (median). The first frame on the ship is about
240 ms, all of it a still of the cab on the quay.

**Tests.** `checks.py` ("away from the keys", last, sea on) plays the whole ring to the second
flight: the order, every cab getting there within 3 units, hitting nothing, on the streets, each
setting off where the ride before ended; the dissolve; and `close()` in the middle of a cruise.
`pty_checks.py` plays it with `afk=3`: the show, and `x` brings the street HUD back.
