# Parts of town

`DISTRICTS` is a table and `district_at()` picks a row from it. Everything a building is — how tall,
how lit, whether it carries neon and in which of the eight tubes, whether its frontage is strung
with lanterns — comes from that row, so a district is one line of data rather than special cases
scattered through the generator. `scale` multiplies the block's own base height and `lo`/`hi` clamp
it, which keeps a block's internal coherence inside a district's range.

The nine: **downtown** (the tall neon one, still the commonest), **residential** (low, banded with
balconies, no signs at all), **old town** (pitched roofs), **chinatown** and **market**
(lantern-strung, and restricted to warm tubes), **financial** (enormous, cold, and dark but for the
occasional whole floor left on), **docks** (low corrugated sheds, roller doors), **yokocho** (the
alleys are the point — signs and warm light down a back lane where everywhere else has a bare bulb
and the dark palette), and **park**.

**Height and window density are nearly useless as district markers, and finding that out took a
measurement.** From the street you see four storeys of frontage and hardly any roofline, and the
facade is 60–80% structure — corners, roofs, awnings, bands — with lit windows under a seventh of
it. So the things that actually separate a district are, in order:

1. **Its palette.** `wall_colour()` picks the family named by the district, and this carries more
   than everything else combined. Amber housing against cold blue glass against rust-lit sheds is
   obvious at a glance in a way that a different window *glyph* never is.
2. **Its structure** — `band` draws a line at every storey (balconies in Chinatown, ribbing on a
   corrugated shed), `roof` varies the roofline, `ground` and `gap` decide what the shopfronts are
   made of, and `whole_floors` is the financial district's alone: a glass tower is not lit window by
   window, it is black with one floor on because the cleaners are there. That one is keyed on
   `b["block"]` rather than the cell, or the lit floor is five metres wide and stops reading as a
   floor at all.
3. **Its props** — lanterns, and `alley_lit`.

There is a test for exactly the thing that was reported, and it is worth keeping honest: a histogram
of what gets drawn on the facade, compared pairwise between districts. Measured on **glyphs alone**
the worst pair scored 0.08 — indistinguishable, matching the report. With the colour of each cell
included and the palettes in, the worst pair is 0.43 and the median 0.69. Count only the rows above
the horizon, or road, footings and rain — identical everywhere — swamp the comparison.

The grid of districts is offset a different amount on each row so the boundaries stagger like
brickwork rather than lining up into one seam across the city. Note that a district is 180 units
across and you can see 130, so from the middle of the financial district you will still catch the
neon of whatever is next door down a long street — which is correct, and worth not mistaking for a
bug.

**The park is the one that changes the world model**, not just its parameters: `is_open()` returns
true for park cells, so it is ground you walk on, except for the quarter of them that are a clump of
trees. Making a clump *solid* is what makes it free — the raycaster and the collision already know
what a solid cell is, and `draw_tree_column()` just draws it with no roof line, no corner and no
footing, its canopy height wandering along the clump so the top comes out ragged. Clubs and casinos
are barred from parks: the cell would be a clump of trees and would be drawn as one, so the venue
would exist and be invisible. Nothing is hung on a tree either — `draw_props()` skips tree lots,
because the alley's bins and bulbs were turning up against the trunks.

The parks are small and stay small. The big wood is a different thing — see *The woods*.
