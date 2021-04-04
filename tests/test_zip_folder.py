"""Tests for `zip-folder` executable."""

import platform
import shutil
from pathlib import Path
from zipfile import ZipFile

from click.testing import CliRunner
from pkg_resources import parse_version

from zip_files import __version__
from zip_files.zip_folder import zip_folder


ROOT = Path(__file__).parent / 'root'


def test_valid_version():
    """Check that the package defines a valid ``__version__``."""
    runner = CliRunner()
    result = runner.invoke(zip_folder, ['--version'])
    assert __version__ in result.output
    assert result.exit_code == 0
    v_curr = parse_version(__version__)
    v_orig = parse_version("0.1.0-dev")
    assert v_curr >= v_orig


def _check_exit_code(run_res):
    if run_res.exit_code != 0:
        print("STDOUT:")
        print(run_res.stdout)
        print("(END OF STDOUT)")
    assert run_res.exit_code == 0


_ZIP_FOLDER_EXPECTED_HELP = r'''
Usage: zip-folder [OPTIONS] FOLDER

  Create a zip file containing the FOLDER.

Options:
  -h, --help                      Show this message and exit.
  --version                       Show the version and exit.
  --debug                         Activate debug logging.
  -f, --root-folder ROOT_FOLDER   Folder name to use as the top level folder
                                  inside the zip file (replacing FOLDER).

  -c, --compression [stored|deflated|bzip2|lzma]
                                  Zip compression method. The following methods
                                  are available: "stored": no compression;
                                  "deflated": the standard zip compression
                                  method; "bzip2": BZIP2 compression method
                                  (part of the zip standard since 2001); "lzma":
                                  LZMA compression method (part of the zip
                                  standard since 2006).  [default: deflated]

  -a, --auto-root                 If given in combination with --outfile, use
                                  the stem of the OUTFILE (without path and
                                  extension) as the value for ROOT_FOLDER

  -x, --exclude GLOB_PATTERN      Glob-pattern to exclude. This is matched from
                                  the right against all paths in the zip file,
                                  see Python pathlib's Path.match method. This
                                  option can be given multiple times.

  -X, --exclude-from FILE         File from which to read a list of glob-
                                  patterns to exclude, cf. --exclude. Each line
                                  in FILE is one pattern. This option can be
                                  given multiple times.

  --exclude-dotfiles / --include-dotfiles
                                  Whether or not to include dotfiles in the zip
                                  files. By default, dotfiles are included.

  --exclude-vcs / --include-vcs   Whether or not to include files and
                                  directories commonly used by version control
                                  systems. (Git, CVS, RCS, SCCS, SVN, Arch,
                                  Bazaar, Mercurial, and Darcs), e.g.  '.git/',
                                  '.gitignore' '.gitmodules' '.gitattributes'
                                  for Git. By default, VCS are included.

  --exclude-git-ignores / --include-git-ignores
                                  Whether or not to look for .gitignore files
                                  and to process them for exclude patterns. Note
                                  that the .gitignore file itself is still
                                  included in the zip archive unless --exclude-
                                  vcs is given. By default, .gitignore files are
                                  not processed.

  -o, --outfile OUTFILE           The path of the zip file to be written. By
                                  default, the file is written to stdout.
'''.strip()


def test_help():
    """Test the output of ``zip-folder --help``.

    This especially needs to be tested since we're auto-transferring help text
    from ``zip-files``.
    """
    runner = CliRunner()
    result = runner.invoke(zip_folder, ['--help'])
    assert result.exit_code == 0
    # with open("expected_zip_folder_help.debug", "w") as out_fh:
    #     out_fh.write(result.stdout)
    assert result.stdout.strip() == _ZIP_FOLDER_EXPECTED_HELP


