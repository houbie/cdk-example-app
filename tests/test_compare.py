import re

import pytest

from tests.compare import assert_similar, ignore


def test_assert_similar_list():
    assert_similar([1, "two", 3], [1, "two", 3])
    assert_similar([1, "two", 3], [1, "two"])
    with pytest.raises(
        AssertionError, match=re.escape('found 1 differences:\nexpected[2]: "3", actual[2]: "index 2 not found"')
    ):
        assert_similar([1, "two"], [1, "two", 3])

    # def test_assert_similar_dict():
    assert_similar({1: "one", 2: "two"}, {1: "one", 2: "two"})
    assert_similar({1: "one", 2: "two"}, {2: "two"})
    with pytest.raises(AssertionError, match=re.escape('found 1 differences:\nexpected.1: "one", actual.1: "None"')):
        assert_similar({2: "two"}, {1: "one", 2: "two"})


def test_assert_similar_with_callable():
    assert_similar([1, "two", 3], [1, "two", (str, "3")])


def test_assert_similar_nested():
    class Cls:
        def __init__(self):
            self.a = 1
            self.b = "b"

    actual = [
        {"foo": "bar", "amount": 0.1, "ignored": (1, 2, "c"), "nested": [{"regex": "123 abc"}, 1, "string", Cls()]},
        (1, 2, "c"),
    ]

    assert_similar(
        actual,
        [
            {
                "foo": "bar",
                "amount": pytest.approx(1 / 10),
                "ignored": ignore,
                "nested": [{"regex": re.compile(r"\d{3}\s\w{3}")}, 1, "string", {"a": 1, "b": "b"}],
            },
            (1, 2, "c"),
        ],
    )

    with pytest.raises(
        AssertionError,
        match=re.escape(
            "found 5 differences:\n"
            'expected[0].not: "present", actual[0].not: "None"\n'
            "expected[0].nested[0]: \"1\", actual[0].nested[0]: \"{'regex': '123 abc'}\"\n"
            'expected[0].nested[1]: "string", actual[0].nested[1]: "1"\n'
            'expected[0].nested[2].a: "1", actual[0].nested[2].a: "None"\n'
            'expected[0].nested[2].nope: "c", actual[0].nested[2].nope: "None"'
        ),
    ):
        assert_similar(
            actual,
            [
                {
                    "foo": "bar",
                    "amount": pytest.approx(1 / 10),
                    "ignored": ignore,
                    "not": "present",
                    "nested": [1, "string", {"a": 1, "nope": "c"}],
                },
                (1, 2, "c"),
            ],
        )
