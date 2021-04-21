"""Tests for `zip-files` executable."""

import io
import os
import stat
import sys
import time
from pathlib import Path
from zipfile import ZipFile

import pytest
from click.testing import CliRunner
from pkg_resources import parse_version

from test_zip_folder import _check_exit_code, _prepare_folder_with_git_excludes
from zip_files import __version__
from zip_files.zip_files import zip_files


ROOT = Path(__file__).parent / 'root'


def test_valid_version():
    """Check that the package defines a valid ``__version__``."""
    runner = CliRunner()
    result = runner.invoke(zip_files, ['--version'])
    assert __version__ in result.output
    assert result.exit_code == 0
    v_curr = parse_version(__version__)
    v_orig = parse_version("0.1.0-dev")
    assert v_curr >= v_orig


def test_zip_files_simple(tmp_path):
    """Test a simple "zip-folder FOLDER"."""
    runner = CliRunner()
    outfile = tmp_path / 'simple.zip'
    files = [
        ROOT / 'user' / 'folder' / 'My Documents',
        ROOT / 'user' / 'folder' / 'Hello World.docx',
        ROOT / 'user' / 'folder2' / 'FILE.txt',
    ]
    result = runner.invoke(
        zip_files, ['--debug', '-o', str(outfile)] + [str(f) for f in files]
    )
    _check_exit_code(result)
    expected_files = ['Hello World.docx', 'FILE.txt'] + [
        "/".join(["My Documents", f.name]) for f in files[0].iterdir()
    ]
    with ZipFile(outfile) as zipfile:
        zipfile.debug = 3
        assert zipfile.testzip() is None
        assert set(zipfile.namelist()) == set(expected_files)


def test_zip_files_with_root_folder(tmp_path):
    """Test zip-files with "--root-folder"."""
    runner = CliRunner()
    outfile = tmp_path / 'simple.zip'
    files = [
        ROOT / 'user' / 'folder' / 'My Documents',
        ROOT / 'user' / 'folder' / 'Hello World.docx',
        ROOT / 'user' / 'folder2' / 'FILE.txt',
    ]
    result = runner.invoke(
        zip_files,
        ['--debug', '-o', str(outfile), '--root-folder', 'xyz']
        + [str(f) for f in files],
    )
    _check_exit_code(result)
    expected_files = ['xyz/Hello World.docx', 'xyz/FILE.txt'] + [
        "/".join(["xyz", "My Documents", f.name]) for f in files[0].iterdir()
    ]
    with ZipFile(outfile) as zipfile:
        zipfile.debug = 3
        assert zipfile.testzip() is None
        assert set(zipfile.namelist()) == set(expected_files)


def test_zip_files_to_stdout():
    """Test zip-files without --outfile."""
    runner = CliRunner(mix_stderr=False)
    files = [
        ROOT / 'user' / 'folder' / 'My Documents',
        ROOT / 'user' / 'folder' / 'Hello World.docx',
        ROOT / 'user' / 'folder2' / 'FILE.txt',
    ]
    result = runner.invoke(
        zip_files,
        ['--debug', '--root-folder', 'xyz'] + [str(f) for f in files],
    )
    _check_exit_code(result)
    expected_files = ['xyz/Hello World.docx', 'xyz/FILE.txt'] + [
        "/".join(["xyz", "My Documents", f.name]) for f in files[0].iterdir()
    ]
    assert len(result.stdout_bytes) > 0
    with ZipFile(io.BytesIO(result.stdout_bytes)) as zipfile:
        zipfile.debug = 3
        assert zipfile.testzip() is None
        assert set(zipfile.namelist()) == set(expected_files)


def test_zip_files_auto_root(tmp_path):
    """Test zip-files with "--auto-root"."""
    runner = CliRunner()
    outfile = tmp_path / 'autoroot.zip'
    files = [
        ROOT / 'user' / 'folder' / 'My Documents',
        ROOT / 'user' / 'folder' / 'Hello World.docx',
        ROOT / 'user' / 'folder2' / 'FILE.txt',
    ]
    result = runner.invoke(
        zip_files,
        ['--debug', '-o', str(outfile), '-a'] + [str(f) for f in files],
    )
    _check_exit_code(result)
    expected_files = ['autoroot/Hello World.docx', 'autoroot/FILE.txt'] + [
        "/".join(["autoroot", "My Documents", f.name])
        for f in files[0].iterdir()
    ]
    with ZipFile(outfile) as zipfile:
        zipfile.debug = 3
        assert zipfile.testzip() is None
        assert set(zipfile.namelist()) == set(expected_files)


def test_zip_files_exclude(tmp_path):
    """Test zip-files with "--exclude"."""
    runner = CliRunner()
    outfile = tmp_path / 'excluded.zip'
    files = [
        ROOT / 'user' / 'folder' / 'My Documents',
        ROOT / 'user' / 'folder' / 'Hello World.docx',
        ROOT / 'user' / 'folder2' / 'FILE.txt',
    ]
    result = runner.invoke(
        zip_files,
        [
            '--debug',
            '-o',
            str(outfile),
            '--exclude',
            '*.txt',
            '-x',
            'My Documents/*.md',
        ]
        + [str(f) for f in files],
    )
    _check_exit_code(result)
    expected_files = ['Hello World.docx'] + [
        "/".join(["My Documents", f.name])
        for f in files[0].iterdir()
        if not f.name.endswith('.md')
    ]
    with ZipFile(outfile) as zipfile:
        zipfile.debug = 3
        assert zipfile.testzip() is None
        assert set(zipfile.namelist()) == set(expected_files)


