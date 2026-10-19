# Preferences and consent

> A user's choice applies to every message sent after they make it, including messages you queued before. Check preferences at the moment you send, and keep required account notices out of the user's off switch.

**Time:** 20 minutes

## Goal

By the end of this chapter you can model notification categories and preferences, decide which notices users may turn off, and check consent at the right moment.

## The idea

### Categories, not one switch

Users do not want "notifications on" or "off". They want product news monthly, security alerts always, marketing never. Model each notification with a **category**, and store preferences per user and category, often per channel too:

| Category | Can the user turn it off? | Examples |
| --- | --- | --- |
| security | no | new sign-in, password changed, two-factor code |
| billing | no | receipt, payment failed, plan changing |
| product | yes | weekly summary, release notes |
| marketing | yes, and the law says it must be easy | offers, newsletters |

Required notices exist because a user who turns everything off still needs to know their account was taken over. Keep that list short and honest: a "required" newsletter is still a newsletter.

### Consent is a legal requirement

For marketing email, laws such as CAN-SPAM in the US, the GDPR and PECR in the UK and EU, and CASL in Canada require an easy way to unsubscribe and say it must be honoured promptly. Gmail and Yahoo also require bulk senders to support one-click unsubscribe (RFC 8058), and to honour it within two days. An unsubscribe that is ignored is a complaint, a spam report and, in some places, a fine.

### Check at send time

Notifications are often created long before they are sent: campaigns are scheduled, digests are gathered (chapter 08), quiet hours hold pushes (chapter 07), retries wait (chapter 04). The preference that matters is the one in force **when the message leaves**. Checking only when you queue it reads a stale answer.

## The case

Open `lab/cases/case06_preferences.py`. At 09:00 a campaign is queued for every user, to send at 10:00, along with a security notice for u_2002. At 09:30 u_2001 and u_2002 unsubscribe from marketing, and u_2002 turns off every optional category, and tries to turn off security too.

```bash
uv run python -m notify run 6
```

```text
09:00  the campaign is queued for every user, sending at 10:00
09:30  u_2001 and u_2002 unsubscribe from marketing

10:00  u_2001  marketing  Spring offer: 30% off annual plans
10:00  u_2002  marketing  Spring offer: 30% off annual plans
10:00  u_2003  marketing  Spring offer: 30% off annual plans
10:05  u_2002  security   New sign-in from Firefox on Linux

marketing sent after an unsubscribe: 2
```

Two people unsubscribed and were sent the campaign half an hour later.

## Reasoning towards the fix

`Preferences.allows()` is right: it lets required categories through and honours every other choice. It is called at the wrong time. Queue everything, and ask `allows()` in `tick()`, just before each send.

## Check your fix

```bash
uv run python -m notify check 6
```

As shipped:

```text
  FAIL  no marketing after an unsubscribe (2 sent)
  FAIL  the campaign reaches exactly the users still subscribed
  PASS  nobody who opted out last week gets it
  PASS  the security notice still arrives, though u_2002 turned everything off
```

Deleting everything queued for a user whenever their preferences change looks thorough, and drops the security notice. Checking both when queueing and when sending is fine.

## In production

- **Preference reads are hot.** Every send reads them. Cache them, and invalidate the cache when a user changes them, or the cache becomes the stale answer.
- **Unsubscribe links must work without signing in.** Use a signed token in the link, and act on it at once.
- **Per channel.** A user may want security alerts by email and push, but billing by email only. Store `(user, category, channel)`.
- **Audit trail.** Keep when and how consent was given or withdrawn. You may need to prove it.

## Key points

- Give every notification a category. Store preferences per user and category.
- Keep a short list of required notices that users cannot turn off.
- Check preferences when the message is sent, not when it is queued.
- Unsubscribes are a legal duty, and must be easy and immediate.
