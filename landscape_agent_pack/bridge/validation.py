"""Numerical checks of the real native-import fixture, never synthetic SKP data."""
import math

def require(condition, message='Bridge geometry validation failed'):
    if not condition:
        raise ValueError(message)

def check_fixture(snapshot, facts, request):

    def near(a, b, tolerance):
        return len(a) == len(b) and max((abs(x - y) for x, y in zip(a, b))) <= tolerance
    require(snapshot['model_units_code'] == 2, 'SketchUp units are not mm')
    require(len(snapshot['root_entities']) == 1, 'Unexpected root geometry')
    require(snapshot['reference_name'] == 'CAD_REFERENCE', 'Bridge geometry validation failed')
    require(snapshot['reference_markers']['source_sha256'] == request.source_sha256, 'Bridge geometry validation failed')
    require(set(facts['layers']).issubset(snapshot['tags']), 'Missing CAD tags')
    require(near(snapshot['bbox_mm'], facts['expected_bbox_mm'], request.bbox_tolerance_mm), 'Bounds mismatch')
    edges = snapshot['edges']
    points = [e[key] for e in edges for key in ('a', 'b')]
    coordinate_error = max((min((math.dist(p, q) for q in points)) for p in facts['control_points_mm'].values()))
    require(coordinate_error <= request.coordinate_tolerance_mm, 'Key CAD coordinate missing')
    expected_lines = [([0, 0, 0], [10000, 0, 0]), ([10000, 0, 0], [10000, 5000, 0]), ([2500, 3500, 1200], [2500, 4500, 1200]), ([2500, 3500, 0], [4000, 4500, 0]), ([4000, 4500, 0], [5500, 4000, 0])]
    for a, b in expected_lines:
        require(any((near(e['a'], a, request.coordinate_tolerance_mm) and near(e['b'], b, request.coordinate_tolerance_mm) or (near(e['b'], a, request.coordinate_tolerance_mm) and near(e['a'], b, request.coordinate_tolerance_mm)) for e in edges)), 'CAD line missing')
    require(snapshot['edges_by_tag']['L-HARDSCAPE'] == 4, 'Closed rectangle not preserved')
    rect = [e for e in edges if e['tag'] == 'L-HARDSCAPE']
    expected_corners = [[1000, 500, 0], [7000, 500, 0], [7000, 2500, 0], [1000, 2500, 0]]
    for i, a in enumerate(expected_corners):
        b = expected_corners[(i + 1) % 4]
        require(any((near(e['a'], a, 0.1) and near(e['b'], b, 0.1) or (near(e['b'], a, 0.1) and near(e['a'], b, 0.1)) for e in rect)), 'Rectangle side missing')
    deviations = {}
    for name, tag in (('circle', 'L-PLANT'), ('arc', 'L-WATER')):
        curve = facts[name]
        selected = [e for e in edges if e['tag'] == tag and e['curve_id'] is not None]
        require(selected, f'{name} native curve missing')
        radius, center = (curve['radius_mm'], curve['center'])
        radial_error = max((abs(math.dist(p, center) - radius) for e in selected for p in (e['a'], e['b'])))
        sagitta = max((radius - math.sqrt(max(0, radius * radius - math.dist(e['a'], e['b']) ** 2 / 4)) for e in selected))
        angle_sum = sum((2 * math.asin(min(1, math.dist(e['a'], e['b']) / (2 * radius))) for e in selected))
        require(abs(angle_sum - math.radians(360 if name == 'circle' else 140)) < 1e-06, f'{name} angular coverage incomplete or duplicated')
        require(radial_error <= request.coordinate_tolerance_mm, f'{name} radius mismatch')
        require(sagitta + radial_error <= request.curve_tolerance_mm, f'{name} chord deviation exceeds tolerance')
        if name == 'arc':
            for angle in (200, 340):
                a = math.radians(angle)
                p = [center[0] + radius * math.cos(a), center[1] + radius * math.sin(a), 0]
                require(min((math.dist(p, q) for e in selected for q in (e['a'], e['b']))) <= request.coordinate_tolerance_mm, 'Arc endpoint mismatch')
        deviations[name] = {'edges': len(selected), 'radial_error_mm': radial_error, 'chord_deviation_mm': sagitta}
    require(len(edges) == sum(snapshot['edges_by_tag'].values()), 'Bridge geometry validation failed')
    return {'edges': len(edges), 'coordinate_error_mm': coordinate_error, 'curves': deviations, 'bbox_mm': snapshot['bbox_mm']}

def compare_persistence(before, after, tolerance=1e-06):
    require(len(before['edges']) == before['edge_count'] and len(after['edges']) == after['edge_count'],
            'Snapshot edge count does not match actual edge records')
    for key in ('edge_count', 'edges_by_tag', 'tags', 'reference_transform', 'reference_markers', 'root_entities', 'model_units_code'):
        require(before[key] == after[key], f'Persistence mismatch: {key}')

    def ordered(s):
        return sorted(((e['tag'], *sorted((tuple(e['a']), tuple(e['b'])))) for e in s['edges']))
    error = 0.0
    for a, b in zip(ordered(before), ordered(after)):
        require(a[0] == b[0], 'Bridge geometry validation failed')
        error = max(error, math.dist(a[1], b[1]), math.dist(a[2], b[2]))
    require(error <= tolerance, 'Geometry changed after disk reopen')
    require(sorted(((c['class'], c['edge_count']) for c in before['curves'])) == sorted(((c['class'], c['edge_count']) for c in after['curves'])), 'Curve types changed')
    return {'maximum_edge_coordinate_change_mm': error, 'edge_count': after['edge_count']}
