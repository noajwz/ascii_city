"""Ordinary play, driven through a real terminal.

    python3 tests/pty_checks.py

Forks a pty, sets its size with TIOCSWINSZ, types at it and reads back what
curses emits. This is the only way to test the input handling and the blit
loop - checks.py never goes near a terminal - and it is what catches a local
name shadowing loop state in main(), which no amount of headless rendering
will show you.

Watch out writing new cases here: an arrow key is "\x1bOC" once curses has
the keypad on (xterm's application mode), not "\x1b[C" - write the second and
it reads as a bare ESC, which quits. Two dead-end investigations started that
way, with the program fine and the harness killing it."""
import fcntl, os, pty, re, select, struct, sys, termios, time

ANSI = re.compile(rb"\x1b\[[0-9;?]*[a-zA-Z]|\x1b[()][B0]|\x1b[=>]|\x1b\][^\x07]*\x07")
APP = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                   "ascii_city.py")

def run(keys, cols=110, rows=34, term="xterm-256color", settle=0.9):
    pid, fd = pty.fork()
    if pid == 0:
        os.environ["TERM"] = term
        os.environ["ASCII_CITY_TEST"] = "1"     # ctrl-a jumps, off the panel
        os.execv(sys.executable, [sys.executable, APP])
    fcntl.ioctl(fd, termios.TIOCSWINSZ, struct.pack("HHHH", rows, cols, 0, 0))
    out = bytearray()
    def pump(sec):
        end = time.time() + sec
        while time.time() < end:
            r, _, _ = select.select([fd], [], [], 0.05)
            if r:
                try: b = os.read(fd, 65536)
                except OSError: return
                if not b: return
                out.extend(b)
    pump(settle)
    for k, w in keys:
        try: os.write(fd, k)
        except OSError: pass
        pump(w)
    try: os.write(fd, b"q")
    except OSError: pass
    pump(0.6)
    try: _, status = os.waitpid(pid, 0)
    except ChildProcessError: status = "?"
    try: os.close(fd)
    except OSError: pass
    return status, bytes(out)

def report(name, status, out):
    plain = ANSI.sub(b"", out).decode("utf-8", "replace")
    bad = "Traceback" in plain or "Error" in plain
    print("%-34s exit=%-4s bytes=%-8d %s" % (name, status, len(out),
                                             "CRASH" if bad else "ok"))
    if bad:
        i = plain.find("Traceback"); print(plain[i:i+1500])
    return not bad

# F1, the panel's key, as xterm sends it with the keypad on.
F1 = b"\x1bOP"

# The casino and club jumps stand you out front, to see the door; these
# steps walk you in.
IN = [(b"w", .25)] * 12
# And the tackle shops, the fishing boat's captain and the cruise ship's
# gangway, a few steps short of them: walked into, like a door.
# One press of w is about two units; a shop's counter is one step on, and a
# second press would be a key in the shop.
WALK_IN = [(b"w", .3)] * 2
TACKLE_IN = [(b"w", .5)]
HERRING_IN = [(b"w", .5)]       # him too: a second w would be a key in his list

