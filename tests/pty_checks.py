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

ok = True
ok &= report("walk, turn, sidestep", *run(
    [(b"w",.5),(b"W",.6),(b"a",.5),(b"d",.4),(b"s",.4),(b",",.3),(b".",.3)]))
ok &= report("tab to skyline and back", *run(
    [(b"\t",.6),(b"l",.4),(b"L",.4),(b"\t",.6),(b"w",.5)]))
ok &= report("wander on spacebar", *run([(b" ", 5.0)]))
ok &= report("panel open, arrows still walk", *run(
    [(b"`",.6),(b"\x1bOA",.4),(b"\x1bOC",.4),(b"\x1bOB",.4),(b"`",.4),(b"w",.4)]))
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
    [(b"`", .5), (b"c", 1.0)] + IN + [(b"+", .3), (b"p", 3.0), (b"-", .3), (b"p", 3.0),
     (b"b", .6), (b"k", 3.0)], cols=100, rows=30))
ok &= report("sky deck: lift up, look round, lift down", *run(
    [(b"`", .5), (b"^", 1.0), (b"w", 6.0), (b"d", .5), (b"a", .5), (b"s", 6.0),
     (b"w", .4)], cols=100, rows=30))
ok &= report("fire escape: climb, look round, climb down", *run(
    [(b"`", .5), (b"|", 1.0), (b"w", 1.0), (b"w", 4.0), (b"d", .5), (b"s", 1.0),
     (b"w", 4.0)], cols=100, rows=30))
ok &= report("the pictures: go in, watch, walk out", *run(
    [(b"`", .5), (b"m", 2.5), (b"s", .6), (b"s", .6), (b"w", .4)], cols=100, rows=30))
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
    [(b"`", .5), (b"c", 1.0)] + IN + [(b"`", .5), (b"%", .4), (b"`", .3), (b"p", 3.5),
     (b"s", .6), (b"s", .6), (b"s", 1.0)], cols=100, rows=30))
ok &= report("the plinko machine: over to it, bet up, drop three, back, out", *run(
    [(b"`", .5), (b"c", 1.0)] + IN + [(b"o", .4), (b"+", .2), (b"p", .2), (b"p", .2),
     (b"p", 3.0), (b"o", .4), (b"s", .6), (b"s", .6)], cols=100, rows=30))
ok &= report("the races: over to the track, stake up, two bets, watch, back", *run(
    [(b"`", .5), (b"c", 1.0)] + IN + [(b"r", .4), (b"+", .2), (b"1", .2), (b"4", 3.0),
     (b"r", .4), (b"s", .6), (b"s", .6)], cols=100, rows=30))
ok &= report("plinko, bigger and harder: rows up, high risk, drop, rows down", *run(
    [(b"`", .5), (b"c", 1.0)] + IN + [(b"o", .4), (b"]", .2), (b"]", .2), (b"3", .2),
     (b"p", 3.5), (b"[", .3), (b"1", .3), (b"p", 2.5), (b"o", .4), (b"s", .6),
     (b"s", .6)], cols=100, rows=30))
ok &= report("closing time at the club, outside and in", *run(
    [(b"`", .5), (b"/", .4), (b"k", 4.5)] + IN + [(b"s", .6)], cols=100, rows=30))
ok &= report("the strength tester: swing, swing again, walk out", *run(
    [(b"`", .5), (b"h", 1.0), (b"p", 2.5), (b"p", 2.5), (b"s", .6), (b"s", .6)],
    cols=100, rows=30))
ok &= report("the roof party: lift up, walk about, back to the lift, down", *run(
    [(b"`", .5), (b"p", 1.0), (b"w", 6.0), (b"w", .6), (b"a", .5), (b"W", .6),
     (b"s", .6), (b"s", .6), (b"s", .6), (b"s", .6), (b"s", 6.0)], cols=100, rows=30))
ok &= report("the stock exchange: buy, more, sell, walk out", *run(
    [(b"`", .5), (b"e", 1.0), (b"b", .4), (b"+", .3), (b"b", .4), (b"n", .4),
     (b"l", .4), (b"\x1bOB", .3), (b"\x1bOB", .3), (b"b", .4), (b"\x1bOA", .3),
     (b"l", .4), (b"\x1bOC", .3), (b"-", .3), (b"s", .6), (b"s", .6)],
    cols=100, rows=30))
ok &= report("money: +1000 in the menu, a film, a bowl, walk out", *run(
    [(b"`", .5), (b"+", .4), (b"m", 2.0), (b"s", .6), (b"s", .6), (b"`", .5),
     (b"r", .6)] + IN + [(b"s", .1), (b"w", 5.0), (b"s", .6), (b"s", .6)],
    cols=100, rows=30))
ok &= report("a manhole: walk on, down, a slice, back up", *run(
    [(b"`", .5), (b"x", 1.0)] + [(b"w", .25)] * 3
    + [(b"e", 1.5), (b"p", .5), (b"s", .8), (b"w", .4)], cols=100, rows=30))
ok &= report("the temple: across the street, in, the word of god twice, out", *run(
    [(b"`", .5), (b"*", 1.0)] + IN + IN + [(b"g", .3), (b"g", .45), (b"g", .7),
                                             (b"s", .6),
     (b"s", .6)], cols=100, rows=30))
ok &= report("the confession booth: in, type with q and s in it, confess, esc, out",
             *run([(b"`", .5), (b"*", 1.0)] + IN + IN + [(b"c", 1.6)]
                  + [(bytes([c_]), .05) for c_ in b"i quit my job and stole"]
                  + [(b"\x7f", .1), (b"l", .1), (b"\r", 3.0), (b"\x1b", .5), (b"s", .6),
                     (b"s", .6)], cols=100, rows=30))
ok &= report("a blackout: to the night, the power going, walking in the dark", *run(
    [(b"`", .5), (b"0", 8.0), (b"w", 1.0), (b"`", .4), (b"c", 1.5)], cols=100, rows=30))
ok &= report("a taxi: hail, it pulls up, choose, ride, arrive", *run(
    [(b"t", 3.6), (b"\x1bOB", .3), (b"s", .3), (b"w", .3), (b"\r", 15.0), (b"w", .5)],
    cols=100, rows=30))
ok &= report("the highway", *run([(b"`", .5), (b")", 1.2), (b"w", .5)], cols=100, rows=30))
print("ALL OK" if ok else "FAILURES")
sys.exit(0 if ok else 1)
