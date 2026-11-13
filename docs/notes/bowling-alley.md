# The bowling alley

One lot in `BOWL_ODDS`, on a street, not in the residential or financial parts of town or a park, held
low (`b["bowling"]`). `draw_bowling_column()`: dark, two bands of neon chasing in opposite directions,
glass along the bottom; `draw_bowling_front()` the BOWLING board, a neon pin and a ball. Walk in
(a venue; no fee at the door, `BOWL_COST` a game). `k` in the menu stands you in a doorway.

**It is really played.** `Bowling` is ten frames, in inches, on a lane of real size: `step()` moves the
ball and the pins as circles at `BOWL_STEP` and `_hit()` knocks them apart, and a pin that has been hit
has fallen. So a strike is what a hooked ball in the pocket does and a split is what one on the nose
does, and nobody decides. Measured over random throws: about 6 pins, strikes 2%. It costs well under a
millisecond a frame. `bowl_scores()` is the scoring, and it waits for a strike's two balls and a
spare's one, as the rules do. Curses sees no key go up, so nothing asks you to hold one: `a`/`d` line
you up, `p` stops the spin meter, `p` the power meter. The hand wobbles a little (`bowl()`'s caller),
or a good line would strike for ever. `x` stops playing; `s` only walks you out when you are not.

`render_bowling()` is three lanes going away from you under the black light. The last stretch to the
pins is drawn longer than it is (`place()`): true to scale, four rows of pins land on one row of the
screen. Big windows go by the one system: the maths grows, the pins and people `_bar_sprite()` them,
the name, the sum and STRIKE in `_blocks()`, and the frames and meters stay plain.
