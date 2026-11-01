# Verification — 2026-11-01

- All carrier revision 2, jet, graph and effects artwork was approved by the owner.
- Production art is checked against the approved draft sprites and carrier PNG.
- 80 local tests pass on Python 3.15 / Pillow 13. Lint and formatting pass.
- Source distribution and wheel build; the installed wheel's CLI renders offline.
- The seeded demo (`git-jet-loop`) exports at 960×640, 560 frames, 28 seconds at
  20 FPS (8,418,853 bytes), with 56 synthetic
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
- CI runs verification and an offline composite-action smoke render on pushes
  and pull requests. The profile-workflow template schedules daily generation.

The graph represents complete UTC calendar dates including the current day.
One attack clears one active day, not one individual commit. Per-commit attacks
remain a future optional mode in the README goals.
