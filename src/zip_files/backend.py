"""Backend implementing the core functionality.

This handles the both the ``zip-files`` and the ``zip-folder`` command line
utility.
"""
import logging
from zipfile import ZipFile

import click


__all__ = ['zip_files']


def zip_files(
    debug, root_folder, compression, exclude, exclude_dotfiles, outfile, files
):
    """Compress list of `files`.

    Args:
        debug (bool): Whether to show debug logging.
        root_folder (Path or None): folder name to prepend to `files` inside
            the zip archive
        compression (int): Zip compression. One of :obj:`zipfile.ZIP_STORED`
            :obj:`zipfile.ZIP_DEFLATED`, :obj:`zipfile.ZIP_BZIP2`,
            :obj:`zipfile.ZIP_LZMA`
        exclude (list[str]): A list of glob patterns to exclude. Matching is
            done from the right on the path names inside the zip archive.
            Patterns must be relative (not start with a slash)
        exclude_dotfiles (bool): If given as True, exclude all files starting
            with a dot.
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
            _add_to_zip(
                zipfile,
                file,
                root_folder,
                exclude,
                exclude_dotfiles,
                relative_to=file.parent,
            )
    logger.debug("Done")


def _add_to_zip(
    zipfile, file, root_folder, exclude, exclude_dotfiles, relative_to
):
    """Recursively add the `file` to the (open) `zipfile`."""
    logger = logging.getLogger(__name__)
    if file.is_file():
        if root_folder is None:
            filename = file.relative_to(relative_to)
        else:
            filename = root_folder / file.relative_to(relative_to)
        data = file.read_bytes()
        if exclude_dotfiles and filename.stem.startswith("."):
            logger.debug("Skipping %s (exclude dotfiles)", filename)
            return
        for pattern in exclude:
            if filename.match(pattern):
                logger.debug(
                    "Skipping %s (exclude pattern %s)", filename, pattern
                )
                return
        logger.debug("Adding %s to zip as %s", file, filename)
        zipfile.writestr(str(filename), data)
    elif file.is_dir():
        directory = file
        for file_in_dir in directory.iterdir():
            _add_to_zip(
                zipfile,
                file_in_dir,
                root_folder,
                exclude,
                exclude_dotfiles,
                relative_to,
            )
