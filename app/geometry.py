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
