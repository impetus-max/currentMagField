# -*- coding: utf-8 -*-
"""
전류의 자기장 학습용 스트림릿 앱 (상세 콘텐츠 + GPT 기능 통합 최종본)
"""

########################  공통 import  ########################
import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
from matplotlib import font_manager
import matplotlib.patches as patches
from mpl_toolkits.mplot3d import Axes3D  # 3D 시뮬레이션을 위해 추가
import os, datetime
from pathlib import Path

# ------------------------------------------------------------
#  FPDF (선택)
# ------------------------------------------------------------
try:
    from fpdf import FPDF
    FPDF_ENABLED = True
except ModuleNotFoundError:
    FPDF_ENABLED = False

# ------------------------------------------------------------
#  OpenAI (선택)
# ------------------------------------------------------------
try:
    from openai import OpenAI
    GPT_ENABLED = True
except ModuleNotFoundError:
    GPT_ENABLED = False
    st.warning(
        "⚠️ `openai` 패키지가 설치돼 있지 않아 AI챗봇 기능이 꺼져 있습니다.\n"
        "• 로컬:  `pip install openai`\n"
        "• 배포:  requirements.txt 에  openai  추가 후 재배포"
    )

# ------------------------------------------------------------
#  Google Sheets (선택)
# ------------------------------------------------------------
try:
    import gspread
    from google.oauth2.service_account import Credentials
    GSHEET_ENABLED = True
except ModuleNotFoundError:
    GSHEET_ENABLED = False

# ============================================================
#  GPT 헬퍼
# ============================================================
def call_gpt(system_prompt: str, user_prompt: str, max_tokens: int = 350):
    """GPT-4o 호출 헬퍼 – API Key 는 사이드바 입력"""
    if not GPT_ENABLED:
        return "(openai 모듈 없음)"
    api_key = st.session_state.get("openai_api_key", "")
    if not api_key:
        st.warning("사이드바에 OpenAI API Key를 입력해주세요.")
        return "(API Key 미입력)"
    try:
        client = OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            max_tokens=max_tokens,
            temperature=0.7,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        st.error(f"[AI챗봇 오류] {e}")
        return f"[AI챗봇 오류] {e}"

# ============================================================
#  스트림릿 페이지/글꼴
# ============================================================
st.set_page_config(page_title="고등학교 2학년 물리학1 전류의 자기장",
                   page_icon="🧲", layout="wide")
st.markdown("""
<style>
html, body, [class*="st-"] { font-size:18px !important; }
</style>
""", unsafe_allow_html=True)

# ---- 한글 폰트 설정 ----
@st.cache_resource
def load_font():
    from matplotlib import rcParams
    FONT_DIR = Path(__file__).parent / "fonts"
    FONT_DIR.mkdir(exist_ok=True)
    font_path = FONT_DIR / "NanumGothic-Regular.ttf"
    if font_path.exists():
        font_manager.fontManager.addfont(str(font_path))
        rcParams["font.family"] = font_manager.FontProperties(fname=str(font_path)).get_name()
    else:
        st.warning("⚠️ NanumGothic-Regular.ttf 폰트가 없습니다. fonts 폴더에 추가하면 한글이 깨지지 않습니다.")
    rcParams["axes.unicode_minus"] = False
load_font()

# ============================================================
#  유틸 – 이미지 & GSheet
# ============================================================
BASE_DIR = Path(__file__).parent
def safe_img(src: str, **kwargs):
    """폴더 내부 또는 상위에서 안전하게 이미지 로딩"""
    cand = [BASE_DIR / "image" / src, BASE_DIR / src]
    for p in cand:
        if p.exists():
            st.image(str(p), **kwargs)
            return
    st.warning(f"⚠️ 'image' 폴더에 파일 없음: {src}")

