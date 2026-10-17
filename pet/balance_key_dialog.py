# -*- coding: utf-8 -*-
"""快速配置 DeepSeek API Key 弹窗。

方便查看 DeepSeek 余额及 AI 对话，通过轻量级非模态弹窗快速配置 API Key：
- 输入框支持密码掩码（••••）与明文切换（eye/hide 矢量图标）；
- 自动 .strip() 去除首尾空格换行，防止粘贴格式污染；
- 提供 DeepSeek 开放平台 API Keys 页面快速直达链接；
- 提供「测试连接」按钮，优先免费验证 /user/balance 接口连通性（带余额反馈），
  连通失败自动回退测试 /v1/chat/completions 验证凭据有效性；
- 凭据优先加密保存到系统钥匙串（SecretStore / keyring 服务名 dsh-pet-standalone），
  不可用时回退到内存并给出明确提示；
- 保存时自动失效余额缓存并触发即时刷新，立刻在桌宠气泡与灵动岛展示最新余额；
- UI 规范严格遵循 .agents/skills/desktop-pet-ui-style/（12px 卡片圆角、7px 按钮圆角、
  13px 正文 / 12px 提示、强调色 #0a84ff、深浅主题自适应调色板）。
"""
from __future__ import annotations

import logging
import threading

import shiboken6
from PySide6.QtCore import QObject, Qt, QTimer, Signal
from PySide6.QtGui import QPalette
from PySide6.QtWidgets import (
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from .context_menus.icons import vector_widget_icon

logger = logging.getLogger(__name__)


def _stylesheet(widget: QWidget) -> str:
    """令牌：与待办面板及网络信息弹窗同一套，随明暗主题自适应切换。"""
    dark = widget.palette().color(QPalette.ColorRole.Window).lightness() < 128
    if dark:
        window, card, border, divider = "#202024", "#2a2a30", "#3a3a42", "#33333a"
        text, hint, hover = "#e0e0e6", "#9a9aa3", "#303036"
        input_bg = "#26262b"
    else:
        window, card, border, divider = "#fcfcfd", "#ffffff", "#e2e4e8", "#eceef1"
        text, hint, hover = "#252525", "#777777", "#f4f5f6"
        input_bg = "#ffffff"
    accent = "#0a84ff"
    return f"""
    QDialog#balanceKeyDialog, QWidget#balanceKeyBody {{
        background: {window};
        color: {text};
        font-size: 13px;
    }}
    QLabel#balanceKeyTitle {{
        font-size: 15px;
        font-weight: 600;
        color: {text};
        background: transparent;
    }}
    QLabel[role="label"] {{
        color: {hint};
        font-size: 12px;
    }}
    QLabel[role="value"] {{
        color: {text};
        font-size: 13px;
    }}
    QLabel[role="hint"] {{
        color: {hint};
        font-size: 12px;
    }}
    QFrame#balanceKeyCard {{
        background: {card};
        border: 1px solid {border};
        border-radius: 12px;
    }}
    QFrame[divider="true"] {{
        background: {divider};
        border: none;
        max-height: 1px;
    }}
    QLineEdit {{
        background: {input_bg};
        color: {text};
        border: 1px solid {border};
        border-radius: 7px;
        min-height: 28px;
        padding: 2px 8px;
        font-size: 13px;
    }}
    QLineEdit:focus {{
        border: 1px solid {accent};
    }}
    QPushButton {{
        background: {card};
        color: {text};
        border: 1px solid {border};
        border-radius: 7px;
        min-height: 26px;
        padding: 3px 14px;
        font-size: 13px;
    }}
    QPushButton:hover {{ background: {hover}; }}
    QPushButton:focus {{ border: 1px solid {accent}; }}
    QPushButton:disabled {{ color: {hint}; border-color: {divider}; }}
    QPushButton[accent="true"] {{
        background: {accent};
        color: #ffffff;
        border: 1px solid {accent};
    }}
    QPushButton[accent="true"]:hover {{ background: {accent}; }}
    QPushButton[accent="true"]:disabled {{
        background: {divider};
        color: {hint};
        border-color: {divider};
    }}
    """


class _TestBridge(QObject):
    """跨线程测试结果回传 GUI 线程。"""

    test_done = Signal(bool, str)


class BalanceKeyDialog(QDialog):
    """轻量级非模态弹窗：快速配置 DeepSeek API Key。"""

    def __init__(self, app, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._app = app
        self._bridge = _TestBridge()
        self._bridge.test_done.connect(self._on_test_done, Qt.ConnectionType.QueuedConnection)
        self._testing = False

        self.setWindowTitle("配置 API Key")
        self.setObjectName("balanceKeyDialog")
        self.setMinimumWidth(380)
        self.setStyleSheet(_stylesheet(self))
        self._build_ui()
        self._load_current_key()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(12)

        title = QLabel("配置 API Key", self)
        title.setObjectName("balanceKeyTitle")
        layout.addWidget(title)

        subtitle = QLabel("用于 DeepSeek AI 对话及账户余额实时查询", self)
        subtitle.setProperty("role", "hint")
        layout.addWidget(subtitle)

        self.card = QFrame(self)
        self.card.setObjectName("balanceKeyCard")
        card_layout = QVBoxLayout(self.card)
        card_layout.setContentsMargins(14, 12, 14, 12)
        card_layout.setSpacing(8)

        provider_box = QHBoxLayout()
        prov_label = QLabel("服务商", self.card)
        prov_label.setProperty("role", "label")
        self.prov_value = QLabel("", self.card)
        self.prov_value.setProperty("role", "value")
        provider_box.addWidget(prov_label)
        provider_box.addStretch(1)
        provider_box.addWidget(self.prov_value)
        card_layout.addLayout(provider_box)

        div1 = QFrame(self.card)
        div1.setProperty("divider", True)
        card_layout.addWidget(div1)

        key_label = QLabel("API Key", self.card)
        key_label.setProperty("role", "label")
        card_layout.addWidget(key_label)

        self.key_edit = QLineEdit(self.card)
        self.key_edit.setPlaceholderText("请输入 DeepSeek API Key (sk-...)")
        self.key_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.key_edit.setClearButtonEnabled(True)
        self.key_edit.returnPressed.connect(self._on_save)

        self._toggle_action = self.key_edit.addAction(
            vector_widget_icon(self.key_edit, "hide", 16),
            QLineEdit.ActionPosition.TrailingPosition,
        )
        self._toggle_action.setToolTip("显示/隐藏 API Key")
        self._toggle_action.triggered.connect(self._toggle_echo_mode)
        card_layout.addWidget(self.key_edit)

        link_label = QLabel(
            '获取 API Key：<a href="https://platform.deepseek.com/api_keys" '
            'style="color: #0a84ff; text-decoration: none;">DeepSeek 开放平台</a>',
            self.card,
        )
        link_label.setProperty("role", "hint")
        link_label.setOpenExternalLinks(True)
        card_layout.addWidget(link_label)

        div2 = QFrame(self.card)
        div2.setProperty("divider", True)
        card_layout.addWidget(div2)

        self.storage_hint = QLabel("", self.card)
        self.storage_hint.setProperty("role", "hint")
        card_layout.addWidget(self.storage_hint)

        layout.addWidget(self.card)

        self.status_label = QLabel("", self)
        self.status_label.setObjectName("balanceKeyStatus")
        self.status_label.setWordWrap(True)
        layout.addWidget(self.status_label)

        buttons = QHBoxLayout()
        self.test_btn = QPushButton("测试连接", self)
        self.test_btn.clicked.connect(self._run_test)
        buttons.addWidget(self.test_btn)
        buttons.addStretch(1)

        self.cancel_btn = QPushButton("取消", self)
        self.cancel_btn.clicked.connect(self.reject)
        buttons.addWidget(self.cancel_btn)

        self.save_btn = QPushButton("保存", self)
        self.save_btn.setProperty("accent", True)
        self.save_btn.clicked.connect(self._on_save)
        buttons.addWidget(self.save_btn)

        layout.addLayout(buttons)

    def _load_current_key(self) -> None:
        try:
            settings = self._app.config.chat_settings()
            provider = settings.active_config
            self.prov_value.setText(f"{provider.name} ({provider.base_url})")
            current_key = self._app.config.resolve_api_key(provider)
            if current_key:
                self.key_edit.setText(current_key)
        except Exception:
            self.prov_value.setText("DeepSeek (https://api.deepseek.com)")

        try:
            from .chat.models import SecretStore

            keyring_ok = SecretStore().available
        except Exception:
            keyring_ok = False

        if keyring_ok:
            self.storage_hint.setText("✓ 系统安全存储可用（凭据将加密保存在系统钥匙串）")
            self.storage_hint.setStyleSheet("")
        else:
            self.storage_hint.setText("⚠ 系统安全存储不可用（Key 仅在本次运行内存中有效）")
            self.storage_hint.setStyleSheet("color: #d97706;")

    def _toggle_echo_mode(self) -> None:
        if self.key_edit.echoMode() == QLineEdit.EchoMode.Password:
            self.key_edit.setEchoMode(QLineEdit.EchoMode.Normal)
            self._toggle_action.setIcon(vector_widget_icon(self.key_edit, "eye", 16))
            self._toggle_action.setToolTip("隐藏 API Key")
        else:
            self.key_edit.setEchoMode(QLineEdit.EchoMode.Password)
            self._toggle_action.setIcon(vector_widget_icon(self.key_edit, "hide", 16))
            self._toggle_action.setToolTip("显示 API Key")

    def _run_test(self) -> None:
        if self._testing:
            return
        key = self.key_edit.text().strip()
        if not key:
            self.status_label.setText("请先输入 API Key")
            self.status_label.setStyleSheet("color: #dc2626;")
            return

        self._testing = True
        self.test_btn.setEnabled(False)
        self.test_btn.setText("测试中…")
        self.status_label.setText("正在测试连接…")
        self.status_label.setStyleSheet("color: #777777;")

        settings = self._app.config.chat_settings()
        provider = settings.active_config
        base_url = provider.base_url or "https://api.deepseek.com"
        verify_ssl = provider.verify_ssl

        def worker() -> None:
            try:
                from . import balance as balance_mod

                if "deepseek.com" in base_url.lower():
                    try:
                        info = balance_mod.fetch_balance(
                            base_url, key, timeout=10.0, verify_ssl=verify_ssl
                        )
                        msg = f"连接成功！当前账户总可用：¥{info.total_balance}"
                        self._bridge.test_done.emit(True, msg)
                        return
                    except Exception as b_exc:
                        logger.debug("余额接口测试异常，回退聊天端点: %s", b_exc)

                from .chat.models import ProviderConfig
                from .chat.providers import test_connection

                prov = ProviderConfig(
                    provider_id=provider.provider_id,
                    name=provider.name,
                    base_url=base_url,
                    chat_path=provider.chat_path,
                    model=provider.model,
                    api_key_ref=provider.api_key_ref,
                    api_key=key,
                    timeout=10.0,
                    verify_ssl=verify_ssl,
                )
                ok, msg = test_connection(prov, timeout=10.0)
                self._bridge.test_done.emit(ok, msg)
            except Exception as exc:
                self._bridge.test_done.emit(False, f"测试失败：{exc}")

        threading.Thread(target=worker, daemon=True, name="pet-balance-key-test").start()

    def _on_test_done(self, ok: bool, message: str) -> None:
        if not shiboken6.isValid(self):
            return
        self._testing = False
        self.test_btn.setEnabled(True)
        self.test_btn.setText("测试连接")
        self.status_label.setText(message)
        self.status_label.setStyleSheet("color: #16a34a;" if ok else "color: #dc2626;")

    def _on_save(self) -> None:
        new_key = self.key_edit.text().strip()
        settings = self._app.config.chat_settings()
        provider = settings.active_config
        ref = provider.api_key_ref or f"provider/{provider.provider_id}"
        provider.api_key_ref = ref

        from .chat.models import SecretStore

        store = SecretStore()

        if new_key:
            persisted = store.set(ref, new_key)
            if persisted:
                provider.api_key = ""
            else:
                provider.api_key = new_key
                QMessageBox.warning(
                    self,
                    "安全存储不可用",
                    "无法使用系统安全存储，Key 仅本次运行保留，重启需重输。",
                )
        else:
            store.set(ref, "")
            provider.api_key = ""

        self._app.config.set_chat_settings(settings)
        self._app.config.save()

        # 清除余额缓存（内存与磁盘文件）
        self._app._balance_cache = None
        cache_path = getattr(self._app, "_balance_cache_path", None)
        if cache_path is not None:
            try:
                if cache_path.exists():
                    cache_path.unlink()
            except Exception:
                pass

        # 若保存了有效 Key，触发即时刷新余额
        if new_key and callable(getattr(self._app, "show_balance", None)):
            QTimer.singleShot(0, lambda: self._app.show_balance())

        self.accept()
