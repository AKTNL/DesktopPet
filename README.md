# DesktopPet

基于 **Python + PySide6** 的独立桌面宠物。

本项目基于开源项目 [dsh-pet-indesktop](https://github.com/MerZlin/dsh-pet-indesktop)（MIT 许可证）进行定制与二次开发。原项目完整的设计文档与功能说明已整理归档至 [README_UPSTREAM.md](README_UPSTREAM.md)。

---

## 快速启动

### 1. 环境准备
推荐使用 Python 3.10 ~ 3.12 环境。

```bash
pip install -r requirements.txt
```

### 2. 运行桌宠
- **方式一（命令行）**：
  ```bash
  python -m pet
  ```
- **方式二（Windows 双击快捷运行）**：
  双击根目录下的 `run.bat` 即可（无控制台黑框后台启动）。

---

## 服务联动与自启机制

- 设置中另有「随桌宠启动 dsh 服务」开关与「自启目标」（只影响自启这一路，菜单点哪项就起哪项）：开启后桌宠启动即按目标拉起——目标是 dsh web 时后台静默起服务（不开浏览器、不弹窗口），目标是桌面端界面时直接打开应用；**自启还要求同时开着 DSH 联动**（联动关着时 dsh web 没有消费者，不会拉起）；**关闭开关只是不再自动拉起**，已经在跑的 dsh web 要等桌宠退出或关闭 DSH 联动时才收口（唯一例外：在桌宠拉起探测期间关掉开关，那一次刚拉起的实例会被立刻收掉）；非 Windows 上「自启目标」里的桌面端项置灰并写明原因（暂不支持 ≠ 永远不支持）。

---

## 项目结构

```text
DesktopPet/
├── pet/                   # 桌宠核心源码（窗口穿透、动画引擎、状态机、设置界面等）
├── assets/                # 静态资产
│   ├── characters/        # 宠物角色素材（含动作视频/序列帧及配置文件）
│   ├── sounds/            # 音效文件
│   └── icon.ico           # 应用图标
├── resources/             # 运行期支持模型与工具库
├── docs/                  # 开发与设计文档
├── packaging/             # 打包配置（PyInstaller / Inno Setup）
├── run.bat                # Windows 一键启动脚本
├── requirements.txt       # Python 依赖清单
├── LICENSE                # MIT 开源许可证
├── THIRD_PARTY_NOTICES.md # 第三方开源组件声明
└── README_UPSTREAM.md     # 原项目完整技术与配置参考手册
```

---

## 开源许可与致谢

- 本项目代码遵循 [MIT 许可证](LICENSE)。
- 核心框架基于 [MerZlin/dsh-pet-indesktop](https://github.com/MerZlin/dsh-pet-indesktop)，感谢原作者及社区贡献者。
- 引用的第三方库及素材声明参见 [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md)。
