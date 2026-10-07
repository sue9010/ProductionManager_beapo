import platform
import tkinter as tk
from datetime import datetime, timedelta
from tkinter import messagebox

import customtkinter as ctk
import matplotlib.dates as mdates
# Matplotlib 관련 임포트
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib import font_manager, rc
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# [수정] FONT_FAMILY 추가
from styles import COLORS, FONT_FAMILY, FONTS, get_color_str


class GanttView(ctk.CTkFrame):
    def __init__(self, parent, data_manager, popup_manager):
        super().__init__(parent, fg_color="transparent")
        self.dm = data_manager
        self.pm = popup_manager

        # 한글 폰트 설정 (Matplotlib)
        self._setup_font()

        self.create_widgets()
        
        # 초기 데이터 로드
        self.refresh_data()

    def _setup_font(self):
        """OS에 따른 Matplotlib 한글 폰트 설정"""
        # [핵심] 우리가 설정한 FONT_FAMILY(Pretendard)를 최우선으로 적용
        plt.rcParams['font.family'] = FONT_FAMILY
        plt.rcParams['axes.unicode_minus'] = False

    def create_widgets(self):
        # 1. 상단 툴바
        toolbar = ctk.CTkFrame(self, height=50, fg_color="transparent")
        toolbar.pack(fill="x", padx=20, pady=(10, 0))

        ctk.CTkLabel(toolbar, text="📈 Gantt Chart (생산중)", font=FONTS["title"], text_color=COLORS["text"]).pack(side="left")

        ctk.CTkButton(
            toolbar, text="🔄 새로고침", width=80, height=32,
            fg_color=COLORS["bg_medium"], hover_color=COLORS["bg_light"], text_color=COLORS["text"],
            command=self.refresh_data, font=FONTS["main"]
        ).pack(side="right")

        # 2. 차트 영역 (스크롤 가능하도록 변경)
        # 기존 CTkFrame -> CTkScrollableFrame
        self.chart_scroll_frame = ctk.CTkScrollableFrame(self, fg_color=COLORS["bg_dark"], corner_radius=10)
        self.chart_scroll_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # 내부 컨텐츠 프레임 (캔버스가 들어갈 곳)
        self.chart_content = ctk.CTkFrame(self.chart_scroll_frame, fg_color="transparent")
        self.chart_content.pack(fill="both", expand=True)
        
        # 빈 캔버스 자리 표시
        self.canvas = None

    def refresh_data(self):
        """데이터를 로드하고 차트를 다시 그립니다."""
        df = self.dm.df
        
        # [수정] 데이터가 없는 경우에 대한 처리 강화
        if df is None or df.empty:
            self._show_empty_msg("데이터가 없습니다.\n좌측 하단의 [데이터 로드] 버튼을 눌러 파일을 불러오세요.")
            return

        # 데이터 전처리: 날짜 변환 및 필터링
        processed_df = self._process_data_for_gantt(df)
        
        if processed_df.empty:
            self._show_empty_msg("표시할 '생산중' 데이터가 없습니다.")
            return

        self._draw_gantt_chart(processed_df)

    def _process_data_for_gantt(self, df):
        """간트 차트용 데이터 가공"""
        # 1. 사본 생성
        temp_df = df.copy()
        
        # 2. 날짜 형식 변환 (errors='coerce' -> 실패시 NaT)
        temp_df['start_date'] = pd.to_datetime(temp_df['출고요청일'], errors='coerce')
        temp_df['end_date'] = pd.to_datetime(temp_df['출고예정일'], errors='coerce')
        
        # 3. 필터링
        temp_df['Status'] = temp_df['Status'].astype(str).str.strip()
        
        # 생산중인 항목만 표시 (조건 완화 가능)
        mask_producing = temp_df['Status'] == '생산중'
        # 날짜가 있는 항목만 (시작일 필수)
        mask_dates = temp_df['start_date'].notna()
        
        active_df = temp_df[mask_producing & mask_dates].copy()
        
        if active_df.empty:
            return active_df

        # 종료일이 없으면 시작일로 채움 (최소 1일 표시를 위해)
        mask_no_end = active_df['end_date'].isna()
        active_df.loc[mask_no_end, 'end_date'] = active_df.loc[mask_no_end, 'start_date']

        # [핵심 수정] 번호(req_no) 기준으로 그룹화하여 중복 제거
        # 번호별로 가장 빠른 시작일과 가장 늦은 종료일을 구함 (혹은 첫 번째 행 기준)
        # 여기서는 단순히 첫 번째 행의 정보를 대표값으로 사용하되, 품목 수 등을 라벨에 추가할 수 있음
        
        # 그룹화할 컬럼들 (번호와 업체명은 동일하다고 가정)
        group_cols = ['번호', '업체명']
        
        # 집계 방식 정의
        agg_dict = {
            'start_date': 'min',  # 시작일은 가장 빠른 날짜
            'end_date': 'max',    # 종료일은 가장 늦은 날짜
            '모델명': 'count',    # 모델명 개수로 품목 수 파악
            'Status': 'first'     # 상태값 가져오기 (생산중)
        }
        
        # 그룹화 수행
        grouped_df = active_df.groupby(group_cols, as_index=False).agg(agg_dict)
        
        # 4. 기간 계산 (matplotlib barh용 width)
        grouped_df['duration'] = (grouped_df['end_date'] - grouped_df['start_date']).dt.days
        grouped_df.loc[grouped_df['duration'] <= 0, 'duration'] = 1
        
        # 5. Y축 라벨 생성 (번호 + 업체명 + 품목수)
        grouped_df['label'] = grouped_df.apply(lambda x: f"No.{x['번호']} [{x['업체명']}] ({x['모델명']}종)", axis=1)
        
        # 6. 정렬 (번호 내림차순 -> 차트에서는 위에서부터 그려짐)
        try:
            grouped_df['sort_helper'] = pd.to_numeric(grouped_df['번호'])
        except:
            grouped_df['sort_helper'] = grouped_df['번호'].astype(str)
            
        grouped_df = grouped_df.sort_values(by='sort_helper', ascending=False)
        
        return grouped_df

    def _draw_gantt_chart(self, df):
        """Matplotlib을 이용해 차트 그리기"""
        # 기존 캔버스 제거
        if self.canvas:
            self.canvas.get_tk_widget().destroy()
            self.canvas = None

        # 기존 메시지 라벨 제거
        for w in self.chart_content.winfo_children(): w.destroy()

        # [신규] 호버/클릭 이벤트를 위해 데이터프레임 저장
        self.gantt_df = df

        # --- 스타일 설정 ---
        # [수정] Matplotlib은 튜플 색상을 이해하지 못하므로 get_color_str()을 통해 단일 색상 문자열로 변환
        bg_color = get_color_str("bg_dark")
        text_color = get_color_str("text")
        
        # 고정된 항목 높이 기반 Figure 크기 계산
        ITEM_HEIGHT_INCH = 0.5
        MIN_ITEMS = 10 
        
        item_count = len(df)
        display_count = max(item_count, MIN_ITEMS)
        fig_height = 2 + (display_count * ITEM_HEIGHT_INCH)
        
        # Figure 생성
        fig, ax = plt.subplots(figsize=(10, fig_height), dpi=100)
        self.ax = ax # [신규] 이벤트를 위해 ax 저장
        
        fig.patch.set_facecolor(bg_color)
        ax.set_facecolor(bg_color)
        
        # --- 데이터 매핑 ---
        y_labels = df['label'].tolist()
        start_dates = mdates.date2num(df['start_date'])
        durations = df['duration'].tolist()
        
        # [수정] 색상 변환
        color = get_color_str("success")
        
        # Y축 위치 (0부터 시작)
        y_pos = range(len(y_labels))
        
        # --- 막대 그리기 (Barh) ---
        # [신규] 이벤트를 위해 bars 객체 저장
        self.bars = ax.barh(y_pos, durations, left=start_dates, height=0.4, align='center', color=color, edgecolor=bg_color)
        
        # [신규] 툴팁 어노테이션 생성 (초기에는 숨김)
        self.annot = ax.annotate("", xy=(0,0), xytext=(15,0), textcoords="offset points",
                                 bbox=dict(boxstyle="round", fc="white", ec="gray", alpha=0.9),
                                 color="black", weight="bold", fontsize=9,
                                 arrowprops=dict(arrowstyle="-", color="gray"))
        self.annot.set_visible(False)

        # --- X축 눈금 간격 동적 계산 ---
        min_date = df['start_date'].min()
        max_date = df['end_date'].max()
        interval = 1
        if pd.notna(min_date) and pd.notna(max_date):
            total_days = (max_date - min_date).days
            MAX_TICKS = 15
            if total_days > MAX_TICKS:
                interval = int(total_days / MAX_TICKS) + 1
        
        # --- 축 설정 ---
        ax.xaxis_date()
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d'))
        ax.xaxis.set_major_locator(mdates.DayLocator(interval=interval))
        
        # Y축: 항목 라벨
        ax.set_yticks(y_pos)
        ax.set_yticklabels(y_labels, color=text_color, fontsize=10)
        
        # [핵심 수정] Y축을 오른쪽으로 이동
        ax.yaxis.tick_right()
        # (선택사항) 라벨 위치도 오른쪽으로 설정
        ax.yaxis.set_label_position("right") 
        
        # Y축 범위 설정
        ax.set_ylim(-0.5, display_count - 0.5)

        # 그리드 및 테두리
        # [수정] 그리드 색상 변환
        grid_color = get_color_str("text_dim")
        
        ax.grid(True, axis='x', linestyle='--', alpha=0.3, color=grid_color)
        ax.spines['bottom'].set_color(grid_color)
        ax.spines['top'].set_color(bg_color)
        ax.spines['left'].set_color(bg_color)
        ax.spines['right'].set_color(bg_color)
        ax.tick_params(axis='x', colors=text_color)
        ax.tick_params(axis='y', colors=text_color)
        
        # 제목 제거 (사용자 요청)
        # ax.set_title(f"생산 진행 현황 (총 {len(df)}건)", color=text_color, fontsize=14, pad=15)
        
        # 레이아웃 조정 (하단 여백 제거)
        # [핵심 수정] tight_layout의 pad를 0으로 줄이거나, subplots_adjust로 하단 여백을 최소화
        plt.tight_layout(pad=1.05) 
        # 만약 tight_layout만으로 부족하다면 아래 주석을 해제하고 bottom 값을 0에 가깝게 조정하세요.
        # plt.subplots_adjust(bottom=0.05, top=0.95)

        # --- Tkinter 캔버스에 통합 ---
        self.canvas = FigureCanvasTkAgg(fig, master=self.chart_content)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill="both", expand=True)

        # [신규] 마우스 호버 이벤트 연결
        self.canvas.mpl_connect("motion_notify_event", self.on_hover)
        # [신규] 마우스 클릭 이벤트 연결 (더블클릭 감지)
        self.canvas.mpl_connect("button_press_event", self.on_click)

    # [신규] 마우스 호버 이벤트 핸들러
    def on_hover(self, event):
        if event.inaxes == self.ax:
            for i, bar in enumerate(self.bars):
                cont, _ = bar.contains(event)
                if cont:
                    # 해당 바의 데이터 가져오기
                    row = self.gantt_df.iloc[i]
                    end_date = row['end_date']
                    date_str = end_date.strftime('%Y-%m-%d')
                    
                    # 툴팁 위치 및 텍스트 설정 (바의 오른쪽 끝에 표시)
                    self.annot.xy = (bar.get_x() + bar.get_width(), bar.get_y() + bar.get_height()/2)
                    self.annot.set_text(f"출고예정: {date_str}")
                    self.annot.set_visible(True)
                    self.canvas.draw_idle()
                    return
        
        # 마우스가 바 위에 없으면 툴팁 숨김
        if hasattr(self, 'annot') and self.annot.get_visible():
            self.annot.set_visible(False)
            self.canvas.draw_idle()

    # [신규] 마우스 클릭(더블클릭) 이벤트 핸들러
    def on_click(self, event):
        # 더블클릭인지 확인
        if event.dblclick and event.inaxes == self.ax:
            for i, bar in enumerate(self.bars):
                cont, _ = bar.contains(event)
                if cont:
                    # 클릭된 바의 데이터 가져오기
                    row = self.gantt_df.iloc[i]
                    req_no = row['번호']
                    status = row['Status']
                    
                    # 상태에 따른 팝업 열기
                    if status == "생산중":
                        self.pm.open_complete_popup(req_no)
                    elif status == "완료":
                        self.pm.open_completed_view_popup(req_no)
                    else:
                        self.pm.open_schedule_popup(req_no)
                    return

    def _show_empty_msg(self, msg):
        if self.canvas:
            self.canvas.get_tk_widget().destroy()
            self.canvas = None
        
        # 메시지 라벨 표시 (스크롤 프레임 내부 컨텐츠 삭제 후 추가)
        for w in self.chart_content.winfo_children(): w.destroy()
        
        # 안내 메시지를 가운데에 예쁘게 표시
        msg_frame = ctk.CTkFrame(self.chart_content, fg_color="transparent")
        msg_frame.pack(expand=True, fill="both", pady=50)
        
        ctk.CTkLabel(msg_frame, text="⚠️", font=("Emoji", 48)).pack(pady=(0, 10))
        ctk.CTkLabel(msg_frame, text=msg, font=FONTS["header"], text_color=COLORS["text_dim"]).pack()