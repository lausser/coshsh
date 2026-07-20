# Lessons

## 2026-07-03 — Legacy Python (<3.8) compat layer (spec 006)

### The compat layer must transform SOURCE, not runtime
- **Failure mode considered**: a pure "import a shim module first" approach cannot make
  an unmodified `coshsh` module import on 3.6, because `from __future__ import annotations`
  is a **compile-time** `SyntaxError` — the module never reaches runtime.
- **Prevention rule**: for compile-time incompatibilities, intercept via a `sys.meta_path`
  finder + a `SourceFileLoader` that AST-rewrites the source before `compile()`. Scope the
  finder to the owning namespace (`coshsh.*`) so stdlib/third-party stay untouched (FR-013).

### Disable the bytecode cache for transformed modules
- **Failure mode**: a `.pyc` compiled from *untransformed* source (by a modern interpreter
  or another tool) can shadow the transform on <3.8 and reintroduce the SyntaxError path;
  conversely a transformed `.pyc` would persist a shimmed artifact.
- **Prevention rule**: in the strip loader, override `get_code()` to always recompile from
  source and `set_data()` to a no-op so no `.pyc` is read or written.

### Validate in a DISPOSABLE copy, never run the suite on the host
- **Failure mode (detected the hard way)**: several *unmodified* test files
  (`test_datarecipient`, `test_recipes`, `test_extensions`, `test_for_tool`) drive a
  `datarecipient_simplesample` whose default `objects_dir="/tmp"`; its cleanup `rmtree`s
  that dir and **deletes `/tmp` itself** mid-run. In a *dirty* playground it even escalated
  to wiping the whole playground tree.
- **Detection signal**: pytest crashes at teardown with `chdir(...startdir...)` ENOENT, and
  later `tempfile`-based tests fail with `FileNotFoundError: /tmp/tmpXXXX.cfg`. Failure
  counts vary run-to-run (ordering-dependent) — a tell that it is an isolation quirk, not a
  deterministic code defect.
- **Prevention rule**: run the full suite only inside the disposable container playground
  (`/packages/coshsh/coshsh-12.2.1.1`), rebuilt fresh via `rsync` with `var/objects` removed
  (per quickstart.md). Do **not** run it on the mounted host — it can delete the host `/tmp`.
  Recreate `/tmp` & `/var/tmp` (chmod 1777) before each run.

### CentOS 7 needs an explicit UTF-8 locale
- **Failure mode**: with `LANG` unset the interpreter defaults to ASCII; Python 3.6 then
  opens cookbook files in ascii mode → `UnicodeDecodeError: 'ascii' codec ... byte 0xc3`.
- **Prevention rule**: run with `LANG=en_US.UTF-8 LC_ALL=en_US.UTF-8`. (The CI legacy job
  uses `python:<ver>-slim-bullseye`, which sets `LANG=C.UTF-8` by default, so it is immune.)

### `podman exec` needs `-i` to feed a heredoc
- **Failure mode**: `podman exec CID python3 - <<'EOF'` silently ran no code (empty stdin),
  leaving files unchanged with no error.
- **Prevention rule**: use `podman exec -i` whenever piping stdin into the container.

## 2026-07-20 — Template render-error handling (spec 007)

### "Superseded" describes a document's design status, not its information content
- **Failure mode**: while generating `tasks.md` I proposed deleting `TEMPLATE-ERRORS.md`
  (the sketch this feature grew out of) on the strength of `research.md` Finding 1 calling it
  superseded. I had not opened the file. It turned out to hold a whole section — "Why
  `max_delta` doesn't solve this", covering `count_objects()` / `too_much_delta()` mechanics
  and three reasons a disk-delta signal cannot serve as a render-error signal — with no
  counterpart in any spec artifact, plus the float64 precision argument behind the
  never-round-before-comparing rule. Deleting it would have destroyed the record of why the
  feature needed a new mechanism instead of tuning an existing one.
- **Detection signal**: the user pushed back with "it might be moved into specs/ as the
  document with which everything started". Reading the file then took one tool call and
  immediately contradicted my recommendation. The general tell: I am about to recommend a
  **destructive, irreversible** action against a file whose contents I know only through
  another document's summary of it.
- **Prevention rule**: never propose deleting or overwriting a file without reading it in
  full first, however confident a secondary source sounds. Note also what Finding 1 actually
  said — its *design* is superseded and its *description of current behaviour was reused* —
  which is narrower than "its content lives elsewhere now". Read the claim precisely rather
  than rounding it up to the convenient conclusion. Default to moving/archiving over deleting
  when a document has historical value as the origin of a feature.

### `git stash -u` is a destructive move against a working tree full of untracked work
- **Failure mode**: to check whether a failing test (`test_logging.LoggingTest::test_write`)
  predated my changes, I ran `git stash -u` on a tree holding an entire unfinished feature —
  six modified source files plus a dozen brand-new untracked ones. The `stash pop` then failed
  partway with "could not restore untracked files from stash" because `.pytest_cache` entries
  collided. Everything happened to survive, but only because the collision was in a cache
  directory; a collision in a real file would have left the feature half-restored with no
  obvious signal about which half.
- **Detection signal**: `error: could not restore untracked files from stash. The stash entry
  is kept in case you need it again.` The general tell: I am reaching for a whole-tree VCS
  operation to answer a question about **one** file.
