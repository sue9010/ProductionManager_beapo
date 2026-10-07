import tkinter as tk
from tkinter import messagebox

import customtkinter as ctk

try:
    from tkinterdnd2 import TkinterDnD
    DND_AVAILABLE = True
except ImportError:
    DND_AVAILABLE = False
    print("⚠️ tkinterdnd2 라이브러리가 설치되지 않았습니다. 드래그 앤 드롭 기능이 제한됩니다.")

from config import Config
from data_manager import DataManager
from popup_manager import PopupManager
from styles import COLORS, FONT_FAMILY, FONTS
from views.dashboard import DashboardView
from views.table_view import TableView

if DND_AVAILABLE:
    class BaseApp(ctk.CTk, TkinterDnD.DnDWrapper):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.TkdndVersion = TkinterDnD._require(self)
else:
    class BaseApp(ctk.CTk):
        pass

class COXProductionManager(BaseApp):
    def __init__(self):
        super().__init__()

        self.dm = DataManager()

        self.title(f"COX Production Manager - v{Config.APP_VERSION}")
        self.geometry("1650x900")
        
        ctk.set_appearance_mode(self.dm.current_theme)
        ctk.set_default_color_theme("dark-blue")
        
        # 종료 이벤트 프로토콜 설정
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

        self.pm = PopupManager(self, self.dm, self.refresh_ui)

        self.current_view = None
        self.refresh_timer = None # [수정] 타이머 ID 저장을 위한 변수

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.create_sidebar()
        self.create_content_area()
        
        self.bind("<Button-1>", self.handle_global_click)

        self.load_data_initial()
        self.show_dashboard_view()
        
        # [신규] 자동 새로고침 루프 시작 (5초마다 체크)
        self.start_auto_refresh_loop()

    # [신규] 외부 데이터 변경 감지 루프
    def start_auto_refresh_loop(self):
        try:
            # 창이 이미 닫혔다면 루프 중단
            if not self.winfo_exists():
                return

            # 외부에서 파일이 변경되었는지 확인
            if self.dm.check_for_external_changes():
                # 변경되었다면 조용히 데이터 로드 및 UI 갱신
                success, _ = self.dm.load_data()
                if success:
                    self.refresh_ui()
        except Exception as e:
            print(f"Auto-refresh error: {e}")
            
        # [핵심 수정] 5000ms(5초) 후에 다시 실행하며 타이머 ID 저장
        self.refresh_timer = self.after(5000, self.start_auto_refresh_loop)

    def create_sidebar(self):
        self.sidebar_frame = ctk.CTkFrame(self, width=220, corner_radius=0, fg_color=COLORS["bg_dark"])
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        self.sidebar_frame.grid_propagate(False)

        self.logo_label = ctk.CTkLabel(self.sidebar_frame, text="Production Manager", font=("Emoji", 24, "bold"), text_color=COLORS["primary"])
        self.logo_label.pack(pady=(30, 20), padx=20, anchor="w")
        
        self.logo_label.bind("<Button-1>", lambda e: self.show_dashboard_view())
        self.logo_label.bind("<Enter>", lambda e: self.logo_label.configure(cursor="hand2"))
        self.logo_label.bind("<Leave>", lambda e: self.logo_label.configure(cursor=""))
        
        self.nav_buttons = {}
        btn_data = [
            ("🏠  대시보드", self.show_dashboard_view),
            ("📊  테이블 뷰", self.show_table_view),
        ]

        for text, cmd in btn_data:
            btn = ctk.CTkButton(
                self.sidebar_frame, text=text, command=cmd,
                height=45, anchor="w", fg_color="transparent", 
                text_color=COLORS["text_dim"], hover_color=COLORS["bg_medium"], font=FONTS["header"]
            )
            btn.pack(fill="x", padx=10, pady=5)
            self.nav_buttons[text] = btn

        ctk.CTkFrame(self.sidebar_frame, height=1, fg_color=COLORS["border"]).pack(fill="x", pady=20, padx=10, side="bottom")
        ctk.CTkButton(self.sidebar_frame, text="⚙️  설정", command=self.pm.open_settings, height=40, anchor="w", fg_color="transparent", text_color=COLORS["text_dim"], hover_color=COLORS["bg_medium"], font=FONTS["header"]).pack(fill="x", padx=10, pady=5, side="bottom")
        ctk.CTkButton(self.sidebar_frame, text="🔄  데이터 로드", command=self.reload_all_data, height=40, anchor="w", fg_color=COLORS["bg_medium"], text_color=COLORS["text"], hover_color=COLORS["bg_light"], font=FONTS["header"]).pack(fill="x", padx=10, pady=10, side="bottom")

    def create_content_area(self):
        self.content_frame = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.content_frame.grid(row=0, column=1, sticky="nsew")
        
        self.view_dashboard = DashboardView(self.content_frame, self.dm, self.pm)
        self.view_table = TableView(self.content_frame, self.dm, self.pm)

    def switch_view(self, view_name, view_instance):
        if hasattr(self, 'view_table') and self.view_table.is_dropdown_open:
            self.view_table.close_dropdown()
        for text, btn in self.nav_buttons.items():
            if text == view_name:
                btn.configure(fg_color=COLORS["bg_light"], text_color=COLORS["text"])
            else:
                btn.configure(fg_color="transparent", text_color=COLORS["text_dim"])
        
        for child in self.content_frame.winfo_children():
            child.pack_forget()
        
        view_instance.pack(fill="both", expand=True)
        self.current_view = view_instance
        
        if hasattr(view_instance, "refresh_data"):
            view_instance.refresh_data()

    def show_dashboard_view(self): self.switch_view("🏠  대시보드", self.view_dashboard)
    def show_table_view(self): self.switch_view("📊  테이블 뷰", self.view_table)

    def reload_all_data(self):
        success, msg = self.dm.load_data()
        if success:
            messagebox.showinfo("완료", "데이터를 새로고침했습니다.")
            self.refresh_ui()
        else:
            messagebox.showerror("오류", msg)

    def load_data_initial(self):
        self.dm.load_data()

    def refresh_ui(self):
        self.update_sidebar_theme()
        self.refresh_current_view()

    def update_sidebar_theme(self):
        if self.dm.is_dev_mode:
            self.sidebar_frame.configure(fg_color="#5a1e1e")
            self.logo_label.configure(text="[DEV MODE]", text_color=COLORS["danger"])
        else:
            self.sidebar_frame.configure(fg_color=COLORS["bg_dark"])
            self.logo_label.configure(text="Production Manager", text_color=COLORS["primary"])

    def refresh_current_view(self):
        if self.current_view and hasattr(self.current_view, "refresh_data"):
            self.current_view.refresh_data()

    def handle_global_click(self, event):
        if self.current_view == self.view_table:
            if self.view_table.is_dropdown_open:
                x, y = event.x_root, event.y_root
                dd = self.view_table.dropdown_frame
                btn = self.view_table.filter_dropdown_btn
                
                dd_x, dd_y = dd.winfo_rootx(), dd.winfo_rooty()
                dd_w, dd_h = dd.winfo_width(), dd.winfo_height()
                
                btn_x, btn_y = btn.winfo_rootx(), btn.winfo_rooty()
                btn_w, btn_h = btn.winfo_width(), btn.winfo_height()

                in_dd = (dd_x <= x <= dd_x + dd_w) and (dd_y <= y <= dd_y + dd_h)
                in_btn = (btn_x <= x <= btn_x + btn_w) and (btn_y <= y <= btn_y + btn_h)

                if not in_dd and not in_btn:
                    self.view_table.close_dropdown()

    def on_closing(self):
        # [핵심 수정] 종료 시 예약된 자동 새로고침 타이머 취소
        if self.refresh_timer:
            self.after_cancel(self.refresh_timer)
            self.refresh_timer = None
            
        self.quit()    
        self.destroy() 

if __name__ == "__main__":
    app = COXProductionManager()
    app.mainloop()