def append_row_to_gsheet(row_data):
    """Google Sheets 에 한 행 추가 (헤더: 학번, 성명, 이동반, 접속확인, (1), (2), (3), 피드백)"""
    if not GSHEET_ENABLED:
        return False
    try:
        creds_dict = st.secrets["gcp_service_account"]
        scopes = ["https://www.googleapis.com/auth/spreadsheets",
                  "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
        client = gspread.authorize(creds)
        spreadsheet = client.open("MagFieldResponses")
        sheet = spreadsheet.sheet1
        while len(row_data) < 8:   # 8 컬럼 맞추기
            row_data.append("")
        sheet.append_row(row_data, value_input_option="USER_ENTERED")
        return True
    except Exception as e:
        st.sidebar.error(f"GSheet 오류: {e}")
        return False

def get_check_tag() -> str:
    """세션에 저장한 접속확인 태그 반환"""
    return st.session_state.student_info.get("접속확인", "")

# ============================================================
#  메뉴 정의
# ============================================================
steps_1_all = [
    "메인 화면", "학습 목표", "자기장 시뮬레이션",
    "기본 개념 문제 (1차시)",
    "전류의 자기장 실험1 : 직선 도선 주위에서 자기장 확인하기",
    "전류의 자기장 실험2 : 원형 도선의 중심에서 자기장 확인하기",
    "전류의 자기장 실험3 : 솔레노이드에서 자기장 확인하기",
    "실험 결과 작성하기",
]
steps_2 = [
    "학습 목표", "기본 개념 문제 (2차시)",
    "전류에 의한 자기작용 이론 정리", "예제 풀이",
    "수능응용 문제", "탐구 과제", "피드백 / 정리하기",
]
steps_all  = steps_1_all + steps_2
steps_1_menu = steps_1_all[1:]
N1, N2 = len(steps_1_menu), len(steps_2)

# ============================================================
#  세션 상태 초기화
# ============================================================
default_states = {
    "done":                [False] * len(steps_all),
    "current":             0,
    "student_info":        {"학번": "", "성명": "", "이동반": ""},
    "student_info_saved":  False,
    "roster":              [],
    "report_submitted":    False,
    "final_report":        {"text1": "", "text2": "", "text3": "", "feedback": ""},
}
# 실험 1·2·3 관찰 & 피드백
for i in range(1, 4):
    default_states[f"exp{i}_text"]     = ""
    default_states[f"exp{i}_feedback"] = ""

for k, v in default_states.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ============================================================
#  사이드바 – 학습자 정보 & 진행률
# ============================================================
with st.sidebar:
    st.subheader("🗝️ OpenAI API Key")
    st.text_input("Key 입력", key="openai_api_key",
                  type="password", placeholder="sk-…")
    if st.session_state.get("openai_api_key", "").startswith("sk-") \
       and len(st.session_state.openai_api_key) > 40:
        st.success("✅ API Key 입력 확인!")

    st.markdown("---")
    st.markdown("#### 🗂️ 접속 확인")
    if not st.session_state.roster:
        st.markdown("- _아직 없음_")
    else:
        for tag in st.session_state.roster:
            st.markdown(f"- {tag}")
    st.markdown("---")

    # ---------- 학습자 정보 입력 / 수정 ----------
    if st.session_state.student_info_saved:
        with st.expander("학습자 정보 (수정하려면 클릭)", expanded=False):
            for k in ("학번", "성명", "이동반"):
                st.session_state.student_info[k] = st.text_input(
                    k, value=st.session_state.student_info[k],
                    key=f"in_{k}_edit")
            if st.button("수정 완료", key="info_edit"):
                st.rerun()
    else:
        with st.expander("학습자 정보 입력", expanded=True):
            for k in ("학번", "성명", "이동반"):
                st.session_state.student_info[k] = st.text_input(
                    k, value=st.session_state.student_info[k],
                    key=f"in_{k}_initial")
            if st.button("저장"):
                info = st.session_state.student_info
                if info["학번"] and info["성명"]:
                    st.session_state.student_info_saved = True
                    now_str = datetime.datetime.now().strftime("%y-%m-%d %H:%M")
                    tag     = f"{info['학번']} {info['성명']}"
                    full_tag = f"{tag} ({now_str})"
                    st.session_state.student_info["접속확인"] = full_tag
                    if not any(tag in r for r in st.session_state.roster):
                        st.session_state.roster.append(full_tag)

                    # GSheet – 접속 로그
                    append_row_to_gsheet(
                        [info["학번"], info["성명"], info["이동반"],
                         full_tag, "", "", "", ""]
                    )
                    st.rerun()
                else:
                    st.warning("학번과 성명을 모두 입력하세요.")

    st.markdown("---")
    st.success("💡 아래 버튼을 클릭하면 해당 내용으로 이동합니다. 진행 완료 시 ✅로 표시됩니다.")

    # ---------- 메뉴 ----------
    if st.sidebar.button("🤖 AI챗봇 (첫 화면)"):
        st.session_state.current = 0
        st.rerun()

    # 1차시 진행률
    p1 = sum(st.session_state.done[1:1+N1]) / N1 if N1 else 0
    st.sidebar.markdown(f"### 1차시 진행률 : {int(p1*100)}%")
    st.sidebar.progress(p1)
    for i, n in enumerate(steps_1_menu, start=1):
        label = f"{'✅' if st.session_state.done[i] else '○'} {n}"
        if st.sidebar.button(label, key=f"btn1_{i}"):
            st.session_state.current = i
            st.session_state.done[i] = True
            st.rerun()

    # 2차시 진행률
    p2 = sum(st.session_state.done[len(steps_1_all):]) / N2 if N2 else 0
    st.sidebar.markdown(f"### 2차시 진행률 : {int(p2*100)}%")
    st.sidebar.progress(p2)
    for i, n in enumerate(steps_2, start=len(steps_1_all)):
        label = f"{'✅' if st.session_state.done[i] else '○'} {n}"
        if st.sidebar.button(label, key=f"btn2_{i}"):
            st.session_state.current = i
            st.session_state.done[i] = True
            st.rerun()

    st.markdown("---")
    if st.sidebar.button("🤖 AI챗봇", key="chatbot_bottom"):
        st.session_state.current = 0
        st.rerun()

# 현재 페이지 이름
step_name = steps_all[st.session_state.current]
st.header(f"📝 {step_name}")

# ============================================================
#  페이지 함수들
# ============================================================
def page_intro_physics():
    """메인 화면"""
    st.title("물리학1: 전류의 자기작용 🧲")
    st.markdown("---")

    st.markdown("""
    1820년, 덴마크의 물리학자 **한스 크리스티안 외르스테드**는
    전류가 흐르는 전선 주위에서 나침반이 움직이는 현상을 관찰했습니다.
    이는 전기와 자기의 깊은 연관성을 보여주는 역사적인 발견이었고,
    오늘날 전자기학의 출발점이 되었습니다.
    """)
    safe_img("oersted_experiment.png", caption="외르스테드의 실험(1820)")

    st.markdown("---")
    st.markdown("#### 💬 AI챗봇과 자유롭게 대화하기")
    st.info("궁금한 점이 있다면 AI챗봇에게 무엇이든 물어보세요!")

    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    for role, msg in st.session_state.chat_history:
        st.chat_message(role).write(msg)

    if prompt := st.chat_input("전류와 자기장에 대해 궁금한 점을 물어보세요."):
        st.session_state.chat_history.append(("user", prompt))
        st.chat_message("user").write(prompt)
        with st.chat_message("assistant"):
            with st.spinner("AI챗봇이 답변을 생성 중입니다..."):
                sys = ("You are a friendly and knowledgeable physics tutor for "
                       "Korean high-school students. Your name is 'Phi-Bot'. "
                       "Answer in Korean.")
                ans = call_gpt(sys, prompt, 450)
                st.write(ans)
                st.session_state.chat_history.append(("assistant", ans))

def page_goal():
    st.markdown("""
    ### 학습 목표
    1. 전류에 의한 자기 작용을 시뮬레이션과 실험으로 확인한다.
    2. 직선도선, 원형도선, 솔레노이드에 의한 자기장 모양을 이해한다.
    """)

def page_goal_2():
    st.markdown("""
    ### 학습 목표
    1. 전류의 방향과 세기가 자기장에 미치는 영향을 정량적으로 해석할 수 있다.  
    2. 전류의 자기 현상이 적용된 생활 속 사례를 설명할 수 있다.
    """)

def page_simulation():
    """자기장 시뮬레이션(막대자석 & 자석 상호작용)"""
    # --- 막대자석 ---
    L, R = st.columns(2)
    with L:
        safe_img("magnet_lines_compass.png",
                 caption="막대자석의 자기력선 & 나침반")
    with R:
        st.markdown("""**자기장**: 자기력이 작용하는 공간  
**자기력선**: 눈에 보이지 않는 자기장을 가상의 선으로 표현
                    (나침반의 N이 향하는 방향을 연결한 선이다.)
- 자기력선은 N극에서 S극 방향을 향하고 폐곡선이다.
- 자기력선은 교차되거나 끊어지지 않는다.  
- 자기력선은의 간격이 좁은 곳일수록 자기장이 강한 곳이다.  
- 자기력선의 한 점에서 접선 방향은 해당 점에서의 자기장 방향이다.""")

    st.markdown("---")
    st.markdown("### ⚡ 막대자석 주위 자기장 시뮬레이션")
    c1, c2 = st.columns([1, 2])
    with c1:
        strength = st.slider("🔧 자석 세기(k)", 0.5, 5.0, 1.0, 0.1)
        dens     = st.slider("화살표 밀도", 15, 35, 25, 5)
    with c2:
        # 벡터필드 계산
        fig, ax = plt.subplots(figsize=(7, 7))
        ax.set_aspect('equal'); ax.grid(True, ls='--', alpha=0.3)
        mag_len, mag_w = 1.2, 0.4
        north, south = np.array([0,  mag_len/2]), np.array([0, -mag_len/2])
        x, y = np.linspace(-3, 3, dens), np.linspace(-3, 3, dens)
        X, Y = np.meshgrid(x, y)
        RX, RY = X - north[0], Y - north[1]
        SX, SY = X - south[0], Y - south[1]
        rN, rS = np.hypot(RX, RY)+1e-9, np.hypot(SX, SY)+1e-9
        Bx = strength * (RX/rN**3 - SX/rS**3)
        By = strength * (RY/rN**3 - SY/rS**3)
        ax.streamplot(X, Y, Bx, By, color="k", density=1.3, linewidth=0.9)
        # 자석 표시
        ax.add_patch(patches.Rectangle((-mag_w/2, 0), mag_w, mag_len/2,
                                       fc="#DC143C", ec="k", zorder=10))
        ax.add_patch(patches.Rectangle((-mag_w/2, -mag_len/2), mag_w, mag_len/2,
                                       fc="#4169E1", ec="k", zorder=10))
        ax.text(0,  mag_len/2 + 0.2, "N", ha="center", weight="bold")
        ax.text(0, -mag_len/2 - 0.3, "S", ha="center", weight="bold")
        st.pyplot(fig)

    # --- 두 자석 ---
    st.markdown("---")
    st.markdown("### 🧲↔️🧲 두 자석의 상호작용 시뮬레이션")
    c1, c2 = st.columns([1, 2])
    with c1:
        interaction = st.radio("자석 배치",
                               ["S극-N극 (인력)", "S극-S극 (척력)"])
        distance = st.slider("두 자석 중심 거리 (×0.1)", 100.0, 400.0, 250.0, 10.0) / 100.0
        strength2 = st.slider("자석 세기 k'", 50.0, 300.0, 100.0, 10.0) / 10.0
    with c2:
        x, y = np.linspace(-4, 4, 37), np.linspace(-3, 3, 29)
        X, Y = np.meshgrid(x, y)
        # 자석 좌표
        n1, s1 = np.array([-distance/2-0.4, 0]), np.array([-distance/2+0.4, 0])
        if interaction.startswith("S극-N극"):
            n2, s2 = np.array([distance/2-0.4, 0]), np.array([distance/2+0.4, 0])
        else:  # N-S
            n2, s2 = np.array([distance/2+0.4, 0]), np.array([distance/2-0.4, 0])
        # 합성 자기장
        def dB(px, py, mx, my):
            RX, RY = px - mx, py - my
            r3 = (RX**2 + RY**2)**1.5 + 1e-9
            return RX/r3, RY/r3
        Bx = strength2 * (dB(X, Y, *n1)[0] - dB(X, Y, *s1)[0] +
                          dB(X, Y, *n2)[0] - dB(X, Y, *s2)[0])
        By = strength2 * (dB(X, Y, *n1)[1] - dB(X, Y, *s1)[1] +
                          dB(X, Y, *n2)[1] - dB(X, Y, *s2)[1])
        # 그림
        fig, ax = plt.subplots(figsize=(9, 6))
        ax.set_aspect('equal'); ax.set_xlim(-4, 4); ax.set_ylim(-3, 3)
        ax.grid(True, ls='--', alpha=0.3)
        ax.streamplot(X, Y, Bx, By, color='k', density=2.0, linewidth=1)
        # 자석 4개 직사각 + N/S 텍스트
        for m, color, txt in [(n1, '#DC143C', 'N'), (s1, '#4169E1', 'S'),
                              (n2, '#DC143C', 'N'), (s2, '#4169E1', 'S')]:
            ax.add_patch(patches.Rectangle((m[0]-0.4, -0.2), 0.8, 0.4,
                                           fc=color, ec='k'))
            ax.text(m[0], 0, txt, ha='center', va='center',
                    color='w', weight='bold')
        ax.set_title(f"두 자석 합성 자기장 ({interaction})")
        st.pyplot(fig)

def page_basic_1():
    """기본 개념 문제 – 1차시"""
    safe_img("magnet_quiz_1.png", width=500)
    ans = st.text_input("A 지점에 놓은 나침반의 N극이 가리키는 방향은 어디인가? (동/서/남/북)")
    if st.button("채점"):
        if ans and "동" in ans:
            st.success("🎉 정답입니다!")
        else:
            st.error("❌ 오답입니다. 자기력선은 N극에서 S극을 향합니다. A지점에서는 동쪽을 향합니다.")

def page_exp(title: str, exp_num: int):
    """실험1·2·3 관찰 & AI튜터 피드백"""
    st.markdown(f"#### {title}")
    key_txt = f"exp{exp_num}_text"
    key_fb  = f"exp{exp_num}_feedback"

    st.session_state[key_txt] = st.text_area(
        "관찰 내용을 작성하세요 (나침반의 N극 움직임 등)",
        st.session_state[key_txt], height=150, key=f"ta_{exp_num}")

    if st.button("🤖 AI튜터 피드백 요청", key=f"fb_btn_{exp_num}"):
        if st.session_state[key_txt]:
            with st.spinner("AI튜터가 피드백(마인드맵 포함)을 생성 중입니다..."):
                prompt = (
                    f"아래 학생 관찰 기록을 교사 시각으로 분석해 간단 · 긍정적 "
                    f"피드백과 **마인드맵**(Markdown List) 형태 정리를 해줘.\n\n"
                    f"---\n{st.session_state[key_txt]}"
                )
                feedback = call_gpt(
                    "You are a veteran physics teacher. Respond in Korean.",
                    prompt, 300)
                st.session_state[key_fb] = feedback
        else:
            st.warning("먼저 관찰 내용을 입력하세요.")

    if st.session_state[key_fb]:
        st.info(st.session_state[key_fb])

def page_report():
    """실험 결과 작성 + AI튜터 종합 피드백 + GSheet 기록"""
    st.info("세 항목을 모두 작성 후 **최종 보고서 제출**을 눌러주세요.")

    # --- 이전 실험 1·2·3 리뷰 영역 -----------------------------
    with st.expander("실험 1·2·3 관찰 내용 & AI튜터 피드백 검토하기", expanded=False):
        for i in range(1, 3+1):
            st.markdown(f"**실험 {i} 관찰**")
            st.markdown(st.session_state.get(f"exp{i}_text", "") or "_(미입력)_")
            st.markdown(f"**AI튜터 피드백**")
            st.markdown(st.session_state.get(f"exp{i}_feedback", "") or "_(없음)_")
            st.markdown("---")

    # --- 이미 제출했으면 잠금 -------------------------------
    if st.session_state.report_submitted:
        st.success("보고서가 제출되었습니다.")
        for k, label in [("text1", "(1) 실험 방법 요약"),
                         ("text2", "(2) 요소와 관계 설명"),
                         ("text3", "(3) 아이디어 및 소감")]:
            st.text_area(label, st.session_state.final_report[k],
                         disabled=True, height=120)
        st.markdown("### 🤖 AI튜터 종합 피드백")
        st.info(st.session_state.final_report["feedback"])
        return

    # --- 입력 폼 -------------------------------------------
    text1 = st.text_area(
        "(1) 직선 전류가 만드는 자기장의 세기에 영향을 미치는 "
        "요소를 확인할 수 있는 실험 방법을 요약하시오. "
        "[※ 새로운 실험을 설계하거나, 검색한 실험 방법을 설명하면 됩니다.]", height=150)
    text2 = st.text_area(
        "(2) 직선 전류가 만드는 자기장의 세기에 영향을 미치는 "
        "요소와 자기장 세기의 관계를 설명하시오.", height=150)
    text3 = st.text_area(
        "(3) 실험 결과와 상관없이 새로운 아이디어, 자신의 역할, "
        "잘했던 점 등을 자유롭게 작성하시오.", height=150)

    if st.button("🔬 최종 보고서 제출", type="primary"):
        if text1 and text2 and text3:
            with st.spinner("AI튜터 종합 피드백 생성 & 데이터 저장 중..."):
                full_report = f"① {text1}\n\n② {text2}\n\n③ {text3}"
                feedback = call_gpt(
                    "You are a helpful physics TA. Summarize key points and "
                    "provide constructive feedback in Korean.",
                    f"학생 보고서:\n{full_report}", 350)
                st.session_state.final_report = {
                    "text1": text1, "text2": text2, "text3": text3,
                    "feedback": feedback
                }
                st.session_state.report_submitted = True

                info = st.session_state.student_info
                append_row_to_gsheet([
                    info["학번"], info["성명"], info["이동반"],
                    get_check_tag(), text1, text2, text3, feedback
                ])
                st.rerun()
        else:
            st.warning("세 항목 모두 작성해야 제출 가능합니다.")

def page_basic_2():
    st.markdown("""
1. 그림은 직선 도선 아래 나침반 자침을 북-남 방향으로 맞춘 실험을 나타낸 것이다.
   가변 저항을 조절하며 전류가 변할 때, 자침의 움직임을 관찰하였다.
   실험에 관한 설명으로 옳지 않은 것은?""")
    safe_img("basic_quiz_2.png")
    opts = ["① 스위치 열어두면 나침반의 N극은 북쪽을 향한다.", "② 스위치 닫으면 나침반의 N극은 동쪽으로 회전한다.",
            "③ 전류의 세기가 증가하면 나침반의 N극은 남쪽을 향한다.", "④ 전류의 세기가 증가하면 회전각이 증가한다.", "⑤ 전류의 방향을 반대로 하면 나침반의 N극은 서쪽을 향해 회전한다."]
    sel = st.radio("선택", opts, index=None, key="basic2_sel")
    if st.button("채점 (2차시)"):
        ok = sel is not None and sel.startswith("③")
        
         # ✅ 오류 없는 메시지 출력
        if ok:
            st.success("🎉 정답입니다!")
        else:
            st.error("❌ 오답입니다.")

        info = st.session_state.student_info
        append_row_to_gsheet([
            info["학번"], info["성명"], info["이동반"],
            get_check_tag(), f"기본문제2차시: {sel}", str(ok), "", ""
        ])
        if not ok:
            st.markdown("""
**풀이**  
도선에 전류가 흐르면 전류에 의한 자기장은 나침반이 있는 곳에서 동쪽을 향하게 형성된다. 지구 자기장이 더해진 합성 자기장의
방향은 북동쪽이고, 나침반의 N극은 북동쪽을 가리킨다.
""")

def page_theory():
    st.markdown("## 전류에 의한 자기작용 이론 정리")

    # ───────────────────── 1. 직선 도선 ─────────────────────
    st.markdown("### 1. 직선 도선에 의한 자기장")
    st.latex(r"B = k \frac{I}{r}")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""
**방향**: 오른손 엄지를 전류 방향으로 하면,
나머지 손가락이 감아쥐는 방향이 자기장 방향.  
**세기**: 전류의 세기가 증가하면 ⇒ 자기장의 세기가 증가한다.  
      전류로부터의 거리가 멀어질수록 자기장의 세기가 감소한다.
""")
        safe_img("right_hand_rule_straight.png", width=250)
    with col2:
        current_I = st.slider("전류 I", -5.0, 5.0, 2.0, 0.1, key="i_str_3d")
        fig = plt.figure(figsize=(6, 6))
        ax = fig.add_subplot(111, projection='3d')
        ax.view_init(elev=20, azim=-45)
        ax.plot([0, 0], [0, 0], [-5, 5],
                color='red' if current_I > 0 else 'blue', lw=3)
        if abs(current_I) > 0.1:
            for r in np.linspace(1, 3, 3):
                theta = np.linspace(0, 2*np.pi, 100)
                x, y = r*np.cos(theta), r*np.sin(theta)
                for z in [-3, 0, 3]:
                    ax.plot(x, y, z, color='k', lw=1)
                    idx = 15 if current_I > 0 else 65
                    ax.quiver(x[idx], y[idx], z,
                              -y[idx]/r, x[idx]/r, 0,
                              length=0.8, normalize=True,
                              color='k', arrow_length_ratio=0.5)
        ax.set_xlabel('X'); ax.set_ylabel('Y'); ax.set_zlabel('Z')
        st.pyplot(fig)

    # ───────────────────── 2. 원형 도선 ─────────────────────
    st.markdown("### 2. 원형 도선에 의한 자기장")
    st.latex(r"B_{\text{중심}} = k' \frac{N I}{R}")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""
**방향**: 전류 방향으로 네 손가락을 감아쥐면
엄지가 가리키는 방향이 중심 자기장.  
**세기**: N(감은 수)와 I(전류)의 세기가 증가하면 ⇒ 자기장(B)의 세기는 증가한다.  
      R(반지름)이 증가하면 ⇒ B는 감소한다.
""")
    with col2:
        I_circ = st.slider("전류 I", -5.0, 5.0, 2.0, 0.1, key="i_circ_3d")
        R_circ = st.slider("반지름 R", 0.5, 3.0, 1.5, key="r_circ_3d")
        fig = plt.figure(figsize=(6, 6))
        ax = fig.add_subplot(111, projection='3d')
        ax.view_init(elev=25, azim=30)
        theta = np.linspace(0, 2*np.pi, 100)
        x, y = R_circ*np.cos(theta), R_circ*np.sin(theta)
        ax.plot(x, y, 0, color='gray', lw=3)
        if abs(I_circ) > 0.1:
            d = 1 if I_circ > 0 else -1
            ax.quiver(R_circ, 0, 0, 0, d, 0,
                      length=1.0, color='red', arrow_length_ratio=0.4)
            ax.quiver(0, 0, 0, 0, 0, d,
                      length=abs(I_circ), color='b', arrow_length_ratio=0.2)
        st.pyplot(fig)

    # ▶ 원형 도선 정적 그림 2장
    st.markdown("#### 원형 도선 관찰 사진")
    c1img, c2img = st.columns(2)
    with c1img:
        safe_img("circular_wire_center.png",
                 caption="원형 도선 중심의 자기장")
    with c2img:
        safe_img("circular_wire_pattern.png",
                 caption="원형 도선의 자기력선 패턴")

    # ───────────────────── 3. 솔레노이드 ─────────────────────
    st.markdown("### 3. 솔레노이드에 의한 자기장")
    st.latex(r"B = k''\,nI")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""
