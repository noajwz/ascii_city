# A yokocho is a kind of alley, not a part of town

It was a district for a while and that was wrong: a yokocho is not an area, it is *one lane*, the
same one-cell width as any other alley but lit and lined with places too small to have a front on
the street. `yokocho_at()` decides it per alley cell, keyed on the same run the alley itself is cut
into so a lit lane is a whole stretch rather than a few cells — about one alley in five.

Three things make it feel like somewhere rather than a gap between two buildings:

- **Lanterns strung across it**, wall to wall, by `draw_lantern_string()` — not hung off one facade,
  which is what a shopfront does. The wire sags in the middle and drifts, because a dead straight
  line of dots reads as a fence, and they only go over every other cell or the lane gets a ceiling.
- **Places you can see into.** A `pub` face draws its counter and the backs of the people at it
  through the window. Stacked in *rows* off the counter, not at true heights: half a metre between
  someone's shoulders and their head is a dozen rows when you are stood right outside, and they come
  apart into unrelated marks. One column a person, too, or a seat slot wider than a cell smears them
  into a row of Ms — the same trick the sign letters use.
- **Japanese neon over the door**, `draw_over_door()`, drawn in screen space with `put_wide()` so
  the characters sit side by side, stepping two columns at a time.

That means **what goes on a facade is not the district's business** when the facade gives onto an
alley. `face_kind()` returns `"road"`, `"yokocho"` or `None`, and it is passed around in place of the
old is-it-lit boolean, because a yokocho is lit but is not a street and must not look like one — its
walls take the red palette whatever district they stand in. A yokocho running behind a residential
block turns those back faces into bars, which is exactly what one is, so a test that "residential has
no neon" has to count street frontages only.
