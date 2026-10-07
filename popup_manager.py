# popup_manager.py

from popups import SettingsPopup, SchedulePopup, CompletePopup, ViewPopup

class PopupManager:
    def __init__(self, parent, data_manager, refresh_callback):
        self.parent = parent
        self.dm = data_manager
        self.refresh_callback = refresh_callback

    def open_settings(self):
        """환경 설정 팝업을 엽니다."""
        win = SettingsPopup(self.parent, self.dm, self.refresh_callback)
        win.grab_set()

    def open_schedule_popup(self, req_no):
        """생산 일정 수립 팝업을 엽니다."""
        win = SchedulePopup(self.parent, self.dm, self.refresh_callback, req_no)
        win.grab_set()

    def open_complete_popup(self, req_no):
        """생산 완료 처리 팝업을 엽니다."""
        win = CompletePopup(self.parent, self.dm, self.refresh_callback, req_no)
        win.grab_set()

    def open_completed_view_popup(self, req_no):
        """완료 데이터 상세 조회 팝업을 엽니다."""
        win = ViewPopup(self.parent, self.dm, self.refresh_callback, req_no)
        win.grab_set()
