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
