# The temple, and the word of God

`TEMPLE_ODDS` on its own hash, a street front required, never in the financial district, and
`TEMPLE_H` tall whatever its district — low, so the rose window over the door is in sight from
across the road, which is the one view a street guarantees. `draw_temple_column()` is pale stone
with a buttress at every bay's edge and between them tall **pointed windows of stained glass**,
lit from inside by candles: panes in the city's neon colours with the lead between, flickering,
narrowing to a point at the top. The front comes up into a gable (the roofline is `/`, `^`, `\`
over the door face, and the column returns that higher roof, so it occludes properly). The middle
bay of the front is `draw_temple_front()`: the **rose window** — a ring of stone, twelve spokes of
glass turning their colours slowly, a gold eye in the middle — the arched door standing open on
candlelight, a candle either side, and the name over it (`TEMPLE_NAMES`). ctrl-a `*` in the checks' menu stands
you across the street from one, the way the casino's does; a few steps in is the door.

Inside (`render_temple()`): the vault, the pillars going away down the nave with stained glass
between them, pews either side of the aisle, candles along the altar — and on the altar a
terminal, on which `g` asks for **the word of God** — one word a press. It is Terry A. Davis's
oracle from TempleOS, done his way: the random number is the time since the last word was asked
for, in nanoseconds (`oracle["last_ns"]`, `time.perf_counter_ns()`), and `god_word()` is that
gap modulo `GOD_WORDS` — a list of the city's own, not his, each word once (it had duplicates,
which made "behold" likelier). It gave twelve words a press at first, a generator seeded with
the gap; that was asked to change "so it's truly random", and rightly: twelve words from one
seed are one random number's worth, the other eleven decided by the generator. Now nothing
stands between the moment you press and the word. Words build up into a verse; `GOD_PAUSE`
without one, or `GOD_VERSE` words, and the next starts a new verse. The last few verses stay on the screen, the newest bright. Free to go in; nothing to pay.

**The choir** (`draw_choir()`) stands on risers across the nave from the booth: two rows in white
robes, mouths opening on `CHOIR_BPM` a breath apart along the row, a director side on with his
hands going, ASCII notes (`CHOIR_NOTES`) floating up and fading — and over them, in gold on the
beat, **the last word the terminal gave, sung**, cut up by `syllables()` (hal-le-lu-jah, mer-cy);
until it has given one they hold a long a-men. Visual only: the standard library has no sound
but the terminal bell.

**The confession booth** stands against the side of the nave; `c` steps into it (`booth` in
`main()`, cleared when you leave the temple or jump). `render_confession()` is the inside: dark
wood, the lattice, the panel sliding back and the priest's shape behind it with a candle, and
what has been said both ways. **Every key is a letter in there**, `q` and `s` included — you type
your confession, Enter gives it, backspace works, and **esc** steps out. That needed
`curses.set_escdelay(25)` in `main()`: by default curses holds a bare esc for a second to see
whether an arrow key follows, so esc-then-anything was read as one meta key and the booth never
let you go — and the pty harness, which ends every run with `q`, hung on it. `absolve()` is the
priest: the first of `SINS` whose words he hears — **whole words or their starts**, matched on
tokens, because "cheat" has "eat" in it and a confession about the menu was first told hunger is
no sin — and otherwise that the city has heard worse; now and then what the city told him
(`ledger`: how many times you jumped across it from the menu tonight, or what is left of your
thousand dollars); a penance from `PENANCES`, all of them things to go and do in the city; and
peace. He takes `CONFESS_WAIT` to answer. Someone saying they are hurting is told, plainly, to
talk to someone.
