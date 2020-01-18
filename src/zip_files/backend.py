"""Backend implementing the core functionality.

This handles the both the ``zip-files`` and the ``zip-folder`` command line
utility.
"""
import logging
from zipfile import ZipFile

import click


__all__ = ['zip_files']


def zip_files(debug, root_folder, compression, outfile, files):
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
