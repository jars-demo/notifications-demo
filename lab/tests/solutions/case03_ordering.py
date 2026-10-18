"""Case 03: delivered, then out for delivery.

Every scan of a parcel becomes an event. Each event pushes a notification to the customer and
updates the tracking card on their lock screen. Two queue workers share the events, so they do
not arrive in the order they happened. The phone believes whatever arrived last. Ben's parcel is
on his doormat, and his phone says it is still on the van.
Run it: uv run python -m dove run 3
"""

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Scan:
    parcel: str
    seq: int  # the tracking service numbers each parcel's scans 1, 2, 3, ... as they happen
    status: str
    at: str  # the clock on the scanner that made the scan, as HH:MM:SS


@dataclass
class Phone:
    owner: str
    card: dict[str, str] = field(default_factory=dict)  # parcel -> status on the lock screen
    pushes: list[Scan] = field(default_factory=list)
    newest: dict[str, int] = field(default_factory=dict)  # parcel -> highest seq applied

    def receive(self, scan: Scan) -> None:
        if scan.seq <= self.newest.get(scan.parcel, 0):
            return  # older than what we show, or a repeat: drop it quietly
        self.newest[scan.parcel] = scan.seq
        self.card[scan.parcel] = scan.status
        self.pushes.append(scan)


OWNERS = {"DC-3001": "Ben", "DC-3002": "Iris", "DC-3003": "Noor"}

HAPPENED = [  # in the order the scans really happened
    Scan("DC-3001", 1, "at the depot", "06:58:10"),
    Scan("DC-3001", 2, "out for delivery", "07:30:02"),
    Scan("DC-3001", 3, "delivered", "07:28:40"),  # the van's scanner runs four minutes slow
    Scan("DC-3002", 1, "at the depot", "06:59:30"),
    Scan("DC-3002", 2, "out for delivery", "07:31:15"),
    Scan("DC-3002", 3, "missed you, retrying", "09:12:44"),
    Scan("DC-3002", 4, "out for delivery", "13:05:20"),  # second round, same afternoon
    Scan("DC-3003", 1, "at the depot", "07:01:00"),
    Scan("DC-3003", 2, "out for delivery", "07:32:40"),
    Scan("DC-3003", 3, "delivered", "07:41:05"),
]
H = HAPPENED
ARRIVED = [  # what two workers and one retry hand to the phones
    H[0],
    H[3],
    H[2],  # Ben's "delivered" overtook "out for delivery"
    H[7],
    H[1],
    H[4],
    H[4],  # a redelivered event: Iris's "out for delivery" arrives twice
    H[5],
    H[6],
    H[9],  # Noor's "delivered" overtook "out for delivery" too
    H[8],
]


def morning() -> dict[str, Phone]:
    phones = {owner: Phone(owner) for owner in OWNERS.values()}
    for scan in ARRIVED:
        phones[OWNERS[scan.parcel]].receive(scan)
    return phones


def run() -> None:
    phones = morning()
    final = {scan.parcel: scan.status for scan in HAPPENED}
    print(f"scans: {len(HAPPENED)}, events delivered: {len(ARRIVED)}")
    print()
    for parcel, owner in OWNERS.items():
        phone = phones[owner]
        pushes = ", ".join(scan.status for scan in phone.pushes)
        print(f"{owner}'s pushes:  {pushes}")
        print(f"  lock screen says: {phone.card[parcel]:<17} the truth: {final[parcel]}")
