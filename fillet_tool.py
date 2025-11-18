# fillet_tool.py

from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtGui import QColor, QFont
from qgis.gui import QgsMapTool, QgsRubberBand
from qgis.core import (
    QgsPointXY, QgsGeometry, QgsFeature, QgsProject,
    QgsWkbTypes, QgsVectorLayer
)
from qgis.PyQt.QtWidgets import QLabel
import math

# --- 你的所有辅助函数 ---
def unit(vx, vy):
    L = math.hypot(vx, vy)
    return (vx / L, vy / L) if L > 0 else (0.0, 0.0)

def dot(a, b):
    return a[0]*b[0] + a[1]*b[1]

def normalize_angle(a):
    while a <= -math.pi:
        a += 2*math.pi
    while a > math.pi:
        a -= 2*math.pi
    return a

def fillet_three_points(p_prev, p, p_next, radius, segs_per_quarter=4):
    # ... [你的原函数内容不变] ...
    v1 = (p_prev.x() - p.x(), p_prev.y() - p.y())
    v2 = (p_next.x() - p.x(), p_next.y() - p.y())
    l1 = math.hypot(v1[0], v1[1])
    l2 = math.hypot(v2[0], v2[1])
    if l1 == 0 or l2 == 0:
        return [QgsPointXY(p)]
    s1 = (v1[0]/l1, v1[1]/l1)
    s2 = (v2[0]/l2, v2[1]/l2)
    cos_alpha = max(-1.0, min(1.0, dot(s1, s2)))
    alpha = math.acos(cos_alpha)
    if alpha < 1e-6 or abs(math.pi - alpha) < 1e-6:
        return [QgsPointXY(p)]
    t = radius / math.tan(alpha / 2.0)
    t_max = min(l1, l2)
    if t > t_max:
        t = t_max
        radius_local = t * math.tan(alpha / 2.0)
        if radius_local <= 0:
            return [QgsPointXY(p)]
        radius = radius_local
    T1 = QgsPointXY(p.x() + s1[0] * t, p.y() + s1[1] * t)
    T2 = QgsPointXY(p.x() + s2[0] * t, p.y() + s2[1] * t)
    bis = (s1[0] + s2[0], s1[1] + s2[1])
    bis_len = math.hypot(bis[0], bis[1])
    if bis_len == 0:
        return [QgsPointXY(p)]
    bis_u = (bis[0]/bis_len, bis[1]/bis_len)
    h = radius / math.sin(alpha / 2.0)
    Cx = p.x() + bis_u[0] * h
    Cy = p.y() + bis_u[1] * h
    a1 = math.atan2(T1.y() - Cy, T1.x() - Cx)
    a2 = math.atan2(T2.y() - Cy, T2.x() - Cx)
    d = normalize_angle(a2 - a1)
    segs = max(1, int(math.ceil(abs(d) / (math.pi/2) * segs_per_quarter)))
    pts = [T1]
    for k in range(1, segs):
        theta = a1 + d * (k / segs)
        x = Cx + radius * math.cos(theta)
        y = Cy + radius * math.sin(theta)
        pts.append(QgsPointXY(x, y))
    pts.append(T2)
    return pts