def test_zip_folder_simple(tmp_path):
    """Test a simple "zip-folder FOLDER"."""
    runner = CliRunner()
    outfile = tmp_path / 'simple.zip'
    folder = ROOT / 'user' / 'folder'
    result = runner.invoke(
        zip_folder, ['--debug', '-o', str(outfile), str(folder)]
    )
    _check_exit_code(result)
    expected_files = ['folder/Hello World.docx', 'folder/hello.txt'] + [
        "/".join(["folder", "My Documents", f.name])
        for f in (folder / 'My Documents').iterdir()
    ]
    with ZipFile(outfile) as zipfile:
        zipfile.debug = 3
        assert zipfile.testzip() is None
        assert set(zipfile.namelist()) == set(expected_files)


def test_zip_folder_with_root_folder(tmp_path):
    """Test zip-folder with "--root-folder"."""
    runner = CliRunner()
    outfile = tmp_path / 'root.zip'
    folder = ROOT / 'user' / 'folder'
    result = runner.invoke(
        zip_folder,
        ['--debug', '-o', str(outfile), '--root-folder', 'xyz', str(folder)],
    )
    _check_exit_code(result)
    expected_files = ['xyz/Hello World.docx', 'xyz/hello.txt'] + [
        "/".join(["xyz", "My Documents", f.name])
        for f in (folder / 'My Documents').iterdir()
    ]
    with ZipFile(outfile) as zipfile:
        zipfile.debug = 3
        assert zipfile.testzip() is None
        assert set(zipfile.namelist()) == set(expected_files)


def test_zip_folder_compression(tmp_path):
    """Test the different compressions."""
    runner = CliRunner()
    folder = (ROOT / 'user' / 'folder').resolve()
    with runner.isolated_filesystem():
        result = runner.invoke(
            zip_folder,
            ['--debug', '-o', 'uncompressed.zip', '-c', 'stored', str(folder)],
        )
        _check_exit_code(result)
        result = runner.invoke(
            zip_folder,
            [
                '--debug',
                '-o',
                'deflated.zip',
                '--compression',
                'deflated',
                str(folder),
            ],
        )
        _check_exit_code(result)
        result = runner.invoke(
            zip_folder,
            [
                '--debug',
                '-o',
                'bzip2.zip',
                '--compression',
                'BZIP2',
                str(folder),
            ],
        )
        _check_exit_code(result)
        result = runner.invoke(
            zip_folder,
            [
                '--debug',
                '-o',
                'lzma.zip',
                '--compression',
                'Lzma',
                str(folder),
            ],
        )
        _check_exit_code(result)
        outfiles = [
            Path('uncompressed.zip'),
            Path('deflated.zip'),
            Path('bzip2.zip'),
            Path('lzma.zip'),
        ]
        for file in outfiles:
            print("size(%s) = %s" % (file.resolve(), file.stat().st_size))
        s_uncompressed = Path('uncompressed.zip').stat().st_size
        s_deflated = Path('deflated.zip').stat().st_size
        s_bzip2 = Path('bzip2.zip').stat().st_size
        s_lzma = Path('lzma.zip').stat().st_size
        assert s_uncompressed > s_deflated
        assert s_uncompressed > s_bzip2
        assert s_uncompressed > s_lzma
        assert s_uncompressed != s_bzip2 != s_lzma

        result = runner.invoke(
            zip_folder,
            [
                '--debug',
                '-o',
                'invalid.zip',
                '--compression',
                'invalid',
                str(folder),
            ],
        )
        assert result.exit_code != 0
        assert (
            "Invalid value for " in result.output
            and "--compression" in result.output
        )


def test_zip_folder_auto_root(tmp_path):
    """Test zip-folder with "--auto-root"."""
    runner = CliRunner()
    outfile = tmp_path / 'archive.zip'
    folder = ROOT / 'user' / 'folder'
    result = runner.invoke(
        zip_folder,
        ['--debug', '-o', str(outfile), '--auto-root', str(folder)],
    )
    _check_exit_code(result)
    expected_files = ['archive/Hello World.docx', 'archive/hello.txt'] + [
        "/".join(["archive", "My Documents", f.name])
        for f in (folder / 'My Documents').iterdir()
    ]
    with ZipFile(outfile) as zipfile:
        zipfile.debug = 3
        assert zipfile.testzip() is None
        assert set(zipfile.namelist()) == set(expected_files)


