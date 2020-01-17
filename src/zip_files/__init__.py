"""Command line utilities for creating zip files."""
from pathlib import Path
import logging
from zipfile import ZipFile, ZIP_STORED, ZIP_DEFLATED, ZIP_BZIP2, ZIP_LZMA

import click


__version__ = '0.1.0+dev'

__all__ = []


def _zip_files(debug, root_folder, compression, outfile, files):
    """Compress list of `files`.

    Args:
        debug (bool): Whether to show debug logging.
        root_folder (Path): folder name to prepend to `files` inside the zip
            archive
        compression (int): Zip compression. One of :obj:`zipfile.ZIP_STORED`
            :obj:`zipfile.ZIP_DEFLATED`, :obj:`zipfile.ZIP_BZIP2`,
            :obj:`zipfile.ZIP_LZMA`
        outfile (Path): The path of the zip file to be written
        files (List[Path]): The files to include in the zip archive
    """
    logger = logging.getLogger(__name__)
    if debug:
        logger.setLevel(logging.DEBUG)
        logger.debug("Enabled debug output")
    logger.debug("root_folder: %s", root_folder)
    logger.debug("Writing zip file to %s", outfile)
    if outfile is None or outfile == '--':
        logger.debug("Routing output to stdout (from %r)", outfile)
        outfile = click.get_binary_stream('stdout')
    with ZipFile(outfile, mode='w', compression=compression) as zipfile:
        for file in files:
            _add_to_zip(zipfile, file, root_folder, relative_to=file.parent)
    logger.debug("Done")


def _add_to_zip(zipfile, file, root_folder, relative_to):
    """Recursively add the `file` to the (open) `zipfile`."""
    logger = logging.getLogger(__name__)
    if file.is_file():
        if root_folder is None:
            filename = str(file.relative_to(relative_to))
        else:
            filename = str(root_folder / file.relative_to(relative_to))
        logger.debug("Adding %s to zip as %s", file, filename)
        data = file.read_bytes()
        zipfile.writestr(filename, data)
    elif file.is_dir():
        directory = file
        for file in directory.iterdir():
            _add_to_zip(zipfile, file, root_folder, relative_to)


def _activate_debug_logger():
    logging.basicConfig(
        format='(%(levelname)s) %(message)s', level=logging.DEBUG
    )


_COMPRESSION = {
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
    '--outfile',
    '-o',
    help=(
        "The path of the zip file to be written. By default, the file is "
        "written to stdout."
    ),
)
@click.argument('files', nargs=-1, type=click.Path(exists=True, readable=True))
def zip_files(debug, root_folder, compression, outfile, files):
    """Create a zip file containing FILES."""
    if debug:
        _activate_debug_logger()
    files = [Path(f) for f in files]
    _zip_files(
        debug, root_folder, _COMPRESSION[compression.lower()], outfile, files
    )


def _help(name):  # pragma: no cover
    """Help text for the given option in the ``zip-files`` command.

    Just so we don't have to repeat ourselves.
    """
    for p in zip_files.params:
        if p.name == name:
            if p.help is None:
                raise ValueError("No help text available for %r" % name)
            return p.help
    raise ValueError("Unknown option: %r" % name)


@click.command()
@click.help_option('--help', '-h')
@click.version_option(version=__version__)
@click.option('--debug', is_flag=True, help=_help('debug'))
@click.option(
    '--root-folder',
    '-f',
    help=(
        "Folder name to use as the top level folder inside the zip file "
        "(replacing FOLDER)."
    ),
)
@click.option(
    '--compression',
    '-c',
    type=click.Choice(list(_COMPRESSION.keys()), case_sensitive=False),
    default='deflated',
    show_default=True,
    help=_help('compression'),
)
@click.option('--outfile', '-o', help=_help('outfile'))
@click.argument(
    'folder',
    nargs=1,
    type=click.Path(file_okay=False, exists=True, readable=True),
)
def zip_folder(debug, root_folder, compression, outfile, folder):
    """Create a zip file containing the FOLDER."""
    if debug:
        _activate_debug_logger()
    files = Path(folder).iterdir()
    if root_folder is None:
        root_folder = Path(folder).name
    _zip_files(
        debug, root_folder, _COMPRESSION[compression.lower()], outfile, files,
    )
