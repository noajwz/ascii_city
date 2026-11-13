# The rooftop bar

One sky-deck tower in `BAR_ODDS` is a bar instead (`kind: "bar"`, a name from `BAR_NAMES`, and
`bar_yaw`, which way the bar stands; decided on its own hash in `lot()`, off the same towers, so
nothing else about the building or the city moves). From the street: a neon glass over the door,
ROOFTOP BAR and the name, one step in and the lift, `LIFT_FEES["bar"]`. From other roofs and the
plane it has no mast, but a string of warm bulbs round the roofline (`draw_tower_beacon()`). `s`
goes back down, as on any roof. `b` in the menu stands you outside; the sky deck's jump skips bars
(`_tower_spot(x, z, bar)`).

The roof is `roof_view()`, so the skyline is the real city with everything out there in it. Over it
`draw_rooftop_bar()` draws the terrace **in screen space but by bearing** (`bar_col()`), so things
slide on and off the side as you turn and hold still as they should: at arm's length, world points
come out as stripes - the parapet's lesson. A rail with the city showing through under it, a deck
that hides the nearest street, bulbs sagging across the top, and round you the bar at `bar_yaw`,
tables, heaters, a trio and some people at the rail (`BAR_SPOTS`). Straight behind the bar is left
empty: that is the view. Sprites are solid (`_bar_sprite()`: a blank inside a row hides the city).

`1`-`4` order, facing it (`bar_facing()`), off the wallet (`BAR_DRINKS`): `BAR_MIX` of the bartender
shaking it, then the glass on the counter and a line from `BAR_SERVED`. After `BAR_LIMIT` it is
water, free. Past two drinks the view sways, a very little, off `at_bar["n"]`: the tab is for the
visit and goes when you leave. **Big windows go by the one system**: the art `k` times over, the
name in `_blocks()` on its own board, the menu and what is said in plain letters, `z` in `main()`.
Don't put the name directly on the city: its lights ran through the letters.
