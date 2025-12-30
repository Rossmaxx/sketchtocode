# take the raw_wireframe.json (output of stage 1 - image-to-json.py)
# output a hierarchially structured, LLM-facing json (ir.json)

import json
from pathlib import Path
from typing import Dict, Any, List

from .paths import FILES_DIR


def rect_contains(outer: Dict[str, float], inner: Dict[str, float], tol: float = 0.0) -> bool:
    """
    True if 'inner' rect is fully inside 'outer' rect.
    Rect format: {"x":..., "y":..., "w":..., "h":...}
    """
    ox, oy, ow, oh = outer["x"], outer["y"], outer["w"], outer["h"]
    ix, iy, iw, ih = inner["x"], inner["y"], inner["w"], inner["h"]

    return (
        ix >= ox - tol
        and iy >= oy - tol
        and ix + iw <= ox + ow + tol
        and iy + ih <= oy + oh + tol
    )


def rect_union(rects: List[Dict[str, float]]) -> Dict[str, float]:
    """
    Minimal rect that contains all rects.
    """
    min_x = min(r["x"] for r in rects)
    min_y = min(r["y"] for r in rects)
    max_x = max(r["x"] + r["w"] for r in rects)
    max_y = max(r["y"] + r["h"] for r in rects)
    return {"x": min_x, "y": min_y, "w": max_x - min_x, "h": max_y - min_y}


def rect_area(rect: Dict[str, float]) -> float:
    return rect["w"] * rect["h"]


