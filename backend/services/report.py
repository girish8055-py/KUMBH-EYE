import base64
import io
from collections import defaultdict
from datetime import datetime

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from backend.config.settings import VIDEOS_CFG
from backend.state import detection_history, alert_history


def _chart_b64(fig):
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=100, bbox_inches="tight",
                facecolor="#161b22", edgecolor="none")
    plt.close(fig)
    buf.seek(0)
    return base64.b64encode(buf.read()).decode()


def build_report(vid_id):
    hist = list(detection_history.get(vid_id, []))
    vtype = VIDEOS_CFG.get(vid_id, {}).get("type", "unknown")
    ts_now = datetime.now().strftime("%d %B %Y, %I:%M %p")
    cam = vid_id.replace("_", " ").upper()
    accent = {"crowd": "#00c9a7", "vehicle": "#f59e0b", "parking": "#a78bfa"}.get(vtype, "#3b82f6")
    rows = ""
    chart_imgs = ""
    if not hist:
        rows = '<tr><td colspan="2" style="text-align:center;color:#8b949e;padding:20px">No data yet.</td></tr>'
    else:
        ts = [h["timestamp"] for h in hist]
        if vtype == "crowd":
            counts = [h["count"] for h in hist]
            dens = [h["density"] for h in hist]
            confs = [h["avg_confidence"] for h in hist]
            levels = [h.get("density_level", "Low") for h in hist]
            rows = f"""<tr><td>Total Samples</td><td><strong>{len(hist)}</strong></td></tr>
              <tr><td>Avg Person Count</td><td><strong>{np.mean(counts):.1f}</strong></td></tr>
              <tr><td>Peak Count</td><td><strong>{max(counts)}</strong></td></tr>
              <tr><td>Avg Density</td><td><strong>{np.mean(dens):.4f}</strong></td></tr>
              <tr><td>Avg AI Confidence</td><td><strong>{np.mean(confs)*100:.1f}%</strong></td></tr>
              <tr><td>High-Level Frames</td><td><strong>{levels.count("High")} / {len(hist)}</strong></td></tr>"""
            fig, axes = plt.subplots(1, 2, figsize=(12, 4), facecolor="#161b22")
            for ax in axes:
                ax.set_facecolor("#1c2333")
            short_ts = [t[11:19] for t in ts]
            axes[0].plot(short_ts, counts, color=accent, lw=2)
            axes[0].fill_between(range(len(counts)), counts, alpha=.15, color=accent)
            axes[0].set_title("Person Count", color="#e6edf3", fontsize=11)
            axes[0].tick_params(colors="#484f58", labelsize=8)
            axes[0].xaxis.set_major_locator(plt.MaxNLocator(8))
            ld = {"Low": levels.count("Low"), "Medium": levels.count("Medium"), "High": levels.count("High")}
            axes[1].pie(list(ld.values()), labels=list(ld.keys()),
                        colors=["#3fb950", "#f59e0b", "#f85149"],
                        autopct="%1.0f%%", textprops={"color": "#e6edf3", "fontsize": 9})
            axes[1].set_title("Density Distribution", color="#e6edf3", fontsize=11)
            plt.tight_layout()
            chart_imgs = f'<img src="data:image/png;base64,{_chart_b64(fig)}" style="width:100%;border-radius:8px;margin:8px 0"/>'
        elif vtype == "vehicle":
            totals = [h["total_count"] for h in hist]
            dens = [h["density"] for h in hist]
            confs = [h["avg_confidence"] for h in hist]
            all_cls = defaultdict(int)
            for h in hist:
                for k, v in h.get("class_breakdown", {}).items():
                    all_cls[k] += v
            rows = f"""<tr><td>Total Samples</td><td><strong>{len(hist)}</strong></td></tr>
              <tr><td>Avg Vehicle Count</td><td><strong>{np.mean(totals):.1f}</strong></td></tr>
              <tr><td>Peak Count</td><td><strong>{max(totals)}</strong></td></tr>
              <tr><td>Avg Density</td><td><strong>{np.mean(dens):.4f}</strong></td></tr>
              <tr><td>Avg Confidence</td><td><strong>{np.mean(confs)*100:.1f}%</strong></td></tr>
              <tr><td>Top Vehicle Type</td><td><strong>{max(all_cls, key=all_cls.get) if all_cls else "N/A"}</strong></td></tr>"""
            fig, axes = plt.subplots(1, 2, figsize=(12, 4), facecolor="#161b22")
            for ax in axes:
                ax.set_facecolor("#1c2333")
            short_ts = [t[11:19] for t in ts]
            axes[0].plot(short_ts, totals, color=accent, lw=2)
            axes[0].fill_between(range(len(totals)), totals, alpha=.15, color=accent)
            axes[0].set_title("Vehicle Count", color="#e6edf3", fontsize=11)
            axes[0].tick_params(colors="#484f58", labelsize=8)
            axes[0].xaxis.set_major_locator(plt.MaxNLocator(8))
            if all_cls:
                clrs = ["#3b82f6", "#f59e0b", "#f85149", "#3fb950", "#a78bfa"]
                axes[1].bar(list(all_cls.keys()), list(all_cls.values()), color=clrs[:len(all_cls)])
                axes[1].tick_params(colors="#484f58", labelsize=8)
                axes[1].set_title("Vehicle Types", color="#e6edf3", fontsize=11)
            plt.tight_layout()
            chart_imgs = f'<img src="data:image/png;base64,{_chart_b64(fig)}" style="width:100%;border-radius:8px;margin:8px 0"/>'
        elif vtype == "parking":
            occ = [h["occupied"] for h in hist]
            avail = [h["available"] for h in hist]
            rates = [h["occupancy_rate"] for h in hist]
            rows = f"""<tr><td>Total Samples</td><td><strong>{len(hist)}</strong></td></tr>
              <tr><td>Avg Occupancy</td><td><strong>{np.mean(rates):.1f}%</strong></td></tr>
              <tr><td>Peak Occupancy</td><td><strong>{max(rates)}%</strong></td></tr>
              <tr><td>Min Occupancy</td><td><strong>{min(rates)}%</strong></td></tr>
              <tr><td>Times Full</td><td><strong>{sum(1 for r in rates if r>=100)} / {len(hist)}</strong></td></tr>
              <tr><td>Avg Free Slots</td><td><strong>{np.mean(avail):.1f}</strong></td></tr>"""
            fig, ax = plt.subplots(figsize=(12, 4), facecolor="#161b22")
            ax.set_facecolor("#1c2333")
            short_ts = [t[11:19] for t in ts]
            ax.fill_between(range(len(occ)), occ, color="#f85149", alpha=.6, label="Occupied")
            ax.fill_between(range(len(avail)), avail, color="#3fb950", alpha=.5, label="Available")
            ax.set_title("Slots Over Time", color="#e6edf3", fontsize=11)
            ax.tick_params(colors="#484f58", labelsize=8)
            ax.legend(labelcolor="#e6edf3", facecolor="#1c2333", edgecolor="#30363d")
            plt.tight_layout()
            chart_imgs = f'<img src="data:image/png;base64,{_chart_b64(fig)}" style="width:100%;border-radius:8px;margin:8px 0"/>'

    alert_rows = "".join(
        f'<tr><td style="padding:6px 12px;color:#8b949e;font-size:12px;border-bottom:1px solid #21262d">{a["timestamp"][11:19]}</td>'
        f'<td style="padding:6px 12px;color:#e6edf3;font-size:12px;border-bottom:1px solid #21262d">{a["title"]}</td></tr>'
        for a in alert_history if a.get("video_id") == vid_id
    ) or '<tr><td colspan="2" style="padding:14px;color:#484f58;font-size:12px">No alerts for this camera.</td></tr>'

    return f"""<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"/><title>SmartVision Report — {cam}</title>
<style>*{{margin:0;padding:0;box-sizing:border-box}}body{{font-family:'Segoe UI',system-ui,sans-serif;background:#0d1117;color:#e6edf3;padding:32px;max-width:860px;margin:0 auto}}
.rh{{display:flex;align-items:center;justify-content:space-between;margin-bottom:26px;padding-bottom:18px;border-bottom:2px solid {accent}}}
.rh-ic{{width:48px;height:48px;background:{accent};border-radius:11px;display:flex;align-items:center;justify-content:center;font-size:22px}}
h1{{font-size:20px;font-weight:700}}
.rm{{font-size:11px;color:#8b949e;margin-top:3px}}
.sec{{background:#161b22;border:1px solid #21262d;border-radius:11px;padding:20px;margin-bottom:18px}}
.sec h2{{font-size:12px;font-weight:600;color:{accent};text-transform:uppercase;letter-spacing:1px;margin-bottom:14px}}
table{{width:100%;border-collapse:collapse}}td{{padding:8px 12px;border-bottom:1px solid #21262d;font-size:12px;color:#8b949e}}td strong{{color:#e6edf3;font-weight:600}}tr:last-child td{{border-bottom:none}}
.badge{{display:inline-block;padding:2px 9px;border-radius:20px;font-size:10px;font-weight:600;background:rgba(0,201,167,.12);color:{accent};border:1px solid rgba(0,201,167,.25)}}
.footer{{text-align:center;color:#484f58;font-size:10px;margin-top:20px;padding-top:14px;border-top:1px solid #21262d}}
@media print{{body{{background:#fff;color:#000}}h1,.sec h2,td strong{{color:#000}}.sec{{border:1px solid #ccc;background:#f9f9f9}}}}
</style></head><body>
<div class="rh"><div style="display:flex;align-items:center;gap:14px"><div class="rh-ic">📊</div><div><h1>Surveillance Report — {cam}</h1><div class="rm">SmartVision AI · Generated {ts_now} · <span class="badge">{vtype.upper()}</span></div></div></div><div style="text-align:right;font-size:11px;color:#484f58"><div>Total Alerts: <strong style="color:#f85149">{sum(1 for a in alert_history if a.get("video_id")==vid_id)}</strong></div><div style="margin-top:3px">Data Points: <strong style="color:{accent}">{len(hist)}</strong></div></div></div>
<div class="sec"><h2>Summary Statistics</h2><table><tbody>{rows}</tbody></table></div>
<div class="sec"><h2>Trend Charts</h2>{chart_imgs or '<p style="color:#484f58;font-size:12px">No chart data yet.</p>'}</div>
<div class="sec"><h2>Alert History</h2><table><tbody>{alert_rows}</tbody></table></div>
<div class="footer">SmartVision Intelligent Surveillance &nbsp;·&nbsp; {ts_now}<br/><span style="font-size:9px">Print (Ctrl+P) to save as PDF</span></div>
</body></html>"""
