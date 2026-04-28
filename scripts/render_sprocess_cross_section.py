#!/usr/bin/env python3
"""Render a heuristic SProcess 2D cross-section sketch as SVG.

This is not a process simulator. It reads common SProcess deck patterns and
creates a review-oriented conceptual cross-section: substrate, masks, likely
implanted regions, oxide/STI/gate hints, contacts, and refinement/contact boxes.
"""

from __future__ import annotations

import argparse
import html
import math
import re
import ast
import operator
from dataclasses import dataclass
from pathlib import Path

from shapely.geometry import box
from shapely.ops import unary_union


NUMBER = r"[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?"

DEFAULT_PARAMS = {
    # Defaults from the LDMOS degradation project overview.
    "Lch": 1.5,
    "Lacc": 0.2,
    "Lsti": 2.5,
    "tox": 0.05,
    "tsti": 0.3,
    "pmesh": 1.0,
    "dmesh": 1.0,
    # Useful harmless placeholders.
    "psubD": 1.0e15,
    "nwellD": 1.0e13,
    "pbD": 1.0e15,
    "nsD": 1.0e15,
    "node": 0.0,
}


@dataclass
class Mask:
    name: str
    spans: list[tuple[float, float]]
    negative: bool = False


@dataclass
class Contact:
    name: str
    material: str
    xlo: float | None
    xhi: float | None
    ylo: float | None
    yhi: float | None
    kind: str


@dataclass
class ImplantStep:
    section: str
    mask: str | None
    species: str
    dose: str
    energy: str
    tilt: str | None
    rotation: str | None


@dataclass
class ThermalStep:
    section: str
    kind: str
    name: str | None
    temp: str | None
    time: str | None
    gas: str | None
    note: str


def join_continuations(text: str) -> list[str]:
    logical: list[str] = []
    current = ""
    for raw in text.splitlines():
        line = raw.rstrip()
        if not line:
            if current:
                logical.append(current.strip())
                current = ""
            continue
        if current:
            current += " " + line.lstrip()
        else:
            current = line
        if current.endswith("\\"):
            current = current[:-1].rstrip()
            continue
        logical.append(current.strip())
        current = ""
    if current:
        logical.append(current.strip())
    return logical


def strip_unit(value: str) -> str:
    return re.sub(r"(?<!@)<[^>]+>", "", value).strip()


def safe_number(value: str, env: dict[str, float] | None = None) -> float | None:
    value = strip_unit(value)
    if env:
        evaluated = eval_value(value, env)
        if evaluated is not None:
            return evaluated
    match = re.search(NUMBER, value)
    if not match:
        return None
    try:
        return float(match.group(0))
    except ValueError:
        return None


def eval_ast(node: ast.AST) -> float:
    ops = {
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: operator.mul,
        ast.Div: operator.truediv,
        ast.Pow: operator.pow,
        ast.USub: operator.neg,
        ast.UAdd: operator.pos,
    }
    if isinstance(node, ast.Expression):
        return eval_ast(node.body)
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return float(node.value)
    if isinstance(node, ast.UnaryOp) and type(node.op) in ops:
        return ops[type(node.op)](eval_ast(node.operand))
    if isinstance(node, ast.BinOp) and type(node.op) in ops:
        return ops[type(node.op)](eval_ast(node.left), eval_ast(node.right))
    raise ValueError(f"unsupported expression node: {type(node).__name__}")


def eval_arithmetic(expr: str) -> float | None:
    try:
        return eval_ast(ast.parse(expr, mode="eval"))
    except Exception:
        return None


def replace_vars(expr: str, env: dict[str, float]) -> str:
    def var_repl(match: re.Match[str]) -> str:
        return str(env.get(match.group(1), 0.0))

    expr = re.sub(r"\$([A-Za-z_][A-Za-z0-9_]*)", var_repl, expr)
    for key, value in sorted(env.items(), key=lambda item: -len(item[0])):
        expr = re.sub(rf"\b{re.escape(key)}\b", str(value), expr)
    return expr


