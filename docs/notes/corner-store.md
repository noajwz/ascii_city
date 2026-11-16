# The corner store

Asked for on 2026-11-16: "A convenience store: a bright white interior against the neon outside."

**Where** (`store_in_tile()`, `store_at()`): at most one to a square of city `STORE_TILE` (18)
cells across, and one square in `STORE_ODDS` (3) has none - about three in five have one, a
store every couple of blocks. The square's hash picks a cell, and the nearest front round it that
will do is the store (`_store_fits()`): an ordinary building's face (none of the special ones -
casino, club, tower, cinema, diner, arcade, bowling, karaoke, minigolf, temple, exchange,
warehouse, Pokemon Center, landmark - nor a tree, a park, the coast's cells or a ramen front) on
a proper street (`road_at()`, not an alley), tall enough for a shop on the ground floor. Cached
per square, like the sky decks' beacons. A name from `STORE_NAMES` (made up) and a stripe colour.

**From the street** - the point of it - the whole ground floor of that face is one window
(`store_window()`, in the wall pass after the diner's): **white, by reverse video**
(`SNOW | A_REVERSE`, a white cell with the glyph dark on it) - the one white thing in a street of
neon. Across it shelves (an edge every 0.42 up) with what is on them as cells of colour (the
neon colours, reversed), the glass door in the middle, the counter at one end with the clerk dark
behind it. Over it a box sign in screen space (`draw_store_sign()`, the diner's way): the name in
black on white, a stripe of the store's colour under it, OPEN 24 HOURS under that. White light
spills on the pavement (`collect_glow()`). In a blackout it is dark like everything else: its
white is blank cells, which `unpowered()` leaves alone, so the window is just not drawn then.

**Inside** (`render_store()`): the room is a box cast once per window size (`_store_room()`,
14 ms at 300x90, then 2.5 ms a frame): every cell a ray from your eye into a 6 x 2.7 x 9 room -
floor tiles, the ceiling and two rows of tubes (one now and then flickers), **the front window
down the left: dark, onto the street, with HOTEL, BAR and RAMEN in neon through it, the rain
when it is raining and a car going by**, the counter and the cigarettes down the right, a
gondola of shelves, the fridges at the back with their bottles in cold light. Everything else is
white: a bright room, and the dark window is the contrast that was asked for. The clerk is
behind the counter (`STORE_CLERK_ART`; on a big window `STORE_CLERK_BIG`), filled in or the shelves
showed through his face, and yawns now and then. `* ding-dong *` when you come in.

**Buying**: `1`-`5` (`STORE_ITEMS`, `store_buy()`): onigiri, hot coffee, cup noodles, ice cream,
a lotto ticket scratched there and then (`STORE_LOTTO`: one in eight wins $5, one in a hundred
$100, one in two thousand $1000). What you bought is in the bag along the bottom for the visit.
The clerk says something, never much. `x` walks out. `z` for the big screen: the name in block
letters on a big window, nothing else changes - the room is worked out at the size it is.

`m` on the panel (AND THE REST) stands you across the pavement from the nearest one; a few steps
forward is the door. It does not change the street walk's cost: 17.0 ms against 17.2 before, at
300x90.
