# -*- coding: utf-8 -*-
"""Command line interface for Axonius API Client."""
from __future__ import absolute_import, division, print_function, unicode_literals

import click

from ... import tools
from .. import context
from . import grp_common


@click.command("check", context_settings=context.CONTEXT_SETTINGS)
@context.OPT_URL
@context.OPT_KEY
@context.OPT_SECRET
@context.OPT_EXPORT_FILE
@context.OPT_EXPORT_PATH
@context.OPT_EXPORT_FORMAT
@context.OPT_EXPORT_OVERWRITE
@context.OPT_INCLUDE_SETTINGS
@context.OPT_NO_ERROR
@click.option(
    "--rows",
    "-r",
    "rows",
    help="The output from 'cnx get' supplied as a file or via stdin.",
    default="-",
    type=click.File(mode="r"),
    show_envvar=True,
)
@context.pass_context
def cmd(
    ctx,
    url,
    key,
    secret,
    export_format,
    export_file,
    export_path,
    export_overwrite,
    rows,
    error,
    include_settings,
):
    """Get all adapters with clients that have errors."""
    client = ctx.start_client(url=url, key=key, secret=secret)
    content = context.json_from_stream(ctx=ctx, stream=rows, src="--rows")

    cnxs = tools.listify(obj=content, dictkeys=False)

    msg = "Loaded {nc} connections from --rows"
    msg = msg.format(nc=len(cnxs))
    ctx.echo_ok(msg)

    processed = []

    with context.exc_wrap(wraperror=ctx.wraperror):
        for cnx in cnxs:
            if "cnx" in cnx:
                cnx = cnx["cnx"]

            raw_data = client.adapters.cnx.check(cnx=cnx, error=error)
            grp_common.handle_response(cnx=raw_data, action="checking")
            processed.append(raw_data)

    formatters = {"json": context.to_json, "csv": grp_common.to_csv}

    ctx.handle_export(
        raw_data=processed,
        formatters=formatters,
        export_format=export_format,
        export_file=export_file,
        export_path=export_path,
        export_overwrite=export_overwrite,
        include_settings=include_settings,
    )
