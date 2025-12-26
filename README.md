# ![LOGO](/icons/icon.svg) Fillet Digitize Tool  
# ![LOGO](/icons/icon.svg) 倒角数字化工具

> **Draw polylines with real-time rounded corners in QGIS.**  
> **在 QGIS 中绘制带实时倒角（圆角）的多段线。**

This QGIS plugin enables you to digitize polylines with live fillet (rounded corner) previews. Adjust the fillet radius interactively using keyboard shortcuts while drawing—ideal for sketching roads, pipelines, boundaries, or any feature requiring smooth transitions.  
本插件支持在绘制多段线时实时预览倒角效果，并可通过键盘快捷键动态调整倒角半径，特别适用于快速绘制带圆角的道路中心线、管线、边界等要素。

Unlike traditional workflows that apply fillets *after* geometry creation, this tool integrates rounding into the digitizing process itself—mimicking how designers naturally sketch on reference maps.  
与传统“先绘图、后倒角”的流程不同，本工具将倒角直接融入绘制线段过程，更贴近设计师在底图上手绘的直觉操作。

---

## 🌟 Features / 功能特点

- **Real-time fillet preview**  
  **实时倒角预览**：绘制过程中动态显示圆角效果
- **Interactive radius control**  
  **交互式半径控制**：
  - Global default radius: `+`/`-` (or `=`/`_`) to adjust by **1 unit**; `]`/`[` to adjust by **10 units**  
    全局默认半径：按 `+` / `-`（或 `=` / `_`）以 **1 单位**增减；按 `]` / `[` 以 **10 单位**增减
  - Per-vertex radius: Use `,` to decrease / `.` to increase the radius for the **next corner only** (temporary override)  
    逐角独立半径：使用 `,`（逗号）减小 / `.`（句号）增大 **下一个拐角** 的半径（临时覆盖，不影响全局值）
- **On-cursor radius display**  
  **光标附近实时显示半径值**：清晰反馈当前设置
- **Self-intersection detection**  
  **自相交检测**：
  - Preview turns **red** if fillet causes self-intersection, with warning tooltip  
    若倒角导致自相交，预览线变为**红色**并提示警告
  - Invalid geometries are blocked on double-click completion  
    双击完成时若结果无效，将弹出警告并阻止保存
- **Full undo/redo support**  
  **完整的撤销/重做支持**：
  - `Backspace`: Undo last action (point addition or radius change)  
    `Backspace`：撤销上一步操作（包括点添加和半径修改）
  - `Ctrl+Z` / `Ctrl+Y`: Standard undo/redo  
    `Ctrl+Z` / `Ctrl+Y`：标准撤销/重做
- **Pure PyQGIS implementation**  
  **纯 PyQGIS 实现**：无外部依赖
- **Works with any editable line layer** (e.g., Shapefile, GeoPackage)  
  **支持任意可编辑线矢量图层**（如 Shapefile、GeoPackage）

---

## 📥 Installation / 安装方法

### Method 1: QGIS Plugin Repository (Recommended)  
### 方法一：通过 QGIS 插件仓库（推荐）
1. Go to **Plugins → Manage and Install Plugins**  
   菜单栏 → **Plugins（插件）** → **Manage and Install Plugins（管理并安装插件）**
2. Search for `Fillet Digitize Tool`  
   在搜索框中输入 `Fillet Digitize Tool`
3. Click **Install** and **Enable**  
   点击安装并启用

