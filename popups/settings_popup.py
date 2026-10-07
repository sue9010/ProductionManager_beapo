from tkinter import filedialog, messagebox, simpledialog

import customtkinter as ctk

from config import Config
from styles import COLORS, FONT_FAMILY, FONTS

from .base_popup import BasePopup


class SettingsPopup(BasePopup):
    def __init__(self, parent, data_manager, refresh_callback):
        super().__init__(parent, data_manager, refresh_callback, title="환경 설정", geometry="500x550")
        self.create_widgets()

    def create_widgets(self):
        parent = self.content_frame

        # 1. 테마 설정 섹션
        ctk.CTkLabel(parent, text="테마 설정 (Appearance)", font=FONTS["header"]).pack(pady=(20, 10), padx=20, anchor="w")
        
        theme_frame = ctk.CTkFrame(parent, fg_color="transparent")
        theme_frame.pack(fill="x", padx=20)
        
        self.theme_var = ctk.StringVar(value=self.dm.current_theme)
        
        self.theme_switch = ctk.CTkSegmentedButton(
            theme_frame, 
            values=["Light", "Dark"], 
            variable=self.theme_var,
            command=self.change_theme,
            font=(FONT_FAMILY, 12, "bold"),
            selected_color=COLORS["primary"],
            selected_hover_color=COLORS["primary_hover"]
        )
        self.theme_switch.pack(fill="x")

        # 구분선
        ctk.CTkFrame(parent, height=1, fg_color=COLORS["border"]).pack(fill="x", padx=20, pady=20)

        # 2. 엑셀 파일 경로 설정 섹션
        ctk.CTkLabel(parent, text="엑셀 파일 경로 설정", font=FONTS["header"]).pack(pady=(0, 10), padx=20, anchor="w")

        path_frame = ctk.CTkFrame(parent, fg_color="transparent")
        path_frame.pack(fill="x", padx=20)

        self.path_entry = ctk.CTkEntry(path_frame, width=350, font=(FONT_FAMILY, 12))
        self.path_entry.insert(0, self.dm.current_excel_path)
        self.path_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))

        ctk.CTkButton(path_frame, text="찾기", width=60, command=self.browse_excel, text_color=COLORS["text"], fg_color=COLORS["bg_light"], font=(FONT_FAMILY, 12)).pack(side="right")
        
        # 구분선
        ctk.CTkFrame(parent, height=1, fg_color=COLORS["border"]).pack(fill="x", padx=20, pady=20)

        # 3. 첨부 파일 저장 경로 설정 섹션
        ctk.CTkLabel(parent, text="첨부 파일 저장 폴더 설정", font=FONTS["header"]).pack(pady=(0, 10), padx=20, anchor="w")

        attach_frame = ctk.CTkFrame(parent, fg_color="transparent")
        attach_frame.pack(fill="x", padx=20)

        self.attach_path_entry = ctk.CTkEntry(attach_frame, width=350, font=(FONT_FAMILY, 12))
        self.attach_path_entry.insert(0, self.dm.attachment_dir)
        self.attach_path_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))

        ctk.CTkButton(attach_frame, text="폴더 선택", width=80, command=self.browse_folder, text_color=COLORS["text"],fg_color=COLORS["bg_light"], font=(FONT_FAMILY, 12)).pack(side="right")

        # 구분선
        ctk.CTkFrame(parent, height=1, fg_color=COLORS["border"]).pack(fill="x", padx=20, pady=20)

        # 4. 개발자 모드 설정
        dev_frame = ctk.CTkFrame(parent, fg_color="transparent")
        dev_frame.pack(fill="x", padx=20)
        
        self.dev_var = ctk.BooleanVar(value=self.dm.is_dev_mode)
        
        ctk.CTkSwitch(
            dev_frame, 
            text="개발자 모드 (관리자)", 
            variable=self.dev_var,
            command=self.toggle_dev_mode,
            font=FONTS["main_bold"],
            progress_color=COLORS["danger"]
        ).pack(side="left")

        # 개발자 도구 버튼들 (개발자 모드일 때만 보임)
        self.dev_tools_frame = ctk.CTkFrame(parent, fg_color="transparent")
        if self.dm.is_dev_mode:
            self.dev_tools_frame.pack(fill="x", padx=20, pady=(10, 0))
            
            ctk.CTkButton(self.dev_tools_frame, text="💾 백업 생성", width=120, height=30,
                          fg_color=COLORS["success"], command=self.do_backup).pack(side="left", padx=(0, 10))
            
            ctk.CTkButton(self.dev_tools_frame, text="🧹 로그 정리 (3개월)", width=120, height=30,
                          fg_color=COLORS["warning"], command=self.do_clean_logs).pack(side="left")

        # 5. 하단 저장 버튼
        ctk.CTkButton(parent, text="설정 저장 및 닫기", command=self.save, fg_color=COLORS["primary"], hover_color=COLORS["primary_hover"], font=(FONT_FAMILY, 12, "bold")).pack(side="bottom", pady=20)

    def change_theme(self, new_theme):
        """테마 즉시 변경"""
        ctk.set_appearance_mode(new_theme)

    def browse_excel(self):
        file_path = filedialog.askopenfilename(parent=self, filetypes=[("Excel files", "*.xlsx;*.xls")])
        self.lift()
        if file_path:
            self.path_entry.delete(0, "end")
            self.path_entry.insert(0, file_path)

    def browse_folder(self):
        folder_path = filedialog.askdirectory(parent=self)
        self.lift()
        if folder_path:
            self.attach_path_entry.delete(0, "end")
            self.attach_path_entry.insert(0, folder_path)

    def toggle_dev_mode(self):
        if self.dev_var.get():
            # 켜려고 할 때: 비밀번호 확인
            pwd = simpledialog.askstring("관리자 인증", "관리자 비밀번호를 입력하세요:", show="*", parent=self)
            
            if pwd == Config.DEV_PASSWORD:
                self.dm.set_dev_mode(True)
                messagebox.showinfo("인증 성공", "개발자 모드가 활성화되었습니다.", parent=self)
                # 도구 버튼 보이기
                self.dev_tools_frame.pack(fill="x", padx=20, pady=(10, 0))
                for widget in self.dev_tools_frame.winfo_children(): widget.destroy()
                
                ctk.CTkButton(self.dev_tools_frame, text="💾 백업 생성", width=120, height=30,
                              fg_color=COLORS["success"], command=self.do_backup).pack(side="left", padx=(0, 10))
                
                ctk.CTkButton(self.dev_tools_frame, text="🧹 로그 정리 (3개월)", width=120, height=30,
                              fg_color=COLORS["warning"], command=self.do_clean_logs).pack(side="left")
            else:
                self.dev_var.set(False)
                messagebox.showerror("인증 실패", "비밀번호가 올바르지 않습니다.", parent=self)
        else:
            # 끌 때는 그냥 끔
            self.dm.set_dev_mode(False)
            self.dev_tools_frame.pack_forget()

    def do_backup(self):
        if messagebox.askyesno("백업", "현재 데이터의 백업본을 생성하시겠습니까?", parent=self):
            success, msg = self.dm.create_backup()
            if success:
                messagebox.showinfo("성공", msg, parent=self)
            else:
                messagebox.showerror("실패", msg, parent=self)

    def do_clean_logs(self):
        if messagebox.askyesno("로그 정리", "3개월이 지난 로그 데이터를 삭제하여 파일 크기를 줄이시겠습니까?\n이 작업은 되돌릴 수 없습니다.", parent=self):
            success, msg = self.dm.clean_old_logs()
            if success:
                messagebox.showinfo("성공", msg, parent=self)
            else:
                messagebox.showerror("실패", msg, parent=self)

    def save(self):
        new_path = self.path_entry.get()
        new_theme = self.theme_var.get()
        new_attachment_dir = self.attach_path_entry.get()
        
        if new_path:
            try:
                self.dm.save_config(new_path, new_theme, new_attachment_dir)
                
                messagebox.showinfo("설정 저장", "설정이 저장되었습니다.", parent=self)
                
                self.destroy()
                self.dm.load_config() 
                self.refresh_callback()
            except Exception as e:
                messagebox.showerror("오류", f"설정 저장 실패: {e}", parent=self)
        else:
            messagebox.showwarning("경고", "엑셀 파일 경로를 입력해주세요.", parent=self)
