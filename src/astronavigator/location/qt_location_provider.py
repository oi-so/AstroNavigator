from __future__ import annotations

import math
import sys

from PySide6.QtCore import QCoreApplication, QLocationPermission, QObject, QPermission, Qt
from PySide6.QtPositioning import QGeoPositionInfo, QGeoPositionInfoSource

from astronavigator.location.location_provider import GeographicLocation, LocationCallback, LocationErrorCallback


LOCATION_TIMEOUT_MS = 10000

def can_use_qt_permission_api() -> bool:
    if sys.platform != "darwin":
        return True

    return "__compiled__" in globals()


class QtLocationProvider(QObject):
    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._source = QGeoPositionInfoSource.createDefaultSource(self)
        self._on_location: LocationCallback | None = None
        self._on_error: LocationErrorCallback | None = None

        if not can_use_qt_permission_api():
            return

        if self._source is not None:
            self._source.setPreferredPositioningMethods(
                QGeoPositionInfoSource.PositioningMethod.AllPositioningMethods
            )
            self._source.positionUpdated.connect(self._handle_position_updated)
            self._source.errorOccurred.connect(self._handle_error_occurred)


    def request_location(self, on_location: LocationCallback, on_error: LocationErrorCallback) -> None:
        self._on_location = on_location
        self._on_error = on_error

        if not can_use_qt_permission_api():
            self._finish_with_error("macOSでuvからは位置情報を使えません")

        application = QCoreApplication.instance()
        if application is None:
            self._finish_with_error("アプリケーションが起動していないので、現在地を取得できません")
            return

        if not can_use_qt_permission_api():
            self._request_source_update()
            return

        permission = QLocationPermission()
        permission.setAccuracy(QLocationPermission.Accuracy.Precise)
        permission.setAvailability(QLocationPermission.Availability.WhenInUse)

        status = application.checkPermission(permission)
        if status == Qt.PermissionStatus.Undetermined:
            application.requestPermission(permission, self, self._handle_permission_result)
            return
        if status == Qt.PermissionStatus.Denied:
            self._finish_with_error("位置情報の使用が許可されていません。設定アプリから位置情報を利用を許可して下さい。")
            return

        self._request_source_update()

    def _handle_permission_result(self, permission: QPermission) -> None:
        if permission.status() == Qt.PermissionStatus.Granted:
            self._request_source_update()
        else:
            self._finish_with_error("位置情報の使用が許可されていません。設定アプリから位置情報を利用を許可して下さい。")

    def _request_source_update(self) -> None:
        if self._source is None:
            self._finish_with_error("位置情報の取得に対応していない端末です")
            return

        self._source.requestUpdate(timeout=LOCATION_TIMEOUT_MS)

    def _handle_position_updated(self, info: QGeoPositionInfo) -> None:
        coordinate = info.coordinate()
        if not coordinate.isValid():
            self._finish_with_error("位置情報の取得に失敗しました")
            return

        altitude = coordinate.altitude()
        elevation = altitude if math.isfinite(altitude) else None

        callback = self._on_location
        self._clear_callbacks()
        if callback is not None:
            callback(GeographicLocation(coordinate.latitude(), coordinate.longitude(), elevation))


    def _handle_error_occurred(self, error: QGeoPositionInfoSource.Error) -> None:
        error_messages = {
            QGeoPositionInfoSource.Error.AccessError: "位置情報の使用が許可されていません。設定アプリから位置情報を利用を許可して下さい。",
            QGeoPositionInfoSource.Error.ClosedError: "位置情報サービスが停止しています。設定アプリから位置情報サービスを有効にして下さい。",
            QGeoPositionInfoSource.Error.UnknownSourceError: "位置情報の取得に失敗しました",
            QGeoPositionInfoSource.Error.UpdateTimeoutError: "位置情報の取得に失敗しました",
        }
        self._finish_with_error(error_messages.get(error, "位置情報の取得に失敗しました"))

    def _finish_with_error(self, message: str) -> None:
        callback = self._on_error
        self._clear_callbacks()
        if callback is not None:
            callback(message)

    def _clear_callbacks(self) -> None:
        self._on_location = None
        self._on_error = None