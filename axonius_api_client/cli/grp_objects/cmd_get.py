# -*- coding: utf-8 -*-
"""Command line interface for Axonius API Client."""
from __future__ import absolute_import, division, print_function, unicode_literals

import click

from .. import context


@click.command("get", context_settings=context.CONTEXT_SETTINGS)
@context.OPT_URL
@context.OPT_KEY
@context.OPT_SECRET
@context.OPT_EXPORT_FILE
@context.OPT_EXPORT_PATH
@context.OPT_EXPORT_FORMAT
@context.OPT_EXPORT_OVERWRITE
@context.OPT_QUERY
@context.OPT_FIELDS
@context.OPT_FIELDS_DEFAULT
@context.OPT_MAX_ROWS
@context.pass_context
@click.pass_context
def cmd(
    clickctx,
    ctx,
    url,
    key,
    secret,
    export_format,
    export_file,
    export_path,
    export_overwrite,
    query,
    fields,
    fields_default,
    max_rows,
):
    """Get all objects matching a query."""
    client = ctx.start_client(url=url, key=key, secret=secret)

    api = getattr(client, clickctx.parent.command.name)

    with context.exc_wrap(wraperror=ctx.wraperror):
        raw_data = api.get(
            query=query, fields=fields, fields_default=fields_default, max_rows=max_rows
        )

    formatters = {"json": context.to_json, "csv": context.obj_to_csv}

    ctx.handle_export(
        raw_data=raw_data,
        formatters=formatters,
        export_format=export_format,
        export_file=export_file,
        export_path=export_path,
        export_overwrite=export_overwrite,
    )
