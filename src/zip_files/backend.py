"""Backend implementing the core functionality.

This handles the both the ``zip-files`` and the ``zip-folder`` command line
utility.
"""
import logging
import os
import random
import re
from pathlib import Path
from string import ascii_letters
from zipfile import ZipFile, ZipInfo

import click


try:
    # Python > 3.6
    from re import Pattern as RegexPattern
except ImportError:
    # Python 3.6
    from typing import Pattern as RegexPattern


__all__ = ['zip_files']

_VCS_EXCLUDES = [
    'CVS/*',
    'RCS/*',
    'SCCS/*',
    '.git/*',
    '.gitignore',
    '.gitmodules',
    '.gitattributes',
    '.cvsignore',
    '.svn/*',
    '.arch-ids/*',
    '{arch}/*',
    '=RELEASE-ID',
    '=meta-update',
    '=update',
    '.bzr',
    '.bzrignore',
    '.bzrtags',
    '.hg',
    '.hgignore',
    '.hgrags',
    '_darcs',
]


def gitignore_to_regex(prefix, pattern):
    """Convert a gitignore glob `pattern` into a regex string.

    See https://git-scm.com/docs/gitignore for the glob-style syntax that
    gitignore uses.

    The resulting regex will only match strings that start with `prefix` (a
    path string for a folder in which the `pattern` applies)
    """
    logger = logging.getLogger(__name__)

    # while the gitignore always uses forward-slashes as path separators, the
    # pathnames the regex must match does not: we have to use a
    # platform-dependent path separator in the regex we produce
    sep = re.escape(os.path.sep)

    # Normalize the pattern
    pattern = pattern.strip()
    if pattern.endswith("\\"):  # did we strip off '\ '?
        pattern = pattern + " "
    if "/" not in pattern[:-1]:
        # > A leading "**" followed by a slash means match in all
        # > directories. For example, "**/foo" matches file or directory
        # > "foo" anywhere, the same as pattern "foo"
        # That is, we can prepend "**/" without changing semantics
        pattern = "**/" + pattern
    if pattern.endswith("/"):
        # > If there is a separator at the end of the pattern then the pattern
        # > will only match directories, otherwise the pattern can match both
        # > files and directories.
        # However, "matching a directory" is equivalent to matching all
        # directories/files within it, so we can apend "**" without chaning
        # semantics
        pattern = pattern + "**"

    # Process all special characters in gitignore-style glob patterns.
    replacements = [  # map glob-patterns to equivalent regex
        # A leading "**" followed by a slash means match in all directories
        (re.compile(r'^\*\*/'), rf'(?:.*{sep})?'),
        # A trailing "/**" matches everything inside
        (re.compile(r'/\*\*$'), rf'{sep}.*$'),
        # A slash followed by two consecutive asterisks then a slash matches
        # zero or more directories
        (re.compile(r'/\*\*/'), rf'(?:{sep}[^{sep}]+)*{sep}?'),
        # An asterisk "*" matches anything except a slash.
        (re.compile(r'\*'), rf'[^{sep}]+'),
        # The character "?" matches any one character except "/" (path sep)
        (re.compile(r'\?'), rf'[^{sep}]'),
        # The character "/" is a path separator, independent of platform
        (re.compile(r'/'), sep),
        # The range notation, e.g. [a-zA-Z], can be used to match one of the
        # characters in a range. -- handled below, since it doesn't have a
        # fixed replacement.
    ]
    # Anything that involves a special regex character needs to be "protected":
    # we replace it with a random ascii-string and create a map of which regex
    # pattern the protected string should restored as
    protected_replacements = []
    protected_pattern = pattern
    for (rx, repl) in replacements:
        for glob_expr in rx.findall(pattern):
            prot_key = ''.join(random.choices(ascii_letters, k=32))
            protected_replacements.append((prot_key, repl))
            protected_pattern = protected_pattern.replace(glob_expr, prot_key)
    for range_expr in re.findall(r'\[.*?\]', pattern):  # [A-Za-z], [cod]
        prot_key = ''.join(random.choices(ascii_letters, k=32))
        protected_replacements.append((prot_key, range_expr))
        protected_pattern = protected_pattern.replace(range_expr, prot_key)

    # un-protect the pattern
    regex_pattern = re.escape(protected_pattern)
    for (prot_key, repl) in protected_replacements:
        regex_pattern = regex_pattern.replace(re.escape(prot_key), repl)
    if regex_pattern.startswith(sep):
        # strip of any leading `sep` so as to not conflict with the `sep` we
        # insert between prefix and pattern below
        regex_pattern = regex_pattern[len(sep) :]

    # To complete the regex, we anchor it with the prefix and allow trailing
    # subfolders/files
    regex = "^" + re.escape(prefix) + sep + regex_pattern + rf'(?:{sep}.*)?$'
    # fmt: off
    logger.debug(
        "Translating normalized gitignore pattern %r with prefix %r to "
        "regex %r:", pattern, prefix, regex,
    )
    # fmt: on

    return regex


