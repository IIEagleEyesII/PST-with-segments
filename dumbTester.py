import argparse
import importlib.util
from pathlib import Path

import matplotlib.pyplot as plt


def load_main_module():
    """
    Tester must set path to main here
    """
    path = "./main.py"
    spec = importlib.util.spec_from_file_location("pst_main", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

mod = load_main_module()
Point2D = mod.Point2D
Segment = mod.Segment
PSTleft = mod.PSTleft


class CollectRenderer:
    def __init__(self):
        self.items = []

    def report(self, segment):
        self.items.append(segment)


def seg_key(s: Segment):
    """
    This function is used to sort segments by their left point.
    """
    return (s.left_point.x, s.left_point.y, s.right_point.x, s.right_point.y)


def parse_segments_file(path: Path):
    segments = []
    with path.open("r", encoding="utf-8") as file:
        for line in file:
            line = line.strip()
            if not line:
                continue
            x1, y1, x2, y2 = map(float, line.split())
            p1 = Point2D(x1, y1)
            p2 = Point2D(x2, y2)
            segment = Segment(p1, p2)
            if segment.type == "horizontal":
                segments.append(segment)
    segments.sort(key=seg_key)
    return segments


def format_segment(s: Segment) -> str:
    return f"{s.left_point.x} {s.left_point.y} {s.right_point.x} {s.right_point.y}"


def render_query(segments, selected, qx, ymin, ymax):
    """
    Prety printer
    :param segments: all segments loaded from main
    :param selected: selected during the query
    :param qx: vertical line to delimit the query from the rigth side
    :param ymin: horizontal line to delimit the query from the bottom side
    :param ymax: horizontal line to delimit the query from the top side
    :return: None
    Selected segments are marked in red, the others in blue
     the query line is marked with a black dotted line
    """
    fig, ax = plt.subplots(figsize=(10, 7))

    for s in segments:
        ax.plot(
            [s.left_point.x, s.right_point.x],
            [s.left_point.y, s.right_point.y],
            color="royalblue",
            linewidth=1,
            zorder=1,
        )

    for s in selected:
        ax.plot(
            [s.left_point.x, s.right_point.x],
            [s.left_point.y, s.right_point.y],
            color="crimson",
            linewidth=1.8,
            zorder=3,
        )

    ax.axvline(qx, color="black", linestyle="--", linewidth=1.2, label=f"x <= {qx}")
    ax.axhline(ymin, color="seagreen", linestyle=":", linewidth=1.2, label=f"ymin={ymin}")
    ax.axhline(ymax, color="seagreen", linestyle=":", linewidth=1.2, label=f"ymax={ymax}")

    ax.set_title("PST query rendering")
    ax.set_xlabel("x")
    ax.set_ylabel("y")
    ax.grid(True, alpha=0.25)
    ax.legend(loc="best")
    plt.tight_layout()
    plt.show()


def run_query(scene_file="1000.txt", qx=500.0, ymin=-250.0, ymax=750.0):
    root = Path(__file__).resolve().parents[1]
    file_path = root / "scenes" / scene_file
    if not file_path.exists():
        raise FileNotFoundError(f"Fichier introuvable: {file_path}")

    segments = parse_segments_file(file_path)
    renderer = CollectRenderer()
    tree = PSTleft(segments, renderer=renderer)

    renderer.items = []
    tree.initialQuery(qx, ymin, ymax)
    selected = sorted(renderer.items, key=seg_key)

    print(f"Query: x <= {qx}, y in [{ymin}, {ymax}]")
    print(f"Total: {len(selected)} segment(s)")
    for segment in selected:
        print(format_segment(segment))

    render_query(segments, selected, qx, ymin, ymax)


def _build_cli_parser():
    parser = argparse.ArgumentParser(description="Run one PST query and render it with matplotlib")
    parser.add_argument("--scene", default="1000.txt", help="Scene file name inside scenes/")
    parser.add_argument("--qx", type=float, default=500.0, help="Upper x bound (x <= qx)")
    parser.add_argument("--ymin", type=float, default=-250.0, help="Lower y bound")
    parser.add_argument("--ymax", type=float, default=750.0, help="Upper y bound")
    return parser


if __name__ == "__main__":
    args = _build_cli_parser().parse_args()
    run_query(scene_file=args.scene, qx=args.qx, ymin=args.ymin, ymax=args.ymax)
