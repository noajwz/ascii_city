# The fortune teller

Asked for on 2026-11-16, "with some quotes", on one condition: "I do not want to waste real
estate space on them. They may not occupy a building." So she is not a building and not a
shopfront: **a card table on the pavement** in front of an ordinary building, under a striped
canopy on two poles, which the building behind does not know about. Whatever that building was
- its windows, its door, the smoker outside it - it still is.

**Where** (`teller_in_tile()`, `teller_at()`): placed the corner store's way, by squares of city
`FORTUNE_TILE` (26) cells across, and one square in `FORTUNE_ODDS` (2) has none - about one in
two has one, five times rarer than a store. The square's hash picks a cell and the nearest front
round it that will do is hers (`_teller_fits()`): an ordinary building's (`plain_front()`, and
none of the tower, cinema, diner, warehouse, Pokemon Center, landmark, Strip, airport,
university), on a proper street (`road_at()`), not over water, a tunnel, the woods, the coast or
a park, and not a store's or a ramen counter's front. She sits `FORTUNE_OUT` from the wall at
one end of the front (`u` 1.3 from the corner), whichever the bin is not at, or the other end
or the middle if a corner leaves no room to stand in front of her (`can_stand()` keeps 1.15 off
any wall, so the table's own spot is only asked to be open ground, `dry_at()`). Cached per square,
and nothing of it is in `is_open()`'s or `road_at()`'s path: the street only asks
`teller_at()` in `draw_props()` and `collect_glow()`, one dict lookup per face, like the store.

**From the street** (`draw_teller()`): one sprite, `FORTUNE_STALL`, drawn in layers over the
same box the vending machine's way - all of it dim, then the canopy in her stripe (magenta,
purple or red, `tone`), the cloth, the ball (purple, now and then cyan) and the candle, which
flickers. Over it a painted board in screen space (`draw_teller_board()`, the store sign's way)
- FORTUNES, `* FORTUNES *` nearer, the price under it close up - so she is found from across the
street. Her glass throws a little purple on the pavement whatever the weather. **She is lit by
the candle and the glass, not the mains**, so she is not in `LIGHT_PROPS`: in a blackout she is
the one light on the street.

**At her table** - walked up to like a door (see the walk-in rule): `venue_at()` returns
`"fortune"` within `0.7 * CASINO_REACH` of a point 1.2 in front of the table. The hurry rule and
`same_venue()` apply as for every door. It is in `FEES` ($5): the first reading is paid sitting
down, and broke, `render_turned_away()` has her lay a hand over the glass. `told` in `main()` is
the reading (`new_reading()`): made fresh each time you sit down, so up and back is a new one.
`p` (or enter) asks again for `FORTUNE_COST`, not while she is still looking. `x` leaves.

**The screen** (`render_fortune()`): inside the tent, the cloth all round in folds with moons and
stars on it, the canopy's stripe along the top, her name over her (`FORTUNE_NAMES`, made up), her
in her hood (`FORTUNE_HER`; she blinks) with her hands round the glass. The glass is worked out,
not drawn: a circle `3 * k` rows across, its mist turning, fast for `FORTUNE_LOOK` seconds while
she looks into it ("she looks into the glass..."), slow after. The candle on her left, the card on
her right, face down until the look is over and then turned (`FORTUNE_CARDS`: the old cards and a
few the city added - THE TAXI, THE LIGHTHOUSE, THE RIVER, THE NEON, THE RAIN), its name on the
cloth under it. Then she says it, `FORTUNE_TYPE` letters a second, in quotes, and "that is all I
see."

**The fortunes** (`FORTUNES`) are the feature: about fifty, in the city's deadpan voice (the
vending machine's lines are the register), most of them about the city - the river, the one door
that opens, the club's bouncer, the blackout, the aurora, the turtles' pizza, the fire escapes,
the drone show, the stock exchange. All original, all ASCII, none attributed to anyone. She does
not say the same thing twice in a session till she has said them all (`_fortune_deck`, shuffled
by the clock at first use) - for the session only, nothing saved.

**Big windows**: on the one system (see CLAUDE.md, Big windows). Her, the candle and the card
are `k` times over, the glass is redrawn bigger, her name goes in `_blocks()`, what she says and
the card's name stay words. `z` is in the venues' `z` condition (`told is not None`). Under
50x18 it is two lines of words; at 80x24 the whole of it fits.

`"` on the panel (NIGHTLIFE, with the lemonade stand and the stargazer: AND THE REST is as
long as an 80x24 panel allows) stands you across the street from the nearest, facing her table
(`_fortune_spot()`); a few steps forward and you are sat at it. `"` was free on the panel (the
checks' hidden menu uses it for the library, behind ctrl-a, which is a separate list) and has no
case twin.
