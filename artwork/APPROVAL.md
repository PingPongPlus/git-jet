# Artwork approval

Both carrier designs and the base artwork are approved. Production artwork lives in
`src/git_jet/art.py` (Classic, jets and effects) and `src/git_jet/lincoln.py` (Lincoln).
Draft sources and review images retain the approved drawings for regression checks.

The owner requested a complete water redesign on 2026-11-02. The sea now lives in
`src/git_jet/water.py`, beneath both carriers: crossing travelling swells, drifting
bow foam, waterline turbulence and spreading stern eddies. The original carrier
studies remain archived; regression checks preserve their hull, deck and island
pixels while allowing the original detached water strips to be removed.

The refined bow animation and the selectable `ocean` / `original` setting were
approved by the owner on 2026-11-02. The bow foam starts at the submerged stem and
peels aft along the hull. Pressure crests expand away from the stem, foam flows
out to both sides, and short spray droplets rise and fall into the wake.
Pressure crests dissolve into the sea before their animation age wraps, fixing
the visible reset reported by the owner on 2026-11-02.
The `original` setting reproduces the archived water pixels for both carriers.
Run `python scripts/preview_water.py` to generate the ocean review loop, or add
`--water original` to inspect the preserved effect.

| Asset | Status | Preview |
| --- | --- | --- |
| Angled aircraft carrier, parked aircraft and waves | Revision 2 approved by project owner, 2026-11-01 | drafts/output/carrier-approval.png |
| Jet, 16 headings, banking and exhaust | Approved by project owner, 2026-11-01 | drafts/output/jet-approval.png |
| Commit grid and activity palette | Approved by project owner, 2026-11-01 | drafts/output/effects-approval.png |
| Projectiles, explosion and smoke | Approved by project owner, 2026-11-01 | drafts/output/effects-approval.png |
| Mast antenna rotating through a full turn | Approved by project owner, 2026-11-02; detached aerial pixels removed as requested | [Animation](drafts/output/radar-spinner.gif) · [Eight angles](drafts/output/radar-spinner-sheet.png) |
| Lincoln carrier traced from the owner's silhouette/runway guides, including island details and radar cleanup | Approved by project owner, 2026-11-02 | [Approved pixels](drafts/output/lincoln-island-detail-transparent.png) · [Island comparison](drafts/output/lincoln-island-detail-comparison.png) · [Animation](drafts/output/lincoln-island-detail-motion.gif) |
| Ocean water with expanding bow pressure crests, outward foam and spray; original water remains selectable | Approved by project owner, 2026-11-02 | [Lincoln demo](../examples/demo/git-jet.gif) · [Classic demo](../examples/demo-classic/git-jet.gif) |

Lincoln is the default; Classic is selectable. Classic's original hull, deck and
island remain unchanged. Its detached aerial was removed alongside the same cleanup
in Lincoln. The rotating antenna is checked separately from the original static study.

The review sheets include example light/dark backgrounds. Exported sprites and
the draft GIF use binary transparency, nearest-neighbor scaling and exact pixel
edges. Review-sheet captions use a separate UI font; exported artwork does not.
The small bitmap font source was carried over from Git Ship under its MIT license.
