# Send after commit: the outbox

> A notification is a promise about something that happened. Send it only once that thing has really happened, and make sure it is still sent if the process dies a moment later.

**Time:** 20 minutes

## Goal

By the end of this chapter you can describe the parts of a notification system, explain the dual write problem, and fix it with a transactional outbox.

## The idea

### What a notification system does

Every notification system, from a two-line script to a platform sending billions a day, does the same five things:

1. **An event happens.** A payment clears, someone is invited, a build fails.
2. **Decide.** Who should hear about it, on which channel, and is now a good time?
3. **Render.** Turn the event into a message: a subject, a body, a push payload.
4. **Deliver.** Hand it to a provider: an email API, an SMS gateway, a push service.
5. **Learn what happened.** The provider reports back: delivered, bounced, failed.

Each step fails in its own ways. This workshop takes them in roughly that order, one failure per chapter, starting with the gap between steps 1 and 4.

### Two systems, no shared transaction

When an admin invites someone to a workspace, two things must happen: the database records the membership, and the person gets an email. The database and the email provider are separate systems, and no transaction covers both. Whichever you do first, the process can fail before the second. This is the **dual write problem**, and it has two ways to go wrong:

| What happened | What the user sees |
| --- | --- |
| email sent, database change rolled back | told about something that did not happen |
| database committed, email never sent | something happened and nobody was told |

The first is worse, because people act on it. They click the link and find no workspace.

### Why "send after commit" is not enough

Moving the send after `COMMIT` fixes the first row of the table. It does not fix the second: if the process dies between the commit and the send, the email is lost, and nothing remembers that it was owed.

### The transactional outbox

The fix is to make the notification part of the same transaction as the change:

1. In the transaction, insert a row into an `outbox` table: who, what, and a `sent` flag.
2. Commit. The change and the notification now exist together, or not at all.
3. A separate **relay** reads unsent rows, sends them, and marks them sent.

If the relay dies after sending and before marking, the row is sent again on restart. The outbox gives you **at-least-once** delivery. Chapter 02 makes the repeats harmless.

## The case

Open `lab/cases/case01_outbox.py`. Inviting someone inserts a membership, emails the invite and takes a seat on the workspace's plan, all inside one transaction. `ws_orbit` is on a plan with no free seats, so its `CHECK (free_seats >= 0)` fails and the transaction rolls back.

```bash
cd lab
uv sync
uv run python -m notify run 1
```

```text
sending 5 invitations
  dana@example.com   ws_acme   added
  eli@example.com    ws_acme   added
  fay@example.com    ws_orbit  no free seat, rolled back
  gus@example.com    ws_acme   added
  hal@example.com    ws_orbit  no free seat, rolled back

emails sent: 5
emails for memberships that do not exist: 2
  fay@example.com was told they joined ws_orbit. They did not.
  hal@example.com was told they joined ws_orbit. They did not.
```

The rollback worked perfectly. The database is right. A rollback cannot recall an email: anything you do to the outside world inside a transaction is not part of the transaction.

## Reasoning towards the fix

The service already has an `outbox` table and a `relay()` that runs after every invite. Nothing writes to the outbox yet. Replace the call to the email provider with an insert into the outbox, inside the same transaction. If the seat update fails, the outbox row rolls back with the membership.

## Check your fix

```bash
uv run python -m notify check 1
```

As shipped:

```text
  FAIL  no email for an invite that rolled back (2 sent)
  PASS  every new member gets exactly one email (3 joined)
  PASS  a crash straight after the commit still sends the email, once
  FAIL  no email when the commit itself fails
```

The checker runs the batch three times: as is, with the process crashing straight after one commit, and with one commit failing. Moving the send after the commit, without an outbox, passes the first check and fails the crash check: the email after the crash is lost.

`uv run python -m notify try outbox` measures what the outbox costs in a real SQLite commit on your machine:

```text
  one payment                                per payment
  change only, one commit                       535.1 µs
  change and outbox row, one commit             576.7 µs
  change, then outbox row, two commits         1183.8 µs
```

The row rides in a commit you were making anyway. The commit is the expensive part.

## In production

- **The relay.** Poll for unsent rows in small pages, oldest first, or stream them with change data capture (Debezium reading the write-ahead log). Mark rows sent, then delete or archive them on a schedule.
- **Many relays.** Run more than one for availability, and claim rows with `SELECT ... FOR UPDATE SKIP LOCKED` in Postgres so two relays never take the same row.
- **Events, not emails.** In a larger system the outbox holds domain events (`member.invited`), and a notification service decides what to send. The principle is the same: the event commits with the change.
- **Same database.** The outbox only works because it shares a transaction with the change. It must live in the same database.

## Key points

- A notification system: event, decide, render, deliver, learn what happened.
- A database and a provider cannot share a transaction. That is the dual write problem.
- Write the notification as an outbox row in the same transaction, and send it after commit.
- The outbox gives at-least-once delivery, so sends must be safe to repeat.
