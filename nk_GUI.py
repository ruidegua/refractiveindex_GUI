"""
nk_GUI.py - Optical Constants (n, k) and Dielectric Function (eps1, eps2) Viewer
Based on refractiveindex.info database (bundled in ./db, CC0 public domain).

v0.5.8 (refractiveindex_GUI): small-screen layout fixes (Linux Mint).
        - Left control panel is now wrapped in a scrollable Canvas via
          the `_make_scrollable(parent)` helper, so all controls
          (including the Export CSV button at the bottom) remain
          reachable via mouse wheel / scrollbar on small screens where
          the total content height (~540 px) exceeds the left pane's
          visible content area. Before this fix Tk `pack` silently
          clipped the bottom widget on 1280x800 Linux Mint setups.
        - Right pane switched from `pack(expand=True)` to `grid` layout
          with `weight=1` on both plot rows so frame_nk and frame_eps
          always have the same height. Before, matplotlib's
          FigureCanvasTkAgg figsize-based natural-size request made
          the two plots render at different heights on 1280x800
          Linux Mint.
        - Mouse wheel handling in `_make_scrollable` covers macOS
          delta events, X11 Button-4/5 (Cinnamon), and Windows
          MouseWheel. Bound on canvas Enter, unbound on Leave.

v0.5.7 (refractiveindex_GUI): adaptive window geometry.
        - Replaced hard-coded `1200x900` default + `minsize(1000, 650)`
          with `_adaptive_geometry(root)` that reads
          `winfo_screenwidth/height` and picks a sensible size for the
          current display. Default = 85% of usable screen, clamped to
          [720, 1800] x [500, 1100] and capped so the window never
          exceeds the display. Minsize = 85% of default, floor
          [640, 440].
        - Left PanedWindow pane width is now `_left_panel_width(sw)`:
          min(430, max(280, 32% of screen width)). On a 1280-wide
          display this is 409 px; on 1024-wide it drops to 327 px
          so the right pane keeps room for the plots.
        - Behaviour on common resolutions:
            * 1920x1080 -> default 1598x867, left 430, minsize 1358x736
            * 1366x768  -> default 1127x601, left 430, minsize  957x510
            * 1280x800  -> default 1054x629, left 409, minsize  895x534
            * 1024x600  -> default  836x500, left 327, minsize  751x440
        - minsize_w also has a layout-aware floor (left pane + sash +
          right pane minsize + 20 px slack) so the panes always fit
          at minsize, not just at default.
        - Pure helpers `_compute_geometry(sw, sh) -> (w, h, min_w, min_h)`
          and `_left_panel_width(sw)` are unit-tested without a display.

v0.5.6 (refractiveindex_GUI): cross-platform compatibility fixes.
        - Window maximize is now platform-aware (helper _maximize_window):
          state('zoomed') on win32, no-op on darwin (Tk ignores it),
          try-zoomed-then-fallback-geometry on linux (some WMs, notably
          Wayland sessions and certain Cinnamon/MATE configs on Linux
          Mint, silently drop _NET_WM_STATE_MAXIMIZED_HORZ/VERT).
        - PanedWindow switched from ttk.PanedWindow to tk.PanedWindow
          (classic) for smoother sash drag on macOS and Linux. The ttk
          version redraws all child widgets on every sash motion event.

v0.5.4 (refractiveindex_GUI): CSV export wavelength units changed from nm
        to μm (column header wavelength_um, values divided by 1000). Most
        optics workflows and the upstream refractiveindex.info raw data
        files use μm.

v0.5.3 (refractiveindex_GUI): log-axis bug fixes.
        - Scroll zoom / Apply button / entry boxes all now work correctly
          when x or y is on a log scale. matplotlib's get_xlim/set_xlim
          always work in LINEAR values regardless of scale, but the previous
          code did spurious log<->linear conversions that broke zoom and
          entry-box round-tripping on log axes.
        - Apply button: now applies user limits AFTER plot, so they survive
          the autoscale reset that clear() triggers (previously silently
          dropped on both linear and log modes).
        - Range info text and entry boxes always show LINEAR values.

v0.5.2 (refractiveindex_GUI): extra-DB path is now ./db_extra/ (was ./pu_data/db/).
        CSV export simplified to 3 columns (wavelength_nm, n, k).

v0.5.1 (refractiveindex_GUI): prefer bundled db/ next to this script over the
        system DB shipped with the `refractiveindex` pip package, so the repo
        is self-contained. Title bar and DB_PATH reflect the choice at startup.

v0.5 (original): two independent plots (Refractive Index, Dielectric Function)
        in separate frames; left panel controls only the currently selected
        (active) plot; independent zoom/pan per plot.

Features:
  - Select material by shelf / book / page (3-level tree)
  - Two independent plot frames: n,k and eps1,eps2
  - X-axis switchable: wavelength (nm) or photon energy (eV) — synced across both plots
  - Per-plot Y range, log-Y toggle
  - Tab-style active-plot selector on left panel (radio buttons)
  - Rubber-band drag to zoom (mouse box select) — per plot
  - Mouse-wheel zoom (fixed) — per plot
  - Right-click drag to pan — per plot
  - Query n/k at a given wavelength or energy
  - Reset button to restore auto scale for active plot
  - Export data to CSV

Dependencies: numpy, matplotlib, tkinter (ttk), pyyaml, scipy, refractiveindex
"""

import sys
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from pathlib import Path
import re

import numpy as np
import matplotlib
matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import yaml
from scipy.interpolate import interp1d

import refractiveindex.refractiveindex as ri

# ════════════════════════════════════════════════════════════
# Theme Colors
# ════════════════════════════════════════════════════════════
BG       = "#1e1e2e"
FG       = "#cdd6f4"
SEL_BG   = "#313244"
SEL_FG   = "#cdd6f4"
ACCENT   = "#89b4fa"
ACCENT2  = "#f38ba8"
ENTRY_BG = "#181825"
BTN_BG   = "#313244"
BTN_FG   = "#cdd6f4"

# Prefer bundled db/ (next to this script) for self-contained use; fall back
# to the system DB distributed with the `refractiveindex` pip package. The
# bundled DB ships at the same layout (catalog-*.yml + data/<shelf>/<book>/...)
# as the upstream refractiveindex.info database, so no further changes needed.
_BUNDLED_DB = Path(__file__).resolve().parent / "db"
_SYSTEM_DB  = Path(ri._DEFAULT_DB_PATH)
if (_BUNDLED_DB / "catalog-nk.yml").exists():
    DB_PATH = _BUNDLED_DB
    _DB_SOURCE = "bundled (./db)"
else:
    DB_PATH = _SYSTEM_DB
    _DB_SOURCE = f"system ({ri._DEFAULT_DB_PATH})"

# Local database(s) (Pu: J. Appl. Phys. 125, 183102 - Appendices B & C,
# Sc: Sigrist 1987 + Henke 1993, etc.). The GUI auto-discovers any
# `catalog-*.yml` file in LOCAL_DB_PATH and merges it into CAT_NK. Add a
# new material by dropping a shelf directory under LOCAL_DB_PATH/ and
# creating a matching catalog-*.yml that points at it.
LOCAL_DB_PATH = Path(__file__).resolve().parent / "db_extra"