def test_invalid_auto_root():
    """Test imcompatibility of --auto-root and other options."""
    runner = CliRunner()
    outfile = 'archive.zip'
    folder = ROOT

    result = runner.invoke(
        zip_folder,
        [
            '--debug',
            '-a',
            '-o',
            str(outfile),
            '--root-folder',
            'xyz',
            str(folder),
        ],
    )
    assert result.exit_code != 0
    assert '--auto-root is incompatible with --root-folder' in result.output

    result = runner.invoke(
        zip_folder,
        ['--debug', '--auto-root', str(folder)],
    )
    assert result.exit_code != 0
    assert '--auto-root requires --outfile' in result.output


def test_zip_folder_exclude(tmp_path):
    """Test zip-folder with basic "--exclude"."""
    runner = CliRunner()
    outfile = tmp_path / 'excluded.zip'
    folder = ROOT / 'user' / 'folder'
    result = runner.invoke(
        zip_folder, ['--debug', '-o', str(outfile), str(folder), '-x', '*.txt']
    )
    _check_exit_code(result)
    expected_files = ['folder/Hello World.docx'] + [
        "/".join(["folder", "My Documents", f.name])
        for f in (folder / 'My Documents').iterdir()
    ]
    with ZipFile(outfile) as zipfile:
        zipfile.debug = 3
        assert zipfile.testzip() is None
        assert set(zipfile.namelist()) == set(expected_files)


def _prepare_folder_with_git_excludes(tmp_path, original):
    """Add git-ignored files to folder."""
    root = tmp_path / original.stem
    shutil.copytree(original, root)
    for file in root.glob('**/*.py'):
        shutil.copy(file, file.with_suffix('.pyc'))
    for file in root.glob('**/Makefile.in'):
        shutil.copy(file, file.parent / 'Makefile')
    for (i, file) in enumerate(['file1.rst', 'file2.rst'], start=1):
        (root / 'docs' / 'sources' / 'API' / file).write_text("file %d" % i)
    (root / "venv").mkdir()
    (root / "venv" / "README.md").write_text("# This is a virtual env")
    (root / 'docs' / '_build').mkdir()
    (root / 'docs' / '_build' / 'build.log').write_text("# build log")
    (root / 'docs' / '_build' / 'index.html').write_text("# HTML")
    return root


