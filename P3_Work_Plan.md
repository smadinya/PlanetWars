# P3 Behavior-Tree Bot — Two-Person Work Plan

## Context
The assignment (`P3_Instructions.md`) requires a single behavior-tree bot that
beats all five opponents in `opponent_bots/` within 1s/turn, plus a text file of
`tree_to_string()`. The starter bot (`behavior_tree_bot/bt_bot.py`) issues **one
fleet per turn**, gated on `len(state.my_fleets()) >= 1`, and picks targets by raw
ship count — too weak to beat the growth-aware opponents. We replace its actions
with **multi-fleet, growth-aware** ones and give the tree a real priority order:
**defend → attack when ahead → expand economy → fallback attack**.

We only edit three files: `bt_bot.py`, `behaviors.py`, `checks.py`. Do **not**
touch `bt_nodes.py` node classes (`Node`/`Composite` are off-limits per spec).
Reuse `state` helpers (`my_planets()`, `neutral_planets()`, `enemy_planets()`,
`my_fleets()`, `enemy_fleets()`, `distance()`) — don't re-derive data.

Opponent cheat-sheet (targets to beat):
- **easy_bot** — 1 fleet at a time to weakest not-mine. Trivial.
- **spread_bot / aggressive_bot** — multi-fleet spread + growth-aware attack; differ only in order.
- **defensive_bot** — spreads, then rebalances ships internally toward its average; barely attacks the enemy.
- **production_bot** — greedily grabs the *biggest* planets (highest growth) first.

Split: **by strategy domain**. Person A = Economy/Expansion, Person B =
Combat/Defense + integration. Target: **win all five reliably** (no competition
tuning phase).

---

## Phase 0 — Setup (do first; ~15 min, either person, commit before splitting)
This environment can't run matches yet.
1. Install **Java** on PATH (needed by `tools/PlayGame.jar`).
2. Make `python` resolve to Python 3 **or** edit `run.py` lines 11, 12, 23, 24 to
   use `python3`.
3. Baseline: `python3 run.py test` → record which of the 5 the starter loses to.
4. **Shared helper contract** (Person A writes it in `behaviors.py` before the
   split so both build on one version — avoids duplication and merge churn):
   ```python
   def ships_needed(state, target, source):
       # ships to capture `target` from `source`, growth-aware for enemy planets
       cost = target.num_ships + 1
       if target.owner == 2:                     # enemy grows en route
           cost += state.distance(source.ID, target.ID) * target.growth_rate
       return cost
   ```
   Both attack and spread actions call this. Agree on the naming convention
   (`snake_case`, one `state` arg, actions return `issue_order(...)`/`False`,
   checks return `bool` and never issue orders).

---

## Person A — Economy / Expansion track
Files: `behaviors.py`, `checks.py` (own functions only).

Actions (`behaviors.py`):
- `spread_to_best_neutral(state)` — replaces `spread_to_weakest_neutral_planet`.
  Score neutrals by **growth_rate ÷ cost** (best economic return), skip neutrals
  already targeted by one of `my_fleets()`, and **issue multiple orders** in one
  turn from planets that have the surplus (`p.num_ships > ships_needed(...)`).
  Remove the `my_fleets() >= 1` gate — that gate is the starter's main weakness.

Checks (`checks.py`):
- `if_neutral_planet_available(state)` — already exists, reuse as-is.
- `have_economic_advantage(state)` — sum of my planets' `growth_rate` vs enemy's
  (economy, not just ship count; complements the existing `have_largest_fleet`).
- `can_expand(state)` — true if I own a planet with surplus ships to spare for a
  neutral (guards the spread sequence).

Validate against: **easy_bot, spread_bot, defensive_bot** (economy-driven
opponents) via `python3 run.py test`.

---

## Person B — Combat / Defense track + integration
Files: `behaviors.py`, `checks.py` (own functions only), `bt_bot.py` (sole owner).

Actions (`behaviors.py`):
- `attack_enemy_weakpoint(state)` — replaces `attack_weakest_enemy_planet`.
  For enemy planets, send from a surplus planet only when
  `source.num_ships > ships_needed(state, target, source)` (guarantees capture,
  not a dribble). Issue multiple orders/turn; skip already-targeted enemies.
- `defend_planet(state)` — find my planets with an **incoming enemy fleet**
  (`enemy_fleets()` whose `destination_planet` is mine) where incoming ships >
  current defenders, and reinforce from the nearest surplus planet. This is what
  beats aggressive_bot / production_bot.

Checks (`checks.py`):
- `have_largest_fleet(state)` — already exists, reuse (gates the attack sequence).
- `is_under_threat(state)` — any of my planets has an incoming enemy fleet that
  would capture it (gates the defense sequence).
- `enemy_is_weaker(state)` — total enemy ships (planets+fleets) below mine, i.e.
  safe to press an attack.

Integration (`bt_bot.py setup_behavior_tree`, Person B, after A+B functions land):
Compose existing `Selector/Sequence/Check/Action` (reuse `.copy()` for the
fallback attack). Priority order:
```
Selector: root
| Sequence: Defense      -> Check is_under_threat        + Action defend_planet
| Sequence: Attack       -> Check have_largest_fleet(or enemy_is_weaker) + Action attack_enemy_weakpoint
| Sequence: Expand       -> Check if_neutral_planet_available + Action spread_to_best_neutral
| Action:   Fallback     -> attack_enemy_weakpoint.copy()
```
Keep the existing `logging.info('\n' + root.tree_to_string())` line — it's the
source of the required submission text file.

Validate against: **aggressive_bot, production_bot** via `python3 run.py test`.

---

## Integration & Verification (joint, end)
1. Merge both branches. Because A and B add **disjoint functions** to the same
   files, git merges cleanly — the only coordination point is the shared
   `ships_needed` helper from Phase 0 (one owner, one version).
2. `python3 run.py test` → must print a win vs **all five** bots. If a case
   loses, tune the **tree ordering** first (cheapest lever), then the action
   thresholds — don't add nodes until a specific match needs one.
3. Confirm each turn stays well under 1s (multi-fleet loops are O(planets²) at
   worst — fine for these maps; avoid per-turn re-sorting of everything).
4. Watch a suspect match with `python3 run.py` (needs Java + display) if a result
   is confusing; read `behavior_tree_bot/bt_bot.log` for the execution trace and
   any `logging.exception` crash. **Never use `print()`** — it corrupts the
   engine's stdout protocol; use `logging.debug()`/`logging.error()`.
5. Copy the `tree_to_string()` block from `bt_bot.log` into a `.txt` file for
   submission.
6. Package: zip the **`behavior_tree_bot/` folder itself** (not just its files) +
   the tree text file as `Lastname1-Lastname2-P3.zip`.

## Coordination notes
- One `state` argument per function; actions return truthy on an issued order,
  `False` otherwise; checks return `bool` and **never** issue orders.
- Don't edit `bt_nodes.py`. Don't add decorator/random-selector nodes — the
  four base node types cover this tree (spec lists them as optional).
- Add each new function next to the example it replaces so diffs stay local and
  the two workstreams don't overlap line ranges.
