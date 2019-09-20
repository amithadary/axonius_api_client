# -*- coding: utf-8 -*-
"""Command line interface for Axonius API Client."""
from __future__ import absolute_import, division, print_function, unicode_literals

import click

from .. import context


@click.command(name="get", context_settings=context.CONTEXT_SETTINGS)
@context.OPT_URL
@context.OPT_KEY
@context.OPT_SECRET
@context.OPT_EXPORT_FILE
@context.OPT_EXPORT_PATH
@context.OPT_EXPORT_FORMAT
@context.OPT_EXPORT_OVERWRITE
@context.OPT_INCLUDE_SETTINGS
@click.option(
    "--name",
    "-n",
    "names",
    help="Only include adapters with matching names.",
    multiple=True,
    show_envvar=True,
    show_default=True,
)
@click.option(
    "--node",
    "-no",
    "nodes",
    help="Only include adapters with matching node names.",
    multiple=True,
    show_envvar=True,
    show_default=True,
)
@click.option(
    "--no-cnx-working",
    "-ncw",
    "cnx_working",
    help="Exclude adapters with working connections.",
    is_flag=True,
    default=True,
    show_envvar=True,
    show_default=True,
)
@click.option(
    "--no-cnx-broken",
    "-ncb",
    "cnx_broken",
    help="Exclude adapters with broken connections.",
    is_flag=True,
    default=True,
    show_envvar=True,
    show_default=True,
)
@click.option(
    "--no-cnx-none",
    "-ncn",
    "cnx_none",
    help="Exclude adapters with no connections.",
    default=True,
    is_flag=True,
    show_envvar=True,
    show_default=True,
)
@click.option(
    "--cnx-count",
    "-c",
    "cnx_count",
    help="Only include adapters with this number of connections.",
    type=click.INT,
    show_envvar=True,
    show_default=True,
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
    names,
    nodes,
    cnx_working,
    cnx_broken,
    cnx_none,
    cnx_count,
    include_settings,
):
    """Get adapters based on name, node name, and connection status or count."""
    client = ctx.start_client(url=url, key=key, secret=secret)

    statuses = []

    if cnx_working:
        statuses.append(True)

    if cnx_broken:
        statuses.append(False)

    if cnx_none:
        statuses.append(None)

    with context.exc_wrap(wraperror=ctx.wraperror):
        all_adapters = client.adapters.get()

        by_nodes = client.adapters.filter_by_nodes(adapters=all_adapters, value=nodes)
        context.check_empty(
            ctx=ctx,
            this_data=by_nodes,
            prev_data=all_adapters,
            value_type="node names",
            value=nodes,
            objtype="adapters",
            known_cb=ctx.obj.adapters.get_known,
            known_cb_key="adapters",
        )

        by_names = client.adapters.filter_by_names(adapters=by_nodes, value=names)
        context.check_empty(
            ctx=ctx,
            this_data=by_names,
            prev_data=by_nodes,
            value_type="names",
            value=names,
            objtype="adapters",
            known_cb=ctx.obj.adapters.get_known,
            known_cb_key="adapters",
        )

        by_statuses = client.adapters.filter_by_status(
            adapters=by_names, value=statuses
        )
        context.check_empty(
            ctx=ctx,
            this_data=by_statuses,
            prev_data=by_names,
            value_type="statuses",
            value=statuses,
            objtype="adapters",
            known_cb=ctx.obj.adapters.get_known,
            known_cb_key="adapters",
        )

        by_cnx_count = client.adapters.filter_by_cnx_count(
            adapters=by_names, value=cnx_count
        )
        context.check_empty(
            ctx=ctx,
            this_data=by_cnx_count,
            prev_data=by_statuses,
            value_type="connection count",
            value=cnx_count,
            objtype="adapters",
            known_cb=ctx.obj.adapters.get_known,
            known_cb_key="adapters",
        )

    formatters = {"json": context.to_json, "csv": to_csv}
    ctx.handle_export(
        raw_data=by_cnx_count,
        formatters=formatters,
        export_format=export_format,
        export_file=export_file,
        export_path=export_path,
        export_overwrite=export_overwrite,
        include_settings=include_settings,
    )


def to_csv(ctx, raw_data, include_settings=True, **kwargs):
    """Pass."""
    rows = []

    simples = [
        "name",
        "node_name",
        "node_id",
        "status_raw",
        "cnx_count",
        "cnx_count_ok",
        "cnx_count_bad",
    ]

    cnx_tmpl = "cnx{idx}_{t}".format

    for adapter in raw_data:
        row = {k: adapter[k] for k in simples}

        for idx, cnx in enumerate(adapter["cnx"]):
            status = [
                "status: {}".format(cnx["status_raw"]),
                "error: {}".format(cnx["error"]),
            ]

            row[cnx_tmpl(idx=idx, t="id")] = cnx["id"]
            row[cnx_tmpl(idx=idx, t="status")] = context.join_cr(status)

            if include_settings:
                row[cnx_tmpl(idx=idx, t="settings")] = context.join_tv(cnx["config"])

        if include_settings:
            row["adapter_settings"] = context.join_tv(adapter["settings"])
            row["advanced_settings"] = context.join_tv(adapter["adv_settings"])

        rows.append(row)

    return context.dictwriter(rows=rows)
