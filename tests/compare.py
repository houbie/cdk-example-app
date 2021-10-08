import re

ignore = object()


def collect_differences(actual, expected, path, differences):
    if expected == ignore:
        return differences

    if isinstance(expected, tuple) and len(expected) == 2 and callable(expected[0]):
        return collect_differences(expected[0](actual), expected[1], path=path, differences=differences)

    if isinstance(expected, (list, tuple)):
        for index, expected_item in enumerate(expected):
            try:
                collect_differences(actual[index], expected_item, path=f"{path}[{index}]", differences=differences)
            except IndexError:
                differences.append(
                    {"path": f"{path}[{index}]", "actual": f"index {index} not found", "expected": expected[index]}
                )
        return differences

    if isinstance(expected, dict):
        for key, expected_value in expected.items():
            actual_value = actual.get(key) if isinstance(actual, dict) else getattr(actual, key, None)
            collect_differences(actual_value, expected_value, path=f"{path}.{key}", differences=differences)
        return differences

    if isinstance(expected, re.Pattern):
        if not expected.match(str(actual)):
            differences.append({"path": path, "actual": actual, "expected": expected})
        return differences

    if expected != actual:
        differences.append({"path": path, "actual": actual, "expected": expected})
    return differences


def assert_similar(actual, expected):
    differences = [
        f'expected{diff["path"]}: "{diff["expected"]}", actual{diff["path"]}: "{diff["actual"]}"'
        for diff in collect_differences(actual, expected, path="", differences=[])
    ]
    assert not differences, "found {} differences:\n{}".format(len(differences), "\n".join(differences))
