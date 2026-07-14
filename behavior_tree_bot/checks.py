from behavior_tree_bot.behaviors import threat_deficit


def if_neutral_planet_available(state):
    return any(state.neutral_planets())


def is_under_threat(state):
    return any(threat_deficit(state, planet.ID) > 0 for planet in state.my_planets())


def have_largest_fleet(state):
    return sum(planet.num_ships for planet in state.my_planets()) \
             + sum(fleet.num_ships for fleet in state.my_fleets()) \
           > sum(planet.num_ships for planet in state.enemy_planets()) \
             + sum(fleet.num_ships for fleet in state.enemy_fleets())
