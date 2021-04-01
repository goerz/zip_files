"""Test parsing of .gitignore glob expressions.

Note: run pytest with --log-cli-level=DEBUG to see logging messages
"""
import os
import re

import pytest

from zip_files.backend import gitignore_to_regex


def _path(unix_path):
    """Convert a unix-path into a platform-dependent path."""
    return unix_path.replace("/", os.path.sep)


# fmt: off
TESTS = [
    # prefix        pattern          path                             matches
    (_path('a'),    '*.pyc',         _path('a/file.pyc'),             True),
    (_path('a'),    '*.pyc',         _path('b/file.pyc'),             False),
    (_path('a'),    'b/*.pyc',       _path('a/b/file.pyc'),           True),
    (_path('a'),    '/b/*.pyc',      _path('a/b/file.pyc'),           True),
    (_path('a'),    '/c/*.pyc',      _path('a/b/c/file.pyc'),         False),
    (_path('a'),    '*.py[cod]',     _path('a/b/file.pyc'),           True),
    (_path('a'),    '*.py[cod]',     _path('a/b/file.pyd'),           True),
    (_path('a'),    '*.py[cod]',     _path('a/b/file.pyo'),           True),
    (_path('a/b'),  '*.pyc',         _path('a/b/file.pyc'),           True),
    (_path('root'), 'doc/frotz/',    _path('root/doc/frotz/'),        True),
    (_path('root'), 'doc/frotz/',    _path('root/a/doc/frotz/'),      False),
    (_path('root'), 'frotz/',        _path('root/doc/frotz/'),        True),
    (_path('root'), 'frotz/',        _path('root/a/doc/frotz/'),      True),
    (_path('root'), 'venv/',         _path('root/venv/file.txt'),     True),
    (_path('root'), 'venv/',         _path('root/venv/sub/file.txt'), True),
    (_path('root'), 'venv/',         _path('root/sub/venv/file.txt'), True),
    (_path('root'), '/build',        _path('root/build'),             True),
    (_path('root'), '/build',        _path('root/build/'),            True),
    (_path('root'), '/build',        _path('root/build/file.txt'),    True),
    (_path('a'),    '**/foo',        _path('a/b/foo'),                True),
    (_path('a'),    '**/foo',        _path('a/b/c/foo'),              True),
    (_path('a'),    '**/foo/',       _path('a/b/foo/'),               True),
    (_path('root'), 'abc/**',        _path('root/abc/file.txt'),      True),
    (_path('root'), 'abc/**',        _path('root/abc/sub/file.txt'),  True),
    (_path('root'), 'abc/**',        _path('root/sub/abc/file.txt'),  False),
    (_path('root'), 'a/**/b',        _path('root/a/b'),               True),
    (_path('root'), 'a/**/b',        _path('root/a/x/b'),             True),
    (_path('root'), 'a/**/b',        _path('root/a/x/y/b'),           True),
    (_path('a'),    '?.pyc',         _path('a/f.pyc'),                True),
    (_path('a'),    '?.pyc',         _path('a/file.pyc'),             False),
    (_path('a'),    'f[a-zA-Z].pyc', _path('a/fa.pyc'),               True),
    (_path('a'),    'f[a-zA-Z].pyc', _path('a/f1.pyc'),               False),
    (_path('a'),    'f[a-zA-Z].pyc', _path('a/file.pyc'),             False),
]
# fmt: on


@pytest.mark.parametrize("prefix,pattern,path,matches", TESTS)
def test_gitignore_to_regex(prefix, pattern, path, matches):
    regex = gitignore_to_regex(prefix, pattern)
    rx = re.compile(regex)
    match = rx.match(path)
    assert bool(match) == matches
