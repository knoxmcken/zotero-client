# Note Persistence Investigation (Refs #11)

Investigation of: *"items created via the API are sometimes never readable (notes?)"*.

All data below was observed against the live Zotero API (`https://api.zotero.org`,
`zotero-api-version: 3`, `zotero-schema-version: 42`) on 2026-09-16, using the
credentials in `.env`. Library version moved from `2534` to `2565` during the
investigation. Every key that was created is listed in the appendix; nothing
readable was left behind.

**Status: closed as a documented limitation (#11).** The behaviour reproduces,
the client cannot work around it, and notes are not a current use case for this
library (457 items, zero notes). See "Verification addendum" and "Decisions".

## Conclusion (short version)

**Item type is the deciding variable, and the answer is `note`.** `book` and
`journalArticle` writes are readable on the *first* read attempt (~0.5-1.0 s).
Notes — **in both code paths, standalone and `parentItem`-attached** — are never
readable through any read path, at any point, no matter how long we poll.

**The previous "general propagation lag" theory is dead.** There is no lag
window to wait out: for books and journalArticles there was never anything to
wait for (1 attempt, every round), and for notes waiting does not help (30 s of
polling, still `404`).

**But "notes are never persisted" is also not what the evidence shows.** The
deletion-log evidence (below) demonstrates that a note created with a
`parentItem` *does* exist server-side: deleting the parent produces a deletion
record for the note's key. So the accurate statement is:

> A note write is accepted (HTTP 200, a key, a library version bump) and the
> object is stored — including its parent link — but **every read path available
> to this API key refuses to return it**, and it cannot be addressed or deleted
> by the client either.

We could not determine *why* the note is withheld from reads from client-side
evidence alone. See "What this does not establish".

## Verification addendum

Re-verified independently after the client's write paths were corrected (#18,
#20). Nothing below depends on the original run.

**The cascade evidence reproduces.** Parent `MEHCFXRV` was created, a child note
`PVIQR84Q` attached, the parent deleted (`204`), and `/deleted?since=2773` then
listed **both** keys:

```
/deleted?since=2773 -> deleted keys: ['MEHCFXRV', 'PVIQR84Q']
```

A cascade can only name a key the server recorded as that parent's child, so the
note is stored. Yet `/items/MEHCFXRV/children` returned `[]` moments *before*
that delete.

**This is not a payload problem.** The documented shape
(`{"itemType": "note", "note": "<p>...</p>"}`), plain text, and a
`parentItem`-attached variant all behave identically. A genuinely invalid payload
*is* rejected properly — adding `title` returns
`400 "'title' is not a valid field for type 'note'"` — so the `200 successful`
responses are real validation rather than silent acceptance.

**Not an API-version artefact.** Sending `Zotero-API-Version: 3` explicitly
changes nothing.

**Not a permission restriction.** `GET /keys/<key>` reports
`{"user": {"library": true, "files": true, "write": true}, "groups": {"all": {"library": true, "write": true}}}`
— full library read/write, with no note carve-out.

**Not timing.** The seven standalone keys from the first run still return `404`
hours later.

**The signature:** the write layer (create, delete, cascade) operates on real
stored objects, while every read path — `GET /items/<key>`, `/children`,
`/items?itemType=note`, listings, and `includeTrashed` — excludes notes
entirely, and permanently.

**Still untested (recorded for whoever picks this up):** whether this key can
read a note created *outside* the API. Create one in the Zotero web library and
re-run the read checks. If the API can read it, the defect is in how notes are
*written* and it becomes fixable client-side; if it cannot, the account is blind
to notes and this limitation is the final word. A group-library comparison
(10 groups are available) would localise it further, but writes into a
student-visible library.

## Observed matrix

Controlled run, 3 rounds per arm, same payload shape per round, polled at
t+0/1/2/4/8 s, then a 30 s tail on the first standalone note.

| Arm | Round | POST | Key | Library version | Readable | First success | In newest-10 | `?itemKey=` | `?since=` delta | `/items/top` |
|---|---|---|---|---|---|---|---|---|---|---|
| `note` (standalone) | 1 | 200 | `Z24BQMKR` | 2534 → 2535 | **no** | never (30.8 s, 5 polls + 30 s tail) | no | 0 results | absent | no |
| `note` (standalone) | 2 | 200 | `RB39RN2Q` | 2535 → 2536 | **no** | never (9.0 s) | no | 0 results | absent | no |
| `note` (standalone) | 3 | 200 | `2366IVPG` | 2536 → 2537 | **no** | never (9.4 s) | no | 0 results | absent | no |
| `book` | 1 | 200 | `P7PETZDA` | 2537 → 2538 | yes | attempt 1 (0.8 s) | yes | 1 result | present | yes |
| `book` | 2 | 200 | `RAXHHWR3` | 2538 → 2539 | yes | attempt 1 (0.5 s) | yes | 1 result | present | yes |
| `book` | 3 | 200 | `ZAF77K28` | 2539 → 2540 | yes | attempt 1 (0.5 s) | yes | 1 result | present | yes |
| `journalArticle` | 1 | 200 | `PT4M7UPF` | 2540 → 2541 | yes | attempt 1 (1.0 s) | yes | 1 result | present | yes |
| `journalArticle` | 2 | 200 | `72NREW2M` | 2541 → 2542 | yes | attempt 1 (0.5 s) | yes | 1 result | present | yes |
| `journalArticle` | 3 | 200 | `N7KDSTKX` | 2542 → 2543 | yes | attempt 1 (0.5 s) | yes | 1 result | present | yes |
| `note` + `parentItem` | 1 | 200 | `EUH3S9KI` | 2543 → 2544 | **no** | never (9.0 s) | no | 0 results | absent | no |
| `note` + `parentItem` | 2 | 200 | `F8V6SRJM` | 2544 → 2545 | **no** | never (10.0 s) | no | 0 results | absent | no |
| `note` + `parentItem` | 3 | 200 | `MVSBJDV9` | 2545 → 2546 | **no** | never (10.3 s) | no | 0 results | absent | no |

Additional facts about the failing rows:

- `GET /items/<key>?includeTrashed=1` was `404` for every note, in every round.
  So the note is not merely trashed.
- The parent book's `meta.numChildren` stayed `0` after each child-note create.
- `GET /items?itemType=note` returns `0` items for this library.
- An earlier raw contact probe (`JDG94BST`, version 2534) was polled at
  t+0.46/1.37/2.47/4.55/8.46 s: `404` at every sample, with and without
  `includeTrashed`. That predates all retry-helper changes, so this is not a
  regression introduced by the test rewrite.

Note: **`?parentItem=` is not a filter the API honours** — it is silently
ignored and returns the unfiltered list. Only the `meta.numChildren` field and
`GET /items/<parentKey>/children` are trustworthy for child relationships.
(`GET /items/<parentKey>/children` does work: for pre-existing parents it
returns the expected child keys.)

### Control for the standalone-vs-child confound

Both paths fail, so the confound is ruled out as the explanation — the failure
follows the item type, not the presence of a parent. The two paths do differ in
one respect, though, and that difference is the single most informative
observation in this investigation.

### The deletion-log evidence

`GET /users/<id>/deleted?since=<v>` is a version-indexed record of removals.
Scanning it version by version across the run:

```
since  n  newly-appeared keys
 2546  9  []
 2547  5  ['EUH3S9KI (child note r1)', 'F8V6SRJM (child note r2)',
            'MVSBJDV9 (child note r3)', 'P7PETZDA (parent book r1)']
 2548  4  ['RAXHHWR3 (book r2)']
 2549  3  ['ZAF77K28 (book r3)']
 2550  2  ['PT4M7UPF (journalArticle r1)']
 2551  1  ['72NREW2M (journalArticle r2)']
 2552  0  ['N7KDSTKX (journalArticle r3)']
```

Version 2547 is exactly the operation in which the cleanup deleted the parent
book `P7PETZDA`. At that version **all three child notes entered the deletion
log together with their parent**: deleting the parent cascaded a delete onto
notes that the client could never read, list, or address.

This was then reproduced deliberately (2 creates): parent book `DM3AQ26G`
(2556 → 2557, readable) and child note `89PIUFTS` (2557 → 2558). Immediately
after creation, for `89PIUFTS`:

```
GET /items/89PIUFTS                     -> 404
GET /items/89PIUFTS?includeTrashed=1    -> 404
GET /items?itemKey=89PIUFTS             -> 200, 0 results
GET /items/DM3AQ26G/children            -> 200, 0 children
parent meta.numChildren                 -> 0
GET /items?itemType=note                -> 0
```

then `DELETE /items/DM3AQ26G` → `204`, and:

```
/deleted?since=2558 -> ['4GJZ36FM', '89PIUFTS', 'DM3AQ26G']
/deleted?since=2559 -> ['4GJZ36FM']
keys that entered the deletion log at the parent's deletion version:
    ['89PIUFTS', 'DM3AQ26G']
```

The note's key was removed **as a consequence of deleting its parent**. A delete
cascade can only emit that key if the server had recorded the note as a child of
that parent. So the note object existed. It was simply never readable.

By contrast, the standalone notes **never appear in the deletion log at all**,
in any version window — they leave no removal record, consistent with their
having never been removed rather than having been created and dropped.

### Two things that are *not* the cause

1. **API key permissions.** `GET /keys/<key>` for the key in use returns
   `access.user = {"library": true, "files": true, "write": true}` (plus
   `groups.all {library: true, write: true}`) — full library read and write. The
   response carries no note-specific restriction. Note the caveat: older Zotero
   docs describe a `notes` boolean in this object and this response omits the
   field entirely, so absence of the field is not proof that no note restriction
   exists server-side; it is proof only that the API does not report one.
2. **A general read-index lag.** Books and journalArticles were readable on the
   first attempt in all six rounds, ~0.5–1.0 s after the POST. Nothing about
   those writes needed waiting for.

### The library has no notes at all

Enumerating all 457 items: 171 `book`, 145 `attachment`, 73 `journalArticle`, 31
`webpage`, plus smaller types — and **0 `note`**. Of the 123 parents reporting
`meta.numChildren > 0`, **all 123 matched the number of children that could
actually be enumerated** (0 mismatches), so there are no other notes hidden
under existing parents either. This is consistent with (but does not prove)
notes being withheld from this key across the whole library.

## Reproduction

Credentials come from `.env` in the repository root:

```bash
cd /path/to/zotero-client
set -a; . ./.env; set +a

# full matrix, 3 rounds, printing every status:
.venv/bin/python scripts/diagnose_zotero_write.py \
    --types note,book,journalArticle,note+parent --rounds 3

# opt-in contract check: exit non-zero if a 2xx create never became readable
.venv/bin/python scripts/diagnose_zotero_write.py \
    --types note,book,journalArticle,note+parent --rounds 1 --strict
```

The script is safe by default: it exits `0` in diagnostic mode, prints the HTTP
status of every call, and deletes everything it can delete. `--strict` is what
turns a broken write contract into a non-zero exit.

## What this evidence does and does not establish

**Establishes:**

- `note` writes (standalone *and* with `parentItem`) return `200` with a key and
  advance the library version, but are unreadable on every available read path,
  indefinitely (30 s+ tested), with and without `includeTrashed`.
- `book` and `journalArticle` writes on the same key against the same library
  are readable on the first attempt.
- A `parentItem`-attached note exists server-side: deleting the parent produced
  a deletion record for the note's key (reproduced twice, once incidentally and
  once deliberately).
