# The arcade

`ARCADE_ODDS` on its own hash, a street front required (`_road_face()`), never in the financial
district, and cut down to no more than eleven units unless its district builds higher: the light
wall and the sign over the door have to be where you are looking from across the street. It is
the third building with its own wall column, after the club and the casino.

`draw_arcade_column()`: above the shopfront the whole face is a wall of coloured panes, solid
across each bay with a dark line between so it reads as a screen of big pixels and not as lit
windows. `arcade_pixel()` runs it, one pattern every `ARCADE_MODE` seconds - a rainbow rolling
across, a chequer flipping, a bar sweeping, a sparkle - with each arcade starting the cycle
somewhere else so two in one street are not in step. The sparse ones were made fuller after a
measurement: the sweep lit two bays in seven and the wall went nearly dark between passes. Bulbs
in every colour chase round the roof and the canopy, the corners change colour, and the ground
floor is dark glass with a cabinet's screen glowing in each bay. The pavement takes the colour of
the wall (`collect_glow()`).

`draw_arcade_front()` is the sign: ARCADE in the big font on a blanked board (letters made of the
same blocks as the wall behind them were lost in it), ringed with rainbow bulbs, the arcade's name
under it, and INSERT COIN blinking on the canopy. `arcade_letter()` gives the letters their
routine - dark, on one at a time, the word flashing, then each in its own colour turning slowly.
Within `ARCADE_BIG`; further off, the word in ordinary letters. It hangs just over the canopy: an
early one higher up went off the top of the screen from across a narrow street.

Inside (`render_arcade()`) is a row of cabinets, as many as the window takes (`arcade_order()`),
each with its game's name lit on top and a demo of it running on the screen (`cabinet_demo()`, a
function of time alone); the arcade's name across the top in the big font, the carpet every arcade
has, and two kids at the machines. `a`/`d` pick a cabinet (it lights and gets a `vvv` over it), `p`
plays it, `s` walks you out. ctrl-a `g` in the checks' menu stands you in the door.

**The games** are `GAMES`, one class each on `ArcadeGame`'s fixed-step clock (`GAME_DT`, and no
catching up more than half a second after a stall): `key()` takes `up`/`down`/`left`/`right`/`act`,
`tick()` advances, `draw()` fills a `GAME_W` x `GAME_H` playfield that `render_game()` puts in the
cabinet's bezel with the score, the high score and the controls under it. All of them are taps,
never holds, for the claw machine's reason. While one is going `main()` gives it every key — `w`
and `s` with the rest, so you do not walk out mid-game — except `x`, which leaves the cabinet, and
`q`; space is kept from the autopilot while you are in an arcade, or it walked you out. High scores
are per arcade per game for the session (`play["hi"]`). The six:

- **ROOFTOP RUN** — roofs come at you, `p` jumps, faster and faster. Roofs get longer as it does:
  one jump carries you further, and the bot that tests it once came down off the end of a roof
  shorter than its jump.
- **FIX THE NEON** — turn the tubes until the power runs from the plug to the sign. Each puzzle is
  dealt by walking a path from one to the other and scrambling everything (`answer` keeps the way
  round, so there is a test that every one can be lit), against a clock that shortens.
- **LATE DELIVERY** — a scooter that keeps going on a grid of streets, arrows steer it, deliver to
  the `X`; every delivery buys time.
- **NEON DRIFT** — lanes, traffic, left and right, faster.
- **SKY SHOW** — rockets go up and `p` bursts them on the line; three up dark and it is over. Their
  speed is capped: uncapped, by five thousand points they were a blur nobody could time.
- **NIGHT OWL** — move along the branch and catch the moths; three got away and it is over.

Each has a test in which a simple bot plays it properly and gets somewhere (and, where it makes
sense, one in which doing nothing loses), which is the test that found both of those.
