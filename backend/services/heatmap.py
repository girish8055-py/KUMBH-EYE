import io
from datetime import datetime

import cv2
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np

from backend.state import heatmap_points, path_history


def build_heatmap(vid_id, W=800, H=450):
    points = heatmap_points.get(vid_id, [])
    path = list(path_history.get(vid_id, []))
    hmap = np.zeros((H, W), dtype=np.float32)
    for cx, cy in points:
        x = max(0, min(W - 1, int(cx * W)))
        y = max(0, min(H - 1, int(cy * H)))
        hmap[y, x] += 1
    if hmap.max() > 0:
        hmap = cv2.GaussianBlur(hmap, (61, 61), 0)
        hmap /= hmap.max()
    fig, ax = plt.subplots(figsize=(10, 5.6), facecolor="#0d1117")
    ax.set_facecolor("#0d1117")
    ax.set_xlim(0, W)
    ax.set_ylim(H, 0)
    if points:
        ax.imshow(hmap, cmap="inferno", alpha=0.92, aspect="auto",
                  extent=[0, W, H, 0], interpolation="bicubic")
        cbar = plt.colorbar(ax.images[0], ax=ax, fraction=0.02, pad=0.02)
        cbar.set_label("Activity Density", color="#8b949e", fontsize=9)
        plt.setp(plt.getp(cbar.ax.axes, "yticklabels"), color="#8b949e")
    else:
        ax.text(0.5, 0.5, "No activity data yet", ha="center", va="center",
                color="#484f58", fontsize=14, transform=ax.transAxes)
    if len(path) > 1:
        xs = [p[0] * W for p in path]
        ys = [p[1] * H for p in path]
        n = len(xs)
        cmap = plt.cm.cool
        for i in range(n - 1):
            frac = i / max(n - 2, 1)
            ax.plot([xs[i], xs[i + 1]], [ys[i], ys[i + 1]],
                    color=cmap(frac), linewidth=1.8, alpha=0.75, solid_capstyle="round")
        step = max(1, n // 12)
        for i in range(0, n - 1, step):
            dx = xs[i + 1] - xs[i]
            dy = ys[i + 1] - ys[i]
            if abs(dx) + abs(dy) < 2:
                continue
            ax.annotate("", xy=(xs[i + 1], ys[i + 1]), xytext=(xs[i], ys[i]),
                        arrowprops=dict(arrowstyle="-|>", color=cmap(i / max(n - 2, 1)),
                                       lw=1.0, mutation_scale=10))
        ax.scatter([xs[0]], [ys[0]], color="#3fb950", s=80, zorder=10,
                   edgecolors="white", linewidths=.8)
        ax.scatter([xs[-1]], [ys[-1]], color="#f85149", s=80, zorder=10,
                   edgecolors="white", linewidths=.8)
        ax.legend(handles=[
            mpatches.Patch(color="#3fb950", label=f"Start ({path[0][2][11:19]})"),
            mpatches.Patch(color="#f85149", label=f"Latest ({path[-1][2][11:19]})"),
            plt.Line2D([0], [0], color="#00c9a7", lw=2, label=f"Trail ({n} pts)"),
        ], loc="lower left", fontsize=8, framealpha=0.6, facecolor="#161b22",
                   edgecolor="#30363d", labelcolor="#e6edf3")
    tmap = {
        "crowd_1": "Crowd · Cam 1", "crowd_2": "Crowd · Cam 2",
        "vehicle_1": "Vehicle · Cam 1", "vehicle_2": "Vehicle · Cam 2",
        "parking_1": "Parking Lot",
    }
    ax.set_title(f"{tmap.get(vid_id, vid_id)} — Heatmap & Movement Trail",
                 color="#e6edf3", fontsize=12, pad=10, fontweight="bold")
    ax.tick_params(colors="#484f58")
    for sp in ax.spines.values():
        sp.set_edgecolor("#21262d")
    ax.text(0.99, 0.01, f"Generated {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            ha="right", va="bottom", color="#484f58", fontsize=7, transform=ax.transAxes)
    plt.tight_layout(pad=0.8)
    buf = io.BytesIO()
    plt.savefig(buf, format="png", dpi=110, bbox_inches="tight",
                facecolor="#0d1117", edgecolor="none")
    plt.close(fig)
    buf.seek(0)
    return buf.read()
