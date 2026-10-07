from tkinter import messagebox

import customtkinter as ctk

from styles import COLORS, FONTS

from .base_popup import BasePopup
from .serial_input_popup import SerialInputPopup


class ViewPopup(BasePopup):
    def __init__(self, parent, data_manager, refresh_callback, req_no):
        self.req_no = req_no
        self.target_rows = data_manager.df[data_manager.df["번호"].astype(str) == str(req_no)]

        if self.target_rows.empty:
            messagebox.showerror("오류", "데이터를 찾을 수 없습니다.")
            return

        self.row0 = self.target_rows.iloc[0]
        self.current_status = str(self.row0.get("Status", ""))
        
        super().__init__(parent, data_manager, refresh_callback, title=f"출고 완료 상세 정보 - 번호 [{req_no}]", geometry="900x650", req_no=req_no)
        self.create_widgets()

    def create_widgets(self):
        parent = self.content_frame

        file_path = self.row0.get("파일경로", "-")

        header_frame = ctk.CTkFrame(parent, fg_color="transparent")
        header_frame.pack(fill="x", padx=20, pady=20)

        header_line = ctk.CTkFrame(header_frame, fg_color="transparent")
        header_line.pack(fill="x", pady=(0, 10))

        ctk.CTkLabel(header_line, text=f"출고 완료 상세 정보 (번호: {self.req_no})", font=FONTS["title"]).pack(side="left")

        if file_path and str(file_path) != "-":
            ctk.CTkButton(header_line, text="PDF 보기", width=80, fg_color=COLORS["danger"], hover_color=COLORS["danger_hover"],
                          command=lambda: self._open_pdf_file(file_path)).pack(side="right")
        
        self._add_hold_button(header_line, self.req_no, self.current_status)
        
        # [수정] BasePopup의 공통 버튼 추가 메서드 사용 (상단 헤더)
        self._add_dev_edit_button(header_line)

        grid_frame = ctk.CTkFrame(header_frame, fg_color=COLORS["bg_dark"])
        grid_frame.pack(fill="x")

        common_items = [
            ("업체명", self.row0.get("업체명", "-")),
            ("Status", self.row0.get("Status", "-")),
            ("출고요청일", self.row0.get("출고요청일", "-")),
            ("출고예정일", self.row0.get("출고예정일", "-")),
            ("출고일", self.row0.get("출고일", "-")),
            ("기타요청사항", self.row0.get("기타요청사항", "-")),
            ("업체별 특이사항", self.row0.get("업체별 특이사항", "-"))
        ]

        for i, (label, value) in enumerate(common_items):
            r = i // 2
            c = (i % 2) * 2
            ctk.CTkLabel(
                grid_frame, 
                text=label, 
                font=FONTS["main_bold"], 
                text_color=COLORS["primary"]
            ).grid(row=r, column=c, padx=15, pady=8, sticky="w")
            
            ctk.CTkLabel(
                grid_frame, 
                text=str(value), 
                font=FONTS["main"],
                text_color=COLORS["text"]
            ).grid(row=r, column=c+1, padx=15, pady=8, sticky="w")

        ctk.CTkLabel(parent, text="품목별 상세 정보", font=FONTS["header"]).pack(anchor="w", padx=20, pady=(10, 5))

        scroll_frame = ctk.CTkScrollableFrame(parent, height=350, corner_radius=10)
        scroll_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        for idx, row in self.target_rows.iterrows():
            card = ctk.CTkFrame(scroll_frame, fg_color=COLORS["bg_medium"], corner_radius=6)
            card.pack(fill="x", pady=5, padx=5)

            content = ctk.CTkFrame(card, fg_color="transparent")
            content.pack(side="left", fill="both", expand=True, padx=15, pady=10)

            model_name = row.get('모델명')
            qty = row.get('수량')
            model_info = f"[{model_name}] {row.get('상세')}"
            ctk.CTkLabel(content, text=model_info, font=FONTS["main_bold"]).pack(anchor="w")

            top_info_frame = ctk.CTkFrame(content, fg_color="transparent")
            top_info_frame.pack(fill="x", pady=(5, 0))
            
            infos_top = [
                f"수량: {qty}",
                f"렌즈: {row.get('렌즈업체')}"
            ]
            
            for info in infos_top:
                ctk.CTkLabel(
                    top_info_frame, 
                    text=info, 
                    font=FONTS["main"], 
                    fg_color=COLORS["border"], 
                    corner_radius=4
                ).pack(side="left", padx=(0, 10), ipadx=5)

            serial_text = f"시리얼: {row.get('시리얼번호')}"
            ctk.CTkLabel(
                content, 
                text=serial_text, 
                font=FONTS["main"], 
                fg_color=COLORS["border"], 
                corner_radius=4,
                wraplength=650,
                justify="left",
                anchor="w"
            ).pack(fill="x", pady=(5, 0), ipadx=5)

            btn_frame = ctk.CTkFrame(card, fg_color="transparent")
            btn_frame.pack(side="right", anchor="ne", padx=10, pady=10)

            ctk.CTkButton(
                btn_frame, 
                text="상세 보기", 
                width=80, 
                height=30,
                fg_color=COLORS["bg_light"], 
                hover_color=COLORS["bg_light_hover"],
                text_color=COLORS["text"],
                command=lambda m=model_name, q=qty: self.open_serial_popup(m, q)
            ).pack()

        footer_frame = ctk.CTkFrame(parent, fg_color="transparent")
        footer_frame.pack(pady=20)

        ctk.CTkButton(footer_frame, text="닫기", command=self.destroy, fg_color=COLORS["bg_light"], hover_color=COLORS["bg_light_hover"]).pack(side="left", padx=5)
        ctk.CTkButton(footer_frame, text="요청 삭제", command=self.delete_entry, fg_color=COLORS["danger"], hover_color=COLORS["danger_hover"]).pack(side="left", padx=5)

    def delete_entry(self):
        if messagebox.askyesno("삭제 확인", f"정말로 요청 번호 [{self.req_no}]의 모든 데이터를 삭제하시겠습니까?\n이 작업은 되돌릴 수 없습니다.", parent=self):
            success, msg = self.dm.delete_request(self.req_no)
            if success:
                messagebox.showinfo("삭제 완료", "데이터가 성공적으로 삭제되었습니다.", parent=self.master)
                self.destroy()
                self.refresh_callback()
            else:
                messagebox.showerror("삭제 실패", msg, parent=self)

    def open_serial_popup(self, model, qty):
        popup = None
        def on_save_callback(model_name, data_list):
            if popup: popup.attributes("-topmost", False)
            self.attributes("-topmost", False)

            self.dm.update_serial_list(self.req_no, model_name, data_list)
            success, msg = self.dm.save_to_excel()
            
            target_parent = popup if popup else self

            if success:
                if self.refresh_callback: self.refresh_callback()
                messagebox.showinfo("저장 완료", "수정된 내용이 저장되었습니다.", parent=target_parent)
                self.destroy()
            else:
                messagebox.showerror("저장 실패", msg, parent=target_parent)
                if popup: popup.attributes("-topmost", True)
                self.attributes("-topmost", True)

        popup = SerialInputPopup(self, self.dm, self.req_no, model, qty, on_save_callback)