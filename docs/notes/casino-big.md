# The casino, big

Zoomed out, a window can be three hundred columns across, and the casino was drawn for a third of
that: the wheel stopped growing at 42 columns by 10 rows, and the slot machine and the blackjack
table are fixed drawings, so on a big window it was an island in the middle. `big_scale()`
gives a scale of 2 on a window with room for two rooms (`BIG_W` by `BIG_H`, 150 by 44 —
so 300 by 88) and 3 on one with room for three; anything smaller is scale 1, and **at scale 1 the
room is exactly what it was** — checked frame for frame against the old code at five sizes up to
299 by 87.

At scale 2 or 3 `render_casino_room()` draws the banner in block letters (`_blocks()`, the 3x5
`BIG_FONT` plus `CASINO_FONT` for `$ @ * & %` and the suits), lets the wheel grow into the room —
with a rim and an inner cone (`RIM`) so a wheel that size reads as a wheel and not a ring of
numbers, and a little taller than the small one's flatness, or a tall window's bottom third was
empty — and puts the winning number and FAITES VOS JEUX in block letters. The machine and the
table are drawn again by `draw_slot_big()` and `draw_blackjack_big()` (`slot_size()`,
`table_size()` give their footprints, which the room's layout uses in place of `SLOT_W` and the
table's 40): the payline's three symbols big in their own windows with the rows above and below
small, the cards with their ranks in block letters and the suit in two corners, the money, the
win and the outcome in block letters. **Ordinary text stays small** — the paytable, the keys,
"dealer" — because a terminal cannot draw a letter bigger than its font, and a sentence in block
letters is four columns a letter. `z` in the casino turns the big room off and on (`_big_screens`), for comparing the two on one
window.

**Plinko, the races and High Flyer** scale too, each at the biggest scale that fits it in the
room (`kp`, `kr` in `render_casino_room()`) - in practice the room's. Plinko (`draw_plinko(...,
k)`, `plinko_tall(rows, k)`, `plinko_wide(rows, k)`, `plinko_title(k)`) spreads its pegs k times
both ways, puts PLINKO over it and the last win under it in block letters. The races
(`draw_races_big()`, `race_size(k)`) give each horse a lane five rows deep: its number in block
letters in its silks, name and odds beside it, and a three-row horse and jockey (`HORSE_BIG`)
galloping. High Flyer (`draw_flyer(..., k)`) was already as big as the room - its graph is drawn
from the space it is given - so only the words grow: HIGH FLYER, the multiplier (very big) and
FLEW AWAY in block letters, and the plane (`FLY_PLANE_BIG`). **Watch for `k` as a loop
variable**: `draw_plinko()` and `draw_flyer()` both had `for k in` loops, and once `k` was the
scale those loops overwrote it - the normal-size frame comparison caught it (balls in the wrong
row, the big plane at scale 1). They loop over `n` now. This
is the first screen of the scaling system described near the top of this file - follow that for
the next ones.
