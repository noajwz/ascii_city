# The big bridge

Once every `GRAND_GAP` cells along the river the channel opens into a **bay** and a suspension
bridge crosses it. `grand_avenue()` picks the avenue — the nearest one to a hashed spot that has
not been built over, so there is exactly one per stretch — and `river_span()` widens the channel
under it by a Gaussian bulge (`BAY_WIDEN`, `BAY_REACH`): a suspension bridge over a 35-unit
channel is a footbridge with pretensions, and 90 units is water worth spanning. No piers in the
bay; the bay is the bridge's. The crossing is forced (`bridge_at()` says yes for the grand avenue
whatever `BRIDGE_ODDS` said), and there is a test that you can walk over it to the far bank.

`draw_grand_bridge()` is all world points. Two towers standing in the water at 27% and 73% of the
span, each a pair of legs with the portal bracing between them that makes a suspension tower read
as one, in `EMBER_HOT` — the orange those bridges are painted; a red light on each top, blinking.
The legs stand `TOWER_OUT` outside the deck's edges, because the deck passes *between* the legs of
a real one, and with the legs on the deck edge the whole thing was squeezed into the avenue's
fifteen units. The main cables are three parabolas meeting at the tower tops (`_cable_y()`), drawn
dim, and it is the **bulbs along them** that draw the curve — which is what you actually see of
one at night, and the thing anyone would recognise it by. Suspenders every couple of units down to
the deck, lamps along it. It is drawn from `GRAND_SEEN` (340 units), because the towers are what
you see first.

**Where you can see it from is limited, and that is the city's doing, not the bridge's.** The
bank is not a promenade — buildings run right down to the water — so from beside the bridge you
are looking through a block. The views that exist are the avenue approach, where the tower stands
over the end of the street like a gate, and the deck itself, which is where ctrl-a `b` in the checks' menu puts
you: the bracing across the sky ahead, the cables coming down either side, the far bank beyond.
