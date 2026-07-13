

def if_neutral_planet_available(state):
    return any(state.neutral_planets())


def have_largest_fleet(state):
    return sum(planet.num_ships for planet in state.my_planets()) \
             + sum(fleet.num_ships for fleet in state.my_fleets()) \
           > sum(planet.num_ships for planet in state.enemy_planets()) \
             + sum(fleet.num_ships for fleet in state.enemy_fleets())

def have_economic_advantage(state):
    my_growth = sum(p.growth_rate for p in state.my_planets())
    enemy_growth = sum(p.growth_rate for p in state.enemy_planets())
    return my_growth > enemy_growth


def can_expand(state):
    if not state.neutral_planets():
        return False
    cheapest_neutral = min(state.neutral_planets(), key=lambda p: p.num_ships)
    return any(
        p.num_ships > ships_needed(state, cheapest_neutral, p)
        for p in state.my_planets()
    )