**방향**: 원형 도선과 동일한 오른손 법칙  
**세기**: 단위 길이당 감은 수 n와 전류의 세기 I가 증가하면 ⇒ B의 세기는 증가한다.  
**특징**: 내부에 균일한 자기장이 형성된다.
""")
    with col2:
        I_sol = st.slider("전류 I", 0.1, 5.0, 2.0, key="i_sol_3d")
        n_sol = st.slider("n (단위 길이당 감은 수)",
                          5.0, 30.0, 15.0, key="n_sol_3d")
        fig = plt.figure(figsize=(6, 5))
        ax = fig.add_subplot(111, projection='3d')
        ax.view_init(elev=20, azim=-60)
        R, L = 1, 6
        t = np.linspace(-np.pi*n_sol/2, np.pi*n_sol/2, 200)
        z = np.linspace(-L/2, L/2, 200)
        ax.plot(R*np.cos(t), R*np.sin(t), z, color='gray')
        for x_pos in [-0.5, 0, 0.5]:
            ax.quiver(x_pos, 0, -L/2, 0, 0, 1,
                      length=L*I_sol/5,
                      color='b', arrow_length_ratio=0.1)
        st.pyplot(fig)

    # ▶ 솔레노이드 정적 그림 2장
    st.markdown("#### 솔레노이드 관찰 사진")
    s1img, s2img = st.columns(2)
    with s1img:
        safe_img("solenoid_direction.png",
                 caption="솔레노이드 전류·자기장 방향")
    with s2img:
        safe_img("solenoid_iron_filings.png",
                 caption="솔레노이드 주변 철가루 패턴")



def page_example():
    st.markdown("""
