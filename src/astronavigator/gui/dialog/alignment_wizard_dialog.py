from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from astronavigator.mount.slew_path import PierSide
from astronavigator.sky.coordinate_format import DeclinationFormat, RightAscensionFormat


if TYPE_CHECKING:
    from astronavigator.application.application import Application


class AlignmentWizardDialog(QDialog):
    """SynScan Proの「Align with Sync」を利用したアライメント支援ダイアログ。

    SynScan App Protocolにはアライメント専用のコマンドは存在せず、
    ASCOMのSyncToCoordinates（同期）を送ることでアライメント星を
    1点追加したことになる。何スター目かという制限や進行状況の管理は
    ソフト側では持たず、ユーザーが好きな対象を好きなだけ導入・同期
    できるようにする。

    SynScan Pro側で「Alignment > Align with Sync」メニューを開いた
    状態でないと、送ったsyncはアライメント星の追加ではなく既存モデルへの
    補正サンプル追加として扱われてしまうため、ウィザード開始時に案内する。

    なお、個々のアライメント星（sync点）を後から選んで削除する機能は
    実装していない。アライメントモデルはSynScan Proアプリ内部にのみ
    保持され、ASCOM/SynScan App Protocol経由では個別の点へアクセスする
    手段が提供されていないため。
    """

    def __init__(self, application: Application, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._application = application

        self.setWindowTitle("アライメント")
        self.setMinimumWidth(480)

        layout = QVBoxLayout(self)

        notice = QLabel(
            "SynScan Proアプリで「Alignment」→「Align with Sync」を開いた状態にしてから"
            "作業してください。このメニューを開いていないと、ここで行う同期が"
            "アライメント星の追加として扱われません。\n\n"
            "手順: 対象を選択 → 「この対象へ導入」→ 望遠鏡の実視野で対象を中心に導入 →"
            "「この位置で同期」。星の数に制限はなく、好きなだけ繰り返せます。\n\n"
            "※ 個別のアライメント星を後から削除する機能はありません"
            "（SynScan Pro側にのみモデルが保持され、外部から個々の点を操作する手段がないため）。"
            "やり直したい場合はSynScan Pro側でアライメントをリセットしてください。"
        )
        notice.setWordWrap(True)
        layout.addWidget(notice)

        self._status_label = QLabel("-")
        layout.addWidget(self._status_label)

        self._history_list = QListWidget()
        self._history_list.setToolTip("このセッション中に同期した対象の記録（表示のみ、削除はできません）")
        layout.addWidget(self._history_list)

        button_layout = QHBoxLayout()
        self._goto_button = QPushButton("この対象へ導入")
        self._sync_button = QPushButton("この位置で同期")
        button_layout.addWidget(self._goto_button)
        button_layout.addWidget(self._sync_button)
        layout.addLayout(button_layout)

        self._goto_button.clicked.connect(self._goto_selected)
        self._sync_button.clicked.connect(self._sync_selected)

        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        button_box.rejected.connect(self.reject)
        button_box.accepted.connect(self.accept)
        button_box.button(QDialogButtonBox.StandardButton.Close).clicked.connect(self.accept)
        layout.addWidget(button_box)

        self._update_status()

    def _goto_selected(self) -> None:
        scene = self._application.scene
        selected = scene.selection.selected
        mount = scene.mount

        if selected is None or mount is None:
            msg = "導入する対象が選択されていません。" if selected is None else "マウントが接続されていません。"
            QMessageBox.warning(self, "導入エラー", msg)
            return

        try:
            position = selected.get_position(time=scene.time, observer=scene.observer)
            mount.slew_to(position)
            self._status_label.setText(f"{selected.name} へ導入中です。実視野で中心に合わせてから同期してください。")
        except Exception as e:
            QMessageBox.critical(self, "導入エラー", f"マウントの導入に失敗しました: {e}")

    def _sync_selected(self) -> None:
        scene = self._application.scene
        selected = scene.selection.selected
        mount = scene.mount

        if selected is None or mount is None:
            msg = "同期する対象が選択されていません。" if selected is None else "マウントが接続されていません。"
            QMessageBox.warning(self, "同期エラー", msg)
            return

        try:
            position = selected.get_position(time=scene.time, observer=scene.observer)

            pier_side: PierSide | None = None
            if mount.requires_pier_side_for_sync:
                from astronavigator.gui.dialog.mount_sync_dialog import MountSyncDialog

                ra_text = position.get_ra(RightAscensionFormat.HMS)
                dec_text = position.get_dec(DeclinationFormat.DMS)
                dialog = MountSyncDialog(selected.name, ra_text, dec_text, self)
                if dialog.exec() != MountSyncDialog.DialogCode.Accepted:
                    return
                pier_side = dialog.selected_pier_side
                if pier_side is None:
                    return

            self._application.scene_controller.sync_mount(position, pier_side=pier_side)

            ra_text = position.get_ra(RightAscensionFormat.HMS)
            dec_text = position.get_dec(DeclinationFormat.DMS)
            self._history_list.addItem(f"{selected.name}  (RA: {ra_text}, Dec: {dec_text})")
            self._status_label.setText(f"{selected.name} で同期しました。続けて他の対象を導入・同期できます。")
        except Exception as e:
            QMessageBox.critical(self, "同期エラー", f"マウントの同期に失敗しました: {e}")

    def _update_status(self) -> None:
        mount = self._application.scene.mount
        if mount is None:
            self._status_label.setText("マウントが接続されていません。")
            self._goto_button.setEnabled(False)
            self._sync_button.setEnabled(False)
            return

        self._status_label.setText("対象を選択し、導入してから同期してください。")
