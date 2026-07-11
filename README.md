# P3: Behavior Trees for Planet Wars

A Python bot that plays *Planet Wars* — a real-time galaxy-conquest strategy
game — using a single reactive **Behavior Tree**. The bot must defeat five
distinct opponent bots, each posing a different challenge, within the game's
per-turn time limit.

## Overview

Planet Wars is turn-based at the engine level but simulates real-time play:
every planet produces ships each turn, and fleets are dispatched between
planets to capture neutral territory or attack the enemy. The actual match
simulation is a Java program (`tools/PlayGame.jar` / `tools/ShowGame.jar`);
Python bots communicate with it over stdin/stdout.

The goal of this assignment is to design a single behavior tree (in
`behavior_tree_bot/bt_bot.py`) that reliably beats all five opponent bots in
`opponent_bots/`, and optionally to place well in a class-wide round-robin
competition.

## Requirements

- Python 3
- Java (to run `PlayGame.jar` / `ShowGame.jar`)

If `python run.py` fails to launch, check lines 11, 12, 23, and 24 of
`run.py` — you may need to change `python` to `python3` depending on your
environment.

## Running

From the project root:

```
python run.py
```

This runs a match between your bot (`behavior_tree_bot/bt_bot.py`) and each
of the five opponent bots in turn, then replays each match in a graphical
viewer window.

To run the matches headless and just print the results to the console:

```
python run.py test
```

## Project Structure

```
run.py                          Entry point: runs matches and (optionally) replays them
planet_wars.py                  Game state model (PlanetWars, Planet, Fleet) and issue_order/finish_turn
behavior_tree_bot/
    bt_bot.py                   Bot entry point; builds the behavior tree in setup_behavior_tree()
    behaviors.py                Action nodes (functions that issue orders)
    checks.py                   Check nodes (functions that test conditions in the game state)
    bt_nodes.py                 Behavior tree node classes: Check, Action, Selector, Sequence
opponent_bots/                  The five bots to beat, plus do_nothing_bot for isolated testing
maps/                           Map files used for matches
tools/                          PlayGame.jar / ShowGame.jar (the Java match engine/viewer)
```

## Behavior Tree Basics

The tree is built from four node types (see `bt_nodes.py`):

- **Check** — a leaf node wrapping a condition function (state -> bool).
  Must not issue orders.
- **Action** — a leaf node wrapping a function that issues orders
  (state -> bool, True on success).
- **Selector** — runs children in order until one succeeds; then stops.
- **Sequence** — runs children in order until one fails; then stops.

Do not use the abstract `Node` / `Composite` base classes directly.

Optionally, you can extend `bt_nodes.py` with decorator nodes (e.g.
`Inverter`, `LoopUntilFailed`, `AlwaysSucceed`) and/or a `RandomSelector`.

The starter tree in `bt_bot.py` looks like:

```
Selector: High Level Ordering of Strategies
| Sequence: Offensive Strategy
| | Check: have_largest_fleet
| | Action: attack_weakest_enemy_planet
| Sequence: Spread Strategy
| | Check: if_neutral_planet_available
| | Action: spread_to_weakest_neutral_planet
| Action: attack_weakest_enemy_planet
```

Use this as a starting point, or replace it entirely.

## Debugging

Bots can't use `print()` for debugging — the game engine communicates with
each bot over stdout, so anything printed there corrupts the protocol.
Instead, use the standard `logging` module:

- Each bot writes a `<botname>.log` file (configured via
  `logging.basicConfig` at the top of `bt_bot.py`).
- Tree construction is logged via `logging.info(root.tree_to_string())`.
- Tree execution is already wrapped in `logging.debug()` calls.
- Uncaught exceptions are recorded via `logging.exception()`.
- Add your own `logging.debug()` / `logging.error()` calls in
  `behaviors.py` and `checks.py` as needed.

To test your bot in isolation (no active opponent), use
`opponent_bots/do_nothing_bot.py`.

## Submission Checklist

- [ ] `behavior_tree_bot/bt_bot.py` wins against all five opponent bots
- [ ] `behavior_tree_bot/behaviors.py` and `behavior_tree_bot/checks.py`
      included, containing all actions/checks used by the bot
- [ ] Bot runs within the 1-second-per-turn time limit
- [ ] A text file containing the output of `root.tree_to_string()`
      (logged automatically to `bt_bot.log` on construction)
- [ ] Zipped as `Lastname1-Lastname2-P3.zip`, containing the
      `behavior_tree_bot` folder itself (not just its files)

## References

- [Behavior trees for AI: How they work](http://gamasutra.com/blogs/ChrisSimpson/20140717/221339/Behavior_trees_for_AI_How_they_work.php)
- [Decorators](http://aigamedev.com/open/article/decorator/)
- [Description of the game](http://franz.com/services/conferences_seminars/webinar_1-20-11.gm.pdf)
