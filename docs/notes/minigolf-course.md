# The minigolf course

One lot in `GOLF_ODDS`, on its own hash (salt 3001) after the karaoke bar's, on a street face, not
in the financial part of town or a park (`b["minigolf"]`). It is open ground, so the lot is held at
`GOLF_H`, under a storey, and `draw_minigolf_column()` is only the fence: pickets with the green
between them, a string of bulbs chasing along the top, the gate lit. `draw_minigolf_front()` puts a
windmill with its sails going round, MINI GOLF (big within `ARCADE_BIG`), the name and a flag over
the gate. A taxi destination ("the mini golf"), and ctrl-a `l` for the checks.

**It is really played.** A hole is a map in `GOLF_HOLES`, a cell a character (`#` wall, `:` sand,
`~` water, `>` `<` `^` `v` slopes, `W` the windmill's gap), and `Minigolf.step()` rolls the ball in
cells at `GOLF_DT` on the course's own clock: friction by the ground, a slope adding its push, off a
wall it bounces at 0.8, into the cup only under `GOLF_DROP` (faster runs over), into the water a
stroke and back where you hit from, `GOLF_MAX` and you pick up. The sails shut the gap for part of
every `GOLF_SAILS` by that clock. `a`/`d` aim, `p` starts the power meter and `p` again hits, as
the bowling alley's meters go; down arrow backs out of the meter. `x` stops a round, `s` walks out
when not playing. `update()` steps at most 240 at a time, so a stalled frame loses time rather
than rolling seconds of ball at once. `GOLF_COST` a round, the best of the session on the card.

The checks play every hole with a bot trying a fan of shots, so a hole that cannot be holed in par
fails. Measured with a shaky hand (aim off by up to 2 degrees, power by 5%), the holes come out
around par; the windmill is the one that bites, since it wants timing.

`render_minigolf()` draws a cell 2 columns by 1 row so the course is square to the eye, bigger as
the window allows (up to `2 * big_scale()` a cell), the name in `_blocks()` big; the scorecard
between rounds, the score over par in `_blocks()` big. **The aim line is a line**: a stroke in
every screen cell it crosses (`-` `|` `/` `\` by the way it leans), bold, white and gold
running out along it, a `+` at its end, eight cells long while you aim and as long as the shot
is hard with the meter going. It was a dot every half cell on felt that is itself dots, and the
owner could not make it out.
