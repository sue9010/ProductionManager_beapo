import os
import re
from datetime import datetime
from tkinter import filedialog, messagebox

import customtkinter as ctk

try:
    from tkinterdnd2 import DND_FILES
    DND_AVAILABLE = True
except ImportError:
    DND_AVAILABLE = False
    print("Warning: tkinterdnd2 library not found. Drag and drop will not work.")

from styles import COLORS, FONT_FAMILY, FONTS
from popups.memo_popup import MemoSidebar


class BasePopup(ctk.CTkToplevel):
    def __init__(self, parent, data_manager, refresh_callback, title="Popup", geometry="800x600", req_no=None):
        super().__init__(parent)
        self.dm = data_manager
        self.refresh_callback = refresh_callback
        self.req_no = req_no

        self.title(title)
        
        try:
            w_str, h_str = geometry.split('x')
            base_width = int(w_str)
            base_height = int(h_str)
        except:
            base_width, base_height = 800, 600

        SIDEBAR_WIDTH = 320
        total_width = base_width + SIDEBAR_WIDTH if req_no else base_width

        self.center_window(total_width, base_height)

        self.main_container = ctk.CTkFrame(self, fg_color="transparent")
        self.main_container.pack(fill="both", expand=True)

        if req_no:
            self.main_container.grid_columnconfigure(0, weight=1) 
            self.main_container.grid_columnconfigure(1, weight=0, minsize=SIDEBAR_WIDTH) 
            self.main_container.grid_rowconfigure(0, weight=1)

            self.content_frame = ctk.CTkFrame(self.main_container, fg_color="transparent")
            self.content_frame.grid(row=0, column=0, sticky="nsew")

            self.sidebar_frame = ctk.CTkFrame(self.main_container, fg_color=COLORS["bg_medium"], corner_radius=0, width=SIDEBAR_WIDTH)
            self.sidebar_frame.grid(row=0, column=1, sticky="nsew")
            self.sidebar_frame.grid_propagate(False)

            self._create_memo_sidebar()
        else:
            self.content_frame = ctk.CTkFrame(self.main_container, fg_color="transparent")
            self.content_frame.pack(fill="both", expand=True)

        self.bind("<Escape>", self.close)

    def close(self, event=None):
        self.destroy()

    def center_window(self, width, height):
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = (screen_width / 2) - (width / 2)
        y = (screen_height / 2) - (height / 2)
        self.geometry(f"{width}x{height}+{int(x)}+{int(y)}")

    # ----------------------------------------------------------------
    # Shared Helper Methods
    # ----------------------------------------------------------------
    def _open_pdf_file(self, file_path):
        if not file_path or str(file_path) == "-":
            return
            
        try:
            if os.path.exists(file_path):
                os.startfile(file_path)
            else:
                messagebox.showerror("오류", "파일을 찾을 수 없습니다.", parent=self)
        except Exception as e:
            messagebox.showerror("오류", f"파일 열기 실패: {e}", parent=self)

    def _add_dev_edit_button(self, parent_frame):
        """개발자 모드일 경우 정보 수정 버튼을 추가합니다."""
        if getattr(self.dm, 'is_dev_mode', False):
            ctk.CTkButton(parent_frame, text="정보 수정", width=100, command=self.open_edit_popup, 
                          fg_color=COLORS["warning"], hover_color="#D35400").pack(side="right", padx=(0, 5))

    def open_edit_popup(self):
        """[Dev] 공통 정보 및 품목별 정보 수정 팝업"""
        if not getattr(self.dm, 'is_dev_mode', False):
            return

        target_indices = self.dm.df[self.dm.df["번호"].astype(str) == str(self.req_no)].index
        if len(target_indices) == 0:
            messagebox.showerror("오류", "데이터를 찾을 수 없습니다.", parent=self)
            return
        
        first_row = self.dm.df.loc[target_indices[0]]

        edit_win = ctk.CTkToplevel(self)
        edit_win.title(f"[DEV] 데이터 수정 - {self.req_no}")
        edit_win.geometry("600x700")
        
        # [수정] 팝업 최상위 설정 강화
        edit_win.transient(self)
        edit_win.grab_set()
        
        container = ctk.CTkScrollableFrame(edit_win)
        container.pack(fill="both", expand=True, padx=10, pady=10)
        
        # --- A. 공통 정보 수정 섹션 ---
        ctk.CTkLabel(container, text="■ 공통 정보 (일괄 적용)", font=FONTS["header"]).pack(anchor="w", pady=(0, 10))
        
        common_fields = ["업체명", "출고요청일", "출고예정일", "출고일", "Status", "기타요청사항", "업체별 특이사항", "대기사유"]
        common_entries = {}
        
        for field in common_fields:
            row_frame = ctk.CTkFrame(container, fg_color="transparent")
            row_frame.pack(fill="x", pady=2)
            ctk.CTkLabel(row_frame, text=field, width=120, anchor="w").pack(side="left")
            
            val = first_row.get(field, "")
            
            # Status 필드는 드롭다운(OptionMenu)으로 생성
            if field == "Status":
                status_options = ["생산 접수", "대기", "생산중", "중지", "완료"]
                entry = ctk.CTkOptionMenu(row_frame, values=status_options, height=28, fg_color=COLORS["bg_medium"], text_color=COLORS["text"], button_color=COLORS["primary"], button_hover_color=COLORS["primary_hover"])
                entry.set(str(val))
            else:
                entry = ctk.CTkEntry(row_frame, height=28)
                entry.insert(0, str(val))
            
            entry.pack(side="left", fill="x", expand=True)
            common_entries[field] = entry

        # --- B. 품목별 정보 수정 섹션 ---
        ctk.CTkFrame(container, height=2, fg_color=COLORS["border"]).pack(fill="x", pady=20)
        ctk.CTkLabel(container, text="■ 품목별 상세 정보", font=FONTS["header"]).pack(anchor="w", pady=(0, 10))

        item_entries = []

        for idx in target_indices:
            row_data = self.dm.df.loc[idx]
            
            item_card = ctk.CTkFrame(container, fg_color=COLORS["bg_dark"])
            item_card.pack(fill="x", pady=5, padx=5)
            
            r1 = ctk.CTkFrame(item_card, fg_color="transparent")
            r1.pack(fill="x", padx=5, pady=2)
            ctk.CTkLabel(r1, text="모델명:", width=60, anchor="w").pack(side="left")
            e_model = ctk.CTkEntry(r1, width=200)
            e_model.insert(0, str(row_data.get("모델명", "")))
            e_model.pack(side="left", fill="x", expand=True)
            
            r2 = ctk.CTkFrame(item_card, fg_color="transparent")
            r2.pack(fill="x", padx=5, pady=2)
            
            ctk.CTkLabel(r2, text="상세:", width=60, anchor="w").pack(side="left")
            e_detail = ctk.CTkEntry(r2, width=150)
            e_detail.insert(0, str(row_data.get("상세", "")))
            e_detail.pack(side="left", fill="x", expand=True, padx=(0, 10))
            
            ctk.CTkLabel(r2, text="수량:", width=40, anchor="w").pack(side="left")
            e_qty = ctk.CTkEntry(r2, width=60)
            e_qty.insert(0, str(row_data.get("수량", "")))
            e_qty.pack(side="left")

            item_entries.append({
                "index": idx,
                "model": e_model,
                "detail": e_detail,
                "qty": e_qty
            })
            
        def save_changes():
            new_common_data = {f: e.get() for f, e in common_entries.items()}
            
            for idx in target_indices:
                for col, val in new_common_data.items():
                    self.dm.df.loc[idx, col] = val
            
            for item in item_entries:
                idx = item["index"]
                self.dm.df.loc[idx, "모델명"] = item["model"].get()
                self.dm.df.loc[idx, "상세"] = item["detail"].get()
                
                qty_val = item["qty"].get()
                try:
                    self.dm.df.loc[idx, "수량"] = int(qty_val)
                except:
                    self.dm.df.loc[idx, "수량"] = qty_val
            
            success, msg = self.dm.save_to_excel()
            if success:
                messagebox.showinfo("성공", "데이터가 수정되었습니다.", parent=edit_win)
                edit_win.destroy()
                if self.refresh_callback:
                    self.refresh_callback()
            else:
                messagebox.showerror("실패", msg, parent=edit_win)

        ctk.CTkButton(edit_win, text="저장", command=save_changes, fg_color=COLORS["primary"], width=100).pack(pady=20)

    def _add_grid_item(self, parent, label_text, value, row, col, **kwargs):
        ctk.CTkLabel(parent, text=label_text, font=FONTS["main_bold"], text_color=COLORS["primary"]).grid(row=row, column=col*2, padx=10, pady=5, sticky="nw")
        ctk.CTkLabel(parent, text=str(value), font=FONTS["main"], text_color=COLORS["text"], **kwargs).grid(row=row, column=col*2+1, padx=10, pady=5, sticky="w")

    def _open_change_date_input(self, req_no, current_date, parent=None):
        master = parent if parent else self
        win = ctk.CTkToplevel(master)
        win.transient(master) 
        win.title("출고예정일 변경")
        
        width, height = 300, 150
        screen_width = win.winfo_screenwidth()
        screen_height = win.winfo_screenheight()
        x = (screen_width / 2) - (width / 2)
        y = (screen_height / 2) - (height / 2)
        win.geometry(f"{width}x{height}+{int(x)}+{int(y)}")

        win.lift()
        win.bind("<Escape>", lambda e: win.destroy())

        ctk.CTkLabel(win, text="새로운 출고예정일을 입력하세요.", font=FONTS["main"]).pack(pady=(20, 10))
        
        entry = ctk.CTkEntry(win, width=150)
        entry.pack(pady=5)
        entry.insert(0, current_date if current_date != '-' else datetime.now().strftime("%Y-%m-%d"))
        
        def confirm():
            new_date = entry.get()
            if not new_date: return
            
            success, msg = self.dm.update_expected_date(req_no, new_date)
            if success:
                if hasattr(self, 'lbl_expected_date'):
                    self.lbl_expected_date.configure(text=new_date)
                self.refresh_callback()
                win.destroy()
            else:
                messagebox.showerror("실패", msg, parent=win)
            
        ctk.CTkButton(win, text="변경 저장", command=confirm, fg_color=COLORS["primary"], width=100).pack(pady=10)
        win.focus_force() 
        entry.focus_set()

    def _add_hold_button(self, parent_frame, req_no, current_status):
        """상태에 따라 중지/재개 버튼을 추가합니다."""
        if current_status == "중지":
            ctk.CTkButton(parent_frame, text="생산 재개", width=80, 
                          fg_color=COLORS["success"], hover_color=COLORS["success_hover"],
                          command=lambda: self._open_resume_production_popup(req_no)).pack(side="right", padx=(0, 5))
        else:
            ctk.CTkButton(parent_frame, text="중지", width=80, 
                          fg_color=COLORS["danger"], hover_color=COLORS["danger_hover"],
                          command=lambda: self._open_hold_confirm_popup(req_no)).pack(side="right", padx=(0, 5))

    def _open_hold_confirm_popup(self, req_no):
        answer = messagebox.askyesno("생산 중지", f"번호 [{req_no}] 생산을 중지하시겠습니까?", parent=self)
        if answer:
            success, msg = self.dm.update_status_to_hold(req_no)
            if success:
                messagebox.showinfo("완료", "생산이 중지되었습니다.", parent=self)
                self.destroy()
                if self.refresh_callback:
                    self.refresh_callback()
            else:
                messagebox.showerror("실패", msg, parent=self)

    def _open_resume_production_popup(self, req_no):
        win = ctk.CTkToplevel(self)
        win.transient(self) 
        win.title("생산 재개")
        
        width, height = 500, 450
        screen_width = win.winfo_screenwidth()
        screen_height = win.winfo_screenheight()
        x = (screen_width / 2) - (width / 2)
        y = (screen_height / 2) - (height / 2)
        win.geometry(f"{width}x{height}+{int(x)}+{int(y)}")

        win.lift()
        win.bind("<Escape>", lambda e: win.destroy())
        
        ctk.CTkLabel(win, text=f"번호 [{req_no}] 생산을 재개합니다.\n새로운 출고예정일을 입력하세요.", font=FONTS["main_bold"]).pack(pady=(20, 10))
        
        # 날짜 입력
        entry = ctk.CTkEntry(win, width=200)
        entry.pack(pady=5)
        entry.insert(0, datetime.now().strftime("%Y-%m-%d"))
        
        # [신규] 품목 정보 및 시리얼 번호 표시 영역
        ctk.CTkLabel(win, text="품목 리스트", font=FONTS["header"]).pack(anchor="w", padx=20, pady=(20, 5))
        scroll = ctk.CTkScrollableFrame(win, height=150, corner_radius=6, fg_color=COLORS["bg_medium"])
        scroll.pack(fill="both", expand=True, padx=20, pady=(0, 10))
        
        target_rows = self.dm.df[self.dm.df["번호"].astype(str) == str(req_no)]
        
        for _, row in target_rows.iterrows():
            item_frame = ctk.CTkFrame(scroll, fg_color="transparent")
            item_frame.pack(fill="x", pady=2)
            
            # 모델명 및 수량
            model_info = f"[{row.get('모델명')}] {row.get('상세')} ({row.get('수량')}개)"
            ctk.CTkLabel(item_frame, text=model_info, font=FONTS["main_bold"], anchor="w").pack(fill="x")
            
            # 시리얼 번호
            serials = str(row.get('시리얼번호', '')).strip()
            if serials == '-' or serials == 'nan': serials = ""
            if serials:
                ctk.CTkLabel(item_frame, text=f"S/N: {serials}", font=FONTS["small"], text_color=COLORS["text_dim"], 
                             wraplength=420, justify="left", anchor="w").pack(fill="x")

        def confirm():
            new_date = entry.get()
            if not new_date:
                messagebox.showwarning("입력 오류", "날짜를 입력해주세요.", parent=win)
                return

            success, msg = self.dm.update_status_resume(req_no, new_date)
            if success:
                self.refresh_callback()
                win.destroy()
                self.destroy()
            else:
                messagebox.showerror("실패", msg, parent=win)
            
        ctk.CTkButton(win, text="저장 및 생산 재개", command=confirm, fg_color=COLORS["primary"], width=150).pack(pady=10)
        win.focus_force() 
        entry.focus_set()

    def open_waiting_reason_popup(self):
        reason_window = ctk.CTkToplevel(self)
        reason_window.title("생산 대기 설정")
        
        width, height = 400, 200
        screen_width = reason_window.winfo_screenwidth()
        screen_height = reason_window.winfo_screenheight()
        x = (screen_width / 2) - (width / 2)
        y = (screen_height / 2) - (height / 2)
        reason_window.geometry(f"{width}x{height}+{int(x)}+{int(y)}")

        # [수정] 팝업 최상위 설정 및 포커스 유지
        reason_window.transient(self)
        reason_window.grab_set()
        
        ctk.CTkLabel(reason_window, text="대기 사유를 입력하세요.", font=FONTS["header"]).pack(pady=(20, 10))
        
        e_reason = ctk.CTkEntry(reason_window, width=300)
        e_reason.pack(pady=5)
        e_reason.focus_set()
        
        def submit_reason():
            reason_text = e_reason.get().strip()
            if not reason_text:
                messagebox.showwarning("경고", "대기 사유를 입력해주세요.", parent=reason_window)
                return
            
            success, msg = self.dm.update_status_to_waiting(self.req_no, reason_text)
            if success:
                messagebox.showinfo("성공", "상태가 '대기'로 변경되었습니다.", parent=reason_window)
                reason_window.destroy()
                self.destroy()
                if self.refresh_callback:
                    self.refresh_callback() 
            else:
                messagebox.showerror("실패", msg, parent=reason_window)
        
        btn_frame = ctk.CTkFrame(reason_window, fg_color="transparent")
        btn_frame.pack(pady=20)
        
        ctk.CTkButton(btn_frame, text="확인", command=submit_reason, fg_color=COLORS["primary"], hover_color=COLORS["primary_hover"], width=80).pack(side="left", padx=5)
        ctk.CTkButton(btn_frame, text="취소", command=reason_window.destroy, fg_color=COLORS["bg_light"], hover_color=COLORS["bg_light_hover"], width=80).pack(side="left", padx=5)

    def _create_memo_sidebar(self):
        self.memo_sidebar = MemoSidebar(self.sidebar_frame, self.dm, self.req_no)

    def create_widgets(self):
        raise NotImplementedError
