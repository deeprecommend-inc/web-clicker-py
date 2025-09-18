#!/usr/bin/env python3
import argparse
import json
import os
import re
import sys
from typing import Any, Dict, Optional, Tuple

import requests


FIGMA_API_BASE = "https://api.figma.com/v1"


def get_token(cli_token: Optional[str]) -> str:
    token = cli_token or os.getenv("FIGMA_TOKEN")
    if not token:
        print("Error: Provide --token or set FIGMA_TOKEN env var", file=sys.stderr)
        sys.exit(2)
    return token


def parse_file_key(arg: Optional[str], url: Optional[str]) -> str:
    if arg:
        return arg
    if not url:
        print("Error: Provide --file-key or --url", file=sys.stderr)
        sys.exit(2)
    # Parse https://www.figma.com/:file_type/:file_key/:file_name
    m = re.search(r"figma\.com/[^/]+/([a-zA-Z0-9_-]+)/", url)
    if not m:
        print("Error: Could not parse file key from URL", file=sys.stderr)
        sys.exit(2)
    return m.group(1)


def parse_node_id_from_url(url: str) -> Optional[str]:
    # https://www.figma.com/file/<key>/<name>?node-id=<id>
    m = re.search(r"[?&]node-id=([^&#]+)", url)
    return m.group(1) if m else None


def request_figma(
    method: str,
    path: str,
    token: str,
    params: Optional[Dict[str, Any]] = None,
    json_body: Optional[Dict[str, Any]] = None,
) -> Tuple[int, Dict[str, Any]]:
    headers = {"X-FIGMA-TOKEN": token}
    url = f"{FIGMA_API_BASE}{path}"
    resp = requests.request(method, url, headers=headers, params=params, json=json_body, timeout=60)
    try:
        data = resp.json()
    except Exception:
        data = {"raw": resp.text}
    return resp.status_code, data


