from datetime import datetime
from tkinter import messagebox

import customtkinter as ctk

from styles import COLORS, FONTS

from .base_popup import BasePopup, DATE_VALIDATION_MESSAGE, validate_date


class SchedulePopup(BasePopup):
    def __init__(self, parent, data_manager, refresh_callback, req_no):
        self.req_no = req_no
        self.target_rows = data_manager.df[data_manager.df["번호"].astype(str) == str(req_no)]
        
        if self.target_rows.empty:
            messagebox.showerror("오류", "데이터를 찾을 수 없습니다.")
            return

        self.first_row = self.target_rows.iloc[0]
        self.current_status = str(self.first_row.get("Status", ""))

        title = f"생산 일정 수립 - 번호 [{req_no}]"
        if self.current_status == "중지":
            title = f"생산 재개 (중지 해제) - 번호 [{req_no}]"
        elif self.current_status == "대기":
            title = f"생산 대기 관리 - 번호 [{req_no}]"

        super().__init__(parent, data_manager, refresh_callback, title=title, geometry="800x650", req_no=req_no)
        self.create_widgets()

    def create_widgets(self):
        parent = self.content_frame

        file_path = self.first_row.get("파일경로", "-") 

        common_info = {
            "업체명": self.first_row.get("업체명", "-"),
            "기타요청사항": self.first_row.get("기타요청사항", "-"),
            "업체별 특이사항": self.first_row.get("업체별 특이사항", "-"),
            "출고요청일": self.first_row.get("출고요청일", "-"),
            "대기사유": self.first_row.get("대기사유", "-")
        }

        info_frame = ctk.CTkFrame(parent, fg_color="transparent")
        info_frame.pack(fill="x", padx=20, pady=10)

        header_line = ctk.CTkFrame(info_frame, fg_color="transparent")
        header_line.pack(fill="x", pady=(0, 10))
        
        title_text = f"생산 일정 수립 (번호: {self.req_no})"
        if self.current_status == "중지":
            title_text = f"생산 재개 (번호: {self.req_no})"
        elif self.current_status == "대기":
            title_text = f"생산 대기 관리 (번호: {self.req_no})"
            
        ctk.CTkLabel(header_line, text=title_text, font=FONTS["title"]).pack(side="left")
        
        if file_path and str(file_path) != "-":
            ctk.CTkButton(header_line, text="PDF 보기", width=80, fg_color=COLORS["danger"], hover_color=COLORS["danger_hover"],
                          command=lambda: self._open_pdf_file(file_path)).pack(side="right")
        
        self._add_hold_button(header_line, self.req_no, self.current_status)
        
        # BasePopup의 공통 버튼 추가 메서드 사용 (상단 헤더)
        self._add_dev_edit_button(header_line)

        if self.current_status == "대기":
            pass
        elif self.current_status != "중지":
            ctk.CTkButton(header_line, text="생산 대기", width=80, fg_color=COLORS["danger"], hover_color=COLORS["danger_hover"], 
                          command=self.open_waiting_reason_popup).pack(side="right", padx=(0, 5))

        grid_frame = ctk.CTkFrame(info_frame, fg_color=COLORS["bg_dark"])
        grid_frame.pack(fill="x")

        self._add_grid_item(grid_frame, "업체명", common_info["업체명"], 0, 0)
        self._add_grid_item(grid_frame, "출고요청일", common_info["출고요청일"], 0, 1)
        
        # [수정] 텍스트가 길어지면 줄바꿈 되도록 설정 (wraplength=250)
        self._add_grid_item(grid_frame, "기타요청사항", common_info["기타요청사항"], 1, 0, wraplength=250, justify="left")
        self._add_grid_item(grid_frame, "업체별 특이사항", common_info["업체별 특이사항"], 1, 1, wraplength=250, justify="left")

        if self.current_status == "대기":
            ctk.CTkLabel(grid_frame, text="⚠️ 대기 사유", font=FONTS["main_bold"], text_color=COLORS["warning"]).grid(row=2, column=0, padx=10, pady=5, sticky="w")
            ctk.CTkLabel(grid_frame, text=str(common_info["대기사유"]), font=FONTS["main_bold"], text_color=COLORS["text"]).grid(row=2, column=1, padx=10, pady=5, sticky="w")

        ctk.CTkLabel(parent, text="품목 리스트", font=FONTS["header"]).pack(anchor="w", padx=20, pady=(20, 5))
        scroll_frame = ctk.CTkScrollableFrame(parent, height=200, corner_radius=10)
        scroll_frame.pack(fill="both", expand=True, padx=20, pady=(0, 10))

        for idx, row in self.target_rows.iterrows():
            card = ctk.CTkFrame(scroll_frame, fg_color=COLORS["bg_medium"])
            card.pack(fill="x", pady=5, padx=5)
            left = ctk.CTkFrame(card, fg_color="transparent")
            left.pack(side="left", fill="both", expand=True, padx=10, pady=10)
            ctk.CTkLabel(left, text=f"[{row.get('모델명')}] {row.get('상세')}", font=FONTS["main_bold"], wraplength=680, justify="left").pack(anchor="w")
            ctk.CTkLabel(left, text=f"수량: {row.get('수량')}", font=FONTS["main"], text_color=COLORS["warning"]).pack(anchor="w")

            # [신규] 시리얼 번호가 있으면 표시
            serials = str(row.get('시리얼번호', '')).strip()
            if serials == '-' or serials == 'nan': serials = ""
            
            if serials:
                ctk.CTkLabel(left, text=f"S/N: {serials}", 
                             font=FONTS["small"], text_color=COLORS["text_dim"], 
                             wraplength=450, justify="left").pack(anchor="w", pady=(5, 0))

        footer = ctk.CTkFrame(parent, fg_color="transparent")
        footer.pack(fill="x", padx=20, pady=20)
        
        ctk.CTkLabel(footer, text="출고예정일:", font=FONTS["header"]).pack(side="left", padx=(0, 10))
        
        self.date_entry = ctk.CTkEntry(footer, width=200, placeholder_text="yyyy-mm-dd")
        self.date_entry.pack(side="left", padx=(0, 20))
        
        old_expected = self.first_row.get("출고예정일", "")
        if old_expected and str(old_expected) != "-" and str(old_expected) != "NaT":
             self.date_entry.insert(0, str(old_expected))
        else:
             self.date_entry.insert(0, datetime.now().strftime("%Y-%m-%d"))

        btn_text = "일정 등록 (생산 시작)"
        if self.current_status == "중지":
            btn_text = "일정 재등록 및 생산 시작"
        elif self.current_status == "대기":
            btn_text = "대기 해제 및 생산 시작"
            
        ctk.CTkButton(footer, text=btn_text, command=self.confirm, fg_color=COLORS["primary"], hover_color=COLORS["primary_hover"]).pack(side="right", padx=(5,0))
        ctk.CTkButton(footer, text="요청 삭제", command=self.delete_entry, fg_color=COLORS["danger"], hover_color=COLORS["danger_hover"]).pack(side="right", padx=(0,0))
        

    def delete_entry(self):
        if messagebox.askyesno("삭제 확인", f"정말로 요청 번호 [{self.req_no}]의 모든 데이터를 삭제하시겠습니까?\n이 작업은 되돌릴 수 없습니다.", parent=self):
            success, msg = self.dm.delete_request(self.req_no)
            if success:
                messagebox.showinfo("삭제 완료", "데이터가 성공적으로 삭제되었습니다.", parent=self.master)
                self.destroy()
                self.refresh_callback()
            else:
                messagebox.showerror("삭제 실패", msg, parent=self)

    def confirm(self):
        date_str = validate_date(self.date_entry.get())
        if date_str is None:
            messagebox.showwarning("경고", DATE_VALIDATION_MESSAGE, parent=self)
            return
        
        try:
            success, msg = self.dm.update_production_schedule(self.req_no, date_str)
            if success:
                messagebox.showinfo("성공", "생산 일정이 등록/수정 되었습니다.", parent=self)
                self.destroy()
                self.refresh_callback() 
            else:
                messagebox.showerror("실패", msg, parent=self)
        except Exception as e:
            messagebox.showerror("오류", f"오류 발생: {e}", parent=self)
