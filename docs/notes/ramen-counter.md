# The ramen counter

The third way into a building. **One yokocho pub to a lit lane** is a ramen shop
(`ramen_at()`), and none within `RAMEN_APART` (60) of another. It was one pub in three, each on
its own hash - two a stretch, side by side or facing each other across the lane - and the owner
found them "showing up too many times and sometimes right across each other on a very narrow
road". Now each stretch of lit lane (`lane_run()`: the `LANE_RUN` cells an alley is cut in) puts
forward its lowest-hash pub (`_ramen_first()`), and `ramen_pick()` makes that one the shop unless
a nearby stretch's - round the corner, crossing it - has a lower hash still: about a third as
many as before, in two lit stretches in five. Both are cached per stretch. From the lane it says so: the
sign over the door reads ラーメン instead of the pub's usual word, a split red **noren** hangs over
the door, and steam comes out from under it. `venue_at()` treats its door like the casino's —
stand within `CASINO_REACH` and `render_ramen()` draws the room round you.

**The front** (`draw_ramen_front()`) is made to be found from down the lane, and all of it is
steam and red light: a **neon bowl** over the name — red tube, an orange band round it, chopsticks
lifting and dipping with yellow noodles swinging off them, three strands of steam climbing off
the top in pulses — a **vent** at one end of the front puffing steam out over the lane, puffs that
grow, rise faster as they go and thin from white through grey to haze, more steam **rolling out
under the noren**, a swaying red **lantern** each side of the door, and the cyan **ticket
machine** by it. Where it sits is set by what the camera can see: it cannot tilt, and from
across a five-unit lane nothing above about five is on screen, so the bowl is small and sits at
`RAMEN_SIGN_Y` just over the name, and the vent is at 4.1, not up at the roof — at the roof it
was a plume nobody standing in front of the shop would ever see. Down the lane, further off, the
plume is what you find it by. About 0.3 ms a frame.

Inside is the one room in the city that is **not on a beat**: the noren across the top, the menu
board with prices in yen and a lantern either side, the cook moving between two stock pots, the
others along the counter heads down and slurping on their own counts, and steam off everything.
You sit down to chopsticks; the bowl arrives `RAMEN_SERVE` seconds later — egg, nori, steam — and
the cook calls it. `seated` in `main()` is what remembers when you sat, keyed on the shop, so
walking out and back in is a new bowl. It is all ASCII inside: the room is drawn without the
`v.wide` bookkeeping, so the Japanese stays on the sign outside. ctrl-a `r` in the checks' menu stands you
across the lane from a shop, looking at the front — a step or two in is the counter — and a
second press finds another.
