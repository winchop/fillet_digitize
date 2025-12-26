# fillet_tool.py

from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtGui import QColor, QFont
from qgis.gui import QgsMapTool, QgsRubberBand
from qgis.core import (
    QgsPointXY, QgsGeometry, QgsFeature, QgsProject,
    QgsWkbTypes, QgsVectorLayer
)
from qgis.PyQt.QtWidgets import QLabel, QMessageBox
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

# --- new: robust segment intersection checks to detect self-crossings in preview/final geometry ---
def _orient(ax, ay, bx, by, cx, cy):
    return (bx-ax)*(cy-ay) - (by-ay)*(cx-ax)

def _on_segment(ax, ay, bx, by, cx, cy):
    # check if point C(cx,cy) is on segment AB
    return min(ax, bx) - 1e-9 <= cx <= max(ax, bx) + 1e-9 and min(ay, by) - 1e-9 <= cy <= max(ay, by) + 1e-9

def _segments_intersect(p1, p2, p3, p4):
    ax, ay = p1.x(), p1.y()
    bx, by = p2.x(), p2.y()
    cx, cy = p3.x(), p3.y()
    dx, dy = p4.x(), p4.y()
    o1 = _orient(ax, ay, bx, by, cx, cy)
    o2 = _orient(ax, ay, bx, by, dx, dy)
    o3 = _orient(cx, cy, dx, dy, ax, ay)
    o4 = _orient(cx, cy, dx, dy, bx, by)

    if (o1 > 0 and o2 < 0 or o1 < 0 and o2 > 0) and (o3 > 0 and o4 < 0 or o3 < 0 and o4 > 0):
        return True
    # special colinear cases
    if abs(o1) <= 1e-9 and _on_segment(ax, ay, bx, by, cx, cy):
        return True
    if abs(o2) <= 1e-9 and _on_segment(ax, ay, bx, by, dx, dy):
        return True
    if abs(o3) <= 1e-9 and _on_segment(cx, cy, dx, dy, ax, ay):
        return True
    if abs(o4) <= 1e-9 and _on_segment(cx, cy, dx, dy, bx, by):
        return True
    return False