def eval_value(value: str, env: dict[str, float]) -> float | None:
    value = strip_unit(value).strip()
    value = value.strip('"{}')
    if value.startswith("[expr") and value.endswith("]"):
        value = value[5:-1].strip()
    value = re.sub(r"@<\s*(.*?)\s*>@", lambda m: str(eval_value(m.group(1), env) or 0.0), value)
    value = re.sub(r"@([A-Za-z_][A-Za-z0-9_]*)@", lambda m: str(env.get(m.group(1), 0.0)), value)
    value = replace_vars(value, env)
    value = value.replace("[", "").replace("]", "")
    if re.fullmatch(rf"\s*{NUMBER}\s*", value):
        return float(value)
    if re.fullmatch(r"[0-9eE+\-*/().\s]+", value):
        return eval_arithmetic(value)
    match = re.search(NUMBER, value)
    return float(match.group(0)) if match else None


def value_tokens(value: str, env: dict[str, float]) -> list[float]:
    value = strip_unit(value)
    value = re.sub(r"\[expr\s+([^\]]+)\]", lambda m: str(eval_value(m.group(1), env) or 0.0), value)
    value = re.sub(r"@<\s*(.*?)\s*>@", lambda m: str(eval_value(m.group(1), env) or 0.0), value)
    value = re.sub(r"@([A-Za-z_][A-Za-z0-9_]*)@", lambda m: str(env.get(m.group(1), 0.0)), value)
    value = replace_vars(value, env)
    return [float(v) for v in re.findall(NUMBER, value)]


def parse_key_number(line: str, key: str, env: dict[str, float]) -> float | None:
    match = re.search(rf"\b{re.escape(key)}\s*=\s*(\[[^\]]+\]|\"[^\"]+\"|\{{[^}}]+\}}|[^ \t]+)", line)
    return eval_value(match.group(1), env) if match else None


def parse_key_raw(line: str, key: str) -> str | None:
    match = re.search(rf"\b{re.escape(key)}\s*=\s*(\[[^\]]+\]|\"[^\"]+\"|\{{[^}}]+\}}|[^ \t]+)", line)
    return match.group(1).strip('"{}') if match else None


def parse_environment(lines: list[str], params: dict[str, float]) -> dict[str, float]:
    env = dict(DEFAULT_PARAMS)
    env.update(params)
    for line in lines:
        match = re.match(r"\s*fset\s+([A-Za-z_][A-Za-z0-9_]*)\s+(.+?)\s*$", line)
        if not match:
            continue
        name, expr = match.group(1), match.group(2)
        value = eval_value(expr, env)
        if value is not None:
            env[name] = value
    return env


def parse_lines(lines: list[str], env: dict[str, float]) -> tuple[list[float], list[float]]:
    xs: list[float] = []
    ys: list[float] = []
    for line in lines:
        if not line.lower().startswith("line "):
            continue
        axis = re.search(r"\bline\s+([xyz])\b", line, re.I)
        loc = re.search(r"\b(?:loc|location)\s*=\s*([^ \t]+)", line, re.I)
        if not axis or not loc:
            continue
        value = eval_value(loc.group(1), env)
        if value is None:
            continue
        if axis.group(1).lower() == "x":
            xs.append(value)
        elif axis.group(1).lower() == "y":
            ys.append(value)
    return xs, ys