def cases(run, report):
    """Every case, in order. Run twice: once to learn what each run() will be
    asked for, so they can all be played at once, and once with the results,
    to report on them - see the bottom of the file."""
    ok = True
    ok &= report("walk, turn, sidestep", *run(
        [(b"w",.5),(b"W",.6),(b"a",.5),(b"d",.4),(b"s",.4),(b",",.3),(b".",.3)]))
    ok &= report("tab to skyline and back", *run(
        [(b"\t",.6),(b"l",.4),(b"L",.4),(b"\t",.6),(b"w",.5)]))
    ok &= report("wander on spacebar", *run([(b" ", 5.0)]))
    ok &= report("turn: taps, then held, then wander and stop", *run(
        [(b"a", .3), (b"d", .3)] + [(b"\x1bOD", .04)] * 25 + [(b" ", 4.0), (b"w", .3)]))
    ok &= report("panel open, arrows still walk", *run(
        [(F1,.6),(b"\x1bOA",.4),(b"\x1bOC",.4),(b"\x1bOB",.4),(F1,.4),(b"w",.4)]))
    ok &= report("the panel on F1, and ` is nothing now", *run(
        [(F1, .6), (b"\x1b", .4), (F1, .4), ("\u00e0".encode(), .4),
         (F1, .6), (F1, .4), (b"w", .4)]))
    ok &= report("panel keys then esc then play", *run(
        [(F1,.5),(b"\x01y", .7),(b"w",.4),(b"L",.6),(b"\x1b",.4),(b"w",.5),(b"a",.4)]))
    ok &= report("TERM=xterm (8 colours)", *run(
        [(F1,.5),(b"\x01k", .7),(b"\x1b",.3),(b"w",.4)], term="xterm"))
    ok &= report("20x8 window with panel", *run(
        [(F1,.5),(b"\x01c", .7),(b"w",.4)], cols=20, rows=8))
    ok &= report("240x70 window with panel", *run(
        [(F1,.5),(b"n", .7),(b"w",.4)], cols=240, rows=70))
    ok &= report("ramen counter, sit and leave", *run(
        [(F1, .5), (b"\x01r", 1.0)] + IN + [(b"s", .6), (b"s", .6), (b"w", .4)]))
    ok &= report("casino slot: bet up, pull, bet down", *run(
        [(F1, .5), (b"\x01c", 1.0)] + IN + [(b"+", .3), (b"p", 3.0), (b"-", .3),
         (b"p", 3.0), (b"b", .6), (b"k", 3.0)], cols=100, rows=30))
    # A corner store: m on the panel, a few steps in, a coffee, x out.
    cs_st, cs_out = run([(F1, .5), (b"m", 1.0)] + IN + [(b"", 1.0), (b"2", 1.0),
                                                       (b"z", .5), (b"z", .5),
                                                       (b"x", 1.2), (b"w", .5)],
                        cols=300, rows=60)
    cs_plain = ANSI.sub(b"", cs_out).decode("utf-8", "replace")
    cs_ok = report("a corner store: in, a coffee, out", cs_st, cs_out)
    if cs_ok and cs_out and not ("open 24 hours" in cs_plain and "hot coffee" in cs_plain
                                 and "you step back out" in cs_plain):
        print("    not in, no coffee, or not out")
        cs_ok = False
    ok &= cs_ok
    # x leaves: in at the casino's door, and x walks you out. And with the
    # doors shut on the panel, walking at the same door takes you nowhere.
    xl_st, xl_out = run([(F1, .5), (b"\x01c", 1.0)] + IN + [(b"", 1.0), (b"x", 1.5),
                                                            (b"w", .3)],
                        cols=300, rows=60)      # wide: the note goes after the HUD
    xl_plain = ANSI.sub(b"", xl_out).decode("utf-8", "replace")
    xl_ok = report("x walks you out of the casino", xl_st, xl_out)
    if xl_ok and xl_out and not ("FAITES VOS JEUX" in xl_plain
                                 and "you step back out" in xl_plain):
        print("    not in, or not out again")
        xl_ok = False
    ok &= xl_ok
    ds_st, ds_out = run([(F1, .5), (b"o", .6), (b"\x01c", 1.0)] + IN + [(b"", 1.5)],
                        cols=110, rows=34)
    ds_plain = ANSI.sub(b"", ds_out).decode("utf-8", "replace")
    ds_ok = report("doors shut: past the casino's door", ds_st, ds_out)
    if ds_ok and ds_out and ("FAITES VOS JEUX" in ds_plain or "shut" not in ds_plain):
        print("    the door still took you in")
        ds_ok = False
    ok &= ds_ok
    ok &= report("sky deck: lift up, look round, lift down", *run(
        [(F1, .5), (b"\x01^", 1.0), (b"w", 6.0), (b"d", .5), (b"a", .5), (b"s", 6.0),
         (b"w", .4)], cols=100, rows=30))
    ok &= report("fire escape: climb, look round, climb down", *run(
        [(F1, .5), (b"\x01|", 1.0), (b"w", 1.0), (b"w", 4.0), (b"d", .5), (b"s", 1.0),
         (b"w", 4.0)], cols=100, rows=30))
    ok &= report("the pictures: go in, watch, walk out", *run(
        [(F1, .5), (b"\x01m", 2.5), (b"s", .6), (b"s", .6), (b"w", .4)],
        cols=100, rows=30))
    ok &= report("a lit alley, then under the el", *run(
        [(F1, .5), (b"\x01y", 1.0), (b"w", 2.0), (F1, .5), (b"\x01=", 1.0), (b"w", 3.0)],
        cols=100, rows=30))
    ok &= report("a police car coming, then traffic off", *run(
        [(F1, .5), (b"\x01<", 1.5), (F1, .5), (b">", .4), (b">", .4), (b"w", .5)],
        cols=100, rows=30))
    ok &= report("the diner: sit, coffee, walk out; then a billboard", *run(
        [(F1, .5), (b"\x01d", 6.5), (b"s", .8), (F1, .5), (b"$", 1.0), (b"w", .4)],
        cols=100, rows=30))
    ok &= report("the claw machine: play, drop, walk out", *run(
        [(F1, .5), (b"\x01j", 1.0), (b"p", 1.5), (b"p", 6.0), (b"p", .4), (b"s", .6),
         (b"s", .6), (b"w", .4)], cols=100, rows=30))
    ok &= report("up the lighthouse: climb, light a show, fire, climb down", *run(
        [(F1, .5), (b"\x01i", 1.0), (b"w", 6.0), (b"f", 3.0), (b"f", .5), (b"F", 1.5),
         (b"d", .4), (b"s", 6.0), (b"w", .4)], cols=100, rows=30))
    ok &= report("the arcade: choose, play, play keys, leave, walk out", *run(
        [(F1, .5), (b"\x01g", 2.0), (b"d", .4), (b"p", 1.0), (b"p", .3), (b"\x1bOD", .3),
         (b"w", .3), (b"s", .3), (b"d", .3), (b"x", .5), (b"a", .3), (b"p", 1.5),
         (b"x", .4), (b"s", .6), (b"s", .6)], cols=100, rows=30))
    ok &= report("the casino: 777 next pull, pull, walk out into the gold", *run(
        [(F1, .5), (b"\x01c", 1.0)] + IN + [(F1, .5), (b"%", .4), (F1, .3),
         (b"p", 3.5), (b"s", .6), (b"s", .6), (b"s", 1.0)], cols=100, rows=30))
    ok &= report("the plinko machine: over to it, bet up, drop three, back, out", *run(
        [(F1, .5), (b"\x01c", 1.0)] + IN + [(b"o", .4), (b"+", .2), (b"p", .2),
         (b"p", .2), (b"p", 3.0), (b"o", .4), (b"s", .6), (b"s", .6)],
        cols=100, rows=30))
    ok &= report("the races: over to the track, stake up, two bets, watch, back", *run(
        [(F1, .5), (b"\x01c", 1.0)] + IN + [(b"r", .4), (b"+", .2), (b"1", .2),
         (b"4", 3.0), (b"r", .4), (b"s", .6), (b"s", .6)], cols=100, rows=30))
    ok &= report("plinko, bigger and harder: rows up, high risk, drop, rows down", *run(
        [(F1, .5), (b"\x01c", 1.0)] + IN + [(b"o", .4), (b"]", .2), (b"]", .2),
         (b"3", .2), (b"p", 3.5), (b"[", .3), (b"1", .3), (b"p", 2.5), (b"o", .4),
         (b"s", .6), (b"s", .6)], cols=100, rows=30))
    ok &= report(
        "high flyer: over to it, stake up, bet, auto, watch, cash out, back", *run(
            [(F1, .5), (b"\x01c", 1.0)] + IN + [(b"f", .4), (b"+", .2), (b"p", .3),
             (b"u", .2), (b"u", 9.0), (b"p", .4), (b"f", .4), (b"s", .6), (b"s", .6)],
            cols=100, rows=30))
    ok &= report("closing time at the club, outside and in", *run(
        [(F1, .5), (b"/", .4), (b"\x01k", 4.5)] + IN + [(b"s", .6)], cols=100, rows=30))
    ok &= report("the strength tester: swing, swing again, walk out", *run(
        [(F1, .5), (b"\x01h", 1.0), (b"p", 2.5), (b"p", 2.5), (b"s", .6), (b"s", .6)],
        cols=100, rows=30))
    ok &= report("the roof party: lift up, walk about, back to the lift, down", *run(
        [(F1, .5), (b"\x01p", 1.0), (b"w", 6.0), (b"w", .6), (b"a", .5), (b"W", .6),
         (b"s", .6), (b"s", .6), (b"s", .6), (b"s", .6), (b"s", 6.0)],
        cols=100, rows=30))
    ok &= report("the stock exchange: buy, more, sell, walk out", *run(
        [(F1, .5), (b"\x01e", 1.0), (b"b", .4), (b"+", .3), (b"b", .4), (b"n", .4),
         (b"l", .4), (b"\x1bOB", .3), (b"\x1bOB", .3), (b"b", .4), (b"\x1bOA", .3),
         (b"l", .4), (b"\x1bOC", .3), (b"-", .3), (b"s", .6), (b"s", .6)],
        cols=100, rows=30))
    ok &= report("money: +1000 in the menu, a film, a bowl, walk out", *run(
        [(F1, .5), (b"+", .4), (b"\x01m", 2.0), (b"s", .6), (b"s", .6), (F1, .5),
         (b"r", .6)] + IN + [(b"s", .1), (b"w", 5.0), (b"s", .6), (b"s", .6)],
        cols=100, rows=30))
    ok &= report("a manhole: down, along the tunnel, back up the ladder", *run(
        [(F1, .5), (b"\x01x", 1.0)] + [(b"w", .25)] * 3
        + [(b"e", 1.0), (b"d", .4), (b"w", .4), (b"a", .4), (b"s", .4), (b"e", .8),
           (b"w", .4)], cols=100, rows=30))
    ok &= report("the lair: through the door, a slice, back out", *run(
        [(F1, .5), (b"t", 1.0)] + [(b"w", .25)] * 6
        + [(b"p", .5), (b"s", .6), (b"w", .3)], cols=300, rows=90))
    ok &= report("the temple: across the street, in, the word of god twice, out", *run(
        [(F1, .5), (b"\x01*", 1.0)] + IN + IN + [(b"g", .3), (b"g", .45), (b"g", .7),
                                                 (b"s", .6),
         (b"s", .6)], cols=100, rows=30))
    ok &= report("the confession booth: in, type with q and s in it, confess, esc, out",
                 *run([(F1, .5), (b"\x01*", 1.0)] + IN + IN + [(b"c", 1.6)]
                      + [(bytes([c_]), .05) for c_ in b"i quit my job and stole"]
                      + [(b"\x7f", .1), (b"l", .1), (b"\r", 3.0), (b"\x1b", .5),
                         (b"s", .6), (b"s", .6)], cols=100, rows=30))
    ok &= report("a blackout: to the night, the power going, walking in the dark", *run(
        [(F1, .5), (b"&", 8.0), (b"w", 1.0), (F1, .4), (b"\x01c", 1.5)],
        cols=100, rows=30))
    ok &= report("a taxi: hail, it pulls up, choose, ride, arrive", *run(
        [(b"t", 3.6), (b"\x1bOB", .3), (b"s", .3), (b"w", .3), (b"\r", 15.0),
         (b"w", .5)], cols=100, rows=30))
    for cab_size in ((100, 30), (300, 90)):
        ok &= report("drive the cab yourself, %dx%d" % cab_size, *run(
            [(b"t", 3.6), (b"d", .6), (b"w", .3), (b"w", 1.5), (b"a", .1), (b"a", .1),
             (b"a", .4), (b"m", .3), (b"m", .3), (b"h", .3), (b"l", .3), (b"l", .3),
             (b"x", .3)]
            + [(b"e", .04), (b"d", .04)] * 12
            + [(b" ", 2.5), (b"x", 1.0), (b"w", .5)], cols=cab_size[0], rows=cab_size[1]))
    ok &= report("a fog night: to it, walk, a taxi through it", *run(
        [(F1, .5), (b"#", 1.0), (b"w", 1.0), (b"W", 1.0), (b"t", 3.6), (b"\r", 8.0)],
        cols=100, rows=30))
    ok &= report("pace: up to very fast, walk, run into a wall, back down", *run(
        [(b"+", .2)] * 4 + [(b"w", .5), (b"W", .2), (b"W", 1.0)] + [(b"-", .2)] * 3
        + [(b"w", .5)], cols=100, rows=30))
    ok &= report("the factories: the zone, the site, into the rave and out", *run(
        [(F1, .5), (b"9", 1.5), (b"W", 1.0), (F1, .5), (b"\x01]", 1.5), (F1, .5),
         (b"\x01}", 1.5), (b"w", 1.0), (F1, .5), (b"[", 1.5)] + [(b"w", .25)] * 14
        + [(b"x", 1.0), (b"s", .6), (b"s", .6)],
        cols=100, rows=30))
    ok &= report("the suburbs: to them, walk a curving street, a taxi out", *run(
        [(F1, .5), (b"0", 1.5), (b"w", 1.0), (b"W", 1.0), (b"a", .5), (b"w", 1.0),
         (b"t", 3.6), (b"\x1b", .4)], cols=100, rows=30))
    ok &= report("a vending machine: up to the glass, buy two, step back", *run(
        [(F1, .5), (b"d", 1.5)] + [(b"w", .25)] * 14 + [(b"p", .8), (b"d", .3),
         (b"s", .3), (b"p", 1.5), (b"w", .3), (b"a", .3), (b"\r", 1.5), (b"x", .5),
         (b"w", .4)], cols=100, rows=30))
    ok &= report("the vending machine, big, and small again on z", *run(
        [(F1, .5), (b"d", 1.5)] + [(b"w", .25)] * 14 + [(b"p", .8), (b"p", 1.5),
         (b"z", .6), (b"z", .6), (b"x", .5)], cols=300, rows=90))
    ok &= report("lemonade at 3am: buy three, and the stargazer's telescope", *run(
        [(F1, .5), (b";", 1.5), (b"w", .4), (b"p", .4), (b"p", .4), (b"p", 1.0),
         (b"s", .6), (F1, .5), (b"?", 1.5), (b"w", .4), (b"x", 10.0), (b"s", .6)],
        cols=100, rows=30))
    ok &= report("the strip: to it, run up the boulevard, into a hotel's casino", *run(
        [(F1, .5), (b":", 1.5), (b"+", .2), (b"W", 1.0), (b"W", 1.0), (b"d", .4),
         (b"d", .4), (b"w", 1.0), (b"w", 1.0), (b"s", .6)], cols=100, rows=30))
    ok &= report("the airport: the end of the runway, watch one land, turn round", *run(
        [(F1, .5), (b"'", 6.0), (b"a", .4), (b"a", .4), (b"a", 3.0), (b"w", 1.0)],
        cols=100, rows=30))
    ok &= report("the fountain show: to it, and watch the start", *run(
        [(F1, .5), (b"\x01(", 14.0), (b"a", .4), (b"d", .4)], cols=100, rows=30))
    ok &= report("the university: the quad, across it, the panel's other page", *run(
        [(F1, .5), (b"\t", .4), (b"{", 1.5), (b"w", 1.0), (b"w", 1.0), (F1, .5),
         (b"\t", .4), (b"\t", .4), (F1, .4)], cols=80, rows=24))
    # Walking in is the reading room. w hands the terminal to the Wikipedia
    # reader, which opens on its search prompt: esc out of that, then q back to
    # the room; x out onto the quad. Not s after:
    # backing up is back through the doors. Up to walk in, not w: inside, w is
    # Wikipedia.
    lib_st, lib_out = run([(F1, .5), (b'\x01"', 1.5)] + [(b"\x1bOA", .3)] * 8   # up: in
                          + [(b"w", 2.5), (b"\x1b", 1.5), (b"q", 1.5),
                             (b"x", .8)] + [(b"w", .3)] * 4,
                          cols=100, rows=30)
    lib_txt = ANSI.sub(b"", lib_out).decode("utf-8", "replace")
    ok &= report("the library: the room, the reader, back out on the quad",
                 lib_st, lib_out)
    seen = ("THE READING ROOM" in lib_txt and "wiki_tui" in lib_txt
            # back on the street after it: its HUD. Not the library's hint -
        # on a fog night "the fog is in" has the hint line, and the night
        # follows the real clock.
        and lib_txt.rfind("ws walk") > lib_txt.rfind("wiki_tui"))
    print("%-34s %s" % ("  and the reader came up, and went",
                        "ok" if seen else "FAIL"))
    ok &= seen
    # The festival: the menu goes on to its night and in front of the dragon.
    fest_st, fest_out = run([(F1, .5), (b"*", 2.0), (b"\x1bOD", .4), (b"\x1bOC", .4)],
                            cols=120, rows=34)
    ok &= report("the festival: the dragon dance", fest_st, fest_out)
    fest_txt = ANSI.sub(b"", fest_out).decode("utf-8", "replace")
    seen = "dragon dance" in fest_txt and "no dragon dance near" not in fest_txt
    print("%-34s %s" % ("  and the menu took you there", "ok" if seen else "FAIL"))
    ok &= seen
    ok &= report("a flight: the gate, a seat, off, doze, land, out", *run(
        [(F1, .5), (b"\x01.", 1.5)] + [(b"w", .3)] * 6 + [(b"\r", 4.0), (b"\x1bOD", .3),
         (b"\x1bOC", .3), (b"x", 1.0)] + [(b"", 3.0)] * 9 + [(b"w", .3)],
        cols=100, rows=30))
    ok &= report("a flight: the gate, and straight back out", *run(
        [(F1, .5), (b"\x01.", 1.5)] + [(b"w", .3)] * 6 + [(b"x", .8), (b"w", .4)],
        cols=80, rows=24))
    # Up to walk in, not w; h to heal, c the PC - the type chart, which q quits -
    # then x out, and the street again: its "walk in" hint is back after the PC.
    pc_st, pc_out = run([(F1, .5), (b",", 1.5)] + [(b"\x1bOA", .25)] * 14
                        + [(b"h", 4.5), (b"c", 2.5), (b"q", 1.5), (b"x", 1.2),
                           (b"w", .6)], cols=100, rows=30)
    ok &= report("the Pokemon Center: in, heal, the PC, q, out", pc_st, pc_out)
    pc_txt = ANSI.sub(b"", pc_out).decode("utf-8", "replace")
    pc_at = max(pc_txt.rfind("Fire"), pc_txt.rfind("Water"))
    seen = ("Nurse Joy" in pc_txt and "hope to see you" in pc_txt and pc_at > 0
            and pc_txt.rfind("ws walk") > pc_at)      # the street's HUD, any night
    print("%-34s %s" % ("  and she healed, the PC came up", "ok" if seen else "FAIL"))
    ok &= seen
    ok &= report("the metro: down, a ticket, the train, the ride, up", *run(
        [(F1, .5), (b"-", 1.5), (b"e", 1.0), (b"s", .5), (b"\r", .5)]
        + [(b"", 3.0)] * 15 + [(b"x", .5)], cols=100, rows=30))
    ok &= report("the metro: down and straight back up", *run(
        [(F1, .5), (b"-", 1.5), (b"e", 1.0), (b"w", .4), (b"x", .8), (b"w", .5)],
        cols=80, rows=24))
    # A zoomed-out window: the room in block letters, and z gives back the
    # small one - its banner in plain letters - and z again the big.
    big_st, big_out = run([(F1, .5), (b"\x01c", 1.0)] + IN
                          + [(b"p", 2.0), (b"b", 1.0), (b"z", .8), (b"z", .8),
                             (b"s", .6), (b"s", .6)], cols=300, rows=90)
    ok &= report("the big casino on a big window: spin, pull, deal, z off and on",
                 big_st, big_out)
    big_txt = ANSI.sub(b"", big_out).decode("utf-8", "replace")
    seen = big_txt.count("#") > 500 and bool(re.search(r"CASINO  [A-Z]", big_txt))
    print("%-34s %s" % ("  and z gave the small room back", "ok" if seen else "FAIL"))
    ok &= seen
    ok &= report("the big casino's games: plinko, the races, high flyer, and back",
                 *run([(F1, .5), (b"\x01c", 1.0)] + IN
                      + [(b"o", .8), (b"p", 3.0), (b"o", .5), (b"r", .8), (b"1", .5),
                         (b"r", .5), (b"f", .8), (b"p", 2.5), (b"f", .5), (b"s", .6),
                         (b"s", .6)], cols=300, rows=90))
    # The arcade on a big window: the menu puts you inside; a game, big, then
    # z gives the small one - its plain-letter name - and z again the big.
    arc_st, arc_out = run([(F1, .5), (b"\x01g", 2.0), (b"p", 1.0), (b"p", .5),
                           (b"p", .5), (b"z", .8), (b"z", .8), (b"x", .6), (b"s", .6),
                           (b"s", .6)], cols=300, rows=90)
    ok &= report("the big arcade: in, a game, z off and on, out", arc_st, arc_out)
    arc_txt = ANSI.sub(b"", arc_out).decode("utf-8", "replace")
    seen = arc_txt.count("#") > 500 and "SCORE" in arc_txt
    print("%-34s %s" % ("  and z gave the small game back", "ok" if seen else "FAIL"))
    ok &= seen
    # The Center on a big window: heal, then z small, z big again, out.
    pcb_st, pcb_out = run([(F1, .5), (b",", 1.5)] + [(b"\x1bOA", .25)] * 14
                          + [(b"h", 4.5), (b"z", .8), (b"z", .8), (b"x", 1.2),
                             (b"w", .6)], cols=300, rows=90)
    ok &= report("the big Pokemon Center: heal, z off and on, out", pcb_st, pcb_out)
    pcb_txt = ANSI.sub(b"", pcb_out).decode("utf-8", "replace")
    # curses sends only the cells that change, so look for the small
    # machine's lid - drawn whole where nothing was - not Joy's face.
    seen = ("@@((" in pcb_txt and "+-------+" in pcb_txt
            and "hope to see you" in pcb_txt)
    print("%-34s %s" % ("  and big, then small, then big", "ok" if seen else "FAIL"))
    ok &= seen
    ok &= report("up a fire escape to something on the roof", *run(
        [(F1, .5), (b"r", 1.5)] + [(b"\x1bOA", .3)] * 6
        + [(b"", 9.0), (b"d", .3), (b"a", .3), (b"s", 8.0)], cols=300, rows=90))
    ok &= report("feeding the pigeons", *run(
        [(F1, .5), (b"r", 1.5)] + [(b"\x1bOA", .3)] * 6
        + [(b"", 9.0), (b"f", 3.0), (b"r", 2.0), (b"n", 2.0), (b"d", .3),
           (b"a", .3), (b"s", 8.0)], cols=110, rows=34))
    ok &= report("under the washing lines", *run(
        [(F1, .5), (b"h", 1.5)] + [(b"w", .25)] * 10, cols=300, rows=90))
    for bw_size in ((110, 34), (300, 90)):
        ok &= report("a frame of bowling, %dx%d" % bw_size, *run(
            [(F1, .5), (b"k", 1.5), (b"p", .4), (b"d", .2), (b"a", .2), (b"p", .4),
             (b"p", 5.0), (b"p", .4), (b"p", .4), (b"z", .3), (b"x", .4)],
            cols=bw_size[0], rows=bw_size[1]))
    for kb_size in ((110, 34), (300, 90)):
        ok &= report("a song at the karaoke bar, %dx%d" % kb_size, *run(
            [(F1, .5), (b"\x01a", 1.5), (b"n", .3), (b"p", 3.0), (b"j", .2),
             (b"k", .2), (b"l", .2), (b"z", .3), (b"x", .4), (b"s", .5)],
            cols=kb_size[0], rows=kb_size[1]))
    for mg_size in ((110, 34), (300, 90)):
        ok &= report("a round of mini golf, %dx%d" % mg_size, *run(
            [(F1, .5), (b"\x01l", 1.5), (b"p", .4), (b"a", .2), (b"d", .2),
             (b"p", .5), (b"p", 4.0), (b"z", .3), (b"x", .4), (b"s", .5)],
            cols=mg_size[0], rows=mg_size[1]))
    ok &= report("a jump off a roof takes you off the roof", *run(
        [(F1, .5), (b"\x01^", 1.5)] + [(b"\x1bOA", .3)] * 6
        + [(b"", 7.0), (F1, .4), (b"\x01c", 1.0), (b"w", .3)], cols=110, rows=34))
    for ck_size in ((110, 34), (300, 90)):
        ok &= report("flying the plane, %dx%d" % ck_size, *run(
            [(F1, .5), (b"f", 1.0)] + [(b"W", .1)] * 10 + [(b"", 5.0)]
            + [(b"s", .1)] * 4 + [(b"", 3.0), (b"d", .1), (b"d", .1), (b"d", .1),
                                  (b"", 2.0), (b"a", .1), (b"w", .1), (b"-", .1),
                                  (b"r", 1.5), (b"f", .2), (b"g", .3), (b"p", 2.0),
                                  (b"g", .3), (b"z", .3), (b"m", .5), (b"-", .3),
                                  (b"+", .3), (b"S", .2), (b"W", .2), (b"i", .3),
                                  (b"c", .3), (b"v", 1.5), (b"l", .5),
                                  (b"a", .3), (b"v", 1.0), (b"l", .3),
                                  (b"", 1.0), (b"x", .8), (b"w", .3)],
            cols=ck_size[0], rows=ck_size[1]))
    ok &= report("the desk: a check ride, and the autopilot pushes back", *run(
        [(F1, .5), (b"\x01.", 1.0)] + [(b"w", .25)] * 6 + [(b"t", .6), (b"p", 4.0), (b"k", 2.0),
                                                       (b"v", 1.0), (b"x", .8)],
        cols=110, rows=34))
    ok &= report("the desk: the keys, and straight into a wall", *run(
        [(F1, .5), (b"\x01.", 1.0)] + [(b"w", .25)] * 6 + [(b"c", .6)]
        + [(b"W", .1)] * 10 + [(b"d", .1)] * 12 + [(b"", 8.0)], cols=110, rows=34))
    for rb_size in ((110, 34), (300, 90)):
        ok &= report("a drink at the rooftop bar, %dx%d" % rb_size, *run(
            [(F1, .5), (b"b", 1.5)] + [(b"\x1bOA", .3)] * 6
            + [(b"", 8.0), (b"1", 3.2), (b"4", 3.2), (b"z", .5), (b"z", .5),
               (b"d", .3), (b"d", .3), (b"a", .3), (b"s", 8.0)],
            cols=rb_size[0], rows=rb_size[1]))
    ok &= report("a far storm out of the plane's window", *run(
        [(F1, .5), (b"\x01.", 1.5)] + [(b"\x1bOA", .3)] * 6
        + [(b"\r", 12.0), (F1, .4), (b"\\", .4), (F1, .4), (b"", 4.0)],
        cols=300, rows=90))
    ok &= report("a far storm from a roof", *run(
        [(F1, .5), (b"\x01^", 1.5)] + [(b"\x1bOA", .25)] * 6
        + [(b"", 6.0), (F1, .4), (b"\\", .4), (F1, .4), (b"", 4.0), (b"s", 5.0)],
        cols=300, rows=90))
    ok &= report("the highway", *run([(F1, .5), (b"\x01)", 1.2), (b"w", .5)],
                                     cols=100, rows=30))
    ok &= report("the beach: to a bar on the sand, two drinks, back out, the surf", *run(
        [(F1, .5), (b"\x011", 1.5)] + [(b"w", .25)] * 2 + [(b"1", 3.2), (b"3", 3.2),
         (b"z", .5), (b"s", .6), (b"s", .6), (b"d", .6)] + [(b"W", .5)] * 8
        + [(b"a", .6), (b"w", .6)], cols=100, rows=30))
    ok &= report("the beach bar, big, and small again on z", *run(
        [(F1, .5), (b"\x011", 1.5)] + [(b"w", .25)] * 2 + [(b"2", 3.2), (b"z", .6),
         (b"z", .6), (b"s", .8)], cols=300, rows=90))
    ok &= report("the pier: out along it at a run, and a look round", *run(
        [(F1, .5), (b"\x012", 1.5)] + [(b"W", .6)] * 10 + [(b"a", .5), (b"d", .9),
         (b"s", .5)], cols=110, rows=34))
    ok &= report("the pier's wheel: on, round a way, looking about", *run(
        [(F1, .5), (b"\x013", 1.5), (b"p", 4.0), (b"a", .4), (b"a", .4), (b"d", 3.0),
         (b"x", 2.0)], cols=110, rows=34))
    ok &= report("the wheel on a big window", *run(
        [(F1, .5), (b"\x013", 1.5), (b"p", 6.0), (b"d", .5)], cols=300, rows=90))
    ok &= report("the sea off and on from the panel, standing on the beach", *run(
        [(F1, .5), (b"\x011", 1.5), (b"w", .5), (F1, .5), (b"~", 1.2), (b"\x1b", .4),
         (b"w", .6), (F1, .5), (b"~", 1.2), (b"\x1b", .4), (b"w", .6)],
        cols=110, rows=34))
    # The launch pad: a launch from the panel, fifteen seconds of countdown,
    # liftoff on the top bar, then out along the causeway at a run to the fence.
    lp_st, lp_out = run([(F1, .5), (b"\x014", 1.5), (F1, .5), (b"^", .6),
                         (b"\x1b", .4)] + [(b"", 4.0)] * 5 + [(b"W", .5)] * 8,
                        cols=160, rows=48)
    lp_plain = ANSI.sub(b"", lp_out).decode("utf-8", "replace")
    lp_ok = report("the launch pad: a launch, and out along the causeway",
                   lp_st, lp_out)
    if lp_ok and lp_out and not ("fifteen" in lp_plain and "LIFTOFF" in lp_plain):
        print("    no launch from the panel, or no LIFTOFF on the top bar")
        lp_ok = False
    ok &= lp_ok
    # Mission control: in at the door, l, every camera, big and small, out.
    mc_st, mc_out = run([(F1, .5), (b"\x015", 1.5), (b"w", .4), (b"w", .4),
                         (b"w", 1.5), (b"l", 1.2), (b"c", .8), (b"3", .8), (b"4", .8),
                         (b"1", .8), (b"z", .8), (b"z", .8), (b"s", .6), (b"s", .6)],
                        cols=160, rows=48)
    mc_plain = ANSI.sub(b"", mc_out).decode("utf-8", "replace")
    mc_ok = report("mission control: launch it, every camera, out", mc_st, mc_out)
    if mc_ok and mc_out and not ("LIVE" in mc_plain and "FLIGHT:" in mc_plain
                                 and "BOOSTER CAM" in mc_plain):
        print("    no webcast, no launch from the desk, or no booster camera")
        mc_ok = False
    ok &= mc_ok
    # The harbour: money, the gangway, a cruise, a look round, back ashore.
    hb_st, hb_out = run([(F1, .5), (b"+", .4), (b"\x017", 1.5)] + WALK_IN + [(b"", 3.0),
                         (b"a", .5), (b"d", .5), (b"", 3.0), (b"x", 1.2), (b"w", .5)],
                        cols=300, rows=60)      # wide: the note goes after the HUD
    hb_plain = ANSI.sub(b"", hb_out).decode("utf-8", "replace")
    hb_ok = report("the harbour: a cruise, and ashore again", hb_st, hb_out)
    if hb_ok and hb_out and not ("all aboard" in hb_plain and "tender" in hb_plain):
        print("    did not get aboard, or not back ashore")
        hb_ok = False
    ok &= hb_ok
    # The speedboat: hire one, open her up, turn, slide, the horn, back.
    sb_st, sb_out = run([(F1, .5), (b"+", .4), (b"\x018", 1.5), (b"p", 1.0)]
                        + [(b"w", .2)] * 6 + [(b"", 2.0), (b"a", .3), (b"d", .3),
                                              (b"A", .4), (b"h", .4), (b"x", 1.2),
                                              (b"w", .5)], cols=300, rows=60)
    sb_plain = ANSI.sub(b"", sb_out).decode("utf-8", "replace")
    sb_ok = report("the speedboat: out, a turn, back to the quay", sb_st, sb_out)
    if sb_ok and sb_out and not ("she is yours" in sb_plain and "KNOTS" in sb_plain
                                 and "back at the quay" in sb_plain):
        print("    did not get her out, or not back")
        sb_ok = False
    ok &= sb_ok
    # The beach's two rare nights: y on the panel for a drone show, c to the
    # coast; then j for a night the surf glows.
    dr_st, dr_out = run([(F1, .5), (b"y", .6), (b"c", 1.5), (b"", 6.0), (F1, .5),
                         (b"j", .6), (b"c", 1.5), (b"", 2.0)], cols=300, rows=60)
    dr_plain = ANSI.sub(b"", dr_out).decode("utf-8", "replace")
    dr_ok = report("a drone show night, and a glowing one, at the beach", dr_st, dr_out)
    if dr_ok and dr_out and not ("a drone show over the sea" in dr_plain
                                 and "the surf glows" in dr_plain):
        print("    no show, or the surf not glowing")
        dr_ok = False
    ok &= dr_ok
    # The rocket: i on the panel straps you in; space lights it; a tap of w
    # tips her over; the map and back, the view from outside and back; x
    # twice is the escape motor, and x once more is out on the causeway.
    rk_st, rk_out = run([(F1, .5), (b"i", 1.5), (b" ", 6.0), (b"w", .6), (b"w", .6),
                         (b"m", 1.0), (b"m", 1.0), (b"v", 1.2), (b"v", 1.0), (b"z", .5),
                         (b"z", .5), (b"x", .6), (b"x", 1.5), (b"x", 1.5), (b"w", 1.0)],
                        cols=300, rows=60)
    rk_plain = ANSI.sub(b"", rk_out).decode("utf-8", "replace")
    rk_ok = report("the rocket: strapped in, liftoff, the map, out by the escape motor",
                   rk_st, rk_out)
    if rk_ok and rk_out and not ("IGNITION" in rk_plain and "CAPCOM" in rk_plain
                                 and "MAP" in rk_plain and "ABORT" in rk_plain
                                 and "abort" in rk_plain):
        print("    not strapped in, no liftoff, no map, or not out")
        rk_ok = False
    ok &= rk_ok
    # The submarine: from the pen, out, down, a ping, the lamp, back.
    su_st, su_out = run([(F1, .5), (b"+", .4), (b"\x01[", 1.5), (b"p", 1.0)]
                        + [(b"w", .2)] * 3 + [(b"f", .3)] * 4 + [(b"", 4.0),
                                                                 (b"h", 1.5), (b"l", 1.5),
                                                                 (b"l", 1.0), (b"a", .5),
                                                                 (b"z", .8), (b"z", .8),
                                                                 (b"x", 1.5), (b"w", 1.0)],
                        cols=300, rows=60)
    su_plain = ANSI.sub(b"", su_out).decode("utf-8", "replace")
    su_ok = report("the submarine: out, down, a ping, back to the pen", su_st, su_out)
    if su_ok and su_out and not ("the hatch shuts" in su_plain and "DEPTH" in su_plain
                                 and "the dark comes" in su_plain and "PING" in su_plain
                                 and "back at the pen" in su_plain):
        print("    did not get her out, or not down, or not back")
        su_ok = False
    ok &= su_ok
    # Fishing: a kiosk on a river pier, a rod, worms and a float, out facing
    # the water, the panel's big one next, a cast, the strike, the fight.
    DOWN, RIGHT = b"\x1bOB", b"\x1bOC"
    fi_st, fi_out = run([(F1, .5), (b"+", .3), (b"\x010", 1.5)] + TACKLE_IN
                        + [(b"", .5),
                         (DOWN, .2), (b"p", .4), (RIGHT, .3), (DOWN, .2), (b"p", .4),
                         (RIGHT, .3), (b"p", .4), (b"x", .6), (F1, .4), (b"g", .3),
                         (F1, .4), (b"f", .8), (b"f", 1.2)] + [(b"f", .3)] * 16
                        + [(b"w", .1)] * 15 + [(b"x", .8), (b"w", .4)],
                        cols=160, rows=45)
    fi_plain = ANSI.sub(b"", fi_out).decode("utf-8", "replace")
    fi_ok = report("fishing: the kiosk, a cast, a bite, the fight", fi_st, fi_out)
    if fi_ok and fi_out and not ("LIVE BAIT" in fi_plain and "CAST" in fi_plain
                                 and "TENSION" in fi_plain):
        print("    no shop, no cast, or nothing on the line")
        fi_ok = False
    ok &= fi_ok
    # The fishing boat: no rod and the captain sends you to the shop; then a
    # big game rod and lure from the pier, the trip out, a cast, and home.
    nr_st, nr_out = run([(F1, .5), (b"\x01v", 1.5)] + HERRING_IN + [(b"", .5), (b"p", .8),
                         (b"x", .6)], cols=160, rows=45)
    nr_plain = ANSI.sub(b"", nr_out).decode("utf-8", "replace")
    nr_ok = report("the fishing boat's captain, no rod", nr_st, nr_out)
    if nr_ok and nr_out and not ("WHERE TO" in nr_plain and "teeth" in nr_plain):
        print("    no captain, or he took you without a rod")
        nr_ok = False
    ok &= nr_ok
    ex_st, ex_out = run([(F1, .5), (b"+", .3), (b"\x019", 1.5)] + TACKLE_IN
                        + [(b"", .5)]
                        + [(DOWN, .15)] * 3 + [(b"p", .4), (RIGHT, .3)]
                        + [(DOWN, .15)] * 5 + [(b"p", .4), (b"x", .5),
                                               (F1, .5), (b"\x01v", 1.5)] + HERRING_IN + [
                                               (b"", .5),
                                               (b"p", 1.0)]
                        + [(b" ", .3)] * 9 + [(b"", 1.5), (b"c", .8), (b"1", .6),
                                               (b"t", .5), (b"5", .4), (b"a", .3),
                                               (b"x", .6), (b"f", 1.5), (b"x", 1.0)]
                        + [(b" ", .3)] * 7 + [(b"", 1.5), (b"w", .4)],
                        cols=160, rows=45)
    ex_plain = ANSI.sub(b"", ex_out).decode("utf-8", "replace")
    ex_ok = report("a fishing trip: out, a cast, and home", ex_st, ex_out)
    if ex_ok and ex_out and not ("going out to the open ocean" in ex_plain
                                 and "CAST" in ex_plain and "going home" in ex_plain
                                 and "captain's cabin" in ex_plain
                                 and "DRINKS" in ex_plain):
        print("    did not sail, fish, or come home")
        ex_ok = False
    ok &= ex_ok
    # The wreck: the second on his list, out, and the captain on her.
    wr_st, wr_out = run([(F1, .5), (b"+", .3), (b"\x019", 1.5)] + TACKLE_IN
                        + [(b"", .5), (DOWN, .15), (DOWN, .15), (b"p", .4), (b"x", .5),
                           (F1, .5), (b"\x01v", 1.5)] + HERRING_IN
                        + [(b"", .5), (DOWN, .3), (b"p", 1.0)] + [(b" ", .3)] * 8
                        + [(b"", 2.0), (b"x", 1.0)], cols=160, rows=45)
    wr_plain = ANSI.sub(b"", wr_out).decode("utf-8", "replace")
    wr_ok = report("the wreck: out to the Mary Ellen", wr_st, wr_out)
    if wr_ok and wr_out and not ("going out to the wreck" in wr_plain
                                 and "THE WRECK" in wr_plain):
        print("    he did not take you to the wreck")
        wr_ok = False
    ok &= wr_ok
    # The glowing sea: e on the panel for a dark night, then out to the cove.
    gl_st, gl_out = run([(F1, .5), (b"+", .3), (b"e", .4), (b"\x019", 1.5)]
                        + TACKLE_IN + [(b"", .5), (DOWN, .15), (b"p", .4), (b"x", .5),
                                       (F1, .5), (b"\x01v", 1.5)] + HERRING_IN
                        + [(b"", .5)] + [(DOWN, .3)] * 4 + [(b"p", 1.0)]
                        + [(b" ", .3)] * 8 + [(b"", 2.0), (b"x", 1.0)],
                        cols=300, rows=60)
    gl_plain = ANSI.sub(b"", gl_out).decode("utf-8", "replace")
    gl_ok = report("the glowing sea, on a dark night", gl_st, gl_out)
    if gl_ok and gl_out and not ("a dark night" in gl_plain
                                 and "going out to the glowing sea" in gl_plain):
        print("    no dark night, or he did not take you")
        gl_ok = False
    ok &= gl_ok
    # The deep trench and the ice floes: a big game rod and squid from the pier,
    # then each: out, a cast (the trench: it sinks), and at the floes, a cocoa.
    BUY = [(b"\x019", 1.5)] + TACKLE_IN + [(b"", .5), (DOWN, .15), (DOWN, .15),
                                          (DOWN, .15), (b"p", .4), (RIGHT, .3),
                                          (DOWN, .15), (DOWN, .15), (DOWN, .15),
                                          (b"p", .4), (b"x", .5)]
    # The launch pad: and in his cabin, six of his tales for the treasure map.
    for name_, downs_, look_, more_ in (
            ("the deep trench", 2, "SINKING", []),
            ("the ice floes", 3, "warms your hands", []),
            ("the launch pad", 5, "X marks it", [(b"t", .4)] * 6),
            # The sea cave: into the dinghy, the ARCH bar, his echo off the rock.
            ("the sea cave", 6, "atey...", [(b"f", 2.0)])):
        tr_st, tr_out = run([(F1, .5), (b"+", .3), (b"+", .3)] + BUY
                            + [(F1, .5), (b"\x01v", 1.5)] + HERRING_IN + [(b"", .5)]
                            + [(DOWN, .3)] * downs_ + [(b"p", 1.0)]
                            + [(b" ", .3)] * 13 + [(b"", 2.0), (b"f", 2.5),
                                                   (b"c", .8), (b"4", .8)]
                            + more_ + [(b"x", .6)],
                            cols=300, rows=60)
        tr_plain = ANSI.sub(b"", tr_out).decode("utf-8", "replace")
        tr_ok = report("out to " + name_, tr_st, tr_out)
        if tr_ok and tr_out and not ("going out to " + name_ in tr_plain
                                     and look_ in tr_plain
                                     and (name_ != "the sea cave" or "ARCH" in tr_plain)):
            print("    did not get there, or no %r" % look_)
            tr_ok = False
        ok &= tr_ok
    # Treasure Island: his map from six tales in the cabin, home, then back to
    # him - it is on his list now, last - out to it, ashore with g, and a dig.
    ti_st, ti_out = run([(F1, .5), (b"+", .3), (b"+", .3)] + BUY
                        + [(F1, .5), (b"\x01v", 1.5)] + HERRING_IN
                        + [(b"", .5), (b"p", 1.0)] + [(b" ", .3)] * 13
                        + [(b"", 2.0), (b"c", .8)] + [(b"t", .4)] * 6
                        + [(b"x", .6), (b"x", 1.0)] + [(b" ", .3)] * 13 + [(b"", 3.0)]
                        + [(F1, .5), (b"\x01v", 1.5)] + HERRING_IN + [(b"", .5)]
                        + [(DOWN, .3)] * 6 + [(b"p", 1.0)] + [(b" ", .3)] * 13
                        + [(b"", 2.0), (b"g", 1.0)] + [(b"a", .05)] * 30
                        + [(b" ", 1.6), (b"", 1.0), (b"x", 1.5)],
                        cols=300, rows=60)
    ti_plain = ANSI.sub(b"", ti_out).decode("utf-8", "replace")
    ti_ok = report("a map, and ashore on Treasure Island", ti_st, ti_out)
    if ti_ok and ti_out and not ("going out to treasure island" in ti_plain
                                 and "THE MAP: from the skull" in ti_plain
                                 and "you row back" in ti_plain):
        print("    no map, no island, or no dig")
        ti_ok = False
    ok &= ti_ok
    return ok


# Each case is its own process that mostly waits - 51 of them, 630 seconds
# of waiting one after another. So: a dry pass, quietly, to collect what each
# run() is asked for; all of them played PTY_JOBS at a time; then the real
# pass, handed the results in the same order, reporting as it goes.
# PTY_JOBS=1 plays them one at a time, as it used to.
if __name__ == "__main__":
    import contextlib
    import io
    import warnings
    from concurrent.futures import ThreadPoolExecutor

    # The child execs straight away, so forking with threads about is safe.
    warnings.filterwarnings("ignore", category=DeprecationWarning)
    asked = []
    with contextlib.redirect_stdout(io.StringIO()):
        cases(lambda keys, **kw: asked.append((keys, kw)) or (0, b""),
              lambda *a: True)
    with ThreadPoolExecutor(max(1, int(os.environ.get("PTY_JOBS", "6")))) as pool:
        played = iter(list(pool.map(lambda a: run(a[0], **a[1]), asked)))
    ok = cases(lambda keys, **kw: next(played), report)
    print("ALL OK" if ok else "FAILURES")
    sys.exit(0 if ok else 1)
