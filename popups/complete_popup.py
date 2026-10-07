from datetime import datetime
from tkinter import messagebox

import customtkinter as ctk

from styles import COLORS, FONTS

from .base_popup import BasePopup, DATE_VALIDATION_MESSAGE, validate_date
from .serial_input_popup import SerialInputPopup


class CompletePopup(BasePopup):
    @staticmethod
    def _get_serial_status_color(saved_count, qty):
        try:
            return COLORS["success"] if saved_count >= int(qty) else COLORS["warning"]
        except (TypeError, ValueError, OverflowError):
            return COLORS["warning"]

    def __init__(self, parent, data_manager, refresh_callback, req_no):
        self.req_no = req_no
        self.target_rows = data_manager.df[data_manager.df["번호"].astype(str) == str(req_no)]

        if self.target_rows.empty:
            messagebox.showerror("오류", "데이터를 찾을 수 없습니다.")
            return
            
        self.first_row = self.target_rows.iloc[0]
        self.current_status = str(self.first_row.get("Status", ""))
        
        super().__init__(parent, data_manager, refresh_callback, title=f"생산 완료 처리 - 번호 [{req_no}]", geometry="850x700", req_no=req_no)
        self.create_widgets()

    def create_widgets(self):
        parent = self.content_frame
        
        # --- 상단 정보 ---
        file_path = self.first_row.get("파일경로", "-")
        common_info = {
            "업체명": self.first_row.get("업체명", "-"),
            "출고요청일": self.first_row.get("출고요청일", "-"),
            "출고예정일": self.first_row.get("출고예정일", "-"),
            "기타요청사항": self.first_row.get("기타요청사항", "-"),
            "특이사항": self.first_row.get("업체별 특이사항", "-")
        }

        info_frame = ctk.CTkFrame(parent, fg_color="transparent")
        info_frame.pack(fill="x", padx=20, pady=10)
        
        header_line = ctk.CTkFrame(info_frame, fg_color="transparent")
        header_line.pack(fill="x", pady=(0, 10))
        ctk.CTkLabel(header_line, text=f"생산 완료 처리 (번호: {self.req_no})", font=FONTS["title"]).pack(side="left")

        if file_path and str(file_path) != "-":
            ctk.CTkButton(header_line, text="PDF 보기", width=80, fg_color=COLORS["danger"], hover_color=COLORS["danger_hover"],
                          command=lambda: self._safe_open_pdf(file_path)).pack(side="right")
        
        self._add_hold_button(header_line, self.req_no, self.current_status)
        
        # 개발자 모드 수정 버튼 추가
        self._add_dev_edit_button(header_line)

        # [신규] 대기 버튼 추가 (중지와 PDF 보기 왼쪽)
        if self.current_status != "대기" and self.current_status != "중지":
             ctk.CTkButton(header_line, text="대기", width=80, 
                           fg_color=COLORS["warning"], hover_color="#D35400", 
                           command=self.open_waiting_reason_popup).pack(side="right", padx=(0, 5))

        grid_frame = ctk.CTkFrame(info_frame, fg_color=COLORS["bg_dark"])
        grid_frame.pack(fill="x")
        self._add_grid_item(grid_frame, "업체명", common_info["업체명"], 0, 0)
        self._add_grid_item(grid_frame, "출고요청일", common_info["출고요청일"], 0, 1)
        
        # [수정] 출고예정일 수정 기능 추가
        # 기존: self._add_grid_item(grid_frame, "출고예정일", common_info["출고예정일"], 1, 0)
        # 변경: 라벨 + 변경 버튼 추가
        ctk.CTkLabel(grid_frame, text="출고예정일", font=FONTS["main_bold"], text_color=COLORS["primary"]).grid(row=1, column=0, padx=10, pady=5, sticky="nw")
        
        date_frame = ctk.CTkFrame(grid_frame, fg_color="transparent")
        date_frame.grid(row=1, column=1, padx=10, pady=5, sticky="w")
        
        self.lbl_expected_date = ctk.CTkLabel(date_frame, text=str(common_info["출고예정일"]), font=FONTS["main"], text_color=COLORS["text"])
        self.lbl_expected_date.pack(side="left", padx=(0, 5))
        
        ctk.CTkButton(date_frame, text="변경", width=40, height=20, font=FONTS["small"], 
                      fg_color=COLORS["bg_light"], text_color=COLORS["text"],
                      command=lambda: self._open_change_date_input(self.req_no, self.lbl_expected_date.cget("text"))).pack(side="left")

        self._add_grid_item(grid_frame, "특이사항", common_info["특이사항"], 1, 1)

        # --- 품목 리스트 및 상세 입력 버튼 ---
        ctk.CTkLabel(parent, text="품목별 상세 정보 입력 (시리얼 관리)", font=FONTS["header"]).pack(anchor="w", padx=20, pady=(20, 5))
        scroll_frame = ctk.CTkScrollableFrame(parent, height=250, corner_radius=10)
        scroll_frame.pack(fill="both", expand=True, padx=20, pady=(0, 10))

        for item_index, (idx, row) in enumerate(self.target_rows.iterrows(), start=1):
            model = row.get('모델명')
            detail = row.get('상세')
            qty = row.get('수량', 0)
            
            card = ctk.CTkFrame(scroll_frame, fg_color=COLORS["bg_medium"])
            card.pack(fill="x", pady=5, padx=5)

            # 좌측 정보
            left = ctk.CTkFrame(card, fg_color="transparent")
            left.pack(side="left", fill="both", expand=True, padx=10, pady=10)
            ctk.CTkLabel(left, text=f"[{model}] {detail}", font=FONTS["main_bold"]).pack(anchor="w")
            ctk.CTkLabel(left, text=f"수량: {qty}개", font=FONTS["main"], text_color=COLORS["warning"]).pack(anchor="w")

            # [신규] 시리얼 번호 표시 라벨 생성
            serial_records = self.dm.get_serial_list(self.req_no, model, item_index)
            serials = ", ".join(str(item["시리얼번호"]) for item in serial_records)
            
            serial_lbl = ctk.CTkLabel(left, text=f"S/N: {serials}" if serials else "", 
                                      font=FONTS["small"], text_color=COLORS["text_dim"], 
                                      wraplength=450, justify="left")
            # 값이 있을 때만 표시
            if serials:
                serial_lbl.pack(anchor="w", pady=(5, 0))

            # 우측 버튼
            right = ctk.CTkFrame(card, fg_color="transparent")
            right.pack(side="right", padx=10, pady=10)
            
            # 현재 입력된 개수 확인
            saved_count = len(serial_records)
            
            status_lbl = ctk.CTkLabel(
                right,
                text=f"입력됨: {saved_count}/{qty}",
                font=FONTS["small"],
                text_color=self._get_serial_status_color(saved_count, qty),
            )
            status_lbl.pack(side="left", padx=10)
            
            # [수정] open_serial_popup에 serial_lbl 전달
            btn = ctk.CTkButton(right, text="상세 입력", width=100, 
                                command=lambda m=model, q=qty, l=status_lbl, sl=serial_lbl, i=item_index: self.open_serial_popup(m, q, l, sl, i))
            btn.pack(side="left")

        # --- 하단 공통 정보 ---
        footer = ctk.CTkFrame(parent, fg_color="transparent")
        footer.pack(fill="x", padx=20, pady=20)

        ctk.CTkLabel(footer, text="출고일:").pack(side="left", padx=(0, 5))
        self.e_date = ctk.CTkEntry(footer, width=120)
        self.e_date.pack(side="left", padx=(0, 20))
        self.e_date.insert(0, datetime.now().strftime("%Y-%m-%d"))

        ctk.CTkButton(footer, text="최종 완료 처리", command=self.save_all, fg_color=COLORS["primary"], hover_color=COLORS["primary_hover"], width=150).pack(side="right")
        ctk.CTkButton(footer, text="취소", command=self.destroy, fg_color=COLORS["bg_light"], hover_color=COLORS["bg_light_hover"], width=80).pack(side="right", padx=(0, 5))

    def _safe_open_pdf(self, path):
        self._open_pdf_file(path)

    def open_serial_popup(self, model, qty, status_label, serial_label=None, item_index=None):
        def on_save_callback(model_name, data_list):
            # 1. 데이터 업데이트
            self.dm.update_serial_list(self.req_no, model_name, data_list, item_index)
            saved_records = self.dm.get_serial_list(self.req_no, model_name, item_index)
            
            # 2. 상태 라벨 업데이트 (입력 개수)
            current_len = len(saved_records)
            status_label.configure(text=f"입력됨: {current_len}/{qty}")
            status_label.configure(text_color=self._get_serial_status_color(current_len, qty))
                
            # 3. [신규] 시리얼 번호 라벨 즉시 업데이트
            if serial_label:
                # 입력된 데이터에서 시리얼 번호만 추출하여 문자열 생성
                new_serials = [str(item["시리얼번호"]) for item in saved_records]
                joined_text = ", ".join(new_serials)
                
                if joined_text:
                    serial_label.configure(text=f"S/N: {joined_text}")
                    # 기존에 안 보였던 경우를 위해 pack (이미 되어있어도 안전함)
                    serial_label.pack(anchor="w", pady=(5, 0))
                else:
                    serial_label.configure(text="")
                    serial_label.pack_forget()

        SerialInputPopup(self, self.dm, self.req_no, model, qty, on_save_callback, item_index)

    def save_all(self):
        out_date = validate_date(self.e_date.get())
        if out_date is None:
            messagebox.showwarning("입력 오류", DATE_VALIDATION_MESSAGE, parent=self)
            return

        answer = messagebox.askyesno("완료 처리", "모든 데이터를 저장하고 '생산 완료' 처리하시겠습니까?", parent=self)
        
        if answer:
            try:
                success, msg = self.dm.finalize_production(self.req_no, out_date)
                
                if success:
                    messagebox.showinfo("성공", "생산 완료 처리되었습니다.", parent=self)
                    self.destroy()
                    self.refresh_callback()
                else:
                    messagebox.showerror("실패", msg, parent=self)
                    
            except Exception as e:
                messagebox.showerror("오류", f"저장 중 오류: {e}", parent=self)