# --- 主工具类 ---
class FilletDigitizeTool(QgsMapTool):
    def __init__(self, canvas, line_layer, radius=10.0, segs_per_quarter=6):
        super().__init__(canvas)
        self.canvas = canvas
        self.layer = line_layer
        self.radius = float(radius)
        self.segs = segs_per_quarter
        self.setCursor(Qt.CrossCursor)

        self.perm_rb = QgsRubberBand(self.canvas, QgsWkbTypes.LineGeometry)
        self.perm_rb.setColor(QColor(50, 150, 255, 200))
        self.perm_rb.setWidth(2)

        self.preview_rb = QgsRubberBand(self.canvas, QgsWkbTypes.LineGeometry)
        self.preview_rb.setColor(QColor(255, 80, 80, 200))
        self.preview_rb.setWidth(2)

        self.radius_label = QLabel(self.canvas)
        self.radius_label.setWindowFlags(self.radius_label.windowFlags() | Qt.ToolTip)
        self.radius_label.setStyleSheet("background: rgba(0,0,0,180); color: white; padding:4px; border-radius:4px;")
        self.radius_label.setFont(QFont("Sans", 9))
        self.radius_label.hide()

        self.points = []
        self.last_mouse_pt = None
        self.last_global_pos = None
        self._radius_step = 1.0

    def canvasPressEvent(self, event):
        pt_map = self.toMapCoordinates(event.pos())
        self.last_mouse_pt = QgsPointXY(pt_map)
        self.last_global_pos = self.canvas.mapToGlobal(event.pos())
        if event.button() == Qt.LeftButton:
            self.points.append(QgsPointXY(pt_map))
            self.perm_rb.reset(QgsWkbTypes.LineGeometry)
            for p in self.points:
                self.perm_rb.addPoint(p, False)
            self.perm_rb.show()
            self._update_preview(self.last_mouse_pt)
            self._update_radius_label()

    def canvasMoveEvent(self, event):
        pt_map = self.toMapCoordinates(event.pos())
        self.last_mouse_pt = QgsPointXY(pt_map)
        self.last_global_pos = self.canvas.mapToGlobal(event.pos())
        self._update_preview(self.last_mouse_pt)
        self._update_radius_label()

    def canvasDoubleClickEvent(self, event):
        if len(self.points) >= 1:
            pt = self.toMapCoordinates(event.pos())
            pts_final = self.points + [QgsPointXY(pt)]
            if len(pts_final) < 2:
                return
            if len(pts_final) == 2:
                final_geom = QgsGeometry.fromPolylineXY(pts_final)
            else:
                new_pts = self._build_filleted_points(pts_final)
                final_geom = QgsGeometry.fromPolylineXY(new_pts)
            if self.layer.isEditable() or (self.layer.dataProvider().capabilities() & self.layer.dataProvider().AddFeatures):
                feat = QgsFeature(self.layer.fields())
                feat.setGeometry(final_geom)
                res, feats = self.layer.dataProvider().addFeatures([feat])
                if res:
                    self.layer.triggerRepaint()
            self.points = []
            self.perm_rb.reset(QgsWkbTypes.LineGeometry)
            self.preview_rb.reset(QgsWkbTypes.LineGeometry)
            self.radius_label.hide()

    def keyPressEvent(self, event):
        k = event.key()
        changed = False
        if k in (Qt.Key_Plus, Qt.Key_Equal):
            self.radius += self._radius_step
            changed = True
        elif k in (Qt.Key_Minus, Qt.Key_Underscore):
            self.radius = max(0.0, self.radius - self._radius_step)
            changed = True
        elif k == Qt.Key_BracketRight:
            self.radius += self._radius_step * 10.0
            changed = True
        elif k == Qt.Key_BracketLeft:
            self.radius = max(0.0, self.radius - self._radius_step * 10.0)
            changed = True

        if changed:
            if self.last_mouse_pt is not None:
                self._update_preview(self.last_mouse_pt)
            self._update_radius_label()
            event.accept()
        else:
            super().keyPressEvent(event)

    def _build_filleted_points(self, pts_list):
        if len(pts_list) < 3:
            return list(pts_list)
        new_pts = [QgsPointXY(pts_list[0])]
        n = len(pts_list)
        for i in range(1, n-1):
            prev_p = pts_list[i-1]
            cur_p = pts_list[i]
            next_p = pts_list[i+1]
            seg = fillet_three_points(prev_p, cur_p, next_p, self.radius, self.segs)
            for q in seg:
                if len(new_pts) > 0:
                    last = new_pts[-1]
                    if abs(last.x() - q.x()) < 1e-9 and abs(last.y() - q.y()) < 1e-9:
                        continue
                new_pts.append(q)
        lastpt = pts_list[-1]
        if len(new_pts) == 0 or not (abs(new_pts[-1].x() - lastpt.x()) < 1e-9 and abs(new_pts[-1].y() - lastpt.y()) < 1e-9):
            new_pts.append(QgsPointXY(lastpt))
        return new_pts

    def _update_preview(self, moving_pt):
        self.preview_rb.reset(QgsWkbTypes.LineGeometry)
        if len(self.points) == 0:
            self.preview_rb.show()
            return
        pts_for_preview = self.points + [QgsPointXY(moving_pt)]
        if len(pts_for_preview) < 3:
            for i, p in enumerate(pts_for_preview):
                self.preview_rb.addPoint(p, i == len(pts_for_preview)-1)
            self.preview_rb.show()
            return
        preview_pts = self._build_filleted_points(pts_for_preview)
        for i, p in enumerate(preview_pts):
            self.preview_rb.addPoint(p, i == len(preview_pts)-1)
        self.preview_rb.show()
        try:
            self.canvas.refresh()
        except Exception:
            pass

    def _update_radius_label(self):
        text = "Radius: {:.2f}".format(self.radius)
        self.radius_label.setText(text)
        self.radius_label.adjustSize()
        if self.last_global_pos is None:
            center = self.canvas.rect().center()
            global_center = self.canvas.mapToGlobal(center)
            gx, gy = global_center.x(), global_center.y()
        else:
            gx, gy = self.last_global_pos.x(), self.last_global_pos.y()
        self.radius_label.move(gx + 12, gy + 12)
        self.radius_label.show()

    def deactivate(self):
        self.perm_rb.reset(QgsWkbTypes.LineGeometry)
        self.preview_rb.reset(QgsWkbTypes.LineGeometry)
        self.radius_label.hide()
        super().deactivate()