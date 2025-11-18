# Fillet Digitize Tool  
## 倒角数字化工具  

A QGIS plugin to draw polylines with real-time rounded corners (fillets). Adjust the fillet radius on-the-fly using keyboard shortcuts while digitizing.  
QGIS 插件，用于绘制带实时倒角（圆角）的多段线。在数字化过程中，可通过键盘快捷键即时调整倒角半径。已有的工具倾向于在polyline 、Polygon 绘制完成后，再进行下一步的圆角修饰步骤。实际绘图过程中，设计师习惯于边思考边绘制。

---

## 🌟 Features / 功能特点

- **Real-time preview** of filleted polyline as you digitize  
  数字化时**实时预览**倒角多段线效果  
- **Interactive radius control**: Press `+`/`-` or `[`/`]` to increase/decrease radius  
  **交互式半径控制**：按 `+`/`-` 或 `[`/`]` 键增大/减小半径  
- **On-screen radius display** near cursor for visual feedback  
  光标附近显示**半径数值**，提供直观反馈  
- Works on any **editable line vector layer**  
  支持任意**可编辑的线矢量图层**  
- No external dependencies – pure PyQGIS implementation  
  无外部依赖，纯 PyQGIS 实现  

---

## 📥 Installation / 安装方法

### Option 1: Manual Install (Recommended)  
### 方法一：手动安装（推荐）

1. Download the plugin folder [`fillet_digitize`](https://github.com/yourname/fillet_digitize/releases)  
   下载插件文件夹 [`fillet_digitize`](https://github.com/yourname/fillet_digitize/releases)
2. Copy it to your QGIS plugin directory:  
   将其复制到 QGIS 插件目录：
   - **Windows**:  
     `%APPDATA%\QGIS\QGIS3\profiles\default\python\plugins\`
   - **macOS**:  
     `~/Library/Application Support/QGIS/QGIS3/profiles/default/python/plugins/`
   - **Linux**:  
     `~/.local/share/QGIS/QGIS3/profiles/default/python/plugins/`
3. Restart QGIS and enable the plugin in **Plugins → Manage and Install Plugins**  
   重启 QGIS，在 **插件 → 管理和安装插件** 中启用本插件

### Option 2: Clone from GitHub  
### 方法二：从 GitHub 克隆

```bash
cd ~/.local/share/QGIS/QGIS3/profiles/default/python/plugins/
git clone https://github.com/winchop/fillet_digitize.git
```

---

## 🛠️ Usage / 使用说明

1. Load a **line vector layer** (e.g., Shapefile, GeoPackage)  
   加载一个**线矢量图层**（如 Shapefile、GeoPackage）
2. Toggle **editing mode** for the layer  
   开启图层的**编辑模式**
3. Click the **Fillet Digitize Tool** icon in the toolbar  
   点击工具栏中的 **倒角数字化工具** 图标
4. **Left-click** to add vertices  
   **左键单击** 添加顶点
5. **Move mouse** to preview filleted polyline with current radius  
   **移动鼠标** 预览当前半径下的倒角效果
6. Press:
   - `+` or `=` → increase radius by 1 unit  
     `+` 或 `=` → 半径增加 1 单位
   - `-` or `_` → decrease radius by 1 unit  
     `-` 或 `_` → 半径减少 1 单位
   - `]` → increase radius by 10 units  
     `]` → 半径增加 10 单位
   - `[` → decrease radius by 10 units  
     `[` → 半径减少 10 单位
7. **Double-click** to finish and save the feature  
   **双击** 完成绘制并保存要素

> 💡 The radius value is displayed near the cursor in real time.  
> 💡 半径值会实时显示在光标附近。

---

## 📐 How It Works / 工作原理

At each interior vertex, the tool computes a circular arc that smoothly connects the two adjacent segments, tangent to both. The arc radius is user-defined and adjustable during digitizing. For sharp angles or short segments, the radius is automatically reduced to fit geometrically.  
在每个内部顶点处，工具会计算一段圆弧，使其与相邻两段线平滑相切连接。圆弧半径由用户定义，并可在绘制过程中调整。对于锐角或短线段，半径会自动缩小以适应几何约束。

---

## 🧪 Requirements / 环境要求

- **QGIS 3.16 or higher**  
  QGIS 3.16 及以上版本
- Python 3 (built into QGIS)  
  Python 3（QGIS 自带）
- An editable **line-type vector layer**  
  一个可编辑的**线类型矢量图层**

---

## 📜 License / 许可证

This project is licensed under the **GNU General Public License v3.0**.  
本项目采用 **GNU 通用公共许可证 v3.0** 发布。

See [LICENSE](LICENSE) for details.  
详见 [LICENSE](LICENSE) 文件。

---

## 🙌 Contributing / 贡献

Contributions are welcome! Please open an issue or submit a pull request.  
欢迎贡献！请提交 Issue 或 Pull Request。

---

## 📧 Contact / 联系方式

- Author:🚁 Chopper 🚁 
- Email: winchop@gmail.com  
   
- GitHub: [@winchop](https://github.com/winchop)  

---

## To Be Add / 待续
- 撤销操作
- 绘制过程调整半径，区分为仅调整当前 / 全局调整
- ……
---
> ✨ Happy mapping with smooth corners!  
> ✨ 享受流畅圆角绘图的乐趣吧！