### Method 2: Manual Installation  
### 方法二：手动安装
1. Download the plugin folder [`fillet_digitize`](https://github.com/winchop/fillet_digitize/releases)  
   下载插件文件夹 [`fillet_digitize`](https://github.com/winchop/fillet_digitize/releases)
2. Copy it to your QGIS plugins directory:  
   复制到 QGIS 插件目录：
   - **Windows**: `%APPDATA%\QGIS\QGIS3\profiles\default\python\plugins\`  
   - **macOS**: `~/Library/Application Support/QGIS/QGIS3/profiles/default/python/plugins/`  
   - **Linux**: `~/.local/share/QGIS/QGIS3/profiles/default/python/plugins/`
3. Restart QGIS and enable the plugin in the Plugin Manager  
   重启 QGIS，在插件管理器中启用

### Method 3: Clone from GitHub  
### 方法三：从 GitHub 克隆
```bash
cd ~/.local/share/QGIS/QGIS3/profiles/default/python/plugins/
git clone https://github.com/winchop/fillet_digitize.git
```

---

## 🛠️ Usage / 使用说明

1. Load an **editable line vector layer** (e.g., Shapefile, GeoPackage)  
   加载或新建一个**可编辑的线矢量图层**（如 Shapefile、GeoPackage）
2. Toggle editing mode for the layer  
   开启该图层的编辑模式
3. Click the **“Fillet Digitize Tool”** icon in the toolbar  
   点击工具栏中的 **“倒角数字化工具”** 图标
4. **Left-click** to add vertices  
   **左键单击** 添加顶点
5. **Move the mouse** to preview the filleted polyline with current radius  
   **移动鼠标** 预览当前半径下的倒角效果
6. **Adjust radius on-the-fly**:  
   **实时调整半径**：
   - `+` or `=` → Increase global radius by 1  
     `+` 或 `=` → 全局半径 +1
   - `-` or `_` → Decrease global radius by 1  
     `-` 或 `_` → 全局半径 -1
   - `]` → Increase global radius by 10  
     `]` → 全局半径 +10
   - `[` → Decrease global radius by 10  
     `[` → 全局半径 -10
   - `.` → Increase next corner’s radius by 1 (temporary)  
     `.` → **下一个拐角** 半径 +1（临时）
   - `,` → Decrease next corner’s radius by 1 (temporary)  
     `,` → **下一个拐角** 半径 -1（临时）
7. **Undo actions**:  
   **撤销操作**：
   - `Backspace`: Undo last step  
     `Backspace`：撤销上一步
   - `Ctrl+Z`: Undo  
     `Ctrl+Z`：撤销
   - `Ctrl+Y`: Redo  
     `Ctrl+Y`：重做
8. **Double-click** to finalize and save the feature  
   **双击** 完成绘制并保存要素

> 💡 **Tips / 提示**：  
> - The current radius (global or per-corner) is displayed near the cursor  
>   当前半径（全局或逐角）会显示在光标附近  
> - A **red preview** indicates self-intersection — reduce the radius  
>   **红色预览** 表示自相交，请减小半径  
> - Temporary per-corner radius applies only to the **last placed vertex**, and takes effect when the *next* point is added  
>   临时拐角半径仅作用于**最后一个已放置的点**，在下一点确认后生效

---

## 📐 How It Works / 工作原理

At each internal vertex, the tool constructs a **circular arc tangent to both adjacent segments**.  
在每个内部顶点处，工具生成一段**与相邻两线段相切的圆弧**。

- Radius can be set globally or overridden per vertex  
  半径可全局设置，也可为每个拐角单独指定
- Automatically reduces radius for sharp angles or short segments to maintain valid geometry  
  对锐角或短线段自动缩减半径，确保几何有效性
- All previews and final geometries undergo **self-intersection checks** (via segment-pair intersection + GEOS fallback)  
  所有预览和最终结果均经过**自相交检测**（基于线段对交叉判断 + GEOS 回退）

---

## 🧪 Requirements / 环境要求

- QGIS 3.16 or higher  
  QGIS 3.16 或更高版本
- Python 3 (bundled with QGIS)  
  Python 3（QGIS 自带）
- An editable **line-type vector layer**  
  一个可编辑的**线类型矢量图层**

---

## 📜 License / 许可证

This project is licensed under the [MIT License](LICENSE).  
本项目采用 [MIT 许可证](LICENSE) 发布。

---

## 🙌 Contributing / 贡献

Contributions are welcome! Please open an issue or submit a pull request.  
欢迎提交 Issue 或 Pull Request！

---

## 📧 Contact / 联系方式

- **Author**: 🚁 Chopper 🚁  
- **Email**: winchop@gmail.com  
- **GitHub**: [@winchop](https://github.com/winchop)

---