# The landmark, and the party on its roof

One skyscraper a whole city block wide in every `LANDMARK_TILE` square — 48 tiles in 49 have one —
an Art Deco wedding cake: a broad base `LANDMARK_BASE` high round the edge, the tower set back from
it to `LANDMARK_H`, over every sky deck in town, and a spire over that with a red light. A
`LANDMARK_NAMES` name over the lobby with ROOF PARTY TONIGHT under it in the beat's colours.

**It is the first building that is more than one cell.** `landmark_of()` picks a block per tile —
away from the river, the woods and the parks, wide enough, and held against its south and west
streets so the lobby (`lobby`, the middle of the south edge, door `+z`) fronts a road — working out
the block's bounds from `_is_road()`, which is pure, so asking it from inside `is_open()` is safe.
`is_open()` says every cell of it is solid, alleys and all, and `lot()` gives each cell the base's
height or the tower's by `landmark_ring()` and marks it `landmark`; the raycaster does the rest,
the tower showing over the base the way any tall building does over a short one.
`draw_landmark_column()` is pale stone with a pier up every bay, lit windows between, lights along
every roofline, and the tower's top floors floodlit in a colour that changes every eight seconds.

**The roof is the first one you walk about on**, and that needed two things the sky decks never
did. They stand you at the parapet, which hides that the renderer has no floors; from the middle of
a 25-unit roof the street a hundred units down showed straight through. `draw_party_floor()` draws
the floor the way the ground is drawn, per screen row: where each column's ray leaves the roof the
parapet goes up, and nearer than that is floor — a dance floor of tiles lit on the beat. And from
inside it the building's own cells were walls in front of everything on the roof, so `View.skip`
holds the landmark's cells and `draw_walls()` passes over them. In `main()` the lobby is a lift
like a sky deck's, `kind: "party"`; at the top you step out of the lift hut and `roof_x`/`roof_z`
walk you about inside the parapet, and walking back into the hut (`lift_hut()`, forwards or
backwards) takes you down.

On it (`draw_party()`), at `PARTY_BPM` off `party_light()`: the booth at the north end with the DJ
and the stacks, a lighting tower at every corner with a head on top, a crowd of 22 on the floor
going up on the kick a fraction of a beat apart, and the strobe the last bar of every eight. Its
lasers (in `draw_spire()`) fan out from the booth over the city, nearly level, a new colour every
bar — seen from across town at 250 units from about half the streets round it, and from nearer
not at all, because they are over the top of the screen: the street camera does not tilt, which is
the sky-deck crowns' trouble again. ctrl-a `p` in the checks' menu stands you outside the lobby. About 9 ms a
frame on the roof at 110x34, 19 at 240x70.