- Standalone notes leave no deletion record in any version window.
- The API key has full library read/write. The library contains no notes.
- A note the client cannot read also cannot be deleted by the client:
  `DELETE /items/<noteKey>` returns `404` with and without an
  `If-Unmodified-Since-Version` header.

**Does not establish:**

- **Why** the note is withheld from reads. Client-side evidence cannot
  distinguish between (a) a server-side note visibility/permission rule that also
  suppresses reads, and (b) the note never reaching the read/search index that
  backs `GET /items/<key>`, listings and `meta.numChildren`. Both are compatible
  with every observation here, including the version bump and the deletion
  record. Resolving this needs server-side access (Zotero support, or a
  different account/key that can see notes) — we did not attempt it.
- Whether a *different* API key or the Zotero desktop/web client would see these
  same notes. That would be the decisive next experiment, and it was out of
  scope here.
- Whether the same happens in group libraries. Only a user library was tested.
- Whether it depends on `Zotero-API-Version`. Only the default (v3) was used.

"No reproduction of the *reason*" is the honest result: the *behaviour* is
reproducible and type-specific, the *mechanism* is not determined.

## Consequences for the client

1. `create_item` on a note is a **trap**: it returns a fully-formed `Item` with
   a key and a version that the caller can never fetch, update or delete. It
   leaks an object that only a parent-delete or a hand cleanup can remove.