def test_zip_folder_exclude_options(tmp_path):
    """Test --exclude-from, --exclude-vcs, --exclude-git-ignores."""
    runner = CliRunner()
    folder = _prepare_folder_with_git_excludes(
        tmp_path, ROOT / 'folder_with_git_excludes'
    )

    # zip without excludes
    outfile = tmp_path / 'archive_noexclude.zip'
    result = runner.invoke(
        zip_folder,
        [
            '--debug',
            '-o',
            str(outfile),
            '--include-vcs',
            '--include-git-ignores',
            str(folder),
        ],
    )
    _check_exit_code(result)
    expected_files = [
        'folder_with_git_excludes/Makefile',
        'folder_with_git_excludes/HISTORY.md',
        'folder_with_git_excludes/docs/.gitignore',
        'folder_with_git_excludes/docs/sources/index.rst',
        'folder_with_git_excludes/docs/sources/API/file2.rst',
        'folder_with_git_excludes/docs/sources/API/file1.rst',
        'folder_with_git_excludes/docs/sources/API/.gitignore',
        'folder_with_git_excludes/README.md',
        'folder_with_git_excludes/setup.pyc',
        'folder_with_git_excludes/setup.py',
        'folder_with_git_excludes/.gitignore',
        'folder_with_git_excludes/CONTRIBUTING.md',
        'folder_with_git_excludes/venv/README.md',
        'folder_with_git_excludes/Makefile.in',
        'folder_with_git_excludes/src/module/file2.py',
        'folder_with_git_excludes/src/module/__init__.py',
        'folder_with_git_excludes/src/module/file1.pyc',
        'folder_with_git_excludes/src/module/file2.pyc',
        'folder_with_git_excludes/src/module/sub/__init__.py',
        'folder_with_git_excludes/src/module/sub/__init__.pyc',
        'folder_with_git_excludes/src/module/file1.py',
        'folder_with_git_excludes/src/module/__init__.pyc',
    ]
    if platform.system() == "Windows":
        # Windows has problems with filesystem case sensitivity.
        # https://bugs.python.org/issue26655
        expected_files = [f.lower() for f in expected_files]
    with ZipFile(outfile) as zipfile:
        zipfile.debug = 3
        assert zipfile.testzip() is None
        # the zip file might include additional pyc and __pycache__files that
        # pytest may have created in the source folder, hence we test for the
        # subset of files we created manually.
        files = list(zipfile.namelist())
        if platform.system() == "Windows":
            files = [f.lower() for f in files]
        assert set(expected_files).issubset(files)

    # zip with excludes
    (tmp_path / 'excludes.txt').write_text("HISTORY.md\nCONTRIBUTING.md\n")
    outfile = tmp_path / 'archive_exclude.zip'
    result = runner.invoke(
        zip_folder,
        [
            '--debug',
            '-o',
            str(outfile),
            '-X',
            str(tmp_path / 'excludes.txt'),
            '--exclude-vcs',
            '--exclude-git-ignores',
            str(folder),
        ],
    )
    _check_exit_code(result)
    expected_files = [
        'folder_with_git_excludes/docs/sources/index.rst',
        'folder_with_git_excludes/README.md',
        'folder_with_git_excludes/setup.py',
        'folder_with_git_excludes/Makefile.in',
        'folder_with_git_excludes/src/module/file2.py',
        'folder_with_git_excludes/src/module/__init__.py',
        'folder_with_git_excludes/src/module/sub/__init__.py',
        'folder_with_git_excludes/src/module/file1.py',
    ]
    if platform.system() == "Windows":
        # Windows has problems with filesystem case sensitivity.
        expected_files = [f.lower() for f in expected_files]
    with ZipFile(outfile) as zipfile:
        zipfile.debug = 3
        assert zipfile.testzip() is None
        files = list(zipfile.namelist())
        if platform.system() == "Windows":
            files = [f.lower() for f in files]
        assert set(files) == set(expected_files)


def test_zip_folder_include_dotfiles(tmp_path):
    """Test zip-folder with "--include-dotfiles"."""
    runner = CliRunner()
    outfile = tmp_path / 'archive.zip'
    folder = ROOT / 'folder_with_dotfiles'
    result = runner.invoke(
        zip_folder,
        [
            '--debug',
            '-o',
            str(outfile),
            str(folder),
            '-x',
            '*.txt',
            '--include-dotfiles',
        ],
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


def test_zip_folder_exclude_dotfiles(tmp_path):
    """Test zip-folder with "--exlude-dotfiles"."""
    runner = CliRunner()
    outfile = tmp_path / 'archive.zip'
    folder = ROOT / 'folder_with_dotfiles'
    result = runner.invoke(
        zip_folder,
        [
            '--debug',
            '-o',
            str(outfile),
            str(folder),
            '-x',
            '*.txt',
            '--exclude-dotfiles',
        ],
    )
    _check_exit_code(result)
    expected_files = ['folder_with_dotfiles/b/5.md']
    with ZipFile(outfile) as zipfile:
        zipfile.debug = 3
        assert zipfile.testzip() is None
        assert set(zipfile.namelist()) == set(expected_files)