def parse_masks(lines: list[str], env: dict[str, float]) -> dict[str, Mask]:
    masks: dict[str, Mask] = {}
    for line in lines:
        if not line.lower().startswith("mask "):
            continue
        name_match = re.search(r"\bname\s*=\s*([^\s]+)", line)
        if not name_match:
            continue
        name = name_match.group(1).strip('"')
        spans: list[tuple[float, float]] = []
        left = parse_key_number(line, "left", env)
        right = parse_key_number(line, "right", env)
        if left is not None and right is not None:
            spans.append((min(left, right), max(left, right)))
        seg_match = re.search(r"\bsegments\s*=\s*(?:\"([^\"]+)\"|\{([^}]+)\})", line)
        if seg_match:
            vals = value_tokens(seg_match.group(1) or seg_match.group(2) or "", env)
            for i in range(0, len(vals) - 1, 2):
                spans.append((min(vals[i], vals[i + 1]), max(vals[i], vals[i + 1])))
        if not spans:
            continue
        negative = bool(re.search(r"\bnegative\b", line, re.I))
        if name not in masks:
            masks[name] = Mask(name=name, spans=[], negative=negative)
        masks[name].spans.extend(spans)
        masks[name].negative = masks[name].negative or negative
    for mask in masks.values():
        mask.spans = merge_spans(mask.spans)
    return masks


def merge_spans(spans: list[tuple[float, float]]) -> list[tuple[float, float]]:
    if not spans:
        return []
    shapes = [box(lo, 0.0, hi, 1.0) for lo, hi in spans if hi > lo]
    if not shapes:
        return []
    merged = unary_union(shapes)
    geoms = list(merged.geoms) if hasattr(merged, "geoms") else [merged]
    result = [(float(g.bounds[0]), float(g.bounds[2])) for g in geoms]
    return sorted(result)


def parse_contacts(lines: list[str], env: dict[str, float]) -> list[Contact]:
    contacts: list[Contact] = []
    for line in lines:
        if not line.lower().startswith("contact "):
            continue
        name_match = re.search(r"\bname\s*=\s*\"?([^\"\s]+)\"?", line)
        if not name_match:
            continue
        name = name_match.group(1)
        material_match = re.search(r"\bbox\s+([A-Za-z0-9_]+)", line)
        if material_match:
            kind = "box"
            material = material_match.group(1)
        elif re.search(r"\bbottom\b", line, re.I):
            kind = "bottom"
            material_match = re.search(r"\bbottom\s+([A-Za-z0-9_]+)", line)
            material = material_match.group(1) if material_match else "Silicon"
        elif re.search(r"\bregion\s*=", line, re.I):
            kind = "region"
            material = "region"
        else:
            kind = "contact"
            material = "unknown"
        contacts.append(
            Contact(
                name=name,
                material=material,
                xlo=parse_key_number(line, "xlo", env),
                xhi=parse_key_number(line, "xhi", env),
                ylo=parse_key_number(line, "ylo", env),
                yhi=parse_key_number(line, "yhi", env),
                kind=kind,
            )
        )
    return contacts


def deck_traits(lines: list[str]) -> set[str]:
    joined = "\n".join(lines).lower()
    traits: set[str] = set()
    for key in ["locos", "sti", "gate", "polysilicon", "nwell", "pwell", "body", "srcdrn", "nplus"]:
        if key in joined:
            traits.add(key)
    return traits


def parse_section(line: str, current: str) -> str:
    match = re.search(r"\b(?:SubSection\.Start|Section)\b.*?\b(?:title|tag)\s*=\s*([^\s]+(?:\s+[^\s]+)*)", line, re.I)
    if not match:
        return current
    title = match.group(1).strip()
    title = re.split(r"\s+\w+\s*=", title)[0].strip()
    return title.strip('"') or current


def parse_implants(lines: list[str]) -> list[ImplantStep]:
    implants: list[ImplantStep] = []
    section = "Global"
    active_mask: str | None = None
    for line in lines:
        section = parse_section(line, section)
        photo = re.search(r"\bphoto\s+mask\s*=\s*([^\s]+)", line, re.I)
        if photo:
            active_mask = photo.group(1).strip('"')
            continue
        if re.match(r"\s*strip\s+(?:photoresist|resist)\b", line, re.I):
            active_mask = None
            continue
        match = re.match(r"\s*implant\s+([A-Za-z][A-Za-z0-9_]*)\b", line, re.I)
        if not match:
            continue
        implants.append(
            ImplantStep(
                section=section,
                mask=active_mask,
                species=match.group(1),
                dose=parse_key_raw(line, "dose") or "?",
                energy=parse_key_raw(line, "energy") or "?",
                tilt=parse_key_raw(line, "tilt"),
                rotation=parse_key_raw(line, "rotation"),
            )
        )
    return implants


