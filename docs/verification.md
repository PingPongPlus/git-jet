# Verification — 2026-11-02

- The owner approved the Lincoln silhouette, angled runway, parked aircraft,
  detailed island wall, radar animation and detached-pixel cleanup. Classic's
  original hull/deck/island and the jet, grid and effects retain their approvals.
- 164 local tests pass on Python 3.15 / Pillow 13. Lint, formatting and package builds pass.
- Lincoln is the default in the renderer, CLI and GitHub Action. Classic remains
  selectable. The chosen carrier reaches every jet and size-reduction retry,
  and is recorded in the export report. Invalid names fail before collection.
- Lincoln's initial pixels match the approved transparent PNG. Its animation
  matches the approved drawing source across 80 phases. Classic matches its
  original reference outside the rotating radar and the requested aerial cleanup.
- Both models retain the original projection and transparent 350×190 native
  carrier canvas. Lincoln's launch and landing anchors now come from the painted
  angled runway. Its ground jet fits the runway, smoothly grows after liftoff
  and shrinks before touchdown. Tests check every visible sprite pixel stays
  inside the runway throughout both ground rolls with 1–3 jets at every supported
  FPS. The landing roll stops at the next launch point without overshooting.
  Tests also cover smooth, bounded flight with all 365 targets and randomized
  routes; upper loops remain ahead of the new departure entry.
- Both mast antennas rotate once every four seconds, including while jets are
  on deck. Tests check every supported FPS, complete-cycle continuity, binary
  transparency and no disconnected pixels above the radars in all 80 phases.
- Both README demos use the same fixed 56-commit, 14-active-day synthetic calendar,
  seed `git-jet-loop`, 960×640 size and 20 FPS. Lincoln exports 24 seconds and
  7,345,520 bytes; Classic remains 28 seconds and 8,407,801 bytes. Every decoded GIF frame matches
  its intended pixels, transparency, timing and cleanup. Each demo has 14 attacks.
- Auto size reduction retains all day-cell targets and the route seed, lowers
  scale before FPS, and preserves the selected carrier. Tests also cover opt-out,
  frame limits, failure preservation and avoiding retries for unrelated errors.
- Collection tests cover UTC windows, authored SHA deduplication, pagination and
  scoped-token fallback. The calendar scope remains public, owned, non-fork
  repositories' default branches, including documentation commits.
- CI verifies Python 3.11 and 3.15 and runs the composite Action with both carrier
  choices. The profile workflow schedules daily generation.

Rebuild both fixed-data README demos with
`PYTHONPATH=src python scripts/render_demos.py`. Their reports record the carrier,
seed, requested/final scale and FPS, and every target. One attack clears one
active day; per-commit attacks remain a future optional mode.
