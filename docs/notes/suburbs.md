# The suburbs

The other placed zone in `ZONES`, beyond the woods in every tile; `district()` returns `SUBURBS`
— one storey or two, warm windows, a pitched roof, nothing lit but the porch and the television.
**It has its own streets, and they curve**: `road_at()` asks `suburb_road()` in there instead of
the grid — a ring road just inside the edge, following its wobble, three streets winding along
x and three across, two cells wide; and through the edge band the city's own grid carries on in
to the ring, so every street joins up with the way in (a test floods from the edge and reaches
all of them). Deeper in, the grid is gone: under half its cells are still road, against all of
them anywhere else.

`suburb_rank()` is how far a cell is from the road: 1 is the front lawn along it, 2 where the
houses stand, every other cell so each stands on its own (`suburb_house()`), 3 the back gardens
with a tree in one in five (`suburb_tree()`, a solid cell `lot()` marks as a tree, so
`draw_tree_column()` draws it with nothing else learning anything). `is_open()` says yes to all
of it but the houses and the trees; the ground pass mows the lawns closer than a park and paints
no centre line down the curves; `face_kind()` calls a lawn a street, so a house faces over its
lawn the way a shop faces the road. No venues out here, no El, no tunnels, no walkers and no
traffic — the cars' trips need straight road the length of a few blocks, and in here there is
none, which is why the quiet came almost free.

`draw_suburb()` is what it is close to, from `v.suburb` (`near_suburb()`, within 48): a **white
picket fence** along every front lawn where it meets the road, pickets with points, a rail; a
gate in it up to each house, with a letterbox, and a wider gap for a drive where one house in
four has a car on it; and on each house the porch light (`porches()`, spilling on the lawn
through `collect_glow()`) and the blue flicker of the television in one window in three. Now and
then the HUD hears a dog. `0` in the menu stands you on a street in the middle, facing the way
it runs furthest before it bends.

**And two things you would not expect** (`suburb_eggs()`, one of each per suburb, found once).
**A lemonade stand at 3am** on a front lawn by the road, where the fence would be: a kid behind a
home-made sign, LEMONADE $1. Walk up from the road (`egg_points()`: where it stands, and where
you stand to be served, which is what `venue_at()` checks) and `render_lemonade()` is the close-up
— the house dark behind with its porch light on, the fence either side, the kid blinking over
the jug and the cups, and what the kid says (`KID_LINES`, unsettling). `p` buys a glass for a
dollar out of the wallet, and the thanks get stranger (`KID_THANKS`) until, at five, you live
here now; after that the kid just looks at you. `lemon` in `main()` counts them for the session.

**The stargazer**: an old man on a lawn between two houses with a telescope on a tripod. Walk
up beside him and `render_telescope()` is the eyepiece: a round field, its columns twice its rows,
stars in it, and the moon close up — craters, and the side the sun is not on in earthshine, in
the night's real phase — and then, on a `SCOPE_LOOP` from when you put your eye to it
(`scope_at`), it does something: comes into focus, a lander comes down on it and somebody gets
out, plants a flag and waves, a cow goes over it, and it winks. On the strange night a saucer
crosses it instead of the cow. Step back and it starts again. `;` and `?` in the menu, under
NIGHTS where there was room.
