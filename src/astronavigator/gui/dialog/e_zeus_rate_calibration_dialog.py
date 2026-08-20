from __future__ import annotations

from datetime import datetime

from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QLabel,
    QLineEdit,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from astronavigator.mount.e_zeus.e_zeus2 import EZeus2
from astronavigator.tracking.e_zeus_rate_calibrator import (
    EZeusRateCalibrator,
)
from astronavigator.tracking.e_zeus_rate_profile import (
    EZeusRateProfile,
)


class EZeusRateCalibrationDialog(QDialog):
    def __init__(
        self,
        mount: EZeus2,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)

        self.setWindowTitle(
            "E-ZEUS II 自動レート測定"
        )
        self.resize(520, 420)

        self._mount = mount
        self._profile: EZeusRateProfile | None = None
        self._calibrator: EZeusRateCalibrator | None = None

        self._name = QLineEdit(
            "E-ZEUS II 自動校正 "
            + datetime.now().strftime("%Y-%m-%d %H:%M")
        )

        self._status = QLabel("測定を開始できます。")
        self._status.setWordWrap(True)

        self._progress = QProgressBar()
        self._progress.setValue(0)

        self._log = QTextEdit()
        self._log.setReadOnly(True)

        self._start_button = QPushButton("自動測定を開始")
        self._start_button.clicked.connect(
            self._start_calibration
        )

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Cancel
        )
        buttons.rejected.connect(self._cancel)

        warning = QLabel(
            "測定中はRA・Decの両軸が短時間動きます。\n"
            "所要時間は約1分です。鏡筒・架台・"
            "ケーブルが衝突しないことを確認してください。"
        )
        warning.setWordWrap(True)

        layout = QVBoxLayout(self)
        layout.addWidget(warning)
        layout.addWidget(QLabel("プロファイル名"))
        layout.addWidget(self._name)
        layout.addWidget(self._status)
        layout.addWidget(self._progress)
        layout.addWidget(self._log)
        layout.addWidget(self._start_button)
        layout.addWidget(buttons)

    @property
    def profile(self) -> EZeusRateProfile:
        if self._profile is None:
            raise RuntimeError(
                "Calibration has not completed."
            )
        return self._profile

    def _start_calibration(self) -> None:
        name = self._name.text().strip()
        if not name:
            QMessageBox.warning(
                self,
                "入力エラー",
                "プロファイル名を入力してください。",
            )
            return

        result = QMessageBox.warning(
            self,
            "実機を動かします",
            "E-ZEUS IIの全速度帯を短時間駆動します。\n"
            "周囲の安全を確認しましたか？",
            QMessageBox.StandardButton.Yes
            | QMessageBox.StandardButton.Cancel,
            QMessageBox.StandardButton.Cancel,
        )

        if result is not QMessageBox.StandardButton.Yes:
            return

        self._calibrator = EZeusRateCalibrator(
            self._mount,
            name,
            self,
        )

        self._progress.setRange(
            0,
            self._calibrator.total_steps,
        )

        self._calibrator.progress.connect(
            self._on_progress
        )
        self._calibrator.measurement_completed.connect(
            self._log.append
        )
        self._calibrator.finished.connect(
            self._on_finished
        )
        self._calibrator.failed.connect(
            self._on_failed
        )
        self._calibrator.cancelled.connect(
            self._on_cancelled
        )

        self._start_button.setEnabled(False)
        self._name.setEnabled(False)

        try:
            self._calibrator.start()
        except Exception as error:
            self._on_failed(str(error))

    def _on_progress(
        self,
        current: int,
        total: int,
        message: str,
    ) -> None:
        self._progress.setRange(0, total)
        self._progress.setValue(current)
        self._status.setText(message)

    def _on_finished(
        self,
        profile: EZeusRateProfile,
    ) -> None:
        self._profile = profile
        self._status.setText("自動測定が完了しました。")
        self._progress.setValue(
            self._progress.maximum()
        )

        QMessageBox.information(
            self,
            "測定完了",
            "レートプロファイルを作成しました。",
        )
        self.accept()

    def _on_failed(self, message: str) -> None:
        self._start_button.setEnabled(True)
        self._name.setEnabled(True)
        self._status.setText("測定に失敗しました。")

        QMessageBox.critical(
            self,
            "自動測定エラー",
            message,
        )

    def _cancel(self) -> None:
        if (
            self._calibrator is not None
            and self._calibrator.is_active
        ):
            self._calibrator.cancel()
            return

        self.reject()

    def _on_cancelled(self) -> None:
        self._status.setText(
            "測定を中止し、架台を停止しました。"
        )
        self.reject()