def build_nodes(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Build nodes (ui + text) + outer box from raw JSON.
    Returns dict with "image_path" and "nodes" (including outer).
    """
    nodes: List[Dict[str, Any]] = []

    # UI boxes
    for i, box in enumerate(data.get("ui_boxes", [])):
        nodes.append(
            {
                "id": f"ui_{i}",
                "kind": "ui",  # UI box
                "abs": {
                    "x": float(box["x"]),
                    "y": float(box["y"]),
                    "w": float(box["w"]),
                    "h": float(box["h"]),
                },
                "children": [],
            }
        )

    # Text boxes
    for i, label in enumerate(data.get("text_labels", [])):
        bbox = label["bbox"]
        nodes.append(
            {
                "id": f"text_{i}",
                "kind": "text",
                "text": label["text"],
                "abs": {
                    "x": float(bbox["x"]),
                    "y": float(bbox["y"]),
                    "w": float(bbox["w"]),
                    "h": float(bbox["h"]),
                },
                "children": [],
            }
        )

    if not nodes:
        raise ValueError("No ui_boxes or text_labels found")

    # Outer box: union of all rects
    all_rects = [n["abs"] for n in nodes]
    outer_rect = rect_union(all_rects)

    outer_node = {
        "id": "outer_0",
        "kind": "outer",
        "abs": outer_rect,
        "children": [],
    }

    return {
        "image_path": data.get("image_path"),
        "nodes": [outer_node] + nodes,
    }


def build_hierarchy(nodes_info: Dict[str, Any]) -> Dict[str, Any]:
    """
    Given dict from build_nodes(), build parent-child hierarchy by containment.
    Returns: {"image_path":..., "root": outer_node_with_children}
    """
    image_path = nodes_info["image_path"]
    all_nodes: List[Dict[str, Any]] = nodes_info["nodes"]

    # Find outer
    outer = next(n for n in all_nodes if n["kind"] == "outer")
    outer_area = rect_area(outer["abs"])

    other_nodes = [n for n in all_nodes if n is not outer]

    # Sort by area: smallest first (so we attach tight parents)
    other_nodes_sorted = sorted(other_nodes, key=lambda n: rect_area(n["abs"]))

    # Build a lookup for convenience
    id_to_node = {n["id"]: n for n in all_nodes}

    for node in other_nodes_sorted:
        node_rect = node["abs"]
        best_parent = outer
        best_parent_area = outer_area

        for cand in all_nodes:
            if cand is node:
                continue

            cand_rect = cand["abs"]
            area_cand = rect_area(cand_rect)

            # parent must be larger and must contain the node
            if area_cand > rect_area(node_rect) and rect_contains(cand_rect, node_rect):
                if area_cand < best_parent_area:
                    best_parent_area = area_cand
                    best_parent = cand

        # Attach node to its best parent
        node["_parent_id"] = best_parent["id"]
        best_parent["children"].append(node)

    return {
        "image_path": image_path,
        "root": outer,
        "id_to_node": id_to_node,
    }


def add_relative_geometry(tree: Dict[str, Any]) -> Dict[str, Any]:
    """
    Recursively add:
      - margins (px + relative) to each node, relative to its parent
      - size_rel (relative width/height to parent)
      - font_size_rel_outer for text nodes (relative to OUTER box height)
    Returns same structure with enriched nodes.
    """
    root = tree["root"]
    outer_rect = root["abs"]

    def _recurse(node: Dict[str, Any], parent_abs: Dict[str, float]):
        rect = node["abs"]

        if node["kind"] == "outer":
            # Outer: margins = 0, size_rel = 1
            node["margins"] = {
                "top": 0.0,
                "left": 0.0,
                "right": 0.0,
                "bottom": 0.0,
                "top_rel": 0.0,
                "left_rel": 0.0,
                "right_rel": 0.0,
                "bottom_rel": 0.0,
            }
            node["size_rel"] = {"w_rel": 1.0, "h_rel": 1.0}
        else:
            px = parent_abs["x"]
            py = parent_abs["y"]
            pw = parent_abs["w"]
            ph = parent_abs["h"]

            x, y, w, h = rect["x"], rect["y"], rect["w"], rect["h"]

            m_left = x - px
            m_top = y - py
            m_right = (px + pw) - (x + w)
            m_bottom = (py + ph) - (y + h)

            node["margins"] = {
                "top": m_top,
                "left": m_left,
                "right": m_right,
                "bottom": m_bottom,
                "top_rel": m_top / ph if ph else 0.0,
                "left_rel": m_left / pw if pw else 0.0,
                "right_rel": m_right / pw if pw else 0.0,
                "bottom_rel": m_bottom / ph if ph else 0.0,
            }

            node["size_rel"] = {
                "w_rel": w / pw if pw else 0.0,
                "h_rel": h / ph if ph else 0.0,
            }

        # Font size: relative to OUTER box height
        if node["kind"] == "text":
            node["font_size_rel_outer"] = (
                rect["h"] / outer_rect["h"] if outer_rect["h"] else 0.0
            )

        for child in node.get("children", []):
            _recurse(child, rect)

    _recurse(root, root["abs"])
    return tree


def _round4(x: float) -> float:
    return float(f"{x:.4f}")


def simplify_node_for_llm(node: Dict[str, Any]) -> Dict[str, Any]:
    """
    Take a rich node (with abs, margins, size_rel, etc.)
    and return a compact, LLM-friendly representation:
      - id
      - type: "root" | "box" | "text"
      - text (only for text nodes)
      - layout: {top, left, right, bottom, width, height} (all relative)
      - font: {size_rel_outer} for text
      - children: simplified children
    """
    kind = node["kind"]
    if kind == "outer":
        node_type = "root"
    elif kind == "ui":
        node_type = "box"
    else:
        node_type = "text"

    margins = node["margins"]
    size_rel = node["size_rel"]

    layout = {
        "top": _round4(margins["top_rel"]),
        "left": _round4(margins["left_rel"]),
        "right": _round4(margins["right_rel"]),
        "bottom": _round4(margins["bottom_rel"]),
        "width": _round4(size_rel["w_rel"]),
        "height": _round4(size_rel["h_rel"]),
    }

    simple: Dict[str, Any] = {
        "id": node["id"],
        "type": node_type,
        "layout": layout,
        "children": [simplify_node_for_llm(ch) for ch in node.get("children", [])],
    }

    if kind == "text":
        simple["text"] = node.get("text", "")
        simple["font"] = {
            "size_rel_outer": _round4(node.get("font_size_rel_outer", 0.0))
        }

    return simple


def process_wireframe_json():
    """
    Full pipeline:
      - read JSON
      - detect outer box
      - build hierarchy
      - convert to relative margins/size
      - simplify to an LLM-facing layout tree
      - (optional) write result to another json file
    """
    input_filepath = FILES_DIR / "raw_wireframe.json"
    with input_filepath.open("r", encoding="utf-8") as f:
        data = json.load(f)

    nodes_info = build_nodes(data)
    tree = build_hierarchy(nodes_info)
    tree = add_relative_geometry(tree)

    id_to_node = tree.pop("id_to_node")
    for node in id_to_node.values():
        node.pop("_parent_id", None)

    # LLM-facing tree
    layout_root = simplify_node_for_llm(tree["root"])

    result = {
        "image_path": tree["image_path"],
        "layout": layout_root,
    }

    # Write the json file to disk for generating the code
    save_to = FILES_DIR / "hierarchy_wireframe.json"
    with save_to.open("w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)

    return "Hierarchy generated successfully!"


# Script entry point
if __name__ == "__main__":
    status = process_wireframe_json()
    print(status)
