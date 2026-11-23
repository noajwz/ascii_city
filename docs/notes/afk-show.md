# Away from the keyboard: the show

Asked for on 2026-11-23: "some sort of screensaver ... I want it to have an AFK option and when
on idle it does things". What the owner settled, in their words and choices:

- **Only the idle timer starts it** - no key. `AFK_IDLE`, two minutes without a key
  (`ASCII_CITY_AFK` in the environment overrides it, which is how the pty case gets 3 s).
- **No walking in it.** "The set routes j & J and any autowalking is not part of AFK. for the
  afk we can have general things just showing of things like skyline rides/transport." So
  not the wander, not `j`, not `J`.
- **The skyline and the rides**: the cruise, the plane, the el, the metro and the taxi. Not the
  submarine or the rocket (they had no autopilot and were not picked).
- "make it so the taxi/metro rides in the AFK/Idle blend well into that theme": no WHERE TO?,
  no meter, no fare out of the wallet, no board to pick a station from, no key hints.

Scene length (3 minutes, `AFK_SCENE`) and "any key puts you back exactly where you were" were
my defaults, offered as changeable.

**How it hangs together.** `Afk` (just before `main()`) keeps its own camera for every scene
and touches none of `main()`'s state, so coming back is just dropping it: `main()` skips its
input, simulation and drawing while `afk` is set, and the key that ends it is spent on ending
it. It starts only when nothing of yours runs on the clock (`elsewhere()`, a doorway, the
wheel, a lift, the booth, a hailed taxi, the autopilot or a walk), since those would carry on
or time out while it played. The blit loop is the `blit()` closure in `main()`, shared by both.
The order of scenes is shuffled once per show, each tried in turn and skipped if there is none
near (no sea: no cruise); each dissolves in over `AFK_FADE`. The HUD says what is showing,
`~ aboard the Midnight Star, down the coast ~`, and for the first `AFK_HINT` seconds that any
key comes back.

**The scenes.**
- **Skyline**: `render_skyline()` panning at `AFK_SKY_PAN` from where your skyline camera was.
- **Cruise**: the nearest harbour whose ship is in; `liner_sail()` and `render_cruise()` looking
  slowly round; `close()` calls `liner_home()`, or the ship would stay out at sea for the real
  you. Ends with the trip if that is sooner. Laying her route out is about 300 ms, once.
- **Plane**: the nearest airport's flight (`render_flight()`), take-off to landing - about 83 s,
  so it ends before the 3 minutes - looking a little fore and aft.
- **El**: a real `Train` at the nearest el station, the way with more line ahead, its doors
  closing after 5 s rather than the 20 a driver gets. `el_autodrive()` sets the handle each
  frame: power up to what lets it stop at `AFK_EL_DECEL` before the next stop's mark, a red
  signal or `danger()`, brake by what it needs, stop on the mark, and at the end of the line
  turn back (`key("ends")`). The card, pay and fines are worked out and never shown.
  `_el_drive` is set only while drawing it, for `el_trains()`, and put back to None.
  It waits at reds like anyone: one station in five the train ahead is held, and then it
  stands 30-40 s behind it.
- **Metro**: the nearest station's platform with `render_platform(..., afk=True)` (no `>`, no
  key line), the train it picks the next one in, `render_ride()`, and on from wherever it
  arrived: station to station for the whole scene.
- **Taxi**: a cab following the walk round town's ring (`new_tour()`, `tour_step()` at
  `AFK_CAB_PACE`) - its route, not the walk: from the back seat at the cab's eye height,
  `draw_cab()` with no meter (`meter=None`) and no destination, the driver saying one of his
  lines now and then (`AFK_SAY_EVERY`). The ride a fare gets is a straight run up one avenue;
  for three minutes that is a straight line or a cut every 14 s, so the show's cab turns
  corners. From a roof, it starts on the nearest long street.

**Tests.** `checks.py` ("away from the keys", at the end, sea on) plays every scene 150 s from
the start: it draws, says what it is, the el stops at two stations, the metro rides, the cab
goes 600 units, and `close()` brings the ship home and lets go of the el; and `draw_cab()`
without a meter has no FARE, the show's platform no key line. `pty_checks.py` plays it with
`afk=3`: the show appears with its hint, and `x` brings the street HUD back.
