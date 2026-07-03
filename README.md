# 傑出品 — Navisworks XML 生成工具

![Python](https://img.shields.io/badge/Python-3.12+-blue?logo=python)
![Tkinter](https://img.shields.io/badge/UI-Tkinter-green)
![Navisworks](https://img.shields.io/badge/Navisworks-Manage%202023-orange)
![Platform](https://img.shields.io/badge/Platform-Windows-lightgrey?logo=windows)

桌面工具，把人工输入的查询值批量生成 Autodesk Navisworks 可读取的 exchange XML 查询文件。支持**支架查询**和**坐标查询**两种模式。

> 配套的 Navisworks 查找插件在 [`T8899J/navisworks-plugin`](https://github.com/T8899J/navisworks-plugin)。

---

## 快速开始

### 直接运行（需 Python 3.12+）

```bash
pip install -r requirements.txt
python sqt_tool.py
```

或双击 `运行新版工具.bat`。

### 打包成 exe

用 PyInstaller 打包为独立的 Windows exe，无需 Python 环境即可运行：

```bash
pyinstaller 傑出品.spec
```

产物在 `dist/傑出品.exe`。

---

## 界面

```
┌──────────────────────────────────────┐
│  傑出品                               │
├──────────────────────────────────────┤
│  每行输入一个查询值      [查支架][查坐标] │
├──────────────────────────────────────┤
│                                      │
│  输入区（每行一个值，最多 900 行）      │
│  每行上限 20 字符                      │
│                                      │
├──────────────────────────────────────┤
│  N 行                        [清空]   │
└──────────────────────────────────────┘
```

- **查支架** — 生成 `equals` 匹配的支架查询 XML
- **查坐标** — 生成 `contains` 匹配的坐标查询 XML
- 底部实时显示有内容的行数（第一性原理统计）
- 输入区带占位符、清空按钮、行数/长度校验

---

## 生成示例

支架查询 XML：
```xml
<?xml version="1.0" encoding="utf-8"?>
<exchange units="m" filename="SQT-M14-9.19.nwd">
  <findspec mode="all" disjoint="0">
    <conditions>
      <condition test="equals" flags="74">
        <property>
          <name internal="LcOaSceneBaseUserName">名称</name>
        </property>
        <value>
          <data type="wstring">查询值</data>
        </value>
      </condition>
    </conditions>
    <locator>/</locator>
  </findspec>
</exchange>
```

---

## 项目文件

```
navisworks-xml-tool/
├── sqt_tool.py              # 主程序
├── 傑出品.spec               # PyInstaller 打包配置
├── 运行新版工具.bat           # 快捷启动脚本
├── codegraph.json            # CodeGraph 索引配置
├── README.md                 # 本文件
├── 审查报告.md                # 代码审查记录
└── 坐标用.xml                 # 坐标查询模板（可选）
```

---

## 技术栈

- **语言**: Python 3.12+
- **UI 框架**: Tkinter（标准库）
- **XML 生成**: `xml.etree.ElementTree`
- **打包工具**: PyInstaller 6.20+
- **外部依赖**: 无（仅用标准库）

---

## 相关仓库

| 仓库 | 说明 |
|------|------|
| [`navisworks-xml-tool`](https://github.com/T8899J/navisworks-xml-tool) | 本工具 — XML 生成 |
| [`navisworks-plugin`](https://github.com/T8899J/navisworks-plugin) | Navisworks 查找插件（C# .NET） |
