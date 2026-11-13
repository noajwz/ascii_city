# The karaoke bar

One lot in `KARAOKE_ODDS`, on its own hash (salt 2901) after the bowling alley's, with the same rules
for where (a street face, not the residential or financial parts of town or a park), held at
`KARAOKE_H` (`b["karaoke"]`). `draw_karaoke_column()`: a chasing band under the roof, the private
rooms upstairs a window a bay, each lit its own colour and the colours going round slowly, now and
then somebody at the mic; glass speckled with neon at street level. `draw_karaoke_front()` is
KARAOKE over the door, big within `ARCADE_BIG`, a letter at a time lighting, the name under it, a
neon mic and notes rising. A taxi destination ("the karaoke bar"), and ctrl-a `a` for the checks.

**It is really sung.** `Karaoke.start()` puts a note on every word of the song, a beat apart, each
line `KARA_LINE` beats, in one of three lanes by the song's `tune`. `j`/`k`/`l` is a press in a lane,
judged against the nearest waiting note there (`KARA_GREAT`, `KARA_GOOD`): one key a note, since
curses sees no key go up. A press with no note near is "flat" and breaks the run. The score is out
of a hundred, `kara_verdict()` the machine's word on it. `KARAOKE_COST` a song, `n` the next song
in the book, `x` stops one; `s` walks out when not singing. While a song is on, `j` is a note and
not the mystery's clue line.

`render_karaoke()`: a disco ball throwing spots, neon chasing along the ceiling, the screen filling
the room down to the couch, two friends swaying to the beat (cheering on a run of five), you at the
mic. Notes come in from the right at `KARA_SPEED`, a word cut short where the next note in its lane
starts so they never run together. Big windows by the one system: the speed and the sprites by
`big_scale()`, the name and the score in `_blocks()`, the words plain.
