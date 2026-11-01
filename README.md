# Git Jet

A pixel jet launches from a carrier, banks over your real commit calendar, and
destroys each active day's cell. Transparent background, waves, projectiles and
pixel explosions. Runs with GitHub Actions.

<picture>
  <source media="(prefers-reduced-motion: reduce)" srcset="examples/demo/git-jet.png?v=random-flight-20261101">
  <img src="examples/demo/git-jet.gif?v=random-flight-20261101" width="960" alt="A pixel jet launches from an angled carrier, loops while firing and clears the commit calendar below it.">
</picture>

The demo uses **56 synthetic commits across 14 active days**. Live mode uses your
actual data. **One attack clears one day cell**, regardless of that day's count.
The jet returns to land, the calendar rebuilds, and the animation loops.

## Use in your profile

1. Copy [this workflow](examples/profile-workflow.yml) into your profile repository
   as `.github/workflows/git-jet.yml`.
2. Open **Actions → Git Jet → Run workflow**. It publishes images to `output`.
3. Add this to your README, replacing both `YOUR_USERNAME` values:

```html
<picture>
  <source media="(prefers-reduced-motion: no-preference)"
    srcset="https://raw.githubusercontent.com/YOUR_USERNAME/YOUR_USERNAME/output/git-jet.gif">
  <img width="960"
    src="https://raw.githubusercontent.com/YOUR_USERNAME/YOUR_USERNAME/output/git-jet.png"
    alt="My commit history cleared by a pixel jet">
</picture>
```

Updates run **daily**. Set `days: '30'`, `'7'` or `'365'` under the generation
step's `with:` section. The static PNG preserves the full calendar. Flight uses
smooth curves at a steady cruise speed and fires while moving. The default is
20 FPS; `fps: '10'` makes smaller files while preserving flight speed. Set
`scale: '1'` for smaller images.

Every generation picks a fresh route with varied sweeps, gentle bends and
occasional small loops while shooting. To keep a favorite route, set
`seed: 'my-route'` in the action or use CLI `--seed my-route`. Omit the seed for
new randomness on each run. The generated `report.json` records the chosen seed.

## Run locally

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev]'
git-jet render --demo --output-dir out/demo
git-jet render --username YOUR_USERNAME --days 365 --output-dir out/live
```

For offline real-data rendering, use `--calendar out/live/calendar.json`.
`git-jet collect --username YOUR_USERNAME --output out/calendar.json` saves data
without rendering. `GITHUB_TOKEN` is optional locally; Actions supplies its token.
No server is needed.

## What gets counted

Distinct authored commits in **public, owned, non-fork repositories' default
branches**, including documentation commits. The selected 1–365-day window
includes today and uses UTC. Duplicate SHAs count once. This commit-only graph
excludes issues, PR activity, private repositories and unlinked author identities.
It can differ from GitHub's broader profile contribution calendar.

Each active day gets one visible attack; flight length grows with active days.
No targets are silently sampled or skipped. Empty calendars get a patrol with
no shots. Export is bounded to 3,000 frames and 25 MB per GIF; use fewer days or a
lower scale if needed. Failed generation preserves previously good assets.

Generation and publication are separate. The publisher updates only `git-jet.gif`
and `git-jet.png` on `output`, preserves other files, uses non-force pushes and
never changes your default branch. Publishing requires `contents: write`.

## Goals

- [x] Approved carrier, parked aircraft, waves, directional jets, grid and effects.
- [x] Real commit collection, transparent GIF/PNG export and a daily Actions template.
- [x] Catapult launch, banked flight, one attack per active day and carrier return.
- [ ] Optional **one shot per individual commit** mode.
- [ ] More carrier/jet designs and configurable graph palettes, with artwork approval.

[Artwork approvals](artwork/APPROVAL.md) · [Contributing](CONTRIBUTING.md) · [MIT](LICENSE)
