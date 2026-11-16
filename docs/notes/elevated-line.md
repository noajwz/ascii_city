# The elevated line, and driving it

One avenue in `EL_EVERY` carries a steel viaduct down its middle (`el_span()`, keyed on the
avenue index and only on avenues that actually exist). It is all world points: columns on both
kerbs every `EL_COL` units, cross beams, two girders along the top and two tracks on them, and a
station every `EL_STATION` cells with a canopy and lamps. Points are laid along z only over the
stretch in front of you — an avenue is endless and a column of points down it is not free.

Trains run both ways, `EL_CARS` cars of lit windows, headlights, and a spark underneath now and
then, at `EL_SPEED` with `EL_SPACING` between them on a track; position a function of time, as
everything that moves here. Side-on is where they read best — roof line, a row of windows, the
deck under them; head-on from under the line they are a pair of headlights coming at you through
the steel. Within earshot the HUD says `~ a train overhead ~`. The line stops where the avenue
does, at the woods and the headland (`el_runs()`).

On the waterfront it is a dotted track across the middle layer — its ties on that layer's
parallax, so it sits in the town rather than on the glass — and every 48 seconds a train slides
across the screen along it, one way then the other, drawn before the reflection so it lies on
the water too. The train itself is in screen space, not on the layer's parallax — a simplification;
putting it on the parallax would make it slide with the town as you pan, which it does not yet. ctrl-a `=` in the checks' menu
stands you under it, on the pavement by the columns, looking along.

### Driving it yourself

Asked for on 2026-11-16: "make the train rideable: braking to the platform mark, signals, a
timetable to keep, in the spirit of the plane and the cab." **Walk up a station's stairs** and you
are in the cab of the train at that platform, doors open. Every station has two
(`el_stairs()`), one a side, on the kerb by the columns, each climbing the way its platform's
trains go: the x0 side is for +z, the x1 side for -z. The stairs and their lit `E` with `EL 57TH
ST` are drawn by `draw_el()` from the street only. `el_stairs_near()` is the trigger, put into
`venue_at()`, so the hurry and the doors-shut rules work for it as they do for any door.
`]` on the panel ("drive the el", with the plane and the rocket) stands you a step short of
the nearest stairs and puts you straight in. `x`, stopped, gets you off. At a platform that is
down its stairs, a step short of their foot (`Train.off()`); anywhere else it is the pavement
under the train.

The stations are where they always were (`el_station_z()`, now shared by the trigger and the
drawing). They are named for their cross street (`el_station_name()`). The canopy is now
a train long (`EL_PLAT`, from twelve units to thirty-eight): you cannot stop a 36-unit train at
a 12-unit platform.

- **One handle** (`Train.notch`): `w`/`s` step it one notch from EB through B7..B1, N,
  P1..P4, and it stays where you leave it, the plane's way, because curses sees no key go up.
  `n` is neutral, space is the emergency brake, `h` the horn. Power falls off past `TRAIN_BASE`
  (constant power). Each brake notch is `TRAIN_BRAKE`. While the doors are open there is no
  power and a holding brake.
- **The card** (`_extend()`, `_close_leg()`): stations along the line until there are
  `TRAIN_CARD` stops ahead, one in `TRAIN_PASS` run through (a "pass" time, a timing
  point). Each leg's time is a gentler run than the train can make (`train_ref()`: 0.75 up,
  B5 down, 20 top), plus `TRAIN_SLACK`, plus `TRAIN_DWELL` at a platform, rounded to the
  wall clock's second, which is how the card prints them (`Train.wall()`). The doors close at
  the card's departure, or after `TRAIN_DOORS` if you came in late. You cannot leave early.
- **The mark** is the `[4]` board at `EL_MARK`, where the cab stops with the train centred on
  the platform. Stopped from `TRAIN_SHORT` short to `TRAIN_OVER` past it, the doors open and
  the stop is scored (`_arrive()`). Further short and the desk says draw up. Further past and
  the doors stay shut: it counts as run through, with a fine. Pay is `TRAIN_PAY` plus on the
  mark, on time and a smooth stop: B4 or less at the moment you stop, or the passengers say
  so. At most $21 a stop. It goes into the wallet through `train.pay`, the cab's way.
- **The signals** (`sigs`, rebuilt with the card): a home signal `EL_HOME` before each platform,
  a starter `EL_START` past it, and one between when the gap is over 70. Red while the train
  ahead is anywhere in the block past it (`red()`). A stop's starter is also red until its
  doors have shut: an approach-controlled starter, so you come in on a yellow. The last
  starter before the buffers is always red. Yellow is red next. **Run a red and the train
  trips** (`trip`: the emergency brake till you stop, `TRAIN_SPAD_FINE`).
- **The train ahead** (`lead_at()`) runs your card `TRAIN_HEADWAY` earlier on the reference
  run, and at one stop in `TRAIN_HELD` it stands 25 to 50 seconds too long. When that is
  ahead, control says so and you meet its reds. It is real: `el_trains()` hands it back for
  your track in place of the timetabled trains (`_el_drive`), so `draw_el()` draws it and
  you watch it pull out. **The blocks are short** (50 to 110 units) and one yellow is not room
  to stop in from line speed: the first version's robot ran two reds a shift. So the desk shows
  how far it is to the first signal at danger for the train ahead or the buffers, `RED IN 140 m`
  (`danger()`), the way a modern metro shows the driver's authority. It leaves out the starters
  that only wait for you to stop, because the stop line covers those.
- **Over the limit** (`TRAIN_LINE`, 79 km/h) the brakes come on by themselves till you are
  3 under.
- **The end of the line** is where `el_runs()` stops: the last station on the card is a stop,
  its doors stay open, and `r` (at any platform, stopped) walks you through to the other cab
  with a new card the other way. You change tracks as you do it, to keep running on the left.
  Run on past the last mark and the buffers stop you at 8 units, with a fine if you hit them
  at more than 2 a second.
- **The view** is `render_street()` from the front of the cab at `EL_H + 2.3`. That is under the
  roof renderer's 10, so it is the street's cost: about 7 ms at 120x36 and 14 at 300x90.
  `draw_train_world()` adds what only the driver sees. Your two rails and the sleepers are
  solved per row like `draw_deck()`, and `draw_el()` skips its own one-line rail on your track.
  The platforms are also solid per row, with the yellow edge: from up there the street showed
  through them. Then the people (they board while the doors are open), the mark, the signals
  with their lamps (drawn first, being the furthest) and the buffers.
  `draw_motorman()` is the frame and the desk: the speed, the handle with every notch, the
  signal ahead repeated, the doors, RED IN, the next stop and its distance, the clock, when
  you are due or go, how the last stop went, and the card on the right. On a big window the
  speed is in block letters. Below 50x16 it is one line at each end.

The checks drive six cards with `train_robot()`, a notch a frame as a key would, and every
stop has to come out on the mark with no fines. It is the same robot that ran the reds before
`danger()` was on the desk.
