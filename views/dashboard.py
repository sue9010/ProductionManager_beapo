import tkinter as tk
from datetime import datetime
from tkinter import ttk

import customtkinter as ctk
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from config import Config
from styles import COLORS, FONT_FAMILY, FONTS, get_color_str


class DashboardView(ctk.CTkFrame):
    def __init__(self, parent, data_manager, popup_manager):
        super().__init__(parent, fg_color="transparent")
        self.dm = data_manager
        self.pm = popup_manager

        # 그리드 레이아웃 설정 (2행 2열 구조)
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=0)  # 요약 카드 영역
        self.grid_rowconfigure(1, weight=1)  # 차트 및 리스트 영역

        self.create_widgets()
        self.refresh_data()

    def create_widgets(self):
        # 1. 타이틀
        title_frame = ctk.CTkFrame(self, fg_color="transparent")
        title_frame.grid(row=0, column=0, columnspan=2, sticky="ew", padx=20, pady=(20, 10))

        ctk.CTkLabel(title_frame, text="📊 대시보드", font=FONTS["title"], text_color=COLORS["text"]).pack(side="left")

        ctk.CTkButton(
            title_frame,
            text="🔄 새로고침",
            width=80,
            height=32,
            fg_color=COLORS["bg_medium"],
            hover_color=COLORS["bg_light"],
            text_color=COLORS["text"],
            command=self.refresh_data,
            font=FONTS["main"],
        ).pack(side="right")

        # 2. 요약 카드 영역 (Summary Cards)
        self.cards_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.cards_frame.grid(row=1, column=0, columnspan=2, sticky="ew", padx=10, pady=(0, 20))

        # 4개의 카드를 담을 공간 (균등 분배)
        for i in range(4):
            self.cards_frame.grid_columnconfigure(i, weight=1)

        self.card_widgets = []
        card_titles = ["생산 중", "생산 대기", "중지", "이번달 완료"]
        card_colors = [COLORS["primary"], COLORS["warning"], COLORS["danger"], COLORS["success"]]

        for i, (title, color) in enumerate(zip(card_titles, card_colors)):
            # 테두리 두께를 항상 2로 고정하여 호버 시 크기 변화 방지
            card = ctk.CTkFrame(
                self.cards_frame,
                fg_color=COLORS["bg_medium"],
                corner_radius=10,
                border_width=2,
                border_color=COLORS["border"],
            )
            card.grid(row=0, column=i, sticky="ew", padx=10, pady=5)

            # 카드 내부 레이아웃
            icon_lbl = ctk.CTkLabel(card, text="●", font=("Arial", 16), text_color=color)
            icon_lbl.pack(anchor="ne", padx=10, pady=(5, 0))

            val_lbl = ctk.CTkLabel(card, text="0", font=(FONT_FAMILY, 24, "bold"), text_color=COLORS["text"])
            val_lbl.pack(pady=(0, 5))

            title_lbl = ctk.CTkLabel(card, text=title, font=(FONT_FAMILY, 12), text_color=COLORS["text_dim"])
            title_lbl.pack(pady=(0, 15))

            self.card_widgets.append(val_lbl)  # 값 업데이트를 위해 저장

            # 더블 클릭 이벤트: 카드와 내부 라벨 모두에서 동작
            for w in [card, icon_lbl, val_lbl, title_lbl]:
                w.bind("<Double-1>", lambda e, idx=i: self.on_card_double_click(idx))

        # 3. 하단 컨텐츠 영역 (좌: 차트, 우: 리스트)
        content_frame = ctk.CTkFrame(self, fg_color="transparent")
        content_frame.grid(row=2, column=0, columnspan=2, sticky="nsew", padx=20, pady=(0, 20))
        content_frame.grid_columnconfigure(0, weight=1)
        content_frame.grid_columnconfigure(1, weight=1)
        content_frame.grid_rowconfigure(0, weight=1)

        # [좌측] 현황 차트 프레임
        chart_frame_container = ctk.CTkFrame(
            content_frame,
            fg_color=COLORS["bg_medium"],
            corner_radius=10,
            border_width=1,
            border_color=COLORS["border"],
        )
        chart_frame_container.grid(row=0, column=0, sticky="nsew", padx=(0, 10))

        ctk.CTkLabel(
            chart_frame_container,
            text="진행 상태별 현황",
            font=FONTS["header"],
            text_color=COLORS["text"],
        ).pack(anchor="w", padx=20, pady=15)

        self.chart_area = ctk.CTkFrame(chart_frame_container, fg_color="transparent")
        self.chart_area.pack(fill="both", expand=True, padx=10, pady=10)
        self.canvas = None  # 차트 캔버스 저장용

        # [우측] 금일 출고 예정 및 최근 활동
        right_frame = ctk.CTkFrame(self, fg_color="transparent")
        right_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        right_frame.grid(row=0, column=1, sticky="nsew", padx=(10, 0))
        right_frame.grid_rowconfigure(0, weight=1)
        right_frame.grid_rowconfigure(1, weight=1)
        right_frame.grid_columnconfigure(0, weight=1)

        # 금일 출고 예정 리스트
        today_frame = ctk.CTkFrame(
            right_frame,
            fg_color=COLORS["bg_medium"],
            corner_radius=10,
            border_width=1,
            border_color=COLORS["border"],
        )
        today_frame.grid(row=0, column=0, sticky="nsew", pady=(0, 10))

        header_frame = ctk.CTkFrame(today_frame, fg_color="transparent")
        header_frame.pack(fill="x", padx=20, pady=15)
        ctk.CTkLabel(
            header_frame,
            text="📅 금일 출고 예정",
            font=FONTS["header"],
            text_color=COLORS["text"],
        ).pack(side="left")
        self.today_count_lbl = ctk.CTkLabel(
            header_frame,
            text="0건",
            font=FONTS["main_bold"],
            text_color=COLORS["primary"],
        )
        self.today_count_lbl.pack(side="right")

        self.today_scroll = ctk.CTkScrollableFrame(today_frame, fg_color="transparent")
        self.today_scroll.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        # 최근 활동 로그 (Memo Log 기반)
        log_frame = ctk.CTkFrame(
            right_frame,
            fg_color=COLORS["bg_medium"],
            corner_radius=10,
            border_width=1,
            border_color=COLORS["border"],
        )
        log_frame.grid(row=1, column=0, sticky="nsew", pady=(10, 0))

        ctk.CTkLabel(
            log_frame,
            text="🕒 최근 활동 (Memo Log)",
            font=FONTS["header"],
            text_color=COLORS["text"],
        ).pack(anchor="w", padx=20, pady=15)

        self.log_scroll = ctk.CTkScrollableFrame(log_frame, fg_color="transparent")
        self.log_scroll.pack(fill="both", expand=True, padx=10, pady=(0, 10))

    # 카드 더블 클릭 시 테이블 뷰로 이동 및 필터 적용
    def on_card_double_click(self, index):
        # 1. 카드 인덱스에 따른 타겟 필터 정의
        target_filters = []
        if index == 0:
            target_filters = ["생산 접수", "생산중"]
        elif index == 1:
            target_filters = ["대기"]
        elif index == 2:
            target_filters = ["중지"]
        elif index == 3:
            target_filters = ["완료"]

        # 2. 메인 앱 인스턴스 및 테이블 뷰 찾기
        main_app = self.winfo_toplevel()

        if hasattr(main_app, "show_table_view") and hasattr(main_app, "view_table"):
            # 3. 테이블 뷰로 화면 전환
            main_app.show_table_view()

            # 4. 필터 설정 변경
            table_view = main_app.view_table

            # 먼저 모든 필터 해제
            for status in table_view.filter_states:
                table_view.filter_states[status] = False
                if status in table_view.filter_check_vars:
                    table_view.filter_check_vars[status].set(False)

            # 타겟 필터만 체크
            for status in target_filters:
                if status in table_view.filter_states:
                    table_view.filter_states[status] = True
                    if status in table_view.filter_check_vars:
                        table_view.filter_check_vars[status].set(True)

            # 5. 테이블 뷰 데이터 갱신 및 UI 업데이트
            table_view.update_dropdown_btn_text()
            table_view.refresh_data()

    def refresh_data(self):
        """데이터 로드 및 UI 갱신"""
        df = self.dm.df

        if df is None or df.empty:
            self._update_empty_state()
            return

        # 1. 요약 카드 업데이트
        self._update_summary_cards(df)

        # 2. 차트 업데이트
        self._update_chart(df)

        # 3. 금일 출고 예정 업데이트
        self._update_today_list(df)

        # 4. 최근 활동 로그 업데이트
        self._update_recent_logs()

    def _update_empty_state(self):
        for lbl in self.card_widgets:
            lbl.configure(text="0")
        self.today_count_lbl.configure(text="0건")

    def _update_summary_cards(self, df):
        status_series = df["Status"].fillna("").astype(str).str.strip()

        # 1. 진행 중 (대기, 생산중)
        active_count = len(df[status_series.isin(["생산중", "생산 접수"])])

        # 2. 생산 대기
        waiting_count = len(df[status_series == "대기"])

        # 3. 중지
        hold_count = len(df[status_series.isin(["Hold", "중지"])])

        # 4. 이번달 완료
        completed_count = 0
        if "출고일" in df.columns:
            try:
                dates = pd.to_datetime(df["출고일"], errors="coerce", format="mixed")
                now = datetime.now()
                mask = (dates.dt.year == now.year) & (dates.dt.month == now.month) & (status_series == "완료")
                completed_count = len(df[mask])
            except Exception:
                pass

        counts = [active_count, waiting_count, hold_count, completed_count]
        for lbl, val in zip(self.card_widgets, counts):
            lbl.configure(text=str(val))

    def _update_chart(self, df):
        if self.canvas:
            self.canvas.get_tk_widget().destroy()
            self.canvas = None

        status_series = df["Status"].fillna("").astype(str).str.strip()
        filtered_df = df[status_series != "완료"]
        status_counts = filtered_df["Status"].value_counts()

        if status_counts.empty:
            return

        bg_color = get_color_str("bg_medium")
        text_color = get_color_str("text")

        fig, ax = plt.subplots(figsize=(5, 4), dpi=100)
        fig.patch.set_facecolor(bg_color)
        ax.set_facecolor(bg_color)

        labels = status_counts.index.tolist()
        values = status_counts.values.tolist()

        color_map = {
            "생산 접수": get_color_str("primary"),
            "대기": get_color_str("warning"),
            "생산중": get_color_str("success"),
            "중지": get_color_str("danger"),
        }

        default_colors = plt.cm.Pastel1.colors
        pie_colors = [color_map.get(label, default_colors[i % len(default_colors)]) for i, label in enumerate(labels)]

        wedges, texts, autotexts = ax.pie(
            values,
            labels=labels,
            autopct="%1.1f%%",
            startangle=90,
            colors=pie_colors,
            textprops={"color": text_color, "fontfamily": FONT_FAMILY},
        )

        plt.setp(texts, size=10, weight="bold")
        plt.setp(autotexts, size=9, weight="bold", color=text_color)

        centre_circle = plt.Circle((0, 0), 0.70, fc=bg_color)
        fig.gca().add_artist(centre_circle)

        ax.axis("equal")
        plt.tight_layout()

        self.canvas = FigureCanvasTkAgg(fig, master=self.chart_area)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill="both", expand=True)

    def _update_today_list(self, df):
        for widget in self.today_scroll.winfo_children():
            widget.destroy()

        if df.empty or "출고예정일" not in df.columns:
            self.today_count_lbl.configure(text="0건")
            return

        today_str = datetime.now().strftime("%Y-%m-%d")

        status_series = df["Status"].fillna("").astype(str).str.strip()
        mask = (df["출고예정일"].astype(str) == today_str) & (~status_series.isin(["완료", "중지"]))
        today_df = df[mask]

        self.today_count_lbl.configure(text=f"{len(today_df)}건")

        if today_df.empty:
            ctk.CTkLabel(
                self.today_scroll,
                text="금일 출고 예정 없음",
                text_color=COLORS["text_dim"],
                font=(FONT_FAMILY, 12),
            ).pack(pady=20)
            return

        for _, row in today_df.iterrows():
            self._create_list_item(self.today_scroll, row, is_log=False)

    def _update_recent_logs(self):
        for widget in self.log_scroll.winfo_children():
            widget.destroy()

        if not hasattr(self.dm, "memo_log_df") or self.dm.memo_log_df.empty:
            ctk.CTkLabel(
                self.log_scroll,
                text="최근 활동 없음",
                text_color=COLORS["text_dim"],
                font=(FONT_FAMILY, 12),
            ).pack(pady=20)
            return

        logs = self.dm.memo_log_df.sort_values(by="일시", ascending=False).head(10)

        for _, row in logs.iterrows():
            self._create_list_item(self.log_scroll, row, is_log=True)

    def _create_list_item(self, parent, row_data, is_log=False):
        """리스트 아이템 생성 (Today List / Recent Log 공용)"""
        card = ctk.CTkFrame(
            parent,
            fg_color=COLORS["bg_dark"],
            corner_radius=6,
            border_width=1,
            border_color=COLORS["bg_dark"],
        )
        card.pack(fill="x", pady=3, padx=5)

        req_no = row_data.get("요청번호") if is_log else row_data.get("번호")

        if req_no:
            # 카드 클릭 시 상세 팝업
            card.bind("<Button-1>", lambda e, r=req_no: self.pm.open_schedule_popup(r))

        if is_log:
            time_str = str(row_data.get("일시", ""))[5:-3]
            action = row_data.get("구분", "-")
            user = row_data.get("작업자", "-")
            content = str(row_data.get("내용", ""))
            if len(content) > 15:
                content = content[:15] + "..."

            text = f"[{time_str}] {user}: {content}"
            icon = "[추가]" if action == "추가" else "[삭제]"

            ctk.CTkLabel(
                card,
                text=f"{icon} {text}",
                font=(FONT_FAMILY, 11),
                text_color=COLORS["text"],
                anchor="w",
            ).pack(side="left", padx=10, pady=5)
            ctk.CTkLabel(
                card,
                text=f"No.{req_no}",
                font=(FONT_FAMILY, 10),
                text_color=COLORS["text_dim"],
            ).pack(side="right", padx=10)

        else:
            comp = row_data.get("업체명", "-")
            model = row_data.get("모델명", "-")
            qty = row_data.get("수량", "-")

            ctk.CTkLabel(
                card,
                text=f"[{comp}] {model}",
                font=(FONT_FAMILY, 12, "bold"),
                text_color=COLORS["text"],
            ).pack(anchor="w", padx=10, pady=(5, 0))
            ctk.CTkLabel(
                card,
                text=f"수량: {qty}개",
                font=(FONT_FAMILY, 11),
                text_color=COLORS["text_dim"],
            ).pack(anchor="w", padx=10, pady=(0, 5))
