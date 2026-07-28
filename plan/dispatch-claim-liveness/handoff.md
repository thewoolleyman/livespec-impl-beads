# Handoff — dispatch-claim-liveness

> # ✅ THE LAST OBLIGATION IS DISCHARGED — ZERO LIVE ITEMS (2026-07-28)
>
> **The thread now has NOTHING live at all.** The previous revision of this box carried one
> obligation — a WAIT on `bd-ib-91wj` — and it is closed out. Both of that box's tasks are
> done and verified:
>
> | what it asked | outcome |
> |---|---|
> | Verify PR **#1095** merged | ✅ **MERGED** `3de49c1`, 2026-07-28T15:55:18Z |
> | Finalize `bd-ib-91wj` when factory-hardening's result arrives | ✅ **DONE** — result arrived, framing CORRECTED, row rewritten in place |
>
> ## `bd-ib-91wj` IS NO LONGER ON HOLD — and the answer CHANGED the framing
>
> `plan/factory-hardening/`'s result landed in **`cae25b0`**
> (`plan/factory-hardening/handoff.md` §"Which plugin build a dispatch actually runs"). It
> did **not** confirm the session-pinning framing — it corrected it:
>
> **Which plugin build a dispatch runs is ENTRY-POINT-resolved.** `plugin_root()` returns
> `CLAUDE_PLUGIN_ROOT` when the harness set it, else resolves relative to the executing
> `.py`. **Session pinning is what that means for the plugin-invoked entry point ONLY, and
> it is harness behaviour, not ours.** A file-path invocation — repo checkout or cache dir —
> involves no session at all. That is why a live `dispatcher.py` can run CURRENT code
> against another repo, which a pure-pinning model cannot explain.
>
> All three instructed steps were performed: description finalized **in place** (never
> closed-and-refiled — it remains the ONE record by cross-track agreement), the
> `PROVISIONAL / ON HOLD` title prefix dropped, and the three-sessions sampling lesson
> folded into the **description** where a tierer will actually see it.
> **⚠ SUPERSEDED IN PART — the `factory-hardening` session rewrote the same row three
> minutes later and THEIRS is the live description. That is correct and should stay; see
> the two-causes correction below.** The steps above were performed; the text they produced
> is no longer what the row carries.
>
> **The row is still `backlog` P2 and still UNTIERED — no autonomy label was self-issued**,
> and it is still **not tierable as written** (its original acceptance is already satisfied
> on `master` by `14c3cae`). The mechanical fix for its class is **`bd-ib-3j4u`**.
>
> **⚠ A TIMING FACT WORTH KEEPING, because it is this file's own lesson turned on itself.**
> `cae25b0` committed at **08:51:16-07:00**; this thread's wrap-up commit `d4da1dd`, which
> recorded the hold as still pending, committed at **09:00:49-07:00** — **nine minutes
> later**. The answer was already on `master` while the handoff was being written to say it
> was awaited. Careful is not current, in the act of warning that careful is not current.
>
> **Every claim was re-verified at source before adoption, not taken on report** — the
> resolver body, the gate's single call site, both `prepare()` callers, `reconcile-merged`'s
> bypass, and the gate's absence from the peer's cached build. Two apparent contradictions
> were reconciled rather than papered over (a "one call site" vs "two call sites" reading,
> and an author-date vs commit-date discrepancy). The evidence table is on the row's notes.
>
> **⛔ THINGS THAT ARE SETTLED — do not re-derive or re-litigate them:**
> - **There is NO release gap.** `git tag --contains 14c3cae` → v0.46.23 … v0.47.1.
>   Commit 23:19:21Z, tag commit 23:23:06Z, release published 23:23:18Z (≈3m45s).
> - **Do NOT file a release/propagation gap**, and do NOT re-author the pack fix — it is
>   `14c3cae`.
> - ~~The consumer's stale-base refusal and its `worktree_pack_absent` have **ONE**
>   cause.~~ **⛔ REFUTED — SEE THE TWO-CAUSES BOX DIRECTLY BELOW. There are TWO, and a
>   plugin refresh fixes only one of them.**
> - The **"fourth strand flavor / refused-at-publish"** taxonomy entry is struck; it never
>   appeared anywhere under `plan/` here, so there is nothing of ours to remove.
> - **We are NOT carrying the consumer track's release request or dispatch hold.**
> - **The console track's preserved checkout was NOT touched**, and must not be.
>
> ---
>
> ## ⛔ CORRECTION, 2026-07-28 — "ONE CAUSE" IS REFUTED. THERE ARE **TWO**.
>
> **This correction lands minutes after the commit above asserted the opposite, and the
> refuting evidence predates that commit.** Stated plainly rather than quietly amended,
> because a wrong entry in a *"do not re-derive"* list is the most expensive kind: it is the
> list a successor trusts instead of checking.
>
> **Owning session: `factory-hardening`** (project `livespec-orchestrator-beads-fabro`,
> session `69b00837-bb8f-41e9-884e-d670ca1382da`). They discharged the same hold
> concurrently, wrote `bd-ib-91wj` at **16:11:24Z** — three minutes after this thread's
> write at 16:08:28Z, and five minutes *before* PR #1098 merged at 16:16:41Z carrying the
> refuted claim.
>
> | symptom | cause | does a plugin refresh fix it? |
> |---|---|---|
> | janitor `worktree_pack_absent` | stale plugin cache — the janitor argv comes from the plugin's `_DEFAULT_JANITOR`, and a revision predating `14c3cae` lacks `install-worktree-pack` | **YES** |
> | stale-base publish refusal | **a REPO-LOCAL WORKFLOW OVERRIDE** — `livespec-console-beads-fabro` commits its own `.fabro/workflows/implement-work-item/` tree *including its own five prompts*, and that override wins over the plugin's bundled workflow. Their `prompts/pr.md` never received `231e9a4`. | **NO — and this is the half that matters** |
>
> **Verified here at source before adopting it, not taken on report:**
> `_WORKFLOW_SUBPATH` (`_dispatcher_paths.py:37`) is `.fabro/workflows/implement-work-item/
> workflow.toml` — a **repo-local** path, not `.claude-plugin/.fabro/…`;
> `git -C /data/projects/livespec-console-beads-fabro ls-files` confirms that repo commits
> all seven files including `prompts/pr.md`; `231e9a4` is a `prompts/pr.md` change; and our
> bundled copy carries **6** `rebase` references against the console copy's **2**.
>
> **Why this matters operationally, and it is the whole point of the correction:** telling
> the console track "refresh your plugin" as *the* remedy would leave their publish refusal
> in place and send them chasing a fix that structurally cannot reach their repo-local
> prompts. **Route the second cause to the console repo, not to a plugin refresh.**
>
> ## 📌 `bd-ib-91wj`'s LIVE DESCRIPTION IS `factory-hardening`'s, and that is CORRECT
>
> Two sessions rewrote the same row within three minutes. **Theirs is the live description
> (later write wins), and it should stay** — their two-causes framing is the better record,
> and it is the ONE record by cross-track agreement. **Do not restore the earlier text and
> do not file a second row.**
>
> **Nothing was lost, because beads notes are append-only.** Both discharge notes coexist on
> the row — this thread's *"THE HOLD IS LIFTED"* note with its source-verification table,
> and theirs. The row's title now leads with *"Consumer dispatch skew has TWO causes"*.
>
> **The near-miss worth keeping:** two sessions independently doing the same in-place rewrite
> of one row is exactly what the one-record agreement exists to prevent, and the agreement
> held only because the second writer improved on the first rather than duplicating it. Had
> either session used close-and-refile instead of rewrite-in-place, there would now be two
> rows asserting different causes. **Before rewriting a cross-track row, re-read it first —
> a peer may have just answered the same question better.**
>
> ## 📌 The `auto-backup failed` warning on every `bd` write is ALREADY FILED — do not chase it
>
> Every ledger write prints `auto-backup failed: … command denied to user
> 'livespec-orch-beads-fabro'`. That is **`bd-ib-rxf`** (P2, `backlog`, filed
> **2026-07-11**): *"beads auto-backup fails: tenant SQL user lacks DOLT_BACKUP grant."*
> The tenant SQL user lacks `DOLT_BACKUP` on the shared family dolt-server, so remote
> registration is denied and **no backups run for this tenant**; writes otherwise succeed
> normally, and the item records two fix options.
>
> **Both readings of that warning are correct and both are already on the record: the write
> DID persist, and there IS a real backup gap.** Verify persistence by re-reading the row —
> do not treat the warning as a failed write, and do not re-file it. It has printed on every
> write for seventeen days unowned, which is the same "visible but unowned" shape this
> thread keeps meeting.
>
> **⛔ A SESSION-PINNING SECTION WAS DELIBERATELY NOT LANDED IN THIS FILE.** It was written,
> committed to a branch, and that branch was deleted unmerged once the hold arrived. **Do
> not resurrect it from git history** — and note it is now doubly obsolete, since the
> framing it argued has since been superseded. If you find
> `docs/dispatch-claim-liveness-archivable` in a reflog, that is why it is gone.
>
> ---
>
> # 📌 THE THREE STANDING RULES — the durable yield of the 2026-07-28 cross-track exchange
>
> These are what survived a day in which **three sessions independently reached confident
> wrong answers on the same question.** They are stated as rules because each was paid for.
>
> ## RULE 1 — ASSERTING AN ABSENCE REQUIRES STATING THE SCOPE SEARCHED
>
> **"No call site", "no release", "no occurrence" are the claims that went wrong all day.**
> Every instance was a confident generalisation from too narrow a search, and every one
> produced a **CONFIDENT WRONG ANSWER rather than an obviously empty one** — which is
> exactly why none of them self-announced.
>
> **When you assert an absence, STATE THE SCOPE YOU SEARCHED, and make it the WHOLE
> WORKSPACE unless there is a reason it cannot be.**
>
> The tally, recorded honestly because the count is the argument:
>
> | who | the absence claimed | why the search could not have found it |
> |---|---|---|
> | console supervisor | host-wide scope | searched narrower than the claim |
> | console supervisor | "one dead assertion" | there were **four** |
> | console supervisor | "merged upstream but unreleased" | sampled builds that predated the commit |
> | console supervisor | "no production call site" | grepped **one crate** |
> | this thread's supervisor | "verified" (2 cached builds) | both predated the fix commit |
> | `factory-hardening` | zero of 110 caches | grepped the REPO-shaped path against CACHE-shaped dirs |
>
> **The last one is the only one that was caught in the act, and it was caught by a smell,
> not a method:** zero-out-of-110 was *"too clean to be true."* Keep that heuristic — on the
> day's evidence it is the single thing that worked.
>
> ## RULE 2 — VERIFY THE ABSENCE OF THE *RIGHT* TOKEN. A COUNT IS NOT A BEHAVIOR TEST.
>
> > **⚠ READ THIS AS A METHOD CORRECTION, NOT A FACT CORRECTION. THE CONCLUSION NEVER
> > MOVED.** `livespec-console-beads-fabro`'s repo-local `prompts/pr.md` genuinely lacks the
> > `231e9a4` rebase-before-push fix — that was true when first written and is true now, and
> > **it is settled: do not re-litigate it.** What changed is the *evidence* behind it,
> > upgraded from a token count that **could have returned the wrong answer** to a token that
> > **could not**. The lesson is "our test was weaker than our confidence", not "we were
> > wrong about the console fork".
>
> **Worked example, recorded because it is more instructive than the abstract rule — and
> because it is this thread's own error, offered as settled evidence when it was not.**
>
> This file's PR #1101 argued the point above while citing:
>
>     "our bundled copy carries 6 `rebase` references against the console copy's 2"
>
> **That count is NOT probative.** Both of their two hits are innocent:
>
>     line  1   "# PR stage — publish the work and arm rebase auto-merge"     <- a title
>     line 44   "gh pr merge --rebase --auto --delete-branch"                 <- arming auto-merge
>
> Neither is rebase-before-push. **Had their file happened to say "rebase" six times in
> auto-merge context, the test would have reported the fix PRESENT.** A count that can be
> satisfied by unrelated text is not a test of behavior.
>
> **The absence that actually discriminates is `fetch` — ours 2, theirs 0** (re-verified
> here: both of ours are `mise exec -- git fetch origin master --quiet`, at `pr.md:30` and
> `:49`, which IS the refresh-before-push). `fetch` is the right token precisely because it
> **cannot appear unless the behavior is there**.
>
> **So: pick the token that can only appear if the behavior is present, and SAY WHICH TOKEN
> YOU CHOSE AND WHY.** The original count was directionally right and still not evidence —
> which is the whole point, and why a directionally-right check is the most dangerous kind.
>
> ### ⭐ REFINEMENT — PREFER A PROVENANCE QUESTION TO ANY CONTENT PROBE
>
> **Found 2026-07-28 while auditing this same question, and it beats both token tests.**
> Before grepping a file's *contents* for a fix, ask whether it **could possibly contain**
> the fix. The console fork's `prompts/pr.md` has **exactly ONE commit in its entire
> history** — `3fa2d5c`, 2026-07-06 — and `231e9a4` is dated **2026-07-24**. **A file whose
> only commit predates a fix by eighteen days cannot contain it.**
>
> | probe | verdict |
> |---|---|
> | `rebase` count — ours 6, theirs 2 | **NOT probative** — both their hits are innocent; six mentions in auto-merge context would have reported the fix PRESENT |
> | `fetch` count — ours 2, theirs 0 | **probative** — the token cannot appear unless the behavior is there |
> | `git log -- <file>` — one commit, 2026-07-06 | **decisive** — provenance, not content |
>
> **All three returned the right answer. Only the last two could not have returned the
> wrong one, and only the third has no wrong-answer failure mode at all** — it cannot be
> satisfied by unrelated text, needs no judgement about which token is discriminating, and
> is cheaper than reading the file. **When the question is "does this artifact carry a known
> commit?", ask git about the artifact's history, not the artifact about its contents.**
>
> **Why the weaker version was left standing in #1101 rather than force-pushed away.** A
> deliberate call, and it is the house style: this file marks superseded wording rather than
> deleting it, keeps its `⛔ CORRECTED` blocks, and leaves retracted recommendations visible
> with their reasons. Erasing a weak claim would teach *"hide your mistakes"* in the same
> document that teaches *"a handoff is a claim with a timestamp"* — those cannot both be the
> rule. The error is the teaching artifact; without it Rule 2 is an abstraction a successor
> nods at and then repeats.
>
> ## RULE 3 — AN INSTRUCTION CAN OUTLIVE THE CONDITION THAT MADE IT CORRECT
>
> **The danger is not writing something false. It is writing something TRUE that stops being
> true while still reading as authoritative** — and sitting in the section a successor trusts
> *instead of* checking.
>
> Two instances from one day, deliberately paired because the shape only becomes obvious
> when you see it twice:
>
> | instance | true when written | falsified by | where it landed |
> |---|---|---|---|
> | console's *"expect the stale-base refusal, apply the known recovery"* | while their worker ran a July-22 plugin | their worker restarting | a **merged handoff** |
> | our *"the refusal and `worktree_pack_absent` have ONE cause"* | on the evidence then available | `factory-hardening`'s repo-local-override finding, 5 min before the merge | this file's **do-not-re-derive list** |
>
> Both were written carefully. Both reached a merged document. Neither announced itself.
> **A do-not-re-derive list is the highest-risk place in any handoff for exactly this
> reason** — it is written to be trusted without checking, so a stale entry there is
> maximally load-bearing. Date every such entry, and re-verify before quoting one.
>
> ## 📎 A FACT TO CARRY — the console track's state, NOT ours, and NOT to act on
>
> **There were THREE blockers on the console side, not two.** The third was a missing
> `check-no-workflow-edits` recipe, since adopted in **their PR #474** and merged.
>
> **Their current position: the janitor half is addressed; the stale-base half is explicitly
> NOT addressed and is blocking all their dispatch** until their committed `pr.md` is fixed.
> Recorded so nobody re-derives it or offers them a plugin refresh as the remedy — **it
> structurally cannot reach their repo-local prompts.** Do not act on this; it is theirs.
>
> **One more staleness for the tally, and it is ours about a peer.** This thread's note to
> the console track was **~90 minutes stale on their state**: they had already acted on
> `factory-hardening`'s finding and stopped the dispatch before any resume, so it warned
> them about a condition they had already left. It was still net-positive — one datum was
> new to them, that `231e9a4` also shipped `test_pr_stage_prompt_publish_freshness.py`,
> which guards OUR prompt and has **no equivalent in their fork**, reframing their
> keep-vs-delete-the-fork call materially toward deletion. **But the staleness was ours, and
> it belongs in the tally honestly:** the re-query rule applies to a peer's state too, not
> only to ledger rows.
>
> ---
>
> # ✅ COMPLETE AND ARCHIVABLE — 2026-07-28
>
> **This thread is finished and this file is ready to be archived.** Archival itself is
> the maintainer's call and was NOT performed by an agent; this section exists so the
> decision can be made from a file that is honest about its own state.
>
> **Nothing is lost by archiving, because every surviving obligation now lives on a LEDGER
> ROW rather than in this document.** That was the last piece of work: an archived handoff
> is where obligations go to die, and losing one would have been this thread's own
> signature failure committed as its final act.
>
> **What survives, and where — re-queried against the ledger 2026-07-28, not copied from
> any summary:**
>
> | what | id | state | owner / note |
> |---|---|---|---|
> | journal-path has two conventions | `bd-ib-xw2k` | `backlog` P3 | **UNTIERED** |
> | plugin build is entry-point-resolved (**framing FINALIZED 2026-07-28**) | `bd-ib-91wj` | `backlog` P2 | **UNTIERED**; not tierable as written — fixed on master by `14c3cae` |
> | already-fixed items accumulate | `bd-ib-js1f` | `backlog` P2 | **UNTIERED** |
> | `reconcile-merged` bypasses the currency gate | `bd-ib-3j4u` | `backlog` **P1** | **UNTIERED** |
> | sandbox setup needs a live api.github.com fetch | `bd-ib-bic7hb` | `ready` P2 | host-only; BORROWED from `plan/factory-hardening/` and recorded there |
> | the deliberate S3 fixture | `bd-ib-w4h4` | `active` P1 | held ON PURPOSE; now cross-linked to `bd-ib-rxxx` on BOTH rows |
> | red master CI hard-gates dispatch | `bd-ib-wmqsn7` | `backlog` P2 | **`plan/factory-hardening/`'s — NOT ours** |
>
> **All four in-tenant items carry NO autonomy-tier label** (verified: no
> `factory-safety:` / `autonomy` label on any of them). None is dispatchable until a
> **human** signs the `autonomy_tiered` gate. **An agent must not self-issue it** — and
> `bd-ib-js1f`, which is about items that describe already-fixed behavior, is the last one
> anybody should self-sign.
>
> Two more untiered items sit in OTHER tenants, prose-linked because beads has no
> cross-tenant edge: **`bd-gj-pch`** (`livespec-orchestrator-git-jsonl`) and
> **`livespec-r5df`** (core `livespec`).
>
> **⛔ ONE CORRECTION TO THE HAND-OFF LIST I WAS GIVEN: `bd-ib-bwgko4` is CLOSED.** It was
> named as a surviving `plan/factory-hardening/` item; the ledger says otherwise, and the
> ledger wins. It is not a survivor and nobody should go looking for it.
>
> **The `bd-ib-w4h4` obligation is now discharged into the ledger, in both directions.**
> `bd-ib-rxxx`'s description carries a closing instruction — when it lands, un-strand
> `bd-ib-w4h4` — and `bd-ib-w4h4`'s description carries the reciprocal, so a reader
> arriving from either side finds the other. Both state the fact that makes the delay safe:
> **`bd-ib-w4h4` costs NOTHING where it sits.** S3 shipped, so `claimed_active_count()`
> excludes a row holding no live dispatch lock — verified under real concurrent load at raw
> `active` 3 / claimed 2. It is a stranded row consuming no WIP slot, which is the epic's
> fix demonstrating itself. **Do not un-strand it early, and do not read it as a live
> leak.**
>
> ---
>
> # ⛔ STOP — READ THIS BOX BEFORE ANYTHING ELSE (last written 2026-07-28)
>
> **THIS THREAD IS FINISHED. THERE IS NO IN-FLIGHT WORK AND NOTHING TO PICK UP.**
>
> You were handed this file with "read it and follow it". **Following it correctly
> means NOT restarting the work below.** Every assignment this thread carried is
> COMPLETE and MERGED:
>
> - **Epic `bd-ib-waov` — DONE**, all three slices. S1 `bd-ib-ohdu5a` (PR #978), S2
>   `bd-ib-cfgkkk` (PR #1006), S3 `bd-ib-pme57n` (PR #1014 / `5b32017`). The core
>   defect — a dead claim permanently eating a WIP slot — is FIXED and was verified
>   end-to-end on the live tenant.
> - **The `/livespec:revise` pass — DONE.** Both pending proposals processed and
>   ratified as **v051** (PR #1036 / `715d81a`). `SPECIFICATION/proposed_changes/` is
>   empty.
> - **2026-07-28 — the two factory-safe follow-ups this thread filed are also DONE**,
>   dispatched SERIALLY on maintainer autonomy-tier sign-off and each verified by
>   re-executing its red against the merged tree: `bd-ib-ktxb` (PR #1048 / `521d7f71`,
>   the `reject:rework` durable journal record) and `bd-ib-3lmt` (PR #1050 / `599e3df`,
>   the doc-only pre-commit fast path). See §"Session close-out addendum".
> - **2026-07-28 — `bd-ib-ri1x` was ROUTED OUT of this tenant**, not left filed. It is
>   now `livespec-j49m` in the core `livespec` tenant, with a ratifying spec amendment
>   merged as core PR #1811 (`45ab15e5`). Do not go looking for it in this ledger.
> - **2026-07-28 — `bd-ib-d6op2n` was CLOSED as a DUPLICATE**, discharging the last of
>   this thread's hand-routing obligations. The owning tenant had already filed the same
>   defect as `livespec-driver-claude-tun` six days earlier, and theirs is the better
>   record. Do not re-file it here. Evidence was contributed to their item first; the
>   filed-items entry below explains what, and why the previous wording of that entry was
>   the thing that hid the duplicate for two days.
> - **2026-07-28 — SIX items were filed and left UNTIERED ON PURPOSE.** None is
>   dispatchable until a maintainer signs the `autonomy_tiered` gate; an agent must not
>   self-sign it. **In this tenant, FOUR:** **`bd-ib-xw2k`** (P3, journal-path has two
>   conventions), **`bd-ib-91wj`** (P2, janitor checkout lacks the worktree pack),
>   **`bd-ib-js1f`** (P2, items describing already-fixed behavior accumulate in
>   recently-worked areas) and **`bd-ib-3j4u`** (**P1**, `reconcile-merged` bypasses the
>   plugin-currency staleness gate). Elsewhere, prose-linked because beads has no
>   cross-tenant edge: **`bd-gj-pch`** (`livespec-orchestrator-git-jsonl`) and
>   **`livespec-r5df`** (core `livespec`), the per-repo and fleet-level halves of the
>   doc-only pre-commit gap.
>   **⚠ THIS BULLET SAID "FOUR" AND "BOTH IN-TENANT" UNTIL 2026-07-28, WHILE TWO MORE HAD
>   ALREADY BEEN FILED.** Corrected here. It is a small thing and it is precisely the
>   defect `bd-ib-js1f` describes, occurring in the most-read paragraph of this file: a
>   count written once, still reading as current, quietly wrong. **If you add a filed item
>   anywhere below, fix this count in the same change.**
> - **⚠ THE TWO ORIGINAL IN-TENANT UNTIERED ITEMS WERE MEASURED LATER ON 2026-07-28, AND
>   BOTH PREMISES MOVED. READ THEIR NOTES BEFORE TIERING EITHER.** `bd-ib-91wj`'s reported
>   defect is **ALREADY FIXED on master** by `14c3cae` — it is a re-report from a session
>   running a week-old cached plugin, so **do not tier it for dispatch**; the remedy for
>   the reporting side is a plugin refresh **for the `worktree_pack_absent` half ONLY —
>   their publish refusal has a second cause a refresh cannot reach, see the two-causes
>   correction above**. `bd-ib-xw2k`'s "nothing passes `--journal`
>   today" premise is **FALSE** — three committed scripts pass one — though the
>   divergence still never bites in a single run. Both findings are proven by execution
>   and recorded on the items; see §"2026-07-28 addendum — the two untiered items were
>   MEASURED".
> - **⛔ 2026-07-28 — STAND DOWN on `bd-ib-wmqsn7`.** It belongs to
>   `plan/factory-hardening/`, which is ACTIVELY RUNNING in its own session (it holds a
>   live dispatch in THIS tenant). Do not tier, dispatch, adopt or re-describe it. Our
>   field evidence on `bd-ib-wmqsn7` STAYS — it was a contribution, not an adoption. Full
>   terms in the stand-down box further down.
> - **✅ CORRECTION — `bd-ib-bwgko4` was named in that stand-down and is CLOSED.** It was
>   never live work to stand down FROM. It closed 2026-07-28 as SUPERSEDED: the same defect
>   was independently re-filed as **`bd-ib-qq7f`** on 2026-07-23, dispatched, and merged
>   2026-07-24 as **PR #905 / `231e9a48` "fix: refresh PR publish base before push"** —
>   and `plan/factory-hardening/` confirmed the fix is live in the RUNNING factory, not
>   merely on `master`. **No tiering decision is pending on it and there is nothing to
>   stand down from.** (Verified here independently: `231e9a4` is dated 2026-07-24
>   02:05:42Z and carries tags v0.46.4 onward.)
>
> **Everything below this box is the RECORD of how that was done, plus filed items
> this thread does NOT own.** It is reference material, not a task list. The slice
> tables, requirement lists and design sections describe SHIPPED work — do not read
> them as pending.
>
> **If you are looking for something to do, the honest answer is: this thread has
> nothing for you.** Go to §"CLOSE-OUT 2026-07-27" for the verified end state and the
> short list of filed-but-unowned items, and check with the maintainer before adopting
> any of them — several are explicitly other threads' or fleet-level.
>
> **THE PIN ASSUMPTION IS NOW DISCHARGED — it is no longer inherited.** Earlier
> revisions of this box said the dispatch path PAST setup was untested on
> `livespec-dev-tooling` v0.56.3 and told you to suspect the janitor and pr stages
> first. That is SUPERSEDED: on 2026-07-28 two full dispatches ran end-to-end on
> sandbox image **v0.56.6** — through setup, agent work, janitor `just check`, the pr
> node, auto-merge and the post-merge janitor — and BOTH merged green. The whole path
> is now proven by execution, not presumed. See §"The v0.54.19 pin hold".
>
> **`bd-ib-w4h4` must stay `active`.** It is the deliberate live fixture and it costs
> no WIP slot — which IS the fixed behavior. Do not un-strand or close it until
> `bd-ib-rxxx` lands (still `backlog`, re-checked 2026-07-28).
> - **2026-07-28 — `bd-ib-rxxx` IS NOW ROOT-CAUSED, and it names the WRONG CHECK.** The
>   janitor red that stranded `bd-ib-w4h4` was **`check-coverage`**, not
>   `supervisor_discipline` — proven from the journal's own tail and by re-running the
>   real check at the exact commit and dev-tooling version with the interpreter pinned,
>   where BOTH of the item's competing theories are refuted. The true mechanism is a
>   `check-coverage` recipe that branches on a gitignored `.coverage` file to decide
>   which command to run. **The item needs retitling by its owner before anyone
>   implements against it.** Full evidence is on its notes and in §"`bd-ib-rxxx`
>   ROOT-CAUSED". This does NOT license un-stranding `bd-ib-w4h4` — that is still a
>   maintainer call.
> - **⛔ 2026-07-28 — ITEMS DESCRIBING ALREADY-FIXED BEHAVIOR ACCUMULATE IN RECENTLY-WORKED
>   AREAS, AND A STALE ITEM IS DISPATCHABLE.** In the janitor/dispatch area this session
>   worked, **four of eight items were fully stale — three of them P1**; this very file
>   asked the maintainer to tier `bd-ib-91wj` for dispatch when its defect had been fixed
>   two days earlier. **But a seeded RANDOM sample of ten other items found ZERO stale**,
>   so the effect is concentrated where fixes have recently landed, NOT diffuse across the
>   backlog. Filed as **`bd-ib-js1f`** (P2, untiered), retitled to match the corrected
>   claim. **Before acting on ANY item named in this file, verify the defect still exists
>   in the merged tree** — the standing re-query rule above is necessary but not
>   sufficient, because the ledger can be current and the ITEM still stale.
> - **⛔ 2026-07-28, COMPLETED — `bd-ib-rxxx`'s DEFECT WAS FIXED ON 2026-07-20, the day it
>   was filed. RECOMMEND CLOSING IT.** The mechanism is the runner's effective **UID**, not
>   the `.coverage` arm and not checkout provenance: the only live-pid test probes pid 1,
>   which root can signal and an unprivileged uid cannot, so CI's root container covered a
>   line the host janitor at uid 1000 did not. `ff97ad8` fixed exactly that the same
>   evening, and the `check-python` matrix's new `uid: root`/`uid: nonroot` dimension now
>   guards it. **So `bd-ib-w4h4`'s stated precondition is MET IN SUBSTANCE** — which still
>   does NOT license un-stranding it; that is the maintainer's call.
>
> **⚠ It is NOT "the only `active` row" — earlier revisions said so and that is now
> false.** Other sessions dispatch into this shared tenant, so the `active` set moves
> under you. Verified 2026-07-28 with a peer dispatch in flight: **3 raw `active` rows,
> `claimed_active_count()` = 2.** `bd-ib-eha3wh` and `bd-ib-wefw` each held a LIVE
> dispatch lock and counted; `bd-ib-w4h4` held no lock and was correctly excluded. That
> is the S3 fix discriminating live claims from a dead one under real concurrent load —
> the strongest field evidence for it so far, and a reminder that any statement here
> about *how many* rows are in a state is a snapshot, per the standing rule above.
>
> ---
>
> ## 📌 STANDING RULE — A CONFIDENT VERIFICATION IS STILL A SAMPLE
>
> **State what population your check covers, and whether it COULD have returned the other
> answer.** If it could not, it is not evidence — it is a confident wrong answer waiting to
> be quoted.
>
> **THREE sessions made the same sampling error on the SAME question in one day,
> independently**, each while believing it was verifying:
>
> | who | sample | why it could not have worked |
> |---|---|---|
> | the console track | 3 cached plugin builds | all predated the fix commit |
> | this thread's supervisor | 2 cached builds, reported as "verified" | both predated the fix commit |
> | `plan/factory-hardening/` | (nearly) all 110 caches | grepped the REPO-shaped path `.claude-plugin/scripts/…` instead of the CACHE-shaped `scripts/…`, returning zero |
>
> **The sampling error is what cost the time — not the underlying fact it was chasing.**
> And note the shape, which is why none of the three self-announced: **each bad method
> produced a CONFIDENT WRONG ANSWER rather than an obviously empty one.** The third was
> caught only because zero-out-of-110 was *"too clean to be true"* — keep that heuristic;
> it was the only thing that worked.
>
> **On the specific question they all got wrong — "was this released?" — the one-command
> answer is `git tag --contains <sha>`.** An artifact created BEFORE the commit cannot
> answer it. Measured here:
>
> ```
> 14c3cae committed          2026-07-26T23:19:21Z
> v0.46.23 tag commit        2026-07-26T23:23:06Z
> v0.46.23 release published 2026-07-26T23:23:18Z
> ```
>
> ≈**3m45s** from commit to tag. **Cite the three timestamps, never a delta** — an earlier
> revision of this material said "24 seconds", derived by comparing the fix commit against
> the RELEASE-BRANCH commit `e470f4d` (23:19:45Z), which is a *different git object* from
> the commit the tag points at. Two clocks, silently combined, presented as a measurement.
> Immaterial to the conclusion; fatal to the method.
>
> ## 📌 STANDING RULE — RE-QUERY THE LEDGER BEFORE ACTING ON ANY ID IN THIS FILE
>
> **Every work-item status, table row and ownership claim below is a SNAPSHOT with a
> timestamp. The ledger is the authority; this file is not.** Before you act on any id
> here — dispatch it, tier it, adopt it, cite it, or tell someone it is open — read it
> from the ledger first:
>
> ```bash
> /usr/local/bin/with-livespec-env.sh -- bd show <id>
> ```
>
> **This is not defensive boilerplate. It is the single most expensive recurring mistake
> this thread made**, and it went wrong FOUR separate times in one session on
> 2026-07-28 alone:
>
> 1. Two of the four items this file listed as "pre-existing unowned" work
>    (`bd-ib-5ymv5p`, `bd-ib-hvuhxp`) had ALREADY been closed by another session's
>    dispatches. Caught only by re-querying.
> 2. `bd-ib-wmqsn7` was promoted to an EPIC and re-scoped, and `bd-ib-bwgko4` was
>    CLOSED, by an actively-running peer session — while this file described both as
>    dormant and awaiting tiering.
> 3. This file asserted evidence had been attached to an item BEFORE the write was
>    actually made.
> 4. A defect class was called "worth a general rule" on the strength of two examples;
>    measurement showed it is bounded at exactly those two.
> 5. **A NEW CLASS, found 2026-07-28: the rule was being applied to THIS tenant only.**
>    `bd-ib-d6op2n` was filed here, and described here for two days as unowned work
>    needing hand-routing, while the owning tenant had already filed the same defect six
>    days EARLIER (`livespec-driver-claude-tun`). Nobody had queried the owning tenant's
>    ledger — the entry even said "NO plan thread owns it", which is true and irrelevant,
>    because ownership lives in a ledger, not in a plan thread. **For any cross-tenant
>    prose-linked item, re-query the OWNING tenant — and do it BEFORE filing, not just
>    before acting.** The cost here was a duplicate record of another repo's own bug.
>
> **The trap is that this file is written carefully — and careful is not the same as
> current.** A well-argued paragraph about an item someone else closed an hour ago reads
> exactly like a well-argued paragraph about live work. Nothing in the prose signals the
> difference; only the ledger does.
>
> The same rule applies to the ledger's own claims about the world: an item asserting
> "PR #N produced no merge" is a claim too, and this thread has been burned by trusting
> one. **Verify against the forge after a fetch, and establish outcomes from artifacts —
> a merged PR, a ledger row, a journal record — never from an exit code or a green
> summary.**

## What this thread is

A work-item admitted to `active` by a dispatch that then reaches a terminal
outcome with no defined ledger transition is left in `active` with
`assignee: fabro` **forever**, permanently consuming a WIP slot. The failure is
silent — a full cap is indistinguishable from a busy factory — and it is
monotonic: every abandonment costs a slot that never comes back.

**Ledger anchor:** the three P1 slices below. Status is READ from the ledger
(`list-work-items` / `next`), never stored here.

| slice | id | status 2026-07-26 | scope |
|---|---|---|---|
| S1 | `bd-ib-ohdu5a` | **DONE** — PR #978 merged `a869253` | Harden the dispatch lock's liveness verdict (`started_at_epoch` + `O_EXCL`) |
| — | `bd-ib-l2vglr` | **DONE** — PR #982 merged `acf061c` | The S1 regression: stale reclamation for the now-exclusive lock write |
| S2 | `bd-ib-cfgkkk` | **DONE** — PR #1006 merged `ebe7419` | Surface a stranded merged-yet-unfinished claim in needs-attention |
| S3 | `bd-ib-pme57n` | **DONE** — PR #1014 merged `5b32017`, item `closed` | Stop counting dead claims against the per-repo WIP cap |

Items filed by this thread, none part of the epic. Statuses vary — read each line.

- **`bd-ib-ri1x`** (**P1**, host-only) — **the fleet-level finding, and the most
  valuable thing this thread surfaced. ✅ ROUTED ONWARD 2026-07-28 and CLOSED here
  — the routing obligation below is DISCHARGED; do not re-file it in this tenant.**
  It now lives as **`livespec-j49m`** (P1, `backlog`) in the **core `livespec`**
  tenant, with a spec amendment filed alongside it
  (`SPECIFICATION/proposed_changes/github-app-request-budget.md`, core PR #1811).
  `bd-ib-ri1x`'s close reason carries the full argument and points at
  `livespec-j49m`; that item points back. No `resolution:` label was set, matching
  the `livespec-console-beads-fabro-6ma` cross-tenant precedent — this was a
  RELOCATION, not a fix. **Why core:** core's
  `SPECIFICATION/non-functional-requirements.md` §"Constraints" already owns this
  credential normatively (§"Canonical source" — "one canonical App private key
  shared by all fleet members" — plus §"GitHub automation credential", §"GitHub App
  permission set", §"Obligations per repo class") and is silent only on the request
  BUDGET; `livespec-2ef0` is the precedent for a fleet-wide App finding anchored in
  core; and the installation was measured on 2026-07-28
  (`GET /installation/repositories`) to cover **exactly the 9 fleet members** — the
  adopters are NOT on it — so this repo is one consumer of nine and structurally
  cannot govern the other eight. The finding itself, retained because it is what a
  successor will recognise in the field: the family GitHub App installation's single
  5000/hr PRIMARY bucket is exhaustible and unmeasured; while it is empty EVERY
  credentialed call fails identically (`gh pr create`, the merge poll, the janitor),
  and `mise install` was merely the first consumer to reach it. It carries the
  observable signature and the recommendation to
  **measure before mitigating** — nothing today can answer "what spent 5000
  requests", so any mitigation chosen now is a guess. **First measurements were
  taken 2026-07-27 and are recorded on the item: the two prime suspects are
  ELIMINATED by execution.** The discriminator is that the exhausted bucket was
  `core`, and GitHub meters `core` (REST) and `graphql` separately. (1) The merge
  poll — the factory's highest-volume GitHub operation at **982 `pr-view` records
  across 118 dispatches**, up to 85 on one item — costs **1 graphql point and ZERO
  core**, even returning 94 `statusCheckRollup` entries in a 30 KB payload. (2)
  Installation-token minting costs **zero core** (App-JWT requests are metered
  separately), for one mint or three. So the burn is neither of the obvious
  candidates, and the search now points at REST calls made with the installation
  token — `gh pr merge`/`create`, the now-decoupled `mise install` path, and
  consumers OUTSIDE this repo sharing the fleet-wide installation. The bracketing
  technique (diff `GET /rate_limit` around one real production argv; the call is
  itself free) is written up on the item and eliminates a candidate in ~10s.
- **`bd-ib-3lmt`** (P2, factory-safe) — ✅ **DONE 2026-07-28, PR #1050 / `599e3df`,
  item `closed`.** Dispatched through the factory on maintainer autonomy-tier sign-off.
  The `check-pre-commit` doc-only fast path ran **3 of the aggregate's 72 targets**,
  skipping 69 — all three it kept were Python/tooling checks, so every
  spec-and-doc-integrity check was dropped on the change shape this repo makes most
  often. Five doc-shaped checks are now in the doc-only list
  (`check-heading-coverage`, `check-agents-ai-references-resolve`,
  `check-claude-md-coverage`, `check-handoff-dispatch-routing`,
  `check-plan-thread-anchor-declared`); the path went 3 → 8 targets and ~1.5s → 5.19s,
  and `check-pre-push` delegates to the same recipe so push-time was fixed for free.
  **Verified by re-executing the red against the merged tree**: an unregistered
  `## Scenario 99` heading staged alone now makes `just check-pre-commit` FAIL with the
  same `"level": "error"` diagnostic CI emits, where it previously passed. The stale
  `li-bb5suo` / `li-4liaxt` comment was deleted, not left dangling.
- **`bd-ib-ktxb`** (P2, factory-safe) — ✅ **DONE 2026-07-28, PR #1048 / `521d7f71`,
  item `closed`.** Dispatched through the factory on maintainer autonomy-tier sign-off.
  `reject:<id>:rework` now writes a DURABLE journal record. **Verified by re-executing
  the red against the merged tree**: the real dispatch journal grew where it previously
  gained nothing, and the record carries the actor
  (`{"actor":"operator","stage":"human-valve-reject-rework","work_item_id":…}`), which
  discharges the SECOND injected defect as well as the first. `human-valve` records went
  **0 → 1** of 3,853. `## Scenario 51`'s `TODO` is bound to
  `tests.integration.test_drive_rework_return_scenario51::…` — integration-tier as the
  item required — and that test passes when run directly.
  **Residual worth knowing:** the fix hardcodes the journal path literal rather than
  calling `_dispatcher_paths.py:80`, the canonical resolver for exactly that path. It
  follows existing precedent (3 of 4 call sites hardcode it) and the value is identical
  today, so this is a latent divergence risk, not a defect — the same class as
  `bd-ib-81l0`. UNFILED; surfaced to the maintainer 2026-07-28, not adopted.
- **`bd-ib-bic7hb`** (P2, **host-only**, `ready`) — **was** the S3 blocker; **root
  cause is now SETTLED and half of it has shipped** (PR #1008, `5846ab7`). See §"THE
  S3 BLOCKER — SETTLED". **It stays OPEN deliberately** and its description now
  leads with a status block saying so: the durable prevention (pre-baking the
  aqua-backed tools) is unshipped and is the first two clauses of its acceptance;
  only the third (a real dispatch survives setup) is discharged. It sits `ready`
  rather than `blocked` because host-only items are refused by admission and
  host-routed — that is where they legitimately wait — so **do not dispatch it**.
  **Ownership is borrowed, and the loan is recorded.** By
  charter this belongs to `plan/factory-hardening/` ("reliability hardening of the
  dark-factory dispatch path"), which already holds two items of the same class
  (`bd-ib-bwgko4`, `bd-ib-wmqsn7`). We took it because it was the sole blocker on
  S3 and that thread was dormant at the time. The transfer is written into
  `plan/factory-hardening/handoff.md`'s ledger table and into the item's own
  description, so it cannot be worked twice or dropped.
  **⚠ THE DORMANCY PREMISE EXPIRED 2026-07-28** — see the stand-down note below.
  `plan/factory-hardening/` is ACTIVELY RUNNING. Its two items are NOT waiting on us
  and NOT waiting on a tiering request routed through us.
- **`bd-ib-u46hcv`** (P2, **host-only**) — the upstream `livespec-dev-tooling`
  check defect that took the factory down. **CLOSED 2026-07-27T00:22:55Z, and its
  pin hold has been lifted** — the pin ran v0.54.19 → v0.56.2 later that morning
  and both guards are gone. This thread's pin-hold obligation is DISCHARGED; do
  not re-impose it. It closed with NO recorded close reason or resolution, and the
  "a REAL dispatch must survive setup on the new pin" condition is still UNMET, so
  the next dispatch is the test — see §"The v0.54.19 pin hold". (Earlier revisions
  of this line said no plan thread owned it and that the pin-hold half was ours.
  Both were true when written and are now superseded.)
- **`bd-ib-d6op2n`** (P2, host-only) — the `livespec-driver-claude` core-resolution
  misfire. ✅ **ROUTING OBLIGATION DISCHARGED 2026-07-28, and it turned out to be a
  DUPLICATE. CLOSED here; do not re-file it in this tenant.** The defect is real and
  still unfixed, but the owning tenant had already filed it as
  **`livespec-driver-claude-tun`** on **2026-07-20 — six days BEFORE** we filed ours, and
  theirs is the better item (it carries a measured fleet-exposure table across six repos
  that ours lacked). Closed as a RELOCATION matching the `bd-ib-ri1x` → `livespec-j49m`
  precedent: close reason points at the target, and **no `resolution:` label** is set,
  because nothing was resolved here.
  **⛔ THE PREVIOUS TEXT OF THIS ENTRY WAS THE TRAP, AND IT IS WORTH READING WHY.** It
  said "**NO plan thread owns it** — do not assume a successor has picked it up." That
  was accurate about *plan threads* and completely missed the point: the check that
  mattered was the owning **tenant's ledger**, which nobody had queried. The standing
  re-query rule at the top of this file was being applied only to THIS tenant.
  **Generalize it: for any cross-tenant prose-linked item, re-query the OWNING tenant
  before acting — including before filing, because the duplicate this thread created
  cost the owning repo a second record of its own bug.**
  **Contributed to `livespec-driver-claude-tun` before closing, so nothing was lost:**
  re-verified against the INSTALLED driver build `f320cca4011e` that all eight bindings
  still ship the directory test and none the file test; and the misresolution was
  executed VERBATIM with no operator judgement — the snippet resolves `<core-root>` to
  this repo's `.claude-plugin`, **the not-found guard PASSES (exit 0)**, and both
  `prose/revise.md` and `scripts/bin/revise.py` are absent there. Their 2026-07-20 repro
  had recovered because the operator followed the stated rule instead of the snippet;
  this is the same failure with nobody in the loop.
  **A sequencing finding neither item had, recorded on both:** this defect **MASKS**
  `livespec-driver-claude-6lc` (core-root resolution picks `entries[0]`, an arbitrary
  build). The step-2 directory false-match short-circuits before step 3 ever runs, so
  `-6lc` is invisible in exactly the repos where `-tun` fires. **Fixing `-tun` alone will
  EXPOSE `-6lc`** in those repos, surfacing as a confusing "stale build" error. On this
  host the `livespec@livespec` key already spans **three distinct builds**, so that is
  not hypothetical.
- **`bd-ib-5ymv5p`** (P2, factory-safe) — ✅ **DONE. CLOSED `resolution:completed`,
  PR #1023**, fixed on `master` by `a219f88` "fix: clear assignee on operator moves".
  `move_item` now passes `clear_assignee=True` through
  `store.update_work_item_status`. **Re-verified BY OBSERVATION 2026-07-28**: recovering
  the stranded `bd-ib-ktxb` with `move:bd-ib-ktxb:ready` returned the row as `ready` with
  `assignee: None`, where the defect would have left `assignee: fabro`. The historical
  note is retained because it explains a confusing artifact in this file's own record —
  it bit this thread twice on `bd-ib-pme57n`, where each recovery left `assignee: fabro`
  on a `ready` row, reading exactly like a dispatch in progress.
- **`bd-ib-hvuhxp`** (P2, factory-safe) — ✅ **DONE. CLOSED `resolution:completed`,
  PR #1018.** `CandidateSlice.priority` was dead API surface and was DELETED rather than
  wired through, because `WorkItem` removed `priority` deliberately and `rank` is the
  sole ordering authority.

> **⚠ Both of the two entries above were closed by ANOTHER session's factory dispatches
> on 2026-07-27, while this file still listed them as open work.** They were caught on
> 2026-07-28 only because the ledger was re-queried rather than trusted from this file.
> That is this thread's own recurring lesson turned on itself: **a handoff is a claim
> with a timestamp too.** Before acting on ANY item named here, re-read it from the
> ledger — the statuses in this file are a snapshot, and the ledger is the authority.

Shipped by this thread beyond the slices: **`bd-ib-81l0`** (PR #1000 `47c75ac`,
S2's gate — `reconcile_plan` now threads `resolve_fabro_bin`) and
**`bd-ib-2wgooj`** (PR #1003 `817aeb1` — `_MOVE_ALLOWED` no longer contains
`"active"`, discharging S3's residual). Both verified by re-executing their reds
against the merged tree.

The originating epic **`bd-ib-waov`** was CLOSED 2026-07-26T08:32:25Z by the groom
with the explicit disposition "regroomed out into replacement slices:
`bd-ib-ohdu5a`, `bd-ib-cfgkkk`, `bd-ib-pme57n`". Its description was corrected
BEFORE closing, so the closed record carries the corrected root cause and all three
maintainer rulings rather than the superseded framing.

**Supersedes `livespec-console-beads-fabro-6ma`** (P1, filed 2026-07-20 in the
CONSOLE tenant, closed as superseded + mis-filed). That item diagnosed the
symptom correctly and cited the exact admission arithmetic, but the defect is
entirely orchestrator-side, so it sat six days in a backlog whose owners could not
fix it. Beads has no cross-tenant edge; this prose IS the link, and `-6ma`'s close
reason points back to `bd-ib-waov`.

## ▶ CURRENT STATE + NEXT ACTION (read this first)

### ✅ THE EPIC IS DONE. All three slices shipped and were verified by execution.

Say that plainly too — this thread's charter cuts both ways. It was opened because a
silent failure looked like normal operation for six days, so an unearned "done" is
the same sin as an unearned "almost done". What follows is what was actually
executed, not what a green dispatcher summary reported.

**Shipped and verified** (each red demonstrated by execution BEFORE dispatch and
re-verified flipped afterwards against the merged tree):

| piece | PR / sha |
|---|---|
| S1 `bd-ib-ohdu5a` — PID + `started_at_epoch` liveness, `O_EXCL` claim | #978 / `a869253` |
| `bd-ib-l2vglr` — the S1 regression: TOCTOU-correct stale reclamation | #982 / `acf061c` |
| `bd-ib-81l0` — S2's gate: `reconcile_plan` threads `resolve_fabro_bin` | #1000 / `47c75ac` |
| `bd-ib-2wgooj` — `_MOVE_ALLOWED` drops `"active"` (v050 divergence) | #1003 / `817aeb1` |
| S2 `bd-ib-cfgkkk` — the `host-only:stranded-dispatch` attention lane | #1006 / `ebe7419` |
| `bd-ib-bic7hb` (partial) — sandbox `mise install` runs anonymously | #1008 / `5846ab7` |
| **S3 `bd-ib-pme57n` — the WIP-cap arithmetic** | **#1014 / `5b32017`** |

**S3's verification, 2026-07-26.** The headline red was captured against `5846ab7`
BEFORE the dispatch (`wip_cap` 1, one dead claim, `admitted=[]`, nothing journaled)
and re-run against the merged tree, where it flips. All EIGHT acceptance clauses were
then exercised against the real `admit_and_select` — including the three added by the
predicate amendment — and each passes with a named injected defect that would re-red
it: the dead claim releases its slot; the abandonment is journaled
(`dispatch-claim-abandoned`, reason `terminal-outcome-non-green`); the row's status is
UNTOUCHED; a live lock still consumes its slot; both rework parks (green last outcome)
still COUNT and are NOT journaled; a dispatch killed after `ledger-admit` with no
outcome since IS reclaimed (`no-outcome-since-ledger-admit`); and the reconcile still
runs at `enforce_cap` false / `wip_cap` 0. Structurally confirmed in the shipped code:
`claimed_active_count` is called OUTSIDE the `if enforce_cap:` branch
(`_dispatcher_admission.py:93`), and `write_dispatch_lock` now fires at ADMISSION time
(`:124`) as well as at `dispatch_one` entry.

**End-to-end on the real tenant, which is the proof that matters.** Against the live
ledger and a COPY of the real journal (read-only — the real journal was not written):
`bd-ib-w4h4`, the six-day stranded claim this epic was opened for, has no live lock
and a non-green terminal outcome, so `claimed_active_count` now returns **0** where the
raw `active` row count is **1**. Its status is untouched, so `reconcile-merged` still
accepts it. And S2's lane surfaces it with the right handoff, carrying the
prior-attempt count the S2 constraint demanded:

```
host-only:stranded-dispatch:bd-ib-w4h4 [high] Reconcile merged active work-item
  bd-ib-w4h4: PR #836 merged at ba9fdaf...; janitor-post-merge failed across 3
  prior attempts.
  Handoff: dispatcher.py reconcile-merged --repo <path> --item bd-ib-w4h4 --json
```

Reclaimed capacity AND a surfaced failure with an actionable handoff — the pair the
charter insisted on, since either alone re-hides the defect.

**✅ RE-VERIFIED 2026-07-28 against the CURRENT tree — the headline fix still holds.**
The original proof was taken on 2026-07-26; a great deal has landed since (six
dev-tooling pin bumps to v0.56.6, two factory dispatches, and several merges), so the
epic's central invariant was re-run rather than assumed:

```
live ledger:
  raw `active` row count : 1
    - bd-ib-w4h4  assignee=fabro
  claimed_active_count() : 0
```

A raw `active` row that costs ZERO WIP capacity — which IS the fixed behavior. Run
against the live ledger and a COPY of the real journal; the real journal was confirmed
byte-identical before and after by two independent size checks, so this verification
wrote nothing.

Nothing is in flight from this thread. Repo clean on `master`, no orphaned worktrees.

**`bd-ib-w4h4` remains deliberately stranded, and that is still correct.** It is the
live fixture, it is the ONLY `active` row, and it now costs no WIP slot — which is
precisely the fixed behavior. It becomes recoverable once `bd-ib-rxxx` lands; do not
un-strand or close it before then.

**Remaining open work is NOT part of this epic** — see the filed-items list above and
§"The revise pass". The epic anchor `bd-ib-waov` was already closed at groom time.

### ✅ CLOSE-OUT 2026-07-27 — this thread has NO in-flight work

Both assignments this thread carried are complete. Stated plainly so a successor does
not go looking for work that is finished, and does not mistake the leftovers for it:

| assignment | outcome |
|---|---|
| The epic `bd-ib-waov` — all three slices | **DONE.** S1 `bd-ib-ohdu5a` #978/`a869253`; S2 `bd-ib-cfgkkk` #1006/`ebe7419`; S3 `bd-ib-pme57n` #1014/`5b32017`. Plus `bd-ib-l2vglr` #982/`acf061c`, `bd-ib-81l0` #1000/`47c75ac`, `bd-ib-2wgooj` #1003/`817aeb1`, and `bd-ib-bic7hb` (partial) #1008/`5846ab7`. |
| The `/livespec:revise` pass over BOTH pending proposals | **DONE.** Ratified as **v051**, PR #1036 / `715d81a`. `reconcile-merged-dispatch-lock` → modify; `rework-return-door-attribution` → accept, both findings. |

Verified on the forge after a fetch, not from a working tree:

- **`SPECIFICATION/proposed_changes/` is EMPTY** of in-flight proposals (`.gitkeep`
  only), and `SPECIFICATION/history/v051/` is present on `master`.
- **`git for-each-ref refs/heads/spec/` is EMPTY** — the next revise pass's Step 3.5
  precondition is clear. (Re-check it at ITS run time anyway; that is the whole
  lesson of §"The blocking precondition".)
- Primary checkout clean on `master`; no worktrees left by this thread.

**What remains is filed, not in flight.** This list said TWO pre-existing unowned items —
`bd-ib-bic7hb` and `bd-ib-d6op2n`, both `ready` and host-only. **It is now ONE.**
`bd-ib-d6op2n` was CLOSED 2026-07-28 as a duplicate of `livespec-driver-claude-tun`,
which the owning tenant had filed six days earlier; see its entry in the filed-items list
above for what was contributed there before closing. **`bd-ib-bic7hb` is the only one
left**, it is not part of this epic, it is not blocked on this thread, and the
filed-items list says who owns it and why it is where it is.

**Re-verified against the ledger 2026-07-28, and the list SHRANK.** `bd-ib-5ymv5p` and
`bd-ib-hvuhxp` were also on this list and are now CLOSED `resolution:completed` — fixed
by another session's factory dispatches (PR #1023 and PR #1018) on 2026-07-27. Do not
chase them.

**TWO NEW ITEMS WERE FILED 2026-07-28. Both are UNTIERED by design** — the
`autonomy_tiered` Definition-of-Ready gate is a human sign-off and must not be
self-signed — so neither is dispatchable until a maintainer tiers it. **Neither is part
of this epic.**

- **`bd-ib-xw2k`** (P3, `backlog`) — the dispatch-journal path has TWO conventions.
  `_dispatcher_paths.journal_path` honors a `--journal` override that six-plus dispatcher
  call sites resolve through, while `bd-ib-ktxb`'s journal write
  (`_drive_valves.py:205`) and both `_needs_attention_*` readers rebuild the literal by
  hand and silently ignore it. **LOW SEVERITY and deliberately filed as such** — `drive`
  exposes no `--journal` flag, so today the literal and the resolver produce an identical
  path and nothing is broken. Filed anyway because the failure it sets up is an ABSENT
  journal record, which is precisely the silent-failure class this epic exists to remove.
  Do NOT re-open `bd-ib-ktxb` over it; that fix is correct and merely followed the
  majority local precedent.
- **`bd-ib-91wj`** (P2, `backlog`) — a janitor-created checkout lacks the worktree pack,
  so `reconcile-merged` fails `primary_checkout_commit_refuse_hook_installed`
  (`worktree_pack_absent`) on v0.56.x. **Measured by the `livespec-console-beads-fabro`
  track and assigned to this tenant because the fix is orchestrator-side** — the janitor
  creates the checkout, so the janitor bootstraps it. **SCOPE WAS NARROWED HERE against
  our own journal**: the originating report said it "blocks every dispatch on this host",
  but `bd-ib-ktxb` (00:55:55Z) and `bd-ib-3lmt` (01:24:01Z) both passed
  `janitor-post-merge` and reached done/green on the same host, same day, under v0.56.x.
  Every failing artifact comes from a `reconcile-merged` run and a
  `janitor-reconcile-<id>` checkout. Cross-referenced with `bd-ib-rxxx` in both directions
  but deliberately NOT folded into it: `bd-ib-rxxx` is derived-coverage divergence, this
  is a missing bootstrap.
  **✅ ITS OPEN QUESTION IS NOW SETTLED — read the item's NOTES before touching it.** The
  item originally named two candidates and told the implementer to establish which one
  first. **Both were refuted by source inspection 2026-07-28, and the real mechanism is
  neither: it is PLUGIN-REVISION SKEW BETWEEN SESSIONS.**
  **⚠ THAT SENTENCE IS ITSELF SUPERSEDED — see the discharge box at the top of this file.**
  The skew is real and everything below this line still holds, but "between SESSIONS" names
  the wrong axis: which build runs is **entry-point-resolved**, and a session pin applies to
  the plugin-invoked entry point only. Kept rather than deleted because the janitor-argv
  evidence below is what established the skew in the first place. The janitor argv is baked into
  the plugin's `_DEFAULT_JANITOR`, and it changed — revision `1567e8f200dc` (which the
  console session's dispatch ran) is `("mise","exec","--","just","check")`, while
  `c878ea43f8cd` (installed for this project) is
  `(…,"check-no-workflow-edits","install-worktree-pack","check")`. `install-worktree-pack`
  runs immediately before `check` in the newer revision, which is exactly why THIS
  tenant's two dispatches passed while their reconcile failed — same host, same day,
  different plugin revision. Neither repo sets a `janitor` config key, so both take the
  default. Two consequences are written up on the item: a plugin refresh may suffice for
  their symptom (code landed in a working tree does nothing for a session pinned to an
  older cached revision) — **⛔ it does NOT: it resolves the `worktree_pack_absent` half
  only, and their publish refusal has a second cause a refresh cannot reach; see the
  two-causes correction in the stop box** — and the janitor ARGV is the wrong durable home for the fix
  because `janitor_argv_with_default` is per-repo overridable — the robust placement is
  `_provision_janitor_checkout`'s `steps` tuple, with `cwd=plan.janitor_checkout` (the
  check asserts hooks in the PRIMARY and the pack in the WORKTREE; the existing
  `janitor-checkout-bootstrap` step satisfies only the first).
  **⛔ The console track's kept checkout at
  `~/.worktrees/livespec-console-beads-fabro/janitor-reconcile-...-dm5f7q` is PRESERVED
  EVIDENCE.** They are deliberately not working around the defect so it cannot hide. Do
  not remove it, install a pack into it, or run anything that precleans it.

**`bd-ib-3lmt` and `bd-ib-ktxb` are no longer on that list — both SHIPPED 2026-07-28**
(PR #1050 / `599e3df` and PR #1048 / `521d7f71`), dispatched serially through the
factory on maintainer autonomy-tier sign-off and each verified by re-executing its red
against the merged tree. See their entries in the filed-items list above.

**`bd-ib-ri1x` is no longer on that list — it was ROUTED to core and closed here on
2026-07-28** (now `livespec-j49m`; core PR #1811 carries the spec amendment). See its
entry in the filed-items list above. It is the one item from this thread that left
the tenant entirely, so a successor looking for it in this ledger will not find it.

**The one live obligation anyone inherits is the pin assumption**, not a task — and it
is now **NARROWED**: the setup leg is VERIFIED on v0.56.3, so what remains untested is
the dispatch path PAST setup. See §"The v0.54.19 pin hold" → §"SETUP IS NOW VERIFIED".

#### 2026-07-28 addendum — three LEDGER-ONLY writes, invisible to a code reader

These left no commit in this repo. Recorded here because nothing else would surface them.

| what | where it lives |
|---|---|
| Field evidence for the master-CI flake that killed a dispatch | **`bd-ib-wmqsn7` notes** (this tenant) |
| The same doc-only pre-commit defect, found in a SIBLING | **`bd-gj-pch`** (`livespec-orchestrator-git-jsonl` tenant) |
| The FLEET-level version of it | **`livespec-r5df`** (core `livespec` tenant) |

**`bd-ib-wmqsn7` now genuinely carries the evidence.** An earlier revision of this file
claimed it did BEFORE the write had been made — that claim was premature and is now
true. Attached: `bd-ib-ktxb` attempt 1 dying at 7 minutes with no agent work, the PyPI
`hypothesis-jsonschema` timeout that reddened master, and three things the item's
original description did not have — (a) the flake class is BROADER than the "cpython
from GitHub" it names, since this one was a different package from a different host, so
a fix that retries only the cpython fetch under-fixes; (b) `gh run rerun --failed`
WORKED here, where the item records it being refused on the first occurrence, so the
recovery recipe is `--failed` first then full re-run; (c) the reddening commit was
DOCS-ONLY and could not have broken anything. Its `blocked` / needs-human status was NOT
touched.

**The doc-only gap is fleet-wide, and this repo was simply the first to look.** Surveyed
2026-07-28 by reading every member's own justfile. The five doc-integrity checks are
`check-heading-coverage`, `check-agents-ai-references-resolve`,
`check-claude-md-coverage`, `check-handoff-dispatch-routing`,
`check-plan-thread-anchor-declared`:

| repo | doc-only fast path | aggregate | of the 5, actually run |
|---|---|---|---|
| `livespec` (core) | 7 targets | 73 | **2** |
| `livespec-orchestrator-beads-fabro` | 8 targets | 72 | **5** — fixed today, PR #1050 |
| `livespec-orchestrator-git-jsonl` | 3 targets | 65 | **0** |
| `livespec-dev-tooling` | no-op `exit 0` | 64 | **0** |
| `livespec-overseer` | no-op `exit 0` | 62 | **0** |
| `livespec-runtime` | no-op `exit 0` | 62 | **0** |
| `console`, `driver-claude`, `driver-codex` | none — full gate | — | all (no gap) |

**Every repo in the top six already HAS all five in its own aggregate**, so this is not
"the checks don't exist there yet" — they exist and are unwired. Two distinct stale
rationales are involved: git-jsonl carries the byte-identical dead
`li-bb5suo`/`li-4liaxt` comment this repo just deleted, while dev-tooling, overseer and
runtime each say "no repo-metadata checks wired yet" — also false.

Both filings verify the safety precondition the pre-dispatch review established, rather
than assuming it ports: all five were RUN in git-jsonl and all five PASS, so wiring them
would not instantly block that repo's commits. Neither item sets an autonomy tier — an
agent must not self-sign another tenant's work through a human gate.

`livespec-r5df` argues the durable fix is a `check-fleet-conformance` rule rather than
six hand-fixes, since nothing keeps these recipes aligned and that is exactly how the
six-way divergence arose.

**The safety precondition is now measured for ALL SIX repos, not two.** Each of the five
checks was RUN individually against each repo's current tree: **every check passes in
every repo**, so wiring them is safe everywhere — no repo would suffer an instant false
refusal. Recorded on `livespec-r5df`'s notes.

**Scope is BOUNDED — do not go hunting for more stale rationales.** The fleet was swept
for comments asserting a temporary state pending a work-item ("until X lands", "not
wired yet", "temporarily", "intentionally absent") across every member's `justfile`,
`pyproject.toml`, `.livespec.jsonc`, `lefthook.yml` and CI workflows. **Exactly ONE
instance of the "until those land" form remains fleet-wide** — git-jsonl's, already
filed. Every other "intentionally absent" hit is CI `needs:` wiring, a PERMANENT design
statement rather than a resolved condition. A broader sweep for the dead `li-` id scheme
returns many hits, but they are almost all legitimate PROVENANCE citations ("epic
li-cvaudit") explaining why a rule exists — **those are correct and must not be treated
as stale.** The defect is a comment asserting a condition that has since resolved, not a
reference to an old id.

**⚠ A SEPARATE small defect found while measuring, worth knowing because it produces a
FALSE RED on any long-lived checkout.** `check-claude-md-coverage` FAILS in core
`livespec`'s primary checkout, reporting four directories missing a required
`CLAUDE.md` — and **the same check PASSES in a fresh worktree of the same commit,
because none of those directories exists in the repo at all.** They were deleted from
git months ago (`4916bfa2` 2026-06-24 "retire orphaned implementation-gaps subsystem";
`b930d9bd` 2026-06-11 "extract the Claude Code Driver bindings"), and what remains on
disk is a stale `__pycache__/` inside each. `git status --porcelain
--untracked-files=all` reports **zero** untracked entries, because a directory holding
no tracked files and only ignored content is invisible to git — so the cruft evades the
usual cleanliness check.

**This is the MIRROR IMAGE of a failure mode already recorded in this file.**
`primary_checkout_commit_refuse_hook_installed` fails on a FRESH clone and passes on a
bootstrapped one, because it asserts a gitignored worktree pack (see §"The v0.54.19 pin
hold"). Same root cause inverted: a check reading filesystem state that git does not
track, so its verdict depends on checkout age rather than repo content. Practical impact
here is low (nobody commits on a primary checkout; every worktree is fresh), but it costs
diagnosis time and invites the wrong fix. **Do NOT fix it by creating those `CLAUDE.md`
files** — the directories were deliberately deleted. Remedy is either clearing the stale
`__pycache__` on that machine (local cleanup, not a repo change) or narrowing the check
to skip a directory containing no tracked files. Recorded on `livespec-r5df`; NOT
separately filed.

**⛔ CORRECTED — an earlier revision of this paragraph said "two independent instances
now — the class is worth a general rule". That was an inference from two examples, and
MEASUREMENT DISPROVED IT.** The class is real but **bounded at exactly those two**; a
suite-wide rule is NOT warranted.

The static reading looks alarming and is misleading: of the 71 modules in
`livespec_dev_tooling.checks`, **17 walk the filesystem directly** (`rglob`/`iterdir`/
`glob`) and **only one — `file_lloc` — consults git (`ls-files`) for its file set.** So
17 checks appear exposed. Rather than read all 17, each was RUN in core's primary
checkout AND in a fresh worktree of the SAME commit, and the results diffed (16 runnable
there; `check-tool-backed-surfaces` is absent from core):

```
check-claude-md-coverage                             primary=FAIL   fresh=PASS
check-primary-checkout-commit-refuse-hook-installed  primary=PASS   fresh=FAIL
(the other 14: identical in both)
```

**Exactly 2 of 16 diverge, in OPPOSITE directions, and both were already known.** No
third instance exists **within this population**. So walking the filesystem is NOT by
itself the defect — 14 of 16 do it safely, because they key off content that cannot exist
untracked. **Fix the two specific checks; do not generalize from two examples.** The
lesson is this thread's own:
an inference is not a measurement, and it was worth ten minutes to find out which one
this was.

**⚠ THE COUNT IS NOW THREE, not two — see §"`bd-ib-rxxx` ROOT-CAUSED" below.** The
measurement above swept the 71 modules in `livespec_dev_tooling.checks` and is sound
within that population. `check-coverage` is a **justfile recipe**, not a checks module,
so it was never in the sample — and it diverges harder than either of these two: it
branches on a gitignored `.coverage` file to decide **which command to run**, so the same
coverage shortfall reports as exit 2 in one venue and exit 1 in another. The method here
was right; only its population was too narrow. **Do not read "bounded at exactly two" as
covering the justfile.**

#### Session close-out addendum — work done AFTER the close-out above

All of it merged; none of it changed the "no in-flight work" status. Recorded because
two pieces live on the LEDGER and would otherwise be invisible to a successor reading
only this file.

| what | where it landed |
|---|---|
| Pin setup verified on v0.56.3 by a non-admitting probe | PR #1041 / `5aaceeb` (in this file) |
| Acceptance evidence for `bd-ib-lza6` + `bd-ib-ug4z`; first `bd-ib-ri1x` measurements | PR #1042 / `a35b804` (in this file) |
| **`bd-ib-3lmt` root-caused, costed, retitled** | **ledger notes only** |
| **`bd-ib-ri1x` control experiment + problem sizing** | **ledger notes only** |

**`bd-ib-3lmt` is now implementation-ready — read its notes before touching it.** The
defect is NOT "one check was forgotten": `just check-pre-commit` takes a **doc-only
fast path** whenever zero `.py` is staged (`justfile:1176-1198`), and that path
(`:1230-1250`) runs **3 of the aggregate's 72 targets** — all three of them
Python/tooling checks — so **every spec-and-doc-integrity check is skipped on exactly
the change shape this repo makes most often.** Cost measured: the six cheap doc checks
add **5.26s** (1.50s → 6.76s), while `check-doctor-static` alone is **10.13s**;
recommended two-tier split with doctor gated on `SPECIFICATION/**` being staged. The
check that actually fired, `check-heading-coverage`, is the **cheapest of the seven at
0.87s** — there was never a performance reason for its absence.

**`bd-ib-ri1x` now has a unit and a control.** A REST call with the installation token
spends exactly **1 core point** (verified against `gh api`, so the earlier zero-deltas
are real eliminations and not a dead counter). Therefore draining 5000 needs **~83 REST
calls/minute sustained for an hour** — which no observed factory operation approaches,
since the merge poll (982 calls across the WHOLE journal) spends **zero** core. That
points the search away from this repo's dispatch loop and corroborates the item's
fleet-level framing.

**⚠ BOTH OF THE FOLLOWING WERE RESOLVED ON 2026-07-28 — read the resolution, not just
the original reasoning.** The reasoning is retained because it was correct at the time
and the escalation it describes is the pattern to repeat; only the outcome changed.

1. **Did not dispatch the factory-safe items it filed** (`bd-ib-3lmt`, `bd-ib-ktxb`).
   They sat `backlog` because they were filed with raw `bd create`, which bypasses the
   intake dialogue. Reaching a dispatchable lane requires the six-gate Definition-of-
   Ready (`intake_dor.py`), one gate of which — `autonomy_tiered` — is a deliberate
   HUMAN sign-off before an unattended dispatch. Self-signing one's own filing through
   that gate is precisely what it exists to prevent.
   **✅ RESOLVED 2026-07-28: escalated to the maintainer, who signed off on the autonomy
   tier for BOTH. Both then cleared all six gates through the real `apply_intake_dor`
   primitive (NOT a hand-set label), were dispatched SERIALLY, and both merged.** Note
   for anyone auditing: both items already carried an `intake:triaged` label despite
   being raw-filed, so **that marker was not trustworthy here** — the gate was re-run
   rather than believed.
2. **Did not modify `check-pre-commit`** despite having the fix scoped and costed.
   It is a SHARED surface — every session's commits run it — and other sessions were
   actively committing throughout. That is a maintainer call, not a unilateral one.
   **✅ RESOLVED 2026-07-28: the maintainer required TWO independent codex reviews as a
   PRECONDITION of dispatch, and they changed the shipped fix.** The safety lens found
   no regression (all candidates pass individually; none touches network/`gh`/ledger/
   credential-wrapper; no Red-Green-Replay interaction, since the doc-only and Red/Green
   branches are mutually exclusive on `py_staged`). The correctness lens found the item
   itself was not implementation-ready. Three findings landed in the shipped result:
   `check-comment-line-anchors` was **dropped** (its docstring proves it walks `.py`
   files only, so on a zero-`.py` commit its result cannot change — it was the most
   expensive candidate for zero signal); the acceptance's second clause was **rescoped**
   (it was scoped to `SPECIFICATION/**.md`-or-`heading-coverage.json` while the branch
   actually triggers on zero `.py` staged, and no check accepts a path argument — an
   implementer told to satisfy it literally would have built `git diff --cached` gating
   the recommendation calls unnecessary); and deleting the stale comment became a
   **required acceptance clause** rather than a nicety.
   **The reviews disagreed, and that was the point.** One ran
   `check-comment-line-anchors` and it passed; the other called it dead weight. Both
   were right inside their own lens — passing is not the same as signalling — and
   neither was right about the decision, which was settled by reading the module
   directly. **Do not arbitrate competing review summaries against each other; go to the
   artifact.**

#### 2026-07-28 addendum — the two untiered items were MEASURED; both premises moved

Three more LEDGER-ONLY writes, invisible to a code reader. No item was closed, retitled,
re-scoped or tiered — an agent must not sign the `autonomy_tiered` gate. What changed is
that a maintainer can now decide both without re-deriving anything.

| what | where it lives |
|---|---|
| `bd-ib-91wj`'s reported defect is ALREADY FIXED on master | **`bd-ib-91wj` notes** |
| The `--janitor` override surface is exercised, refining the above | **`bd-ib-91wj` notes** |
| `bd-ib-xw2k`'s "nothing passes `--journal`" premise is FALSE | **`bd-ib-xw2k` notes** |
| **A FOURTH, added later on 2026-07-28** — the seven "a plugin refresh is the remedy" sentences in `bd-ib-91wj`'s notes are scoped to the `worktree_pack_absent` half only | **`bd-ib-91wj` notes** |

**Why the fourth was necessary, and it is worth knowing before you read that row.** Beads
notes are **append-only**, so the seven stale sentences cannot be edited in place. Left
alone, the row **contradicted itself**: seven of this thread's sentences said a plugin
refresh was *the* remedy, while `factory-hardening`'s note on the same row said *"a plugin
refresh cannot fix the second."* **A tierer reads the notes**, so a self-contradicting row is
a live hazard, not an untidy one. The correction scopes all seven at once and points at
theirs as correct; the janitor half is settled and must not be re-litigated.

**`bd-ib-91wj` — do NOT tier this for dispatch as written; its acceptance is already
satisfied.** `install-worktree-pack` entered `_DEFAULT_JANITOR` in commit **`14c3cae`**
(2026-07-26 22:57 UTC), and that commit's own body names the IDENTICAL failure this item
reports — the `bd-ib-hvuhxp` reconcile, PR #1018, `worktree_pack_absent`, claim stranded
`active`. So the item is a **re-report of an already-fixed defect**, which is exactly what
the plugin-revision-skew mechanism predicts.

Proven by execution, red → green, in a throwaway worktree of master (since removed):
`primary_checkout_commit_refuse_hook_installed` fails with
`"failure_mode": "worktree_pack_absent"` at exit 4, `just install-worktree-pack`
materializes all four pack files, and the same check then exits 0. Both the dispatch and
`reconcile-merged` paths share the argv — `reconcile_plan` and `_dispatcher_loop` both
call `build_plan`, which resolves through `janitor_argv_with_default`.

**The skew is now measured, not inferred.** Of ~75 cached plugin revisions on this host,
**only 5 carry the pack step**. The revision the console session dispatched on,
`1567e8f200dc`, is release **0.45.18 dated 2026-07-20** — a week older than the fix
(`git merge-base --is-ancestor 14c3cae 1567e8f200dc` is false). ~~**A plugin refresh is the
whole remedy for their symptom**, and it needs no code change.~~

> **⛔ SCOPE CORRECTION, 2026-07-28 — "the WHOLE remedy" is wrong; the rest of this
> paragraph stands.** A plugin refresh IS the whole remedy for `worktree_pack_absent`, which
> is what this section measures, and every measurement above is unaffected. It is **NOT** the
> whole remedy for the console track's *symptom*, because their symptom spans two causes: the
> other is their repo-local `.fabro/workflows/implement-work-item/prompts/pr.md`, which
> overrides the plugin's bundled copy and never received `231e9a4`. **A refresh structurally
> cannot reach a file their repo commits.** See the two-causes correction in the stop box.
> **This is a SCOPE error, not a fact error** — the claim was true of the half it was
> measuring and false of the whole it was stated about, which is exactly RULE 1's shape
> applied to a remedy instead of an absence.

**A self-correction recorded on the item, because the distinction matters.** The first
note claimed the per-repo-override fragility has "zero exposure", from reading all 9
fleet members' `.livespec.jsonc` and finding no `janitor` key. True — but it measured the
*config key* only. `orchestrator-image/acceptance-live-golden-master.sh:602` passes
`--janitor "[\"true\"]"` as a **CLI flag**, so the override path is live code. Harmless
there (a `true` janitor runs no `check` at all), but it means the durable-placement
hardening — move the pack install into `_provision_janitor_checkout`'s `steps` tuple with
`cwd=plan.janitor_checkout` — is better motivated than "latent" suggested.

**`bd-ib-xw2k` — its stated premise is false, in the item's favour.** The description
argues the divergence is harmless because `drive` exposes no `--journal` flag. That half
is true, but the override is passed on the OTHER side of the pair: **three committed
scripts pass a non-default journal path to `dispatcher.py loop` today** —
`tier2-dispatch-proof.sh`, `real-work-dispatch.sh` and `acceptance-live-golden-master.sh`,
each with its own `/tmp/livespec-*.jsonl`. Exact inventory: **7 call sites resolve**
through `journal_path` (the description estimated "six-plus"), **3 hardcode the literal**
(`_drive_valves.py:205`, `_needs_attention_work_items.py:44`,
`_needs_attention_stranded_dispatch.py:22`).

**The mechanism is CROSS-CLI, which constrains the fix.** `--journal` is declared only on
the dispatcher (`dispatcher.py:332`, `:354`); `drive` and `needs-attention` are separate
CLIs with no such argument, so the three sites are not ignoring an override they were
handed — there is no `args.journal` to thread. The failure it sets up is that a
`--journal` run's records are invisible to S2's stranded-dispatch lane: an ABSENT record,
the epic's own silent-failure class. **Honest limit that keeps it low severity:** none of
the three callers invokes `drive` or `needs-attention` in the same run, so the two
conventions are each live but never meet today. Recommended fix on the item is a shared
no-argument default resolver — one definition instead of four, no behavior change, and a
prerequisite for ever honoring an override in those CLIs.

**⚠ THE PIN HAS MOVED AGAIN — twice — SINCE THE ASSUMPTION WAS DISCHARGED.** The two
end-to-end dispatches that paid off the standing assumption ran on **v0.56.6**. Since
then: `cc95594` → v0.56.7, and `127cb4a` → **v0.57.0** (2026-07-28 06:27:15Z), with the
sandbox image pin now `python-agent-v0.57.0`. The dispatch journal's last record is
**04:59:58Z**, before that bump, so **nothing has dispatched on either new pin.** This is
recorded as fact, NOT as a re-imposed hold — the maintainer released that hold
deliberately and it must not be re-imposed. Read "assumption fully discharged" as scoped
to v0.56.6, which is what it was measured on.

#### 2026-07-28 — `bd-ib-rxxx` ROOT-CAUSED. It names the wrong check. (ledger-only write)

This one matters to us directly: `bd-ib-rxxx` is the item gating `bd-ib-w4h4`, our live
fixture. Its own correction note asked for a re-diagnosis with the interpreter pinned,
and nobody had run it. It has now been run, and the answer is not either candidate.

**The janitor red was `check-coverage`, not `supervisor_discipline`.** The failure detail
the item quotes is the **tail** of the janitor's `just check` output, and the
`supervisor_discipline` lines in it are `"level": "warning"`. The aggregate ran straight
past them — the same detail string continues through `tests_mirror_pairing`, `ruff`,
`pyright` and only then prints `error: Recipe check-coverage failed with exit code 2`,
then `error: Recipe check failed with exit code 1`. All three of `bd-ib-w4h4`'s
janitor-post-merge records carry that identical tail. **The warning was the most
conspicuous line in the output, not the cause** — its own text even says it does not
hard-fail at Phase 0.

**Both of the item's competing theories are refuted by execution.** A fresh detached
worktree of `ba9fdaf` (the exact commit the janitor checked out) with
`livespec-dev-tooling 0.50.7` (the exact version it ran), interpreter pinned to that
worktree's own `.venv/bin/python` and the loaded version confirmed via
`importlib.metadata` — so the interpreter confound the item warned about does not apply:

```
dev-tooling : 0.50.7
$ python -m livespec_dev_tooling.checks.supervisor_discipline
EXIT CODE = 0        records by level: {'warning': 8}
```

Checkout-dependence of `supervisor_discipline`: refuted. The v0.50.7 → v0.50.8 version
theory: refuted, because v0.50.7 *itself* passes.

**The real failure reproduces, and it is one line.** `just check-coverage` in that same
probe worktree fails at **99.99%** — 1 miss and 1 partial branch out of 25064/3076. The
missing line is `_dispatcher_janitor_lock.py:133`, **in the very file `bd-ib-w4h4`'s own
PR #836 modified**.

**⚠ THE ITEM'S THESIS IS RIGHT; IT IS ATTACHED TO THE WRONG CHECK — and this is a third
member of a family this file already documents.** `check-coverage` branches on a
**gitignored** file:

```bash
if [[ -f .coverage ]]; then  uv run coverage report --fail-under=100   # exit 2
else                         uv run pytest -n 4 --cov ...              # exit 1
```

**The exit codes prove the two runs took different arms.** The janitor's journal records
`exit code 2` — the `coverage report` arm. The fresh-checkout reproduction exits **1** —
the `pytest` arm. Same commit, same dev-tooling, different command, decided purely by
whether an untracked `.coverage` file was present.

That is the same class as the two divergent checks recorded above
(`primary_checkout_commit_refuse_hook_installed` needs a gitignored worktree pack;
`check-claude-md-coverage` reads stale `__pycache__`) — **so the "bounded at exactly
two" measurement in that section is now superseded: there are three, and this third one
is the worst of them, because it silently changes WHICH COMMAND RUNS rather than merely
flipping a verdict.** The earlier measurement was sound — it swept
`livespec_dev_tooling.checks` modules, and `check-coverage` is a justfile recipe, outside
that population. Correcting the count, not the method.

**What this does NOT license.** `bd-ib-w4h4` still must NOT be un-stranded or closed by
an agent — it is the deliberate live fixture, it costs no WIP slot, and that is a
maintainer call. What has changed is that the reason it was parked is now understood
rather than mysterious, and the item's "BLOCKS re-dispatching `bd-ib-w4h4`" clause is
doubly moot: it was already moot because the PR merged, and nothing about
`supervisor_discipline` was ever blocking it.

**`bd-ib-rxxx` needs retitling and rescoping by its owner** — its title names a check
that does not fail, and an implementer would spend the whole budget in the wrong module.
Not done here: retitling is a ledger write on someone else's framing. The full evidence,
the recommended rescope, and three honest limits are on the item's notes.

##### ✅ COMPLETED the same day — the mechanism is the RUNNER'S UID, and it was FIXED on 2026-07-20

The section above left an honest limit — *"whether CI passed PR #836 by taking the other
arm was not established"*. It has now been settled, and **it corrects the section above:
the `.coverage` arm was never the cause of the shortfall.** The cause is the effective
UID of the process running the tests.

`claim_janitor_lock` consults liveness through a short-circuit `or`
(`_dispatcher_janitor_lock.py:75`):

```python
if lock is None or lock.pid == os.getpid() or _pid_is_alive(pid=lock.pid):
```

So reaching `_pid_is_alive`'s direct `return True` needs a pid that is NOT ours and that
`os.kill(pid, 0)` can signal WITHOUT raising. The only live-pid test probes **pid 1** —
and `os.kill(1, 0)` raises `PermissionError` for an unprivileged uid but **succeeds for
root**. Measured with one test and one codebase, root reproduced at the syscall boundary
by monkeypatching `os.kill` so no privileged run was needed:

```
non-root       : missing ... 109, 133
simulated root : missing ... 109, 134
```

**Byte-identical except which line of `_pid_is_alive` goes uncovered.** CI ran PR #836 in
the baked `container:` as ROOT (the workflow's own comment says so), covering line 133 →
100% → merged green. The post-merge janitor ran on the host as `ubuntu` (uid 1000) →
line 133 never executed → 99.99% → red → claim stranded. Same commit, opposite verdicts.

**⛔ AND IT WAS ALREADY FIXED — the same day the item was filed.** `ff97ad8`
(2026-07-20 22:46:11 +0200), *"fix: restore the janitor gate for non-root runners and
cover the reclaim mutex"*, added `test_dispatcher_janitor_lock_nonroot.py`, whose
docstring states this mechanism independently and in the same terms ("CI's root container
masked it"; the pid-1 `PermissionError`; the `lock.pid == os.getpid()` short-circuit). It
also closed a second hole nobody had noticed — the `fcntl.flock` reclaim mutex had no
coverage at all. **The fix is CI-guarded now**: the `check-python` matrix gained a `uid`
dimension, and both `check-coverage (root)` and `check-coverage (nonroot)` pass on recent
`.py`-changing PRs (#1050, #1048). So the item has sat open since 2026-07-20 describing
behavior that stopped existing ~17 hours after it was filed. **Recommend CLOSING it**;
that is its owner's call, not taken here.

**What survives, and it is genuinely separate:** the `check-coverage` arm-switching on a
gitignored `.coverage` file is real, is untouched by `ff97ad8`, and remains the third
member of the gitignored-state divergence family.

**⛔ CORRECTION — an earlier revision of this paragraph said it "deserves its OWN item".
DO NOT FILE ONE: it is ALREADY FILED as `bd-ib-d6v1`** (P1, `backlog`, 2026-07-20) —
*"just check-coverage reuses a STALE .coverage with no freshness check"*. It quotes the
same recipe and names both failure directions. Following the withdrawn recommendation
would have duplicated a P1. Corroboration was contributed there instead: the recipe is
unchanged on master, and the two arms return **different exit codes for an identical
shortfall** (reuse arm 2, suite arm 1) — which is a useful diagnostic handle and a trap,
since a `check-coverage` exit 2 does NOT by itself imply stale data.

**`bd-ib-w4h4`'s stated precondition is therefore MET IN SUBSTANCE** — the defect that
stranded it is fixed and guarded, though the item tracking it is still open. **This still
does NOT license un-stranding it.** That remains a maintainer call, and it costs no WIP
slot where it sits.

#### ⚠ 2026-07-28 — THE REAL PATTERN: this ledger accumulates ALREADY-FIXED items. Filed as `bd-ib-js1f`.

Four separate times in one session, an item this thread was about to act on turned out to
describe work already done. That stopped being a coincidence, so it was measured, and the
measurement is now a filed item — **`bd-ib-js1f`** (P2, `backlog`, **UNTIERED**; an agent
must not self-sign the `autonomy_tiered` gate, least of all on this subject).

Eight non-closed items were checked against the merged tree, each verdict from execution
or from reading the code — never from reading the item:

| item | P | verdict | evidence |
|---|---|---|---|
| `bd-ib-91wj` | P2 | **fully stale** | fixed by `14c3cae`; red→green reproduced |
| `bd-ib-rxxx` | P1 | **fully stale** | fixed by `ff97ad8`, ~17h after it was filed |
| `bd-ib-tyee` | P1 | **stale on OUTCOME, not on literal acceptance** | production half fixed by `74fe125` (exit-127 mapping); its test half is unmet AS WRITTEN — see the correction below |
| `bd-ib-d6op2n` | P2 | **duplicate** | owning tenant filed `livespec-driver-claude-tun` 6 days earlier |
| `bd-ib-d6ds` | P1 | partially stale | fleet table drifted — `livespec-overseer` HAS the recipe now, so 3 of 8 lack it, not 4 |
| `bd-ib-xw2k` | P3 | partially stale | its "nothing passes `--journal`" premise is false |
| `bd-ib-d6v1` | P1 | accurate | recipe unchanged on master |
| `bd-ib-6t4` | P1 | accurate | no `fabro validate` in `justfile` or CI |

**4 of 8 fully stale, three of them P1.** ⚠ **The sample was NOT random** — these were
chosen because they sat in the janitor/dispatch area this session was already in and were
cheap to verify. Treat it as "common enough to hit four times in one session", NOT as a
population rate.

**Why it is this epic's business rather than tidiness.** `next` ranks non-closed items and
the dispatch path admits from that ranking, so **a stale item is dispatchable** — an agent
would burn a full cycle finding nothing, or "fix" it a second way. And this is a near-miss,
not a hypothesis: **THIS FILE asked the maintainer to sign an autonomy tier for
`bd-ib-91wj`, whose defect had been fixed two days earlier.** Only checking the merged tree
caught it before the sign-off. A backlog that looks like work and partly is not is exactly
the silent-failure shape `bd-ib-waov` was opened for.

`bd-ib-js1f` records three fix shapes without choosing one, and notes that a mechanical
"is this fixed?" detector is not buildable — deciding it means reading the merged tree
against the item's claim, which is judgment, not a predicate.

##### ⛔ SELF-CORRECTION, same day — A RANDOM SAMPLE FOUND *ZERO* STALE. The finding is NARROWER.

The caveat above was correct, and **caveats do not stop a number from being quoted** — the
4-of-8 figure had already reached a merged PR and this file before anyone tested it. It
has now been tested and it does not generalize.

A seeded random sample (`random.seed(20260728)`, n=10) drawn from the **70** non-closed
items NOT already examined, sharing no members with the original eight, each verdict read
off the merged tree:

| verdict | n | examples |
|---|---|---|
| **confirmed LIVE** | 6 | `bd-ib-2q0` (LLOC is exactly 246 vs a 200 ceiling), `bd-ib-9p4i` (`write_stdout(text=token)` at `mint_app_token.py:52`), `bd-ib-lzau` (`mkdir` at `_dispatcher_janitor_lock.py:38`), `bd-ib-j9x`, `bd-ib-efjsb4`, `bd-ib-98c.4` |
| undetermined by grep | 4 | `bd-ib-4m5f`, `bd-ib-r6o0`, `bd-ib-98c.2`, `bd-ib-98c.6` |
| **STALE** | **0** | — |

**The revised claim, which is more actionable rather than weaker:**

> **Staleness is real, it is CONCENTRATED in areas of recent activity, and it is NOT
> diffuse across the backlog.**

The original eight came entirely from the janitor / dispatch-path area that had just been
worked hard — **which is exactly where fixes land without closing the item that reported
them.** A sweep therefore does not mean "audit 80 items"; it means "when a subsystem has
just been worked hard, re-check the open items naming it". Small job, obvious trigger.
`bd-ib-js1f` has been retitled and corrected accordingly, and its fix shape (A), a
periodic full-backlog sweep, is now poorly justified and should be dropped; **(C) — require
a recorded re-check that the defect still reproduces before an item may be TIERED for
unattended dispatch — is the best-value option**, because it targets the concrete harm at
the one moment that matters and depends on no sweep happening at all.

**What survives untouched:** all four originally-found stale items are still genuinely
stale, each verified against the merged tree; and the near-miss is unchanged and remains
the strongest argument — a stale item being dispatchable costs a full cycle regardless of
base rate, and the base rate is highest exactly where the factory is most active.

**The method lesson, which is the reusable part:** this is the SECOND time in one day this
thread turned an inference from a small biased sample into a general claim — the first was
"filesystem-walking checks are worth a general rule", disproved by measuring 16 of them.
Ten minutes of random sampling halved the scope of a proposed fix. Prefer the measurement
to the caveat.

**✅ SAMPLE COMPLETED — 10 of 10 determined, and the result HOLDS.** The four items left
"undetermined by grep" were resolved: `bd-ib-4m5f` LIVE (`is_dispatch_candidate` still
re-tests `pending-approval` under a ready projection at `_dispatcher_loop_selection.py:138-145`);
`bd-ib-98c.6` LIVE (`event.rs` carries no node-lifecycle spans at the running binary's
commit); **`bd-ib-98c.2` LIVE** (see the correction below); `bd-ib-r6o0` LIVE (none of its
findings are addressed — scenarios.md has no claimless/gauge-(ii) scenario, contracts.md
states no fail-open clause for an unobservable `fabro ps`, and the config-only cap-raise
clause still sits self-labeled "a design constraint on implementations" inside
contracts.md while constraints.md carries no `host_dispatch_cap` material at all).
**Final: 10 live, 0 stale.**

**⛔ AN EARLIER REVISION OF THIS PARAGRAPH NAMED `bd-ib-98c.4` IN THAT LIST INSTEAD OF
`bd-ib-98c.2`, AND THAT WAS A REPORTING ERROR, NOT A TYPO.** `bd-ib-98c.4` belonged to the
already-verified six; it displaced `bd-ib-98c.2` in the write-up, so **`bd-ib-98c.2` was
reported as resolved without ever having been checked.** It has since been checked and IS
live, so the tally never changed — but the claim was unearned when made.

**`bd-ib-98c.2`'s verdict, now that it is real, is more useful than a bare LIVE.** Its
dataset-mapping half is genuinely unimplemented — `honeycomb_dataset_for`
(`_otel_enrich_export.py:53`) is a bare `resource_attrs.get("service.name", …)`
pass-through with no `fabro` reference anywhere in the export path. **But the current
default is not "nothing": a fabro span would land in a dataset literally named `fabro`,
which is neither of the two candidates the item asks an implementer to choose between.**
The deferred decision is therefore already being made by omission, and it takes effect the
moment the emitter is switched on — which per `bd-ib-98c.4` is one server restart away.
Its content-redaction half, by contrast, is **already structurally satisfied**:
`_otel_scrub.py` is a strict fail-closed ALLOWLIST (`is_allowed_attr`, `:148`), so prompts
and tool I/O cannot egress unless someone explicitly allowlists them. What remains there is
the verifying test, not a redaction pass — a much smaller job than the item's wording
implies.

**Three distinct ways this session produced a wrong verification claim, worth reading
together because they fail differently:** (1) **wrong population** — the 4-of-8 staleness
rate from a non-random sample, caught by sampling randomly; (2) **wrong repository** —
three items grepped against the wrong tree, caught only because one of the three failed
visibly while the other two were right by luck; (3) **wrong bookkeeping** — this one, an
item reported as verified that never was, because a near-identical id substituted itself in
the prose. The third is the hardest to catch: the paragraph was internally consistent and
the ids differ by one character. **A verification claim over a LIST must name its items and
be diffed against the original list, never re-derived from memory** — and that is one more
argument for `bd-ib-js1f`'s fix shape (C) recording a per-item verdict as DATA rather than
as a prose summary.

**⚠ A NEAR-MISS THAT SHARPENS FIX SHAPE (C).** `bd-ib-98c.4` was nearly recorded STALE: its
implementation commit `a4bcb3ff2` HAS landed and IS an ancestor of `b9b63a8`, the commit
the host fabro binary runs. On a "did the code land?" test it is done. **It is not done** —
its acceptance is an OBSERVATION ("one dispatch → ≥1 span") and the running fabro server
carries **zero `OTEL_*` env vars**, so the forwarding path is inert by its own commit
message's admission ("with no OTLP env on the server nothing is forwarded"). Two
consequences, both recorded on `bd-ib-js1f`: a staleness re-check must test the
**acceptance**, not search for a plausible fix commit — otherwise it produces false STALE
verdicts on every observation-shaped item, which is the whole O-track; and it must look in
the **right repository**, since the first pass grepped this repo's dispatcher for work that
lives in the fabro fork. That second error is structurally identical to looking for an
item's owner in the wrong tenant, which is how `bd-ib-d6op2n`'s duplicate hid for two days.

#### ⛔ 2026-07-28 — WHY `bd-ib-91wj` REACHED PRODUCTION DESPITE EXISTING MACHINERY. Filed as `bd-ib-3j4u`.

This is the loose end the `bd-ib-91wj` work left, and it turns out to be a separate defect.

**The repo already HAS a gate for exactly that failure.**
`apply_dispatcher_staleness_gate` refuses a run whose plugin build provably predates the
latest release, with the remedy `claude plugin update …`. It landed **`33bf8d5` on
2026-07-24 — four days BEFORE the console session's failure**, and that session's build
(`1567e8f200dc`, release 0.45.18) is exactly the condition it refuses on. So why did it not
fire?

**Because it has exactly ONE call site, and `reconcile-merged` is not on that path.**
`prepare()` (`_dispatcher_loop_selection.py:73`) applies the gate, and `prepare()` is
reached only from `_dispatcher_loop_command.py:268` (`loop`) and
`_dispatcher_run_commands.py:73` (`dispatch`). **`reconcile-merged` has its own preflight**
— `_reconcile_preflight` (`_dispatcher_reconcile_merged.py:102`) — which never applies it,
and imports only `janitor_core_ref` from that module. Of the dispatcher's nine
subcommands, two get a currency verdict.

**`reconcile-merged` is the worst one to leave ungated**, because the janitor argv is baked
into the PLUGIN (`_DEFAULT_JANITOR`) and no repo overrides it — so a stale build runs a
stale janitor, in a venue that mutates the ledger and can strand a claim. Every failing
artifact in `bd-ib-91wj` comes from a `reconcile-merged` run. The session was on a build
the gate would have refused, on the one path that never asks.

Filed as **`bd-ib-3j4u`** (P2, `backlog`, UNTIERED). The fix site is `_reconcile_preflight`
and the journal seam is already there, so it is a call rather than plumbing. **Preserve the
gate's fail-open design** (`bd-ib-n7ce4n`: an unestablishable verdict must warn and proceed,
never block) — a `reconcile-merged` that cannot run is worse than one on an old plugin,
because it IS the recovery path for a stranded claim.

**Raised to P1 on further evidence, and the reason matters.** `bd-ib-n7ce4n`'s close reason
says: *"**THE INTERIM MANUAL REFRESH-AND-VERIFY RULE IS RETIRED — the gate performs it
mechanically.**"* So the HUMAN control was deliberately withdrawn because the MECHANICAL one
was believed to cover it. Confirmed at the doctrine level too: core `livespec`'s
`.ai/dispatcher-drain-operations.md` carries no plugin refresh-and-verify rule (its only
"refresh" material is about the repo working tree). **On the `reconcile-merged` path neither
control exists, and the human one was traded away for a mechanism that never reached it.**
`bd-ib-n7ce4n`'s own problem statement — *"the window is silent — old behavior runs,
pipelines report green"* — is precisely the `bd-ib-91wj` mechanism.

**A control matrix is on the item, and it exists to STOP over-reach.** `reconcile-merged`
applies exactly ONE of six preflight controls (the live-dispatch-lock refusal). **Do not
read that as "wire in the other five."** The admission mutex guards a `ready → active`
race that `reconcile-merged` never runs; the master-CI preflight exists to stop a dispatch
committing on a red master, and wiring it in would let a transient flake
(`bd-ib-wmqsn7`) block the recovery path for a stranded claim — the opposite of what is
wanted. Only the plugin-currency gate is different in kind, because on this path the
plugin version IS the behavior. Scope is confined to this repo:
`livespec-orchestrator-git-jsonl` has neither module.

**Reproduction caveat that will otherwise cost an hour:** the gate is EXEMPT on a
git-checkout plugin root by design (`ad715ea`, "allow unreleased dispatcher plugin
builds"), and with `CLAUDE_PLUGIN_ROOT` unset `plugin_root()` resolves to
`<repo>/.claude-plugin`, which IS a checkout. **This gap cannot be reproduced from a repo
checkout** — it bites only the cache-installed mode, which is exactly where stale builds
accumulate.

#### ⚠ 2026-07-28 — A RECURRING METHOD ERROR: verifying an item in the WRONG REPOSITORY

Three independent instances in one session. Recording it because, unlike the staleness
overreach above, this is measured at three and the failure shape is identical each time:
**the item names an artifact without naming its repo, this repo has a same-named directory
or concern, so the grep answers confidently and from the wrong tree.**

| item | what was grepped | where the artifact actually lives |
|---|---|---|
| `bd-ib-d6op2n` | this tenant's ledger, for an owner | `livespec-driver-claude`'s tenant — filed there 6 days EARLIER |
| `bd-ib-98c.4` | this repo's dispatcher, for OTLP wiring | the fabro fork, `/data/projects/fabro` on `factory-integration` |
| `bd-ib-efjsb4` | this repo's `.ai/` + `SPECIFICATION/` | core `livespec`'s `.ai/dispatcher-drain-operations.md` |

**The uncomfortable part: two of the three produced the RIGHT ANSWER BY LUCK.** `98c.4` and
`efjsb4` are both genuinely live, so the wrong-tree grep happened to agree with the truth.
Only `bd-ib-d6op2n` visibly failed — and it cost a duplicate P2 filed against another
repo's own bug. **A method that is right by coincidence is not verification**, and two of
these would have gone unnoticed if the third had not surfaced the pattern.

**The check is cheap: before verifying an item, establish WHICH REPO owns the artifact it
names.** Cross-repo work in this family is the norm, not the exception — fabro lives in a
fork, doctrine lives in core, sibling defects live in sibling tenants, and every one of
those has a plausible same-named local path to grep instead.

#### ⛔ 2026-07-28 — `bd-ib-tyee`'s "fully stale" verdict was OVERSTATED. Close it on OUTCOME, not acceptance.

The staleness table above originally recorded `bd-ib-tyee` as fully stale on the strength
of one commit. **That checked half its acceptance**, and the half it skipped changes what a
closer should believe.

- **(a) PRODUCTION — definitively done.** `ShellCommandRunner.run` catches
  `FileNotFoundError` (`_dispatcher_io.py:96`) and `_failure_result` (`:191-194`) maps it
  to exit **127**, with a docstring naming the `0jxs` fail-open invariant it restores. That
  is clause (a) verbatim.
- **(b) TESTS — outcome achieved, literal clause NOT met.** Clause (b) asks for the
  dispatcher **integration** tests to be made hermetic *"by injecting a fake runner through
  the EXISTING injectable runner seam, exercising ALL gh paths (success / non-zero 255 /
  absent 127)"*. Measured: **no integration test references exit 127 or "executable not
  found"** — the absent path is unexercised at integration tier (it IS covered at unit
  tier) — and hermeticity was reached by a DIFFERENT technique, a stub `gh` planted on a
  temp PATH (`tests/integration/test_dispatcher_post_merge_janitor_core_provisioning.py:323`).

**Closing is still right, but for a different reason than "it was fixed".** The item states
its own purpose — *"30+ dispatcher integration tests crash in-container … This BLOCKS the
repo's baked-image CI cutover"* — and **that cutover has happened**: CI now runs inside
`ghcr.io/thewoolleyman/livespec-fabro-sandbox:python-v0.57.0` (`container:` in `ci.yml`) and
recent `.py` PRs pass green. The crash it exists to remove does not occur.

**So: close as MOTIVATION DISCHARGED, not as acceptance met.** If clause (b) is wanted
literally, it is a real residual and must be re-filed — nothing at integration tier
exercises 127 today, and assuming otherwise is exactly the mistake this correction fixes.

##### The session's throughline, stated once: CHECKING THAT A FIX LANDED IS NOT CHECKING THE ACCEPTANCE

Four independent instances, all from this one session, all the same shape — a verdict
reached from "is there a plausible fix commit?" instead of "does the stated acceptance
hold?":

| item | what the commit-check said | what the acceptance-check said |
|---|---|---|
| `bd-ib-98c.4` | code landed and is in the running binary → looked STALE | acceptance is an OBSERVATION; server has zero `OTEL_*`, so it is LIVE |
| `bd-ib-tyee` | `74fe125` fixed it → "fully stale", close it | clause (a) met, clause (b) unmet as written |
| `bd-ib-98c.2` | (never checked at all — a list-bookkeeping slip) | LIVE, and its redaction half is already satisfied structurally |
| `bd-ib-91wj` | `14c3cae` fixed it | acceptance genuinely met — red→green measured, both paths share the argv |

Only the last one survived the stricter test unchanged. **Three of four verdicts moved when
the acceptance was read**, and two of those moves would have changed what a maintainer did
with a P1.

This is the strongest available argument for `bd-ib-js1f`'s fix shape **(C)** — require a
recorded re-check against the item's STATED ACCEPTANCE before it may be tiered for
unattended dispatch — and for that record being **per-item data, not a prose summary**,
since a summary is precisely what let `bd-ib-98c.2` go unchecked while reading as verified.

#### ⛔ 2026-07-28 — "the pack fix is MERGED BUT UNRELEASED" was tested and is FALSE

A cross-track hypothesis arrived late in the session: that `14c3cae` is on `master` but no
RELEASED plugin build carries it, so a consumer's `claude plugin update` would not help and
`bd-ib-91wj` should be re-scoped from "author a fix" to a release/propagation gap. It was
tested against `origin/release` before being acted on, **and it does not survive**:

```
14c3cae merged to master    2026-07-26 22:57:06Z
e470f4d "release 0.46.23"   2026-07-26 23:19:45Z   <- FIRST release carrying it (+22 min)
ac1e737 "release 0.46.24"   2026-07-27 00:36:28Z
c878ea4 "release 0.46.25"   2026-07-27 19:05:36Z
4b1339f "release 0.47.0"    2026-07-28 04:56:52Z
c53fd50 "release 0.47.1"    2026-07-28 08:07:32Z
```

`git merge-base --is-ancestor 14c3cae origin/release` → true. At least five releases carry
it, the earliest more than a day BEFORE the reported failure. **So there is no release gap,
`bd-ib-91wj` was NOT re-scoped, and the remedy stands as recorded: a plugin refresh.**

**Where the contrary reading came from, because the error is one this file already
documents.** Two plugin caches were sampled (`6e94b35ec7f3`, `afeefcb40b65`); neither
carries the pack step, and both statements are true. But both builds **predate `14c3cae`**
— they are older releases, not evidence that no release carries it. Sampling two builds
from a ~75-build cache and generalising is the **"wrong population"** error, the same one
that produced this session's 4-of-8 staleness rate.

**TWO POINTS FROM THAT ANALYSIS WERE ADOPTED WHOLESALE, because they are sharper than what
this thread had written**, and both are now on `bd-ib-91wj`:

1. **The two green dispatches are NOT evidence the defect is narrow.** They are evidence
   that **checkout-run and cache-run consumers diverge** — this repo dispatches from the
   orchestrator checkout and gets current code; a consumer runs the flattened plugin cache
   and gets whatever it last installed. That supersedes the "open question" previously
   recorded there.
2. **A consumer can sit on a stale plugin cache indefinitely with NO SIGNAL, and when it
   finally breaks the failure surfaces as a CHECK NAME (`worktree_pack_absent`) pointing at
   the VENUE rather than the VERSION.** That is why two capable sessions both diagnosed the
   venue first — and it is exactly `bd-ib-3j4u`: the gate that would emit the
   version-shaped signal exists and does not run on the `reconcile-merged` path.

**Not ours to carry:** the consumer track is requesting a release, holding its dispatches,
and taking no local janitor override. Do not adopt or chase that.

#### 2026-07-28 — cross-track corrections ran in BOTH directions, and one of them was wrong

Three exchanges with the peer track today, worth recording together because the same move
produced every good outcome and the failures were symmetrical:

| direction | claim | outcome |
|---|---|---|
| us → them | `bd-ib-wmqsn7` flake class is broader than "cpython from GitHub" | ACCEPTED; their recovery recipe corrected |
| them → us | "`bd-ib-91wj` reported every dispatch on this host is blocked" | REFUTED by our journal; scope narrowed |
| them → us | "`14c3cae` is merged but unreleased" | **REFUTED by `origin/release`; item NOT re-scoped** |

**The move that worked every time was the same: treat the other track's claim as a
HYPOTHESIS TO TEST, not a fact to absorb or a challenge to rebut.** Absorbing the last one
would have re-scoped a P2 onto a false premise; rebutting the second without checking would
have left a real consumer blocked.

**The failure shape is also symmetrical, and it is a scope widening.** The peer widened
"every post-merge janitor leg in this repo" into "every dispatch on this host", and a
hold-all-dispatches decision was taken on the widened version. This thread widened
"4 of 8 items in one hot area are stale" toward a general ledger claim, and published it
before sampling randomly. **Neither widening was caught by reading; both were caught by
measuring.**

#### 2026-07-28 — a THIRD instance of the egress flake, contributed to `bd-ib-wmqsn7`

PR #1073 (docs-only) was reddened by `× Failed to download grimp==3.14 … Request failed
after 5 retries … operation timed out` from PyPI. `gh run rerun --failed` cleared it and
the PR merged.

That is a **third distinct artifact** for that item's flake class — cpython/GitHub as
filed, `hypothesis-jsonschema`/PyPI on 2026-07-28, now `grimp`/PyPI — and the newest is a
**transitive** dependency (nothing here names `grimp`; it arrives via `import-linter`). So
a mitigation scoped to declared dependencies would under-fix just as one scoped to the
cpython fetch would: the exposure is the whole resolution closure. Note also that `uv`'s
own retry did not save it — the log says five retries — so more retries at that layer is
not obviously the fix; a job-level re-run is what worked. **Contribution only; the
stand-down on `plan/factory-hardening/`'s items is unchanged.**

### ✅ THE S3 BLOCKER — SETTLED 2026-07-26, and the blocking half has SHIPPED

**S3 was dispatched twice on 2026-07-26 and both runs died in sandbox SETUP**, before
any agent work, leaving the item stranded `active` each time (recovered by hand both
times via `move:bd-ib-pme57n:ready`):

| run id | at | duration | failure |
|---|---|---|---|
| `01KYG0ANS08T5V1HY1A92WR67J` | 20:02:42Z | 11s | `mise install` → 403 |
| `01KYG0FDVJKEDPCRPWQ11NH6CV` | 20:05:17Z | 8s | identical |

```
Setup command failed (exit code 1): livespec-step-timer mise-install --
  sh -c 'mise trust && mise install --quiet'
mise ERROR Failed to install aqua:koalaman/shellcheck@0.11.0: HTTP status client
  error (403 Forbidden) for url
  (https://api.github.com/repos/koalaman/shellcheck/releases/tags/v0.11.0)
```

**ROOT CAUSE — the sandbox's `mise install` was spending the FACTORY'S OWN GitHub
App credit on a third-party public-repo fetch, and that credit ran out.**

`_dispatcher_credentials.py` projects an ephemeral App INSTALLATION token into the
sandbox as `GITHUB_TOKEN`. mise's aqua backend picks that variable up automatically,
so the release-metadata lookup for `koalaman/shellcheck` went out AUTHENTICATED —
charged against the App installation's single **5000/hr PRIMARY** rate-limit bucket,
the same bucket every `gh`, janitor and merge-poll call in the fleet draws on.
Captured from inside the real sandbox image at 2026-07-26T20:27:16Z:

```
HTTP 403
{"message": "API rate limit exceeded for installation ID 131208965. ..."}
x-ratelimit-limit: 5000   x-ratelimit-remaining: 0   x-ratelimit-used: 5000
x-ratelimit-resource: core
```

**In the SAME sandbox, in the SAME second, the ANONYMOUS request for that same URL
returned 200.** That one pairing is the whole proof: identical egress, identical URL,
identical instant — only the credential differs.

**BOTH candidates this thread previously recorded are REFUTED BY EXECUTION.** Neither
was merely unproven; each was tested and failed:

- **Candidate A — "an installation token is unauthorized on a third-party repo."**
  REFUTED. An App installation token returns **200** on that URL, with
  `x-accepted-github-permissions: contents=read` and a 5000/hr limit. Installation
  tokens are not denied public-repo reads.
- **Candidate B — "a GitHub SECONDARY rate limit."** REFUTED. The failure carries the
  PRIMARY limit's headers and message body, not a secondary-limit message.
- The earlier host-side reading of **59/60 anonymous remaining** was accurate and
  simply IRRELEVANT — the failing request was never anonymous, so it drew on a
  different bucket. (A container on this host does share the host's anonymous bucket:
  verified same egress IP `66.94.121.15`, same reset epoch, decrementing counter.)

**SHIPPED: PR #1008, merged `5846ab7`.** The `mise install` prepare step in
`.claude-plugin/.fabro/workflows/implement-work-item/workflow.toml` now scrubs
`GITHUB_TOKEN`, `GH_TOKEN` and `GITHUB_API_TOKEN` from that ONE command's
environment, so aqua tool resolution runs anonymously and no longer consumes factory
credit. Anonymous is the correct posture rather than a workaround: the fetch reads
public release metadata only and touches the anonymous bucket ~2-3 times per
dispatch. Verifier `tests/integration/test_workflow_mise_install_anonymous.py`,
demonstrated RED against the unscrubbed step and GREEN against the scrubbed one; the
mechanism was independently proven in the sandbox image (a deliberately bad
`GITHUB_TOKEN` makes `mise install` fail 401, `env -u GITHUB_TOKEN` in the same shell
installs `shellcheck 0.11.0` cleanly). **Hand-built, not dispatched, deliberately:**
the janitor's `check-no-workflow-edits` hard gate refuses workflow-file drift from
inside a dispatch, so a dispatched agent cannot edit `workflow.toml` at all.

**Proven live:** dispatch `01KYG2Q1028H` of `bd-ib-pme57n` cleared the mise-install
step in 2s (20:44:05Z → 20:44:07Z) and ran on into the workflow, where the two prior
runs had died at that exact step.

**STILL OPEN on `bd-ib-bic7hb`: the durable prevention.** Pre-bake `shellcheck` and
every other aqua-backed tool so setup makes NO api.github.com call at all. **Correct
the target while you are there:** it is NOT `orchestrator-image/` as the item
originally said — the dispatch sandbox pins
`ghcr.io/thewoolleyman/livespec-fabro-sandbox:python-agent-v0.54.19`, the FAMILY
image built in `livespec-dev-tooling`. So pre-baking is a CROSS-REPO change plus a
pin bump here, gated on `bd-ib-dwv` (image un-rebuildable) AND on `bd-ib-u46hcv`
(the pin is frozen at v0.54.19; see §"The v0.54.19 pin hold").

**A SEPARATE, LARGER FINDING falls out of this and belongs to nobody yet.** The App
installation's 5000/hr bucket reaching ZERO is a fleet-level problem. While it is
empty, EVERY credentialed GitHub call the factory makes fails the same way — `gh pr
create` in the pr node, the merge poll, the janitor. The sandbox `mise install` was
merely the first consumer to surface it. Nothing here measures what burns 5000
requests/hour against installation 131208965; a sample at 20:28:24Z showed a healthy
bucket (10 used), so the burn is BURSTY rather than steady. Recorded in
`bd-ib-bic7hb` under §"SEPARATE FINDING"; it is not part of this epic.

**S3's red is already captured** in `bd-ib-pme57n`'s description — executed against
the real `admit_and_select` with `wip_cap: 1`: a dead claim consumed the only slot,
`admitted=[]`, and no abandonment was journaled. The next session does not need to
re-derive it. **S3's predicate is the AMENDED one**, not "active + no live lock" —
see §"Rework doors".

Both slices were `pending-approval` and both dispatched directly with NO approval
step — see §"Dispatching a `pending-approval` slice"; the approve valve is closed by
construction on this repo.

### The v0.54.19 pin hold — LIFTED 2026-07-27. Not ours any more; one thing is UNVERIFIED.

**Status changed while this thread was mid-session, so read the dates, not the
prose you may remember.** `bd-ib-u46hcv` was **CLOSED 2026-07-27T00:22:55Z** — with
**no recorded close reason and no resolution** — and the pin then moved off v0.54.19
in five bumps between 06:01:53Z and 09:55:22Z: `v0.55.0` (`e45527d`), `v0.55.1`
(`9e630e1`), `v0.56.0` (`15f1281`), `v0.56.1` (`b8c8121`), `v0.56.2` (`6b2e0c9`).
The sandbox image pin moved with it — `workflow.toml` now pins
`ghcr.io/thewoolleyman/livespec-fabro-sandbox:python-agent-v0.56.2`. Both hold
guards are gone from `pin-freshness.yml` and `bump-pin-from-dispatch.yml`.

The ordering is coherent — item closed FIRST, then the bumps flowed — so this reads
as deliberate discharge by the owning item, **not** unattended drift. This thread's
pin-hold obligation is therefore DISCHARGED and is no longer ours to defend. Do not
try to re-impose the hold.

**What was held at v0.54.19 and why** (retained so a successor can judge the risk):
v0.54.20..v0.54.24 took the factory DOWN because
`primary_checkout_commit_refuse_hook_installed` asserts the presence of the
gitignored worktree pack, which cannot exist in a fresh clone — and the sandbox runs
that check as a SETUP command on a fresh clone. The gate-blindness that let it merge
green: `just check` runs on the BOOTSTRAPPED checkout, where the broken check passes.

**⚠ ONE THING IS UNVERIFIED, and it is the condition this section used to state.**
The rule was "do NOT move the pin until a REAL dispatch is proven to survive setup
on the new pin — a green `just check` is not that proof." **That proof does not
exist for v0.56.2 — nor for v0.56.3, which the pin reached later the same day
(`60abb97`), making SIX bumps with no dispatch between them.** The dispatch
journal's last record is `2026-07-27T00:39:28Z`,
before the first bump at 06:01:53Z, so **no dispatch has run on any pin after
v0.54.19.** S3's dispatch (`01KYG2Q1028H`) is not the proof either — it ran at
`5846ab7`, where the pin was still v0.54.19 (verified by reading that commit's
`pyproject.toml`).

**⛔ THE STANDING ASSUMPTION, and it is NOT a blocker — maintainer ruling
2026-07-27.** Do not treat the missing proof as blocking, and do not stall a dispatch
over it. Carry this assumption instead, stated so a successor inherits it explicitly
rather than rediscovering it:

> **The current pin is PRESUMED SOUND until the next real dispatch tests it, and THE
> NEXT DISPATCH IS THE TEST.**

So whoever runs the next dispatch should know in advance: **a setup failure is the
EXPECTED FIRST SUSPECT, not a mystery.** If it dies in setup — particularly on
`primary_checkout_commit_refuse_hook_installed` — check the pin before re-deriving
anything. The failing shape to look for is the one v0.54.20..v0.54.24 produced: the
check asserts the gitignored worktree pack, which cannot exist in the sandbox's fresh
clone.

**⚠ That first-suspect guidance is now SUPERSEDED for the setup leg — read
§"SETUP IS NOW VERIFIED" below before acting on it.** Setup was measured directly on
v0.56.3 and passes, so a setup failure is no longer the expected first suspect; the
janitor and pr stages are. The assumption itself still stands for everything past
setup. (This paragraph is kept rather than deleted because it states the failing
shape, which is still what to look for IF setup ever does fail.)

**Record the shape of the closure, not just the fact of it.** `bd-ib-u46hcv` was
closed with **NO close reason and NO resolution recorded**. The maintainer released
the hold deliberately, so **do NOT reopen it** — but that empty closure carries no
evidence, and it MUST NOT be read as proof that the dispatch condition was ever met.
A closed item is a decision; it is not a verification. The two are being distinguished
here precisely because this thread has twice been burned by reading a filed record as
a measurement.

**Evidence pointing the other way, recorded fairly.** On v0.56.2, `just check`'s
`fresh-clone-setup-gate` PASSES in a fresh worktree, and that gate exercises the four
sandbox setup steps including the offending check, reporting "every conformance setup
step passes on a fresh clone". That is materially stronger than the bootstrapped-`just
check` blindness that let v0.54.24 through — but it is still a gate, not a dispatch,
and this section's own standard says a gate is not the proof. Treat it as good reason
to expect success, not as the verification.

#### ✅ SETUP IS NOW VERIFIED ON v0.56.3 — measured 2026-07-27T20:59Z, at zero risk

**The pin moved again while this was being written** — SIX bumps total, now
`livespec-dev-tooling` **v0.56.3** (`60abb97`) and sandbox image
`ghcr.io/thewoolleyman/livespec-fabro-sandbox:python-agent-v0.56.3` — and the journal
still showed **ZERO dispatch records after the first bump**. So rather than wait for a
real dispatch to discover the answer expensively, the setup leg was tested directly.

**Method — a NON-ADMITTING probe, and the technique is reusable.** A bare
`fabro run` (run `01KYJNZX4GQMQ7R583GPFBJCCY`), NOT `dispatcher.py dispatch`: the probe
workflow pins the SAME image as `workflow.toml` and carries the **eight real
`[[run.prepare.steps]]` script lines extracted verbatim** from `workflow.toml`, with a
trivial confirm node in place of the agent graph. Because nothing is admitted, no
work-item can strand — which is precisely the cost that made the earlier blind retries
of `bd-ib-pme57n` unacceptable. **Use this shape whenever the question is "does sandbox
setup survive X"; it answers in ~15s and risks nothing.**

**Result: all 8 setup commands completed in 13s, and the run SUCCEEDED.**

```
Sandbox: pulling ghcr.io/thewoolleyman/livespec-fabro-sandbox:python-agent-v0.56.3...
Setup: 8 commands (12s)
```

The two things that most needed proving, both confirmed from the node's own output:

- **`verify-commit-refuse-hook` — the EXACT check that took the factory down on
  v0.54.20..v0.54.24 — completed**, and re-running
  `livespec_dev_tooling.checks.primary_checkout_commit_refuse_hook_installed` inside
  the sandbox printed `COMMIT-REFUSE-CHECK-OK`. The fresh-clone worktree-pack failure
  mode does NOT reproduce on v0.56.3.
- **`shellcheck 0.11.0` installed via the anonymous mise path** (`mise-install` step,
  2s), so PR #1008's credential scrub works on the new image too.

**⚠ WHAT THIS DOES *NOT* PROVE — do not overclaim it.** This is a real fabro sandbox
running a real fresh clone through the real setup, which is strictly stronger than the
host-side `fresh-clone-setup-gate`. But it is **not a dispatch**: no ledger admission,
no agent nodes, no janitor `just check`, no pr node, no post-merge path. So:

- The **setup-failure** risk this section was written about is **DISCHARGED** for
  v0.56.3. A dispatch dying in setup is no longer the expected first suspect.
- The **rest of the dispatch path on the new pin remains untested.** If the next
  dispatch fails, look at the janitor and pr stages rather than at setup — the
  `just check` aggregate runs a much larger surface of v0.56.3 than setup does.

The standing assumption above is therefore NARROWED, not retired: v0.56.3 is
**verified through setup** and presumed sound beyond it.

(Corroborating the defect class is still live somewhere: this session hit
`failure_mode: "worktree_pack_absent"` from that exact check in a fresh worktree on
v0.56.2 — it passes only after `just bootstrap` materializes the gitignored pack.
The fresh-clone gate bootstraps, which is why the gate is green.)

#### ✅✅ ASSUMPTION FULLY DISCHARGED 2026-07-28 — the whole path is proven, on v0.56.6

**Do not carry the standing assumption forward; it has been paid off by execution.**
Two real dispatches ran END-TO-END and both merged green, on sandbox image
`ghcr.io/thewoolleyman/livespec-fabro-sandbox:python-agent-v0.56.6` — three bumps past
the v0.56.3 the section above was written about:

| item | run | outcome |
|---|---|---|
| `bd-ib-ktxb` | `01KYK27X1QTE` | PR #1048 / `521d7f71` — merged, post-merge janitor green |
| `bd-ib-3lmt` | `01KYK3V3T04F` | PR #1050 / `599e3df` — merged, post-merge janitor green |

That covers every stage the probe could not: setup (18 commands, 25s), the agent nodes,
the janitor's `just check` aggregate, the pr node, auto-merge, and the post-merge
janitor. The `just check` leg is the important one — it exercises a far larger surface
of the dev-tooling pin than setup does, and it was the specific residual risk this
section named. **Suspecting the janitor and pr stages first is now WRONG advice; they
are proven.**

**⚠ WHAT ACTUALLY BIT INSTEAD, and it is the thing to suspect now.** `bd-ib-ktxb`'s
FIRST dispatch attempt died at 7 minutes without doing any work:

```
✗ Implement (Red-Green-Replay)
Error: required Red commit for bd-ib-ktxb is blocked by pre-existing
       external gate check-master-ci-green: latest master CI i...
```

Master CI was red — on a DOCS-ONLY commit, because `uv` timed out fetching
`hypothesis-jsonschema==0.23.1` from PyPI after 5 retries. A markdown-only change cannot
cause a PyPI timeout. Re-running master CI passed in 55s, and the re-dispatch went green.

**So the current first suspect for a dispatch that dies early is `check-master-ci-green`
fail-closing on a transient master-CI flake — which is exactly `bd-ib-wmqsn7` in
`plan/factory-hardening/`.** That filed item just cost a real dispatch cycle, and the
evidence is now attached to it.

> # ⛔ STAND DOWN — `bd-ib-wmqsn7` AND `bd-ib-bwgko4` ARE NOT OURS (2026-07-28)
>
> **Owned by `plan/factory-hardening/`, which is ACTIVELY RUNNING IN ITS OWN SESSION
> with its own supervisor** (both confirmed live in tmux: `factory-hardening` and
> `factory-hardening-supervisor`). **Do not tier them, do not dispatch them, do not
> adopt them, and do not treat either as awaiting our action or awaiting a maintainer
> tiering routed through us.** The maintainer was asked to tier them and the answer was
> NEITHER — they have an active owner.
>
> Earlier revisions of this file said `bd-ib-wmqsn7` was "still BLOCKED on
> autonomy-tiering" and titled it "tolerate a transient/re-runnable master CI flake".
> Both are stale. As of `cd69f3e` that session promoted it to an **EPIC** and re-scoped
> it to *"a red master CI run hard-gates every factory dispatch — move the master-health
> read to a vantage that can act on it (host-side pre-dispatch precondition + `ghs_`
> out-of-vantage in-sandbox)"*, and **CLOSED `bd-ib-bwgko4`**.
>
> **Our field evidence on `bd-ib-wmqsn7` STAYS — do not retract it.** It was a
> contribution to their item, not an adoption of it, and it is load-bearing: the flake
> class is BROADER than the "cpython from GitHub" their description names (ours was a
> different package from a different host), which is the difference between a fix that
> works and one that under-fixes; and `gh run rerun --failed` SUCCEEDED for us where the
> item records it being refused, which corrects their recovery recipe. Their notes grew
> from ~3.5 KB to ~10.5 KB, so it was read and built on.
>
> **The standing never-touch-another-session's-work clause now explicitly covers
> everything `plan/factory-hardening/` is working on**, and separately the console
> track's PRESERVED janitor checkout at
> `~/.worktrees/livespec-console-beads-fabro/janitor-reconcile-...-dm5f7q` (kept
> deliberately as evidence — see `bd-ib-91wj`).

**Two independent egress flakes inside one hour** (shellcheck from GitHub releases
during a CI job; `hypothesis-jsonschema` from PyPI) suggest host network flakiness is a
live background condition. The shellcheck one is the same fragility class
`bd-ib-bic7hb`'s open half would remove by pre-baking — different failure (connection
reset, not a 403), same cure.

**A second, separate assignment is also open: a `/livespec:revise` pass over BOTH
pending proposals — `reconcile-merged-dispatch-lock.md` and
`rework-return-door-attribution.md` — belongs to this track**
(maintainer-assigned 2026-07-26, scope corrected twice the same day). No deadline.
Every pending proposal is now ours; the peer's was ratified as v050. **The pass is
BLOCKED** on a local `spec/*` branch owned by another session — see §"The revise
pass", and check the precondition at run time, never earlier.

The lock work, both halves verified by executing the real product code, not by
reading a green dispatcher summary:

- **S1 `bd-ib-ohdu5a`** — PR #978 / `a869253`. Consults `started_at_epoch`, so a
  recycled PID no longer reads as the original owner; and claims with `O_EXCL`.
- **`bd-ib-l2vglr`** — PR #982 / `acf061c`, merged 2026-07-26T10:19:41Z. S1's
  `O_EXCL` had landed WITHOUT the stale reclamation that makes exclusive claiming
  safe, so any lock leaked by a dispatch that died without its `ExitStack`
  permanently blocked re-dispatch of that work-item. `write_dispatch_lock` now
  wraps the open in `attempt(...)`, and on `FileExistsError` runs
  `_stale_dispatch_lock_reclaimed`: an `fcntl.flock` mutex on a sibling `.reclaim`
  file, the S1 PID+start-time liveness verdict, **and a re-read of the payload
  compared against the first read immediately before unlinking** — the TOCTOU
  guard `bd-ib-w4h4` was filed about. Verified 2026-07-26 against the merged tree:
  a dead-pid lock is RECLAIMED and re-stamped with the new caller's pid, while a
  lock whose holder is LIVE is still REFUSED rather than clobbered.

**The live leaked locks need no hand removal.** `tmp/fabro-dispatch-bd-ib-fe574e.lock`
(pid 930374) and `…-bd-ib-fjj7f7.lock` (pid 580668) are still on disk with dead
pids. Verified 2026-07-26 by running the merged `write_dispatch_lock` against
COPIES of both real payloads: each is reclaimed automatically, so `bd-ib-fe574e`
and `bd-ib-fjj7f7` are dispatchable again. Leave the originals alone — they are
now inert, and they are this regression's field evidence.

**RE-CHECKED 2026-07-28 — the count and the consequence both moved:**

- **There are now THREE, not two.** A new one appeared:
  `tmp/fabro-dispatch-bd-ib-hvuhxp.lock` (pid 2421000, dead). So dispatches still
  LEAK locks; what `bd-ib-l2vglr` fixed is that a leaked lock is now harmless, not
  that leaking stopped. That was the deliberate design — the S1 brief forbade
  cleanup — so this is the intended steady state, not a new defect.
- **The "dispatchable again" consequence is MOOT for both named items.**
  `bd-ib-fe574e` and `bd-ib-fjj7f7` are both CLOSED now, so nothing waits on their
  reclamation.
- **The reclamation path was demonstrated IN PRODUCTION today, not just against
  copies.** `bd-ib-ktxb`'s attempt 1 died mid-flight at the Implement node, which is
  exactly the shape that leaks a lock — and after attempt 2 ran green, **no
  `…-bd-ib-ktxb.lock` remains on disk at all.** That is consistent with attempt 2
  reclaiming attempt 1's stale lock via `write_dispatch_lock`'s `FileExistsError`
  path, which is precisely the mechanism `bd-ib-l2vglr` shipped. (Stated as
  consistent-with rather than proven: no artifact records the reclaim directly.)

**Normal completion DOES clean up.** Both of today's green dispatches
(`bd-ib-ktxb`, `bd-ib-3lmt`) left no lock behind, so the three on disk are all from
runs that died without unwinding their `ExitStack` — which is what makes them field
evidence rather than clutter.

**Own this honestly:** the regression traced to THIS THREAD's own brief on
`bd-ib-ohdu5a`, which told the implementer "DO NOT add cleanup for leaked lock
files — liveness is PID-keyed, so a lock whose owner is gone already reads dead."
True before `O_EXCL`, false after it. The implementer followed the brief
correctly. The lesson generalizes: a brief's standing prohibitions must be
re-checked against every scope addition made after it was written.

Dependency layering, verified on the ledger: `bd-ib-cfgkkk` 1 dep / 1 dependent;
`bd-ib-pme57n` 2 / 0. `bd-ib-l2vglr` and `bd-ib-hvuhxp` carry no edges.

**S2's `bd-ib-81l0` gate is DISCHARGED.** It shipped 2026-07-26 as PR #1000
(`47c75ac`): `reconcile_plan` now threads `resolve_fabro_bin(cwd=repo)` instead of
the bare literal, so S2's `reconcile-merged` handoff no longer exec-fails under the
credential wrapper. Verified by re-executing the red against the merged tree —
`plan.fabro_bin` is now `/home/ubuntu/.fabro/bin/fabro` and execs at exit 0, where
the bare name raised `FileNotFoundError`. (The gate could never be an edge — groom
resolves `depends_on` handles only to earlier slices in the same draft — so it
lived in `bd-ib-cfgkkk`'s description as prose.)

## ⛔ Dispatching a `pending-approval` slice — the obvious answer is WRONG

Both remaining slices sit in `pending-approval`, and the intuitive move — "run the
approve valve first" — **cannot work on this repo and would block the track
indefinitely.**

`.livespec.jsonc:93` commits `auto_approve_ready: true`, so
`effective_admission_policy` resolves to `auto`, and `_approve_item`
(`_drive_valves.py:141-152`) refuses EVERY item here with `invalid-source-state —
approve requires an effective-manual pending-approval item`. **The approve valve is
closed by construction.** Another session hit exactly this on `bd-ib-wuotqm` on
2026-07-26 and had to route around it.

**⛔ That defect is NOT OURS — `plan/valve-advertisement-mismatch/` owns it**
(opened 2026-07-26). Its `research/prior-work-and-collisions.md` carries an
"Already filed — do NOT duplicate" section and names THIS thread explicitly in its
"Other live tracks — checked, no collision" section, so the cross-check has already
been done from their side. **Do not file against it, do not fix it in passing, and
do not fold it into this epic.** For us it is a standing WORKAROUND note only: the
approve valve is closed here, so dispatch `pending-approval` items directly, per
the rest of this section.

**What actually works: dispatch it directly. No approval step, no status move.**
`ready_items` (`_dispatcher_loop_selection.py:102-120`) filters with
`is_dispatch_candidate`, which re-tests a `pending-approval` item under a READY
PROJECTION (`:138-145`). The `--item` preflight
(`_dispatcher_run_checks.requested_items_preflight_error`) checks membership in
that same set, so it passes. Admission then does both writes in ONE pass:
`_dispatcher_admission.py:102` writes `ready` on the auto-approve leg, `:114` writes
`active`.

Verified 2026-07-26 by executing the real predicates against the live tenant:

```
bd-ib-cfgkkk: status='pending-approval' depends_on=(bd-ib-ohdu5a,)
  is_dispatch_candidate                          -> True
  in ready_items set                             -> True
  requested_items_preflight_error({'bd-ib-cfgkkk'}) -> None
```

So `dispatcher.py dispatch --item bd-ib-cfgkkk` just works.

**Do NOT reach for `dispatcher.py loop` to obtain the auto-approve.** A loop pass
admits a BATCH to `active` and then dispatches under `--parallel 1`, which is
exactly the unlocked-claim window S3 exists to close — and S3 has not shipped.
Per-item `dispatch --item` writes its lock at `dispatch_one` entry, so each claim is
covered for its whole life. Per-item dispatch is the rule until S3 lands.

**`move:<id>:ready` is a working fallback if the direct path ever regresses**, and
it is CLEAN for a `pending-approval` item in a way it is not for an `active` one: the
item has never been `active`, so `assignee` is already `None` and the
`bd-ib-5ymv5p` stale-assignee side effect cannot arise. v050 retires the
move-into-`active` door, NOT move-into-`ready`, so this stays sanctioned.

**Hazard recorded on `bd-ib-4m5f`.** That item reports `next` and the Dispatcher
disagreeing on the candidate set — and the divergence is what makes the above work.
Resolving it by narrowing the Dispatcher to `next`'s stored-status-only reading
would make every `pending-approval` item undispatchable here, with no approval valve
to unblock it. Converge by teaching `next` the ready-projection rule, not by
narrowing the drain.

**Dispatch recipe that worked** (run it from the repo root, already inside the
wrapper — the dispatcher self-wraps but often cannot reach the credstore alone):

```bash
/usr/local/bin/with-livespec-env.sh -- python3 .claude-plugin/scripts/bin/dispatcher.py \
    dispatch --item <id> --repo /data/projects/livespec-orchestrator-beads-fabro
```

Verify preconditions FIRST every time: the `127.0.0.1:32276` listener's
`/proc/<pid>/exe` must resolve to `~/.fabro/bin/fabro`; `fabro --version` must be
`0.254.0 (b9b63a8)` (≥ 0.256 breaks `workflow.fabro`, exit 127 — halt); WIP
headroom. Prove container ownership by an ALL-container run-config scan, never by
name/image/position/timing — every container on this host exits 137, so 137 is
normal teardown here, never kill-proof. Establish outcomes from artifacts (merged
PR, ledger row, journal), never exit codes: both S1's and `bd-ib-l2vglr`'s
dispatchers printed a green summary, and only re-executing the reds proved either
fix was real.

**`fabro ps` need NOT be clear — do not treat a foreign run as a blocker.**
`bd-ib-sd8o` closed 2026-07-24 `resolution:completed`: `host_dispatch_cap`
(default 2, spec v047) demoted the interim host-wide dispatch mutex to a counting
cap, verified live with two concurrent green dispatches. One foreign run is
therefore normal and safe; a THIRD dispatch is what gets refused. When a foreign
run IS present, identify its owner by the dispatcher **argv chain**
(`ps -eo pid,ppid,args` → the `dispatch --item <id>` leaf and the
`CODEX_COMPANION_SESSION_ID` in its launching shell), and name the owning SESSION,
recovered from `~/.claude/projects/<slug>/<session-id>.jsonl` by grepping
`Session renamed to:`. Demonstrated 2026-07-26: while this thread dispatched
`bd-ib-l2vglr`, session **`orch-dirty`** (session
`87f62319-9bda-4b9e-80b0-d35b178bef70`) concurrently dispatched `bd-ib-cfcmse`;
both ran green.

**The root cause below was CORRECTED on 2026-07-26** against the dispatch journal,
the merged PR, and the ledger. The thread's original diagnosis ("the dispatcher
process died mid-flight") is DISPROVEN — see §"Root cause". The epic's own
description was corrected to match before it was closed, so the two no longer
disagree.

**Leave `bd-ib-w4h4` stranded.** It is S3's fixture. Do not un-strand or close it
before the verifier exists. It becomes recoverable once `bd-ib-rxxx` lands.

## ⚠ Rework doors — S3's predicate is NARROWER than "active + no live lock"

**Found 2026-07-26 by the peer supervisor `console-happy-path-mvp-supervisor`,
verified here, and APPROVED as a change to S3's already-approved acceptance
criteria. `bd-ib-pme57n`'s description now carries the amendment; this section is
the reasoning behind it.**

TWO writers set `status="active"` **without passing through admission**, so they
never hold a dispatch lock. Neither is an abandonment — each parks an item for
re-dispatch:

1. **`_drive_valves.py:189`** (`_reject_item`) — `reject:<id>:rework` on an
   `acceptance` item sets `target_status = "active"`. **NOT journaled at all.**
   `valve_success` (`_drive_valve_result.py:29`) builds a `"journal"` object
   INSIDE the drive CLI's RESPONSE payload; neither drive module nor `drive.py`
   references a `JournalFile`, and the dispatch journal holds **zero
   `human-valve-*` records** across its whole history. (A peer brief described
   this door as "journaled `human-valve-reject-rework`" — that is the response
   field, not a journal record.)
2. **`_dispatcher_acceptance_rework.py:79`** — auto-rework after a failing AI
   acceptance pass, genuinely journaled `acceptance-auto-rework`. **Reachable in
   practice:** fired 4 times across 3 distinct items (`bd-ib-vp3pwe` ×2,
   `bd-ib-1jye.4`, `bd-ib-1jye.5`).

A **third** unlocked writer exists today: the bare `move:<id>:active`, legal
because `_MOVE_ALLOWED` (`_drive_policy_valves.py:40`) contains `"active"` and
`move_item` guards only the TARGET status. It is unjournaled too. The pending
`per-state-verb-vocabulary.md` proposal removes exactly that door.

**The obvious discriminator does not work.** "Also require a terminal `outcome`
journal record" fails, because the auto-rework park writes its terminal `outcome`
AFTER the rework write and it is **green** — e.g. for `bd-ib-1jye.4`:
`{"stage": "done", "status": "green", "pr_number": 800, "detail": "merged,
post-merge janitor green"}`. An abandoned claim and a rework park both have one.

**APPROVED PREDICATE** — reclaim (exclude from `active_count`, journal the
abandonment) if and only if:

```
    item.status == "active"
AND live_dispatch_lock(item) is None
AND (the most recent terminal `outcome` for the item is non-green
     OR no `outcome` record exists since its most recent `ledger-admit`)
```

| case | last outcome | verdict |
|---|---|---|
| `bd-ib-w4h4` (janitor-post-merge red) | `failed` | RECLAIM |
| `acceptance-auto-rework` park | `green` | skip |
| `reject:<id>:rework` park | `green` (it reached `acceptance` only via a green `ledger-complete`) | skip |
| dispatch SIGKILLed mid-run | none since `ledger-admit` | RECLAIM |
| queued in an admitted batch | — holds an admission-time lock | skip before the outcome leg is reached |

The last row is why this is sound ONLY together with S3's admission-time lock
move. Without it, a queued item has neither lock nor outcome and would be
reclaimed while perfectly healthy.

**KNOWN RESIDUAL, accepted at approval — now DISCHARGED at the spec level.** A
bare `move:<id>:active` item has no lock and no outcome since its (nonexistent)
admit, so it reads as abandoned. That door was retired by v050 (`27980bb`), and
the shipped-code divergence — `_MOVE_ALLOWED` still contains `"active"` — is filed
as **`bd-ib-2wgooj`**. `bd-ib-pme57n`'s description carries the same cross-
reference. Prose link only; no dependency edge is asserted, because S3's
predicate is correct either way and merely reads a bare-moved item as abandoned
until `bd-ib-2wgooj` lands.

## The revise pass — TWO files, BOTH ours

**Maintainer-assigned 2026-07-26; scope corrected twice the same day — read the
current table, not the earlier "ONLY that file" framing this section used to
carry.** No deadline; run it when the slices make it sensible. **Do not run it
while a dispatch is in flight** — it authors spec text and cuts a `spec/*` branch,
which should not race a live janitor.

`SPECIFICATION/proposed_changes/` on `origin/master` holds exactly two files, and
**both are ours**:

| proposal | filed | this track's obligation |
|---|---|---|
| `reconcile-merged-dispatch-lock.md` | 2026-07-19 (`e957b35`) | Process it. Pending since filing, untouched by any other track. |
| `rework-return-door-attribution.md` | 2026-07-26 (PR #996, `e7c0651`) | Process it. Two separable findings; see §"Rework doors" and the v050 correction below. |

#### ⚠ Ratification ORDERING against `plan/valve-advertisement-mismatch/` — SETTLED, do not re-litigate

`rework-return-door-attribution.md` is pending against the **same
`SPECIFICATION/contracts.md` §"Door rules" block** that any amendment out of the
`valve-advertisement-mismatch` thread must also touch. That thread records the
clash as its "Live collision #2" and asks whoever files theirs to check whether
ours has landed.

**DECISION: OURS RATIFIES FIRST.** Ours is already filed and is narrow — it
corrects a single false justification sentence — so ratifying it leaves a
*corrected* paragraph for their broader amendment to build on. The reverse order
would have them amend text we are about to correct, and the correction would then
have to be re-derived against their new wording. This ordering is recorded so it
is not re-decided; it is worth relaying to that thread, but **do not edit their
files to say so** — surface it to the maintainer for relay.

The peer's `per-state-verb-vocabulary.md` is **GONE** — ratified as v050 in
`27980bb` — and `wip-cap-zero-dispatch-off.md` before it as v049 in `9941317`.
**Consequence: the all-or-nothing property now costs us nothing.** Every pending
proposal is ours, so no coordination with another track is required and no
proposal has to be carved out of the payload. Earlier revisions of this section
recorded a cross-track split; that split no longer exists.

**A revise pass is NOT all-or-nothing anyway** — an early relay said it was, and
that was retracted. The revise PROSE says process every in-flight file, but the
CLI's `--revise-json` payload defines actual scope through its `decisions[]`
array. Verified independently on the forge 2026-07-26, and the timing is
decisive:

- `SPECIFICATION/history/v049/proposed_changes/` contains ONLY
  `wip-cap-zero-dispatch-off.md` and `wip-cap-zero-dispatch-off-revision.md`.
- v049 was ratified at 2026-07-26T09:13:02Z (`9941317`).
- `per-state-verb-vocabulary.md` was added at **08:46:07Z** (`495b903`) — 27
  minutes BEFORE v049 was cut — and `reconcile-merged-dispatch-lock.md` on
  2026-07-19 (`e957b35`), seven days before.

Both therefore sat pending while v049 snapshotted and ratified a single proposal,
and neither received a `-revision.md`. A single-proposal pass is mechanically
supported and was demonstrated today.

### ⛔ The blocking precondition — check it IMMEDIATELY BEFORE the run

Step 3.5 halts on any local `refs/heads/spec/*` ahead of `origin/master`.

**This check is binding at run time, not at session start.** It was verified
EMPTY twice on 2026-07-26 and was non-empty again within the hour on both
occasions. Two demonstrations, both real:

1. `refs/heads/spec/ratify-verb-vocabulary` — the peer track's v050 pass, which
   blocked this pass for most of 2026-07-26. **RESOLVED 2026-07-26: removed on
   maintainer authorization** (branch was `30ffe29`, plus its worktree at
   `~/.worktrees/livespec-orchestrator-beads-fabro/spec-ratify-verb-vocabulary`).
   Checked to destruction first: `git diff origin/master 30ffe29 -- SPECIFICATION/`
   showed the branch carried NOTHING under `SPECIFICATION/` that master lacks —
   the whole v050 ratification is on master via PR #995 / `27980bb` — the worktree
   was clean and no process held it. It was the pre-rebase twin of a merged commit.
   `console-happy-path-mvp-supervisor` was notified after the fact.

   **CORRECTION, recorded because this thread relayed it wrong.** Earlier revisions
   of this file said the branch "is owned by session
   `console-happy-path-mvp-supervisor`; do not remove it ourselves". That
   attribution originated here, was relayed onward unverified, and was wrong: their
   pass CREATED it, but what remained was a **local ref in OUR clone with no unique
   content** — our housekeeping, not theirs. The standing
   never-touch-another-session's-worktree clause is UNCHANGED for everything else;
   the exemption here is narrow and was earned by proving the ref carried nothing.
   The general lesson is this thread's own recurring one: an ownership claim is a
   claim with a timestamp, and "another session owns it" needs the same evidence
   standard as any other assertion before it is allowed to block work.
2. This thread's OWN propose-change cut and deleted `spec/rework-return-door-attribution`
   inside a single turn. Filing a proposal is itself a way to trip the gate.

So: `git for-each-ref refs/heads/spec/` MUST be empty at the moment of the run.
An earlier-in-session verification proves nothing — **including the 2026-07-26
removal recorded above.**

**And do not run the pass while a dispatch is in flight** (already stated above,
repeated here because this is where a successor will be standing): the pass
authors spec text and cuts a `spec/*` branch, which must not race a live janitor.
On 2026-07-26 the precondition came clear WHILE S3's dispatch was running, and the
correct answer was still to wait for the dispatch, not to start the pass.

**Likely outcome for `reconcile-merged-dispatch-lock.md`: accept as written, no
amendment.** The original spec clash is recorded DISSOLVED (§"CORRECTED") — the
approved design leaves the item `active` and narrows the count, so the proposal's
"a red janitor … MUST leave the item `active`" is honored literally.

**But re-read before accepting: v050 landed AFTER that analysis and changed the
door rules around `active`.** The DISSOLVED reading was derived pre-v050. Verify
it against BOTH the proposal's current bytes and the ratified v050 text in
`SPECIFICATION/contracts.md` rather than trusting the earlier conclusion. Expect
a short pass, but do not assume one.

### A driver defect that can misfire this very pass

`bd-ib-d6op2n` (P2, `ready`, host-only): every `livespec-driver-claude` binding —
all eight, `revise` included — ships a core-resolution snippet that tests the
prose DIRECTORY (`-d "./.claude-plugin/prose"`) while its own documented rule 2
tests that operation's prose FILE. This repo HAS a `.claude-plugin/prose/` (six
orchestrator prose files, none of them spec-side), so the snippet resolves
`<core-root>` to THIS repo and the not-found guard — which re-tests the directory
— passes it through silently.

**Workaround, already used successfully:** apply the documented rule-2 condition
(test for `prose/revise.md` specifically), or resolve rule 3 directly from
`~/.claude/plugins/installed_plugins.json`. Do not trust the shipped snippet.

### The peer's proposal contradicts itself — HANDED BACK, not our blocker

**Ruling 2026-07-26: hand back for amendment; delivered.** This is recorded for
the peer's benefit and for provenance. It is **NOT a gate on our pass**, because
`per-state-verb-vocabulary.md` is out of our scope entirely. Do not wait on it and
do not edit the peer's proposal — it is a completed maintainer decision owned by
another track.

The proposal's door rule (line ~66) states:

> "`active` is entered ONLY by a journaled dispatch: **factory dispatch** … or
> **driver-dispatch**. Bare operator moves into `active` are removed from every
> lane."

Its own lane table (line ~56) simultaneously keeps `reject (rework | regroom)` as
a valid operator verb on `acceptance` — and `reject:rework` lands the item in
`active` (`_drive_valves.py:189`), which is neither a dispatch nor journaled. The
document never states where reject-rework lands. **So this is an internal
inconsistency, not merely a clash with shipped code** — the maintainer can settle
it without adjudicating behavior at all. The second contradiction is
`acceptance-auto-rework`: journaled, but not a dispatch.

The intent is clearly to kill the BARE operator move (`_MOVE_ALLOWED`), which the
rest of the proposal supports. The narrowest repair keeps that intent and makes
the text true — for example: "`active` is entered only by a journaled dispatch
(factory dispatch or driver-dispatch) **or by a rework return from `acceptance`
— the `reject:rework` valve or the Dispatcher's `acceptance-auto-rework`
disposition**. Bare operator moves into `active` are removed from every lane."
Drafted here as a concrete option for whoever amends it; the wording is theirs to
choose.

## Root cause — a partial terminal-outcome → ledger-transition mapping

**NOT a dead process.** The previous revision of this file claimed `active` is
written before the run and cleared after it inside ONE transient dispatcher CLI
invocation, so "if that process does not survive to the second half, nothing ever
moves the item." The reproduction refutes that: the dispatcher survived the entire
dispatch — it ran, merged the PR, ran the post-merge janitor, and journaled a
terminal outcome, calibration, review-gate telemetry, and reflection. It reached
the second half. Process death is one way in, not the cause.

`_dispatcher_loop_selection.py:170-179` is the whole disposition branch, and it
holds exactly three conditional exits from `active`:

```python
if outcome.status == "green" and args.close_on_merge:   # -> acceptance
    complete_and_accept(...)
journal.append(record={"stage": "outcome", "outcome": asdict(outcome)})
escalate_needs_human_block(...)                          # -> blocked (needs-human only)
bounce_non_convergence_to_backlog(...)                   # -> backlog (2 narrow signals)
```

`is_non_convergence_outcome` (`_dispatcher_plan.py:273-275`) returns True ONLY for
`status == "stalled-no-progress"`, or `status == "failed"` AND
`NON_CONVERGED_MARKER in outcome.detail`. Its docstring states the narrowness is
deliberate: "Ordinary failures … are NOT non-convergence and must not be bounced."

A `janitor-post-merge` red (`_dispatcher_engine_janitor.py:118-129` —
`status="failed"`, detail = the janitor's stderr tail) matches none of the three
exits. The item stays `active`/`fabro` forever.

So the defect is that **`active` conflates "a run is executing" with "a dispatch
ended in a state nobody defined an exit for", and the WIP cap counts both** — with
no liveness reconcile at the gate, no bound on the claim, and no attention surface.

The admission gate counts rows and never asks whether the claim is still owned
(`_dispatcher_admission.py`):

```
active_count = sum(1 for item in items if item.status == "active")   # :88
free_slots   = max(0, resolve_wip_cap(cwd=repo) - active_count)      # :89
```

## Evidence — measured 2026-07-26 from artifacts

### The live reproduction, in THIS tenant

`bd-ib-w4h4` — P1 bug, status ACTIVE, assignee `fabro`, created
2026-07-20T03:09:54Z, last updated 2026-07-20T18:20:22Z. The **only** active item
in the tenant. Trail from `tmp/fabro-dispatch-journal.jsonl`:

| time (UTC) | stage | meaning |
|---|---|---|
| 2026-07-20T04:57:07Z | `ledger-admit` | admitted → `active`/`fabro` |
| 2026-07-20T05:29:14Z | `fabro-run` exit 0 | the run succeeded |
| 2026-07-20T05:31:52Z | `pull-primary` `Updating c8bde4a..ba9fdaf` | **the PR merged** |
| 2026-07-20T05:34:37Z | `janitor-post-merge` exit 1 | post-merge janitor red |
| 2026-07-20T05:34:37Z | `outcome` | `{stage: janitor-post-merge, status: failed, pr_number: 836, merge_sha: ba9fdaf…}` |
| 16:46, 17:53 | reconcile retries | each re-ran the janitor; each red |

Then nothing. No exit from `active`, six days and counting.

**The stranded item's own work is already shipped.** PR #836 ("fix: protect
janitor stale reclaim race") merged 2026-07-20T05:31:50Z; `ba9fdaf` is an ancestor
of `origin/master`. `git log -S` confirms `ba9fdaf` introduced BOTH guards
`bd-ib-w4h4` demands — the `fcntl.flock` reclaim mutex AND the payload re-read
(`_dispatcher_janitor_lock.py:87-94`). The stranded run is the run that fixed the
bug. That is NOT a discharged acceptance; the maintainer still owns that call.

**Do not un-strand or close `bd-ib-w4h4`.** It is the cleanest available
reproduction and the requirement-1 verifier is modeled directly on it.

### The measured leak rate

Ledger transitions recorded across this repo's whole dispatch history:

| journal stage | meaning | count |
|---|---|---|
| `ledger-admit` | driven INTO `active` | 130 records / **113 distinct items** |
| `ledger-complete` | `active` → `acceptance` | **87 distinct items** |
| `ledger-accept` | `acceptance` → `done` in-dispatch | 18 distinct items |

**26 of 113 distinct admitted items (23%) never received a `ledger-complete`** —
each driven into `active` with no automatic exit. The journal vocabulary contains
**no bounce, no needs-human-block, and no abandonment stage at all**, so nothing
records the reclaim even when it happens.

Terminal outcomes, all time — every non-green row whose item was admitted is a
candidate stranded claim:

| terminal (stage, status) | occurrences | of which admitted |
|---|---|---|
| `done`, `green` | 87 | 87 |
| **`janitor-post-merge`, `failed`** | **20** | 20 (18 distinct items) |
| `fabro-run`, `failed` | 9 | 9 |
| `host-only-refused`, `failed` | 5 | 3 |
| `run-config-overlay`, `failed` | 4 | 3 |
| `merge-poll`, `failed` | 4 | 4 |
| `admission-held`, `failed` | 1 | 1 |

`janitor-post-merge`/`failed` is the LARGEST failure terminal in the repo.
**34 distinct items** have hit some non-green terminal after admission.

### The leak strands more than a WIP slot

Two dispatch lock files are still on disk from 2026-07-24
(`tmp/fabro-dispatch-bd-ib-fe574e.lock`, `…-bd-ib-fjj7f7.lock`; both PIDs dead),
and abandoned janitor worktrees remain under
`~/.worktrees/livespec-orchestrator-beads-fabro/` — including
`janitor-bd-ib-w4h4` and `janitor-reconcile-bd-ib-w4h4`, both at `ba9fdaf`, kept
"for diagnosis" exactly as the outcome detail says. `bd-ib-fe574e` and
`bd-ib-fjj7f7` both appear in the 26-item no-`ledger-complete` list, so the lock
files, the worktrees, and the ledger all corroborate the same abandonment.

Note the irony for requirement 4: the fleet hygiene scan ALREADY detects stale
worktrees, so it sees this failure's shadow while remaining blind to the failure.

## SETTLED — "sometimes recovers" is ad-hoc human recovery, not a code path

The previous revision asked whether recovery is inconsistent or absent, and told
you to settle it FIRST. **Settled: there is NO automatic recovery.**

Every `update_work_item_status` call site in product code:

| site | writes | trigger |
|---|---|---|
| `_dispatcher_admission.py:102` | `ready` | auto-approve |
| `_dispatcher_admission.py:113` | `active` | admission |
| `_dispatcher_completion.py:111` | `acceptance` | green only |
| `_dispatcher_completion.py:188` | `backlog` | non-convergence only |
| `_dispatcher_ledger_close.py:89` | remap target | beads-native normalize (`open→backlog`, `in_progress→active`) — **never leaves `active`** |
| `_dispatcher_acceptance_rework.py:79` | `active` | rework |
| `_drive_policy_valves.py:188` | move target | **human valve** |
| `_drive_valves.py:153/167/194` | ready/done/target | **human valves** |

Nothing leaves `active` without a green run, a non-convergence signal, or a human.
Of the 18 distinct items that hit a `janitor-post-merge` red, **17 are now closed
and 1 (`bd-ib-w4h4`) is still active** — a ~94% ad-hoc recovery rate, which is
exactly the shape that hides a leak: frequent enough to look handled, lossy enough
to leak one slot at a time, monotonically.

The mechanism the previous revision suspected is confirmed and sharper:
`move_item` (`_drive_policy_valves.py:165-196`) guards ONLY the target status
(`target_status not in _MOVE_ALLOWED`, :176) and has **no source-state guard
whatsoever** — `move:<id>:ready` on an `active` item is fully allowed and lands.
Side effect worth noting: the write passes no assignee, so moving out of `active`
leaves `assignee: fabro` behind, against the documented `active ⟹ assignee`
invariant (`work_items/types.py:118`).

## Requirements — all four; the cut into slices is the maintainer's at groom

1. **Reconcile at the gate.** Before computing `active_count`, establish whether
   each `active` item's dispatch is still alive; a dead claim is journaled as an
   abandonment and **excluded from the count**. **Use the per-work-item dispatch
   ownership lock, NOT the heartbeat** — see §"The signal already exists".
   Self-healing, no new lifecycle vocabulary, and it runs exactly when the answer
   matters. (Earlier revisions of this line said "moved out of `active`". That is
   RETRACTED — moving the item breaks the shipped `reconcile-merged` valve; see
   §"CORRECTED".)
2. **Surface it.** An `active` item whose dispatch is dead MUST reach
   needs-attention. Not optional polish: invisibility is why this sat six days,
   and the system's own design expects a human to run `reconcile-merged` while
   nothing ever tells them. **A fix that only reclaims slots re-hides the very
   failure it recovers from.**
3. **Bound the claim.** An `active` claim MUST NOT be able to outlive its dispatch
   without bound. **This is cheaper than "lease vs subsumed" implies** — see
   §"The signal already exists".
4. **Detect it fleet-wide.** A stale-`active` check belongs in the runtime hygiene
   scan. **This is CROSS-REPO and larger than a missing check** — see
   §"Scope boundary". Explicitly the weakest of the four: detection, not
   prevention. It exists so the class is caught in tenants whose dispatcher path
   differs — **but no such tenant exists today, and dropping this slice is the
   standing recommendation; see §"S4 SCOPE".**

**A verifier must be able to fail.** Each requirement needs a test whose injected
defect would make it red. See §"Prepared slice cut" for each slice's red.

## The signal already exists — use the dispatch lock, not the heartbeat

The previous revision pointed requirement 1 at `HeartbeatSink` / `decide_stall`
and flagged that `reconcile-merged-dispatch-lock.md` calls the heartbeat invalid
during the post-merge janitor window. **Both concerns dissolve: the right signal
is already implemented.**

`commands/_dispatcher_dispatch_lock.py` (added 2026-07-19 in `e957b35`, BEFORE
`bd-ib-w4h4` stranded):

- `dispatch_lock_path()` → `tmp/fabro-dispatch-<work-item-id>.lock` —
  **per work-item**, so the gate can ask about one specific `active` claim.
- Payload: `work_item_id`, `pid`, `started_at_epoch`, `dispatch_id` — exactly the
  four fields `reconcile-merged-dispatch-lock.md` mandates.
- `live_dispatch_lock()` → the lock only if its PID is alive, else `None`: a
  ready-made liveness predicate.
- `_dispatcher_loop.py:86-88` writes it at dispatch start and releases it via an
  `ExitStack` callback, so it spans the WHOLE dispatch **including the post-merge
  janitor window** — precisely the window the heartbeat cannot cover.

**The admission gate never asks.** The only consumer is
`_dispatcher_reconcile_merged.py:127`.

Verified 2026-07-26 by executing the real product code: `bd-ib-w4h4` has no lock
file, so `live_dispatch_lock()` returns `None` → correctly classified dead.

### Requirement 3 resolves to "wire in the stamp that already exists"

`DispatchLock` already carries `started_at_epoch` — **and never consults it.**
`_dispatcher_dispatch_lock.py:88-93` judges liveness by bare `os.kill(pid, 0)`,
with an in-code admission: "Known residual risk: this pidfile lock accepts
standard PID-reuse ambiguity."

`_dispatcher_admission_mutex.py:264-280` already solves exactly this, correctly —
`_lock_holder_matches_pid` + `_pid_start_time_mismatches` compare the recorded
`started_at_epoch` against `process_started_at_epoch(pid)` with a tolerance. The
dispatch lock can adopt that helper directly.

**Demonstrated 2026-07-26:** given a lock whose PID is alive but whose
`started_at_epoch` predates that process's real start by 24h,
`live_dispatch_lock()` answers ALIVE while
`_dispatcher_admission_mutex._lock_holder_matches_pid()`, on identical data,
answers DEAD. Requirement 3 was red against `master` until 2026-07-26 — **it is now
FIXED** by S1 (PR #978 / `a869253`), verified by re-executing the demonstration.
This section is retained as the diagnosis, not as a live defect.

## Coordination hazards — check both before designing

Re-read `SPECIFICATION/proposed_changes/` at thread start; both may have moved.

- **`reconcile-merged-dispatch-lock.md`** (TRACKED, pending, 2026-07-19) —
  load-bearing, and it **ratifies the behavior that stranded `bd-ib-w4h4`**:

  > "A red janitor, missing merged PR, wrong source lane, ambiguous merged PR, or
  > held janitor checkout lock MUST leave the item `active` and report the failed
  > guarded precondition or janitor stage."

  That is deliberate — it preserves the item for the `reconcile-merged` recovery
  valve, on the assumption a human is told to run it. Nothing tells them. This
  collides head-on with requirement 1 unless the clause is bounded by ownership-lock
  liveness — i.e. read as "leave it `active` **for the dispatch that owns it**"
  rather than "leave it `active` unconditionally, forever". Likely one added
  sentence in that pending proposal. **Maintainer ruling required.**

  Its earlier heartbeat objection does NOT block requirement 1, because the
  dispatch-scoped lock it specifies is the signal requirement 1 should read.
- **`wip-cap-zero-dispatch-off.md`** — **RESOLVED: ratified as spec v049** in
  `9941317` (2026-07-26T09:13:02Z). It is no longer a pending proposal and no
  longer a coordination hazard; `wip_cap: 0` is now the documented dispatch-off
  value. Its constraint on this thread SURVIVES ratification and is now normative
  rather than speculative: `_dispatcher_admission.py:87-91` computes `active_count`
  only inside `if enforce_cap:`, so **requirement 1's reconcile must sit OUTSIDE
  that branch and must not be gated on "we need a slot"** — otherwise a repo at
  `wip_cap: 0`, or any run with `enforce_cap` false, never reconciles and never
  surfaces a stale claim. Cheap now, expensive to retrofit.

## Slice cut — APPROVED AND FILED 2026-07-26

> **This section is now HISTORY plus the filed record.** The cut below was approved
> by the maintainer as drafted and filed through
> `/livespec-orchestrator-beads-fabro:groom`. **S4 was DROPPED** (ruling 2), so the
> table's S4 row is retained only for the rationale that killed it — do not
> resurrect it. Filed ids: S1 `bd-ib-ohdu5a`, S2 `bd-ib-cfgkkk`, S3 `bd-ib-pme57n`.
> Two approved scope changes are folded into the FILED slices and are NOT reflected
> in the table rows below: **S1 also closes the write-side `O_EXCL` gap**, and
> **S3 also moves `write_dispatch_lock` to admission time**. Read the filed items
> for the authoritative scope.

Drafted 2026-07-26, NOT filed. The maintainer owns the cut and the acceptance.

| slice | req | scope | depends on |
|---|---|---|---|
| **S1** harden dispatch-lock liveness: consult `started_at_epoch` (PID + process start time), adopting `_dispatcher_admission_mutex._pid_start_time_mismatches` | 3 | in-repo, pure, small | — |
| **S2** needs-attention lane: `active` item with no live dispatch lock, enriched from the journal terminal `outcome` record (carry `pr_number`/`merge_sha`, hand off `reconcile-merged`) | 2 | in-repo | S1 (soft) |
| **S3** narrow `active_count` to claims a LIVE dispatch lock still holds, and journal the abandonment. **Do NOT move the item's status** (§"CORRECTED"); must sit outside `if enforce_cap:` | 1 | in-repo | S1 (**required — unsound without it after a SIGKILL**), S2 (**required — S3 alone deletes the only backpressure; see §"S2 MANDATORY"**) |
| **S4** stale-`active` detection in the fleet hygiene scan | 4 | **cross-repo** (see §"Scope boundary") — but see §"S4 SCOPE": recommended DROPPED, as it protects zero tenants today | independent |

**The ordering is the point: S2 before S3.** Both existing reclamation paths
(`_stale_admission_mutex_reclaimed`, `_stale_janitor_lock_reclaimed`) reclaim
silently and journal nothing; S3 must not copy that silence.

> **Refined by later research — read §"Reclaim destination" before relying on
> this paragraph.** The original argument was "shipping the reclaim first cleans
> up silently after a failure nobody is told about." That is now too strong: if
> S3 sends the item to `blocked`/`needs-human` (the recommended destination), the
> EXISTING `human_valves()` lane surfaces it with no new code. The accurate
> argument is worse for S3-alone, not better — the default lane's handoff is
> `resolve-blocked:<id>:ready`, which pushes an ALREADY-MERGED item back into the
> dispatch queue. So S3 alone does not fail to surface; it surfaces with a handoff
> that causes a second defect. The ordering holds, for a sharper reason.

Requirement 2 is cheaper than it looks — `_needs_attention_work_items.py` is
in-repo, and `_recorded_host_only_refusals()` ALREADY reads
`tmp/fabro-dispatch-journal.jsonl`, filters `stage == "outcome"`, matches an
`outcome.stage`, and builds an `AttentionItem` lane. The janitor-red record is the
same verified shape (`detail`, `fabro_run_id`, `merge_sha`, `pr_number`, `stage`,
`status`, `work_item_id`). `human_valves()` today surfaces `pending-approval`,
`acceptance`, and `blocked`(needs-human) — never `active`.

**But "near-copy" is a trap; three constraints bound it.** S2 is only cheap and
only in-repo if it (a) is built like `host_only_items` rather than routed through
`human_valves()`, and invents no new `AttentionKind` — §"S2 SHAPE"; (b) intersects
journal evidence with CURRENT ledger status rather than copying the precedent's
staleness bug — §"S2 CONSTRAINT — do not copy…"; and (c) carries an actionable
handoff with the prior-attempt count, since `reconcile-merged` cannot always
recover — §"S2 CONSTRAINT — 'run `reconcile-merged`'…". Read all three before
sizing S2.

Rejected: **reclaim-first (S3→S2)**, which ships the wrong handoff first; and
**one combined slice**, which carries four requirements (and, unless S4 is dropped
per §"S4 SCOPE", a cross-repo leg). Note the journal's own `sizing-warn` on
`bd-ib-w4h4`: "description is 4897 chars (> 1500) … consider splitting" and
"carries 5 enumerated parts".

### ⚠ S4 SCOPE — requirement 4 is speculative today; consider dropping the slice

Requirement 4's stated rationale is that it "exists so the class is caught in
tenants whose dispatcher path differs." **Verified on the forge 2026-07-26: there
is no such tenant.** Two findings, both checkable:

1. **No second dispatcher-bearing orchestrator exists.** The only other
   orchestrator in the family, `livespec-orchestrator-git-jsonl`, vendors the SAME
   `livespec_runtime/hygiene_scan.py` but has **no dispatcher at all** — no
   `_dispatcher_admission.py`, no `wip_cap`, no `status == "active"` admission
   concept anywhere under its plugin scripts. (Its only "dispatch" matches are the
   unrelated CI workflows `bump-pin-from-dispatch.yml` and
   `release-dispatch.yml`.) So requirement 4 protects zero additional tenants
   today; it is insurance against a future backend, not coverage of a live gap.
2. **The scanner is deliberately store-agnostic, and the architecture already puts
   store-derived lanes on the CONSUMER side.** Upstream, `scan_hygiene` is invoked
   only by its own CLI (`hygiene_scan_cli.py`) and its tests — it is a standalone
   git-level tool. Meanwhile `compose_needs_attention` already accepts
   `impl_next` and `human_valve_lanes`, i.e. work-item-derived inputs **supplied by
   the consumer**. That split is intentional: the fleet has more than one
   work-items backend, so a store-reading check cannot live in the shared scanner
   without first inventing a store abstraction upstream.

Put together: "add a stale-`active` check to the fleet hygiene scan" asks a
deliberately store-agnostic scanner to read a store, to protect tenants that do
not exist. The consumer-side home for exactly this check is
`_needs_attention_work_items.py` — **which is where S2 already puts it.**

Recommendation to take to the groom: **drop S4 as a slice.** Either defer it until
a second dispatcher-bearing orchestrator actually exists, or reframe it as a
recorded CONVENTION — each orchestrator surfaces its own stale-`active` lane
through its own needs-attention composition — which S2 already satisfies for this
repo. That reduces the epic from four slices to three and removes the only
cross-repo leg. **This is a scoping recommendation, not a ruling; requirement 4 is
the maintainer's to keep, defer, or drop.**

### ⚠ S2 CONSTRAINT — do not copy the precedent's staleness bug

The precedent S2 should follow carries a latent defect. In
`_needs_attention_work_items._host_only_reasons`, the second loop adds every
journal-derived id with **no status check at all**:

```python
for item_id in _recorded_host_only_refusals(project_root=project_root):
    if item_id not in reasons:
        reasons[item_id] = _RECORDED_REFUSAL_REASON
```

The journal is append-only and never pruned, so an item refused once is surfaced
forever. Measured 2026-07-26: the lane derives five items from journal history
(`bd-ib-qcnbbp`, `bd-ib-fjj7f7`, `bd-ib-lgv`, `bd-ib-tyxzhv`, `bd-ib-p3sjiy`) and
**all five are CLOSED** — the lane surfaces five stale rows today and zero live
ones.

**S2 MUST intersect journal evidence with CURRENT ledger status.** Copied
verbatim, S2 would surface all 18 items that ever hit a `janitor-post-merge` red
— 17 of them long closed — to expose the single live one. That is the same
failure this thread exists to fix, inverted: a signal buried in noise is as
invisible as no signal. The journal record supplies the EVIDENCE (`pr_number`,
`merge_sha`, the failing stage); the ledger supplies the PREDICATE
(`status == "active"`); the dispatch lock supplies the LIVENESS. All three are
required.

The staleness bug in the existing `host-only` lane is a **separate pre-existing
defect**, not part of `bd-ib-waov`. It is recorded here because S2 must not
inherit it; filing it is the maintainer's call.

### ⚠ S2 SHAPE — how to keep S2 in-repo (it is easy to make it cross-repo by accident)

S2 is only the cheap in-repo slice if it is built the RIGHT way. Two natural-looking
choices silently convert it into the same cross-repo shape as S4.

1. **Do NOT invent a new `AttentionKind`.** It is a CLOSED `Literal` in the
   VENDORED runtime (`_vendor/livespec_runtime/attention_item.py`) with exactly
   seven values: `human-valve`, `impl`, `spec`, `plan`, `hygiene`, `internal`,
   `host-only`. Adding an eighth means an upstream `livespec-runtime` change plus
   `just vendor-update livespec_runtime` — the same cross-repo path as S4, and the
   same reason S4 is recommended dropped. `validate_attention_item_id`'s prefix
   sets (`_TWO_PART_PREFIXES = {impl, plan}`,
   `_THREE_PART_PREFIXES = {host-only, valve, hygiene, spec}`) are upstream too.
   **Reuse an existing kind.**
2. **Do NOT route S2 through `human_valves()`.** `compose_needs_attention`
   hardcodes `handoff=Handoff(kind="drive", …)` for EVERY valve lane. But
   `reconcile-merged` is a `dispatcher.py` CLI subcommand, not a `drive` action-id,
   so a valve-routed lane would misdeclare its handoff and a consumer rendering it
   would try to run it as a drive action.

**The correct in-repo precedent is `host_only_items`, not `human_valves`.** It
builds its `AttentionItem` DIRECTLY with `Handoff(kind="shell", command=…)`, and
`build_attention` CONCATENATES it onto the composed list rather than passing it
through `compose_needs_attention`:

```python
compose_needs_attention(… human_valve_lanes=human_valves(…) …)
+ host_only_items(project_root=project_root, repo=repo_name, items=materialized)
```

S2 should follow that pattern exactly: build the item directly, `Handoff(kind="shell")`
carrying the `reconcile-merged` invocation, concatenated in `build_attention`. No
upstream change, no re-vendor.

**One latent trap in that pattern.** Items concatenated this way BYPASS
`_append_if_valid`, so nothing validates their id grammar — an id that violates it
is simply never caught. S2 must therefore keep its id grammar-valid by discipline:
three parts, prefixed with one of `_THREE_PART_PREFIXES`, each component non-empty
and non-numeric (`_is_stable_component`). `valve:<verb>:<work-item-id>` qualifies,
and `verb` is free text (`WorkItemHumanValveLane.verb: str`), so no upstream change
is needed to name the new verb.

### ⚠ S2 CONSTRAINT — "run `reconcile-merged`" is not always an actionable handoff

`bd-ib-w4h4`'s janitor red is **deterministic**, and `reconcile-merged` cannot
recover it. All three attempts (2026-07-20 at 05:34, 16:48, 17:56) produced a
byte-identical failure. The operative line is:

```
error: Recipe `check-coverage` failed with exit code 2
error: Recipe `check` failed with exit code 1
```

Note the `livespec_footgun_guard.py:225` / `bd-guard-emit.py:112` lines that
dominate the captured detail are `"phase": "0-warn"`, `"level": "warning"` — Phase-0
WARNings that do NOT fail the gate. The actual cause is the coverage gate failing
in a FRESH checkout of the merged ref, even though the PR's own CI was green
before merge. Do not misread the warning noise as the failure.

Consequence for S2: a lane whose handoff is bare "run `reconcile-merged --item
<id>`" sends the operator into a loop that has already failed three times. The
lane MUST carry the failing stage, the failure detail, and **how many prior
attempts produced it**, so a repeat failure escalates instead of retrying. A
recovery surface that cannot recover, offered without that context, is another
way to re-hide the failure.

(Why the gate is red in a fresh checkout when pre-merge CI was green is a SEPARATE
question — and it is **already filed twice**, as `bd-ib-rxxx` and `bd-ib-d6v1`,
both P1. `bd-ib-rxxx` was filed while dispatching `bd-ib-w4h4` and names it. It is
NOT part of `bd-ib-waov`; see §"The janitor red's ROOT CAUSE is already filed" for
the corroboration and for two discrepancies in `bd-ib-rxxx` worth the maintainer's
eye.)

### ⚠ S3 DESIGN CONSTRAINT — "no live lock" is NOT sufficient on its own

A naive S3 that reclaims every `active` item with no live dispatch lock would be
**destructive**. There is an uncovered window between the `active` write and the
lock write, and it is not small.

`_dispatcher_loop_command.py:187-231` admits a BATCH and then dispatches it
through a thread pool:

```python
admission = admit_and_select(..., enforce_cap=True)   # writes `active` for ALL admitted
with ThreadPoolExecutor(max_workers=max(1, args.parallel)) as pool:
    futures = [pool.submit(dispatch_one, ..., item=item) for item in admission.admitted]
```

`write_dispatch_lock` is called at `dispatch_one`'s entry
(`_dispatcher_loop.py:86`), so an admitted item acquires its lock only when a
worker thread picks it up. `--parallel` **defaults to 1**
(`dispatcher.py:317`), and the admitted batch is bounded by
`min(--budget, free_slots)`. So with `--budget 3 --parallel 1`, items 2 and 3 sit
`active` with NO lock for the full duration of the dispatches ahead of them —
and this repo's journal records individual dispatches of 100+ minutes. The
window is hours, not the ~2s the `bd-ib-w4h4` trail
(`ledger-admit` 04:57:07Z → `dispatch-id` 04:57:09Z) suggests in the budget-1 case.

Note this is the OPPOSITE window from the one the previous revision feared. The
post-merge janitor window is COVERED — the lock is held across it and released by
the `ExitStack` at `dispatch_one` exit. The uncovered window is
**admission → worker-thread start**.

Cleanest resolution, and the one to take to the groom: **write the dispatch lock
at ADMISSION time**, alongside the `active` write in `_dispatcher_admission.py`,
rather than at `dispatch_one` entry — keeping the `ExitStack` release. The lock
then means "this dispatcher process owns this claim" and spans admission →
dispatch → janitor → disposition with no gap, which makes "active with no live
lock" unambiguous and makes requirements 1 and 3 both sound. Weaker fallbacks
(a grace period/TTL before reclaiming; checking whether the admitting dispatcher
process is alive at repo level) do not close the window, only narrow it.

#### Pressure-testing that resolution — four things implementation will hit

The admission-time-lock recommendation was checked against the code rather than
asserted. It holds, with these specifics worth knowing before the work starts:

1. **`dispatch_id` is NOT available at admission.** `dispatch_id = run_id()` is
   generated inside `dispatch_one` (`_dispatcher_loop.py:85`), so an
   admission-written lock carries `dispatch_id: null`. That is already legal —
   `DispatchLock.dispatch_id` is typed `str | None` and
   `_dispatch_lock_from_payload` accepts `None`. `dispatch_one` can rewrite the
   lock to fill the id in once it has one; nothing needs the id to judge liveness.
2. **The pid does not change, only the timing.** The pool is a
   `ThreadPoolExecutor`, not a process pool, so `os.getpid()` is identical at
   admission and at `dispatch_one`. Moving the write earlier changes WHEN the
   claim is stamped, not WHOSE it is.
3. **Every item written `active` does reach `dispatch_one`, so the existing
   release still covers it.** `_dispatcher_admission.py` appends to `admitted`
   only on the same path that writes `active` (:113-119); held items go to
   `refused` and never get an `active` write. The loop then does
   `pool.submit(dispatch_one, …)` for each `admission.admitted`, and the
   `ExitStack` fires on both normal return and exception. Leave the release where
   it is.
4. **A leaked lock file is HARMLESS, and that property is what makes this safe.**
   Liveness is PID-keyed, so a lock whose owner is gone reads dead and the item is
   reclaimable. Do NOT add cleanup machinery for leaked lock files — there is
   nothing to clean up correctness-wise, and cleanup would reintroduce the
   unlink-by-pathname TOCTOU class that `bd-ib-w4h4` was filed about.

**This makes the S1 → S3 dependency load-bearing, not a preference.** Consider a
loop process killed by SIGKILL: the `ExitStack` does not run, so its locks leak
with that pid recorded. If the OS later recycles that pid to an unrelated live
process, a bare `os.kill(pid, 0)` check reports the stale lock as LIVE and the
stranded item is **never** reclaimed — the exact bug this thread exists to fix,
reintroduced through the fix itself. Only S1's PID + `started_at_epoch` check
distinguishes "the original owner" from "some new process that inherited its pid".
S3 without S1 is not merely weaker; it is unsound after any SIGKILL.

### Verifiers — each with the injected defect that makes it red

| slice | test | injected defect that makes it RED |
|---|---|---|
| S1 — **DONE, both reds verified flipped** | lock whose `pid` is live but whose `started_at_epoch` long predates that process's real start → assert DEAD; and a second claim on an existing lock is refused | shipped in PR #978 |
| `bd-ib-l2vglr` — **DONE, red demonstrated before dispatch and verified flipped after** | leaked lock whose recorded pid is dead → assert `write_dispatch_lock` RECLAIMS and re-stamps with the new caller's pid; lock whose holder is LIVE → assert it still REFUSES | shipped in PR #982. Pre-dispatch red: bare `os.open(..., O_EXCL)` raised `FileExistsError` on the dead-pid lock. Injected defect that would re-red it: swallow the raise instead of reclaiming → two dispatches share one claim |
| S2 | `active` item + no live lock + journal `janitor-post-merge`/`failed` record → assert a needs-attention lane naming the item and its merged PR | drop the lane → red |
| S2 (no staleness) | an item with a `janitor-post-merge`/`failed` record in the journal that is now CLOSED → assert NO lane is emitted | key the lane off journal history alone (as the `host-only` lane does today) → the closed item is surfaced → red |
| S2 (right handoff) | a stranded merged-yet-janitor-red item → assert its handoff invokes `reconcile-merged` | emit a handoff that moves the item (e.g. `resolve-blocked:<id>:ready`) → an already-merged item is pushed back into the dispatch queue → red |
| S3 (status preserved) | reclaim a merged-yet-janitor-red item → assert its status is STILL `active` afterwards AND `reconcile-merged --item <id>` still passes its source-lane guard | move it to `blocked`/`backlog` → `reconcile-merged` refuses with "expected active item" → the item is stranded from its own recovery path → red |
| S3 (uncounted, not moved) | one `active` item with no live lock plus `wip_cap` 1 → assert an admission-eligible ready item IS admitted on the same pass | count all `active` rows (today's `_dispatcher_admission.py:88`) → `free_slots` is 0 → nothing admitted → red |
| S3 (live janitor window) | an `active` + PR-merged item whose dispatch is mid-janitor with a live lock, up to the 1h `_JANITOR_TIMEOUT_SECONDS` bound | infer death from `status == "active"` + a merged PR (the `bd-ib-ug4z` defect) → a live run's slot is reclaimed → red |
| S3 (positive) | `active` item, no lock file → run the gate → assert it is EXCLUDED from `active_count` AND an abandonment journal record is written. **Do NOT assert it was moved out of `active`** — that expectation is retracted (§"CORRECTED") | remove the reconcile call → the item is still counted and no record is written → red |
| S3 (negative) | `active` item WITH a lock written for `os.getpid()` → assert it STILL counts against the cap | make the reconcile ignore lock liveness → a live run's slot is released → red |
| S3 (cap-independence) | `enforce_cap` false / `wip_cap` 0 → assert the reconcile still runs | nest the reconcile inside `if enforce_cap:` → red |
| S3 (admission window) | admit a batch larger than `--parallel`, run the gate while the queued items are still awaiting a worker → assert the queued `active` items are NOT reclaimed | leave `write_dispatch_lock` at `dispatch_one` entry → the queued items have no lock → reclaimed → red |
| S3 (recycled pid) | leaked lock recording a pid now held by an unrelated LIVE process, stamped with the original owner's start time → assert the item IS reclaimed | judge liveness by bare `os.kill(pid, 0)` (i.e. ship S3 without S1) → the stale lock reads live → never reclaimed → red |
| S3 (auto-rework park) — **added by the 2026-07-26 amendment** | `active` item parked by `acceptance-auto-rework` (no lock; most recent terminal `outcome` is green) → assert it is STILL COUNTED against the cap and gets NO abandonment record | use the bare "active + no live lock" predicate → the item is uncounted and a FALSE abandonment is journaled → red |
| S3 (valve rework park) — **added by the 2026-07-26 amendment** | `active` item parked by `reject:<id>:rework` (no lock, no journal record of its own, most recent terminal `outcome` green) → assert likewise still counted and unjournaled | as above → red |
| S3 (killed before outcome) — **added by the 2026-07-26 amendment** | a dispatch killed after `ledger-admit` but before any `outcome` record → assert the item IS reclaimed | require an explicit non-green outcome → a SIGKILLed dispatch is never reclaimed and requirement 3 goes unsatisfied → red |

The S3 negative test is what discharges `reconcile-merged-dispatch-lock.md`'s
objection: it proves a live dispatch inside its janitor window is never reclaimed.
S3's positive test must assert BOTH the transition AND the abandonment record, or
it passes vacuously on a status the healthy path also produces.

### Draft amendment — FALLBACK ONLY; likely not needed

> **⛔ Read §"CORRECTED" first.** Under the corrected design (leave the item
> `active`, narrow the count) the pending proposal's "MUST leave the item
> `active`" is honored LITERALLY and **no spec amendment is required at all.**
> This section is retained ONLY as a fallback for the case where the maintainer
> prefers a status move despite the `reconcile-merged` source-lane guard. Do not
> read it as live guidance.

DRAFTED, NOT FILED. The spec side is the maintainer's; this exists so the
decision is a yes/no on concrete text rather than an open design question.

`reconcile-merged-dispatch-lock.md` (TRACKED, still pending on `origin/master`)
contains, at line 70 of its proposed contract block:

> "A red janitor, missing merged PR, wrong source lane, ambiguous merged PR, or
> held janitor checkout lock MUST leave the item `active` and report the failed
> guarded precondition or janitor stage."

Read literally, that forbids requirement 1. The narrowest fix is to bound the
claim by the ownership lock the SAME proposal already mandates, appending one
sentence immediately after it:

```markdown
An item left `active` by this valve remains claimed only while a live
dispatch-scoped ownership lock names it. Once no live lock owns the item the
claim is abandoned, and the Dispatcher's admission valve MUST NOT count it
against the per-repo WIP cap: it MUST journal the abandonment and move the item
out of `active` to `blocked` with `blocked_reason` `needs-human`, so the recovery
this valve exists for is surfaced for a human rather than silently held.
```

Why this shape:

- It reuses the proposal's OWN vocabulary — the "dispatch-scoped ownership lock"
  is introduced two paragraphs earlier in the same block — so it adds no new
  concept and needs no new definition.
- It preserves the clause's intent exactly. The item still stays `active` for the
  dispatch that owns it, which is what the clause is protecting; it only stops
  `active` from outliving every owner.
- It names `blocked`/`needs-human` rather than `backlog`, consistent with
  §"Reclaim destination" and with `escalate_needs_human_block`'s existing
  reasoning.
- It is additive: no existing sentence is deleted or reworded, so it does not
  disturb the rest of a proposal already under review.

**Two routes, maintainer's choice.** Either fold this into
`reconcile-merged-dispatch-lock.md` BEFORE it is revised in (cleanest — the
contract lands coherent the first time), or ratify that proposal as-is and file a
follow-on `propose-change` afterwards (lower coupling, but leaves a window where
the ratified contract forbids requirement 1). If the maintainer instead rules
that requirement 1 narrows to "surface only, never auto-reclaim", **no spec change
is needed at all** — S2 alone is legal under the clause as written, and S3 drops
out of the cut.

### ⛔ CORRECTED 2026-07-26 — do NOT move the item at all; stop COUNTING it

**This supersedes §"Reclaim destination" below, which recommended
`blocked`/`needs-human`. That recommendation was WRONG and is retracted.** It was
made without checking the shipped recovery valve.

`_dispatcher_reconcile_merged.py:110-113`:

```python
if item.status != "active":
    detail = f"ERROR: reconcile-merged expected active item {item.id}; found {item.status}\n"
    return EXIT_PRECONDITION_ERROR
```

Moving a reclaimed item OUT of `active` — to `blocked`, `backlog`, or anything
else — makes it **unrecoverable by the sanctioned valve**, which is precisely the
state `bd-ib-lza6` was filed to fix. A reclaim that strands the item from its own
recovery path is worse than the leak.

**The corrected design: leave the status alone and fix the ARITHMETIC.** Requirement
1's actual goal is "a dead claim must not hold a WIP slot", not "the row must
change status". Narrow `active_count` (`_dispatcher_admission.py:88`) to count only
`active` items that a LIVE dispatch lock still claims. Everything else follows:

- **`reconcile-merged` keeps working** — the item stays `active`, so its source-lane
  guard passes.
- **The pending proposal is satisfied LITERALLY.** "A red janitor … MUST leave the
  item `active`" is honored exactly. **So §"Draft amendment" is NOT needed** — the
  spec collision dissolves rather than requiring a ratification-tier change. Keep
  the draft only as a fallback if the maintainer prefers a status move after all.
- **Requirement 2 returns to its original shape.** The item stays `active`, so the
  `blocked`/`needs-human` valve lane does NOT fire and surfacing is NOT free. S2
  must build its own lane, exactly as §"S2 SHAPE" describes. The claim in
  §"Reclaim destination" that surfacing comes free is retracted with it.
- **It is a strictly smaller change** — one predicate in the admission arithmetic,
  no ledger write, no new lifecycle vocabulary, no spec amendment.

Requirement 3 is still satisfied: the claim is bounded in EFFECT (it stops
consuming capacity) even though the row keeps its status. "Unbounded" does not
survive as the answer.

The abandonment MUST still be journaled — dropping the ledger write does not
license dropping the record. See §"S2 CONSTRAINT" clauses; silence is the
anti-precedent.

#### The corrected design makes S2 MANDATORY, not merely first

This follows directly and is the sharpest form of this thread's thesis.

**Today the leak is self-limiting, in a perverse way.** Every stranded claim
permanently costs one slot, so at `wip_cap` 5 the fifth abandonment halts dispatch
entirely. That total stoppage IS the current forcing function — it is ugly and
slow, but it guarantees a human eventually looks. The console tenant's four-of-five
rows are exactly that pressure, one abandonment from the wall.

**Narrowing `active_count` removes that forcing function.** Under the corrected
design a stranded claim costs nothing, so the cap never fills, dispatch never
stops, and NOTHING ever compels anyone to look. The row sits `active` forever,
uncounted and unexamined.

So S3 shipped alone would not merely "re-hide" the failure — it would **delete the
only backpressure that currently surfaces it, while adding no signal in its place.**
That is strictly worse than today's behavior, not a partial improvement.

**Therefore S2 is not a sequencing preference under the corrected design; it is a
correctness precondition.** S3 MUST NOT merge before the attention lane exists. If
the maintainer wants S3 sooner, the honest options are to ship S2 first, or to ship
them as ONE slice — never S3 alone.

(This is a stronger claim than the earlier "ordering is the point" paragraph, and
it supersedes it. That paragraph argued S2-first on record-keeping grounds; this
argues it on capacity-backpressure grounds, which holds even if one considers the
record adequate.)

### ⚠ LEDGER OVERLAP — `bd-ib-waov` is NOT greenfield; four items already cover parts

Scanned 2026-07-26 across all 80 non-closed items. The groom MUST reconcile against
these before cutting slices, or it will file work that is already shipped.

| item | P | status | relationship to `bd-ib-waov` |
|---|---|---|---|
| **`bd-ib-lza6`** | 2 | **acceptance** | **The same defect, already ruled and shipped.** "Merged items strand in `active` when the dispatch process does not complete its post-run disposition." Maintainer ruled 2026-07-19: build FIX OPTION 2, the `reconcile-merged` valve (PR #797). Options 1 ("route to an acceptance-recoverable state / dedicated lane") and 3 ("make the janitor gate pre-merge") were **explicitly NOT selected.** Held from acceptance pending `bd-ib-ug4z`. |
| **`bd-ib-ug4z`** | 1 | **acceptance** | Added the liveness guard to `reconcile-merged` — this is where `_dispatcher_dispatch_lock.py` came from. |
| `bd-ib-hycf` | 1 | backlog | Largely FALSIFIED on re-check (a journal read-timing misread). Its surviving finding matters here: the **admission lock is released BEFORE the outcome event is journaled**, so a watcher keyed on lock release reads a torn state. |
| `bd-ib-81l0` | 2 | ready | `reconcile_plan` hardcodes `fabro_bin='fabro'`, so **the recovery valve exec-fails inside the credential wrapper.** |

Note on the two `acceptance` rows: `bd-ib-lza6` states it is "HELD from acceptance
pending" `bd-ib-ug4z`. `bd-ib-ug4z`'s fix has SHIPPED (`_dispatcher_dispatch_lock.py`
is on `master`) and the item now sits in `acceptance` itself, so whether lza6's hold
is discharged depends on whether "pending this fix" means merged (satisfied) or
accepted (not yet). Both have been parked since 2026-07-19. Worth the maintainer's
eye — accepting them would settle the ratified recovery path this epic's
requirement 2 is built around.

**✅ EVIDENCE NOW ASSEMBLED, 2026-07-27 — the decision is a yes/no, not an open
question.** Both items now carry an `## ACCEPTANCE EVIDENCE` note written by this
thread. **The accept valve was NOT operated** — `accept` is the human door into `done`
and stays the maintainer's — but the verification work is done, so nothing is waiting
on analysis any more. `needs-attention` surfaces both as
`valve:accept:bd-ib-ug4z` / `valve:accept:bd-ib-lza6`, both `[high]`.

What was verified, by execution rather than by reading:

- **`bd-ib-ug4z`** — the guard is not merely present but CONSUMED:
  `_dispatcher_reconcile_merged.py` imports `live_dispatch_lock` (`:20`) and calls it
  (`:128`) inside the `if not args.force:` preflight (`:118`), so it runs BEFORE PR
  resolution and janitor provisioning, which is the ordering the item required.
  Exercised on all three cases: a LIVE lock is HELD; a lock whose pid is alive but
  whose `started_at_epoch` is bogus correctly reads DEAD; a dead-pid lock is
  reclaimable. **The middle case is stronger than the item asked for** — it was filed
  when liveness was a bare `os.kill(pid, 0)` carrying an admitted PID-reuse residual,
  and S1 (#978) plus `bd-ib-l2vglr` (#982) removed exactly that residual.
- **`bd-ib-lza6`** — PR **#797** merged `63d8184`, verified an ancestor of
  `origin/master`; the valve is a reachable `dispatcher.py` subcommand and its
  source-lane guard fires correctly, exercised LIVE read-only:
  `reconcile-merged --item bd-ib-pme57n` → `ERROR: reconcile-merged expected active
  item bd-ib-pme57n; found done`. **Its hold is discharged on the reading that
  matters**, and the design it ratified is now COMPLETE rather than half-built: it
  assumed a human would be told to run the valve, nothing did, and that gap was this
  epic's requirement 2 — closed by S2 (#1006), with S3 (#1014) stopping the stranded
  claim from eating a slot while it waits.

**Two caveats recorded so the accept is informed, neither an argument against it:**
`bd-ib-ug4z`'s guard is verified at the unit level and by code path, NOT by a staged
live race between a real dispatch and a real reconcile; and `reconcile-merged` still
cannot recover `bd-ib-w4h4`, whose janitor red is deterministic — that cause is owned
by `bd-ib-rxxx`/`bd-ib-d6v1` (both still `backlog`, re-checked today), not by
`bd-ib-lza6`.

**What this leaves genuinely NEW in `bd-ib-waov`** — and the groom should scope it
to exactly this, not re-litigate the above:

1. **The WIP-cap consequence.** `bd-ib-lza6` built a recovery path; nothing has ever
   addressed the fact that a stranded claim permanently consumes a slot. That is
   this epic's core.
2. **The notification gap (requirement 2).** `bd-ib-lza6`'s design assumes a human is
   told to run `reconcile-merged`. **Nothing tells them.** Requirement 2 is precisely
   the missing half of an already-ruled design — which is a much stronger warrant
   than "surface it as polish".
3. **The liveness hardening (requirement 3).** `bd-ib-ug4z` shipped the lock but left
   `started_at_epoch` unconsulted.

Two consequences for the plan:

- **`bd-ib-81l0` is a de-facto dependency of S2.** S2's whole handoff is "run
  `reconcile-merged`", and that valve currently exec-fails under the credential
  wrapper. Surfacing a lane pointing at a broken command is not a fix.
- **The 1-hour janitor timeout is the hard bound S3 must respect.**
  `_dispatcher_engine_janitor.py:40` sets `_JANITOR_TIMEOUT_SECONDS = 3600.0`, so a
  LIVE, healthy dispatch can legitimately sit `active` + PR-merged + mid-janitor for
  a full hour. `bd-ib-ug4z` was filed because `reconcile-merged` inferred death from
  `status == "active"` + a merged PR, which is NOT unique to a dead process. **S3
  must not repeat that inference.** This is the strongest available justification for
  keying the reclaim on the live dispatch lock rather than on status, age, or a TTL.

### The janitor red's ROOT CAUSE is already filed — keep it out of `bd-ib-waov`

An earlier revision called the fresh-checkout janitor red "a SEPARATE question —
plausibly systemic" and left it there. It is separate, and it is **already filed
twice**, both P1 `backlog`:

- **`bd-ib-rxxx`** — "janitor gate is checkout-dependent: `supervisor_discipline`
  passes on master, fails in a fresh janitor checkout, stranding items."
  **Filed 2026-07-20 while dispatching `bd-ib-w4h4` and naming it explicitly.** It
  measured both sides: the primary checkout at clean `origin/master` returns rc=0
  with 8 × `"phase": "0-warn"` for `.claude/hooks/livespec_footgun_guard.py` and
  `bd-guard/bd-guard-emit.py` — the SAME two files `bd-ib-w4h4`'s janitor-red
  detail cites, with `"newly_covered": true`. Strong corroboration.
- **`bd-ib-d6v1`** — "`just check-coverage` reuses a STALE `.coverage` with no
  freshness check", so a standalone invocation reports coverage for a tree state
  unrelated to the working tree.

**Consequence for the groom: `bd-ib-waov` must NOT try to fix the janitor red.**
Its cause is owned elsewhere. `bd-ib-waov` owns the *consequence* — that a
stranded claim silently eats a WIP slot and nobody is told — which is true
regardless of why the janitor went red.

It also means **`bd-ib-w4h4` becomes recoverable once `bd-ib-rxxx` lands**, since
its janitor red would stop reproducing. That is the natural moment to un-strand it
— but not before the requirement-1 verifier exists, since it is the fixture.

#### Two discrepancies in `bd-ib-rxxx` worth the maintainer's eye

Recorded because this thread's own charter says a filed item is a claim with a
timestamp, and both were checked against the forge.

1. **`bd-ib-rxxx` says the dispatch "STRANDED that item `active` with no PR". That
   is FALSE.** PR **#836** exists, its head branch is literally
   `feat/bd-ib-w4h4`, it MERGED at 2026-07-20T05:31:50Z with merge commit
   `ba9fdaf`, and all three of `bd-ib-w4h4`'s terminal outcome records carry
   `pr_number: 836` + that merge SHA. This matters practically: a maintainer
   reading "no PR" could reasonably re-dispatch `bd-ib-w4h4`, which would try to
   rebuild an already-merged change — the exact failure `bd-ib-lza6` documents as
   a non-viable workaround.
2. **The two sources attribute the red differently.** `bd-ib-rxxx` attributes it to
   checkout-dependent `supervisor_discipline`; the captured janitor tail carries an
   explicit `error: Recipe `check-coverage` failed with exit code 2` (the
   `supervisor_discipline` lines in that same tail are `"phase": "0-warn"`,
   `"level": "warning"`, which do not fail the gate). Both readings are recorded
   here without adjudication — `bd-ib-rxxx` did a measured both-sides comparison,
   which is stronger evidence than reading a truncated stderr tail, but it does not
   explain the explicit non-zero `check-coverage` line. `bd-ib-d6v1` may reconcile
   them. **Settling this belongs to `bd-ib-rxxx`, not here.**

### Reclaim destination — SUPERSEDED, retained for the reasoning about `backlog`

Researched 2026-07-26. `backlog` is the wrong destination, and the repo already
argues so in its own words.

**`backlog` would re-dispatch already-merged work.** A `janitor-post-merge` red
means the PR IS ON MASTER (`bd-ib-w4h4` carries `pr_number: 836`,
`merge_sha: ba9fdaf…`). `backlog` leaves the item admission-eligible, so the
Dispatcher would pick it up again and try to redo work that already shipped.
`bounce_non_convergence_to_backlog` is a fine precedent for a slice that never
converged — it is the wrong precedent for a slice that converged and merged.

**The repo's own precedent says so.** `escalate_needs_human_block`'s docstring:

> "Persist that as a Dispatcher-level terminal ledger state, not as `backlog`:
> the item remains unavailable to autonomous admission until a human valve
> deliberately clears the block."

That is exactly this situation. The write seam already exists —
`update_work_item_blocked_state(path=…, item_id=…, status="blocked",
blocked_reason="needs-human", admission_policy="manual")` — and sets the
admission policy in the same call. Admission-ineligibility is guaranteed by
construction: `is_item_ready` is defined as `lane_of(...).name == "ready"`, and
`lane_of` maps a stored `blocked` to `Lane("blocked", <blocked_reason>)`.

**This partially satisfies requirement 2 for free — but NOT completely, and the
residue is the important part.** `lane_of` returns
`Lane("blocked", item.blocked_reason)`, and `human_valves()` already has:

```python
elif status == "blocked" and lane_reason == "needs-human":
    lanes.append(_valve(verb="resolve-blocked", …,
                        action_id=f"resolve-blocked:{item_id}:ready"))
```

So a reclaimed item SHOWS UP in needs-attention immediately, with no new lane
code. **But that lane's handoff is `resolve-blocked:<id>:ready` — which pushes an
already-merged item back to `ready` and straight into the dispatch queue.** The
default surfacing is therefore actively wrong for this class: it tells the
operator to do the one thing that redoes merged work.

**This SHARPENS the S2-before-S3 ordering rather than weakening it.** Shipping S3
alone would not leave the failure unsurfaced — it would surface it with a handoff
that causes a second defect. S2's real job is narrower and clearer than first
stated: not "make it visible" (the blocked lane does that) but **"give it the
right handoff"** — `reconcile-merged` carrying the failing stage, the merge
evidence, and the prior-attempt count, instead of the generic
`resolve-blocked → ready`.

### ⛔ FILING CONSTRAINT — linking slices to the epic is KNOWN-BROKEN; read before filing

The groom's output is "dependency-layered slices under `bd-ib-waov`". **The
sanctioned store writer cannot express that link**, and failing halfway is its
observed behavior — not a hypothetical.

Two filed items, both P2 and both `blocked`:

- **`bd-ib-vari3j`** — "store writer cannot express beads epic membership".
  `_store_mutations._add_dependency_edges` maps every `depends_on` entry to
  `bd dep add <item> <dep> --type blocks`, and the live backend REJECTS that when
  the target is an epic: `Error: tasks can only block other tasks, not epics`.
  `create_work_item` also calls `create_issue(parent_id=None)` hardcoded. So a
  child→epic relationship **has no valid expression through the sanctioned
  writer.**
- **`bd-ib-kn63nm`** — the same defect's consequence: because edges are added
  AFTER the item row is written, the rejection leaves a **PARTIALLY-COMPLETED
  write.** The work-item EXISTS, its declared `depends_on` does not, and the
  caller sees only a traceback. **Re-running the same filing therefore
  DUPLICATES the item.**

**What the groom must do about it:**

1. **Do NOT give a slice a `depends_on` entry pointing at `bd-ib-waov`.** It will
   traceback, and the row will already exist.
2. **Inter-slice edges are FINE.** S1→S3 and S2→S3 are task→task, and `blocks` is
   valid there. Only the child→EPIC edge fails.
3. **Record epic membership in PROSE** (in each slice's description) until
   `bd-ib-vari3j` / `bd-ib-kn63nm` land — the same "prose IS the link" device this
   thread already uses for the cross-tenant `-6ma` supersession.
4. **If any filing tracebacks, RE-READ the store before retrying.** The item is
   probably already there.

Also verified 2026-07-26: **`bd-ib-waov` currently has `dependency_count: 0`,
`dependent_count: 0`, and no children** — it is entirely unlinked, and no other
item in the ledger references it. The four overlapping items in §"LEDGER OVERLAP"
are related only by this prose. Linking them is a groom deliverable, subject to
the constraint above.

### Maintainer rulings — ALL SETTLED 2026-07-26. Do not re-ask.

1. **Spec collision — DISSOLVED.** The reclaim narrows the count and leaves status
   untouched, so the pending proposal's "a red janitor … MUST leave the item
   `active`" is honored LITERALLY. **No amendment to
   `reconcile-merged-dispatch-lock.md` is needed**; §"Draft amendment" stays
   FALLBACK ONLY.
2. **Reclaim mechanism — narrow the count, do NOT move the item.** The
   `blocked`/`needs-human` destination stays RETRACTED, because
   `_dispatcher_reconcile_merged.py:110-113` refuses any item not in `active`.
3. **Requirement 4 / S4 — DROPPED, not deferred.** Closed out of the epic entirely
   on the finding that it protects zero tenants today. The rationale is recorded in
   the closed epic's description so a successor does not resurrect it as an
   oversight. See §"S4 SCOPE".
4. **Epic scope — narrowed to the three genuinely-new pieces**, with `bd-ib-81l0`
   pulled in as S2's gate (as prose; it cannot be an edge).
5. **The cut and every acceptance criterion — APPROVED as drafted**, plus two scope
   additions approved at groom time: S1 also closes the write-side `O_EXCL` gap, and
   S3 also moves `write_dispatch_lock` to admission time.

Three further rulings, settled 2026-07-26 AFTER the groom:

6. **S3's reclaim predicate — AMENDED.** It is no longer "active + no live lock";
   it additionally requires that the item's most recent terminal `outcome` be
   non-green, or that no `outcome` exist since its most recent `ledger-admit`.
   `bd-ib-pme57n`'s description carries the amendment and three added verifiers.
   See §"Rework doors".
7. **`per-state-verb-vocabulary.md`'s self-contradiction — HAND BACK for amendment**,
   delivered 2026-07-26. It is NOT a gate on this track's revise pass, because that
   proposal is not in this track's scope. Never edit it here.
8. **The revise pass covers BOTH pending proposals, and both are ours** —
   `reconcile-merged-dispatch-lock.md` and `rework-return-door-attribution.md`.
   This ruling was corrected twice: an early relay claimed a pass is
   all-or-nothing across every in-flight proposal (retracted, and refuted by
   v049's own history); the correction then scoped us to one file, which went
   stale the moment the peer's proposal ratified as v050 and we filed our own.
   No cross-track coordination is required any more. See §"The revise pass".
9. **The v050 rework-return journaling claim is FALSE and a correction is filed.**
   `reject:rework` is journaled nowhere — the `"journal"` object lives in the
   drive CLI's response payload, and the dispatch journal holds zero
   `human-valve-*` records over 134 dispatches. Filed against OUR spec tree as
   `rework-return-door-attribution.md`. Its second finding — whether the
   unattributable door gains attribution or is removed — is deliberately left for
   ratification to settle, with the recommendation stated. See §"Rework doors".
10. **Two follow-on items filed 2026-07-26**, both `ready`, neither part of the
    epic: **`bd-ib-2wgooj`** (P2, factory-safe — `_MOVE_ALLOWED` still permits the
    bare `move:<id>:active` door that v050 retired; discharges S3's accepted
    residual) and **`bd-ib-d6op2n`** (P2, **host-only**, `factory_safety:
    mutates-host-machinery` — the `livespec-driver-claude` core-resolution
    misfire; owned by that repo, filed in this tenant because beads has no
    cross-tenant edge, so the prose IS the link and it must be routed by hand).

Two further calls settled at groom time:

- **Closing the anchor epic was accepted.** `file_approved_slices` always closes the
  target; the anchor moved to the three filed slices and this file was repointed.
- **`CandidateSlice.priority` is dead API surface** — declared on the dataclass but
  never read by `_work_item_for`, and `WorkItem` dropped `priority` entirely. The
  filed slices therefore came out at the store default P2 despite the draft passing
  `priority=1`; they were set back to P1 to match the epic. Worth its own item;
  filing that is the maintainer's call.

## Scope boundary

- The console (`livespec-console-beads-fabro`) is a **consumer** and owns nothing
  in this fix; its only input is `dispatcher.wip_cap`. Do not route any part of
  this into that repo.
- **Requirement 4 is CROSS-REPO.** `hygiene_scan*.py` exists in this repo ONLY as
  a vendored copy at `.claude-plugin/scripts/_vendor/livespec_runtime/`, sourced
  per `.vendor.jsonc` from `https://github.com/thewoolleyman/livespec-runtime` at
  ref `v0.13.0`; `justfile` records `just vendor-update <lib>` as "the only blessed
  mutation path per livespec/SPECIFICATION/constraints.md §Vendoring". It CANNOT
  be implemented by editing this repo — it lands upstream in `livespec-runtime`
  and is then re-vendored. It is also **larger than "no `active` check today"**:
  `scan_hygiene` is a "Git-level hygiene scanner" taking `repo_path`, not a store
  config, and its four finding families (stale worktrees, primary health, stale
  branches, stale PRs) mean it **never reads the work-items store at all**.
  Requirement 4 is therefore "give the fleet scanner work-item-store awareness",
  a scope expansion upstream — not a one-line addition.
- Core `livespec` is involved ONLY if the design elects new lifecycle vocabulary
  or a documented lease semantic. A reconcile-at-admission fix re-derives existing
  statuses and needs neither.

## Read first

1. This file, then `supervisor-handoff.md` beside it.
2. `bd-ib-waov` in the ledger — **but read it with this caveat.** As of
   2026-07-26 its description still carries the SUPERSEDED root cause ("a
   dispatcher whose process then dies … if that process does not survive to the
   second half"), still points requirement 1 at the heartbeat/`decide_stall`
   primitives, and still frames requirement 4 as in-repo. THIS FILE is the current
   record on all three. The epic was deliberately NOT rewritten from this thread:
   restating it is a ledger write on a maintainer-owned record, and the groom is
   where that restatement belongs. **Restating `bd-ib-waov`'s description is
   itself a groom deliverable.**

Product paths below are all under
`.claude-plugin/scripts/livespec_orchestrator_beads_fabro/`:

3. `commands/_dispatcher_admission.py` (`:88-89` the arithmetic, `:114` the write).
4. `commands/_dispatcher_loop_selection.py:170-179` — the three-exit disposition
   branch that IS the defect.
5. `commands/_dispatcher_plan.py:240-275` — `is_non_convergence_outcome`, whose
   deliberate narrowness leaves the janitor-red path with no exit.
6. `commands/_dispatcher_dispatch_lock.py` — the liveness signal requirement 1
   must reuse, and the unused `started_at_epoch` that answers requirement 3.
7. `commands/_dispatcher_admission_mutex.py:264-280` — the correct PID+start-time
   liveness precedent, and (`:205-229`) the TOCTOU-correct reclaim pattern.
8. `commands/_needs_attention_work_items.py` — the in-repo journal-reading
   attention-lane precedent requirement 2 should follow.
9. `SPECIFICATION/proposed_changes/` — both hazards above.
