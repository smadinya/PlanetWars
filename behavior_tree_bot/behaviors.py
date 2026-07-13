import sys
sys.path.insert(0, '../')
from planet_wars import issue_order


def attack_weakest_enemy_planet(state):
    # (1) If we currently have a fleet in flight, abort plan.
    if len(state.my_fleets()) >= 1:
        return False

    # (2) Find my strongest planet.
    strongest_planet = max(state.my_planets(), key=lambda t: t.num_ships, default=None)

    # (3) Find the weakest enemy planet.
    weakest_planet = min(state.enemy_planets(), key=lambda t: t.num_ships, default=None)

    if not strongest_planet or not weakest_planet:
        # No legal source or destination
        return False
    else:
        # (4) Send half the ships from my strongest planet to the weakest enemy planet.
        return issue_order(state, strongest_planet.ID, weakest_planet.ID, strongest_planet.num_ships / 2)


def spread_to_best_neutral(state):
    # Send to neutrals with the best growth_rate-per-cost, skip ones already
    already_targeted = {fleet.destination_planet for fleet in state.my_fleets()}
    committed = {p.ID: 0 for p in state.my_planets()}

    neutral_targets = [p for p in state.neutral_planets() if p.ID not in already_targeted]

    def economic_score(p):
        cost = p.num_ships + 1
        return p.growth_rate / cost if cost > 0 else 0

    neutral_targets.sort(key=economic_score, reverse=True)

    orders_issued = False
    for target in neutral_targets:
        cost = ships_needed(state, target, target)

        best_source = None
        best_available = 0
        for source in state.my_planets():
            available = source.num_ships - committed[source.ID]
            if available > cost and available > best_available:
                best_source = source
                best_available = available

        if best_source:
            issue_order(state, best_source.ID, target.ID, cost)
            committed[best_source.ID] += cost
            orders_issued = True

    return orders_issued

def ships_needed(state, target, source):
    # ships to capture `target` from `source`, growth-aware for enemy planets
    cost = target.num_ships + 1
    if target.owner == 2:  # enemy grows en route
        cost += state.distance(source.ID, target.ID) * target.growth_rate
    return cost