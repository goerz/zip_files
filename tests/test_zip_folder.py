"""Tests for `zip-folder` executable."""

from pathlib import Path
from zipfile import ZipFile

from click.testing import CliRunner
from pkg_resources import parse_version

from zip_files import __version__, zip_folder


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
  -f, --root-folder TEXT          Folder name to use as the top level folder
                                  inside the zip file (replacing FOLDER).
  -c, --compression [stored|deflated|bzip2|lzma]
                                  Zip compression method. The following methods
                                  are available: "stored": no compression;
                                  "deflated": the standard zip compression
                                  method; "bzip2": BZIP2 compression method
                                  (part of the zip standard since 2001); "lzma":
                                  LZMA compression method (part of the zip
                                  standard since 2006).  [default: deflated]
  -o, --outfile TEXT              The path of the zip file to be written. By
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
    assert result.stdout.strip() == _ZIP_FOLDER_EXPECTED_HELP


def test_zip_folder_simple(tmp_path):
    """Test a simple "zip-folder FOLDER"."""
    runner = CliRunner()
    outfile = tmp_path / 'simple.zip'
    folder = ROOT / 'user' / 'folder'
    result = runner.invoke(
        zip_folder, ['--debug', '-o', str(outfile), str(folder)],
    )
    _check_exit_code(result)
    with ZipFile(outfile) as zipfile:
        zipfile.debug = 3
        assert zipfile.testzip() is None
        assert set(zipfile.namelist()) == set(
            [
                'folder/Hello World.docx',
                'folder/hello.txt',
                "folder/My Documents/64px-Fishs & Schrödinger's cat.gif",
                'folder/My Documents/example-1.3.jar',
                'folder/My Documents/你好，世界.md',
            ]
        )


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
    with ZipFile(outfile) as zipfile:
        zipfile.debug = 3
        assert zipfile.testzip() is None
        assert set(zipfile.namelist()) == set(
            [
                'xyz/Hello World.docx',
                'xyz/hello.txt',
                "xyz/My Documents/64px-Fishs & Schrödinger's cat.gif",
                'xyz/My Documents/example-1.3.jar',
                'xyz/My Documents/你好，世界.md',
            ]
        )


def test_zip_folder_compression(tmp_path):
    """Test the different compressions."""
    runner = CliRunner()
    folder = (ROOT / 'user' / 'folder').resolve()
    with runner.isolated_filesystem():
        result = runner.invoke(
            zip_folder,
            [
                '--debug',
                '-o',
                'uncompressed.zip',
                '-c',
                'stored',
                str(folder),
            ],
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
        assert 'Invalid value for "--compression"' in result.output
