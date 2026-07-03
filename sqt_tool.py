"""傑出品 — Navisworks XML 生成工具。

基于 Tkinter 的桌面工具，用于快速生成 Autodesk Navisworks
查询 XML 文件（支架/坐标查询）。
"""

import re
import sys
import tkinter as tk
import xml.etree.ElementTree as ET
from collections.abc import Callable
from pathlib import Path
from tkinter import filedialog, messagebox, scrolledtext

# ── 应用元信息 ──────────────────────────────────────────────
APP_TITLE = "傑出品"
WINDOW_SIZE = "680x560"

# ── 输入限制 ────────────────────────────────────────────────
MAX_INPUT_LINES = 900
MAX_LINE_LENGTH = 20

# ── UI 颜色 ─────────────────────────────────────────────────
COLOR_BG = "#f7f7f5"
COLOR_TEXT_PRIMARY = "#222222"
COLOR_TEXT_SECONDARY = "#666666"
COLOR_BORDER = "#b8b8b0"
COLOR_BORDER_FOCUS = "#5c6a4a"

COLOR_BUTTON_BRACKET_BG = "#2f3a2f"
COLOR_BUTTON_BRACKET_ACTIVE = "#435143"
COLOR_BUTTON_COORD_BG = "#6f755f"
COLOR_BUTTON_COORD_ACTIVE = "#81886f"
COLOR_BUTTON_FG = "#ffffff"

# ── UI 字体 ─────────────────────────────────────────────────
FONT_TITLE = ("Microsoft YaHei UI", 18, "bold")
FONT_BUTTON = ("Microsoft YaHei UI", 10, "bold")
FONT_HINT = ("Microsoft YaHei UI", 10)
FONT_INPUT = ("Microsoft YaHei UI", 12)

# ── 默认文件配置 ────────────────────────────────────────────
DEFAULT_BRACKET_FILENAME = "SQT-M14-9.19.nwd"
DEFAULT_COORD_FILENAME = "TS-M12(2)3.26.nwd"
DEFAULT_COORD_FILEPATH = ""


# ── 路径工具函数 ────────────────────────────────────────────


def app_dir() -> Path:
    """返回应用所在目录（支持 PyInstaller 打包后场景）。"""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent


def resource_dir() -> Path:
    """返回资源目录（支持 PyInstaller 单文件模式）。"""
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS)
    return Path(__file__).resolve().parent


def coordinate_template_paths() -> list[Path]:
    """返回坐标模板文件的候选路径列表（去重）。"""
    external_template = app_dir() / "坐标用.xml"
    bundled_template = resource_dir() / "坐标用.xml"
    if external_template == bundled_template:
        return [external_template]
    return [external_template, bundled_template]


def find_coordinate_template() -> Path | None:
    """在候选路径中查找存在的坐标模板文件。"""
    for template_path in coordinate_template_paths():
        if template_path.exists():
            return template_path
    return None


# ── 文件对话框 ──────────────────────────────────────────────

_last_save_dir: str = ""


def choose_save_path(default_name: str, title: str = "保存文件") -> str:
    """打开 Windows 原生另存为对话框，默认定位到上次的目录。

    Args:
        default_name: 默认文件名。
        title: 对话框标题。

    Returns:
        完整的保存路径，取消则为空字符串。
    """
    global _last_save_dir
    path = filedialog.asksaveasfilename(
        title=title,
        initialdir=_last_save_dir or None,
        initialfile=default_name,
        defaultextension=".xml",
        filetypes=[("XML 文件", "*.xml"), ("所有文件", "*.*")],
    )
    if path:
        _last_save_dir = str(Path(path).parent)
    return path


# ── XML 构建函数 ────────────────────────────────────────────


def _sanitize_xml_text(value: str) -> str:
    """移除 XML 1.0 禁止的控制字符。

    Args:
        value: 原始用户输入。

    Returns:
        清理后的 XML 文本内容。
    """
    cleaned = re.sub(r"[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]", "", value)
    return cleaned


