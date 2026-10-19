"""Four experiments to run on your own machine. Every number they print is measured or computed
there and then.

fanout   send 2,000 pushes to a real HTTP server on localhost: one request each, or in batches
outbox   what the outbox costs: one SQLite commit with and without the extra row, and the relay
backoff  1,000 senders retry through a 30 second outage: fixed delay, exponential, and jitter
digest   the same updates through four batching rules: every update, throttle, debounce, capped
"""

import heapq
import json
import os
import platform
import random
import socket
import sqlite3
import statistics
import sys
import tempfile
import threading
import time
from collections import Counter
from collections.abc import Callable
from http.client import HTTPConnection
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


def describe() -> str:
    return f"Python {sys.version.split()[0]}, {platform.system()}, {os.cpu_count()} CPUs"


# fanout


class Gateway(BaseHTTPRequestHandler):
    """A push gateway on localhost. POST /send takes one push, POST /batch takes a list."""

    protocol_version = "HTTP/1.1"  # keep the connection open between requests
    wbufsize = -1  # write the headers and body of each answer together, in one packet
    received = 0
    lock = threading.Lock()

    def do_POST(self) -> None:
        pushes = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        count = len(pushes) if self.path == "/batch" else 1
        with Gateway.lock:
            Gateway.received += count
        body = json.dumps({"accepted": count}).encode()
        self.send_response(200)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args: object) -> None:  # keep the output clean
        pass


def connect(port: int) -> HTTPConnection:
    """A keep-alive connection that sends each small write at once. Without TCP_NODELAY, Nagle's
    algorithm and delayed ACKs add about 40 ms to every request: a lesson of its own."""
    conn = HTTPConnection("127.0.0.1", port)
    conn.connect()
    conn.sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
    return conn


def post(conn: HTTPConnection, path: str, payload: object) -> None:
    body = json.dumps(payload).encode()
    conn.request("POST", path, body, {"Content-Type": "application/json"})
    conn.getresponse().read()


