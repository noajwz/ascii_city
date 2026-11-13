# The elevated line

One avenue in `EL_EVERY` carries a steel viaduct down its middle (`el_span()`, keyed on the
avenue index and only on avenues that actually exist). It is all world points: columns on both
kerbs every `EL_COL` units, cross beams, two girders along the top and two tracks on them, and a
station every `EL_STATION` cells with a canopy and lamps. Points are laid along z only over the
stretch in front of you — an avenue is endless and a column of points down it is not free.

Trains run both ways, `EL_CARS` cars of lit windows, headlights, and a spark underneath now and
then, at `EL_SPEED` with `EL_SPACING` between them on a track; position a function of time, as
everything that moves here. Side-on is where they read best — roof line, a row of windows, the
deck under them; head-on from under the line they are a pair of headlights coming at you through
the steel. Within earshot the HUD says `~ a train overhead ~`. The line stops where the avenue
does, at the woods and the headland (`el_runs()`).

On the waterfront it is a dotted track across the middle layer — its ties on that layer's
parallax, so it sits in the town rather than on the glass — and every 48 seconds a train slides
across the screen along it, one way then the other, drawn before the reflection so it lies on
the water too. The train itself is in screen space, not on the layer's parallax — a simplification;
putting it on the parallax would make it slide with the town as you pan, which it does not yet. ctrl-a `=` in the checks' menu
stands you under it, on the pavement by the columns, looking along.
