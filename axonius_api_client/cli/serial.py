# -*- coding: utf-8 -*-
"""Command line interface for Axonius API Client."""
from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import csv
import json
import os
import sys

import tabulate
from axonius_api_client import constants

from .. import tools
from ..libext import jsonstreams
from . import cli_constants, context


def ensure_keys(rows, this_cmd, src_cmds, keys, all_items=True):
    """Pass."""
    for idx, row in enumerate(rows):
        for key in keys:
            if key not in row:
                ensure_srcs(this_cmd=this_cmd, src_cmds=src_cmds)

                msg = [
                    "",
                    "Item #{i} in input to {tc!r} is missing key {k!r}",
                    "Item has keys: {hks}",
                    "Item must have keys: {ks}",
                    "",
                ]
                msg = tools.join_cr(obj=msg).format(
                    i=idx + 1, tc=this_cmd, k=key, ks=keys, hks=list(row)
                )
                context.click_echo_error(msg=msg, abort=True)

        if not all_items:
            break


def ensure_srcs_msg(this_cmd, src_cmds):
    """Pass."""
    psrc = "The input for {tc!r} must be the JSON output from one of these commands:"
    srcs = ["", psrc.format(tc=this_cmd), ""] + src_cmds + [""]
    return tools.join_cr(obj=srcs)


def ensure_srcs(this_cmd, src_cmds, err=True):
    """Pass."""
    msg = ensure_srcs_msg(this_cmd=this_cmd, src_cmds=src_cmds)
    echo = context.click_echo_error if err else context.click_echo_ok
    echo(msg=msg, abort=False)


def check_rows_type(rows, this_cmd, src_cmds, all_items=True):
    """Pass."""
    for idx, row in enumerate(rows):
        if not isinstance(row, dict):
            ensure_srcs(this_cmd=this_cmd, src_cmds=src_cmds)

            msg = "Item #{i} in input to {tc!r} is type {t}, must be a dictionary!"
            msg = msg.format(i=idx + 1, tc=this_cmd, t=type(row).__name__)
            context.click_echo_error(msg=msg, abort=True)

        if not all_items:
            break


def json_to_rows(ctx, stream, this_cmd, src_cmds):
    """Pass."""
    stream_name = format(getattr(stream, "name", stream))

    if stream.isatty():
        # its STDIN with no input
        ensure_srcs(this_cmd=this_cmd, src_cmds=src_cmds)

        msg = "No input provided on {s!r} for {tc!r}"
        msg = msg.format(s=stream_name, tc=this_cmd)
        context.click_echo_error(msg=msg, abort=True)

    # its STDIN with input or a file
    content = stream.read()
    msg = "Read {n} bytes from {s!r} for {tc!r}"
    msg = msg.format(n=len(content), s=stream_name, tc=this_cmd)
    context.click_echo_ok(msg=msg)

    content = content.strip()

    if not content:
        ensure_srcs(this_cmd=this_cmd, src_cmds=src_cmds)

        msg = "Empty content supplied in {s!r} for {tc!r}"
        msg = msg.format(s=stream_name, tc=this_cmd)
        context.click_echo_error(msg=msg, abort=True)

    with ctx.obj.exc_wrap(wraperror=ctx.obj.wraperror):
        rows = tools.json_load(obj=content)

    msg = "Loaded JSON rows as {t} with length of {n} for {tc!r}"
    msg = msg.format(t=type(rows).__name__, tc=this_cmd, n=len(rows))
    context.click_echo_ok(msg=msg)

    return tools.listify(obj=rows, dictkeys=False)


def collapse_rows(rows, key):
    """Pass."""
    new_rows = []
    for row in rows:
        if key in row:
            new_rows += tools.listify(obj=row[key], dictkeys=False)
        else:
            new_rows.append(row)
    return new_rows


def join_kv(obj, indent="  ", joiner="\n"):
    """Pass."""
    items = [cli_constants.KV_TMPL.format(k=k, v=v) for k, v in obj.items()]
    return tools.join_cr(obj=items, indent=indent, joiner=joiner)


def join_tv(obj, joiner="\n"):
    """Pass."""
    items = [
        cli_constants.KV_TMPL.format(k=v["title"], v=v["value"]) for k, v in obj.items()
    ]
    return join_cr(obj=items, joiner=joiner)


def join_cr(obj, is_cell=False, joiner="\n"):
    """Pass."""
    str_obj = tools.join_cr(obj=obj, pre=False, post=False, indent="", joiner=joiner)
    max_len = cli_constants.MAX_LEN

    if is_cell and len(str_obj) >= max_len:
        max_str = cli_constants.MAX_STR.format(c=len(obj), mc=max_len)
        str_obj = [str_obj[:max_len], max_str]
        str_obj = tools.join_cr(obj=str_obj)

    return str_obj


def dictwriter(rows, stream=None, headers=None, quoting=cli_constants.QUOTING, **kwargs):
    """Pass."""
    fh = stream or tools.six.StringIO()

    headers = headers or []

    if not headers:
        for row in rows:
            headers += [k for k in row if k not in headers]

    writer = csv.DictWriter(fh, fieldnames=headers, quoting=quoting, **kwargs)

    writer.writeheader()

    for row in rows:
        writer.writerow(row)

    return fh.getvalue()


