# -*- coding: utf-8 -*-
"""dsh-pet 独立桌宠（不依赖 DSH 运行时的 Windows 桌面宠物）。"""

import os
import sys

if sys.platform == "win32":
    _sys32 = os.path.join(os.environ.get("SystemRoot", r"C:\Windows"), "System32")
    if os.path.isdir(_sys32):
        try:
            os.add_dll_directory(_sys32)
        except (AttributeError, OSError):
            pass
        try:
            import ctypes
            ctypes.WinDLL(os.path.join(_sys32, "icuuc.dll"))
        except Exception:
            pass

# 版本号唯一来源：updater（更新检测基准）与安装包版本均从这里读取。
__version__ = '4.3.1'
