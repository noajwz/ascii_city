# Up the fire escapes

One fire escape in `CLIMB_ODDS` down the dark alleys goes all the way to the roof, and says so
with a drop ladder at the bottom (`climbable()`: a real alley face, a real escape on it, three
storeys at least). The roof is the sky deck's roof view with `kind: "escape"` — an aerial and a
chimney stack instead of the mast, and the top of the escape over the parapet — so everything
about seeing the city from up there came for free.

Two things it took. **You climb by walking into the wall at the ladder, not by being near it**
(`escape_at()` wants you within `CLIMB_REACH` *and* facing the wall): an alley is one cell wide,
so a trigger by distance alone would have had you halfway up a building every time you walked
down a lane. The HUD says `~ a fire escape: walk into it to climb ~` when you are near one. And
**only off a roof nothing near overtops** — every solid cell within two has to be no taller —
because the first ones put you face to face with the wall of a taller building across the lane.
That still leaves about one climbable escape every 65 units of alley.

`render_climb()` is the ride: face to the bricks, the wall scrolling down past you with a window
every storey and a light on behind one now and then, the iron stairs zigzagging across it, a
landing at every floor and the count in the corner; at the top the sky opens out over the
parapet. It shares `main()`'s lift state — the same ride, a different picture — and `s` on the
roof climbs you back down into the alley. ctrl-a `|` in the checks' menu stands you at the foot of one.

**The loft can be played with** (`at_loft` in `main()`, `new_loft()`, for the visit): `f` feed, the
flock flutters down and pecks at seed on the gravel for `FEED_LEN`; `r` lets them out, once round on
`FLOCK_LAP`; `n` sends one off, and `POST_TRIP` later it is back with a line from `PIGEON_NOTES`.
Each is only *when it was done*, and `draw_loft_visit()` works out the rest from the time. `loft_key()`
is what says no. You have to be facing it, near enough.

(The back of a giant neon sign, letters reversed, was tried too, and was not interesting enough.)

**Most of these roofs are plain, and that is the point** (the owner asked for it). One in
`LOW_ROOF_ODDS` has somebody's something on it, by a hash of the cell (`low_roof()`): a **pigeon loft**
that sends its flock round over the street on a lap of the clock; **washing lines** that sway harder
in the rain; or
**someone's garden**, with pots, tomatoes, two deck chairs, a string of bulbs and a radio. One roof
in `ROOF_CAT_ODDS`, of any kind, has **the cat**: on the parapet (`v.roof_edge`), and every forty seconds
it walks along it to somewhere else, a function of the time like everything that moves. You come up
facing what is there (`low_roof_yaw()`). `draw_low_roof()` runs in `main()` after `render_street()`,
in screen space by bearing with the bar's helpers (`bar_col()`, `_bar_sprite()`), so a far beam never
cuts across something at arm's length, and the big-window scale comes with them. The loft and the
garden stand on `draw_roof_floor()`, a wall and gravel: without it they hung in the air over the city,
and were reported as not looking great. Keep each scene together and big, not scattered. `r` in the menu goes
to the next kind round; `|` still finds any escape at all.

### Washing lines

The owner liked the washing on the low roofs enough to want it off them too. In the residential
parts of town, one street cell in `WASH_ODDS` has a line across it, building to building
(`wash_lines_at()`: both ends on a real building, under both roofs, at most four cells across, and
now and then a second a floor up); and one low building in `WASH_ROOF_ODDS` has one on its roof, on
posts, seen only from up high. Found per city block and cached (`washing_in_block()`), hash first.
`draw_washing()` is **world points, one screen cell apart**, so nothing bunches at arm's length: you
walk under it, buildings hide it, and it swings from the peg, most at the hem and more in rain. Set
low on purpose, 5 to 8 units: the camera cannot tilt, and from a little way off that is in frame. About
2 ms a frame on a street that has them at 300x90, nothing elsewhere. `h` in the menu stands you down
the street from one.
