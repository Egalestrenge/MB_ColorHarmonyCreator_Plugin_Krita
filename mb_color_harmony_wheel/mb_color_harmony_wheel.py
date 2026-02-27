import math

from krita import DockWidget, Krita
from PyQt5.QtCore import QByteArray, Qt
from PyQt5.QtGui import QColor, QImage, QPainter, QPainterPath
from PyQt5.QtWidgets import (
    QComboBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


TOTAL_HUES = 12
SECTOR_COUNT = 4
HUE_STEP_DEG = 360.0 / TOTAL_HUES
HUE_GAP_DEG = 2
CENTER_HOLE_RATIO = 0.175
OUTER_BEVEL_RATIO = 0.075
RADIAL_PARTITION_E = 1/2

DEFAULT_BG = QColor(236, 236, 236)

ARTISTIC_HEX_ANCHORS = [
    "#f92508",
    "#fa510a",
    "#fa8d0b",
    "#fbc609",
    "#fefc01",
    "#a8f909",
    "#21d107",
    "#04bfbf",
    "#0929f3",
    "#5120fd",
    "#a22ec8",
]


def hsv_to_qcolor(h_deg, sat, val):
    return QColor.fromHsv(
        int(round(h_deg)) % 360,
        int(round(max(0.0, min(1.0, sat)) * 255.0)),
        int(round(max(0.0, min(1.0, val)) * 255.0)),
    )


def circular_midpoint_deg(a_deg, b_deg):
    diff = (b_deg - a_deg) % 360.0
    if diff > 180.0:
        diff -= 360.0
    return (a_deg + (diff / 2.0)) % 360.0


def hex_to_hue_deg(hex_color):
    color = QColor(hex_color)
    hue, _, _, _ = color.getHsv()
    if hue < 0:
        return 0.0
    return float(hue)


def build_artistic_hues():
    hues = [hex_to_hue_deg(h) for h in ARTISTIC_HEX_ANCHORS]

    if len(hues) == TOTAL_HUES - 1:
        hues.append(circular_midpoint_deg(hues[-1], hues[0]))
    elif len(hues) < TOTAL_HUES and len(hues) > 0:
        while len(hues) < TOTAL_HUES:
            hues.append(hues[len(hues) % len(ARTISTIC_HEX_ANCHORS)])
    elif len(hues) > TOTAL_HUES:
        hues = hues[:TOTAL_HUES]

    if len(hues) == 0:
        return [i * HUE_STEP_DEG for i in range(TOTAL_HUES)]

    return hues


ARTISTIC_HUES = build_artistic_hues()


def polar_point(cx, cy, radius, deg):
    ang = math.radians(deg)
    return cx + (math.cos(ang) * radius), cy + (math.sin(ang) * radius)


def build_wedge_path(cx, cy, inner_r, outer_r, start_deg, end_deg, segments, outer_bevel_px):
    path = QPainterPath()
    if outer_r <= inner_r:
        return path

    total_angle = max(0.0, end_deg - start_deg)
    bevel_radius = min(max(0.0, outer_bevel_px), max(0.0, (outer_r - inner_r) - 0.5))

    if bevel_radius > 0.0 and total_angle > 0.0:
        bevel_angle = math.degrees(bevel_radius / max(outer_r, 1e-6))
        bevel_angle = min(bevel_angle, total_angle / 3.0)
    else:
        bevel_angle = 0.0

    outer_points = []

    if bevel_angle > 0.0:
        outer_points.append(polar_point(cx, cy, outer_r - bevel_radius, start_deg))
        start_arc_deg = start_deg + bevel_angle
        end_arc_deg = end_deg - bevel_angle
        outer_points.append(polar_point(cx, cy, outer_r, start_arc_deg))

        arc_steps = max(2, int(segments * ((end_arc_deg - start_arc_deg) / max(total_angle, 1e-6))))
        for i in range(1, arc_steps):
            t = i / float(arc_steps)
            d = start_arc_deg + ((end_arc_deg - start_arc_deg) * t)
            outer_points.append(polar_point(cx, cy, outer_r, d))

        outer_points.append(polar_point(cx, cy, outer_r, end_arc_deg))
        outer_points.append(polar_point(cx, cy, outer_r - bevel_radius, end_deg))
    else:
        for i in range(segments + 1):
            t = i / float(segments)
            d = start_deg + ((end_deg - start_deg) * t)
            outer_points.append(polar_point(cx, cy, outer_r, d))

    inner_points = []
    for i in range(segments + 1):
        t = 1.0 - (i / float(segments))
        d = start_deg + ((end_deg - start_deg) * t)
        inner_points.append(polar_point(cx, cy, inner_r, d))

    points = outer_points + inner_points
    if not points:
        return path

    path.moveTo(points[0][0], points[0][1])
    for px, py in points[1:]:
        path.lineTo(px, py)
    path.closeSubpath()
    return path


def hsv_to_hsl(sat, val):
    lgt = val * (1.0 - (sat / 2.0))
    if lgt <= 0.0 or lgt >= 1.0:
        sat_hsl = 0.0
    else:
        sat_hsl = (val - lgt) / min(lgt, 1.0 - lgt)
    return max(0.0, min(1.0, sat_hsl)), max(0.0, min(1.0, lgt))


def hsx_to_qcolor(h_deg, sat, val, model_key):
    if model_key == "hsl":
        return QColor.fromHsl(
            int(round(h_deg)) % 360,
            int(round(max(0.0, min(1.0, sat)) * 255.0)),
            int(round(max(0.0, min(1.0, val)) * 255.0)),
        )
    return hsv_to_qcolor(h_deg, sat, val)


def ring_model_values(ring_index, model_key):
    if model_key == "hsl":
        if ring_index == 0:
            return 1.0, 0.5
        if ring_index == 1:
            return 0.5, 0.5
        if ring_index == 2:
            return 1.0, 0.25
        return 1.0, 0.5

    if ring_index == 0:
        return 1.0, 1.0
    if ring_index == 1:
        return 0.5, 1.0
    if ring_index == 2:
        return 1.0, 0.5
    return 1.0, 1.0


def ryb_to_hsv_hue(ryb_deg):
    points = [
        (0.0, 0.0),
        (60.0, 42.0),
        (120.0, 78.0),
        (180.0, 120.0),
        (210.0, 165.0),
        (240.0, 205.0),
        (270.0, 245.0),
        (300.0, 285.0),
        (360.0, 360.0),
    ]

    x = ryb_deg % 360.0
    for i in range(len(points) - 1):
        x0, y0 = points[i]
        x1, y1 = points[i + 1]
        if x0 <= x <= x1:
            t = 0.0 if x1 == x0 else (x - x0) / (x1 - x0)
            return (y0 + ((y1 - y0) * t)) % 360.0
    return x


def map_hue_for_space(base_deg, space_key):
    if space_key == "rgb":
        return base_deg % 360.0
    if space_key == "cmy":
        return (base_deg + 180.0) % 360.0
    return ryb_to_hsv_hue(base_deg)


def wrap_hue_index(index):
    return index % TOTAL_HUES


def harmony_offsets(harmony_key):
    if harmony_key == "complementary":
        return [0, 6]
    if harmony_key == "split_complementary":
        return [0, 5, 7]
    if harmony_key == "triad":
        return [0, 4, 8]
    if harmony_key == "analogous":
        return [0, 1, 2, 3]
    if harmony_key == "double_complementary":
        return [0, 1, 6, 7]
    if harmony_key == "rectangular_tetrad":
        return [0, 2, 6, 8]
    if harmony_key == "square_tetrad":
        return [0, 3, 6, 9]
    if harmony_key == "polychromatic":
        return [0, 2, 4, 6, 8, 10]
    return [0, 6]


def get_anchor_rect(doc_w, doc_h, anchor_key):
    if anchor_key == "full":
        side = max(doc_w, doc_h)
        x = int((doc_w - side) / 2)
        y = int((doc_h - side) / 2)
        return x, y, side, side

    side = max(1, int(min(doc_w, doc_h) / 3))

    x_positions = {
        "left": 0,
        "center": int((doc_w - side) / 2),
        "right": doc_w - side,
    }
    y_positions = {
        "top": 0,
        "middle": int((doc_h - side) / 2),
        "bottom": doc_h - side,
    }

    vert, horiz = anchor_key.split("_")
    x = x_positions[horiz]
    y = y_positions[vert]
    return x, y, side, side


class MBColorHarmonyWheelDocker(DockWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("MB Color Harmony Wheel")

        self.rotation = 0
        self._last_paint_rect = None

        base_widget = QWidget(self)
        self.setWidget(base_widget)

        root_layout = QVBoxLayout()
        base_widget.setLayout(root_layout)

        title = QLabel("Color Harmony Wheel")
        title.setAlignment(Qt.AlignCenter)
        root_layout.addWidget(title)

        form_layout = QFormLayout()
        root_layout.addLayout(form_layout)

        self.harmony_combo = QComboBox()
        self.harmony_combo.addItem("Complementary", "complementary")
        self.harmony_combo.addItem("Split Complementary", "split_complementary")
        self.harmony_combo.addItem("Triad", "triad")
        self.harmony_combo.addItem("Analogous", "analogous")
        self.harmony_combo.addItem("Double Complementary", "double_complementary")
        self.harmony_combo.addItem("Rectangular Tetrad", "rectangular_tetrad")
        self.harmony_combo.addItem("Square Tetrad", "square_tetrad")
        self.harmony_combo.addItem("Polychromatic", "polychromatic")
        self.harmony_combo.currentIndexChanged.connect(self.paint_wheel)
        form_layout.addRow("Harmony:", self.harmony_combo)

        self.color_space_combo = QComboBox()
        self.color_space_combo.addItem("RYB / Artist", "ryb")
        self.color_space_combo.addItem("RGB / HSV", "rgb")
        self.color_space_combo.addItem("CMY / Subtractive", "cmy")
        self.color_space_combo.currentIndexChanged.connect(self.paint_wheel)
        form_layout.addRow("Color Space:", self.color_space_combo)

        self.hue_mapping_combo = QComboBox()
        self.hue_mapping_combo.addItem("Mathematical", "math")
        self.hue_mapping_combo.addItem("Artistic (LUT)", "artistic")
        self.hue_mapping_combo.setCurrentIndex(1)
        self.hue_mapping_combo.currentIndexChanged.connect(self.paint_wheel)
        form_layout.addRow("Hue Mapping:", self.hue_mapping_combo)

        self.color_model_combo = QComboBox()
        self.color_model_combo.addItem("HSV", "hsv")
        self.color_model_combo.addItem("HSL", "hsl")
        self.color_model_combo.currentIndexChanged.connect(self.paint_wheel)
        form_layout.addRow("Color Model:", self.color_model_combo)

        self.anchor_combo = QComboBox()
        self.anchor_combo.addItem("Full", "full")
        self.anchor_combo.addItem("Top Left", "top_left")
        self.anchor_combo.addItem("Top Center", "top_center")
        self.anchor_combo.addItem("Top Right", "top_right")
        self.anchor_combo.addItem("Middle Left", "middle_left")
        self.anchor_combo.addItem("Middle Center", "middle_center")
        self.anchor_combo.addItem("Middle Right", "middle_right")
        self.anchor_combo.addItem("Bottom Left", "bottom_left")
        self.anchor_combo.addItem("Bottom Center", "bottom_center")
        self.anchor_combo.addItem("Bottom Right", "bottom_right")
        self.anchor_combo.currentIndexChanged.connect(self.paint_wheel)
        form_layout.addRow("Position:", self.anchor_combo)

        button_layout = QHBoxLayout()
        root_layout.addLayout(button_layout)

        self.rotate_ccw_button = QPushButton("↺")
        self.rotate_ccw_button.setToolTip("Rotate harmony counterclockwise")
        self.rotate_ccw_button.clicked.connect(self.rotate_ccw)
        button_layout.addWidget(self.rotate_ccw_button)

        self.rotate_cw_button = QPushButton("↻")
        self.rotate_cw_button.setToolTip("Rotate harmony clockwise")
        self.rotate_cw_button.clicked.connect(self.rotate_cw)
        button_layout.addWidget(self.rotate_cw_button)

        self.paint_button = QPushButton("Paint")
        self.paint_button.clicked.connect(self.paint_wheel)
        root_layout.addWidget(self.paint_button)

        root_layout.addStretch()

    def canvasChanged(self, canvas):
        _ = canvas

    def rotate_cw(self):
        self.rotation = wrap_hue_index(self.rotation + 1)
        self.paint_wheel()

    def rotate_ccw(self):
        self.rotation = wrap_hue_index(self.rotation - 1)
        self.paint_wheel()

    def _selected_hues(self):
        key = self.harmony_combo.currentData()
        offsets = harmony_offsets(key)
        return {wrap_hue_index(self.rotation + off) for off in offsets}

    def _clamp_rect(self, x, y, w, h, doc_w, doc_h):
        x0 = max(0, x)
        y0 = max(0, y)
        x1 = min(doc_w, x + w)
        y1 = min(doc_h, y + h)
        cw = x1 - x0
        ch = y1 - y0
        if cw <= 0 or ch <= 0:
            return None
        return x0, y0, cw, ch

    def _clear_rect(self, node, rect):
        if not rect:
            return
        x, y, w, h = rect
        clear_data = bytes(w * h * 4)
        node.setPixelData(QByteArray(clear_data), x, y, w, h)

    def paint_wheel(self):
        app = Krita.instance()
        doc = app.activeDocument()
        if not doc:
            return

        node = doc.activeNode()
        if not node:
            return

        doc_w = doc.width()
        doc_h = doc.height()

        if self._last_paint_rect is not None:
            self._clear_rect(node, self._last_paint_rect)

        anchor_key = self.anchor_combo.currentData() or "full"
        x, y, w, h = get_anchor_rect(doc_w, doc_h, anchor_key)
        if w <= 1 or h <= 1:
            return

        image = QImage(w, h, QImage.Format_ARGB32)
        image.fill(Qt.transparent)

        painter = QPainter(image)
        painter.setRenderHint(QPainter.Antialiasing, True)

        selected_hues = self._selected_hues()

        margin = max(2.0, w * 0.02)
        radius = (min(w, h) / 2.0) - margin
        cx = w / 2.0
        cy = h / 2.0

        half_slice_deg = HUE_STEP_DEG / 2.0
        hue_gap_deg = HUE_GAP_DEG
        radial_gap = 0.0
        outer_bevel_px = max(1.0, radius * OUTER_BEVEL_RATIO)
        color_space = self.color_space_combo.currentData() or "ryb"
        hue_mapping = self.hue_mapping_combo.currentData() or "math"
        color_model = self.color_model_combo.currentData() or "hsv"

        hole_radius = radius * CENTER_HOLE_RATIO
        effective_radius = radius - hole_radius
        e = max(0.0, min(1.0, RADIAL_PARTITION_E))

        er = e * effective_radius
        step = er / 3.0

        ring_bounds = [
            (hole_radius + er, hole_radius + effective_radius),
            (hole_radius + (er - step), hole_radius + er),
            (hole_radius + (er - (2.0 * step)), hole_radius + (er - step)),
            (hole_radius + 0.0, hole_radius + (er - (2.0 * step))),
        ]

        outer_gray = DEFAULT_BG

        for hue_idx in range(TOTAL_HUES):
            center_deg = -90.0 + (hue_idx * HUE_STEP_DEG)
            start_deg = center_deg - half_slice_deg + (hue_gap_deg / 2.0)
            end_deg = center_deg + half_slice_deg - (hue_gap_deg / 2.0)
            base_deg = hue_idx * HUE_STEP_DEG
            if hue_mapping == "artistic":
                h_deg = ARTISTIC_HUES[hue_idx]
            else:
                h_deg = map_hue_for_space(base_deg, color_space)
            in_harmony = hue_idx in selected_hues

            inner_base, outer_base = ring_bounds[3]
            inner_r = inner_base + (radial_gap / 2.0)
            outer_r = outer_base - (radial_gap / 2.0)
            if outer_r > inner_r:
                path = build_wedge_path(
                    cx,
                    cy,
                    inner_r,
                    outer_r,
                    start_deg,
                    end_deg,
                    20,
                    0.0,
                )
                sat, val = ring_model_values(3, color_model)
                painter.fillPath(path, hsx_to_qcolor(h_deg, sat, val, color_model))

            if not in_harmony:
                inner_r = ring_bounds[2][0]
                outer_r = ring_bounds[0][1]
                path = build_wedge_path(
                    cx,
                    cy,
                    inner_r,
                    outer_r,
                    start_deg,
                    end_deg,
                    20,
                    outer_bevel_px,
                )
                painter.fillPath(path, outer_gray)
                continue

            for ring_index in range(3):
                inner_base, outer_base = ring_bounds[ring_index]
                inner_r = inner_base + (radial_gap / 2.0)
                outer_r = outer_base - (radial_gap / 2.0)
                if outer_r <= inner_r:
                    continue

                sat, val = ring_model_values(ring_index, color_model)
                color = hsx_to_qcolor(h_deg, sat, val, color_model)
                path = build_wedge_path(
                    cx,
                    cy,
                    inner_r,
                    outer_r,
                    start_deg,
                    end_deg,
                    20,
                    outer_bevel_px if ring_index == 0 else 0.0,
                )

                painter.fillPath(path, color)

        hole_radius_px = max(1, int(hole_radius))
        painter.setCompositionMode(QPainter.CompositionMode_Clear)
        painter.drawEllipse(
            int(cx - hole_radius_px),
            int(cy - hole_radius_px),
            int(hole_radius_px * 2),
            int(hole_radius_px * 2),
        )

        painter.end()

        ptr = image.bits()
        ptr.setsize(image.byteCount())
        node.setPixelData(QByteArray(bytes(ptr)), x, y, w, h)

        self._last_paint_rect = self._clamp_rect(x, y, w, h, doc_w, doc_h)
        doc.refreshProjection()