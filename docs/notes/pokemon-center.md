# The Pokemon Center

A joke, and a useful one. One city block in `CENTER_ODDS` has a Pokemon Center
(`center_of_block()`, hashed per block like the metro stations, and like them never asking
`lot()` — `lot()` asks it, through `center_at()`, and turns the cell into one over whatever it
was going to be). Out of the parks, the woods and the placed zones, on a building with a real
street front. `draw_center_column()`: white walls, the red roof band all the way round, lit
windows, sliding glass doors; `draw_center_signs()` puts POKEMON CENTER on the band and the ball
(`CENTER_BALL`) lit over the doors. The ball was on the roof first, and from across a street —
as far back as you can stand — the roof is over the top of the screen.

Walking in (a venue, so the hurry rule applies) is `render_center()`, the `poke` state in
`main()`: the tiled floor, Nurse Joy (`JOY`) at the counter with her lines (`CENTER_SAYS`),
the healing machine with its six balls, and the PC in the corner. `h` and she takes them —
the balls light one by one, flash, the chime — then she bows and hopes to see you again
(`CENTER_DONE`); free, as it should be. `c` is the PC: **`library/pokemon_types_tui.py`**, a
byte-for-byte copy of the TUI repo's type chart (as of its `fdffd17`), run through the same
`run_program()` hand-over as the library's readers, so the same rules hold — it is run, not
imported; a fix there does not reach here without copying it over again. `q` quits the chart.
`x` steps you back out the way you came, facing the street. `,` in the menu stands you across
the street from the nearest one.

**Big** (`render_center_big()`, on the big-window system when `center_size(k)` fits): POKEMON
CENTER across the back wall in block letters; Nurse Joy and the healing machine drawn small and
blown up `k` times (`_blow_up()`) - they are shapes - so the balls light up big; the PC a bigger
monitor with PC on it in block letters, since blowing the small one up would read PPCC; the
counter and the floor tiles `k` times as wide. What she says, the chime and the keys stay plain.
`_center_state()` works out the moment (what she says, balls lit, the bow) once for both sizes.
`z` is in the Center's own key branch, which catches every key before the shared one. The fifth menu column is AND THE REST now.
