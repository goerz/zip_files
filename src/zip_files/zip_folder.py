"""``zip-folder`` command line utility."""
from pathlib import Path

import click

from . import __version__
from .backend import zip_files as _zip_files
from .click_extensions import DependsOn, activate_debug_logger, help_from_cmd
from .zip_files import _COMPRESSION, zip_files


__all__ = []


_help = help_from_cmd(zip_files)


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
    cls=DependsOn,
    depends_on='outfile',
    incompatible_with=['root_folder'],
    is_flag=True,
    help=_help('auto_root'),
)
@click.option(
    '--exclude',
    '-x',
    multiple=True,
    metavar='GLOB_PATTERN',
    help=_help('exclude'),
)
@click.option(
    '--exclude-from',
    '-X',
    multiple=True,
    metavar="FILE",
    type=click.Path(exists=True),
    help=_help('exclude_from'),
)
@click.option(
    '--exclude-dotfiles/--include-dotfiles',
    default=False,
    help=_help('exclude_dotfiles'),
)
@click.option(
    '--exclude-vcs/--include-vcs',
    default=False,
    help=_help('exclude_vcs'),
)
@click.option(
    '--exclude-git-ignores/--include-git-ignores',
    default=False,
    help=_help('exclude_git_ignores'),
)
@click.option('--outfile', '-o', metavar='OUTFILE', help=_help('outfile'))
@click.argument(
    'folder',
    nargs=1,
    type=click.Path(file_okay=False, exists=True, readable=True),
)
def zip_folder(
    debug,
    auto_root,
    root_folder,
    compression,
    exclude,
    exclude_from,
    exclude_dotfiles,
    exclude_vcs,
    exclude_git_ignores,
    outfile,
    folder,
):
    """Create a zip file containing the FOLDER."""
    if debug:
        activate_debug_logger()
    files = Path(folder).iterdir()
    if root_folder is None:
        root_folder = Path(folder).name
        if auto_root:
            root_folder = Path(outfile).stem
    _zip_files(
        debug=debug,
        root_folder=root_folder,
        compression=_COMPRESSION[compression.lower()],
        exclude=exclude,
        exclude_from=exclude_from,
        exclude_dotfiles=exclude_dotfiles,
        exclude_vcs=exclude_vcs,
        exclude_git_ignores=exclude_git_ignores,
        outfile=outfile,
        files=files,
    )
