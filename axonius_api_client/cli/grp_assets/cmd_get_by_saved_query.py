# -*- coding: utf-8 -*-
"""Command line interface for Axonius API Client."""
from ..context import CONTEXT_SETTINGS, click
from ..options import add_options
from .grp_common import get_handler as handler
from .grp_options import GET_SQ as OPTIONS

METHOD = "get-by-saved-query"


@click.command(name=METHOD, context_settings=CONTEXT_SETTINGS)
@add_options(OPTIONS)
@click.pass_context
def cmd(ctx, url, key, secret, **kwargs):
    """Get assets using a saved query."""
    handler(ctx=ctx, url=url, key=key, secret=secret, method=METHOD, **kwargs)
