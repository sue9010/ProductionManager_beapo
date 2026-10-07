from tkinter import messagebox

import customtkinter as ctk

from styles import COLORS, FONTS


class SerialInputPopup(ctk.CTkToplevel):
    def __init__(self, parent, data_manager, req_no, model_name, qty, callback_save):
        super().__init__(parent)
        self.dm = data_manager
        self.req_no = req_no
        self.model_name = model_name
        try:
            self.qty = int(qty)
        except:
            self.qty = 0
        self.callback_save = callback_save
        
        self.title(f"상세 시리얼 입력 - {model_name} (총 {self.qty}개)")
        self.geometry("600x700")
        
        # 팝업 설정
        self.transient(parent)
        self.grab_set()
        self.attributes("-topmost", True)
        
        self.entry_rows = [] # {seq, sn_entry, lens_entry, note_entry}
        
        self.create_widgets()
        self.load_initial_data()

    def create_widgets(self):
        # 1. 헤더 (기능 버튼)
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=15, pady=10)
        
        ctk.CTkLabel(header, text=f"수량: {self.qty}개", font=FONTS["header"]).pack(side="left")
        
        btn_box = ctk.CTkFrame(header, fg_color="transparent")
        btn_box.pack(side="right")
        
        # 자동 채우기 버튼
        ctk.CTkButton(btn_box, text="자동 채우기 (Hex)", width=120, command=self.open_autofill_dialog, 
                      fg_color=COLORS["bg_medium"], text_color=COLORS["text"]).pack(side="left", padx=5)

        # 2. 스크롤 영역 (입력 폼)
        self.scroll = ctk.CTkScrollableFrame(self, fg_color=COLORS["bg_medium"])
        self.scroll.pack(fill="both", expand=True, padx=15, pady=(0, 15))
        
        # 헤더 라벨
        h_frame = ctk.CTkFrame(self.scroll, fg_color=COLORS["bg_dark"], height=30)
        h_frame.pack(fill="x", pady=(0, 5))
        ctk.CTkLabel(h_frame, text="No.", width=40, font=FONTS["main_bold"]).pack(side="left", padx=5)
        ctk.CTkLabel(h_frame, text="시리얼 번호", width=180, font=FONTS["main_bold"]).pack(side="left", padx=5)
        ctk.CTkLabel(h_frame, text="렌즈 업체", width=100, font=FONTS["main_bold"]).pack(side="left", padx=5)
        ctk.CTkLabel(h_frame, text="비고 (도면 파일명 등)", font=FONTS["main_bold"]).pack(side="left", padx=5)

        # 입력 행 생성
        for i in range(1, self.qty + 1):
            row_frame = ctk.CTkFrame(self.scroll, fg_color="transparent")
            row_frame.pack(fill="x", pady=2)
            
            # 순번
            ctk.CTkLabel(row_frame, text=str(i), width=40, text_color=COLORS["text_dim"]).pack(side="left", padx=5)
            
            # 시리얼 입력
            sn_entry = ctk.CTkEntry(row_frame, width=180, placeholder_text="SN...")
            sn_entry.pack(side="left", padx=5)
            
            # 렌즈 입력
            lens_entry = ctk.CTkEntry(row_frame, width=100, placeholder_text="렌즈")
            lens_entry.pack(side="left", padx=5)
            
            # 비고 입력
            note_entry = ctk.CTkEntry(row_frame, width=150)
            note_entry.pack(side="left", padx=5, fill="x", expand=True)
            
            self.entry_rows.append({
                "seq": i,
                "sn": sn_entry,
                "lens": lens_entry,
                "note": note_entry
            })

        # 3. 하단 저장 버튼
        footer = ctk.CTkFrame(self, fg_color="transparent")
        footer.pack(fill="x", padx=15, pady=15)
        
        ctk.CTkButton(footer, text="취소", fg_color=COLORS["bg_light"], text_color=COLORS["text"], 
                      command=self.destroy).pack(side="left")
                      
        ctk.CTkButton(footer, text="입력 완료 (임시 저장)", fg_color=COLORS["primary"], 
                      command=self.save_temp).pack(side="right")

    def load_initial_data(self):
        # 기존 저장된 데이터 불러오기
        saved_list = self.dm.get_serial_list(self.req_no, self.model_name)
        
        # 순번(seq)을 key로 하는 딕셔너리로 변환
        data_map = {}
        for item in saved_list:
            try:
                seq = int(item["순번"])
                data_map[seq] = item
            except: pass
            
        # UI에 값 채우기
        for row in self.entry_rows:
            seq = row["seq"]
            if seq in data_map:
                data = data_map[seq]
                row["sn"].insert(0, str(data.get("시리얼번호", "")))
                row["lens"].insert(0, str(data.get("렌즈업체", "")))
                row["note"].insert(0, str(data.get("비고", "")))

    def open_autofill_dialog(self):
        # 자동 채우기 팝업
        win = ctk.CTkToplevel(self)
        win.title("자동 채우기 (Hex)")
        win.geometry("300x250")
        win.transient(self)
        win.attributes("-topmost", True)
        
        ctk.CTkLabel(win, text="시리얼 번호 규칙 (16진수)", font=FONTS["main_bold"]).pack(pady=(20,5))
        
        f1 = ctk.CTkFrame(win, fg_color="transparent")
        f1.pack(pady=5)
        ctk.CTkLabel(f1, text="Prefix:").pack(side="left", padx=5)
        e_prefix = ctk.CTkEntry(f1, width=100, placeholder_text="공통 번호")
        e_prefix.pack(side="left")
        
        f2 = ctk.CTkFrame(win, fg_color="transparent")
        f2.pack(pady=5)
        ctk.CTkLabel(f2, text="Start Num (Hex):").pack(side="left", padx=5)
        e_start = ctk.CTkEntry(f2, width=80, placeholder_text="ex.001")
        e_start.pack(side="left")
        
        def apply():
            prefix = e_prefix.get()
            start_num_str = e_start.get().strip()
            
            try:
                # [수정] 16진수로 해석 (예: 'A' -> 10, '10' -> 16)
                if not start_num_str:
                    start_num = 1
                else:
                    start_num = int(start_num_str, 16)
            except:
                start_num = 1
                
            for i, row in enumerate(self.entry_rows):
                current_num = start_num + i
                # [수정] 3자리 16진수 대문자 포맷팅 (00A, 00B... 00F, 010...)
                sn_text = f"{prefix}{current_num:03X}"
                
                # 기존 값이 없을 때만 채우기
                if not row["sn"].get():
                    row["sn"].insert(0, sn_text)
                    
            win.destroy()
            
        ctk.CTkButton(win, text="적용", command=apply).pack(pady=20)

    def save_temp(self):
        # 입력된 데이터를 리스트로 변환
        result_list = []
        for row in self.entry_rows:
            sn_val = row["sn"].get().strip()
            # 빈 값이라도 순번 유지를 위해 저장
            
            result_list.append({
                "요청번호": str(self.req_no),
                "순번": row["seq"],
                "모델명": self.model_name,
                "시리얼번호": sn_val,
                "렌즈업체": row["lens"].get().strip(),
                "비고": row["note"].get().strip()
            })
            
        # 콜백 함수 호출 (DataManager 업데이트)
        self.callback_save(self.model_name, result_list)
        self.destroy()