def parse_thermal_steps(lines: list[str]) -> list[ThermalStep]:
    steps: list[ThermalStep] = []
    section = "Global"
    for line in lines:
        section = parse_section(line, section)
        if re.match(r"\s*temp_ramp\b", line, re.I):
            steps.append(
                ThermalStep(
                    section=section,
                    kind="temp_ramp",
                    name=parse_key_raw(line, "name"),
                    temp=parse_key_raw(line, "temp"),
                    time=parse_key_raw(line, "time"),
                    gas=parse_key_raw(line, "gas_flow"),
                    note="ramped thermal segment",
                )
            )
            continue
        if re.match(r"\s*diffuse\b", line, re.I):
            name = parse_key_raw(line, "temp_ramp")
            note = "uses temp_ramp" if name else "direct diffuse/epi step"
            steps.append(
                ThermalStep(
                    section=section,
                    kind="diffuse",
                    name=name,
                    temp=parse_key_raw(line, "temperature") or parse_key_raw(line, "temp"),
                    time=parse_key_raw(line, "time"),
                    gas=parse_key_raw(line, "gas_flow"),
                    note=note,
                )
            )
    return steps


def mask_role(name: str) -> str:
    key = name.lower()
    if "nwell" in key:
        return "n-well / drift implant window"
    if "pwell" in key or "body" in key or "pbody" in key:
        return "p-body / body contact window"
    if "gate" in key or "poly" in key:
        return "poly gate definition"
    if "src" in key or "drn" in key or "nplus" in key:
        return "source/drain n+ implant window"
    if "locos" in key or "sti" in key:
        return "field isolation window"
    if "contact" in key:
        return "backend contact opening"
    if "etch" in key:
        return "etch window"
    return "process mask"


def format_spans(spans: list[tuple[float, float]]) -> str:
    return ", ".join(f"{lo:g}..{hi:g} um" for lo, hi in spans)


