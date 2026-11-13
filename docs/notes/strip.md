# The Strip

The third placed zone in `ZONES`, at the edge of every tile clear of the woods, and a different
shape from the others: not a wandering rectangle but a boulevard. `strip_at()` is twelve cells
across and `STRIP_HALF` either way along z; the middle four are the boulevard (`strip_road()`,
which keeps the city's cross streets through it, so the hotels come in blocks and you can get
in and out), and the four either side are hotel — `is_open()` says no to all of it but the road,
and the avenues that run into it stop at the hotels. `district()` gives `STRIP`; `lot()` makes
every hotel cell part of one hotel per side per block (`strip_hotel()`), the same height (28 to
56) and name (`STRIP_NAMES`, made up) right through it, and gives the cell at the middle of its
frontage a casino — door on the boulevard, so **every hotel is a casino you walk into**, the
whole room and all six games. The doors faced away from the road at first: `FACES[0]` is -x, not
+x, and that is worth remembering.

`draw_strip_column()` is the façade: every window gold, a band of bulbs chasing round every
fourth floor in the hotel's own colour, neon trim up every bay, the crown lit solid. Nothing
hangs on the walls (`flat`, `hung` 0): each hotel's sign is a **pylon at the kerb**
(`strip_signs()`, `draw_strip_sign()`), the name in the big font in the hotel's colour within 55
units and on a lit board further off, bulbs chasing round it, flashing now and then — screen
space, for the marquee's reason. Down the median `draw_strip_median()` alternates **palms**, lit
from below, and **fountains**: a pool with a row of jets rising and falling in a wave. And
`draw_strip_traffic()` cruises two lanes each way, a car in most slots and a stretch limousine
now and then, headlights coming and tail lights going, never through you. `:` in the menu stands
you at one end in the middle of the boulevard, looking up it.

**The fountain show.** In front of the hotel at the middle of the east side, its first two cells
are a lake (`strip_lake()`, `fountain_rows()`) — in `water_at()`, so it is water the way the
river is: open to see across, not to stand on, and the ground pass and the reflection lay the
hotel and the show on it with nothing told. Every `FOUNTAIN_PERIOD` seconds, for
`FOUNTAIN_LEN`, `draw_fountains()` puts two rows of jets up out of it, lit blue from below, white
up the column, spray at the top, and `fountain_heights()` is the choreography: the lights coming
up, the jets rising together, a wave running down the lake, the rows sweeping side to side
against each other, a chase, the shooters going up forty units on the beat with mist hanging
after them, the finale, and down. Points are spaced by distance, the chimney's lesson. The HUD
says when it is on and when it is about to be. `(` in the menu stands you across the boulevard
facing it and shifts the show (`_fountain_shift`) to start in three seconds, the way the rave is
started when you ask for it.