# ════════════════════════════════════════════════════════════
# Database loading
# ════════════════════════════════════════════════════════════
def _load_yaml(name, base=None):
    if base is None:
        base = DB_PATH
    with open(base / name, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

CAT_NK = _load_yaml("catalog-nk.yml")

# Merge all local catalog-*.yml files into CAT_NK. This lets us add new
# materials (Sc, future metals, alloys, ...) by dropping a shelf folder
# under LOCAL_DB_PATH and writing a matching catalog-<name>.yml -- no
# GUI changes needed.
if LOCAL_DB_PATH.exists():
    for catalog_file in sorted(LOCAL_DB_PATH.glob("catalog-*.yml")):
        try:
            local_catalog = _load_yaml(catalog_file.name, base=LOCAL_DB_PATH)
        except Exception as exc:
            print(f"[nk_GUI] WARN: failed to load {catalog_file.name}: {exc}")
            continue
        CAT_NK.extend(local_catalog)
        n_pages = sum(
            1
            for shelf in local_catalog
            for book in shelf.get("content", [])
            if "BOOK" in book
            for page in book.get("content", [])
            if "PAGE" in page
        )
        print(f"[nk_GUI] Loaded local catalog: {catalog_file.name} "
              f"({n_pages} page(s))")

def _build_index(catalog, local_base=None, local_shelves=()):
    idx = {}
    for shelf in catalog:
        if "SHELF" not in shelf:
            continue
        sid = shelf["SHELF"]
        is_local = local_base is not None and sid in local_shelves
        for book in shelf.get("content", []):
            if "BOOK" not in book:
                continue
            bid = book["BOOK"]
            for page in book.get("content", []):
                if "PAGE" not in page:
                    continue
                pid = page["PAGE"]
                data_path = page["data"]
                # Local DB entries have their own base; system entries use DB_PATH/data/
                if is_local:
                    idx[(sid, bid, pid)] = LOCAL_DB_PATH / data_path
                else:
                    idx[(sid, bid, pid)] = DB_PATH / "data" / data_path
    return idx


# Collect shelf IDs that originated from any local catalog-*.yml so the
# index builder knows where to look for their data files. CAT_NK is the
# merged system + local catalog; we re-derive local_shelves from the
# local_catalogs we already loaded (if any).
_LOCAL_SHELVES: set[str] = set()
if LOCAL_DB_PATH.exists():
    _LOCAL_SHELVES = {
        shelf["SHELF"]
        for catalog_file in LOCAL_DB_PATH.glob("catalog-*.yml")
        for shelf in _load_yaml(catalog_file.name, base=LOCAL_DB_PATH)
        if "SHELF" in shelf
    }

INDEX_NK = _build_index(CAT_NK, LOCAL_DB_PATH, _LOCAL_SHELVES)

def _extract_entries(catalog):
    entries = []
    for shelf in catalog:
        if "SHELF" not in shelf:
            continue
        sid, sname = shelf["SHELF"], shelf["name"]
        for book in shelf.get("content", []):
            if "BOOK" not in book:
                continue
            bid, bname = book["BOOK"], book["name"]
            for page in book.get("content", []):
                if "PAGE" not in page:
                    continue
                entries.append((sid, sname, bid, bname, page["PAGE"], page["name"]))
    return entries

ENTRIES = _extract_entries(CAT_NK)

def _build_tree(entries):
    tree = {}
    for sid, sname, bid, bname, pid, pname in entries:
        tree.setdefault(sid, {"_name": sname, "_books": {}})
        tree[sid]["_books"].setdefault(bid, {"_name": bname, "_pages": []})
        tree[sid]["_books"][bid]["_pages"].append((pid, pname))
    return tree

TREE = _build_tree(ENTRIES)

_HTML = re.compile(r"<[^>]+>")
def _strip(t):
    return _HTML.sub("", t) if t else ""


# ════════════════════════════════════════════════════════════
# Material data loader
# ════════════════════════════════════════════════════════════
def _load_material_data(shelf, book, page):
    key = (shelf, book, page)
    if key not in INDEX_NK:
        raise KeyError(f"Material not found: {key}")

    with open(INDEX_NK[key], "r", encoding="utf-8") as f:
        mat = yaml.safe_load(f)

    n_func = k_func = None
    wl_range = None

    for data in mat.get("DATA", []):
        dtype = data.get("type", "").split()
        cat, sub = dtype[0], dtype[1] if len(dtype) > 1 else None

        if cat == "tabulated":
            wl_list, c1_list, c2_list = [], [], []
            for line in data["data"].strip().split("\n"):
                p = line.split()
                wl_list.append(float(p[0]))
                c1_list.append(float(p[1]))
                c2_list.append(float(p[2]) if len(p) > 2 else None)
            wl_um = np.array(wl_list)
            c1 = np.array(c1_list)
            c2 = np.array([x for x in c2_list if x is not None])

            mk_i = lambda y: interp1d(wl_um, y, kind="cubic", bounds_error=False,
                                      fill_value=(y[0], y[-1]))
            if sub == "n":
                n_func = mk_i(c1)
                wl_range = (wl_um[0] * 1000, wl_um[-1] * 1000)
            elif sub == "k":
                k_func = mk_i(c1)
                wl_range = (wl_um[0] * 1000, wl_um[-1] * 1000)
            elif sub == "nk":
                n_func = mk_i(c1)
                k_func = mk_i(c2)
                wl_range = (wl_um[0] * 1000, wl_um[-1] * 1000)

        elif cat == "formula":
            fid = int(sub)
            coeffs = [float(x) for x in data["coefficients"].split()]
            for rk in ("range", "wavelength_range"):
                if rk in data:
                    break
            rm, rM = [float(x) for x in data[rk].split()]
            wl_range = (rm * 1000, rM * 1000)
            n_func = lambda w, f=fid, c=coeffs: ri._compute_formula(f, c, w)

    if wl_range is None:
        raise ValueError(f"No wavelength range for {key}")

    wl_nm = np.linspace(wl_range[0], wl_range[1], 800)
    wl_um = wl_nm / 1000.0
    n = np.asarray(n_func(wl_um)) if n_func else np.zeros_like(wl_nm)
    k = np.asarray(k_func(wl_um)) if k_func else np.zeros_like(wl_nm)
    return wl_nm, n, k


# ════════════════════════════════════════════════════════════
# Rubber-band zoom manager (left button) — per-axis
# ════════════════════════════════════════════════════════════
class _ZoomManager:
    def __init__(self, ax, on_zoom):
        self.ax = ax
        self.on_zoom = on_zoom
        self._drag_start = None
        self._artists = []

        canvas = ax.figure.canvas
        canvas.mpl_connect("button_press_event",   self._on_press)
        canvas.mpl_connect("motion_notify_event",  self._on_motion)
        canvas.mpl_connect("button_release_event", self._on_release)

    def _xy_from_event(self, event):
        if event.inaxes is not None and event.inaxes is self.ax:
            xy = self.ax.transData.inverted().transform((event.x, event.y))
            return xy[0], xy[1]
        return None

    def _draw_rect(self, x0, y0, x1, y1):
        ax = self.ax
        for a in self._artists:
            a.remove()
        self._artists.clear()

        x, y = min(x0, x1), min(y0, y1)
        w, h = abs(x1 - x0), abs(y1 - y0)
        xr = ax.get_xlim()[1] - ax.get_xlim()[0]
        yr = ax.get_ylim()[1] - ax.get_ylim()[0]
        if w < xr * 0.01 or h < yr * 0.01:
            return

        rect = matplotlib.patches.Rectangle(
            (x, y), w, h,
            linewidth=1.2, edgecolor=ACCENT, facecolor=ACCENT,
            alpha=0.15, zorder=10, transform=ax.transData)
        ax.add_patch(rect)
        self._artists.append(rect)

        for xp in (x, x + w):
            l, = ax.plot([xp, xp], [y, y + h], color=ACCENT,
                         lw=0.8, ls="--", alpha=0.6, zorder=10)
            self._artists.append(l)
        for yp in (y, y + h):
            l, = ax.plot([x, x + w], [yp, yp], color=ACCENT,
                         lw=0.8, ls="--", alpha=0.6, zorder=10)
            self._artists.append(l)

        ax.figure.canvas.draw_idle()

    def _on_press(self, event):
        if event.button != 1 or event.inaxes is None or event.inaxes is not self.ax:
            return
        self._drag_start = self._xy_from_event(event)

    def _on_motion(self, event):
        if self._drag_start is None:
            return
        if event.inaxes is not self.ax:
            return
        xy = self._xy_from_event(event)
        if xy is None:
            return
        self._draw_rect(self._drag_start[0], self._drag_start[1], xy[0], xy[1])

    def _on_release(self, event):
        if self._drag_start is None or event.button != 1:
            return

        xy = self._xy_from_event(event)
        for a in self._artists:
            a.remove()
        self._artists.clear()
        self.ax.figure.canvas.draw_idle()

        x0, y0 = self._drag_start
        self._drag_start = None

        if xy is None:
            return

        x1, y1 = xy[0], xy[1]
        dx = abs(x1 - x0)
        dy = abs(y1 - y0)
        x_range = self.ax.get_xlim()
        y_range = self.ax.get_ylim()
        if dx < (x_range[1] - x_range[0]) * 0.01 or dy < (y_range[1] - y_range[0]) * 0.01:
            return

        self.on_zoom(self.ax, min(x0, x1), max(x0, x1), min(y0, y1), max(y0, y1))


# ════════════════════════════════════════════════════════════
# Pan manager (right button drag) — per-axis
# ════════════════════════════════════════════════════════════
class _PanManager:
    def __init__(self, ax):
        self.ax = ax
        self._drag_start = None
        self._xlim_start = None
        self._ylim_start = None

        canvas = ax.figure.canvas
        canvas.mpl_connect("button_press_event",   self._on_press)
        canvas.mpl_connect("motion_notify_event",  self._on_motion)
        canvas.mpl_connect("button_release_event", self._on_release)

    def _on_press(self, event):
        if event.button != 3 or event.inaxes is None or event.inaxes is not self.ax:
            return
        self._drag_start = (event.x, event.y)
        self._xlim_start = self.ax.get_xlim()
        self._ylim_start = self.ax.get_ylim()

    def _on_motion(self, event):
        if self._drag_start is None or event.inaxes is None or event.inaxes is not self.ax:
            return

        ax = self.ax
        dx_data = ax.transData.inverted().transform(
            (event.x, event.y))[0] - ax.transData.inverted().transform(
            self._drag_start)[0]
        dy_data = ax.transData.inverted().transform(
            (event.x, event.y))[1] - ax.transData.inverted().transform(
            self._drag_start)[1]
        ax.set_xlim(self._xlim_start[0] - dx_data, self._xlim_start[1] - dx_data)
        ax.set_ylim(self._ylim_start[0] - dy_data, self._ylim_start[1] - dy_data)
        ax.figure.canvas.draw_idle()

    def _on_release(self, event):
        if event.button != 3:
            return
        self._drag_start = None
        self._xlim_start = None
        self._ylim_start = None


# ════════════════════════════════════════════════════════════
# Helpers
# ════════════════════════════════════════════════════════════
WL_TO_EN = lambda wl: 1240.0 / wl
EN_TO_WL = lambda en: 1240.0 / en


def _make_scrollable(parent):
    """Wrap a Frame in a Canvas + vertical scrollbar so content can be
    scrolled when it exceeds the visible area. Returns the inner Frame
    that widgets should be packed / gridded into.

    Used by the left control panel so all controls remain reachable
    even on small screens (e.g. 1280x800 with Linux Mint decorations,
    where WM chrome + theme can leave the left pane with less content
    area than the total height of the controls). Without scrolling,
    Tk pack silently clips the bottom widgets -- Export CSV at the
    bottom of the panel was unreachable on some Linux Mint setups.

    Mouse wheel handling: bind when cursor enters canvas, unbind on leave.
    Handles:
      - macOS / Windows MouseWheel (event.delta is +/-120 per notch)
      - X11 Button-4 (scroll up) and Button-5 (scroll down), which some
        Linux WMs (including Cinnamon) deliver in addition to or in
        place of MouseWheel.
    """
    wrapper = ttk.Frame(parent)
    wrapper.pack(fill="both", expand=True)

    canvas = tk.Canvas(wrapper, highlightthickness=0, borderwidth=0,
                       takefocus=0)
    vsb = ttk.Scrollbar(wrapper, orient="vertical", command=canvas.yview)
    canvas.configure(yscrollcommand=vsb.set)

    vsb.pack(side="right", fill="y")
    canvas.pack(side="left", fill="both", expand=True)

    inner = ttk.Frame(canvas)
    window_id = canvas.create_window((0, 0), window=inner, anchor="nw")

    # Keep scrollregion in sync with inner Frame size
    def _on_inner_configure(_event):
        canvas.configure(scrollregion=canvas.bbox("all"))
    inner.bind("<Configure>", _on_inner_configure)

    # Match inner Frame width to canvas width so widgets fill horizontally
    def _on_canvas_configure(event):
        canvas.itemconfigure(window_id, width=event.width)
    canvas.bind("<Configure>", _on_canvas_configure)

    def _on_wheel(event):
        if event.num == 4:
            delta = -1   # X11 scroll up
        elif event.num == 5:
            delta = 1    # X11 scroll down
        else:
            # macOS / Windows: delta > 0 means scroll up
            delta = -1 if event.delta > 0 else 1
        canvas.yview_scroll(delta, "units")

    def _on_enter(_event):
        canvas.bind_all("<MouseWheel>", _on_wheel)
        canvas.bind_all("<Button-4>", _on_wheel)
        canvas.bind_all("<Button-5>", _on_wheel)

    def _on_leave(_event):
        canvas.unbind_all("<MouseWheel>")
        canvas.unbind_all("<Button-4>")
        canvas.unbind_all("<Button-5>")

    canvas.bind("<Enter>", _on_enter)
    canvas.bind("<Leave>", _on_leave)

    return inner


# ════════════════════════════════════════════════════════════
# Main GUI
# ════════════════════════════════════════════════════════════
class NkCurveGUI:

    XAXIS_MODES  = ["wavelength", "energy"]
    XAXIS_LABELS = {"wavelength": "Wavelength (nm)", "energy": "Photon Energy (eV)"}
    PLOT_MODES   = ["nk", "eps"]

    def __init__(self, root):
        self.root = root
        root.title(f"nk Curve Viewer v0.5.8 — refractiveindex.info ({_DB_SOURCE})")
        # Adapt default size + minsize to the actual screen so the window
        # never opens larger than the display and never below a usable
        # floor. See _adaptive_geometry() below for the math.
        self._screen_w, self._screen_h = _adaptive_geometry(root)
        _maximize_window(root)   # platform-aware: zoomed on win32, no-op on darwin, fallback geometry on linux
        root.configure(bg=BG)

        self.wavelengths = self.n_vals = self.k_vals = None
        self.material_label = ""
        self._interp_n = self._interp_k = None

        # Internal x range stored in nanometers (wl space)
        self._xmin_wl = None
        self._xmax_wl = None

        # Stored y ranges for each plot (used as "last known" for sync)
        self._ymin_nk  = None
        self._ymax_nk  = None
        self._ymin_eps = None
        self._ymax_eps = None

        # X log scale — shared across both plots
        self._xlog = False

        # Suppress sync-to-entries during _update_plot (prevents Apply overwriting user input)
        self._suppress_sync_to_entries = False

        self._style()
        self._build_ui()
        self._update_plot()

    def _style(self):
        s = ttk.Style()
        s.theme_use("clam")
        s.configure("Treeview", background=ENTRY_BG, foreground=FG,
                    fieldbackground=ENTRY_BG, rowheight=22)
        s.configure("Treeview.Heading", background=SEL_BG, foreground=FG,
                    font=("Arial", 10, "bold"))
        s.map("Treeview", background=[("selected", SEL_BG)],
              foreground=[("selected", SEL_FG)])

    def _build_ui(self):
        # Use tk.PanedWindow (classic) instead of ttk.PanedWindow. The ttk
        # version's sash drag is janky on macOS — every motion event triggers
        # a full redraw of all child widgets. Classic tk.PanedWindow uses
        # native window handles and stays smooth on all three OSes.
        # On Linux/X11/Cinnamon, ttk.PanedWindow also has occasional sash
        # re-render glitches; classic tk is responsive everywhere.
        paned = tk.PanedWindow(self.root, orient=tk.HORIZONTAL,
                               sashrelief=tk.RAISED, sashwidth=4,
                               bg=BG, bd=0)
        paned.pack(fill=tk.BOTH, expand=True, padx=6, pady=6)

        left = tk.Frame(paned, bg=BG)
        # Left pane width: 430 on normal/large screens, shrinks on small
        # displays (e.g. 1024-wide) so the right pane keeps room for the
        # plots. See _left_panel_width() for the rule.
        left_w = _left_panel_width(self._screen_w)
        paned.add(left, minsize=200, stretch="never", width=left_w)
        self._build_left(left)

        right = tk.Frame(paned, bg=BG)
        paned.add(right, minsize=400, stretch="always")
        self._build_right(right)

    def _build_left(self, parent):
        # Wrap in a scrollable Canvas so all controls (including Export
        # CSV at the bottom) remain reachable on small screens where the
        # total content height exceeds the left pane's visible area.
        # Without this, Tk pack silently clips the bottom widget, which
        # made Export CSV unreachable on 1280x800 Linux Mint setups
        # where WM decorations reduced the visible content area.
        parent = _make_scrollable(parent)
        ttk.Label(parent, text=f"NK Catalog: {len(ENTRIES)} entries",
                  foreground="gray", font=("Arial", 9)).pack(fill="x", pady=(0, 6))

        # Search
        sf = ttk.Frame(parent)
        sf.pack(fill="x", pady=(0, 4))
        ttk.Label(sf, text="Search:").pack(side="left")
        self.search_var = tk.StringVar()
        ttk.Entry(sf, textvariable=self.search_var).pack(
            side="left", fill="x", expand=True, padx=(4, 0))
        self.search_var.trace("w", lambda *_: self._populate_tree(self.search_var.get()))

        # Tree
        tf = ttk.Frame(parent)
        tf.pack(fill="both", expand=True, pady=(0, 6))

        self.tree = ttk.Treeview(tf, columns=("name",), show="tree headings",
                                 selectmode="browse")
        self.tree.heading("#0", text="Path")
        self.tree.heading("name", text="Name")
        self.tree.column("#0", width=155)
        self.tree.column("name", width=260)

        vsb = ttk.Scrollbar(tf, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(tf, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        tf.rowconfigure(0, weight=1)
        tf.columnconfigure(0, weight=1)
        self.tree.bind("<<TreeviewSelect>>", self._on_select)

        # ── Active Plot Selector ──────────────────────────
        pf = ttk.LabelFrame(parent, text=" Active Plot ", padding=(8, 4))
        pf.pack(fill="x", pady=(0, 4))

        self.active_plot = tk.StringVar(value="nk")
        ttk.Radiobutton(pf, text="Refractive Index (n, k)",
                        variable=self.active_plot, value="nk",
                        command=self._on_active_plot_changed).pack(anchor="w")
        ttk.Radiobutton(pf, text="Dielectric Function (ε1, ε2)",
                        variable=self.active_plot, value="eps",
                        command=self._on_active_plot_changed).pack(anchor="w")

        # ── Options ───────────────────────────────────────
        of = ttk.LabelFrame(parent, text=" Options ", padding=(8, 4))
        of.pack(fill="x", pady=(0, 4))

        ttk.Label(of, text="X-Axis:").pack(anchor="w")
        self.xaxis_var = tk.StringVar(value="wavelength")
        for m in self.XAXIS_MODES:
            ttk.Radiobutton(of, text=self.XAXIS_LABELS[m],
                            variable=self.xaxis_var, value=m,
                            command=self._on_xaxis_changed).pack(anchor="w", padx=8)

        # Log X — shared
        self.xlog_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(of, text="Log X", variable=self.xlog_var,
                        command=self._on_xlog_changed).pack(anchor="w")

        ttk.Separator(of, orient="horizontal").pack(fill="x", pady=6)

        # X range — shared (both plots use same x)
        xr = ttk.Frame(of)
        xr.pack(fill="x")
        ttk.Label(xr, text="X Min:").grid(row=0, column=0, sticky="e")
        self.xmin = tk.StringVar()
        ttk.Entry(xr, textvariable=self.xmin, width=9).grid(
            row=0, column=1, padx=(4, 8))
        ttk.Label(xr, text="X Max:").grid(row=0, column=2, sticky="e")
        self.xmax = tk.StringVar()
        ttk.Entry(xr, textvariable=self.xmax, width=9).grid(
            row=0, column=3, padx=(4, 0))

        # Y range — label updates with active plot
        self.yr_label = ttk.Label(of, text="Y Min (n,k):")
        self.yr_label.pack(anchor="w")

        yr = ttk.Frame(of)
        yr.pack(fill="x")
        ttk.Label(yr, text="Y Min:").grid(row=0, column=0, sticky="e")
        self.ymin = tk.StringVar()
        ttk.Entry(yr, textvariable=self.ymin, width=9).grid(
            row=0, column=1, padx=(4, 8))
        ttk.Label(yr, text="Y Max:").grid(row=0, column=2, sticky="e")
        self.ymax = tk.StringVar()
        ttk.Entry(yr, textvariable=self.ymax, width=9).grid(
            row=0, column=3, padx=(4, 0))

        # Log Y — per plot
        self.ylog_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(of, text="Log Y (active plot)", variable=self.ylog_var,
                        command=self._on_ylog_changed).pack(anchor="w")

        btn_row = ttk.Frame(of)
        btn_row.pack(fill="x", pady=(4, 0))
        ttk.Button(btn_row, text="Apply", command=self._update_plot).pack(
            side="left", fill="x", expand=True)
        ttk.Button(btn_row, text="Reset Active",
                   command=self._reset_active_range).pack(
            side="left", fill="x", expand=True, padx=(4, 0))

        # ── Query ─────────────────────────────────────────
        qf = ttk.LabelFrame(parent, text=" Query n / k ", padding=(8, 4))
        qf.pack(fill="x", pady=(0, 4))

        qinput = ttk.Frame(qf)
        qinput.pack(fill="x")
        self.query_var = tk.StringVar()
        ttk.Entry(qinput, textvariable=self.query_var, width=10).grid(
            row=0, column=0, padx=(0, 4))
        self.xaxis_q = tk.StringVar(value="nm")
        ttk.Radiobutton(qinput, text="nm", variable=self.xaxis_q,
                        value="nm").grid(row=0, column=1)
        ttk.Radiobutton(qinput, text="eV", variable=self.xaxis_q,
                        value="eV").grid(row=0, column=2)
        ttk.Button(qinput, text="Query", command=self._query_nk).grid(
            row=0, column=3, padx=(4, 0))

        self.query_result = ttk.Label(qf, text="", foreground=ACCENT,
                                      font=("Arial", 9))
        self.query_result.pack(fill="x", pady=(2, 0))
        self.query_result2 = ttk.Label(qf, text="", foreground=ACCENT,
                                       font=("Arial", 9))
        self.query_result2.pack(fill="x")

        # Status
        self.info = ttk.Label(parent, text="Select a material",
                              foreground="gray", font=("Arial", 9))
        self.info.pack(fill="x", pady=(0, 4))

        ttk.Button(parent, text="Export CSV", command=self._export).pack(fill="x")

        self._populate_tree()

    def _build_right(self, parent):
        # Use grid layout for the two plot frames with equal weights on
        # the rows, so they always have the same height. pack(expand=True)
        # on both frames nominally does the same, but matplotlib's
        # FigureCanvasTkAgg has a figsize-based natural size request
        # (8x4.2 in @ 110 dpi = 880x462 px) that pack doesn't always
        # honour consistently across themes / window managers. Grid
        # forces equal allocation regardless. v0.5.8 regression for
        # 1280x800 Linux Mint where the two plots rendered at different
        # heights.
        self.hint = ttk.Label(parent,
                              text="Drag to zoom  ·  Right-click to pan  ·  Scroll to zoom  ·  Click tab to switch active plot",
                              font=("Arial", 8), foreground="gray")
        self.frame_nk = ttk.LabelFrame(parent, text=" Refractive Index (n, k) ",
                                       padding=(4, 2))
        self.frame_eps = ttk.LabelFrame(parent, text=" Dielectric Function (ε1, ε2) ",
                                        padding=(4, 2))

        parent.columnconfigure(0, weight=1)
        parent.rowconfigure(0, weight=0)   # hint: natural height
        parent.rowconfigure(1, weight=1)   # frame_nk: equal expand
        parent.rowconfigure(2, weight=1)   # frame_eps: equal expand

        self.hint.grid(row=0, column=0, sticky="ew", pady=(0, 4))
        self.frame_nk.grid(row=1, column=0, sticky="nsew", pady=(0, 4))
        self.frame_eps.grid(row=2, column=0, sticky="nsew")
        self.lbl_nk = ttk.Label(self.frame_nk, text="", font=("Arial", 8),
                                foreground=ACCENT, padding=(2, 0))
        # Pack label at top of frame before canvas
        self.lbl_nk.pack(fill="x", padx=(6, 6), pady=(2, 0))

        self.fig_nk = Figure(figsize=(8, 4.2), dpi=110,
                             facecolor=BG, edgecolor=BG)
        self.canvas_nk = FigureCanvasTkAgg(self.fig_nk, master=self.frame_nk)
        self.canvas_nk.get_tk_widget().pack(fill="both", expand=True)
        self.ax_nk = self.fig_nk.add_subplot(111)
        self.fig_nk.subplots_adjust(left=0.09, right=0.88, bottom=0.12, top=0.92)

        self.canvas_nk.mpl_connect("scroll_event", self._on_scroll_nk)
        self._zoom_nk = _ZoomManager(self.ax_nk, on_zoom=self._apply_zoom_nk)
        self._pan_nk  = _PanManager(self.ax_nk)

        # ── Dielectric Function frame contents ───────────
        # (self.frame_eps was created above for grid placement)
        self.lbl_eps = ttk.Label(self.frame_eps, text="", font=("Arial", 8),
                                 foreground=ACCENT, padding=(2, 0))
        self.lbl_eps.pack(fill="x", padx=(6, 6), pady=(2, 0))

        self.fig_eps = Figure(figsize=(8, 4.2), dpi=110,
                              facecolor=BG, edgecolor=BG)
        self.canvas_eps = FigureCanvasTkAgg(self.fig_eps, master=self.frame_eps)
        self.canvas_eps.get_tk_widget().pack(fill="both", expand=True)
        self.ax_eps = self.fig_eps.add_subplot(111)
        self.fig_eps.subplots_adjust(left=0.09, right=0.88, bottom=0.12, top=0.92)

        self.canvas_eps.mpl_connect("scroll_event", self._on_scroll_eps)
        self._zoom_eps = _ZoomManager(self.ax_eps, on_zoom=self._apply_zoom_eps)
        self._pan_eps  = _PanManager(self.ax_eps)

    # ════════════════════════════════════════════════════════
    # Tree
    # ════════════════════════════════════════════════════════
    def _populate_tree(self, query=""):
        tree = self.tree
        tree.delete(*tree.get_children())
        q = query.lower().strip()

        def match(t):
            return not q or q in t.lower()

        if q:
            matching_pages = set()
            for sid in TREE:
                if sid == "_name":
                    continue
                for bid in TREE[sid]["_books"]:
                    if bid == "_name":
                        continue
                    for pid, pname in TREE[sid]["_books"][bid]["_pages"]:
                        if match(_strip(pname)) or match(pid):
                            matching_pages.add((sid, bid, pid))
            matching_shelves = {(s, b) for s, b, _ in matching_pages}
            matching_books   = {s for s, _, _ in matching_pages}
        else:
            matching_pages   = None
            matching_shelves = None
            matching_books   = None

        for sid in TREE:
            if sid == "_name":
                continue
            sname = _strip(TREE[sid]["_name"])
            if q and sid not in matching_books:
                continue

            si = tree.insert("", "end", text=sid, values=(sname,))

            for bid in TREE[sid]["_books"]:
                if bid == "_name":
                    continue
                bname = _strip(TREE[sid]["_books"][bid]["_name"])
                if q and (sid, bid) not in matching_shelves:
                    continue

                bi = tree.insert(si, "end", text=bid, values=(bname,))

                for pid, pname in TREE[sid]["_books"][bid]["_pages"]:
                    full_pname = _strip(pname)
                    if q and (sid, bid, pid) not in matching_pages:
                        continue
                    tree.insert(bi, "end", text=pid, values=(full_pname,))

        if tree.get_children():
            tree.item(tree.get_children()[0], open=True)

    def _on_select(self, event=None):
        sel = self.tree.selection()
        if not sel:
            return
        iid = sel[0]
        if self.tree.get_children(iid):
            return
        book_iid  = self.tree.parent(iid)
        shelf_iid = self.tree.parent(book_iid)
        shelf = self.tree.item(shelf_iid, "text")
        book  = self.tree.item(book_iid, "text")
        page  = self.tree.item(iid, "text")
        self._load(shelf, book, page)

    # ════════════════════════════════════════════════════════
    # Load material
    # ════════════════════════════════════════════════════════
    def _load(self, shelf, book, page):
        try:
            wl, n, k = _load_material_data(shelf, book, page)
            self.wavelengths = wl
            self.n_vals = n
            self.k_vals = k

            self._interp_n = interp1d(wl, n, kind="cubic",
                                      bounds_error=False, fill_value=(n[0], n[-1]))
            self._interp_k = interp1d(wl, k, kind="cubic",
                                      bounds_error=False, fill_value=(k[0], k[-1]))

            self._xmin_wl = float(wl.min())
            self._xmax_wl = float(wl.max())

            bid = None
            for si in self.tree.get_children():
                for bi in self.tree.get_children(si):
                    if self.tree.item(bi, "text") == book:
                        bid = bi
                        break
            bname = self.tree.item(bid, "values")[0] if bid else book
            self.material_label = f"{_strip(bname)} — {page}"
            # Update entry info labels in right-side LabelFrames
            self.lbl_nk.config(text=self.material_label)
            self.lbl_eps.config(text=self.material_label)
            self.info.config(
                text=f"Loaded: {shelf} / {book} / {page}\n"
                     f"Range: {wl[0]:.1f} – {wl[-1]:.1f} nm")
            self.query_result.config(text="")
            self.query_result2.config(text="")
        except Exception as ex:
            self.info.config(text=f"Error: {type(ex).__name__}: {ex}")
            self.lbl_nk.config(text="")
            self.lbl_eps.config(text="")
            self.wavelengths = self.n_vals = self.k_vals = None
            self._interp_n = self._interp_k = None
            self._xmin_wl = self._xmax_wl = None

        self._update_plot()

    # ════════════════════════════════════════════════════════
    # Active plot switch — sync entry widgets from current plot state
    # ════════════════════════════════════════════════════════
    def _on_active_plot_changed(self):
        self._sync_entries_from_active_plot()
        self._update_plot()

    def _sync_entries_from_active_plot(self):
        """Pull current axis limits from the active plot into entry widgets."""
        active = self.active_plot.get()
        xmode = self.xaxis_var.get()

        if active == "nk":
            ax = self.ax_nk
            self.yr_label.config(text="Y Min (n,k):")
        else:
            ax = self.ax_eps
            self.yr_label.config(text="Y Min (ε):")

        # X entries — from active plot's x axis (shared, but use active for consistency)
        xlo, xhi = ax.get_xlim()
        if xmode == "energy":
            self.xmin.set(f"{xhi:.4g}")
            self.xmax.set(f"{xlo:.4g}")
        else:
            self.xmin.set(f"{xlo:.4g}")
            self.xmax.set(f"{xhi:.4g}")

        # Y entries
        ylo, yhi = ax.get_ylim()
        self.ymin.set(f"{ylo:.4g}")
        self.ymax.set(f"{yhi:.4g}")

        # Log Y
        self.ylog_var.set(ylog_get(ax))

    def _sync_active_plot_from_entries(self):
        """Sync ylog state from the UI checkbox into the active plot's state dict.
        Kept for compatibility with toggle handlers; the actual x/y limits are
        applied AFTER plot by _apply_xy_from_entries so they survive autoscale.
        """
        ax = self.ax_nk if self.active_plot.get() == "nk" else self.ax_eps
        ylog_set(ax, self.ylog_var.get())

    def _apply_xy_from_entries(self):
        """Apply xmin/xmax/ymin/ymax from entry boxes to axes. Called after
        _update_plot's clear+plot so the user's limits survive autoscale reset.

        Log-axis handling: the entry boxes always show LINEAR values (nm / eV /
        n / k / ε), so when the axis is log we convert linear -> log for set_*
        via the _set_*_linear helpers. Values <= 0 are silently dropped on a
        log axis.
        """
        # X (shared across both plots since both use the same x range)
        try:
            xmin_v = float(self.xmin.get().strip()) if self.xmin.get().strip() else None
            xmax_v = float(self.xmax.get().strip()) if self.xmax.get().strip() else None
        except ValueError:
            xmin_v = xmax_v = None

        if xmin_v is not None or xmax_v is not None:
            cur_lo, cur_hi = _xlim_linear(self.ax_nk)
            new_lo = xmin_v if xmin_v is not None else cur_lo
            new_hi = xmax_v if xmax_v is not None else cur_hi
            if new_lo < new_hi:
                if _set_xlim_linear(self.ax_nk, new_lo, new_hi):
                    _set_xlim_linear(self.ax_eps, new_lo, new_hi)

        # Y (active plot only)
        try:
            ymin_v = float(self.ymin.get().strip()) if self.ymin.get().strip() else None
            ymax_v = float(self.ymax.get().strip()) if self.ymax.get().strip() else None
        except ValueError:
            ymin_v = ymax_v = None

        ax_active = self.ax_nk if self.active_plot.get() == "nk" else self.ax_eps
        if ymin_v is not None or ymax_v is not None:
            cur_lo, cur_hi = _ylim_linear(ax_active)
            new_lo = ymin_v if ymin_v is not None else cur_lo
            new_hi = ymax_v if ymax_v is not None else cur_hi
            if new_lo < new_hi:
                _set_ylim_linear(ax_active, new_lo, new_hi)

        # Keep internal ymin/ymax mirrors in sync (used by other code paths)
        ylo, yhi = _ylim_linear(ax_active)
        if ax_active is self.ax_nk:
            self._ymin_nk, self._ymax_nk = ylo, yhi
        else:
            self._ymin_eps, self._ymax_eps = ylo, yhi

    # ════════════════════════════════════════════════════════
    # X-axis mode switch
    # ════════════════════════════════════════════════════════
    def _on_xaxis_changed(self):
        xmode = self.xaxis_var.get()

        try:
            cur_xmin = float(self.xmin.get().strip()) if self.xmin.get().strip() else None
            cur_xmax = float(self.xmax.get().strip()) if self.xmax.get().strip() else None
        except ValueError:
            cur_xmin = cur_xmax = None

        if cur_xmin is not None and cur_xmax is not None:
            if xmode == "energy":
                wl_min = EN_TO_WL(cur_xmin)
                wl_max = EN_TO_WL(cur_xmax)
            else:
                wl_min, wl_max = cur_xmin, cur_xmax

            self._xmin_wl = wl_min
            self._xmax_wl = wl_max

            if xmode == "energy":
                self.xmin.set(f"{WL_TO_EN(wl_max):.4g}")
                self.xmax.set(f"{WL_TO_EN(wl_min):.4g}")
            else:
                self.xmin.set(f"{wl_min:.4g}")
                self.xmax.set(f"{wl_max:.4g}")

        self._update_plot()

    def _on_xlog_changed(self):
        self._xlog = self.xlog_var.get()
        self._update_plot()

    def _on_ylog_changed(self):
        self._update_plot()

    # ════════════════════════════════════════════════════════
    # Reset active plot range
    # ════════════════════════════════════════════════════════
    def _reset_active_range(self):
        active = self.active_plot.get()
        self.xmin.set("")
        self.xmax.set("")
        self.ymin.set("")
        self.ymax.set("")
        self.ylog_var.set(False)
        if self.wavelengths is not None:
            self._xmin_wl = float(self.wavelengths.min())
            self._xmax_wl = float(self.wavelengths.max())
        if active == "nk":
            self._ymin_nk = self._ymax_nk = None
        else:
            self._ymin_eps = self._ymax_eps = None
        self._update_plot()

    # ════════════════════════════════════════════════════════
    # Query
    # ════════════════════════════════════════════════════════
    def _query_nk(self):
        if self.wavelengths is None:
            self.query_result.config(text="No material loaded.")
            return

        try:
            val = float(self.query_var.get().strip())
        except ValueError:
            self.query_result.config(text="Enter a number (nm or eV).")
            return

        mode = self.xaxis_q.get()
        if mode == "eV":
            wl_q = EN_TO_WL(val)
            label = f"{val:.4f} eV -> {wl_q:.2f} nm"
        else:
            wl_q = val
            en_q = WL_TO_EN(val)
            label = f"{val:.4f} nm -> {en_q:.4f} eV"

        if wl_q < self.wavelengths.min() or wl_q > self.wavelengths.max():
            self.query_result.config(
                text=f"{label}  |  n=—, k=— (out of range)", foreground="#fab387")
            return

        n_q = float(self._interp_n(wl_q))
        k_q = float(self._interp_k(wl_q))
        eps1_q = n_q**2 - k_q**2
        eps2_q = 2*n_q*k_q
        self.query_result.config(
            text=f"{label}  |  n = {n_q:.5f}  |  k = {k_q:.5f}",
            foreground=ACCENT)
        self.query_result2.config(
            text=f"ε1 = {eps1_q:.4f}  |  ε2 = {eps2_q:.4f}",
            foreground=ACCENT)

    # ════════════════════════════════════════════════════════
    # Scroll zoom — per plot
    # ════════════════════════════════════════════════════════
    def _on_scroll_nk(self, event):
        if event.inaxes is not self.ax_nk:
            return
        self._do_scroll(self.ax_nk, event)

    def _on_scroll_eps(self, event):
        if event.inaxes is not self.ax_eps:
            return
        self._do_scroll(self.ax_eps, event)

    def _do_scroll(self, ax, event):
        factor = 1.15 if event.step > 0 else 1.0 / 1.15
        # transData.inverted().transform returns LINEAR values regardless of
        # axis scale (matplotlib handles log transform internally).
        inv_x, inv_y = ax.transData.inverted().transform((event.x, event.y))

        # X zoom around mouse X
        xlo, xhi = ax.get_xlim()
        new_lo = inv_x - (inv_x - xlo) * factor
        new_hi = inv_x + (xhi - inv_x) * factor
        _set_xlim_linear(ax, new_lo, new_hi)

        # Y zoom around axis center (not mouse Y)
        ylo, yhi = ax.get_ylim()
        yctr = (ylo + yhi) / 2.0
        new_lo = yctr - (yctr - ylo) * factor
        new_hi = yctr + (yhi - yctr) * factor
        # On log y, a 15% zoom-out can push the lower bound below 0
        # (matplotlib rejects). Clamp to a tiny positive to keep it sane.
        if ax.get_yscale() == 'log' and new_lo <= 0:
            new_lo = 1e-30
        _set_ylim_linear(ax, new_lo, new_hi)

        # Always sync: zoomed plot becomes active, left panel shows its range
        self._sync_x_entries_from_ax(ax)
        self._sync_y_entries_from_ax(ax)

        ax.figure.canvas.draw_idle()

    def _active_ax(self):
        return self.ax_nk if self.active_plot.get() == "nk" else self.ax_eps

    def _apply_zoom_nk(self, ax, xlo, xhi, ylo, yhi):
        ax.set_xlim(xlo, xhi)
        ax.set_ylim(ylo, yhi)
        self._sync_x_entries_from_ax(ax)
        self._sync_y_entries_from_ax(ax)
        self.canvas_nk.draw_idle()

    def _apply_zoom_eps(self, ax, xlo, xhi, ylo, yhi):
        ax.set_xlim(xlo, xhi)
        ax.set_ylim(ylo, yhi)
        self._sync_x_entries_from_ax(ax)
        self._sync_y_entries_from_ax(ax)
        self.canvas_eps.draw_idle()

    def _sync_x_entries_from_ax(self, ax):
        if self._suppress_sync_to_entries:
            return
        xlo, xhi = _xlim_linear(ax)  # always linear, even if axis is log
        xmode = self.xaxis_var.get()
        if xmode == "energy":
            self.xmin.set(f"{xhi:.4g}")
            self.xmax.set(f"{xlo:.4g}")
        else:
            self.xmin.set(f"{xlo:.4g}")
            self.xmax.set(f"{xhi:.4g}")
        if xmode == "wavelength":
            self._xmin_wl = xlo
            self._xmax_wl = xhi
        else:
            self._xmin_wl = EN_TO_WL(xhi)
            self._xmax_wl = EN_TO_WL(xlo)
        # Update active plot indicator if needed
        if ax is self.ax_nk and self.active_plot.get() != "nk":
            self.active_plot.set("nk")
            self.yr_label.config(text="Y Min (n,k):")
        elif ax is self.ax_eps and self.active_plot.get() != "eps":
            self.active_plot.set("eps")
            self.yr_label.config(text="Y Min (ε):")

    def _sync_y_entries_from_ax(self, ax):
        ylo, yhi = _ylim_linear(ax)  # always linear, even if axis is log
        self.ymin.set(f"{ylo:.4g}")
        self.ymax.set(f"{yhi:.4g}")
        if ax is self.ax_nk:
            self._ymin_nk, self._ymax_nk = ylo, yhi
            if self.active_plot.get() != "nk":
                self.active_plot.set("nk")
                self.yr_label.config(text="Y Min (n,k):")
        else:
            self._ymin_eps, self._ymax_eps = ylo, yhi
            if self.active_plot.get() != "eps":
                self.active_plot.set("eps")
                self.yr_label.config(text="Y Min (ε):")

    # ════════════════════════════════════════════════════════
    # Plot helpers
    # ════════════════════════════════════════════════════════
    def _add_range_info(self, ax, xmode):
        """Add axis range info text to bottom-right corner of subplot."""
        xlo, xhi = _xlim_linear(ax)  # linear, even if axis is log
        ylo, yhi = _ylim_linear(ax)

        # Format x range
        if xmode == "energy":
            x_unit = "eV"
            x_text = f"X: {xhi:.2f}–{xlo:.2f} {x_unit}"
        else:
            x_unit = "nm"
            x_text = f"X: {xlo:.1f}–{xhi:.1f} {x_unit}"

        # Format y range
        y_text = f"Y: {ylo:.3f}–{yhi:.3f}"

        # Log scale indicators
        xlog = self.xlog_var.get()
        ylog = ylog_get(ax)
        log_text = ""
        if xlog:
            log_text += " (logX)"
        if ylog:
            log_text += " (logY)"
        if log_text:
            log_text = "  " + log_text.strip()

        info_text = f"{x_text}  {y_text}{log_text}"

        # Remove old range info text if exists
        if hasattr(ax, '_range_info_text') and ax._range_info_text is not None:
            try:
                ax._range_info_text.remove()
            except:
                pass

        # Add range info at bottom-right of axes (inside plot area, below any labels)
        ax._range_info_text = ax.text(
            0.98, 0.03, info_text,
            transform=ax.transAxes,
            fontsize=8, color="gray",
            ha="right", va="bottom",
            bbox=dict(boxstyle="round,pad=0.2", facecolor=BG, alpha=0.7, edgecolor="none")
        )

    # ════════════════════════════════════════════════════════
    # Plot
    # ════════════════════════════════════════════════════════
    def _update_plot(self, *args):
        def styl(ax):
            ax.set_facecolor(BG)
            for sp in ax.spines.values():
                sp.set_color(FG)
            ax.tick_params(colors=FG, labelcolor=FG)

        # Sync ylog state from UI BEFORE plot (plot code reads ylog_get to
        # decide whether to set yscale to log).
        self._suppress_sync_to_entries = True
        self._sync_active_plot_from_entries()
        self._suppress_sync_to_entries = False

        styl(self.ax_nk)
        styl(self.ax_eps)

        if self.wavelengths is None:
            for ax, fig, canvas in [
                (self.ax_nk, self.fig_nk, self.canvas_nk),
                (self.ax_eps, self.fig_eps, self.canvas_eps)]:
                ax.clear()
                styl(ax)
                ax.set_title("No data", color=FG, fontsize=10)
                ax.set_xlabel("", color=FG)
            self.fig_nk.suptitle("")
            self.fig_eps.suptitle("")
            self.canvas_nk.draw()
            self.canvas_eps.draw()
            return

        wl = self.wavelengths
        n, k = self.n_vals, self.k_vals
        eps1, eps2 = n**2 - k**2, 2 * n * k

        xmode = self.xaxis_var.get()
        if xmode == "energy":
            x = WL_TO_EN(wl)
            xlbl = "Photon Energy (eV)"
        else:
            x = wl
            xlbl = "Wavelength (nm)"

        xlog = self.xlog_var.get()

        # ── n,k plot ──────────────────────────────────────
        self.ax_nk.clear()
        styl(self.ax_nk)

        self.ax_nk.plot(x, n, color=ACCENT, lw=1.8, label="n")
        self.ax_nk.plot(x, k, color=ACCENT2, lw=1.8, linestyle="--", label="k")
        self.ax_nk.set_xlabel(xlbl, color=FG)
        self.ax_nk.set_ylabel("n, k", color=FG, fontsize=11)
        self.ax_nk.set_title("Refractive Index", color=FG, fontsize=11)
        self.ax_nk.legend(framealpha=0.3, labelcolor=FG, facecolor=BG, edgecolor=FG)
        self.ax_nk.grid(True, alpha=0.15, color=FG)
        if xlog: self.ax_nk.set_xscale("log")
        if ylog_get(self.ax_nk): self.ax_nk.set_yscale("log")

        # ── eps plot ──────────────────────────────────────
        self.ax_eps.clear()
        styl(self.ax_eps)

        self.ax_eps.plot(x, eps1, color=ACCENT, lw=1.8, label="ε1")
        self.ax_eps.plot(x, eps2, color=ACCENT2, lw=1.8, linestyle="--", label="ε2")
        self.ax_eps.axhline(0, color=FG, lw=0.6, alpha=0.4)
        self.ax_eps.set_xlabel(xlbl, color=FG)
        self.ax_eps.set_ylabel("ε1, ε2", color=FG, fontsize=11)
        self.ax_eps.set_title("Dielectric Function", color=FG, fontsize=11)
        self.ax_eps.legend(framealpha=0.3, labelcolor=FG, facecolor=BG, edgecolor=FG)
        self.ax_eps.grid(True, alpha=0.15, color=FG)
        if xlog: self.ax_eps.set_xscale("log")
        if ylog_get(self.ax_eps): self.ax_eps.set_yscale("log")

        # When y is log, autoscale may set ylim to a range containing zeros or
        # negatives (e.g. -0.333 from k=0 data, or negative eps1), which
        # matplotlib rejects with "non-positive ylim" warnings. Clamp to a
        # sensible positive range with log-aware padding (multiplicative so
        # we never accidentally produce a negative lower bound).
        for ax, series in ((self.ax_nk, (n, k)), (self.ax_eps, (eps1, eps2))):
            if ylog_get(ax):
                vals = np.concatenate([np.asarray(s) for s in series])
                pos = vals[np.isfinite(vals) & (vals > 0)]
                if len(pos) > 0:
                    lylo_raw, lyhi = float(pos.min()), float(pos.max())
                    # Floor at 1% of median so a few zero-valued points don't
                    # drag the lower bound to ~0 and dominate the log axis.
                    lylo = max(lylo_raw, float(np.median(pos)) * 0.01, 1e-6)
                    if lyhi <= lylo:
                        lyhi = lylo * 10
                    # Multiplicative padding for log axis: go down by a factor
                    # (0.5x), up by 10% — avoids negative lower bound.
                    new_lo = lylo * 0.5
                    new_hi = lyhi * 1.1
                    ax.set_ylim(new_lo, new_hi)

        self.fig_nk.suptitle(self.material_label, color=FG, fontsize=11, y=0.99)
        self.fig_eps.suptitle(self.material_label, color=FG, fontsize=11, y=0.99)

        # Apply user-specified x/y limits from entry boxes AFTER plot so they
        # survive the autoscale reset that clear() triggers.
        self._suppress_sync_to_entries = True
        self._apply_xy_from_entries()
        self._suppress_sync_to_entries = False

        # Add axis range info in bottom-right corner (no interference with title)
        self._add_range_info(self.ax_nk, xmode)
        self._add_range_info(self.ax_eps, xmode)

        self.canvas_nk.draw()
        self.canvas_eps.draw()

    # ════════════════════════════════════════════════════════
    # Export
    # ════════════════════════════════════════════════════════
    def _export(self):
        if self.wavelengths is None:
            messagebox.showwarning("No Data", "Select a material first.")
            return

        path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV", "*.csv")],
            initialdir=str(Path(__file__).resolve().parent))
        if not path:
            return

        # v0.5.4: wavelength in micrometers (μm). refractiveindex.info upstream
        # uses μm in raw data files and most optics workflows prefer μm over nm.
        # Epsilon1/epsilon2 can always be recomputed downstream as
        # n^2 - k^2 / 2*n*k (they don't depend on wavelength units).
        #
        # v0.5.4: sort by wavelength ascending. Some upstream tabulated files
        # (e.g. Sc-Sigrist) are sampled uniformly in photon energy, so their
        # wavelength column ends up sorted descending (high eV ↔ low λ).
        # Without sorting, the CSV would have wavelengths going 4.6, 4.3,
        # ... 0.0001 — confusing for downstream tools (pandas, gnuplot,
        # spreadsheets) that expect monotonic x.
        order = np.argsort(self.wavelengths)
        wl_sorted = self.wavelengths[order]
        n_sorted = self.n_vals[order]
        k_sorted = self.k_vals[order]
        lines = ["wavelength_um,n,k"]
        # Use %g-style 6 significant digits so small values like k=3e-7
        # don't round to 0.000000, while large values like n=9.558 stay compact.
        for wl_nm, ni, ki in zip(wl_sorted, n_sorted, k_sorted):
            lines.append(f"{wl_nm / 1000.0:.6g},{ni:.6g},{ki:.6g}")

        with open(path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
        messagebox.showinfo("Exported", f"Saved to:\n{path}")


# ────────────────────────────────────────────────────────────
# Helpers for per-axis log scale tracking
# (matplotlib ax.set_yscale doesn't persist a "get" cleanly,
#  so we track it ourselves per axis via figure annotations)
# ────────────────────────────────────────────────────────────
_ylog_state = {}   # maps ax -> bool

def ylog_get(ax):
    return _ylog_state.get(ax, False)

def ylog_set(ax, val):
    _ylog_state[ax] = val


# ────────────────────────────────────────────────────────────
# Log-axis bridge helpers
# matplotlib's get_xlim()/set_xlim()/transData always use LINEAR values
# regardless of the axis scale (matplotlib handles the log transform
# internally for display). GUI entry boxes already show/take LINEAR values
# (nm / eV / n / k / ε), so the helpers are essentially pass-throughs that
# just guard against invalid values (lo >= hi, or <= 0 on a log axis).
# All get/set call sites in the GUI go through these.
# ────────────────────────────────────────────────────────────
def _xlim_linear(ax):
    """Return (xlo, xhi) as matplotlib stores them (always LINEAR values)."""
    return ax.get_xlim()

def _ylim_linear(ax):
    return ax.get_ylim()

def _set_xlim_linear(ax, xlo, xhi):
    """Set xlim from LINEAR values. Returns True if applied."""
    if xlo is None or xhi is None or xlo >= xhi:
        return False
    if ax.get_xscale() == 'log' and (xlo <= 0 or xhi <= 0):
        return False
    ax.set_xlim(xlo, xhi)
    return True

def _set_ylim_linear(ax, ylo, yhi):
    if ylo is None or yhi is None or ylo >= yhi:
        return False
    if ax.get_yscale() == 'log' and (ylo <= 0 or yhi <= 0):
        return False
    ax.set_ylim(ylo, yhi)
    return True


# ════════════════════════════════════════════════════════════
# Cross-platform window maximize helper
#
# - win32: state('zoomed') works (full-screen on Windows).
# - darwin (macOS): Tk's state('zoomed') is silently ignored. The window
#   opens at the geometry() size; the user can use the green maximize
#   button. We intentionally don't try to fake it — fighting macOS Tk's
#   window manager produces worse results than the 1200x900 default.
# - linux (X11 / Wayland / Cinnamon / MATE / Xfce): state('zoomed') sends
#   _NET_WM_STATE_MAXIMIZED_HORZ/VERT. Most WMs honor it, but some (Wayland
#   sessions, certain Cinnamon/MATE configs on Linux Mint) silently drop
#   the request. Belt-and-suspenders: if zoomed didn't take effect, fall
#   back to setting geometry directly.
# ════════════════════════════════════════════════════════════
def _left_panel_width(sw: int) -> int:
    """Pure: given screen width (px), return the suggested width for the
    left control panel. 430 px on normal/large screens, scales down on
    small displays with a 280 px floor.
    """
    return min(430, max(280, int(sw * 0.32)))


def _compute_geometry(sw: int, sh: int) -> tuple[int, int, int, int]:
    """Pure: given screen size (px), return (default_w, default_h,
    min_w, min_h) for the main window.

    Rules:
      - Leave ~40 px horizontal / ~60 px vertical slack for window
        decorations (title bar, borders, taskbar).
      - Default size = 85% of usable screen, clamped to a comfortable
        range [720, 1800] x [500, 1100] and capped at the usable size
        so the window is never larger than the display.
      - Minsize = 85% of default, with hard floor [640, 440] AND a
        layout-aware floor (left pane + sash + right pane minsize +
        20 px slack) so the panes always fit when the window is at
        its minsize.

    Pure (no Tk calls, no side effects) so it can be unit-tested
    without a display.
    """
    screen_w = max(640, sw - 40)
    screen_h = max(440, sh - 60)
    w = min(screen_w, max(720, min(1800, int(screen_w * 0.85))))
    h = min(screen_h, max(500, min(1100, int(screen_h * 0.85))))
    # Layout-aware minsize: left + sash + right minsize + 20 px slack
    left_w = _left_panel_width(sw)
    layout_min_w = left_w + 4 + 400 + 20  # 4 = sash, 400 = right minsize
    min_w = max(640, min(int(w * 0.85), screen_w), layout_min_w)
    min_h = max(440, min(int(h * 0.85), screen_h))
    return w, h, min_w, min_h


def _adaptive_geometry(root) -> tuple[int, int]:
    """Set window default size + minsize based on the actual screen.
    Returns (screen_w, screen_h) so callers can scale other layout
    constants (e.g. left pane width) consistently.
    """
    sw = root.winfo_screenwidth()
    sh = root.winfo_screenheight()
    w, h, min_w, min_h = _compute_geometry(sw, sh)
    root.geometry(f"{w}x{h}")
    root.minsize(min_w, min_h)
    return sw, sh


def _maximize_window(root):
    """Maximize root window across platforms. No-op on macOS."""
    if sys.platform == "win32":
        root.state("zoomed")
        return
    if sys.platform == "darwin":
        return  # macOS Tk doesn't recognize 'zoomed'
    # Linux: try state('zoomed'), then check if it actually applied
    try:
        root.state("zoomed")
        root.update_idletasks()
        if root.state() != ("zoomed",):
            # WM didn't honor it (Wayland, some X11 WMs); force geometry
            sw = root.winfo_screenwidth()
            sh = root.winfo_screenheight()
            root.geometry(f"{sw}x{sh}+0+0")
    except tk.TclError:
        sw = root.winfo_screenwidth()
        sh = root.winfo_screenheight()
        root.geometry(f"{sw}x{sh}+0+0")


# ════════════════════════════════════════════════════════════
if __name__ == "__main__":
    root = tk.Tk()
    app = NkCurveGUI(root)
    root.mainloop()
