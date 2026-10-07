import tkinter as tk
from datetime import datetime
from tkinter import messagebox

import customtkinter as ctk
import pandas as pd

from styles import COLORS, FONT_FAMILY, FONTS


class KanbanView(ctk.CTkFrame):
    def __init__(self, parent, data_manager, popup_manager):
        super().__init__(parent, fg_color="transparent")
        self.dm = data_manager
        self.pm = popup_manager

        # 상태 정의 및 표시 순서
        self.columns = {
            "생산 접수": {"color": COLORS["primary"], "bg": COLORS["bg_dark"]},
            "대기":     {"color": COLORS["warning"], "bg": COLORS["bg_dark"]},
            "생산중":   {"color": COLORS["success"], "bg": COLORS["bg_dark"]},
            "중지": {"color": COLORS["danger"],  "bg": COLORS["bg_dark"]},
            "완료":     {"color": COLORS["text_dim"], "bg": COLORS["bg_dark"]}
        }
        
        # UI 요소 저장소
        self.column_frames = {}  # { "상태명": scrollable_frame }
        self.cards = {}          # { req_no: card_widget }

        # 드래그 앤 드롭 상태
        self.drag_data = {
            "item": None, "req_no": None, "text": None, "window": None, "start_status": None
        }
        self.click_timer = None
        self.drag_started = False

        self.create_widgets()
        self.refresh_data()

    def destroy(self):
        if self.click_timer:
            self.after_cancel(self.click_timer)
            self.click_timer = None
        super().destroy()

    def create_widgets(self):
        toolbar = ctk.CTkFrame(self, height=50, fg_color="transparent")
        toolbar.pack(fill="x", padx=20, pady=(10, 0))

        ctk.CTkLabel(toolbar, text="📋 Kanban Board", font=FONTS["title"], text_color=COLORS["text"]).pack(side="left")

        ctk.CTkButton(
            toolbar, text="🔄 새로고침", width=80, height=32,
            fg_color=COLORS["bg_medium"], hover_color=COLORS["bg_light"], text_color=COLORS["text"],
            command=self.refresh_data, font=FONTS["main"]
        ).pack(side="right")

        self.board_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.board_frame.pack(fill="both", expand=True, padx=10, pady=10)
        self.board_frame.grid_rowconfigure(0, weight=1)

        for i, (status, style) in enumerate(self.columns.items()):
            self.board_frame.grid_columnconfigure(i, weight=1, uniform="col")
            
            col_container = ctk.CTkFrame(self.board_frame, fg_color=style["bg"], corner_radius=10, border_width=1, border_color=COLORS["border"])
            col_container.grid(row=0, column=i, sticky="nsew", padx=5, pady=5)
            col_container.status_tag = status

            header = ctk.CTkFrame(col_container, height=40, fg_color="transparent")
            header.pack(fill="x", padx=10, pady=5)
            
            dot = ctk.CTkLabel(header, text="●", font=(FONT_FAMILY, 14), text_color=style["color"])
            dot.pack(side="left", padx=(0, 5))
            
            title = ctk.CTkLabel(header, text=status, font=FONTS["header"], text_color=COLORS["text"])
            title.pack(side="left")
            
            count_badge = ctk.CTkLabel(header, text="0", width=24, height=24, fg_color=COLORS["bg_medium"], corner_radius=12, font=(FONT_FAMILY, 10, "bold"), text_color=COLORS["text"])
            count_badge.pack(side="right")
            
            scroll_frame = ctk.CTkScrollableFrame(col_container, fg_color="transparent")
            scroll_frame.pack(fill="both", expand=True, padx=5, pady=5)
            
            self.column_frames[status] = {
                "frame": scroll_frame,
                "badge": count_badge,
                "container": col_container
            }

    def refresh_data(self):
        df = self.dm.df
        if df.empty: return

        for status in self.column_frames:
            for widget in self.column_frames[status]["frame"].winfo_children():
                widget.destroy()

        status_series = df['Status'].fillna('').astype(str).str.strip()
        
        for status in self.columns.keys():
            target_df = pd.DataFrame()
            if status == "중지":
                target_df = df[status_series.isin(['Hold','중지'])].copy()
            else:
                target_df = df[status_series == status].copy()
            
            if not target_df.empty:
                # 기본적으로 번호 내림차순(최신순) 정렬
                if "번호" in target_df.columns:
                    # 번호 컬럼을 숫자로 변환하여 정렬
                    target_df["_sort_helper"] = pd.to_numeric(target_df["번호"], errors='coerce')
                    target_df = target_df.sort_values(by="_sort_helper", ascending=False)
                    
                    # [핵심 수정] "완료" 상태인 경우 상위 10건만 유지
                    if status == "완료":
                        # 중복된 번호를 제거한 후 상위 10개 번호 추출
                        unique_nos = target_df["번호"].unique()
                        if len(unique_nos) > 10:
                            top_10_nos = unique_nos[:10]
                            target_df = target_df[target_df["번호"].isin(top_10_nos)]

            unique_groups = target_df['번호'].unique() if "번호" in target_df.columns else []
            count = len(unique_groups)
            
            # 배지에 개수 표시 (완료인 경우 '10+' 등으로 표시할 수도 있음)
            badge_text = str(count)
            if status == "완료" and count == 10: # 정확히 10개라면 실제로는 더 있을 수 있음
                 # 전체 완료 건수를 따로 계산해서 보여줄 수도 있지만, 여기선 화면 표시 개수로 통일
                 pass

            self.column_frames[status]["badge"].configure(text=badge_text)

            self.create_cards(status, target_df)

    def create_cards(self, status, df):
        parent = self.column_frames[status]["frame"]
        if df.empty: return

        # df는 이미 정렬된 상태임 (refresh_data에서 처리)
        unique_req_nos = df['번호'].unique() # pandas unique는 출현 순서 유지

        for req_no in unique_req_nos:
            group_df = df[df['번호'] == req_no]
            if group_df.empty: continue

            first_row = group_df.iloc[0]
            comp = str(first_row['업체명'])
            date = str(first_row['출고예정일']) if pd.notna(first_row['출고예정일']) else "-"
            if status == "생산 접수": date = str(first_row['출고요청일'])
            if status == "완료": date = str(first_row['출고일']) # 완료일 경우 출고일 표시

            card = ctk.CTkFrame(parent, fg_color=COLORS["bg_medium"], corner_radius=6, border_width=1, border_color=COLORS["border"])
            card.pack(fill="x", pady=4, padx=2)
            
            top_row = ctk.CTkFrame(card, fg_color="transparent", height=20)
            top_row.pack(fill="x", padx=8, pady=(8, 2))
            
            ctk.CTkLabel(top_row, text=comp, font=(FONT_FAMILY, 11, "bold"), text_color=COLORS["primary"]).pack(side="left")
            
            item_count = len(group_df)
            count_text = f"{item_count}종" if item_count > 1 else "1종"
            ctk.CTkLabel(top_row, text=count_text, font=(FONT_FAMILY, 10), text_color=COLORS["text_dim"]).pack(side="right")
            
            mid_row = ctk.CTkFrame(card, fg_color="transparent")
            mid_row.pack(fill="x", padx=8, pady=2)
            
            for _, row in group_df.iterrows():
                model = str(row['모델명'])
                qty = str(row['수량'])
                item_text = f"• {model} ({qty})"
                ctk.CTkLabel(mid_row, text=item_text, font=(FONT_FAMILY, 11), text_color=COLORS["text"], wraplength=180, justify="left", anchor="w").pack(fill="x", anchor="w")
            
            bot_row = ctk.CTkFrame(card, fg_color="transparent")
            bot_row.pack(fill="x", padx=8, pady=(5, 8))
            ctk.CTkLabel(bot_row, text=f"No.{req_no}", font=(FONT_FAMILY, 10), text_color=COLORS["text_dim"]).pack(side="left")
            
            date_color = COLORS["text_dim"]
            if status == "생산중": date_color = COLORS["success"]
            ctk.CTkLabel(bot_row, text=date, font=(FONT_FAMILY, 10), text_color=date_color).pack(side="right")

            drag_text = f"[{req_no}] {comp} ({item_count}종)"
            widgets_to_bind = [card, top_row, mid_row, bot_row] + top_row.winfo_children() + mid_row.winfo_children() + bot_row.winfo_children()
            
            for w in widgets_to_bind:
                w.bind("<Button-1>", lambda e, r=req_no, s=status, t=drag_text, w_item=card: self.start_drag(e, r, s, t, w_item))
                w.bind("<B1-Motion>", self.do_drag)
                w.bind("<ButtonRelease-1>", self.stop_drag)
                w.bind("<Double-1>", lambda e, r=req_no: self.on_card_double_click(r))

    def on_card_double_click(self, req_no):
        status = self.dm.get_status_by_req_no(req_no)
        if status == "생산중": self.pm.open_complete_popup(req_no)
        elif status == "완료": self.pm.open_completed_view_popup(req_no)
        else: self.pm.open_schedule_popup(req_no)

    def _start_drag_window(self, text):
        self.drag_started = True
        if self.drag_data["window"] is None:
            self.drag_data["window"] = ctk.CTkToplevel(self)
            self.drag_data["window"].overrideredirect(True)
            self.drag_data["window"].attributes("-topmost", True)
            self.drag_data["window"].attributes("-alpha", 0.7)
            lbl = ctk.CTkLabel(self.drag_data["window"], text=text, fg_color=COLORS["primary"], text_color="white", corner_radius=5, padx=10, pady=5, font=FONTS["main"])
            lbl.pack()
        x, y = self.winfo_pointerxy()
        self.drag_data["window"].geometry(f"+{x+15}+{y+15}")

    def start_drag(self, event, req_no, status, text, widget):
        self.drag_data.update({"item": widget, "req_no": req_no, "start_status": status, "text": text})
        self.drag_started = False
        if self.click_timer: self.after_cancel(self.click_timer)
        self.click_timer = self.after(150, lambda: self._start_drag_window(text))

    def do_drag(self, event):
        if self.drag_started and self.drag_data["window"]:
            x, y = self.winfo_pointerxy()
            self.drag_data["window"].geometry(f"+{x+15}+{y+15}")

    def stop_drag(self, event):
        if self.click_timer:
            self.after_cancel(self.click_timer)
            self.click_timer = None

        if self.drag_started:
            if self.drag_data["window"]:
                self.drag_data["window"].destroy()
                self.drag_data["window"] = None
            
            x, y = self.winfo_pointerxy()
            target_widget = self.winfo_containing(x, y)
            target_status = self.find_target_column(target_widget)
            
            req_no = self.drag_data["req_no"]
            start_status = self.drag_data["start_status"]

            if target_status and target_status != start_status:
                self.handle_status_change(req_no, start_status, target_status)
            
        self.drag_data = {"item": None, "req_no": None, "start_status": None, "text": None, "window": None}
        self.drag_started = False

    def find_target_column(self, widget):
        current = widget
        while current:
            if hasattr(current, "status_tag"): return current.status_tag
            try:
                current = current.master
                if current == self or current is None: break
            except: break
        return None

    def handle_status_change(self, req_no, from_status, to_status):
        success = False
        msg = ""
        if to_status == "완료":
            self.pm.open_complete_popup(req_no)
            return
        elif to_status == "생산중":
            today = datetime.now().strftime("%Y-%m-%d")
            success, msg = self.dm.update_production_schedule(req_no, today)
        elif to_status == "중지":
            success, msg = self.dm.update_status_to_hold(req_no)
        elif to_status == "대기":
            success, msg = self.dm.update_status_to_waiting(req_no, reason="칸반 보드 이동")
        elif to_status == "생산 접수":
            messagebox.showwarning("알림", "생산 접수 상태로 되돌릴 수 없습니다.")
            return

        if success: self.refresh_data()
        elif msg: messagebox.showerror("실패", msg)