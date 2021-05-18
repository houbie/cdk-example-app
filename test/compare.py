import re

ignore = object()


def collect_differences(actual, expected, path, differences):
    if expected == ignore:
        return differences
    if isinstance(expected, list) or isinstance(expected, tuple):
        for index, expected_item in enumerate(expected):
            try:
                collect_differences(actual[index], expected_item, f'{path}.{index}', differences)
            except IndexError:
                differences.append(
                    {'path': f'{path}.{index}', 'actual': 'index not found', 'expected': expected[index]})
        return differences

    if isinstance(expected, dict):
        for key, expected_value in expected.items():
            actual_value = actual.get(key) if isinstance(actual, dict) else getattr(actual, key)
            collect_differences(actual_value, expected_value, f'{path}.{key}', differences)
        return differences

    if isinstance(expected, re.Pattern):
        if not expected.match(str(actual)):
            differences.append({'path': path, 'actual': actual, 'expected': expected})
        return differences

    if expected != actual:
        differences.append({'path': path, 'actual': actual, 'expected': expected})
    return differences


def assert_similar(actual, expected):
    differences = collect_differences(actual, expected, '', [])
    assert not differences, f'found differences: {differences}'