def polyline_self_intersects(pts):
    # detect intersection between any two non-adjacent segments of open polyline pts
    n = len(pts)
    if n < 4:
        return False
    # segments: (0,1), (1,2), ..., (n-2,n-1)
    for i in range(0, n-1):
        a1 = pts[i]
        a2 = pts[i+1]
        for j in range(i+2, n-1):
            # skip adjacent segments that share a vertex
            # for open polyline, i and j are non-adjacent if j > i+1
            # also skip the case where first and last segment share endpoint (not a closed ring)
            if i == 0 and j == n-2:
                # these are not adjacent for an open polyline, keep checking
                pass
            if _segments_intersect(a1, a2, pts[j], pts[j+1]):
                return True
    return False

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
        self.radius = float(radius)           # global default radius
        self.segs = segs_per_quarter
        self.setCursor(Qt.CrossCursor)

        self.perm_rb = QgsRubberBand(self.canvas, QgsWkbTypes.LineGeometry)
        self.perm_rb.setColor(QColor(50, 150, 255, 200))
        self.perm_rb.setWidth(5)

        self.preview_rb = QgsRubberBand(self.canvas, QgsWkbTypes.LineGeometry)
        # normal preview color: green; bad preview: red
        self.preview_color_ok = QColor(0, 200, 0, 200)
        self.preview_color_bad = QColor(255, 0, 0, 200)
        self.preview_rb.setColor(self.preview_color_ok)
        self.preview_rb.setWidth(2)

        self.radius_label = QLabel(self.canvas)
        self.radius_label.setWindowFlags(self.radius_label.windowFlags() | Qt.ToolTip)
        self.radius_label.setStyleSheet("background: rgba(0,0,0,180); color: white; padding:4px; border-radius:4px;")
        self.radius_label.setFont(QFont("Sans", 9))
        self.radius_label.hide()

        self.points = []
        # per-point radii, same length as self.points; value None -> use global self.radius
        self._radii = []

        # next_point_radius: temporary override for the last-placed point (will be committed when next point is clicked)
        self.next_point_radius = None

        self.last_mouse_pt = None
        self.last_global_pos = None
        self._radius_step = 1.0

        # undo/redo stacks: store tuples (points_snapshot, radii_snapshot, next_point_radius_snapshot)
        self._undo_stack = []
        self._redo_stack = []

        # state of last preview validity
        self._last_preview_invalid = False

    def canvasPressEvent(self, event):
        pt_map = self.toMapCoordinates(event.pos())
        self.last_mouse_pt = QgsPointXY(pt_map)
        self.last_global_pos = self.canvas.mapToGlobal(event.pos())
        if event.button() == Qt.LeftButton:
            # push current snapshot for undo (deep copies), then clear redo stack (new action)
            pts_snap = [QgsPointXY(p) for p in self.points]
            radii_snap = [r for r in self._radii]
            next_snap = None if self.next_point_radius is None else float(self.next_point_radius)
            self._undo_stack.append((pts_snap, radii_snap, next_snap))
            self._redo_stack.clear()

            # If we have at least one existing point, and a temporary next_point_radius set,
            # commit that radius to the last point (the corner to be filleted once the new point is placed).
            if len(self.points) >= 1 and self.next_point_radius is not None:
                # ensure radii list is aligned
                while len(self._radii) < len(self.points):
                    self._radii.append(None)
                self._radii[-1] = float(self.next_point_radius)
                # reset temporary override after committing
                self.next_point_radius = None

            # append new point and align radii
            self.points.append(QgsPointXY(pt_map))
            self._radii.append(None)

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
        # keep the guiding (blue) rubber band visible while moving:
        # show permanent points plus a guiding line from last point to current mouse position
        self.perm_rb.reset(QgsWkbTypes.LineGeometry)
        if len(self.points) > 0:
            for p in self.points:
                self.perm_rb.addPoint(p, False)
            # add guiding segment to current mouse position
            self.perm_rb.addPoint(QgsPointXY(pt_map), True)
        self.perm_rb.show()
        self._update_preview(self.last_mouse_pt)
        self._update_radius_label()

    def canvasDoubleClickEvent(self, event):
        if len(self.points) >= 1:
            pt = self.toMapCoordinates(event.pos())
            # before finalizing, if the user had set a temporary next_point_radius, commit it to the last point
            if len(self.points) >= 1 and self.next_point_radius is not None:
                while len(self._radii) < len(self.points):
                    self._radii.append(None)
                self._radii[-1] = float(self.next_point_radius)
                # do not need to keep next_point_radius after commit
                self.next_point_radius = None

            pts_final = self.points + [QgsPointXY(pt)]
            # build radii_for_final aligned with pts_final
            radii_for_final = [None] * len(pts_final)
            for i in range(len(self._radii)):
                if i < len(radii_for_final):
                    radii_for_final[i] = self._radii[i]
            # the appended final point keeps None

            if len(pts_final) < 2:
                return
            if len(pts_final) == 2:
                final_geom = QgsGeometry.fromPolylineXY(pts_final)
                # two-point straight segment cannot self-intersect
                valid = True
            else:
                new_pts = self._build_filleted_points(pts_final, radii_for_pts=radii_for_final)
                final_geom = QgsGeometry.fromPolylineXY(new_pts)
                # robust self-intersection test (detect crossing arcs/segments)
                try:
                    valid = not polyline_self_intersects(new_pts)
                except Exception:
                    # fallback: try GEOS validity if available
                    try:
                        valid = final_geom.isGeosValid()
                    except Exception:
                        valid = True

            if not valid:
                QMessageBox.warning(None, "Fillet warning",
                                    "The calculated fillet would create a self-intersecting or invalid polyline.\n"
                                    "Reduce the radius and try again.")
                return

            if self.layer.isEditable() or (self.layer.dataProvider().capabilities() & self.layer.dataProvider().AddFeatures):
                feat = QgsFeature(self.layer.fields())
                feat.setGeometry(final_geom)
                res, feats = self.layer.dataProvider().addFeatures([feat])
                if res:
                    self.layer.triggerRepaint()
            self.points = []
            self._radii = []
            self.perm_rb.reset(QgsWkbTypes.LineGeometry)
            self.preview_rb.reset(QgsWkbTypes.LineGeometry)
            self.radius_label.hide()
            # clear undo/redo after finishing shape
            self._undo_stack.clear()
            self._redo_stack.clear()

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

        # Per-corner temporary radius adjustments for the next corner (last placed point)
        # '.' increases, ',' decreases. Only affects next_point_radius, not global self.radius.
        if k == Qt.Key_Period or k == Qt.Key_Greater:
            # ensure there is a last placed point to modify
            if len(self.points) >= 1:
                if self.next_point_radius is None:
                    # start from global default
                    self.next_point_radius = float(self.radius)
                self.next_point_radius = float(self.next_point_radius + self._radius_step)
                changed = True
        elif k == Qt.Key_Comma or k == Qt.Key_Less:
            if len(self.points) >= 1:
                if self.next_point_radius is None:
                    self.next_point_radius = float(self.radius)
                self.next_point_radius = max(0.0, float(self.next_point_radius - self._radius_step))
                changed = True

        # Backspace as undo of last change / point addition
        if k == Qt.Key_Backspace:
            if self._undo_stack:
                self._do_undo()
                event.accept()
                return
            elif len(self.points) > 0:
                # fallback: remove last point and push snapshot to redo (keep radii aligned)
                prev_pts = [QgsPointXY(p) for p in self.points]
                prev_radii = [r for r in self._radii]
                next_snap = None if self.next_point_radius is None else float(self.next_point_radius)
                self._redo_stack.append((prev_pts, prev_radii, next_snap))

                self.points.pop()
                if len(self._radii) > 0:
                    self._radii.pop()
                # reset temporary next corner radius since the last point changed
                self.next_point_radius = None

                self.perm_rb.reset(QgsWkbTypes.LineGeometry)
                for p in self.points:
                    self.perm_rb.addPoint(p, False)
                self._update_preview(self.last_mouse_pt if self.last_mouse_pt else None)
                self._update_radius_label()
                event.accept()
                return

        # Ctrl+Z undo
        if event.modifiers() & Qt.ControlModifier and k == Qt.Key_Z:
            if self._undo_stack:
                self._do_undo()
                event.accept()
                return

        # Ctrl+Y redo
        if event.modifiers() & Qt.ControlModifier and k == Qt.Key_Y:
            if self._redo_stack:
                self._do_redo()
                event.accept()
                return

        if changed:
            if self.last_mouse_pt is not None:
                self._update_preview(self.last_mouse_pt)
            self._update_radius_label()
            event.accept()
        else:
            super().keyPressEvent(event)

    def _do_undo(self):
        # snapshot current state into redo, restore last undo snapshot to points/radii/next_point_radius
        current_pts = [QgsPointXY(p) for p in self.points]
        current_radii = [r for r in self._radii]
        current_next = None if self.next_point_radius is None else float(self.next_point_radius)
        self._redo_stack.append((current_pts, current_radii, current_next))

        pts_snap, radii_snap, next_snap = self._undo_stack.pop()
        self.points = [QgsPointXY(p) for p in pts_snap]
        self._radii = [r for r in radii_snap]
        self.next_point_radius = None if next_snap is None else float(next_snap)

        # update rubber band and preview
        self.perm_rb.reset(QgsWkbTypes.LineGeometry)
        for p in self.points:
            self.perm_rb.addPoint(p, False)
        self._update_preview(self.last_mouse_pt if self.last_mouse_pt else None)
        self._update_radius_label()

    def _do_redo(self):
        # snapshot current to undo, restore from redo
        current_pts = [QgsPointXY(p) for p in self.points]
        current_radii = [r for r in self._radii]
        current_next = None if self.next_point_radius is None else float(self.next_point_radius)
        self._undo_stack.append((current_pts, current_radii, current_next))

        pts_snap, radii_snap, next_snap = self._redo_stack.pop()
        self.points = [QgsPointXY(p) for p in pts_snap]
        self._radii = [r for r in radii_snap]
        self.next_point_radius = None if next_snap is None else float(next_snap)

        self.perm_rb.reset(QgsWkbTypes.LineGeometry)
        for p in self.points:
            self.perm_rb.addPoint(p, False)
        self._update_preview(self.last_mouse_pt if self.last_mouse_pt else None)
        self._update_radius_label()

    def _build_filleted_points(self, pts_list, radii_for_pts=None):
        """
        Build filleted polyline from pts_list.
        radii_for_pts (optional): list aligned to pts_list providing per-point radius or None to use global.
        radii_for_pts[i] is the radius to use when pts_list[i] is the corner (i.e., middle point).
        """
        if len(pts_list) < 3:
            return list(pts_list)
        new_pts = [QgsPointXY(pts_list[0])]
        n = len(pts_list)
        # ensure radii_for_pts length
        if radii_for_pts is None:
            radii_for_pts = [None] * n
        else:
            # pad if shorter
            radii_for_pts = list(radii_for_pts) + [None] * max(0, n - len(radii_for_pts))

        for i in range(1, n-1):
            prev_p = pts_list[i-1]
            cur_p = pts_list[i]
            next_p = pts_list[i+1]
            # choose radius: prefer radii_for_pts for this index, otherwise global self.radius
            r = radii_for_pts[i] if i < len(radii_for_pts) and radii_for_pts[i] is not None else self.radius
            seg = fillet_three_points(prev_p, cur_p, next_p, r, self.segs)
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

        # build radii_for_preview aligned with pts_for_preview
        radii_preview = []
        for i in range(len(self.points)):
            if i < len(self._radii):
                radii_preview.append(self._radii[i])
            else:
                radii_preview.append(None)
        # append None for the moving point
        radii_preview.append(None)
        # if user has a temporary next_point_radius (editing the last placed point), apply it to that corner
        if self.next_point_radius is not None and len(self.points) >= 1:
            # the corner to be filleted is the last placed point, which is index len(self.points)-1
            idx = len(self.points)-1
            if idx >= 0 and idx < len(radii_preview):
                radii_preview[idx] = float(self.next_point_radius)

        preview_pts = self._build_filleted_points(pts_for_preview, radii_for_pts=radii_preview)

        # check geometry validity (self-intersection / invalid)
        try:
            # prefer robust segment-pair test for self-intersection
            valid = not polyline_self_intersects(preview_pts)
        except Exception:
            try:
                geom = QgsGeometry.fromPolylineXY(preview_pts)
                valid = geom.isGeosValid()
            except Exception:
                valid = True

        # adjust preview color and label when invalid
        if not valid:
            self.preview_rb.setColor(self.preview_color_bad)
            self._last_preview_invalid = True
        else:
            self.preview_rb.setColor(self.preview_color_ok)
            self._last_preview_invalid = False

        for i, p in enumerate(preview_pts):
            self.preview_rb.addPoint(p, i == len(preview_pts)-1)
        self.preview_rb.show()
        # if invalid, update label to include warning
        if self._last_preview_invalid:
            # red background for warning
            self.radius_label.setStyleSheet("background: rgba(180,0,0,220); color: white; padding:4px; border-radius:4px;")
            text = "Radius: {:.2f}  (Warning: self-intersect)".format(self.radius)
            self.radius_label.setText(text)
            self.radius_label.adjustSize()
        else:
            # restore normal style
            self.radius_label.setStyleSheet("background: rgba(0,0,0,180); color: white; padding:4px; border-radius:4px;")
        try:
            self.canvas.refresh()
        except Exception:
            pass

    def _update_radius_label(self):
        # Show Next corner radius when temporary override exists; otherwise show Default radius
        if self.next_point_radius is not None and len(self.points) >= 1:
            text = "Next corner radius: {:.2f}".format(self.next_point_radius)
        else:
            text = "Default radius: {:.2f}".format(self.radius)

        # if last preview invalid, append warning (kept short; full message shown on double click)
        if self._last_preview_invalid:
            text += "  (invalid)"
            self.radius_label.setStyleSheet("background: rgba(180,0,0,220); color: white; padding:4px; border-radius:4px;")
        else:
            self.radius_label.setStyleSheet("background: rgba(0,0,0,180); color: white; padding:4px; border-radius:4px;")
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