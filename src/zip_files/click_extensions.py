"""Project-specific extensions for `click`."""
import logging

import click


__all__ = ['DependsOn', 'activate_debug_logger', 'help_from_cmd']


class DependsOn(click.Option):
    """A custom click option that depends on other options."""

    def __init__(self, *args, **kwargs):
        self.depends_on = kwargs.pop('depends_on')
        self.incompatible_with = kwargs.pop('incompatible_with', [])
        super().__init__(*args, **kwargs)

    def handle_parse_result(self, ctx, opts, args):
        """Parse command line options (callback)."""
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


def activate_debug_logger():
    """Global logger used when running from command line."""
    logging.basicConfig(
        format='(%(levelname)s) %(message)s', level=logging.DEBUG
    )


def help_from_cmd(cmd):
    """Create a function to look up help from click `cmd`.

    The returned function takes a string `name` and returns the help text for
    the option with given `name` from the click-command `cmd`. This help with
    having the same options in multiple commands without having to repeat the
    documentation.
    """

    def _help(name):  # pragma: no cover
        """Help text for the given option in `cmd`."""
        for p in cmd.params:
            if p.name == name:
                if p.help is None:
                    raise ValueError("No help text available for %r" % name)
                return p.help
        raise ValueError("Unknown option: %r" % name)

    return _help
