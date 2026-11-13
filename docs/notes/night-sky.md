# The night sky

The city is always at night, so the sky is the one thing you look at that is not made of buildings.
`night()` gives each night its own character off a hash of its number — clarity, the moon's phase and
altitude, whether the milky way is up and at what tilt, how warm the starlight runs, how many
meteors. Same night whenever you come back to it, and nothing like the next one.

Two things about it are worth keeping:

- **A star has to clear every roof in its column, not the nearest one.** `draw_walls()` returns
  `wall_top` for the *nearest* wall — which is what occlusion wants — and a fourth array `sky_top`
  holding the highest roofline of anything in the column. They differ the moment a tall building
  stands behind a short one, which is most of a city, and the sky wants the second: using `wall_top`
  drew stars straight into the part of a far tower showing above a near roof.
- **The waterfront draws the city first and the sky around it.** Stars-then-buildings looks
  equivalent and is not: `blit()` leaves blanks alone, so every unlit window becomes a hole with a
  star in it. The silhouette is what a star must clear, not the lit parts of it.
- **Stars go on visible cells, not over the hemisphere.** The first pass scattered them by bearing
  with a random altitude, and from a street that put five in six behind a building: you got one or
  two stars and no sense of a sky at all. They are keyed on `(bearing, row)` instead, which still
  pins them to the compass so they hold still while you turn — there is a test that turns the camera
  and checks not one of them moved.
- **Most of them are faint, and there are fewer than there were.** The sky was reported as "too
  distracting and too much": measured, a clear night with the milky way up was a seventh of
  everything above the roofs, and a fifth of the stars were bright. `STAR_RATE` and `BAND_RATE`
  are half what they were and `STAR_TIERS` makes nine in ten `.` or `'` — a typical night is now
  under 2% of the sky, the clearest under 7%, and one star in ten is bright. A sky where every star
  is bright reads as static and the bright ones stop counting for anything. The colour
  works the same way: mostly grey, a few warm and a few cold, and the milky way in its own dim blue.

Clarity is the whole range from 0.22 to 1.0 with a median around 0.43, so a properly clear night is
worth staying out for and most nights are not one.

**Cloud comes and goes on its own.** `cloud_cover()` is three slow waves on their own periods, like
the rain's, and rain and snow raise it to cover the sky as they come; the sky is
`clarity * (1 - cloud)`, so it goes by degrees rather than at a threshold. Of the time it is not
raining the sky is clear about three quarters of it, cloudy a fifth, overcast one stretch in twenty
— `CLOUD_BASE` sets that, and it was half clear at first, which was "too often" — and the HUD says
which (`sky_word()`). Under cloud the stars and moon go, and nothing is drawn in their place. There
was a faint drifting texture of `~` and `-` for a while, meant as cloud lit from below; it was
reported as noisy, twice, and it is gone — a cloudy night is a night with fewer stars, which is what
one looks like. There is a test that a cloudy frame draws nothing the same frame held clear does
not. Natural cloud never hides the strange night — that sky is
lit by what is in it — but the held overcast does. `s` in the menu cycles the sky: as it comes,
held clear, held cloudy (a few stars through it), held overcast. The moon crosses through the night rather than sitting still, and at new
moon there is simply no moon, which is a perfectly good night in its own right.

`s` in the cheat menu cycles the sky (`_sky_mode`): as it comes, held clear, held cloudy, held
overcast. Held
overcast is a pitch-black sky — no stars, moon, milky way or meteors, from the street or the water,
and on the strange night nothing up there either, though the city still pulses to it. It is a sky
setting, not a weather: the rain, snow and lightning go on underneath it, and a strike still lights
the cloud from below. Held clear is how the star tests look at the stars.

`n` in the cheat menu steps to the next night. Nights are eleven minutes long, and waiting one out to
see whether the next sky differs is not a way to look at anything.
