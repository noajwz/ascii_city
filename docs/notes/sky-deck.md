# The sky deck

One building `TOWER_MIN` tall in `TOWER_ODDS` with a street front has a lobby — `SKY DECK` over a
lit revolving door, and a mast with a blinking red light on the roof that is drawn from 150 units
off, so you can find one from across town. It is made `TOWER_TOP` tall, over everything else in the
city: the first ones were often hemmed in by taller neighbours and the view from the top was the
side of the next tower.

**The roof is the real city, rendered from up there.** `View` carries `eye` (how high the camera
is), `reach` (how far a wall ray goes) and `depth` (how many walls deep it keeps casting); at street
level they are `EYE_Y`, `MAX_VIEW` and four, and nothing about the street changed when every
`EYE_Y` in the renderer became `v.eye` — the whole suite passed untouched before anything else
went in. On a roof the eye is seventy-odd units up, rays go `ROOF_REACH` (520 - at 260 the town stopped short of the
horizon), walls twenty-two deep, and
`draw_ground()` runs as far as the view does, because from that height the nearest ground on
screen is a hundred units away and the street's `GROUND_FAR` cut all of it. What you get is the
grid falling away under you, rooftops at every height, the river, the haze of the far city on the
horizon and the sky over it — about 19 ms a frame at 240x70.

Two things it took to make it read. **You stand at the parapet, not in the middle of the roof**:
`roof_view()` puts you `ROOF_STEP` out towards wherever you are looking, so you see over it and
down — from the middle, the parapet hid everything nearer than the next district — and turning
walks you round the inside of it. And **the parapet is solved per screen column**: each column's
ray leaves the roof square somewhere, the coping goes at that distance and the wall below it hides
whatever the city drew there. As world points, at arm's length a point every quarter-unit landed
five columns from the next and the rows between came out as stripes. A water tower and the mast
stand on the corners.

**The lift** (`render_lift()`) is the way up and down: facing the doors, they slide shut from the
sides, the indicator counts the floors with the arrow blinking, floor slabs go past the gap in the
doors the other way to the ride, a gauge on the wall shows the car in its shaft, and at the top a
ding and the doors open on stars; at the bottom, the lobby. `lift_times()` sets the pace from the
number of floors. In `main()` the lift is a state, not a room: walking into the lobby starts it,
nothing moves you while it runs, on the roof `a`/`d` look round and `s` calls it, and coming down
puts you back outside the door facing the street, a step beyond `CASINO_REACH` so it does not take
you straight back up. ctrl-a `^` in the checks' menu stands you outside a lobby; one step in and you are riding.

### The crown

The top `CROWN_FLOORS` of every sky-deck tower are a weather beacon, by the old rhyme: steady blue,
clear view; flashing blue, clouds due; steady red, rain ahead; flashing red, snow instead — and in a
storm, red and white as fast as it goes. `crown_light()` reads `sky_word()` once a frame into
`v.crown`, so every tower agrees, and the window loop in `draw_wall_column()` fills those floors
solid, every column, so it reads as one band of light rather than lit windows. The blue is its own
colour (`crown_blue`, 33, or plain blue on eight colours): nothing in the palette was blue.

**It cannot be seen from the street, and that was measured, not assumed.** The camera does not
tilt, and a top floor seventy units up only drops onto a thirty-row screen from further off than
`MAX_VIEW` follows a wall — zero of 192 street views around a tower saw it. From another sky deck's
roof it is everywhere: 28 of 32 views, every tower in reach telling you the weather. So the street
gets it at the door instead: SKY DECK over the lobby is lit in the crown's colour.