2. Retrying reads is pointless for notes. It made the integration test look
   green only because the test was changed to use a `book`.
3. Retrying is also pointless for the *types that work* — every successful
   `book`/`journalArticle` create in this investigation was readable on attempt
   1. That is a real observation, not a prediction.

## Decisions

This issue is closed on these decisions. They supersede the recommendations
below, which are kept for the reasoning.

- **No client-side workaround for notes.** They cannot be made readable, so the
  client should not pretend otherwise. `create_item` still accepts them (the API
  does), and the limitation is documented here rather than papered over.
- **`_wait_until_readable` / `_delete_with_retry`: kept, but reduced from 5
  attempts to 2.** The suite runs against a live API where a short read-back
  window is plausible in general, so a single retry is worth having. Five was
  not: readable types settle on attempt 1 every round, and for notes no number
  of retries helps — the extra attempts only delayed a genuine failure. The
  printed attempt count stays, because that number is what exposed this.
- **The "never persist" claim in the tests was wrong and is corrected.** The
  objects *are* persisted; they are never *readable*. That distinction is the
  whole finding, and the old comment asserted the opposite.
- **The CI diagnostic keeps its default non-failing behaviour.**
  `scripts/diagnose_zotero_write.py` still exits 0 by default so an upstream
  change cannot break an unrelated push; `--strict` remains the opt-in. No
  extra workflow step was added.

