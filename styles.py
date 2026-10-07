import platform

import customtkinter as ctk

# ==========================================
# [Color System] (Light, Dark) Tuples
# ==========================================
COLORS = {
    "primary": ("#1565C0", "#3B8ED0"), 
    "primary_hover": ("#0D47A1", "#36719F"),
    "danger": ("#C62828", "#E04F5F"),
    "danger_hover": ("#B71C1C", "#D32F2F"),
    "success": ("#2E7D32", "#2CC985"),
    "warning": ("#EF6C00", "#D35400"),
    "text": ("#212121", "#FFFFFF"),
    "text_dim": ("#616161", "#AAAAAA"),
    "bg_dark": ("#F5F5F5", "#2b2b2b"),
    "bg_medium": ("#FFFFFF", "#333333"),
    "bg_light": ("#E0E0E0", "#555555"),
    "bg_light_hover": ("#BDBDBD", "#333333"),
    "border": ("#9E9E9E", "#444444"),
    "transparent": "transparent"
}

# ==========================================
# [Font System] 심플한 폰트 설정 (맑은 고딕 우선)
# ==========================================

def get_system_font():
    """
    복잡한 로직 없이 OS별 표준 한글 폰트를 반환합니다.
    """
    system_os = platform.system()
    
    if system_os == "Windows":
        return "Malgun Gothic"  # 윈도우 표준
    elif system_os == "Darwin": # macOS
        return "Apple SD Gothic Neo"
    else: # Linux 등
        return "NanumGothic"

# 폰트 결정
FONT_FAMILY = get_system_font()

FONTS = {
    "main": (FONT_FAMILY, 12),
    "main_bold": (FONT_FAMILY, 12, "bold"),
    "header": (FONT_FAMILY, 14, "bold"),
    "title": (FONT_FAMILY, 16, "bold"),
    "small": (FONT_FAMILY, 10),
}

def get_color_str(key):
    color_val = COLORS.get(key)
    if not isinstance(color_val, tuple):
        return color_val
    mode = ctk.get_appearance_mode()
    if mode == "Light":
        return color_val[0]
    else:
        return color_val[1]