def build_condition_element(
    value: str,
    *,
    test: str,
    name_internal: str,
    name_text: str,
    category_internal: str | None = None,
    category_text: str | None = None,
) -> ET.Element:
    """构建 Navisworks 条件查询 XML 元素。

    Args:
        value: 查询值（会被清理非法控制字符）。
        test: 匹配方式（"equals" / "contains"）。
        name_internal: name 元素的 internal 属性。
        name_text: name 元素的显示文本。
        category_internal: 可选的 category 元素 internal 属性。
        category_text: 可选的 category 元素显示文本。

    Returns:
        构建好的 <condition> ET.Element 对象。
    """
    safe_value = _sanitize_xml_text(value)
    cond = ET.Element("condition", test=test, flags="74")

    if category_internal and category_text:
        category = ET.SubElement(cond, "category")
        ET.SubElement(category, "name", internal=category_internal).text = category_text

    prop = ET.SubElement(cond, "property")
    ET.SubElement(prop, "name", internal=name_internal).text = name_text

    val = ET.SubElement(cond, "value")
    ET.SubElement(val, "data", type="wstring").text = safe_value

    return cond


def build_bracket_condition(value: str) -> ET.Element:
    """构建支架查询条件元素（equals 匹配 场景用户名）。"""
    return build_condition_element(
        value,
        test="equals",
        name_internal="LcOaSceneBaseUserName",
        name_text="名称",
    )


def build_coordinate_condition(value: str) -> ET.Element:
    """构建坐标查询条件元素（contains 匹配 System Path）。"""
    return build_condition_element(
        value,
        test="contains",
        name_internal="System Path",
        name_text="System Path",
        category_internal="SP3D",
        category_text="SmartPlant 3D",
    )


# ── XML 文件生成 ────────────────────────────────────────────


def navisworks_xml(
    conditions: list[ET.Element],
    filename: str,
    filepath: str = "",
) -> str:
    """生成完整的 Navisworks exchange XML 字符串。

    Args:
        conditions: 条件 Element 列表。
        filename: 目标文件名属性。
        filepath: 目标文件路径属性。

    Returns:
        格式正确的 XML 字符串。
    """
    root = ET.Element(
        "exchange",
        attrib={
            "xmlns:xsi": "http://www.w3.org/2001/XMLSchema-instance",
            "xsi:noNamespaceSchemaLocation": (
                "http://download.autodesk.com/us/navisworks/schemas/nw-exchange-12.0.xsd"
            ),
            "units": "m",
            "filename": filename,
            "filepath": filepath,
        },
    )
    findspec = ET.SubElement(root, "findspec", mode="all", disjoint="0")
    conditions_elem = ET.SubElement(findspec, "conditions")
    for cond in conditions:
        conditions_elem.append(cond)
    ET.SubElement(findspec, "locator").text = "/"

    return ET.tostring(root, encoding="unicode", xml_declaration=True)


def read_items(text_widget: tk.Text) -> list[str]:
    """从文本组件读取用户输入，按行分割并校验。

    Args:
        text_widget: Tkinter Text 组件。

    Returns:
        按行分割并去除首尾空白的查询值列表。

    Raises:
        ValueError: 输入行数或单行长度超出限制。
    """
    if getattr(text_widget, "_is_placeholder", False):
        return []

    raw = text_widget.get("1.0", tk.END)
    lines = [line.strip() for line in raw.splitlines() if line.strip()]

    if len(lines) > MAX_INPUT_LINES:
        raise ValueError(
            f"输入行数不能超过 {MAX_INPUT_LINES} 行（当前 {len(lines)} 行）"
        )

    for i, line in enumerate(lines, start=1):
        if len(line) > MAX_LINE_LENGTH:
            raise ValueError(
                f"第 {i} 行超长（{len(line)} 字符），"
                f"最大允许 {MAX_LINE_LENGTH} 字符"
            )

    return lines


def generate_xml_content(
    items: list[str],
    condition_builder: Callable[[str], ET.Element],
    filename: str,
    filepath: str = "",
) -> str:
    """纯函数：根据查询值列表生成 XML 字符串。

    Args:
        items: 查询值列表。
        condition_builder: 将字符串转为 ET.Element 的构建函数。
        filename: 写入 XML 的 filename 属性。
        filepath: 写入 XML 的 filepath 属性。

    Returns:
        完整的 XML 字符串。
    """
    conditions = [condition_builder(item) for item in items]
    return navisworks_xml(conditions, filename, filepath)


