# 单枪项目 README

![Python](https://img.shields.io/badge/Python-3.12+-blue?logo=python)
![Tkinter](https://img.shields.io/badge/UI-Tkinter-green)
![Navisworks](https://img.shields.io/badge/Navisworks-Manage%202023-orange)

## 项目概述

这是一个围绕 Navisworks 检索流程搭建的单枪项目，当前由两部分组成：

1. `sqt_tool.py`
   负责把人工输入的查询值批量生成 Navisworks 可读取的 XML 查询文件。
2. `navisworks-plugin-work/`
   负责在 Navisworks Manage 2023 中读取 XML、执行搜索、选中对象、保留结构节点，并按需隐藏未选中对象。

当前工作重点已经从“只生成 XML”推进到“生成 XML + 在 Navisworks 内执行完整查找流程”。

## 当前进展

### 已完成

- Python 桌面工具已可稳定生成两类 XML：
  - 支架查询 XML
  - 坐标查询 XML
- XML 生成工具已补齐基础输入保护：
  - 最大 900 行输入限制
  - 单行最大 200 字符限制
  - XML 非法控制字符清理
- Navisworks 插件已具备完整 UI：
  - 搜索条件页
  - 选项页
  - 结果页
- 插件已支持：
  - 导入 XML 查询条件
  - 手动添加 / 删除 / 清空条件
  - 执行 XML 搜索
  - 将结果写入 Navisworks 当前选择
  - 导出搜索结果
- 插件已实现“搜索范围”机制：
  - 读取用户在选择树中提前选中的蓝色节点
  - 将其作为搜索范围使用
- 插件已实现动态结构保护逻辑：
  - 从当前搜索范围自动识别模型前缀
  - 自动推导对应的 `*-STR` 节点名称
  - 将该结构节点及其子节点纳入最终保留集合
- 插件已实现隐藏未选中对象：
  - 最终保留集合写入 `CurrentSelection`
  - 调用 Navisworks 内核选择反转与隐藏能力
- 插件已加入诊断日志能力：
  - 自动记录搜索范围
  - XML 条件数量
  - 选中数量
  - 最终保留集合数量
  - 隐藏执行情况
  - 异常明细

### 当前阶段

当前项目已经进入“可用版本联调”阶段，核心业务链路已跑通：

`输入查询值 -> 生成 XML -> 在 Navisworks 中执行搜索 -> 选中目标 -> 保留 STR -> 隐藏其他对象`

### 正在持续调整

- 搜索性能还在继续验证
- 不同模型前缀场景仍在持续回归测试
- 部分版本切换后需要重新编译和部署 DLL
- 文档和脚本路径说明正在同步整理

## 当前工作目录说明

```text
主函数/
├─ sqt_tool.py                    # Python XML 生成工具
├─ 运行新版工具.bat                # Python 工具启动脚本
├─ README.md                      # 当前说明文档
├─ 审查报告.md                     # 早期代码审查记录
├─ navisworks-plugin-work/        # 当前主开发目录
│  ├─ PluginEntry.cs              # 插件入口
│  ├─ SearchDialog.cs             # 主界面与搜索流程
│  ├─ ModelItemMatcher.cs         # Navisworks 搜索封装
│  ├─ XmlSearchParser.cs          # XML 解析
│  ├─ SelectionService.cs         # 选择写入
│  ├─ HideServiceFixed.cs         # 隐藏未选中对象
│  ├─ ProtectedKeepService.cs     # 结构节点保护
│  ├─ LogService.cs               # 诊断日志
│  ├─ build_2023.bat              # 编译脚本
│  ├─ install_2023.bat            # 安装脚本
│  └─ README.md                   # 插件说明
├─ build/                         # PyInstaller 构建目录
├─ dist/                          # Python 工具打包输出
└─ .packaging/                    # 打包依赖
```

## Python XML 工具

### 作用

把输入的编号、坐标或路径类查询值批量转换成 Navisworks 可直接读取的 XML 查询文件。

### 启动方式

直接运行：

```bash
python sqt_tool.py
```

或在 Windows 下双击：

```text
运行新版工具.bat
```

### 当前特点

- 使用 Tkinter 实现桌面界面
- 自动调用系统“另存为”窗口
- 记住上一次保存目录
- 可复用坐标查询模板文件

## Navisworks 插件

### 目标环境

- Navisworks Manage 2023
- .NET Framework 4.8
- Windows

### 当前插件能力

- 读取 XML 查询条件
- 支持 `equals` / `contains`
- 根据选择树当前蓝色选中节点确定搜索范围
- 自动识别模型前缀，如：
  - `TS-M12`
  - `TS-M14`
  - `TS-M25`
- 自动推导并保护对应的 `*-STR` 节点
- 支持两种执行模式：
  - 模式 A：仅查找并选中，不隐藏
  - 模式 B：查找并选中后，确认再隐藏未选中
- 自动生成诊断日志，便于排查“选中了但没隐藏”“隐藏过度”“搜索过慢”等问题

### 编译

```bash
navisworks-plugin-work\build_2023.bat
```

或直接调用 MSBuild：

```bash
MSBuild.exe navisworks-plugin-work\NavisworksPlugin.csproj /p:Configuration=Release /t:Rebuild /v:m
```

### 部署

插件 DLL 当前部署目录为：

```text
F:\Navisworks\Navisworks Manage 2023\Plugins\傑出品NavisworksPlugin\
```

典型文件包括：

```text
傑出品NavisworksPlugin.dll
傑出品NavisworksPlugin.plugin
```

如果 Navisworks 正在运行，DLL 可能被占用，部署会失败。此时需要先关闭 Navisworks 再覆盖。

## 诊断日志

当前插件支持自动输出诊断日志，优先写到 XML 同级目录。

文件名格式：

```text
<xml文件名>_诊断日志_yyyyMMdd_HHmmss.txt
```

日志会记录：

- 当前模型文件名
- XML 路径
- XML 条件数量
- 搜索范围数量
- 命中对象数量
- 结构保护节点匹配情况
- 写入 `CurrentSelection` 前后数量
- 隐藏执行方式
- 异常完整堆栈

## 当前已验证的业务规则

当前插件围绕以下目标工作：

- 用户先在选择树中框定蓝色搜索范围
- 插件只根据 XML 命中结果保留需要的对象
- 自动保留当前模型对应的 `*-STR` 结构节点
- 最终只显示：
  - 搜索范围内命中的对象
  - 当前模型对应的 `*-STR` 节点

## 已知注意事项

- 搜索性能与模型大小、XML 条件数量、搜索范围大小直接相关
- 某些版本切换后，部署目录中的 DLL 可能与工作目录源码不一致，发布前需要重新编译并覆盖
- 当前项目主要围绕 Navisworks Manage 2023 调试，不承诺兼容其他版本
- 部分旧文档和脚本仍保留历史命名，后续会逐步统一

## 下一步计划

- 继续稳定搜索性能
- 继续压缩版本切换时的回滚成本
- 继续补正文档和部署说明
- 在业务逻辑稳定后，再做更系统的代码清理与结构优化

## 相关文件

- [根目录审查报告](D:/副业/项目/主函数/审查报告.md)
- [插件说明](D:/副业/项目/主函数/navisworks-plugin-work/README.md)
- [Python 工具入口](D:/副业/项目/主函数/sqt_tool.py)