def to_json(raw_data, **kwargs):
    """Pass."""
    return tools.json_dump(obj=raw_data)


def is_simple(o):
    """Is simple."""
    return isinstance(o, constants.SIMPLE) or o is None


def is_list(o):
    """Is simple."""
    return isinstance(o, constants.LIST)


def is_los(o):
    """Is simple or list of simples."""
    return is_simple(o) or (is_list(o) and all([is_simple(x) for x in o]))


def is_dos(o):
    """Is dict with simple or list of simple values."""
    return isinstance(o, dict) and all([is_los(v) for v in o.values()])


def compress_rows(raw_data, joiner="\n", **kwargs):
    """Pass."""
    raw_data = tools.listify(obj=raw_data, dictkeys=False)
    rows = []

    for raw_row in raw_data:
        row = {}
        rows.append(row)
        for raw_key, raw_value in raw_row.items():

            if is_los(raw_value):
                row[raw_key] = join_cr(raw_value, is_cell=True, joiner=joiner)
                continue

            if is_list(raw_value) and all([is_dos(x) for x in raw_value]):
                values = {}

                for raw_item in raw_value:
                    for k, v in raw_item.items():
                        new_key = "{}.{}".format(raw_key, k)

                        values[new_key] = values.get(new_key, [])

                        values[new_key] += tools.listify(v, dictkeys=False)

                for k, v in values.items():
                    row[k] = join_cr(v, is_cell=True, joiner=joiner)

                continue

            msg = "Data of type {t} is too complex for this export format"
            msg = msg.format(t=type(raw_value).__name__)
            row[raw_key] = msg
    return rows


def obj_to_csv(raw_data, **kwargs):
    """Pass."""
    joiner = kwargs.get("export_delim", cli_constants.EXPORT_DELIM)
    rows = compress_rows(raw_data=raw_data, joiner=joiner, **kwargs)
    data = dictwriter(rows=rows)
    return data


def obj_to_table(raw_data, **kwargs):
    """Pass."""
    tablfmt = kwargs.get("export_table_format", cli_constants.EXPORT_TABLE_FORMAT)
    joiner = kwargs.get("export_delim", cli_constants.EXPORT_DELIM)

    if tablfmt not in tabulate.tabulate_formats:
        msg = "{tf!r} is not a valid table format, must be one of {tfs}"
        msg = msg.format(tf=tablfmt, tfs=tools.join_comma(obj=tabulate.tabulate_formats))
        context.click_echo_error(msg=msg, abort=True)

    rows = compress_rows(raw_data=raw_data, joiner=joiner, **kwargs)
    data = tabulate.tabulate(
        tabular_data=rows, tablefmt=tablfmt, showindex=False, headers="keys"
    )
    return data


class JsonStream(object):
    """Wrap jsonstreams.Stream object."""

    def __init__(self, **kwargs):
        """Wrap jsonstreams.Stream object."""
        self._kwargs = kwargs
        self._export_file = kwargs.get("export_file", None)
        self._export_path = kwargs.get("export_path", None)
        self._export_overwrite = kwargs.get("export_overwrite", False)
        self._full_path = None

        if "fd" in kwargs:
            self._fd_close = kwargs.get("fd_close", True)
            self.__fd = kwargs["fd"]
        elif self._export_file:
            self._export_path = self._export_path or os.getcwd()
            path = tools.path(obj=self._export_path)
            path.mkdir(mode=0o700, parents=True, exist_ok=True)
            self._full_path = path / self._export_file
            self._mode = "overwrote" if self._full_path.exists() else "created"

            if self._full_path.exists() and not self._export_overwrite:
                msg = "Export file {p} already exists and export-overwite is False!"
                msg = msg.format(p=self._full_path)
                context.click_echo_error(msg)

            self._full_path.touch(mode=0o600)
            self._fd_close = True
            self.__fd = self._full_path.open(mode="w")
        else:
            self._fd_close = False
            self.__fd = sys.stdout

        encoder = kwargs.get("encoder", json.JSONEncoder)
        indent = kwargs.get("indent", 2)

        self.__inst = jsonstreams.Array(
            fd=self.__fd,
            indent=indent,
            baseindent=0,
            encoder=encoder(indent=indent),
            pretty=kwargs.get("pretty", True),
        )

        self.subobject = self.__inst.subobject
        self.subarray = self.__inst.subarray

    def close(self):
        """Close the root element and print a message."""
        self.__inst.close()

        if self._fd_close:
            self.__fd.close()

        if self._full_path:
            msg = "Exported assets to path {!r} ({} file)"
            msg = msg.format(format(self._full_path), self._mode)
            context.click_echo_ok(msg)

    def write(self, *args, **kwargs):
        """Write values into the stream."""
        self.__inst.write(*args, **kwargs)

    def iterwrite(self, *args, **kwargs):
        """Write values into the streams from an iterator."""
        self.__inst.iterwrite(*args, **kwargs)

    def __enter__(self):
        """Start context manager."""
        return self

    def __exit__(self, etype, evalue, traceback):
        """Exit context manager."""
        self.close()