def write_analysis(deck: Path, out: Path | None, params: dict[str, float] | None = None) -> str:
    text = deck.read_text(encoding="utf-8", errors="replace")
    lines = join_continuations(text)
    env = parse_environment(lines, params or {})
    masks = parse_masks(lines, env)
    implants = parse_implants(lines)
    thermal_steps = parse_thermal_steps(lines)
    contacts = parse_contacts(lines, env)

    rows: list[str] = []
    rows.append(f"# SProcess Deck Analysis: {deck.name}")
    rows.append("")
    rows.append("This is a heuristic review aid generated from common SProcess deck patterns. Verify final geometry and doping in TDR/SVisual.")
    rows.append("")
    rows.append("## Mask Layout")
    rows.append("")
    rows.append("| Mask | Lateral span | Polarity | Likely role |")
    rows.append("| --- | --- | --- | --- |")
    for mask in masks.values():
        polarity = "negative" if mask.negative else "positive"
        rows.append(f"| {mask.name} | {format_spans(mask.spans)} | {polarity} | {mask_role(mask.name)} |")

    rows.append("")
    rows.append("## Implant To Region Map")
    rows.append("")
    rows.append("| Section | Mask/window | Species | Dose | Energy | Tilt/rotation | Likely device meaning |")
    rows.append("| --- | --- | --- | --- | --- | --- | --- |")
    for step in implants:
        mask = step.mask or "(blanket)"
        angle = "/".join(v for v in (step.tilt, step.rotation) if v is not None) or "-"
        meaning = mask_role(step.mask or step.section)
        rows.append(f"| {step.section} | {mask} | {step.species} | {step.dose} | {step.energy} | {angle} | {meaning} |")

    rows.append("")
    rows.append("## Thermal / Diffusion Budget")
    rows.append("")
    rows.append("| Section | Kind | Ramp/name | Temperature | Time | Gas | Note |")
    rows.append("| --- | --- | --- | --- | --- | --- | --- |")
    for step in thermal_steps:
        rows.append(
            f"| {step.section} | {step.kind} | {step.name or '-'} | {step.temp or '-'} | "
            f"{step.time or '-'} | {step.gas or '-'} | {step.note} |"
        )

    rows.append("")
    rows.append("## Device Contacts")
    rows.append("")
    rows.append("| Contact | Kind/material | y span | x span |")
    rows.append("| --- | --- | --- | --- |")
    for contact in contacts:
        if contact.ylo is None or contact.yhi is None:
            yspan = "-"
        else:
            ylo, yhi = sorted((contact.ylo, contact.yhi))
            yspan = f"{ylo:g}..{yhi:g} um"
        if contact.xlo is None or contact.xhi is None:
            xspan = "-"
        else:
            xlo, xhi = sorted((contact.xlo, contact.xhi))
            xspan = f"{xlo:g}..{xhi:g} um"
        rows.append(f"| {contact.name} | {contact.kind}/{contact.material} | {yspan} | {xspan} |")

    report = "\n".join(rows) + "\n"
    if out:
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(report, encoding="utf-8")
    return report


class Svg:
    def __init__(self, width: int, height: int) -> None:
        self.width = width
        self.height = height
        self.items: list[str] = []

    def rect(self, x: float, y: float, w: float, h: float, fill: str, stroke: str = "#24313a", opacity: float = 1.0) -> None:
        self.items.append(
            f'<rect x="{x:.2f}" y="{y:.2f}" width="{w:.2f}" height="{h:.2f}" '
            f'fill="{fill}" stroke="{stroke}" stroke-width="1" opacity="{opacity}"/>'
        )

    def line(self, x1: float, y1: float, x2: float, y2: float, stroke: str = "#24313a", width: float = 1, dash: str | None = None) -> None:
        dash_attr = f' stroke-dasharray="{dash}"' if dash else ""
        self.items.append(
            f'<line x1="{x1:.2f}" y1="{y1:.2f}" x2="{x2:.2f}" y2="{y2:.2f}" '
            f'stroke="{stroke}" stroke-width="{width}"{dash_attr}/>'
        )

    def text(self, x: float, y: float, text: str, size: int = 13, anchor: str = "start", fill: str = "#17212b", weight: str = "400") -> None:
        self.items.append(
            f'<text x="{x:.2f}" y="{y:.2f}" font-family="Segoe UI, Arial, sans-serif" '
            f'font-size="{size}" text-anchor="{anchor}" fill="{fill}" font-weight="{weight}">{html.escape(text)}</text>'
        )

    def path(self, d: str, fill: str, stroke: str = "#24313a", opacity: float = 1.0) -> None:
        self.items.append(f'<path d="{d}" fill="{fill}" stroke="{stroke}" stroke-width="1" opacity="{opacity}"/>')

    def finish(self) -> str:
        return (
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{self.width}" height="{self.height}" '
            f'viewBox="0 0 {self.width} {self.height}">\n'
            '<rect width="100%" height="100%" fill="#f7f9fb"/>\n'
            + "\n".join(self.items)
            + "\n</svg>\n"
        )


def clamp_span(span: tuple[float, float], ymin: float, ymax: float) -> tuple[float, float] | None:
    a, b = max(span[0], ymin), min(span[1], ymax)
    if b <= a:
        return None
    return a, b


