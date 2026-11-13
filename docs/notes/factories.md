# The factories

**Placed, like the woods, not picked**: `ZONES` holds the industrial zone's place in every
`WOODS_TILE` square — between the river and the woods, a wandering rectangle (`zone_home()`,
`zone_depth()`, cached) — so adding it moved nothing that was already in the city; `district()`
returns `INDUSTRIAL` for its cells the way it returns `WOODS`, the street grid runs through it
as everywhere, and the landmark keeps clear of it. The district row is low rust sheds — `lo`
5.5, `hi` 9.5, sparse windows high up for the night shift, roller doors, bare bulbs and somebody
on a break — and **low on purpose**: at 7 to 13 the near façades took the whole sky in a street
and the chimneys were 20 cells of a frame; at 5.5 to 9.5 they are 80 to 110.

- **Chimneys** (`chimney_at()`, one shed in `CHIMNEY_ODDS`, found per block and cached like the
  sky decks' beacons, `near_chimneys()` out to 260): world points, a banded tapering stack 22 to
  34 over its roof, filled dark so nothing shows through, the lip glowing orange, a red light on
  top. Its points are spaced by distance, no closer than a cell on screen — at a fixed half unit
  a frame with forty stacks in it took 56 ms. Two in three are going: smoke rolls off downwind,
  lit from below where it comes out, thinning to haze, and only within 170 — it filled the sky
  when every stack in reach smoked.
- **Sodium lamps** (`near_ind_lamps()`, `v.ind_lamps`) at the kerb every few cells of road, and
  their orange on the ground through `collect_glow()`.
- **A building site** (`zone_site()`: three cells by two, no road in it, near the middle;
  `site_at()` makes them open in `is_open()`): mud on the ground with lit puddles, a hoarding
  round it with KEEP OUT on it and a gap for the gate, a steel frame three storeys up and a
  fourth half done with work lights on it, two floodlights, and a yellow tower crane whose jib
  turns slowly with a girder swinging off the hook. `]` in the menu stands you on a road with a
  clear view of it (`probe()` — the first try had a building in the way).
- **Empty plots, fenced** (`zone_plots()`, `plot_at()`): the building site is the first of a
  zone's plots, and the rest are empty — one city block in three gets one, grown out from the
  middle of the block until it meets a road, as far as its size (`PLOT_SIZES`, up to six by
  four) lets it, so the big ones take most of a block. Placing them as random rectangles first
  found one plot in a zone: nearly every rectangle caught a road. Each has a chain-link fence on
  posts or a plywood hoarding, a gate on the road side with a sign on it (`PLOT_SIGNS`), weeds
  through the mud, and what was left there (`PLOT_JUNK`): a skip, a burnt-out car, tyres,
  pallets, a lamp that works now and then, a fire in a barrel throwing its light about. `}` in
  the menu stands you looking at the biggest one.
- **The old factory with the rave in it** (`zone_warehouse()`: a solid cell beside the site with
  a street front — it must be solid, the first one was an alley gap and had no door to walk
  into). `draw_warehouse_column()`: dark brick, rows of broken iron windows, a few of them lit
  from inside in the beat's colour (`warehouse_light()`, `WAREHOUSE_BPM`) and all of them by the
  strobe, paint on the brick, and a roller door stuck a third of the way up with the light
  pouring out under it onto the street. Near it the HUD has the bass line. It is a venue like
  the club's; `render_warehouse()` is inside: roof trusses and broken skylights, a stage of
  pallets with the DJ and the stacks, lasers through the smoke, and the crowd in three depths.
  Free; nobody is in charge. `[` in the menu stands you out front.

`9` in the menu stands you on a factory street, facing whichever way along it has the most stacks
at the end — in among the sheds the near walls hide the rest. (Fog moved to `#` and the
blackout to `&` to give the zones the digits after the districts.)
