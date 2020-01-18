"""``zip-files`` command line utility."""
from pathlib import Path
from zipfile import ZIP_BZIP2, ZIP_DEFLATED, ZIP_LZMA, ZIP_STORED

import click

from . import __version__
from .backend import zip_files as _zip_files
from .click_extensions import DependsOn, activate_debug_logger


__all__ = []


_COMPRESSION = {  # possible values for --compression
    'stored': ZIP_STORED,
    'deflated': ZIP_DEFLATED,
    'bzip2': ZIP_BZIP2,
    'lzma': ZIP_LZMA,
}


@click.command()
@click.help_option('--help', '-h')
@click.version_option(version=__version__)
@click.option('--debug', is_flag=True, help="Activate debug logging.")
@click.option(
    '--root-folder',
    '-f',
    metavar='ROOT_FOLDER',
    help="Folder name to prepend to FILES inside the zip file.",
)
@click.option(
    '--compression',
    '-c',
    type=click.Choice(list(_COMPRESSION.keys()), case_sensitive=False),
    default='deflated',
    show_default=True,
    help=(
        "Zip compression method. The following methods are available: "
        '"stored": no compression; '
        '"deflated": the standard zip compression method; '
        '"bzip2": BZIP2 compression method (part of the zip standard since '
        '2001); '
        '"lzma": LZMA compression method (part of the zip standard since '
        '2006).'
    ),
)
@click.option(
    '--auto-root',
    '-a',
    cls=DependsOn,
    depends_on='outfile',
    incompatible_with=['root_folder'],
    is_flag=True,
    help=(
        "If given in combination with --outfile, use the stem of the OUTFILE "
        "(without path and extension) as the value for ROOT_FOLDER"
    ),
)
@click.option(
    '--outfile',
    '-o',
    metavar='OUTFILE',
    help=(
        "The path of the zip file to be written. By default, the file is "
        "written to stdout."
    ),
)
@click.argument('files', nargs=-1, type=click.Path(exists=True, readable=True))
def zip_files(debug, auto_root, root_folder, compression, outfile, files):
    """Create a zip file containing FILES."""
    if debug:
        activate_debug_logger()
    files = [Path(f) for f in files]
    if auto_root:
        root_folder = Path(outfile).stem
    _zip_files(
        debug, root_folder, _COMPRESSION[compression.lower()], outfile, files
    )