def write_xml_file(content: str, output_path: Path) -> None:
    """将 XML 内容写入文件。

    Args:
        content: XML 字符串。
        output_path: 输出文件路径。

    Raises:
        OSError: 文件写入失败。
    """
    output_path.write_text(content, encoding="utf-8")


def write_bracket_xml(items: list[str]) -> None:
    """生成支架查询 XML 文件。"""
    if not items:
        messagebox.showwarning("提示", "没有输入内容")
        return

    save_path = choose_save_path("支架.xml", "保存支架查询文件")
    if not save_path:
        return

    output_path = Path(save_path)

    try:
        content = generate_xml_content(
            items, build_bracket_condition, DEFAULT_BRACKET_FILENAME
        )
        write_xml_file(content, output_path)
    except OSError as exc:
        messagebox.showerror("写入失败", f"无法生成文件：\n{exc}")
        return


def load_coordinate_template_info() -> dict[str, str]:
    """从坐标模板文件读取默认文件名和路径。"""
    defaults: dict[str, str] = {
        "filename": DEFAULT_COORD_FILENAME,
        "filepath": DEFAULT_COORD_FILEPATH,
    }

    coordinate_template = find_coordinate_template()
    if coordinate_template is None:
        return defaults

    try:
        parser = ET.XMLParser()
        parser.entity = {}  # 禁用外部实体解析（XXE 防护）
        root = ET.parse(coordinate_template, parser).getroot()
    except (OSError, ET.ParseError):
        return defaults

    return {
        "filename": root.attrib.get("filename", defaults["filename"]),
        "filepath": root.attrib.get("filepath", defaults["filepath"]),
    }


def write_coordinate_xml(items: list[str]) -> None:
    """生成坐标查询 XML 文件（使用模板配置）。"""
    if not items:
        messagebox.showwarning("提示", "没有输入内容")
        return

    save_path = choose_save_path("坐标.xml", "保存坐标查询文件")
    if not save_path:
        return

    template = load_coordinate_template_info()
    output_path = Path(save_path)

    try:
        content = generate_xml_content(
            items,
            build_coordinate_condition,
            template["filename"],
            template["filepath"],
        )
        write_xml_file(content, output_path)
    except OSError as exc:
        messagebox.showerror("写入失败", f"无法生成文件：\n{exc}")
        return


# ── UI 构建 ────────────────────────────────────────────────


def _draw_round_rect(
    canvas: tk.Canvas,
    x1: int, y1: int,
    x2: int, y2: int,
    r: int,
    **kwargs: object,
) -> int:
    """在 Canvas 上绘制圆角矩形。

    Args:
        canvas: Canvas 对象。
        x1, y1: 左上角坐标。
        x2, y2: 右下角坐标。
        r: 圆角半径。

    Returns:
        图形对象的 ID。
    """
    points = [
        x1, y1 + r,
        x1, y1,
        x1 + r, y1,
        x2 - r, y1,
        x2, y1,
        x2, y1 + r,
        x2, y2 - r,
        x2, y2,
        x2 - r, y2,
        x1 + r, y2,
        x1, y2,
        x1, y2 - r,
    ]
    return canvas.create_polygon(points, smooth=True, splinesteps=12, **kwargs)


