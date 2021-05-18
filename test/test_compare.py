import re

import pytest

from test.compare import assert_similar, ignore


def test_assert_similar_list():
    assert_similar([1, 'two', 3], [1, 'two', 3])
    assert_similar([1, 'two', 3], [1, 'two'])
    with pytest.raises(AssertionError,
                       match="found differences: ..'path': '.2', 'actual': 'index not found', 'expected': 3.."):
        assert_similar([1, 'two'], [1, 'two', 3])


def test_assert_similar_dict():
    assert_similar({1: 'one', 2: 'two'}, {1: 'one', 2: 'two'})
    assert_similar({1: 'one', 2: 'two'}, {2: 'two'})
    with pytest.raises(AssertionError,
                       match="found differences: ..'path': '.1', 'actual': None, 'expected': 'one'.."):
        assert_similar({2: 'two'}, {1: 'one', 2: 'two'})


def test_assert_similar_nested():
    class C:
        def __init__(self):
            self.a = 1
            self.b = 'b'

    actual = [
        {
            'foo': 'bar',
            'amount': 0.1,
            'ignored': (1, 2, 'c'),
            'nested': [
                {'regex': '123 abc'},
                1,
                'string',
                C()
            ]
        },
        (1, 2, 'c')
    ]

    assert_similar(actual, [
        {
            'foo': 'bar',
            'amount': pytest.approx(1 / 10),
            'ignored': ignore,
            'nested': [
                {'regex': re.compile(r'\d{3}\s\w{3}')},
                1,
                'string',
                {'a': 1, 'b': 'b'}
            ]
        },
        (1, 2, 'c')
    ])
