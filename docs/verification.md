# Verification — 2026-11-02

- Base carrier revision 2, jet, graph and effects artwork was approved by the owner.
  The radar animation awaits owner review on `radar-spinner` before merging.
- Production art is checked against the approved draft sprites and carrier PNG;
  only the rotating antenna region differs during animation. The initial frame
  remains pixel-identical to the approved carrier.
- 130 local tests pass on Python 3.15 / Pillow 13. Lint and formatting pass.
- Source distribution and wheel build; the installed wheel's CLI renders offline.
- The seeded demo (`git-jet-loop`) exports at 960×640, 560 frames, 28 seconds at
  20 FPS (8,420,269 bytes), with 56 synthetic
  commits on 14 active days and exactly 14 attacks. Every decoded GIF frame
  matches its intended colors, binary transparency, timing and cleanup.
- Live public collection for PingPongPlus returned 99 distinct authored commits
  on 12 active days in the 30-day UTC window ending 2026-11-01, using 22 requests.
  Rendering that cached calendar produced 12 attacks with decoded frames verified.
  This snapshot is not a claim about private, fork or third-party repositories.
- Tests cover zero activity, 365 active-day target coverage, muzzle origins,
  flight bounds, cell destruction/reset, dates, SHA deduplication, pagination,
  scoped-token fallback, offline Action execution, secret-free metadata, failed
  export preservation, and publishing only images without changing main.
- Continuous flight uses an arc-length course with smoothly ramped turn rates,
  64 rotation steps derived from the approved jet, and moving projectile launches.
  Across 12 seeded routes at 20 FPS, airborne speed stays between 95 and 102
  logical pixels/second through path joins and firing frames; heading changes
  stay below 12 degrees per frame.
  FPS changes sampling density while preserving physical cruise speed.
- Each generation chooses fresh randomized sweeps, bends and optional closed
  loops. Explicit seeds reproduce poses and attack schedules, and are recorded
  in the report. Loop routes schedule a real day-cell attack during the maneuver.
  Five seeded full-year cases retain all 365 targets within the frame limit.
- Optional 1–3 jets keep single-jet behavior as the default. Squadron tests cover
  disjoint, balanced targets; staggered launches; simultaneous visible aircraft;
  projectile origins; smooth motion; shared reset after all landings; empty and
  sparse calendars; seed replay; and every supported FPS. Two and three jets
  shorten dense full-year calendars across five route seeds without losing targets.
- The orhun public-data snapshot has 1,124 commits on 325 active days for
  2025-11-02 through 2026-11-01. With seed `47f76d98ee2f6d5c`, three jets export
  at 960×640, 20 FPS, 1,360 frames, 68 seconds and 23,416,497 bytes. All decoded
  frames match, all 325 dates receive one attack, and their counts still total
  1,124. The same seed with one jet takes 124 seconds.
- Automatic size fitting is enabled by default and retries lower integer scales,
  then supported lower frame rates. Tests cover a real oversized export,
  one collection and one seed across retries, all targets retained, frame-limit
  recovery, opt-out, unrelated errors, and preserving prior assets if nothing fits.
  Before the radar update, the orhun single-jet render automatically fell from 960×640 to 480×320 at
  20 FPS, retains all 325 attacks and 1,124 commits, and produces a 17,014,564-byte
  GIF identical to the earlier manually configured render. Reports record the
  requested and final scale/FPS and whether automatic reduction was used.
- The existing mast antenna makes one full turn every four seconds, with
  foreshortened edge views and a shaded back face. Radar tests check the complete
  loop, hard transparent pixel edges, unchanged timing at 5/10/20/25 FPS, and
  continuous rotation through flight and landing. Review GIF and angle sheet
  can be regenerated with `PYTHONPATH=src python scripts/preview_radar.py`.
- CI runs verification and an offline composite-action smoke render on pushes
  and pull requests. The profile-workflow template schedules daily generation.

The graph represents complete UTC calendar dates including the current day.
One attack clears one active day, not one individual commit. Per-commit attacks
remain a future optional mode in the README goals.
