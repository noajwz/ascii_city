# The street view is a grid raycaster

It did not start that way: when you could only walk up and down one avenue, the facades were two
planes at fixed `x` and a column could solve directly for what it saw. Free turning killed that.
`cast()` now runs a DDA over cells of `CELL = 5.0` world units, in cell units so the arithmetic
stays the standard form, and returns the walls a column meets nearest-first. Because the ray is
built as `dir + plane * cam`, the distance that falls out is already measured along `dir`, so
there is no fisheye to correct at the edges.

- **No depth buffer.** Three per-column arrays — distance, top row, base row — are the whole of the
  depth information, because a facade is a vertical plane. That is why the sky is drawn *after* the
  walls: an unlit window is a blank cell, so `wall_top` is the only thing that knows a building is
  in the way, and `hidden()` is the test every prop, drop and reflection uses.
- **Casting does not stop at the first wall**, because a tall building behind a short one still
  shows over its roof. Hits are drawn near-first, each clipped to the rows above everything already
  drawn, and the loop breaks once the cover reaches row 0.
- **A ray that hits nothing** is looking out of the city down a cross street. `draw_sky()` gives
  those columns a taller haze silhouette; without it the vanishing point is a hole.
- A horizontal line on a facade is a **slope on screen**, so roofs, awnings and footings go through
  `facade_line()`, which fills from the previous column's row to this one's. One cell per column
  instead and the line breaks into dashes.
- **The roofline gets its own colour**, brighter than anything else on the building, through
  `roof_colour()`. It used to take the same near-black trim as the awning and the balcony banding
  below it, which on a *low* building — the only kind whose roof is on screen at all, since a tall
  one's is off the top — meant the top edge lost to its own balconies. It fades in one step rather
  than dropping straight into the fog, because the rooflines you can actually see are the
  middle-distance ones. And no district's roof glyph may be the same mark as its own banding, which
  is asserted: Chinatown's `~` upturned eave exists because its balconies were already `=`.
- **A tower's dark windows are drawn, faintly.** Reported: "hard to make out a skyscraper because
  of the night sky". Measured first, and it was not the outline — 87% of the cells where a tower
  meets the sky already had a corner bar. It was the face: an unlit window was a blank cell, so a
  tower with few lights on was black with scattered points, which is exactly what the sky is.
  Unlit windows on buildings `TOWER_GRID` tall and up are now a `.` in the darkest grey, on the
  window grid — regular, which stars never are. Only on the tall ones: a low building is outlined
  by its own roof, and putting the same grey dots on everything made the districts measurably
  more alike (the docks/Chinatown/financial pairs dropped under their 0.40 bar).
- **Three lines make a building read as a building**: the roof, the awning over the shopfronts, and
  the footing where the wall meets the ground. The footing is the one that does the most work and
  was the last to arrive — with enough neon and lit windows in frame the eye stops being able to
  tell where a building stops and the street starts, and a line along the bottom settles it
  instantly. It is drawn last in the column so nothing paints over the join, and it is `CURB`
  rather than the building's own trim, which puts it in the same visual language as the kerb: this
  is ground level, everything below it is street.
- **Corner bars are only for real corners.** Every cell is its own building, so a naive "the face
  changed, draw a bar" test puts a picket fence down every street. `draw_walls()` first checks
  whether the column to the left was the building *next door on the same plane*; that is a terrace,
  and the step in the roof line is the only edge actually there.
- Windows get the middle of their bay or a near facade smears into horizontal stripes; a flat sign
  letter gets exactly one column, the first of its bay, or the word stutters as `CCCLLLUUUBBB`.
  `draw_hung_sign()` lays its letters out **in rows, not world units** — spacing them by a true
  height makes two of them round onto the same row as the sign recedes, and a HOTEL with the T
  missing is worse than one slightly the wrong size.
- **A painted sign has to be read left to right on screen, and `u` does not run that way.**
  `cast()` measures `u` with +z along an x-facing wall and +x along a z-facing one whichever
  side you stand on, which is right for two faces and mirrored for the other two — OPEN read as
  NEPO on every building whose front faced -x or +z, and nothing else on the facade noticed,
  because a row of windows reads the same both ways. `sign_u()` flips it for those faces, and it
  was found by looking at a screenshot, not by any test: the test came afterwards.
- A projecting sign hangs **perpendicular to the wall**, and its two edges are projected as world
  points rather than stepped out in screen columns. Framing it in screen space makes it a billboard
  that turns to face you wherever you stand, so walking along the pavement swings it out into the
  road and it reads as something you walked straight through. Done properly it foreshortens to a
  strip when you are square in front of it and opens out as you come along the street — which is
  when a sign like that is meant to be read anyway. Drawn edge-on the two sides land in the same
  column, so the frame is suppressed rather than burying the letters behind itself.
- **One sign per frontage.** Reported as "too many lights to make the buildings out". In
  Chinatown a five-metre shopfront could carry a flat neon, a hanging sign and a string of
  lanterns at once, and hanging signs alone were 84% of the lit cells in those streets. A face
  with a hanging sign now drops its flat sign (one in five keeps it) and its lanterns (one in four
  keeps them), decided off values already drawn so nothing else moves; Chinatown hangs signs on
  half its frontages instead of 85%, the market a third. Past `SIGN_LIT_FAR` a hanging sign is
  drawn in its unlit tube colour, so the near ones stand out and the far end of the street goes
  quiet. Measure "lights" as the *lit* tube colours and bulbs only — counting the dark tube colour
  as a light made the first measurement say nothing had changed.
- **A sign hangs from its top and reads downwards, so where it ends is what matters.** Constraining
  the top alone guarantees nothing: a quarter of them used to finish below eye level and one in
  thirty ran into the pavement. `SIGN_CLEAR` is the floor the last letter has to clear, and a
  building too short for the whole word does not get a sign at all (which costs about 1% of them).
  There is a ceiling too — hang it anywhere in the building's height and every sign on a tall block
  ends up in the sky where nobody in the street is looking.
