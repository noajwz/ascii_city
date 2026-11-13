# The arcade, big

The second screen on the big-window system. `render_arcade()` puts the arcade's name up in bigger
block letters (`k` columns by `k - 1` rows a dot, a colour a letter) and draws each cabinet with
`draw_cabinet_big()` at `cab_size(k)` - the screen `k` times over, its demo blown up with
`_blow_up()`, the game's name and COMING SOON / INSERT COIN left in plain letters so they stay
words. `arcade_order(arc, width, height)` counts the cabinets that fit at that size, and `main()`
passes it the height, or the cabinet you pick and the one you get would disagree on a big
window. Playing (`render_game()` hands over to `render_game_big()` when `game_size(k)` fits):
the playfield every cell a `k` by `k` block of itself - the games themselves are untouched and
still draw their 40 by 16 - the name and SCORE / HI in block letters, GAME OVER across the
middle in block letters on a cleared band with the reason under it, the controls in plain
letters. At scale 1 the room and all six games are frame for frame what they were.