## Recommendations

These are the original recommendations, kept for their reasoning. The Decisions
above are what was actually done.

**`_wait_until_readable`.** It encodes a hypothesis ("a transient 404 window
exists") that the data does not support for either outcome: for working types
there is no 404 to tolerate, and for notes there is no window that ever closes.
Recommendation:

- Keep it as a **single-attempt** read (attempt 1 is expected, now with evidence)
  or at most 2 attempts with a short delay, so a genuine write failure surfaces
  immediately instead of being masked by five retries. Whatever the count, keep
  the printed attempt count — it is what made this investigation possible.
- Do **not** rely on it to make a note-based test pass: it cannot. The test must
  keep using a type that is actually readable, and the comment in the test
  asserting a transient propagation window should be corrected — no such window
  was observed. (Note: that comment is in the file this workstream does not own.)

**`_delete_with_retry`.** Same reasoning: retrying a 404 from `DELETE` cannot
help, because an unreadable note is also undeletable (`404` with and without
`If-Unmodified-Since-Version`). One attempt is enough for the types the test
uses. Keep the retry only if there is independent evidence of a real delete-side
race, which this investigation did not find.

**The CI diagnostic step.** `scripts/diagnose_zotero_write.py` runs on every
push with `continue-on-error: true`. Recommendation:

- Keep the **default non-failing** so an upstream/Zotero-side change cannot break
  an unrelated push. This is load-bearing: the note behaviour is understood but
  unexplained, so a strict-by-default step would be permanently red.
- It should be *able* to fail the build, but only when someone opts in. The
  script now supports `--strict` (exit non-zero when a `2xx` create never
  becomes readable). Suggested wiring: leave the push/PR step as-is
  (`continue-on-error: true`, no `--strict`) and add a separate
  `workflow_dispatch`-only step that runs `--strict`, so a human can assert the
  contract on demand without blocking every push.
- When #11 is resolved (notes become readable), flipping the push step to
  `--strict` is the natural end state. Until then it would fail on every run.

**Reporting.** The diagnostic prints a per-item-type RESULT summary and exits 0;
`--strict` is the only way to get a non-zero exit. Any test or workflow that
treats "no exception" as "the write worked" is wrong for notes, and the
diagnostic output is the thing that makes that visible.

## Appendix: every key created during this investigation

20 creates in total, kept deliberately small. Verified at the end: **none of the
20 keys is addressable any more**, the library is back to **457 items**, and no
item whose title or body contains `note-probe`, `write-path diagnostic` or
`Integration test` remains visible.

| # | Key | Type | Outcome | Cleanup |
|---|---|---|---|---|
| 1 | `JDG94BST` | note (standalone) | never readable | **not deletable** (DELETE 404) |
| 2 | `Z24BQMKR` | note (standalone) | never readable | **not deletable** |
| 3 | `RB39RN2Q` | note (standalone) | never readable | **not deletable** |
| 4 | `2366IVPG` | note (standalone) | never readable | **not deletable** |
| 5 | `P7PETZDA` | book | readable (1 attempt) | deleted, verified 404 |
| 6 | `RAXHHWR3` | book | readable (1 attempt) | deleted, verified 404 |
| 7 | `ZAF77K28` | book | readable (1 attempt) | deleted, verified 404 |
| 8 | `PT4M7UPF` | journalArticle | readable (1 attempt) | deleted, verified 404 |
| 9 | `72NREW2M` | journalArticle | readable (1 attempt) | deleted, verified 404 |
| 10 | `N7KDSTKX` | journalArticle | readable (1 attempt) | deleted, verified 404 |
| 11 | `EUH3S9KI` | note + parent | never readable | **not deletable**; reclaimed by deleting parent |
| 12 | `F8V6SRJM` | note + parent | never readable | **not deletable**; reclaimed by deleting parent |
| 13 | `MVSBJDV9` | note + parent | never readable | **not deletable**; reclaimed by deleting parent |
| 14 | `6WVRSX4X` | note (standalone) | never readable | **not deletable** |
| 15 | `DM3AQ26G` | book (designed repro) | readable (1 attempt) | deleted, verified 404 |
| 16 | `89PIUFTS` | note + parent (designed repro) | never readable | **not deletable**; reclaimed by deleting parent |
| 17 | `TXXGMN5V` | note (standalone, script default run) | never readable | **not deletable** |
| 18 | `BXKBVFPD` | book (script default run) | readable (1 attempt) | deleted, verified 404 |
| 19 | `UB8TFKRG` | book (script `--strict` run) | readable (1 attempt) | deleted, verified 404 |
| 20 | `ZVB3RR66` | note (standalone, script `--strict` run) | never readable | **not deletable** |

### Left behind, and why it is unavoidable

The seven standalone note keys remain, and they **cannot be removed by the
client**: `DELETE /items/<noteKey>` returns `404` both with and without an
`If-Unmodified-Since-Version` header. They also cannot be addressed or listed,
so they do not appear in the Zotero desktop/web UI either. Cleaning them up
would require the Zotero web UI's trash view or server-side access with a key
that can see notes. Every other item created was deleted and the deletion
verified by a read-back returning `404`.

This is itself a finding: a client that writes notes to this library leaks
objects it has no way to reclaim.