def parse_param(items: list[str]) -> dict[str, float]:
    params: dict[str, float] = {}
    for item in items:
        if "=" not in item:
            raise SystemExit(f"--param must be NAME=VALUE, got {item!r}")
        key, raw = item.split("=", 1)
        value = safe_number(raw)
        if value is None:
            raise SystemExit(f"Could not parse numeric --param value: {item!r}")
        params[key] = value
    return params


def render(deck: Path, out: Path, title: str | None = None, params: dict[str, float] | None = None) -> str:
    text = deck.read_text(encoding="utf-8", errors="replace")
    lines = join_continuations(text)
    env = parse_environment(lines, params or {})
    xs, ys = parse_lines(lines, env)
    masks = parse_masks(lines, env)
    contacts = parse_contacts(lines, env)
    traits = deck_traits(lines)

    if ys:
        ymin, ymax = min(ys), max(ys)
    else:
        ymin, ymax = 0.0, 10.0
    ypad = max(0.4, (ymax - ymin) * 0.04)
    ymin -= ypad
    ymax += ypad

    # Conceptual x-depth range. Prefer process lines, but allow grown/etched
    # structures in official examples to extend above the original surface.
    if xs:
        xlo, xhi = min(xs), max(xs)
    else:
        xlo, xhi = -1.0, 5.0
    contact_xs = [v for c in contacts for v in (c.xlo, c.xhi) if v is not None]
    if contact_xs:
        xlo = min(xlo, min(contact_xs))
        xhi = max(xhi, max(contact_xs))
    if "locos" in traits or "gate" in traits:
        xlo = min(xlo, -0.8)
    xpad = max(0.2, (xhi - xlo) * 0.05)
    xlo -= xpad
    xhi += xpad

    width, height = 1180, 660
    margin_l, margin_r, margin_t, margin_b = 90, 40, 70, 86
    plot_w = width - margin_l - margin_r
    plot_h = height - margin_t - margin_b

    def sx(yval: float) -> float:
        return margin_l + (yval - ymin) / (ymax - ymin) * plot_w

    def sy(xval: float) -> float:
        return margin_t + (xval - xlo) / (xhi - xlo) * plot_h

    svg = Svg(width, height)
    svg.text(margin_l, 32, title or f"Heuristic cross-section: {deck.name}", 22, weight="600")
    svg.text(margin_l, 54, "Conceptual sketch from SProcess deck commands; not a TCAD-simulated boundary.", 13, fill="#52616f")

    surface = 0.0 if xlo <= 0 <= xhi else xlo + 0.18 * (xhi - xlo)
    top_px, bottom_px = sy(surface), sy(xhi)
    left_px, right_px = sx(ymin + ypad), sx(ymax - ypad)

    # Substrate and drift/background.
    svg.rect(left_px, top_px, right_px - left_px, bottom_px - top_px, "#cfe8d6", "#486b55")
    svg.text(left_px + 10, bottom_px - 18, "Silicon substrate / drift region", 13, fill="#28513a", weight="600")

    # Well and implant hints from masks.
    palette = {
        "NWellImpl": "#a8d8ff",
        "NWELL": "#a8d8ff",
        "PWellImpl": "#ffcab8",
        "PBODY": "#ffb7aa",
        "BodyImpl": "#ff9f9a",
        "NPLUS": "#74c0fc",
        "SrcDrn": "#74c0fc",
    }
    depths = {
        "NWellImpl": 0.38,
        "NWELL": 0.42,
        "PWellImpl": 0.30,
        "PBODY": 0.20,
        "BodyImpl": 0.18,
        "NPLUS": 0.13,
        "SrcDrn": 0.16,
    }
    for name, mask in masks.items():
        if name not in palette:
            continue
        for span in mask.spans:
            clamped = clamp_span(span, ymin, ymax)
            if clamped is None:
                continue
            x1, x2 = sx(clamped[0]), sx(clamped[1])
            h = (bottom_px - top_px) * depths.get(name, 0.2)
            svg.rect(x1, top_px, x2 - x1, h, palette[name], "#517a98", 0.42)
            svg.text((x1 + x2) / 2, top_px + min(h - 8, 28), name, 12, anchor="middle", fill="#244a66", weight="600")

    # LOCOS/STI oxide hints.
    for name in ("Locos", "STI"):
        if name not in masks:
            continue
        for span in masks[name].spans:
            clamped = clamp_span(span, ymin, ymax)
            if clamped is None:
                continue
            x1, x2 = sx(clamped[0]), sx(clamped[1])
            if name == "STI":
                d = f"M {x1:.2f} {top_px:.2f} L {x2:.2f} {top_px:.2f} L {x2 - 16:.2f} {sy(surface + 0.45):.2f} L {x1 + 16:.2f} {sy(surface + 0.45):.2f} Z"
                svg.path(d, "#d8edf7", "#6496aa", 0.88)
            else:
                d = f"M {x1:.2f} {top_px:.2f} Q {(x1+x2)/2:.2f} {sy(surface - 0.7):.2f} {x2:.2f} {top_px:.2f} L {x2:.2f} {sy(surface + 0.22):.2f} L {x1:.2f} {sy(surface + 0.22):.2f} Z"
                svg.path(d, "#d8edf7", "#6496aa", 0.9)
            svg.text((x1 + x2) / 2, sy(surface + 0.35), name, 12, anchor="middle", fill="#315a6d", weight="600")

    # Thin oxide / backend oxide band.
    ox_top = sy(surface - 0.18)
    svg.rect(left_px, ox_top, right_px - left_px, top_px - ox_top, "#eef7fb", "#8bb7c9", 0.92)
    svg.text(right_px - 12, ox_top - 8, "oxide/gate oxide (schematic)", 12, anchor="end", fill="#507386")

    # Gate/polysilicon.
    gate_mask = masks.get("Gate") or masks.get("POLY")
    if gate_mask:
        for span in gate_mask.spans:
            clamped = clamp_span(span, ymin, ymax)
            if clamped is None:
                continue
            x1, x2 = sx(clamped[0]), sx(clamped[1])
            y0 = sy(surface - 0.58)
            svg.rect(x1, y0, x2 - x1, sy(surface - 0.18) - y0, "#b29bd8", "#5f4c82", 0.95)
            svg.text((x1 + x2) / 2, y0 - 8, "Poly gate", 13, anchor="middle", fill="#513d75", weight="600")

    # Contacts.
    for c in contacts:
        if c.kind == "bottom":
            svg.rect(left_px, bottom_px - 13, right_px - left_px, 13, "#f7cf7a", "#8d6d20", 0.95)
            svg.text((left_px + right_px) / 2, bottom_px + 24, c.name, 13, anchor="middle", fill="#6e5315", weight="600")
            continue
        if c.ylo is not None and c.yhi is not None:
            y1, y2 = max(c.ylo, ymin), min(c.yhi, ymax)
        elif gate_mask and c.name.lower() == "gate":
            y1, y2 = gate_mask.spans[0]
        else:
            continue
        if y2 <= y1:
            continue
        x1, x2 = sx(y1), sx(y2)
        y_contact = sy(surface - 0.83)
        svg.rect(x1, y_contact, x2 - x1, 22, "#f6c85f", "#86651a", 0.95)
        svg.line((x1 + x2) / 2, y_contact + 22, (x1 + x2) / 2, top_px, "#86651a", 1.2)
        svg.text((x1 + x2) / 2, y_contact - 7, c.name, 12, anchor="middle", fill="#6e5315", weight="600")

    # Axes and mask ticks.
    svg.line(left_px, bottom_px + 34, right_px, bottom_px + 34, "#7a8793", 1)
    for val in nice_ticks(ymin + ypad, ymax - ypad, 8):
        px = sx(val)
        svg.line(px, bottom_px + 30, px, bottom_px + 38, "#7a8793", 1)
        svg.text(px, bottom_px + 56, f"{val:g}", 11, anchor="middle", fill="#52616f")
    svg.text((left_px + right_px) / 2, bottom_px + 78, "lateral y coordinate (um)", 12, anchor="middle", fill="#52616f")
    svg.line(left_px - 26, top_px, left_px - 26, bottom_px, "#7a8793", 1)
    svg.text(left_px - 42, top_px + 4, "surface", 11, anchor="end", fill="#52616f")
    svg.text(left_px - 42, bottom_px, "depth x", 11, anchor="end", fill="#52616f")

    # Legend.
    legend_x, legend_y = width - 300, 88
    legend = [
        ("Silicon", "#cfe8d6"),
        ("n-type implant/drift", "#a8d8ff"),
        ("p/body implant", "#ffcab8"),
        ("oxide/STI/LOCOS", "#d8edf7"),
        ("poly gate", "#b29bd8"),
        ("contact", "#f6c85f"),
    ]
    svg.text(legend_x, legend_y - 14, "Legend", 13, weight="600")
    for idx, (label, color) in enumerate(legend):
        y = legend_y + idx * 23
        svg.rect(legend_x, y - 13, 18, 14, color, "#6f7b85")
        svg.text(legend_x + 28, y, label, 12, fill="#41505c")

    out.parent.mkdir(parents=True, exist_ok=True)
    rendered = svg.finish()
    out.write_text(rendered, encoding="utf-8")
    return rendered


