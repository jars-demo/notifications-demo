# Send after commit: the outbox

> A notification is a promise about something that happened. Send it only once that thing has really happened, and make sure it is still sent if you crash a moment later.

**Time:** 20 minutes

## Goal

By the end of this chapter you can explain the dual write problem, say why "send after commit" is not enough on its own, and fix it with a transactional outbox.

## What a notification system is

Every notification system, from a two line script to a big platform, does the same five things:

1. **Something happens.** A parcel leaves the depot. A payment clears. Someone signs in.
2. **Decide.** Who should hear about it, on which channel, and is now a good time?
3. **Render.** Turn the event into words: "Hi Noor, DC-1043 is out for delivery on van 3."
4. **Deliver.** Hand it to an SMS gateway, a push service or an email server.
5. **Learn what happened.** The provider reports back: delivered, failed, unknown.

Each step can fail on its own. This workshop takes one failure at a time, in roughly that order. It starts with the gap between step 1 and step 4.

## Two systems, no shared transaction

When the dispatcher puts a parcel on a van, two things must happen:

- the database records that the parcel is out for delivery
- the customer gets a text

The database and the SMS gateway are separate systems. There is no transaction that covers both. Whichever you do first, the process can fail before the second. This is called the **dual write problem**, and it has only two outcomes when it goes wrong:

| What happened                          | What the customer sees                        |
| -------------------------------------- | --------------------------------------------- |
| text sent, database change rolled back | told about a parcel that is still on a shelf  |
| database committed, text never sent    | a parcel arrives with no warning, or a no-show |

Both are bad. The first is worse, because it is a lie, and people act on it. They stay in for a parcel that is not coming.

## The case

Open `lab/cases/case01_outbox.py`. At seven every morning the dispatcher assigns parcels to vans. For each one it opens a transaction, marks the parcel as out for delivery, texts the customer, and takes one space on the van. Van 3 came back full of returns this morning, so it has no space. The `CHECK (space >= 0)` constraint fails, and the transaction rolls back.

Run it:

```bash
cd lab
uv run python -m dove run 1
```

```text
dispatching 5 parcels
  DC-1041  van 7  out for delivery
  DC-1042  van 7  out for delivery
  DC-1043  van 3  van full, stays in the depot
  DC-1044  van 7  out for delivery
  DC-1045  van 3  van full, stays in the depot

texts sent: 5
texts for parcels still in the depot: 2
  Noor was told DC-1043 is out for delivery. It is on a shelf.
  Iris was told DC-1045 is out for delivery. It is on a shelf.
```

The rollback worked perfectly. The database is right. But a rollback cannot recall a text message. Anything you do to the outside world inside a transaction is not part of the transaction.

## Reasoning towards the fix

Run the checker on the code as it ships:

```bash
uv run python -m dove check 1
```

```text
  FAIL  no text for a parcel that stayed in the depot (2 sent)
  PASS  every parcel that left gets exactly one text (3 left)
  PASS  a crash straight after the commit still sends the text, once
  FAIL  no text when the commit itself fails
```

The checker does more than replay this morning. In one run, the process dies straight after the commit for DC-1042. In another, the database refuses the commit for DC-1044, as a full disk would.

The obvious fix is to move the send to after the transaction commits. That passes the refused commit and fails the crash: the commit is safe on disk, the process is gone, and nobody will ever send Ben's text. Sending as the very last line inside the transaction fails the other way round: the text is gone before the commit is refused.

You need the decision to send to be part of the same transaction as the change. Then they commit together or roll back together. The database cannot send a text, but it can store one.

That is the **transactional outbox**:

1. In the same transaction as the business change, insert a row into an `outbox` table: who to send to, and what to say.
2. A separate **relay** reads unsent rows, sends them, and marks them sent.

The case already has an `outbox` table and a `relay` method. The dispatcher just does not use them. Change `dispatch` so that the text is written to the outbox instead of sent. The relay already runs after every dispatch.

If you are stuck, `uv run python -m dove hint 1` gives three nudges, one at a time in order.

## Check it works

```text
  PASS  no text for a parcel that stayed in the depot (0 sent)
  PASS  every parcel that left gets exactly one text (3 left)
  PASS  a crash straight after the commit still sends the text, once
  PASS  no text when the commit itself fails
```

Now a rollback removes the outbox row along with the parcel change. A crash after the commit leaves the row in place, and the relay sends it when the dispatcher starts again.

## What it costs

People worry that an extra insert in every transaction is expensive. Measure it:

```bash
uv run python -m dove try outbox
```

```text
Python 3.13.16, Linux, 4 CPUs, SQLite 3.45.1, WAL, synchronous = FULL

  one dispatch                              per dispatch
  change only, one commit                       138.8 µs
  change and outbox row, one commit             138.2 µs
  change, then outbox row, two commits          247.2 µs

  relay, pages of 500: 20,000 rows marked sent in 44 ms
  that is 452,275 rows a second, before any sending
```

On this machine the outbox row added nothing you can measure. The commit, which waits for the disk, is the expensive part, and the row rides in a commit you were making anyway. Putting the row in its own transaction nearly doubles the cost, and brings back the dual write problem. Your numbers will differ. The shape should not.

## Trade-offs and when the usual advice is wrong

- **The relay is at least once.** It sends, then marks the row sent. If it crashes in between, the text goes twice. The outbox moves the problem from "maybe never" to "maybe twice", which is the problem you can solve. Chapter 02 solves it.
- **Polling or change data capture.** The relay here polls. Large systems often tail the database log instead (change data capture), which removes the polling delay. Polling every second is fine for most products.
- **"Just use a queue" is not a fix.** Publishing to a queue from inside the transaction is the same dual write with a different second system. Some queues and databases offer transactions that cover both, but only if they are the same product.
- **Order.** One relay reading `ORDER BY id` keeps the order of the changes. Several relays in parallel do not. Chapter 03 shows why the phone must not care.
- **Clean up.** An outbox grows forever unless you delete sent rows after a while. Keep them long enough to answer "did we tell her?"

## Exercise

1. Add a `sent_at` column and have the relay record when each row went out. How would you alert on rows that have waited more than a minute?
2. Make the relay crash between `send` and the update. Run the morning again. How many texts does the crashed parcel get, and why is that better than zero?