칠판에 그려진 무한히 긴 직선 도선 주위 P·Q점 자기장에 대해
민수·철수·영희가 토론하였다. 옳은 사람을 고르면?""")
    safe_img("example_quiz_1.png", use_column_width=True)
    opts = ["① 민수", "② 철수", "③ 민수·철수",
            "④ 민수·영희", "⑤ 민수·철수·영희"]
    sel = st.radio("선택", opts, index=None, key="ex_sel")
    if st.button("채점 (예제)"):
        ok = sel is not None and sel.startswith("⑤")
        st.success("🎉 정답입니다!") if ok else st.error("❌ 오답입니다.")
        info = st.session_state.student_info
        append_row_to_gsheet([
            info["학번"], info["성명"], info["이동반"],
            get_check_tag(), f"예제풀이: {sel}", str(ok), "", ""
        ])
        st.markdown("**해설**: 세 명 모두 옳다 → ⑤")

def page_suneung():
    st.markdown(r"""
**[수능 응용 문제]**  
무한히 긴 직선 도선 **A, B, C** ($I_{0},\,I_{B},\,I_{0}$)가
$xy$ 평면에 놓여 있다. 표는 점 P, Q 에서 세 도선 전류가 만드는
자기장 세기를 요약한 것이다. \<보기\>에서 옳은 내용을 모두 고르시오.
""")
    safe_img("suneung_quiz_fig.png", caption="세 도선 A·B·C와 점 P·Q")
    st.markdown(r"<보기>  ㄱ. $I_{B}=I_{0}$  ㄴ. C 전류 방향은 $-y$  ㄷ. Q점 총 $\vec{B}$ 방향은 $+z$")
    opts = ["① ㄱ", "② ㄷ", "③ ㄱ, ㄴ",
            "④ ㄴ, ㄷ", "⑤ ㄱ, ㄴ, ㄷ"]
    sel = st.radio("선택", opts, index=None, key="sat_sel")
    if st.button("채점 (수능응용)"):
        ok = sel is not None and sel.startswith("②")
        st.success("🎉 정답입니다! (② ㄷ)") if ok else st.error("❌ 오답입니다.")
        info = st.session_state.student_info
        append_row_to_gsheet([
            info["학번"], info["성명"], info["이동반"],
            get_check_tag(), f"수능응용: {sel}", str(ok), "", ""
        ])
        safe_img("suneung_quiz_solution.png", caption="해설", use_column_width=True)

def page_essay():
    st.header("탐구 과제: 우리 생활 속 전자기장")
    st.markdown("""
