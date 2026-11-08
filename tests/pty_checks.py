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

# The casino and club jumps stand you out front, to see the door; these
# steps walk you in.
IN = [(b"w", .25)] * 12

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
        [(b"`",.6),(b"\x1bOA",.4),(b"\x1bOC",.4),(b"\x1bOB",.4),(b"`",.4),(b"w",.4)]))
    ok &= report("the panel from a dead-key ` (``, `c, a-grave) and from F1", *run(
        [(b"``", .6), (b"\x1b", .4), (b"`c", .6), (b"\x1b", .4),
         ("\u00e0".encode(), .6), (b"\x1b", .4), (b"\x1bOP", .6), (b"\x1b", .4),
         (b"w", .4)]))
    ok &= report("panel keys then esc then play", *run(
        [(b"`",.5),(b"y",.7),(b"w",.4),(b"L",.6),(b"\x1b",.4),(b"w",.5),(b"a",.4)]))
    ok &= report("TERM=xterm (8 colours)", *run(
        [(b"`",.5),(b"k",.7),(b"\x1b",.3),(b"w",.4)], term="xterm"))
    ok &= report("20x8 window with panel", *run(
        [(b"`",.5),(b"c",.7),(b"w",.4)], cols=20, rows=8))
    ok &= report("240x70 window with panel", *run(
        [(b"`",.5),(b"6",.7),(b"w",.4)], cols=240, rows=70))
    ok &= report("ramen counter, sit and leave", *run(
        [(b"`", .5), (b"r", 1.0)] + IN + [(b"s", .6), (b"s", .6), (b"w", .4)]))
    ok &= report("casino slot: bet up, pull, bet down", *run(
        [(b"`", .5), (b"c", 1.0)] + IN + [(b"+", .3), (b"p", 3.0), (b"-", .3),
         (b"p", 3.0), (b"b", .6), (b"k", 3.0)], cols=100, rows=30))
    ok &= report("sky deck: lift up, look round, lift down", *run(
        [(b"`", .5), (b"^", 1.0), (b"w", 6.0), (b"d", .5), (b"a", .5), (b"s", 6.0),
         (b"w", .4)], cols=100, rows=30))
    ok &= report("fire escape: climb, look round, climb down", *run(
        [(b"`", .5), (b"|", 1.0), (b"w", 1.0), (b"w", 4.0), (b"d", .5), (b"s", 1.0),
         (b"w", 4.0)], cols=100, rows=30))
    ok &= report("the pictures: go in, watch, walk out", *run(
        [(b"`", .5), (b"m", 2.5), (b"s", .6), (b"s", .6), (b"w", .4)],
        cols=100, rows=30))
    ok &= report("a lit alley, then under the el", *run(
        [(b"`", .5), (b"y", 1.0), (b"w", 2.0), (b"`", .5), (b"=", 1.0), (b"w", 3.0)],
        cols=100, rows=30))
    ok &= report("a police car coming, then traffic off", *run(
        [(b"`", .5), (b"<", 1.5), (b"`", .5), (b">", .4), (b">", .4), (b"w", .5)],
        cols=100, rows=30))
    ok &= report("the diner: sit, coffee, walk out; then a billboard", *run(
        [(b"`", .5), (b"d", 6.5), (b"s", .8), (b"`", .5), (b"$", 1.0), (b"w", .4)],
        cols=100, rows=30))
    ok &= report("the claw machine: play, drop, walk out", *run(
        [(b"`", .5), (b"j", 1.0), (b"p", 1.5), (b"p", 6.0), (b"p", .4), (b"s", .6),
         (b"s", .6), (b"w", .4)], cols=100, rows=30))
    ok &= report("up the lighthouse: climb, light a show, fire, climb down", *run(
        [(b"`", .5), (b"i", 1.0), (b"w", 6.0), (b"f", 3.0), (b"f", .5), (b"F", 1.5),
         (b"d", .4), (b"s", 6.0), (b"w", .4)], cols=100, rows=30))
    ok &= report("the arcade: choose, play, play keys, leave, walk out", *run(
        [(b"`", .5), (b"g", 2.0), (b"d", .4), (b"p", 1.0), (b"p", .3), (b"\x1bOD", .3),
         (b"w", .3), (b"s", .3), (b"d", .3), (b"x", .5), (b"a", .3), (b"p", 1.5),
         (b"x", .4), (b"s", .6), (b"s", .6)], cols=100, rows=30))
    ok &= report("the casino: 777 next pull, pull, walk out into the gold", *run(
        [(b"`", .5), (b"c", 1.0)] + IN + [(b"`", .5), (b"%", .4), (b"`", .3),
         (b"p", 3.5), (b"s", .6), (b"s", .6), (b"s", 1.0)], cols=100, rows=30))
    ok &= report("the plinko machine: over to it, bet up, drop three, back, out", *run(
        [(b"`", .5), (b"c", 1.0)] + IN + [(b"o", .4), (b"+", .2), (b"p", .2),
         (b"p", .2), (b"p", 3.0), (b"o", .4), (b"s", .6), (b"s", .6)],
        cols=100, rows=30))
    ok &= report("the races: over to the track, stake up, two bets, watch, back", *run(
        [(b"`", .5), (b"c", 1.0)] + IN + [(b"r", .4), (b"+", .2), (b"1", .2),
         (b"4", 3.0), (b"r", .4), (b"s", .6), (b"s", .6)], cols=100, rows=30))
    ok &= report("plinko, bigger and harder: rows up, high risk, drop, rows down", *run(
        [(b"`", .5), (b"c", 1.0)] + IN + [(b"o", .4), (b"]", .2), (b"]", .2),
         (b"3", .2), (b"p", 3.5), (b"[", .3), (b"1", .3), (b"p", 2.5), (b"o", .4),
         (b"s", .6), (b"s", .6)], cols=100, rows=30))
    ok &= report(
        "high flyer: over to it, stake up, bet, auto, watch, cash out, back", *run(
            [(b"`", .5), (b"c", 1.0)] + IN + [(b"f", .4), (b"+", .2), (b"p", .3),
             (b"u", .2), (b"u", 9.0), (b"p", .4), (b"f", .4), (b"s", .6), (b"s", .6)],
            cols=100, rows=30))
    ok &= report("closing time at the club, outside and in", *run(
        [(b"`", .5), (b"/", .4), (b"k", 4.5)] + IN + [(b"s", .6)], cols=100, rows=30))
    ok &= report("the strength tester: swing, swing again, walk out", *run(
        [(b"`", .5), (b"h", 1.0), (b"p", 2.5), (b"p", 2.5), (b"s", .6), (b"s", .6)],
        cols=100, rows=30))
    ok &= report("the roof party: lift up, walk about, back to the lift, down", *run(
        [(b"`", .5), (b"p", 1.0), (b"w", 6.0), (b"w", .6), (b"a", .5), (b"W", .6),
         (b"s", .6), (b"s", .6), (b"s", .6), (b"s", .6), (b"s", 6.0)],
        cols=100, rows=30))
    ok &= report("the stock exchange: buy, more, sell, walk out", *run(
        [(b"`", .5), (b"e", 1.0), (b"b", .4), (b"+", .3), (b"b", .4), (b"n", .4),
         (b"l", .4), (b"\x1bOB", .3), (b"\x1bOB", .3), (b"b", .4), (b"\x1bOA", .3),
         (b"l", .4), (b"\x1bOC", .3), (b"-", .3), (b"s", .6), (b"s", .6)],
        cols=100, rows=30))
    ok &= report("money: +1000 in the menu, a film, a bowl, walk out", *run(
        [(b"`", .5), (b"+", .4), (b"m", 2.0), (b"s", .6), (b"s", .6), (b"`", .5),
         (b"r", .6)] + IN + [(b"s", .1), (b"w", 5.0), (b"s", .6), (b"s", .6)],
        cols=100, rows=30))
    ok &= report("a manhole: down, along the tunnel, back up the ladder", *run(
        [(b"`", .5), (b"x", 1.0)] + [(b"w", .25)] * 3
        + [(b"e", 1.0), (b"d", .4), (b"w", .4), (b"a", .4), (b"s", .4), (b"e", .8),
           (b"w", .4)], cols=100, rows=30))
    ok &= report("the lair: through the door, a slice, back out", *run(
        [(b"`", .5), (b"5", 1.0)] + [(b"w", .25)] * 6
        + [(b"p", .5), (b"s", .6), (b"w", .3)], cols=300, rows=90))
    ok &= report("the temple: across the street, in, the word of god twice, out", *run(
        [(b"`", .5), (b"*", 1.0)] + IN + IN + [(b"g", .3), (b"g", .45), (b"g", .7),
                                                 (b"s", .6),
         (b"s", .6)], cols=100, rows=30))
    ok &= report("the confession booth: in, type with q and s in it, confess, esc, out",
                 *run([(b"`", .5), (b"*", 1.0)] + IN + IN + [(b"c", 1.6)]
                      + [(bytes([c_]), .05) for c_ in b"i quit my job and stole"]
                      + [(b"\x7f", .1), (b"l", .1), (b"\r", 3.0), (b"\x1b", .5),
                         (b"s", .6), (b"s", .6)], cols=100, rows=30))
    ok &= report("a blackout: to the night, the power going, walking in the dark", *run(
        [(b"`", .5), (b"&", 8.0), (b"w", 1.0), (b"`", .4), (b"c", 1.5)],
        cols=100, rows=30))
    ok &= report("a taxi: hail, it pulls up, choose, ride, arrive", *run(
        [(b"t", 3.6), (b"\x1bOB", .3), (b"s", .3), (b"w", .3), (b"\r", 15.0),
         (b"w", .5)], cols=100, rows=30))
    for cab_size in ((100, 30), (300, 90)):
        ok &= report("drive the cab yourself, %dx%d" % cab_size, *run(
            [(b"t", 3.6), (b"d", .6), (b"w", .3), (b"w", 1.5), (b"a", .1), (b"a", .1),
             (b"a", .4), (b"m", .3), (b"m", .3), (b"h", .3), (b"x", .3)]
            + [(b"e", .04), (b"d", .04)] * 12
            + [(b" ", 2.5), (b"x", 1.0), (b"w", .5)], cols=cab_size[0], rows=cab_size[1]))
    ok &= report("a fog night: to it, walk, a taxi through it", *run(
        [(b"`", .5), (b"#", 1.0), (b"w", 1.0), (b"W", 1.0), (b"t", 3.6), (b"\r", 8.0)],
        cols=100, rows=30))
    ok &= report("pace: up to very fast, walk, run into a wall, back down", *run(
        [(b"+", .2)] * 4 + [(b"w", .5), (b"W", .2), (b"W", 1.0)] + [(b"-", .2)] * 3
        + [(b"w", .5)], cols=100, rows=30))
    ok &= report("the factories: the zone, the site, into the rave and out", *run(
        [(b"`", .5), (b"9", 1.5), (b"W", 1.0), (b"`", .5), (b"]", 1.5), (b"`", .5),
         (b"}", 1.5), (b"w", 1.0), (b"`", .5), (b"[", 1.5)] + [(b"w", .25)] * 14
        + [(b"x", 1.0), (b"s", .6), (b"s", .6)],
        cols=100, rows=30))
    ok &= report("the suburbs: to them, walk a curving street, a taxi out", *run(
        [(b"`", .5), (b"0", 1.5), (b"w", 1.0), (b"W", 1.0), (b"a", .5), (b"w", 1.0),
         (b"t", 3.6), (b"\x1b", .4)], cols=100, rows=30))
    ok &= report("lemonade at 3am: buy three, and the stargazer's telescope", *run(
        [(b"`", .5), (b";", 1.5), (b"w", .4), (b"p", .4), (b"p", .4), (b"p", 1.0),
         (b"s", .6), (b"`", .5), (b"?", 1.5), (b"w", .4), (b"x", 10.0), (b"s", .6)],
        cols=100, rows=30))
    ok &= report("the strip: to it, run up the boulevard, into a hotel's casino", *run(
        [(b"`", .5), (b":", 1.5), (b"+", .2), (b"W", 1.0), (b"W", 1.0), (b"d", .4),
         (b"d", .4), (b"w", 1.0), (b"w", 1.0), (b"s", .6)], cols=100, rows=30))
    ok &= report("the airport: the end of the runway, watch one land, turn round", *run(
        [(b"`", .5), (b"'", 6.0), (b"a", .4), (b"a", .4), (b"a", 3.0), (b"w", 1.0)],
        cols=100, rows=30))
    ok &= report("the fountain show: to it, and watch the start", *run(
        [(b"`", .5), (b"(", 14.0), (b"a", .4), (b"d", .4)], cols=100, rows=30))
    ok &= report("the university: the quad, across it, the panel's other page", *run(
        [(b"`", .5), (b"\t", .4), (b"{", 1.5), (b"w", 1.0), (b"w", 1.0), (b"`", .5),
         (b"\t", .4), (b"\t", .4), (b"`", .4)], cols=80, rows=24))
    # Walking in is the reading room. w hands the terminal to the Wikipedia
    # reader, which opens on its search prompt: esc out of that, then q back to
    # the room; p the same for PsychonautWiki; x out onto the quad. Not s after:
    # backing up is back through the doors. Up to walk in, not w: inside, w is
    # Wikipedia.
    lib_st, lib_out = run([(b"`", .5), (b'"', 1.5)] + [(b"\x1bOA", .3)] * 8   # up: in
                          + [(b"w", 2.5), (b"\x1b", 1.5), (b"q", 1.5),
                             (b"p", 2.5), (b"\x1b", 1.5), (b"q", 1.5),
                             (b"x", .8)] + [(b"w", .3)] * 4,
                          cols=100, rows=30)
    lib_txt = ANSI.sub(b"", lib_out).decode("utf-8", "replace")
    ok &= report("the library: the room, both readers, back out on the quad",
                 lib_st, lib_out)
    seen = ("THE READING ROOM" in lib_txt and "wiki_tui" in lib_txt
            and "psychonaut_tui" in lib_txt
            # back on the street after it: its HUD. Not the library's hint -
        # on a fog night "the fog is in" has the hint line, and the night
        # follows the real clock.
        and lib_txt.rfind("ws walk") > lib_txt.rfind("psychonaut_tui"))
    print("%-34s %s" % ("  and both readers came up, and went",
                        "ok" if seen else "FAIL"))
    ok &= seen
    ok &= report("a flight: the gate, a seat, off, doze, land, out", *run(
        [(b"`", .5), (b".", 1.5)] + [(b"w", .3)] * 6 + [(b"\r", 4.0), (b"\x1bOD", .3),
         (b"\x1bOC", .3), (b"x", 1.0)] + [(b"", 3.0)] * 9 + [(b"w", .3)],
        cols=100, rows=30))
    ok &= report("a flight: the gate, and straight back out", *run(
        [(b"`", .5), (b".", 1.5)] + [(b"w", .3)] * 6 + [(b"x", .8), (b"w", .4)],
        cols=80, rows=24))
    # Up to walk in, not w; h to heal, c the PC - the type chart, which q quits -
    # then x out, and the street again: its "walk in" hint is back after the PC.
    pc_st, pc_out = run([(b"`", .5), (b",", 1.5)] + [(b"\x1bOA", .25)] * 14
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
        [(b"`", .5), (b"-", 1.5), (b"e", 1.0), (b"s", .5), (b"\r", .5)]
        + [(b"", 3.0)] * 15 + [(b"x", .5)], cols=100, rows=30))
    ok &= report("the metro: down and straight back up", *run(
        [(b"`", .5), (b"-", 1.5), (b"e", 1.0), (b"w", .4), (b"x", .8), (b"w", .5)],
        cols=80, rows=24))
    # A zoomed-out window: the room in block letters, and z gives back the
    # small one - its banner in plain letters - and z again the big.
    big_st, big_out = run([(b"`", .5), (b"c", 1.0)] + IN
                          + [(b"p", 2.0), (b"b", 1.0), (b"z", .8), (b"z", .8),
                             (b"s", .6), (b"s", .6)], cols=300, rows=90)
    ok &= report("the big casino on a big window: spin, pull, deal, z off and on",
                 big_st, big_out)
    big_txt = ANSI.sub(b"", big_out).decode("utf-8", "replace")
    seen = big_txt.count("#") > 500 and bool(re.search(r"CASINO  [A-Z]", big_txt))
    print("%-34s %s" % ("  and z gave the small room back", "ok" if seen else "FAIL"))
    ok &= seen
    ok &= report("the big casino's games: plinko, the races, high flyer, and back",
                 *run([(b"`", .5), (b"c", 1.0)] + IN
                      + [(b"o", .8), (b"p", 3.0), (b"o", .5), (b"r", .8), (b"1", .5),
                         (b"r", .5), (b"f", .8), (b"p", 2.5), (b"f", .5), (b"s", .6),
                         (b"s", .6)], cols=300, rows=90))
    # The arcade on a big window: the menu puts you inside; a game, big, then
    # z gives the small one - its plain-letter name - and z again the big.
    arc_st, arc_out = run([(b"`", .5), (b"g", 2.0), (b"p", 1.0), (b"p", .5),
                           (b"p", .5), (b"z", .8), (b"z", .8), (b"x", .6), (b"s", .6),
                           (b"s", .6)], cols=300, rows=90)
    ok &= report("the big arcade: in, a game, z off and on, out", arc_st, arc_out)
    arc_txt = ANSI.sub(b"", arc_out).decode("utf-8", "replace")
    seen = arc_txt.count("#") > 500 and "SCORE" in arc_txt
    print("%-34s %s" % ("  and z gave the small game back", "ok" if seen else "FAIL"))
    ok &= seen
    # The Center on a big window: heal, then z small, z big again, out.
    pcb_st, pcb_out = run([(b"`", .5), (b",", 1.5)] + [(b"\x1bOA", .25)] * 14
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
        [(b"`", .5), (b"2", 1.5)] + [(b"\x1bOA", .3)] * 6
        + [(b"", 9.0), (b"d", .3), (b"a", .3), (b"s", 8.0)], cols=300, rows=90))
    ok &= report("feeding the pigeons", *run(
        [(b"`", .5), (b"2", 1.5)] + [(b"\x1bOA", .3)] * 6
        + [(b"", 9.0), (b"f", 3.0), (b"r", 2.0), (b"n", 2.0), (b"d", .3),
           (b"a", .3), (b"s", 8.0)], cols=110, rows=34))
    ok &= report("under the washing lines", *run(
        [(b"`", .5), (b"3", 1.5)] + [(b"w", .25)] * 10, cols=300, rows=90))
    for bw_size in ((110, 34), (300, 90)):
        ok &= report("a frame of bowling, %dx%d" % bw_size, *run(
            [(b"`", .5), (b"4", 1.5), (b"p", .4), (b"d", .2), (b"a", .2), (b"p", .4),
             (b"p", 5.0), (b"p", .4), (b"p", .4), (b"z", .3), (b"x", .4)],
            cols=bw_size[0], rows=bw_size[1]))
    ok &= report("a jump off a roof takes you off the roof", *run(
        [(b"`", .5), (b"^", 1.5)] + [(b"\x1bOA", .3)] * 6
        + [(b"", 7.0), (b"`", .4), (b"c", 1.0), (b"w", .3)], cols=110, rows=34))
    ok &= report("the mystery, a note and the first clue", *run(
        [(b"`", .5), (b"6", .5), (b"7", 1.5), (b"j", .3), (b"j", .3),
         (b"`", .3), (b"7", 1.5)], cols=110, rows=34))
    for ck_size in ((110, 34), (300, 90)):
        ok &= report("flying the plane, %dx%d" % ck_size, *run(
            [(b"`", .5), (b"8", 1.0)] + [(b"+", .1)] * 10 + [(b"", 5.0)]
            + [(b"s", .1)] * 4 + [(b"", 3.0), (b"d", .1), (b"d", .1), (b"d", .1),
                                  (b"", 2.0), (b"a", .1), (b"w", .1), (b"-", .1),
                                  (b"r", 1.5), (b"f", .2), (b"g", .3), (b"p", 2.0),
                                  (b"g", .3), (b"z", .3), (b"m", .5), (b"]", .3),
                                  (b"[", .3), (b"v", 1.5), (b"l", .5),
                                  (b"a", .3), (b"v", 1.0), (b"l", .3),
                                  (b"", 1.0), (b"x", .8), (b"w", .3)],
            cols=ck_size[0], rows=ck_size[1]))
    ok &= report("the desk: a check ride, and the autopilot pushes back", *run(
        [(b"`", .5), (b".", 1.0)] + [(b"w", .25)] * 6 + [(b"t", .6), (b"p", 4.0), (b"k", 2.0),
                                                       (b"v", 1.0), (b"x", .8)],
        cols=110, rows=34))
    ok &= report("the desk: the keys, and straight into a wall", *run(
        [(b"`", .5), (b".", 1.0)] + [(b"w", .25)] * 6 + [(b"c", .6)]
        + [(b"+", .1)] * 10 + [(b"d", .1)] * 12 + [(b"", 8.0)], cols=110, rows=34))
    for rb_size in ((110, 34), (300, 90)):
        ok &= report("a drink at the rooftop bar, %dx%d" % rb_size, *run(
            [(b"`", .5), (b"1", 1.5)] + [(b"\x1bOA", .3)] * 6
            + [(b"", 8.0), (b"1", 3.2), (b"4", 3.2), (b"z", .5), (b"z", .5),
               (b"d", .3), (b"d", .3), (b"a", .3), (b"s", 8.0)],
            cols=rb_size[0], rows=rb_size[1]))
    ok &= report("a far storm out of the plane's window", *run(
        [(b"`", .5), (b".", 1.5)] + [(b"\x1bOA", .3)] * 6
        + [(b"\r", 12.0), (b"`", .4), (b"\\", .4), (b"`", .4), (b"", 4.0)],
        cols=300, rows=90))
    ok &= report("a far storm from a roof", *run(
        [(b"`", .5), (b"^", 1.5)] + [(b"\x1bOA", .25)] * 6
        + [(b"", 6.0), (b"`", .4), (b"\\", .4), (b"`", .4), (b"", 4.0), (b"s", 5.0)],
        cols=300, rows=90))
    ok &= report("the highway", *run([(b"`", .5), (b")", 1.2), (b"w", .5)],
                                     cols=100, rows=30))
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
