import os
import re
import tkinter as tk
from tkinter import messagebox
import customtkinter as ctk

try:
    from tkinterdnd2 import DND_FILES
    DND_AVAILABLE = True
except ImportError:
    DND_AVAILABLE = False

from styles import COLORS, FONT_FAMILY, FONTS

class MemoSidebar:
    def __init__(self, parent, data_manager, req_no):
        self.parent = parent
        self.dm = data_manager
        self.req_no = req_no
        self.memo_scroll = None
        self.memo_entry = None
        
        # [신규] 답장 및 스크롤 기능을 위한 상태 변수
        self.reply_target = None  # 현재 답장 대상 메모 객체
        self.memo_widgets = {}    # 타임스탬프: 위젯 매핑 (스크롤 이동용)
        self.memos_data = []      # 전체 메모 데이터 (원본 내용 조회용)
        self.reply_context_frame = None # 답장 컨텍스트 UI
        self.current_context_menu = None # [신규] 현재 열린 컨텍스트 메뉴

        self._create_ui()

    def _create_ui(self):
        header = ctk.CTkFrame(self.parent, fg_color="transparent", height=50)
        header.pack(fill="x", padx=15, pady=(15, 10))
        ctk.CTkLabel(header, text="작업 메모", font=FONTS["header"], text_color=COLORS["text"]).pack(side="left")

        self.memo_scroll = ctk.CTkScrollableFrame(self.parent, fg_color="transparent")
        self.memo_scroll.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        input_container = ctk.CTkFrame(self.parent, fg_color="transparent")
        input_container.pack(fill="x", padx=15, pady=(0, 20), side="bottom")

        # [신규] 답장 컨텍스트 프레임 (초기에는 숨김)
        self.reply_context_frame = ctk.CTkFrame(input_container, fg_color=COLORS["bg_medium"], corner_radius=6)
        # pack은 _reply_memo에서 수행

        if DND_AVAILABLE:
            guide_text = "메시지를 입력하거나 파일을 드래그하세요."
        else:
            guide_text = "메시지를 입력하세요."
            
        ctk.CTkLabel(input_container, text=guide_text, font=(FONT_FAMILY, 10), text_color=COLORS["text_dim"]).pack(anchor="w", padx=2, pady=(0,2))

        self.memo_entry = ctk.CTkTextbox(input_container, height=60, font=FONTS["main"], fg_color=COLORS["bg_dark"], border_color=COLORS["border"], border_width=1)
        self.memo_entry.pack(fill="x", pady=(0, 5))
        
        self.memo_entry.bind("<Return>", self._handle_enter_key)
        
        if DND_AVAILABLE:
            try:
                self.memo_entry.drop_target_register(DND_FILES)
                self.memo_entry.dnd_bind('<<Drop>>', self._on_drop_file)
            except Exception as e:
                print(f"DnD bind error: {e}")

        btn_add = ctk.CTkButton(input_container, text="메모 등록", height=30, fg_color=COLORS["primary"], hover_color=COLORS["primary_hover"], command=self._add_memo)
        btn_add.pack(fill="x")

        self.refresh_memo_list()

    def _on_drop_file(self, event):
        files = event.data
        if not files: return
        
        paths = re.findall(r'\{.*?\}|\S+', files)
        
        success_count = 0
        error_msg = ""

        for file_path in paths:
            if file_path.startswith('{') and file_path.endswith('}'):
                file_path = file_path[1:-1]
            
            if os.path.exists(file_path):
                saved_path, error = self.dm.save_attachment(file_path)
                if saved_path:
                    current_text = self.memo_entry.get("1.0", "end").strip()
                    new_text = f"[파일첨부] {os.path.basename(saved_path)}\n(경로: {saved_path})"
                    
                    if current_text:
                        self.memo_entry.insert("end", "\n" + new_text)
                    else:
                        self.memo_entry.insert("1.0", new_text)
                    success_count += 1
                else:
                    error_msg += f"\n{os.path.basename(file_path)}: {error}"
        
        if error_msg:
             messagebox.showerror("일부 파일 저장 실패", error_msg, parent=self.parent)

    def _handle_enter_key(self, event):
        if event.state & 0x0001: 
            return 
        else:
            self._add_memo()
            return "break" 

    def _add_memo(self):
        text = self.memo_entry.get("1.0", "end").strip()
        if not text:
            return

        # [신규] 답장 중이라면 태그 추가 및 원본 읽음 처리
        if self.reply_target:
            timestamp = self.reply_target['일시']
            original_content = self.reply_target['내용']
            
            # 원본 메모 읽음 처리
            self.dm.memo_manager.update_memo_check(self.req_no, timestamp, original_content, 'Y')
            
            text = f"[REPLY:{timestamp}]{text}"
            self._cancel_reply() # 답장 상태 초기화

        success, msg = self.dm.memo_manager.add_memo(self.req_no, text)
        if success:
            self.memo_entry.delete("1.0", "end")
            self.refresh_memo_list()
        else:
            messagebox.showerror("오류", f"메모 저장 실패: {msg}", parent=self.parent)

    def refresh_memo_list(self):
        for widget in self.memo_scroll.winfo_children():
            widget.destroy()
        
        self.memo_widgets.clear() # 위젯 맵 초기화

        self.memos_data = self.dm.memo_manager.get_memos(self.req_no)
        
        if not self.memos_data:
            ctk.CTkLabel(self.memo_scroll, text="등록된 메모가 없습니다.", text_color=COLORS["text_dim"], font=FONTS["small"]).pack(pady=20)
            return

        for memo in self.memos_data:
            self._create_memo_item(memo)
            
        # 스크롤 맨 아래로 이동
        self.memo_scroll.after(100, lambda: self.memo_scroll._parent_canvas.yview_moveto(1.0))

    def _create_memo_item(self, memo):
        is_checked = str(memo.get('확인', 'N')) == 'Y'
        bg_color = COLORS["bg_dark"]
        if is_checked:
            bg_color = "#2C3E50" 
        
        card = ctk.CTkFrame(self.memo_scroll, fg_color=bg_color, corner_radius=12)
        card.pack(fill="x", pady=5, padx=5, anchor="w") 

        # [신규] 위젯 등록 (스크롤 이동용)
        self.memo_widgets[str(memo['일시'])] = card

        card.bind("<Button-3>", lambda e, m=memo: self._show_context_menu(e, m))

        # 헤더
        header_frame = ctk.CTkFrame(card, fg_color="transparent", height=15)
        header_frame.pack(fill="x", padx=12, pady=(8, 2))
        header_frame.bind("<Button-3>", lambda e, m=memo: self._show_context_menu(e, m))

        try:
            date_only = str(memo['일시']).split()[0]
        except:
            date_only = str(memo['일시'])
        
        read_mark = "✓" if is_checked else ""
        header_text = f"{date_only} | {memo['작업자']} {read_mark}"
        header_lbl = ctk.CTkLabel(header_frame, text=header_text, font=(FONT_FAMILY, 11), text_color=COLORS["text_dim"])
        header_lbl.pack(side="left")
        header_lbl.bind("<Button-3>", lambda e, m=memo: self._show_context_menu(e, m))

        # 내용 처리
        raw_content = memo['내용']
        display_content = raw_content
        reply_timestamp = None

        # [신규] 답장 태그 파싱
        if raw_content.startswith("[REPLY:"):
            end_idx = raw_content.find("]")
            if end_idx != -1:
                reply_timestamp = raw_content[7:end_idx]
                display_content = raw_content[end_idx+1:]
                
                # 인용 블록 렌더링
                self._render_quote_block(card, reply_timestamp)

        # 파일 파싱 로직
        file_path = None
        file_display_text = display_content

        if "[파일첨부]" in display_content and "(경로:" in display_content:
            try:
                lines = display_content.splitlines()
                file_display_text = lines[0] 
                for line in lines:
                    line = line.strip()
                    if line.startswith("(경로:"):
                        temp_path = line[5:].strip()
                        if temp_path.endswith(")"):
                            file_path = temp_path[:-1]
                        else:
                            file_path = temp_path
                        break
                if not file_path:
                    start_idx = display_content.find("(경로:") + 5
                    end_idx = display_content.rfind(")") 
                    if start_idx > 4 and end_idx > start_idx:
                        file_path = display_content[start_idx:end_idx].strip()
            except Exception as e:
                print(f"Path parsing error: {e}")
        
        if file_path:
             btn_file = ctk.CTkButton(
                card, 
                text=f"📁 {file_display_text}", 
                fg_color=COLORS["bg_medium"], 
                hover_color=COLORS["bg_light"],
                text_color=COLORS["primary"],
                anchor="w",
                height=28,
                command=lambda p=file_path: self._open_pdf_file(p) 
            )
             btn_file.pack(fill="x", padx=10, pady=(5, 10))
             btn_file.bind("<Button-3>", lambda e, m=memo: self._show_context_menu(e, m))
        else:
            content_lbl = ctk.CTkLabel(card, text=display_content, font=FONTS["main"], text_color=COLORS["text"], wraplength=230, justify="left")
            content_lbl.pack(anchor="w", padx=12, pady=(0, 10))
            content_lbl.bind("<Button-3>", lambda e, m=memo: self._show_context_menu(e, m))

    def _render_quote_block(self, parent, timestamp):
        # 원본 메시지 찾기
        original_memo = next((m for m in self.memos_data if str(m['일시']) == timestamp), None)
        
        # [수정] 높이 고정 및 텍스트 줄임 처리
        quote_frame = ctk.CTkFrame(parent, fg_color=COLORS["bg_medium"], corner_radius=4, border_width=0, height=45)
        quote_frame.pack(fill="x", padx=10, pady=(5, 0))
        quote_frame.pack_propagate(False) # 높이 고정
        
        # 왼쪽 강조선
        line = ctk.CTkFrame(quote_frame, width=3, fg_color=COLORS["primary"])
        line.pack(side="left", fill="y", padx=(0, 5))
        
        content_frame = ctk.CTkFrame(quote_frame, fg_color="transparent")
        content_frame.pack(side="left", fill="both", expand=True, pady=2)
        
        if original_memo:
            user = original_memo['작업자']
            content = original_memo['내용']
            # 답장 태그 제거하고 순수 내용만 표시
            if content.startswith("[REPLY:"):
                end_idx = content.find("]")
                if end_idx != -1:
                    content = content[end_idx+1:]
            
            # [수정] 줄바꿈 제거 및 길이 제한
            content = content.replace("\n", " ")
            if len(content) > 25: content = content[:25] + "..."
            
            ctk.CTkLabel(content_frame, text=f"답장: {user}", font=(FONT_FAMILY, 10, "bold"), text_color=COLORS["text_dim"]).pack(anchor="w")
            ctk.CTkLabel(content_frame, text=content, font=(FONT_FAMILY, 10), text_color=COLORS["text_dim"]).pack(anchor="w")
            
            # 클릭 시 스크롤 이동 이벤트
            for widget in [quote_frame, content_frame, line] + content_frame.winfo_children():
                widget.bind("<Button-1>", lambda e, t=timestamp: self._scroll_to_memo(t))
        else:
            ctk.CTkLabel(content_frame, text="삭제된 메시지입니다.", font=(FONT_FAMILY, 10), text_color=COLORS["text_dim"]).pack(anchor="w")

    def _scroll_to_memo(self, timestamp):
        target_widget = self.memo_widgets.get(str(timestamp))
        if target_widget:
            # 스크롤 위치 계산
            # 1. 전체 스크롤 영역 높이
            scroll_height = self.memo_scroll._parent_canvas.bbox("all")[3]
            # 2. 타겟 위젯의 Y 좌표
            target_y = target_widget.winfo_y()
            # 3. 비율 계산
            if scroll_height > 0:
                pos = target_y / scroll_height
                self.memo_scroll._parent_canvas.yview_moveto(pos)
                
                # 깜빡임 효과 (선택사항)
                original_color = target_widget.cget("fg_color")
                target_widget.configure(fg_color=COLORS["primary"])
                self.parent.after(300, lambda: target_widget.configure(fg_color=original_color))

    def _show_context_menu(self, event, memo):
        # [신규] 커스텀 컨텍스트 메뉴 사용
        # 기존 메뉴가 있다면 닫기
        if self.current_context_menu:
            try:
                self.current_context_menu.destroy()
            except:
                pass
            self.current_context_menu = None

        is_checked = str(memo.get('확인', 'N')) == 'Y'
        read_label = "안읽음 표시" if is_checked else "읽음 표시"
        
        menu_items = [
            ("답장", lambda: self._reply_memo(memo), None),
            (read_label, lambda: self._toggle_check_context(memo), None),
            ("separator", None, None),
            ("삭제", lambda: self._delete_memo_context(memo), COLORS["danger"])
        ]
        
        self.current_context_menu = MemoContextMenu(self.parent, menu_items)
        self.current_context_menu.show(event.x_root, event.y_root)

    def _reply_memo(self, memo):
        self.reply_target = memo
        
        # 컨텍스트 프레임 내용 구성
        for widget in self.reply_context_frame.winfo_children():
            widget.destroy()
            
        content = memo['내용']
        if content.startswith("[REPLY:"):
             end_idx = content.find("]")
             if end_idx != -1: content = content[end_idx+1:]
        
        # [수정] 줄바꿈 제거 및 길이 제한
        content = content.replace("\n", " ")
        if len(content) > 30: content = content[:30] + "..."
        
        info_frame = ctk.CTkFrame(self.reply_context_frame, fg_color="transparent")
        info_frame.pack(side="left", fill="both", expand=True, padx=10, pady=5)
        
        ctk.CTkLabel(info_frame, text=f"답장: {memo['작업자']}", font=(FONT_FAMILY, 11, "bold"), text_color=COLORS["primary"]).pack(anchor="w")
        
        # [수정] wraplength 추가 및 텍스트 길이 제한
        ctk.CTkLabel(info_frame, text=content, font=(FONT_FAMILY, 11), text_color=COLORS["text_dim"], wraplength=250).pack(anchor="w")
        
        btn_close = ctk.CTkButton(self.reply_context_frame, text="×", width=25, height=25, fg_color="transparent", hover_color=COLORS["bg_dark"], text_color=COLORS["text"], command=self._cancel_reply)
        btn_close.pack(side="right", padx=5)
        
        self.reply_context_frame.pack(fill="x", pady=(0, 5), before=self.memo_entry) # 입력창 위에 표시
        self.memo_entry.focus_set()

    def _cancel_reply(self):
        self.reply_target = None
        self.reply_context_frame.pack_forget()

    def _toggle_check_context(self, memo):
        current_status = str(memo.get('확인', 'N'))
        new_status = 'N' if current_status == 'Y' else 'Y'
        success, msg = self.dm.memo_manager.update_memo_check(self.req_no, memo['일시'], memo['내용'], new_status)
        if success:
            self.refresh_memo_list()
        else:
            messagebox.showerror("오류", f"상태 변경 실패: {msg}", parent=self.parent)

    def _delete_memo_context(self, memo):
        if messagebox.askyesno("메모 삭제", "선택한 메모를 삭제하시겠습니까?", parent=self.parent):
            success, msg = self.dm.memo_manager.delete_memo(self.req_no, memo['일시'], memo['내용'])
            if success:
                self.refresh_memo_list()
            else:
                messagebox.showerror("오류", msg, parent=self.parent)

    def _open_pdf_file(self, path):
        if not path or str(path).strip() == "-" or str(path).strip() == "":
            messagebox.showinfo("알림", "등록된 파일 경로가 없습니다.", parent=self.parent)
            return
            
        try:
            path = str(path).replace("₩", "\\")
            path = os.path.normpath(path)
        except:
            pass

        if os.path.exists(path):
            try:
                os.startfile(path)
            except Exception as e:
                messagebox.showerror("에러", f"파일을 여는 중 오류가 발생했습니다.\n{e}", parent=self.parent)
        else:
            messagebox.showerror("에러", f"파일을 찾을 수 없습니다.\n경로: {path}", parent=self.parent)


