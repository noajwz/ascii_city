# Tunnels

The first thing in the city with a roof over the road. A tunnel is a stretch of avenue under a road
deck `TUNNEL_H` up (`tunnel_run()`): **short** ones, two cells in the middle of a block clear of the
cross streets, one avenue-block in `SHORT_ODDS`; and **long** ones, from the middle of one block to
the middle of the next, only where the cross street between was built over — so nothing crosses
them, because a tunnel with a side street opening off it halfway is not a tunnel. Not on the
elevated's avenues, the big bridge's, in the woods or over water.

Four pieces make one, and the ceiling is the one that changed the renderer:

- **The ceiling** is solved per screen row the way the ground is — every row above the horizon is
  one distance to a plane at `TUNNEL_H` — and drawn where that point is over a tunnel and nearer
  than the wall in its column: blank, with a joint every two units. It also goes into `v.ceiling`
  with its distance, and **`put_cell()` will not draw anything further into those cells.** That is
  the general fix, and it took two goes: drawn last, the ceiling painted over a walker inside the
  tunnel in front of you; drawn before the rain, the rain past the far mouth painted straight over
  it. It is drawn right after the ground now and acts as depth for everything after.
- **The lining.** A face whose front cell is a tunnel is drawn as its building as usual and then,
  from the road to the deck, overwritten with dark tiles, grime and the odd tag — above the deck the
  building carries on as itself. Nothing is hung on it: no signs, smokers or bulbs.
- **The headwalls** — brick over each mouth, a railing on top — drawn only from their own outer
  side, or they showed through the ceiling from inside.
- **What is in it.** Under a short one, a fire in a can against one wall with three people round it,
  a blanket, a shopping cart, flames and sparks going up, and its light on the road through
  `collect_glow()`; the HUD says `~ a fire going under the road ~` near one. A long one is lit down
  the middle (`TUNNEL_LAMP`) and otherwise bare: it is being kept for something.

No rain or snow falls in a tunnel and no snow lies there. `[` and `]` in the menu stand you on the
avenue short of the mouth of a short or a long one, looking in. The nearby tunnels are found once a
frame (`v.tunnels`) before the walls, so the side-wall check is skipped wherever there are none;
they cost about 0.3 ms a frame on an ordinary street.

`[` and `]` are not on the panel any more (see *The cheat menu*); `find_place()` still finds
tunnels for the tests.