def _get_single_gitignore_excludes(gitignore, relative_to, root_folder):
    """Return a list of excludes from the given .gitignore file.

    Args:
        gitignore (pathlib.Path): The location of the .gitignore file
        relative_to (pathlib.Path): The path to which `gitignore` (and the
            patterns therein) should be made relative
        root_folder (pathlib.Path): A folder to prepend to all "absolute"
            patterns.
    """
    if root_folder is None:
        root_folder = Path(".")
    with gitignore.open() as in_fh:
        exclude = []
        folder = gitignore.relative_to(relative_to).parent
        prefix = root_folder / folder
        for line in in_fh:
            if line.startswith("#") or line.strip() == "":
                # .gitignore files may contain comments
                continue
            if line.startswith("!"):
                click.echo(
                    "WARNING: Negated pattern %s in %s will be ignored"
                    % (line.strip(), gitignore),
                    err=True,
                )
                continue
            regex = gitignore_to_regex(str(prefix), line)
            exclude.append(re.compile(regex))
        return exclude


def _get_gitignore_excludes(path, root_folder, relative_to):
    """Return a list of excludes from all .gitignore files found in `path`."""
    exclude = []
    if path.is_dir():
        for gitignore in path.glob('**/.gitignore'):
            exclude += _get_single_gitignore_excludes(
                gitignore, root_folder=root_folder, relative_to=relative_to
            )
    elif path.name == ".gitignore":
        exclude += _get_single_gitignore_excludes(
            path, root_folder=root_folder, relative_to=relative_to
        )
    return exclude


def zip_files(
    debug,
    root_folder,
    compression,
    exclude,
    exclude_from,
    exclude_dotfiles,
    exclude_vcs,
    exclude_git_ignores,
    outfile,
    files,
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
        exclude_from (list[str]): A list of filenames from which to read
            exclude patterns (one pattern per line)
        exclude_dotfiles (bool): If given as True, exclude all files starting
            with a dot.
        exclude_vcs (bool): If given as True, exclude files and directories
            used by common version control systems (Git, CVS, RCS, SCCS, SVN,
            Arch, Bazaar, Mercurial, and Darcs), e.g.  '.git/', '.gitignore'
            '.gitmodules' '.gitattributes' for Git
        exclude_git_ignores (bool): If given as True, exclude files listed in
            any '.gitignore' in the given `files` or its subfolders.
        outfile (Path): The path of the zip file to be written
        files (Iterable[Path]): The files to include in the zip archive
    """
    logger = logging.getLogger(__name__)
    if debug:
        logger.setLevel(logging.DEBUG)
        logger.debug("Enabled debug output")
    files = list(files)  # generator->list, so we can consume it multiple times
    logger.debug("root_folder: %s", root_folder)
    logger.debug("Writing zip file to %s", outfile)
    if outfile is None or outfile == '--':
        logger.debug("Routing output to stdout (from %r)", outfile)
        outfile = click.get_binary_stream('stdout')
    exclude = list(exclude)  # make a copy
    for file in exclude_from:
        logger.debug("Reading exclude patterns from: %s", file)
        with open(file) as in_fh:
            exclude += in_fh.read().splitlines()
    if exclude_vcs:
        exclude += _VCS_EXCLUDES
    if exclude_git_ignores:
        for path in files:
            exclude += _get_gitignore_excludes(
                path, root_folder=root_folder, relative_to=path.parent
            )
    if len(exclude) > 0:
        logger.debug("Using effective excludes: %r", (exclude,))
    with ZipFile(outfile, mode='w', compression=compression) as zipfile:
        for file in files:
            _add_to_zip(
                zipfile,
                file,
                root_folder,
                exclude,
                exclude_dotfiles,
                relative_to=file.parent,
                compression=compression,
            )
    logger.debug("Done")


def _add_to_zip(
    zipfile,
    file,
    root_folder,
    exclude,
    exclude_dotfiles,
    relative_to,
    compression,
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
            if isinstance(pattern, RegexPattern):
                if pattern.match(str(filename)):
                    logger.debug(
                        "Skipping %s (exclude RX %r)",
                        filename,
                        pattern.pattern,
                    )
                    return
            elif isinstance(pattern, str):
                if filename.match(pattern):
                    logger.debug(
                        "Skipping %s (exclude pattern %r)", filename, pattern
                    )
                    return
            else:
                raise TypeError("Invalid type for pattern %r" % pattern)
        logger.debug("Adding %s to zip as %s", file, filename)
        zinfo = ZipInfo.from_file(file, arcname=str(filename))
        zinfo.compress_type = compression
        zipfile.writestr(zinfo, data)
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
                compression,
            )