- **Prevention rule**: to test whether a behaviour predates a change, revert the narrowest
  thing that could possibly answer it — copy the single file aside and restore it (as I did
  later, correctly, when checking the `last_success` guard was load-bearing), or read the
  original with `git show HEAD:path`. Never stash a working tree carrying unfinished,
  uncommitted, untracked work to satisfy curiosity.

### A test that reads back accumulated log state passes only by luck
- **Failure mode**: `test_logging.LoggingTest::test_write` asserts a hostname appears in
  `tests/var/log/coshsh.log`, but nothing in the test writes that file at that path —
  `read_cookbook` reconfigures logging to the cookbook's `log_dir`, which for `etc/coshsh.cfg`
  falls back to the system temp dir. The assertion was passing on leftover content in an
  untracked artifact from earlier runs. My new logging tests wiped `tests/var/log` and the
  test started failing, which looked exactly like a regression I had caused.
- **Detection signal**: a test fails in isolation but passes in a full-suite run, or vice
  versa. Verified pre-existing by deleting `tests/var/log` on a pristine tree and watching it
  fail there too.
- **Prevention rule**: when a neighbouring test breaks after a change that "shouldn't touch
  it", first establish whether it was ever independently green — cheapest check is to run it
  alone on an untouched checkout with the shared state removed. And when adding tests that
  need a scratch directory, give them their own (here: `log_dir = ./var/log_renderr` in the
  new cookbook) rather than reusing and wiping one a neighbour depends on.

### WHY comments must justify the code's present shape, not narrate the diff that produced it
- **Failure mode**: nearly every WHY comment I added for spec 007 was written from the
  perspective of the change rather than the file. `# WHY this moved inside "recipe_completed":
  it used to advance on every run...`, `# WHY run() now returns a count where it used to
  return None`, `# previously this branch was the one failure kind that logged nothing`,
  `Kept as a property so that ... keep reading the same attribute they always did`. Each one
  is only decodable by someone who knows the *prior* state of the code, so a reader opening
  the file cold has to go digging through `git log` to understand a comment whose entire
  purpose was to save them that trip. The comment silently assumed the diff as context.
- **Detection signal**: the user asked whether comments could say "why the following lines are
  here" instead of "this code was moved from the previous position". The mechanical tell is
  any comment containing *previously, used to, now, no longer, moved, kept, still, unchanged,
  this feature, before this change* in reference to the code itself. Note the false positives
  to leave alone: "the **previous run's** output is unchanged" is about a prior *execution* at
  runtime, which is a legitimate domain concept, not code history.
- **Prevention rule**: write the comment as if the code had always looked this way. State the
  invariant, the constraint, or the failure the current structure prevents — "this sits under
  `recipe_completed` because the liveness alarm can only fire if the timestamp is refreshed by
  published output and nothing else" — and add a directive where position matters ("do not
  hoist this out of the branch"). Historical framing belongs in the places built to carry it:
  `Changelog`, the migration/compat notes in `docs/`, and the commit message. A useful check
  before committing: reread each new comment pretending the file is brand new. If it only
  makes sense next to the diff, rewrite it.

### A comment explaining how not to misuse an API is usually a sign the API is wrong
- **Failure mode**: my first cut of the render-error counters gave `RenderTally` three
  methods — `record_attempt()`, `record_missing()`, `record_error()`. Most call sites needed
  one of them; the rule-match failure path needed two, because it never reaches the place
  where the attempt is counted. I documented that asymmetry with an eight-line WHY comment
  and moved on. The comment was the tell: it existed purely to stop a future reader making a
  mistake the API permitted, and the mistake would have been **silent** — a missed attempt
  never raises, it just shrinks the denominator of the abort percentage, so a recipe that
  should have refused to publish publishes instead.
- **Detection signal**: any comment whose job is "when you touch this, remember to also...".
  Also: one call site using an API differently from all the others and needing prose to
  justify it. Both mean the shape of the API, not the caller, is the problem.
- **Prevention rule**: when about to write a comment warning against a misuse, first try to
  make the misuse unrepresentable. Here, collapsing the three methods into a single
  `record(outcome)` — where the attempt and its outcome are counted in one indivisible call —
  deleted the asymmetry, the eight-line comment, and three of the four `if tally is not None`
  guards at once. Prefer an API where the wrong thing cannot be expressed over an API plus a
  note asking people not to express it.

### Review your own diff as a stranger before declaring done
- **Failure mode**: I reported the feature complete with 253 tests passing. It was correct,
  but re-reading the diff on request found: a ~240-character call duplicated three times that
  I had made *worse* by appending an argument to each copy rather than noticing the
  duplication; `Generator.run()` grown to 193 lines and 8 levels of nesting, 118 of those
  lines mine; and two parallel counters in one function. Passing tests confirmed I had not
  broken anything — they said nothing about whether the code was any good.
- **Detection signal**: none of this showed up while writing, because each edit was locally
  reasonable. It only became visible reading the finished diff top to bottom with no memory
  of writing it. Cheap mechanical proxies exist: length and max nesting of any function I
  touched, before vs after; and any line I edited in more than two places at once.
- **Prevention rule**: before reporting a non-trivial change complete, read the whole diff
  once as if reviewing someone else's PR, and measure the functions touched. "Tests pass" is
  the floor, not the bar. Ask specifically: did I add to a duplication instead of removing
  it, and is any function meaningfully longer or deeper than I found it?