스피커, 전자석 기중기, 전동기는 모두 전류·자기장 상호작용 원리를
사용한다. 원리를 탐구하고 AI챗봇과 토론해 보세요.
""")
    c1, c2, c3 = st.columns(3)
    with c1:
        safe_img("speaker.webp", caption="스피커")
    with c2:
        safe_img("crane.jpg", caption="전자석 기중기")
    with c3:
        safe_img("motor_structure.png", caption="전동기")

    st.subheader("💬 AI챗봇과 토론하기")
    if "essay_history" not in st.session_state:
        st.session_state.essay_history = []
    for role, msg in st.session_state.essay_history:
        st.chat_message(role).write(msg)
    if prompt := st.chat_input("세 기기의 원리에 대한 생각을 작성해보세요."):
        st.session_state.essay_history.append(("user", prompt))
        st.chat_message("user").write(prompt)
        with st.chat_message("assistant"):
            with st.spinner("GPT가 답변 중..."):
                ans = call_gpt(
                    "You are a Socratic physics mentor. Respond in Korean.",
                    prompt, 400)
                st.write(ans)
                st.session_state.essay_history.append(("assistant", ans))

def page_feedback():
    st.subheader("피드백 / 정리하기 – GPT와 학습 마무리")
    st.markdown("오늘 가장 중요하다고 생각한 점이나 어려웠던 점을 적어보세요.")
    if "feedback_history" not in st.session_state:
        st.session_state.feedback_history = [("assistant", "안녕하세요! 오늘 수업 어떠셨나요?")]
    for role, msg in st.session_state.feedback_history:
        st.chat_message(role).write(msg)
    if prompt := st.chat_input("수업 소감 또는 질문을 남겨보세요."):
        st.session_state.feedback_history.append(("user", prompt))
        st.chat_message("user").write(prompt)
        with st.chat_message("assistant"):
            with st.spinner("GPT가 답변 작성 중..."):
                ans = call_gpt(
                    "You are a friendly physics tutor. Summarize key points "
                    "and encourage the student. Respond in Korean.",
                    prompt, 500)
                st.write(ans)
                st.session_state.feedback_history.append(("assistant", ans))
                info = st.session_state.student_info
                append_row_to_gsheet([
                    info["학번"], info["성명"], info["이동반"],
                    get_check_tag(), "", "", "",
                    f"피드백: {prompt[:500]}"
                ])

    st.markdown("---")
    st.subheader("학습 내용 정리 파일 (.txt)")
    if st.button("💬 다운로드"):
        chat_text = f"===== 전류의 자기장 피드백 ({datetime.datetime.now():%Y-%m-%d %H:%M}) =====\n\n"
        for role, msg in st.session_state.feedback_history:
            chat_text += f"[{role.upper()}]\n{msg}\n\n"
        st.download_button("다운로드 시작", chat_text.encode('utf-8'),
                           file_name=f"feedback_{datetime.datetime.now():%Y%m%d}.txt",
                           mime="text/plain")

# ============================================================
#  페이지 라우팅
# ============================================================
PAGES = {
    "메인 화면": page_intro_physics,
    "학습 목표": page_goal,
    "자기장 시뮬레이션": page_simulation,
    "기본 개념 문제 (1차시)": page_basic_1,
    "전류의 자기장 실험1 : 직선 도선 주위에서 자기장 확인하기":
        lambda: page_exp("실험1 : 직선 도선 주위에서 자기장 확인하기", 1),
    "전류의 자기장 실험2 : 원형 도선의 중심에서 자기장 확인하기":
        lambda: page_exp("실험2 : 원형 도선의 중심에서 자기장 확인하기", 2),
    "전류의 자기장 실험3 : 솔레노이드에서 자기장 확인하기":
        lambda: page_exp("실험3 : 솔레노이드에서 자기장 확인하기", 3),
    "실험 결과 작성하기": page_report,
    "학습 목표": page_goal_2,
    "기본 개념 문제 (2차시)": page_basic_2,
    "전류에 의한 자기작용 이론 정리": page_theory,
    "예제 풀이": page_example,
    "수능응용 문제": page_suneung,
    "탐구 과제": page_essay,
    "피드백 / 정리하기": page_feedback,
}
# 호출
PAGES.get(step_name, page_intro_physics)()