def fanout() -> None:
    print(describe())
    print()
    total = 2000
    pushes = [{"token": f"tok_{n:04d}", "body": "Build #419 passed on main."} for n in range(total)]
    server = ThreadingHTTPServer(("127.0.0.1", 0), Gateway)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    port = server.server_address[1]

    def one_by_one(workers: int) -> int:
        def work(part: list[dict]) -> None:
            conn = connect(port)
            for push in part:
                post(conn, "/send", push)
            conn.close()

        threads = [
            threading.Thread(target=work, args=(pushes[i::workers],)) for i in range(workers)
        ]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
        return total

    def batched(size: int) -> int:
        conn = connect(port)
        for start in range(0, total, size):
            post(conn, "/batch", pushes[start : start + size])
        conn.close()
        return -(-total // size)

    ways: list[tuple[str, Callable[[], int]]] = [
        ("one request each, 1 connection", lambda: one_by_one(1)),
        ("one request each, 8 connections", lambda: one_by_one(8)),
        ("batches of 100, 1 connection", lambda: batched(100)),
        ("batches of 500, 1 connection", lambda: batched(500)),
    ]
    print(f"  {'way':<34}{'requests':>9}{'seconds':>10}{'pushes/s':>11}")
    for label, fn in ways:
        timings = []
        for _ in range(3):
            Gateway.received = 0
            start = time.perf_counter()
            requests = fn()
            timings.append(time.perf_counter() - start)
            assert Gateway.received == total
        seconds = statistics.median(timings)
        print(f"  {label:<34}{requests:>9}{seconds:>10.3f}{total / seconds:>11,.0f}")
    server.shutdown()
    print()
    print("Median of three runs. Every push reached the server in every run. A real gateway is")
    print("across a network, so each request also pays a round trip: batching saves more there.")


# outbox


def database(path: Path, rows: int) -> sqlite3.Connection:
    db = sqlite3.connect(path, isolation_level=None)
    db.executescript(
        """
        PRAGMA journal_mode = WAL;
        PRAGMA synchronous = FULL;
        CREATE TABLE invoices (id INTEGER PRIMARY KEY, status TEXT);
        CREATE TABLE outbox (id INTEGER PRIMARY KEY, recipient TEXT, body TEXT,
                             sent INTEGER DEFAULT 0);
        """
    )
    db.executemany("INSERT INTO invoices VALUES (?, 'open')", [(n,) for n in range(rows)])
    return db


def outbox() -> None:
    print(f"{describe()}, SQLite {sqlite3.sqlite_version}, WAL, synchronous = FULL")
    print()
    rounds, per_round = 3, 1000

    def update(db: sqlite3.Connection, n: int) -> None:
        db.execute("UPDATE invoices SET status = 'paid' WHERE id = ?", (n,))

    def add_row(db: sqlite3.Connection, n: int) -> None:
        db.execute(
            "INSERT INTO outbox (recipient, body) VALUES (?, ?)", (f"u_{n}@example.com", "Paid.")
        )

    def change_only(db: sqlite3.Connection, n: int) -> None:
        db.execute("BEGIN")
        update(db, n)
        db.execute("COMMIT")

    def change_and_outbox(db: sqlite3.Connection, n: int) -> None:
        db.execute("BEGIN")
        update(db, n)
        add_row(db, n)
        db.execute("COMMIT")

    def two_commits(db: sqlite3.Connection, n: int) -> None:
        change_only(db, n)
        db.execute("BEGIN")
        add_row(db, n)
        db.execute("COMMIT")

    with tempfile.TemporaryDirectory() as folder:
        print(f"  {'one payment':<40}{'per payment':>14}")
        for label, fn in [
            ("change only, one commit", change_only),
            ("change and outbox row, one commit", change_and_outbox),
            ("change, then outbox row, two commits", two_commits),
        ]:
            db = database(Path(folder, f"{fn.__name__}.db"), rounds * per_round)
            timings = []
            for r in range(rounds):  # each round pays invoices it has not touched yet
                start = time.perf_counter()
                for n in range(r * per_round, (r + 1) * per_round):
                    fn(db, n)
                timings.append((time.perf_counter() - start) / per_round)
            db.close()
            print(f"  {label:<40}{statistics.median(timings) * 1e6:>11.1f} µs")

        db = database(Path(folder, "relay.db"), 0)
        db.execute("BEGIN")
        for n in range(20_000):
            add_row(db, n)
        db.execute("COMMIT")
        start = time.perf_counter()
        relayed = 0
        while True:  # the relay: read a page of rows, send them, mark them sent in one commit
            rows = db.execute(
                "SELECT id FROM outbox WHERE sent = 0 ORDER BY id LIMIT 500"
            ).fetchall()
            if not rows:
                break
            db.execute("BEGIN")
            db.executemany("UPDATE outbox SET sent = 1 WHERE id = ?", rows)
            db.execute("COMMIT")
            relayed += len(rows)
        seconds = time.perf_counter() - start
        db.close()
    print()
    print(f"  relay, pages of 500: {relayed:,} rows marked sent in {seconds * 1e3:.0f} ms")
    print(f"  that is {relayed / seconds:,.0f} rows a second, before any sending")
    print()
    print("Median of three rounds of 1,000. The outbox row rides in a commit you were making")
    print("anyway. The commit is the expensive part, so a second one costs most.")


# backoff


def equal_jitter(tries: int, rng: random.Random) -> float:
    ceiling = min(60.0, 2.0**tries)
    return ceiling / 2 + rng.uniform(0, ceiling / 2)


def backoff() -> None:
    senders, outage, capacity = 1000, 30.0, 200
    print(f"{senders} sends fail at 0 s. The provider is down until {outage:.0f} s,")
    print(f"then answers {capacity} requests a second and sends 503 to the rest.")
    print()

    def simulate(delay: Callable[[int, random.Random], float]) -> tuple[int, int, float, int]:
        rng = random.Random(7)
        due = [(0.0, n, 0) for n in range(senders)]
        per_second: Counter[int] = Counter()
        done, last, requests = 0, 0.0, 0
        while due:
            when, sender, tries = heapq.heappop(due)
            requests += 1
            second = int(when)
            per_second[second] += 1
            if when >= outage and per_second[second] <= capacity:
                done += 1
                last = when
                continue
            heapq.heappush(due, (when + delay(tries, rng), sender, tries + 1))
        busiest = max(count for second, count in per_second.items() if second >= outage)
        return requests, busiest, last, done

    strategies: list[tuple[str, Callable[[int, random.Random], float]]] = [
        ("retry every second", lambda tries, rng: 1.0),
        ("exponential, 1 2 4 8 ... 60 s", lambda tries, rng: min(60.0, 2.0**tries)),
        ("exponential, full jitter", lambda tries, rng: rng.uniform(0, min(60.0, 2.0**tries))),
        ("exponential, equal jitter", lambda tries, rng: equal_jitter(tries, rng)),
    ]
    print(f"  {'strategy':<32}{'requests':>9}{'busiest second':>16}{'all sent by':>13}")
    for label, delay in strategies:
        requests, busiest, last, done = simulate(delay)
        assert done == senders
        print(f"  {label:<32}{requests:>9,}{busiest:>16,}{last:>11.1f} s")
    print()
    print("Simulated with a fixed seed, so you will see these exact numbers.")


# digest

QUIET, CAP, GAP = 10, 30, 15

PATTERNS = {
    "busy project": list(range(0, 180, 5)),
    "a burst": [*range(30, 42), 150],
    "quiet day": [10, 12, 15, 120],
}


def policy_pushes(rule: str, updates: list[int]) -> list[tuple[int, list[int]]]:
    """Run one batching rule over updates (minutes). Returns (minute sent, updates carried)."""
    pushes: list[tuple[int, list[int]]] = []
    pending: list[int] = []
    due = started = 0
    last = -(10**9)
    for now in range(max(updates, default=0) + 60):
        if pending:
            ready = now - last >= GAP if rule == "throttle" else now >= due
            if ready:
                pushes.append((now, pending))
                last, pending = now, []
        for update in (u for u in updates if u == now):
            if rule == "every" or (rule == "throttle" and not pending and now - last >= GAP):
                pushes.append((now, [update]))
                last = now
                continue
            if not pending:
                started = now
            pending.append(update)
            due = now + QUIET if rule == "debounce" else min(now + QUIET, started + CAP)
    return pushes


RULES = {
    "every": "every update",
    "throttle": f"throttle, {GAP} min",
    "debounce": f"debounce, {QUIET} min",
    "capped": f"debounce {QUIET}, cap {CAP}",
}


def summary(rule: str, updates: list[int]) -> tuple[int, int]:
    pushes = policy_pushes(rule, updates)
    waits = [sent - made for sent, carried in pushes for made in carried]
    assert sorted(made for _, carried in pushes for made in carried) == sorted(updates)
    return len(pushes), max(waits)


def digest() -> None:
    print("Updates for one user, in minutes. A push carries every update waiting for it.")
    for name, updates in PATTERNS.items():
        print()
        print(f"{name}: {len(updates)} updates")
        print(f"  {'rule':<22}{'pushes':>7}{'longest wait':>14}")
        for rule, label in RULES.items():
            count, wait = summary(rule, updates)
            print(f"  {label:<22}{count:>7}{wait:>10} min")
    rng = random.Random(11)
    day = []
    for _ in range(1000):  # a thousand users, most quiet, a few very busy
        busy = rng.random() < 0.05
        count = rng.randint(40, 120) if busy else rng.randint(1, 6)
        day.append(sorted({rng.randrange(0, 600) for _ in range(count)}))
    print()
    print(f"a seeded working day: {len(day):,} users, {sum(map(len, day)):,} updates")
    print(f"  {'rule':<22}{'pushes':>7}{'longest wait':>14}")
    for rule, label in RULES.items():
        results = [summary(rule, updates) for updates in day]
        pushes = sum(count for count, _ in results)
        wait = max(w for _, w in results)
        print(f"  {label:<22}{pushes:>7,}{wait:>10} min")


EXPERIMENTS: dict[str, Callable[[], None]] = {
    "fanout": fanout,
    "outbox": outbox,
    "backoff": backoff,
    "digest": digest,
}
