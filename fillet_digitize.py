import os
from qgis.PyQt.QtWidgets import QAction
from qgis.PyQt.QtGui import QIcon
from qgis.core import QgsProject
from qgis.gui import QgsMapTool
from .fillet_tool import FilletDigitizeTool  # 将你的核心逻辑移到 fillet_tool.py


class FilletDigitizePlugin:
    def __init__(self, iface):
        self.iface = iface
        self.canvas = iface.mapCanvas()
        self.action = None
        self.tool = None

    def initGui(self):
        icon_path = os.path.join(os.path.dirname(__file__), "icons", "icon.svg")
        self.action = QAction(
            QIcon(icon_path),
            "Fillet Digitize Tool",
            self.iface.mainWindow()
        )
        self.action.setCheckable(True)
        self.action.triggered.connect(self.run)
        self.iface.addToolBarIcon(self.action)
        self.iface.addPluginToVectorMenu("Fillet Digitize", self.action)

    def unload(self):
        self.iface.removeToolBarIcon(self.action)
        self.iface.removePluginVectorMenu("Fillet Digitize", self.action)
        if self.tool and self.canvas.mapTool() == self.tool:
            self.canvas.unsetMapTool(self.tool)
        del self.action
        del self.tool

    def run(self):
        layer = self.iface.activeLayer()
        if not layer or not layer.type().value == 0:  # 0 = vector
            self.iface.messageBar().pushWarning("Fillet Tool", "Please select an active vector layer.")
            self.action.setChecked(False)
            return
        if not layer.isEditable():
            self.iface.messageBar().pushWarning("Fillet Tool", "Layer must be in edit mode.")
            self.action.setChecked(False)
            return
        if layer.geometryType().value != 1:  # 1 = line
            self.iface.messageBar().pushWarning("Fillet Tool", "Active layer must be a line layer.")
            self.action.setChecked(False)
            return

        # Create or reuse tool
        if self.tool is None:
            self.tool = FilletDigitizeTool(self.canvas, layer, radius=30.0, segs_per_quarter=12)
        else:
            self.tool.layer = layer
            self.tool.radius = 30.0

        self.tool.setAction(self.action)
        self.canvas.setMapTool(self.tool)