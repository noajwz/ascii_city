# The skyline is a waterfront

Three parallax layers of chunk-generated buildings standing on the far bank, and the water in front
of them. `dens` falling away with distance is most of what separates the layers — the far bank is a
dim shape, the near one is a lit building — and `gap` widening as it comes forward is what keeps the
near layer a row of towers with sky between them instead of a wall across the bottom. Both were the
fix for a view that had become an unreadable mash of glyphs with no silhouette in it.

The street has the matching pair. `road_span()` gives back where a road starts and how wide it is,
not merely whether a cell is one, and that is what lets `draw_ground()` find the middle of a street
to paint a dashed `'` line down — on the wider ones only, and never through a junction, which is how
it works outside too. With the kerb already marking where pavement meets road, that is enough to
tell street from building at a glance even with the neon going.

`reflect()` mirrors everything above the waterline into the water. An ASCII reflection lives or dies
on being broken up: same glyphs, displaced sideways by a swell that changes with depth and time, and
thinned out with depth until it is gone in eight rows or so. Let it survive further down and it
stops reading as water and starts reading as the picture having been printed twice. Rain roughens
the surface, so the harder it comes down the less of the city you can read in it.
