# specific area = 1 / density
# https://en.wikipedia.org/wiki/Circle_packing_in_a_circle
PACKING_SPECIFIC_AREA = {
    # 1: 1.0,
    # 2: 2.0,
    3: 1.547578137,
    4: 1.547578137,  # 1.457106781,
    5: 1.547578137,  # 1.459406085,
    6: 1.5,
    7: 1.5,  # 1.285714286,
    8: 1.5,  # 1.365183857,
    9: 1.5,  # 1.450519887,
    10: 1.4546596,
    11: 1.39965827,
    12: 1.39965827,  # 1.353408333,
    13: 1.380328608,
    14: 1.380328608,  # 1.338588643,
    15: 1.362844587,
    16: 1.362844587,  # 1.331716,
    17: 1.351344059,
    # 18: 1.314200547,
    # 19: 1.245032098,
    # 20: 1.31225645,
    }


def outersected(child_radius, parent_radius, distance):
    depth = distance + child_radius - parent_radius  # of outersection
    if depth <= 0.0: return 0.0
    diameter = 2.0 * child_radius
    # linear approximation
    return min(depth/diameter, 1.0)


def intersected(child_radius, parent_radius, distance):
    depth = parent_radius + child_radius - distance  # of intersection
    diameter = 2.0 * child_radius
    if depth >= diameter: return 1.0
    # linear approximation
    return max(depth/diameter, 0.0)


def packing_specific_area(radii):
    '''
    Returns the ratio of enclosing circle’s sufficient area
    to the enclosed circles total area.
    '''
    number = len(radii)
    if number == 2:
        # exact solution
        return sum(radii)**2 / sum(r*r for r in radii) 
    if number <= 17: return PACKING_SPECIFIC_AREA[number]
    # lower bound for all remaining
    return PACKING_SPECIFIC_AREA[17]
