"""Self-check for the combat/defense behaviors. No Java, no engine: `python3 test_bt.py`."""
from io import StringIO
from unittest.mock import patch

from planet_wars import PlanetWars
from behavior_tree_bot.behaviors import ships_needed, threat_deficit, defend_planet, attack_enemy_weakpoint
from behavior_tree_bot.checks import is_under_threat


def run(action, map_data):
    """Execute an action against a fresh state, returning (result, orders issued)."""
    state = PlanetWars(map_data)
    orders = StringIO()
    # planet_wars does `from sys import stdout`, so redirect_stdout can't reach it.
    with patch('planet_wars.stdout', orders):
        result = action(state)
    return result, [line.split() for line in orders.getvalue().split('\n') if line]


# planet 0 (mine, 10 ships, +2/turn) is hit in 5 turns by 30 enemy ships;
# planet 1 (mine, 50 ships) is 3 away, planet 2 is the enemy 20 away.
UNDER_ATTACK = ('P 0 0 1 10 2\n'
                'P 3 0 1 50 1\n'
                'P 20 0 2 30 3\n'
                'F 2 30 2 0 20 5\n')

state = PlanetWars(UNDER_ATTACK)
assert threat_deficit(state, 0) == 10, 'attackers 30 - (10 held + 5 turns * 2 growth)'
assert threat_deficit(state, 1) == 0, 'no inbound enemy fleet'
assert is_under_threat(state)
assert not is_under_threat(PlanetWars('P 0 0 1 10 2\nP 20 0 2 30 3\n'))

result, orders = run(defend_planet, UNDER_ATTACK)
assert result and orders == [['1', '0', '10']], orders  # exactly the deficit, from the near planet

# Same fight, but the only reinforcer is 30 away and the planet falls in 5 turns.
result, orders = run(defend_planet, 'P 0 0 1 10 2\n'
                                    'P 30 0 1 50 1\n'
                                    'P 20 0 2 30 3\n'
                                    'F 2 30 2 0 20 5\n')
assert not result and not orders, 'ships landing after the planet falls are wasted'

# Enemy planet 10 away, 20 ships, +3/turn -> 20 + 1 + 10*3 = 51 to guarantee the capture.
ENEMY_IN_RANGE = 'P 0 0 1 100 5\nP 10 0 2 20 3\n'
state = PlanetWars(ENEMY_IN_RANGE)
assert ships_needed(state, state.planets[1], state.planets[0]) == 51

result, orders = run(attack_enemy_weakpoint, ENEMY_IN_RANGE)
assert result and orders == [['0', '1', '51']], orders

result, orders = run(attack_enemy_weakpoint, 'P 0 0 1 10 5\nP 10 0 2 20 3\n')
assert not result and not orders, 'no surplus to guarantee a capture -> dribble nothing'

result, orders = run(attack_enemy_weakpoint, ENEMY_IN_RANGE + 'F 1 51 0 1 10 4\n')
assert not result and not orders, 'planet 1 is already targeted by a fleet of mine'

print('ok')