def write_png(svg_path: Path, png_path: Path) -> None:
    try:
        import cairosvg  # type: ignore
    except Exception as exc:
        raise SystemExit(
            "PNG export requires CairoSVG plus the native Cairo runtime. "
            f"SVG was still written. CairoSVG import failed: {exc}"
        ) from exc
    try:
        cairosvg.svg2png(url=str(svg_path), write_to=str(png_path), output_width=1800)
    except Exception as exc:
        raise SystemExit(
            "PNG export failed. On Windows this usually means the native Cairo DLL "
            f"is missing. SVG was still written. Details: {exc}"
        ) from exc


def nice_ticks(lo: float, hi: float, count: int) -> list[float]:
    if hi <= lo:
        return [lo]
    raw = (hi - lo) / max(1, count - 1)
    mag = 10 ** math.floor(math.log10(raw))
    step = min((1, 2, 5, 10), key=lambda n: abs(n * mag - raw)) * mag
    start = math.ceil(lo / step) * step
    ticks = []
    val = start
    while val <= hi + step * 0.5:
        ticks.append(round(val, 8))
        val += step
    return ticks


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("deck", type=Path)
    parser.add_argument("--out", type=Path, help="SVG output path.")
    parser.add_argument("--title")
    parser.add_argument("--param", action="append", default=[], help="Override a Workbench/Tcl parameter, e.g. Lch=1.2")
    parser.add_argument("--png", type=Path, help="Optional PNG export path. Requires CairoSVG and native Cairo.")
    parser.add_argument("--analysis-out", type=Path, help="Optional Markdown analysis report path.")
    parser.add_argument("--analyze", action="store_true", help="Print the Markdown analysis report to stdout.")
    args = parser.parse_args()
    params = parse_param(args.param)
    if not args.out and not args.analysis_out and not args.analyze:
        parser.error("choose at least one of --out, --analysis-out, or --analyze")
    if args.out:
        render(args.deck, args.out, args.title, params)
    if args.png:
        if not args.out:
            parser.error("--png requires --out")
        write_png(args.out, args.png)
        print(f"Wrote {args.png}")
    if args.out:
        print(f"Wrote {args.out}")
    if args.analysis_out or args.analyze:
        report = write_analysis(args.deck, args.analysis_out, params)
        if args.analysis_out:
            print(f"Wrote {args.analysis_out}")
        if args.analyze:
            print(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
