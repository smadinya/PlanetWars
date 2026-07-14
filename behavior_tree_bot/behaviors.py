import sys
from math import ceil
sys.path.insert(0, '../')
from planet_wars import issue_order


def threat_deficit(state, planet_id):
    # Ships one of my planets will be short by when the enemy lands. <= 0 means it holds.
    # ponytail: all inbound enemy fleets are treated as one wave landing at the earliest ETA.
    # Overestimates the threat when waves are staggered; split per-arrival if that costs a match.
    incoming = [f for f in state.enemy_fleets() if f.destination_planet == planet_id]
    if not incoming:
        return 0

    planet = state.planets[planet_id]
    eta = min(f.turns_remaining for f in incoming)
    defenders = planet.num_ships + eta * planet.growth_rate \
                + sum(f.num_ships for f in state.my_fleets()
                      if f.destination_planet == planet_id and f.turns_remaining <= eta)
    return int(ceil(sum(f.num_ships for f in incoming) - defenders))


def defend_planet(state):
    issued = False

    for planet_id in [p.ID for p in state.my_planets()]:
        deficit = threat_deficit(state, planet_id)
        if deficit <= 0:
            continue

        eta = min(f.turns_remaining for f in state.enemy_fleets()
                  if f.destination_planet == planet_id)

        # state.my_planets() is re-read every pass: issue_order replaces the source planet.
        for source in sorted(state.my_planets(), key=lambda p: state.distance(p.ID, planet_id)):
            if source.ID == planet_id or state.distance(source.ID, planet_id) > eta:
                continue  # reinforcements landing after the planet falls are wasted
            if threat_deficit(state, source.ID) > 0:
                continue  # don't strip a planet that is losing its own fight
            if source.num_ships > deficit:
                issued |= issue_order(state, source.ID, planet_id, deficit)
                break

    return issued


def attack_enemy_weakpoint(state):
    targeted = {fleet.destination_planet for fleet in state.my_fleets()}
    targets = sorted((p for p in state.enemy_planets() if p.ID not in targeted),
                     key=lambda p: p.num_ships)

    issued = False
    for target in targets:
        for source in sorted(state.my_planets(), key=lambda p: state.distance(p.ID, target.ID)):
            if threat_deficit(state, source.ID) > 0:
                continue
            cost = ships_needed(state, target, source)
            if source.num_ships > cost:
                issued |= issue_order(state, source.ID, target.ID, cost)
                break

    return issued


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
            # Spend at most half the garrison on expansion. Draining a planet to take a
            # neutral just hands it to the next counterattack, and defend_planet has no
            # source to pull from. Without this, aggressive_bot and production_bot win.
            available = source.num_ships / 2 - committed[source.ID]
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