"""Guard against sub-commands that are registered but never wired to a handler.

`zot attachments upload` shipped without its `set_defaults(func=...)` call and
died with `AttributeError: 'Namespace' object has no attribute 'func'`. Walking
the parser tree catches that class of mistake without running any command.
"""

from zotero_client.cli.main import build_parser


def _subparser_choices(parser):
    """Return the {name: parser} map for a parser that owns sub-commands."""
    for action in parser._actions:
        choices = getattr(action, 'choices', None)
        if isinstance(choices, dict):
            return choices
    return {}


def _leaf_commands(parser, path=()):
    """Yield (path, parser) for every command that does not own sub-commands."""
    choices = _subparser_choices(parser)
    if not choices:
        yield path, parser
        return
    for name, subparser in choices.items():
        yield from _leaf_commands(subparser, path + (name,))


def test_every_leaf_command_has_a_handler():
    leaves = list(_leaf_commands(build_parser()))

    assert leaves, "parser tree contained no leaf commands"

    unwired = [
        ' '.join(path) for path, leaf in leaves if 'func' not in leaf._defaults
    ]
    assert unwired == [], f"sub-commands registered without a handler: {unwired}"