class MemoContextMenu(ctk.CTkToplevel):
    def __init__(self, parent, menu_items):
        super().__init__(parent)
        self.withdraw()
        self.overrideredirect(True)
        # [수정] 부모 창 위에 뜨도록 transient 설정
        self.transient(parent)
        
        # 배경 및 테두리 설정
        self.frame = ctk.CTkFrame(self, fg_color=COLORS["bg_dark"])
        self.frame.pack(fill="both", expand=True)
        
        for label, command, text_color in menu_items:
            if label == "separator":
                ctk.CTkFrame(self.frame, height=1, width=1, fg_color=COLORS["text_dim"]).pack(fill="x", padx=10, pady=4)
            else:
                btn = ctk.CTkButton(
                    self.frame, 
                    text=label, 
                    fg_color="transparent", 
                    hover_color=COLORS["bg_medium"], 
                    text_color=text_color if text_color else COLORS["text"],
                    anchor="w",
                    width=100,
                    height=26,
                    font=FONTS["main"],
                    command=lambda cmd=command: self._on_click(cmd)
                )
                btn.pack(fill="x", padx=2, pady=1)
        
        # 포커스 아웃 시 닫기 (약간의 지연 필요)
        self.after(100, lambda: self.bind("<FocusOut>", lambda e: self.destroy()))
        self.bind("<Escape>", lambda e: self.destroy())

    def _on_click(self, command):
        if command: command()
        self.destroy()

    def show(self, x, y):
        self.geometry(f"+{x}+{y}")
        self.deiconify()
        self.focus_set()
        # [신규] 외부 클릭 감지
        self.after(100, lambda: self.bind_all("<Button-1>", self._check_outside_click))

    def _check_outside_click(self, event):
        try:
            # 클릭된 위젯이 메뉴 내부인지 확인
            widget = event.widget
            if str(widget).startswith(str(self)):
                return
            
            # 메뉴 영역 밖 클릭 시 닫기
            self.unbind_all("<Button-1>")
            self.destroy()
        except:
            self.destroy()

    def destroy(self):
        try:
            self.unbind_all("<Button-1>")
        except:
            pass
        super().destroy()
