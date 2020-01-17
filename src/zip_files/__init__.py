"""Command line utilities for creating zip files."""
from pathlib import Path
import logging
from zipfile import ZipFile, ZIP_STORED, ZIP_DEFLATED, ZIP_BZIP2, ZIP_LZMA

import click


__version__ = '0.2.0'

__all__ = []


def _zip_files(debug, root_folder, compression, outfile, files):
    """Compress list of `files`.

    Args:
        debug (bool): Whether to show debug logging.
        root_folder (Path or None): folder name to prepend to `files` inside
            the zip archive
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
        for file_in_dir in directory.iterdir():
            _add_to_zip(zipfile, file_in_dir, root_folder, relative_to)


def _activate_debug_logger():
    """Global logger used when running from command line."""
    logging.basicConfig(
        format='(%(levelname)s) %(message)s', level=logging.DEBUG
    )


class _DependsOn(click.Option):
    """A custom click option that depends on other options."""

    def __init__(self, *args, **kwargs):
        self.depends_on = kwargs.pop('depends_on')
        self.incompatible_with = kwargs.pop('incompatible_with', [])
        super().__init__(*args, **kwargs)

    def handle_parse_result(self, ctx, opts, args):
        """Parsing callback."""
        if self.name in opts:
            if self.depends_on not in opts:
                raise click.UsageError(
                    "%s requires %s"
                    % (
                        self._fmt_opt(self.name),
                        self._fmt_opt(self.depends_on),
                    )
                )
            for name in self.incompatible_with:
                if name in opts:
                    raise click.UsageError(
                        "%s is incompatible with %s"
                        % (self._fmt_opt(self.name), self._fmt_opt(name))
                    )
        return super().handle_parse_result(ctx, opts, args)

    @staticmethod
    def _fmt_opt(name):
        """'auto_root' -> '--auto-root'."""
        return "--" + name.replace("_", "-")


_COMPRESSION = {  # possible values for --compression
    'stored': ZIP_STORED,
    'deflated': ZIP_DEFLATED,
    'bzip2': ZIP_BZIP2,
    'lzma': ZIP_LZMA,
}


# zip-files ###################################################################


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
    cls=_DependsOn,
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
        _activate_debug_logger()
    files = [Path(f) for f in files]
    if auto_root:
        root_folder = Path(outfile).stem
    _zip_files(
        debug, root_folder, _COMPRESSION[compression.lower()], outfile, files
    )


# #############################################################################


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


# zip-folder ##################################################################


@click.command()
@click.help_option('--help', '-h')
@click.version_option(version=__version__)
@click.option('--debug', is_flag=True, help=_help('debug'))
@click.option(
    '--root-folder',
    '-f',
    metavar='ROOT_FOLDER',
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
@click.option(
    '--auto-root',
    '-a',
    cls=_DependsOn,
    depends_on='outfile',
    incompatible_with=['root_folder'],
    is_flag=True,
    help=_help('auto_root'),
)
@click.option('--outfile', '-o', metavar='OUTFILE', help=_help('outfile'))
@click.argument(
    'folder',
    nargs=1,
    type=click.Path(file_okay=False, exists=True, readable=True),
)
def zip_folder(debug, auto_root, root_folder, compression, outfile, folder):
    """Create a zip file containing the FOLDER."""
    if debug:
        _activate_debug_logger()
    files = Path(folder).iterdir()
    if root_folder is None:
        root_folder = Path(folder).name
        if auto_root:
            root_folder = Path(outfile).stem
    _zip_files(
        debug, root_folder, _COMPRESSION[compression.lower()], outfile, files,
    )


# #############################################################################