def dump_output(data: Dict[str, Any], output: Optional[str]) -> None:
    if output:
        with open(output, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    else:
        json.dump(data, sys.stdout, ensure_ascii=False, indent=2)
        sys.stdout.write("\n")


def cmd_file(args: argparse.Namespace) -> None:
    token = get_token(args.token)
    key = parse_file_key(args.file_key, args.url)
    params: Dict[str, Any] = {}
    if args.version:
        params["version"] = args.version
    if args.ids:
        params["ids"] = args.ids
    if args.depth is not None:
        params["depth"] = args.depth
    if args.geometry:
        params["geometry"] = args.geometry
    if args.plugin_data:
        params["plugin_data"] = args.plugin_data
    if args.branch_data:
        params["branch_data"] = "true"
    status, data = request_figma("GET", f"/files/{key}", token, params=params)
    if status >= 400:
        print(f"Error {status}: {data}", file=sys.stderr)
        sys.exit(1)
    dump_output(data, args.output)


def cmd_nodes(args: argparse.Namespace) -> None:
    token = get_token(args.token)
    key = parse_file_key(args.file_key, args.url)
    if not args.ids and not args.url:
        print("Error: Provide --ids or a --url with node-id", file=sys.stderr)
        sys.exit(2)
    ids = args.ids
    if not ids and args.url:
        node_id = parse_node_id_from_url(args.url)
        if not node_id:
            print("Error: Could not find node-id in URL; pass --ids", file=sys.stderr)
            sys.exit(2)
        ids = node_id
    params: Dict[str, Any] = {"ids": ids}
    if args.version:
        params["version"] = args.version
    if args.depth is not None:
        params["depth"] = args.depth
    if args.geometry:
        params["geometry"] = args.geometry
    if args.plugin_data:
        params["plugin_data"] = args.plugin_data
    status, data = request_figma("GET", f"/files/{key}/nodes", token, params=params)
    if status >= 400:
        print(f"Error {status}: {data}", file=sys.stderr)
        sys.exit(1)
    dump_output(data, args.output)


def cmd_images(args: argparse.Namespace) -> None:
    token = get_token(args.token)
    key = parse_file_key(args.file_key, args.url)
    if not args.ids:
        print("Error: --ids is required for images", file=sys.stderr)
        sys.exit(2)
    params: Dict[str, Any] = {"ids": args.ids}
    if args.scale is not None:
        params["scale"] = args.scale
    if args.format:
        params["format"] = args.format
    if args.svg_outline_text is not None:
        params["svg_outline_text"] = str(args.svg_outline_text).lower()
    if args.svg_include_id is not None:
        params["svg_include_id"] = str(args.svg_include_id).lower()
    if args.svg_include_node_id is not None:
        params["svg_include_node_id"] = str(args.svg_include_node_id).lower()
    if args.svg_simplify_stroke is not None:
        params["svg_simplify_stroke"] = str(args.svg_simplify_stroke).lower()
    if args.contents_only is not None:
        params["contents_only"] = str(args.contents_only).lower()
    if args.use_absolute_bounds is not None:
        params["use_absolute_bounds"] = str(args.use_absolute_bounds).lower()
    if args.version:
        params["version"] = args.version
    status, data = request_figma("GET", f"/images/{key}", token, params=params)
    if status >= 400:
        print(f"Error {status}: {data}", file=sys.stderr)
        sys.exit(1)
    dump_output(data, args.output)


def cmd_image_fills(args: argparse.Namespace) -> None:
    token = get_token(args.token)
    key = parse_file_key(args.file_key, args.url)
    status, data = request_figma("GET", f"/files/{key}/images", token)
    if status >= 400:
        print(f"Error {status}: {data}", file=sys.stderr)
        sys.exit(1)
    dump_output(data, args.output)


def cmd_meta(args: argparse.Namespace) -> None:
    token = get_token(args.token)
    key = parse_file_key(args.file_key, args.url)
    status, data = request_figma("GET", f"/files/{key}/meta", token)
    if status >= 400:
        print(f"Error {status}: {data}", file=sys.stderr)
        sys.exit(1)
    dump_output(data, args.output)


def cmd_artboards(args: argparse.Namespace) -> None:
    """List pages and top-level frames (artboards) with IDs for selection."""
    token = get_token(args.token)
    key = parse_file_key(args.file_key, args.url)
    params: Dict[str, Any] = {"depth": 2}
    status, data = request_figma("GET", f"/files/{key}", token, params=params)
    if status >= 400:
        print(f"Error {status}: {data}", file=sys.stderr)
        sys.exit(1)
    document = data.get("document", {})
    pages = document.get("children", []) if isinstance(document, dict) else []
    result = []
    for page in pages:
        page_name = page.get("name")
        page_id = page.get("id")
        frames = []
        for node in page.get("children", []) or []:
            if node.get("type") in {"FRAME", "COMPONENT", "COMPONENT_SET"}:
                frames.append({
                    "id": node.get("id"),
                    "name": node.get("name"),
                    "type": node.get("type"),
                })
        if frames:
            result.append({
                "page": {"id": page_id, "name": page_name},
                "artboards": frames,
            })
    dump_output({"file": {"key": key, "name": data.get("name")}, "pages": result}, args.output)


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Figma API helper: fetch files, nodes, images, and list artboards.")
    sub = p.add_subparsers(dest="cmd", required=True)

    def common(subp: argparse.ArgumentParser, with_ids: bool = False) -> None:
        subp.add_argument("--token", help="Figma personal access token or set FIGMA_TOKEN")
        subp.add_argument("--file-key", help="Figma file key")
        subp.add_argument("--url", help="Figma file or node URL (extracts file key, and node-id for nodes)")
        subp.add_argument("--output", "-o", help="Output file (defaults to stdout)")
        if with_ids:
            subp.add_argument("--ids", help="Comma-separated node IDs")

    # file
    sp = sub.add_parser("file", help="GET /v1/files/:key")
    common(sp, with_ids=True)
    sp.add_argument("--version")
    sp.add_argument("--depth", type=int)
    sp.add_argument("--geometry", choices=["paths"])
    sp.add_argument("--plugin-data", dest="plugin_data")
    sp.add_argument("--branch-data", action="store_true")
    sp.set_defaults(func=cmd_file)

    # nodes
    sp = sub.add_parser("nodes", help="GET /v1/files/:key/nodes")
    common(sp, with_ids=True)
    sp.add_argument("--version")
    sp.add_argument("--depth", type=int)
    sp.add_argument("--geometry", choices=["paths"])
    sp.add_argument("--plugin-data", dest="plugin_data")
    sp.set_defaults(func=cmd_nodes)

    # images
    sp = sub.add_parser("images", help="GET /v1/images/:key")
    common(sp, with_ids=True)
    sp.add_argument("--scale", type=float)
    sp.add_argument("--format", choices=["jpg", "png", "svg", "pdf"])
    sp.add_argument("--svg-outline-text", dest="svg_outline_text", type=lambda v: v.lower() in ("1", "true", "yes"))
    sp.add_argument("--svg-include-id", dest="svg_include_id", type=lambda v: v.lower() in ("1", "true", "yes"))
    sp.add_argument("--svg-include-node-id", dest="svg_include_node_id", type=lambda v: v.lower() in ("1", "true", "yes"))
    sp.add_argument("--svg-simplify-stroke", dest="svg_simplify_stroke", type=lambda v: v.lower() in ("1", "true", "yes"))
    sp.add_argument("--contents-only", dest="contents_only", type=lambda v: v.lower() in ("1", "true", "yes"))
    sp.add_argument("--use-absolute-bounds", dest="use_absolute_bounds", type=lambda v: v.lower() in ("1", "true", "yes"))
    sp.add_argument("--version")
    sp.set_defaults(func=cmd_images)

    # image-fills
    sp = sub.add_parser("image-fills", help="GET /v1/files/:key/images")
    common(sp)
    sp.set_defaults(func=cmd_image_fills)

    # meta
    sp = sub.add_parser("meta", help="GET /v1/files/:key/meta")
    common(sp)
    sp.set_defaults(func=cmd_meta)

    # artboards
    sp = sub.add_parser("artboards", help="List pages and top-level frames (artboards)")
    common(sp)
    sp.set_defaults(func=cmd_artboards)

    return p


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()