def test_zip_files_excludes(tmp_path):
    """Test that zip-files handles exclude patterns correctly."""
    runner = CliRunner()
    outfile = tmp_path / 'archive.zip'
    files = [ROOT / 'folder_with_dotfiles']
    result = runner.invoke(
        zip_files,
        [
            '--debug',
            '-o',
            str(outfile),
            '-x',
            'folder_with_dotfiles/a/*.txt',
            '-x',
            'b/*.md',
        ]
        + [str(f) for f in files],
    )
    _check_exit_code(result)
    expected_files = [
        'folder_with_dotfiles/a/.hidden',
        'folder_with_dotfiles/b/.hidden',
        'folder_with_dotfiles/b/3.txt',
        'folder_with_dotfiles/b/4.txt',
    ]
    with ZipFile(outfile) as zipfile:
        zipfile.debug = 3
        assert zipfile.testzip() is None
        assert set(zipfile.namelist()) == set(expected_files)


def test_zip_files_exclude_options(tmp_path):
    """Test --exclude-from, --exclude-vcs, --exclude-git-ignores."""
    runner = CliRunner()
    folder = _prepare_folder_with_git_excludes(
        tmp_path, ROOT / 'folder_with_git_excludes'
    )

    # zip without excludes
    outfile = tmp_path / 'archive_noexclude.zip'
    result = runner.invoke(
        zip_files,
        [
            '--debug',
            '-o',
            str(outfile),
            '--include-vcs',
            '--include-git-ignores',
            str(folder / 'docs'),
            str(folder / 'README.md'),
            str(folder / 'HISTORY.md'),
            str(folder / 'CONTRIBUTING.md'),
        ],
    )
    _check_exit_code(result)
    expected_files = [
        'docs/.gitignore',
        'docs/_build/index.html',
        'docs/_build/build.log',
        'docs/sources/index.rst',
        'docs/sources/API/file2.rst',
        'docs/sources/API/file1.rst',
        'docs/sources/API/.gitignore',
        'README.md',
        'HISTORY.md',
        'CONTRIBUTING.md',
    ]
    with ZipFile(outfile) as zipfile:
        zipfile.debug = 3
        assert zipfile.testzip() is None
        assert set(expected_files) == set(zipfile.namelist())

    # zip with excludes
    (tmp_path / 'excludes.txt').write_text("HISTORY.md\nCONTRIBUTING.md\n")
    outfile = tmp_path / 'archive_exclude.zip'
    result = runner.invoke(
        zip_files,
        [
            '--debug',
            '-o',
            str(outfile),
            '-X',
            str(tmp_path / 'excludes.txt'),
            '--exclude-vcs',
            '--exclude-git-ignores',
            str(folder / 'docs'),
            str(folder / 'README.md'),
        ],
    )
    _check_exit_code(result)
    expected_files = [
        'docs/sources/index.rst',
        'README.md',
    ]
    with ZipFile(outfile) as zipfile:
        zipfile.debug = 3
        assert zipfile.testzip() is None
        assert set(zipfile.namelist()) == set(expected_files)


def test_zip_files_default_include_dotfiles(tmp_path):
    """Test that zip-files includes dotfiles by default."""
    runner = CliRunner()
    outfile = tmp_path / 'archive.zip'
    files = [ROOT / 'folder_with_dotfiles']
    result = runner.invoke(
        zip_files,
        ['--debug', '-o', str(outfile), '-x', '*.txt']
        + [str(f) for f in files],
    )
    _check_exit_code(result)
    expected_files = [
        'folder_with_dotfiles/a/.hidden',
        'folder_with_dotfiles/b/5.md',
        'folder_with_dotfiles/b/.hidden',
    ]
    with ZipFile(outfile) as zipfile:
        zipfile.debug = 3
        assert zipfile.testzip() is None
        assert set(zipfile.namelist()) == set(expected_files)


@pytest.mark.skipif(
    sys.platform == 'win32',
    reason="Windows does not have Unix file permissions",
)
def test_zip_files_preserve_executable(tmp_path):
    """Test that an executable file permission is preserved."""
    runner = CliRunner()
    outfile = tmp_path / 'archive.zip'
    executable = tmp_path / 'executable.sh'
    with open(executable, "w") as fh:
        fh.write("#!/usr/bin/bash\n")
        fh.write('echo "Hello World"\n')
    os.chmod(executable, stat.S_IXUSR | stat.S_IRUSR)
    result = runner.invoke(
        zip_files, ['--debug', '-o', str(outfile), str(executable)]
    )
    _check_exit_code(result)
    with ZipFile(outfile) as zipfile:
        zipfile.debug = 3
        assert zipfile.testzip() is None
        assert set(zipfile.namelist()) == set(["executable.sh"])
        zip_info = zipfile.getinfo("executable.sh")
        today = time.localtime()
        today_ymd = (today.tm_year, today.tm_mon, today.tm_mday)
        assert zip_info.date_time >= today_ymd
        assert stat.filemode(zip_info.external_attr >> 16) == '-r-x------'
