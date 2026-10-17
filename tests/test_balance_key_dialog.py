# -*- coding: utf-8 -*-
"""右键菜单「配置 API Key」入口及弹窗单例/接线契约测试。

覆盖：
1. 注册表声明（ACTION_LABELS, ACTION_ICONS, MENU_ACTIONS）；
2. 菜单可用性门控（依附 on_open_balance_key，无回调时不可用，有回调可用）；
3. add_balance_key 动作构建与点击触发；
4. AppShell.open_balance_key_dialog 单例与生命周期（非模态，WA_DeleteOnClose，销毁置空）；
5. 余额查询未配置 Key 时自动调用 open_balance_key_dialog 引导配置；
6. BalanceKeyDialog UI 交互（密码显示/隐藏切换、保存至 SecretStore 并刷新余额）。
"""
from __future__ import annotations

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from unittest.mock import MagicMock
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QLineEdit, QMenu, QWidget

from pet.balance_key_dialog import BalanceKeyDialog
from pet.context_menus import registry as registry_mod
from pet.context_menus.shared import add_balance_key
from pet.menu_layout import load_default_menu_layout

app = QApplication.instance() or QApplication([])


class _CfgStub:
    def get(self, key, default=None):
        return default


class _PetStub:
    def __init__(self, *, with_callback: bool = True):
        self.cfg = _CfgStub()
        self.calls = 0
        if with_callback:
            self.on_open_balance_key = self._open

    def _open(self):
        self.calls += 1


def test_registry_declares_balance_key_action():
    assert registry_mod.ACTION_LABELS["balance_key"] == "配置 API Key"
    assert registry_mod.ACTION_ICONS["balance_key"] == "key"
    assert "balance_key" in registry_mod.MENU_ACTIONS.ids

    def find_ids(nodes) -> list[str]:
        found = []
        for node in nodes:
            if node.get("type") == "action":
                found.append(str(node.get("id")))
            found.extend(find_ids(node.get("children", [])))
        return found

    assert "balance_key" in find_ids(load_default_menu_layout().get("nodes", []))


def test_balance_key_availability_gated_by_callback():
    actions = registry_mod.MENU_ACTIONS
    assert "balance_key" in actions.available_ids(_PetStub(with_callback=True))
    assert "balance_key" not in actions.available_ids(_PetStub(with_callback=False))


def test_add_balance_key_builds_action_and_triggers_callback():
    pet = _PetStub()
    menu = QMenu()
    try:
        action = add_balance_key(menu, pet, icons=True)
        assert action is not None
        assert action.text() == "配置 API Key"
        assert not action.icon().isNull()
        assert action.property("closeOnTrigger") is True
        action.trigger()
        assert pet.calls == 1
    finally:
        menu.close()
        app.processEvents()


def test_balance_key_dialog_ui_and_password_toggle(tmp_path, monkeypatch):
    from pet.app import PetApp
    from pet.config import Config

    cfg = Config(base=tmp_path)
    owner = PetApp(app, cfg)
    owner.win = QWidget()

    dialog = BalanceKeyDialog(owner)
    try:
        assert dialog.key_edit.echoMode() == QLineEdit.EchoMode.Password
        # 触发显示密码
        dialog._toggle_echo_mode()
        assert dialog.key_edit.echoMode() == QLineEdit.EchoMode.Normal
        # 触发隐藏密码
        dialog._toggle_echo_mode()
        assert dialog.key_edit.echoMode() == QLineEdit.EchoMode.Password
    finally:
        dialog.close()
        dialog.deleteLater()
        app.processEvents()


def test_balance_key_dialog_save_persists_to_store_and_refreshes_balance(tmp_path, monkeypatch):
    from pet.app import PetApp
    from pet.config import Config

    cfg = Config(base=tmp_path)
    owner = PetApp(app, cfg)
    owner.win = QWidget()
    balance_calls = []
    owner.show_balance = lambda: balance_calls.append(True)

    fake_store = {}
    class FakeSecretStore:
        available = True
        def get(self, ref): return fake_store.get(ref, "")
        def set(self, ref, val):
            fake_store[ref] = val
            return True

    monkeypatch.setattr("pet.chat.models.SecretStore", FakeSecretStore)

    dialog = BalanceKeyDialog(owner)
    try:
        dialog.key_edit.setText("  sk-test-key-12345  ")
        dialog._on_save()

        # 验证前后空白被 strip 并写入 SecretStore
        settings = owner.config.chat_settings()
        prov = settings.active_config
        assert prov.api_key_ref == f"provider/{prov.provider_id}"
        assert fake_store[prov.api_key_ref] == "sk-test-key-12345"
        # 验证调用了 show_balance 刷新
        app.processEvents()
        assert len(balance_calls) == 1
    finally:
        dialog.close()
        dialog.deleteLater()
        app.processEvents()


def test_app_shell_balance_key_dialog_singleton_lifecycle(tmp_path):
    from pet.app import PetApp
    from pet.config import Config

    cfg = Config(base=tmp_path)
    owner = PetApp(app, cfg)
    owner.win = QWidget()

    assert owner.balance_key_dialog is None
    owner.open_balance_key_dialog()
    d1 = owner.balance_key_dialog
    assert d1 is not None
    assert d1.isVisible()

    # 重复打开应复用同一实例
    owner.open_balance_key_dialog()
    assert owner.balance_key_dialog is d1

    # 关闭窗口释放单例
    d1.close()
    app.processEvents()
    assert owner.balance_key_dialog is None


def test_show_balance_triggers_dialog_when_api_key_empty(tmp_path, monkeypatch):
    from pet.app import PetApp
    from pet.config import Config

    cfg = Config(base=tmp_path)
    owner = PetApp(app, cfg)
    bubbles = []
    owner.win = type("Win", (), {
        "isVisible": lambda self: True,
        "show_bubble": lambda self, text, **kw: bubbles.append(text),
    })()

    opened = []
    owner.open_balance_key_dialog = lambda: opened.append(True)

    # 模拟 _balance_worker 抛出未配置 API Key 错误并通过 bridge.done 回传
    from pet.app import _BalanceBridge
    bridge = _BalanceBridge(owner.win, owner=owner)
    bridge.done.emit(False, "余额查询失败：未配置 API Key")
    app.processEvents()

    assert opened == [True]
    assert any("未配置 API Key" in b for b in bubbles)