def _create_rounded_button(
    parent: tk.Frame,
    text: str,
    command: Callable[[], object],
    bg: str,
    active_bg: str,
    *,
    width: int = 100,
    height: int = 36,
    radius: int = 8,
    fg: str = COLOR_BUTTON_FG,
    font: tuple = FONT_BUTTON,
) -> tk.Canvas:
    """创建圆角按钮（基于 Canvas，圆角不会因拉伸变形）。

    Args:
        parent: 父容器。
        text: 按钮文字。
        command: 点击回调。
        bg: 背景色。
        active_bg: 悬停/激活态背景色。
        width: 按钮宽度（像素）。
        height: 按钮高度（像素）。
        radius: 圆角半径。
        fg: 文字颜色。
        font: 字体。

    Returns:
        Canvas 实例，可被 pack/grid/place 布局。
    """
    canvas = tk.Canvas(
        parent,
        width=width,
        height=height,
        bg=COLOR_BG,
        highlightthickness=0,
        relief=tk.FLAT,
        cursor="hand2",
    )

    rect_id = _draw_round_rect(
        canvas, 1, 1, width - 1, height - 1, radius,
        fill=bg, outline=bg,
    )

    canvas.create_text(
        width // 2, height // 2,
        text=text,
        font=font,
        fill=fg,
    )

    def _on_enter(_event: object = None) -> None:
        canvas.itemconfig(rect_id, fill=active_bg, outline=active_bg)

    def _on_leave(_event: object = None) -> None:
        canvas.itemconfig(rect_id, fill=bg, outline=bg)

    def _on_click(_event: object = None) -> None:
        canvas.itemconfig(rect_id, fill=active_bg, outline=active_bg)
        canvas.after(100, lambda: canvas.itemconfig(rect_id, fill=bg, outline=bg))
        command()

    canvas.bind("<Enter>", _on_enter)
    canvas.bind("<Leave>", _on_leave)
    canvas.bind("<Button-1>", _on_click)

    return canvas


def _build_title(parent: tk.Frame) -> None:
    """创建应用标题。"""
    title = tk.Label(
        parent,
        text=APP_TITLE,
        font=FONT_TITLE,
        bg=COLOR_BG,
        fg=COLOR_TEXT_PRIMARY,
    )
    title.pack(anchor="w")


def _build_action_bar(parent: tk.Frame, root: tk.Tk) -> tk.Frame:
    """创建操作栏（提示 + 按钮）。

    Returns:
        操作栏 Frame，供外部引用。
    """
    action_bar = tk.Frame(parent, bg=COLOR_BG)
    action_bar.pack(fill=tk.X, pady=(8, 16))

    hint = tk.Label(
        action_bar,
        text="每行输入一个查询值",
        font=FONT_HINT,
        bg=COLOR_BG,
        fg=COLOR_TEXT_SECONDARY,
    )
    hint.pack(side=tk.LEFT)

    coord_btn = _create_rounded_button(
        action_bar,
        "查坐标",
        command=lambda: _safe_submit(root, write_coordinate_xml),
        bg=COLOR_BUTTON_COORD_BG,
        active_bg=COLOR_BUTTON_COORD_ACTIVE,
        width=110,
        height=38,
    )
    coord_btn.pack(side=tk.RIGHT, padx=(8, 0))

    bracket_btn = _create_rounded_button(
        action_bar,
        "查支架",
        command=lambda: _safe_submit(root, write_bracket_xml),
        bg=COLOR_BUTTON_BRACKET_BG,
        active_bg=COLOR_BUTTON_BRACKET_ACTIVE,
        width=110,
        height=38,
    )
    bracket_btn.pack(side=tk.RIGHT)

    return action_bar


