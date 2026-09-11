"""Ordinary play, driven through a real terminal.

    python3 tests/pty_checks.py

Forks a pty, sets its size with TIOCSWINSZ, types at it and reads back what
curses emits. This is the only way to test the input handling and the blit
loop - checks.py never goes near a terminal - and it is what catches a local
name shadowing loop state in main(), which no amount of headless rendering
will show you.

Watch out writing new cases here: an arrow key is "\x1b[C", and a program that
quits on bare ESC may read it as one. Two dead-end investigations started that
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

ok = True
ok &= report("walk, turn, sidestep", *run(
    [(b"w",.5),(b"W",.6),(b"a",.5),(b"d",.4),(b"s",.4),(b",",.3),(b".",.3)]))
ok &= report("tab to skyline and back", *run(
    [(b"\t",.6),(b"l",.4),(b"L",.4),(b"\t",.6),(b"w",.5)]))
ok &= report("wander on spacebar", *run([(b" ", 5.0)]))
ok &= report("panel open, arrows still walk", *run(
    [(b"`",.6),(b"\x1b[A",.4),(b"\x1b[C",.4),(b"\x1b[B",.4),(b"`",.4),(b"w",.4)]))
ok &= report("panel keys then esc then play", *run(
    [(b"`",.5),(b"3",.7),(b"w",.4),(b"L",.6),(b"\x1b",.4),(b"w",.5),(b"a",.4)]))
ok &= report("TERM=xterm (8 colours)", *run(
    [(b"`",.5),(b"1",.7),(b"\x1b",.3),(b"w",.4)], term="xterm"))
ok &= report("20x8 window with panel", *run(
    [(b"`",.5),(b"2",.7),(b"w",.4)], cols=20, rows=8))
ok &= report("240x70 window with panel", *run(
    [(b"`",.5),(b"6",.7),(b"w",.4)], cols=240, rows=70))
print("ALL OK" if ok else "FAILURES")
sys.exit(0 if ok else 1)