def _build_input_area(parent: tk.Frame) -> scrolledtext.ScrolledText:
    """创建输入文本框区（含占位符 + 清空按钮）。

    Returns:
        ScrolledText 组件实例。
    """
    # ── 独立容器，隔离布局影响 ──
    container = tk.Frame(parent, bg=COLOR_BG)
    container.pack(fill=tk.BOTH, expand=True)

    # ── 底部按钮栏（先 pack，固定在底部） ──
    bottom_bar = tk.Frame(container, bg=COLOR_BG)
    bottom_bar.pack(fill=tk.X, side=tk.BOTTOM, pady=(10, 0))

    PLACEHOLDER = "输入内容"

    # ── 行数统计（第一性原理：每次直接从文本控件读取原始内容计算，不维护缓存状态） ──
    stats_label = tk.Label(
        bottom_bar,
        text="0 行",
        font=FONT_HINT,
        bg=COLOR_BG,
        fg=COLOR_TEXT_SECONDARY,
    )
    stats_label.pack(side=tk.LEFT)

    def _refresh_stats() -> None:
        """实时统计输入区中有内容的行数。

        第一性原理：每次直接从 Text widget 读取全部原始内容计算，
        不依赖额外计数器或缓存，确保统计永远与真实数据一致。
        """
        if text._is_placeholder:
            stats_label.config(text="0 行")
            return
        raw = text.get("1.0", tk.END)
        count = sum(1 for line in raw.splitlines() if line.strip())
        stats_label.config(text=f"{count} 行")

    def _clear_input(text_widget: scrolledtext.ScrolledText) -> None:
        """清空输入框内容并恢复占位符。"""
        text_widget.delete("1.0", tk.END)
        text_widget._is_placeholder = True
        text_widget.insert("1.0", PLACEHOLDER, "ph")
        _refresh_stats()

    clear_btn = _create_rounded_button(
        bottom_bar,
        "清空",
        command=lambda: _clear_input(text),
        bg="#d4d4ce",
        active_bg="#c0c0b8",
        width=74,
        height=30,
        radius=6,
        fg=COLOR_TEXT_PRIMARY,
        font=FONT_HINT,
    )
    clear_btn.pack(side=tk.RIGHT)

    # ── 输入框（撑满容器剩余空间） ──
    text = scrolledtext.ScrolledText(
        container,
        wrap=tk.WORD,
        font=FONT_INPUT,
        relief=tk.FLAT,
        borderwidth=0,
        highlightthickness=2,
        highlightbackground=COLOR_BORDER,
        highlightcolor=COLOR_BORDER_FOCUS,
        fg=COLOR_TEXT_PRIMARY,
    )
    text.pack(fill=tk.BOTH, expand=True)

    # ── 占位符 ──
    text._is_placeholder = True
    text.tag_configure("ph", foreground=COLOR_TEXT_SECONDARY)
    text.insert("1.0", PLACEHOLDER, "ph")

    def _on_focus_in(_event: object = None) -> None:
        if text._is_placeholder:
            text.delete("1.0", tk.END)
            text._is_placeholder = False
        _refresh_stats()

    def _on_focus_out(_event: object = None) -> None:
        if not text.get("1.0", "end-1c").strip():
            text.delete("1.0", tk.END)
            text.insert("1.0", PLACEHOLDER, "ph")
            text._is_placeholder = True
        _refresh_stats()

    text.bind("<FocusIn>", _on_focus_in)
    text.bind("<FocusOut>", _on_focus_out)
    text.bind("<KeyRelease>", lambda _: _refresh_stats(), add=True)
    text.bind("<<Paste>>", lambda _: text.after(10, _refresh_stats), add=True)

    return text


def build_ui(root: tk.Tk) -> None:
    """创建并布局所有 UI 组件。

    Args:
        root: Tkinter 根窗口。
    """
    outer = tk.Frame(root, bg=COLOR_BG)
    outer.pack(fill=tk.BOTH, expand=True, padx=32, pady=24)

    _build_title(outer)
    _build_action_bar(outer, root)
    root._input_text = _build_input_area(outer)  # type: ignore[attr-defined]


def _safe_submit(
    root: tk.Tk,
    handler: Callable[[list[str]], object],
) -> None:
    """安全提交：读取输入 -> 校验 -> 执行业务逻辑并捕获用户可见的错误。

    Args:
        root: Tkinter 根窗口（从中获取输入组件）。
        handler: 业务处理函数（接收字符串列表）。
    """
    try:
        items = read_items(root._input_text)  # type: ignore[attr-defined]
    except ValueError as exc:
        messagebox.showerror("输入错误", str(exc))
        return

    try:
        handler(items)
    except OSError as exc:
        messagebox.showerror("写入失败", f"无法生成文件：\n{exc}")


# ── 入口点 ──────────────────────────────────────────────────


def _on_window_click(event: tk.Event) -> None:
    """点击窗口空白区域让输入框失去焦点，恢复占位符。"""
    if event.widget.winfo_class() not in ("Text", "Scrollbar"):
        event.widget.winfo_toplevel().focus_set()


def main() -> None:
    """应用入口：初始化窗口、构建 UI、进入事件循环。"""
    root = tk.Tk()
    root.title(APP_TITLE)
    root.geometry(WINDOW_SIZE)
    root.minsize(420, 280)
    root.configure(bg=COLOR_BG)

    build_ui(root)
    root.bind("<Button-1>", _on_window_click)
    root.mainloop()


if __name__ == "__main__":
    main()
