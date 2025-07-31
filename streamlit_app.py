# -*- coding: utf-8 -*-
"""
전류의 자기장 학습용 스트림릿 앱 (상세 콘텐츠 + GPT 기능 통합 최종본)
"""

########################  공통 import  ########################
import streamlit as st, numpy as np, matplotlib.pyplot as plt
from matplotlib import font_manager
import matplotlib.patches as patches
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.transforms import Affine2D
import os, datetime
from pathlib import Path

########################  GPT (선택 사항)  ####################
try:
    from openai import OpenAI
    GPT_ENABLED = True
except ModuleNotFoundError:
    GPT_ENABLED = False
    st.warning(
        "⚠️ `openai` 패키지가 설치돼 있지 않아 GPT 기능이 꺼져 있습니다.\n"
        "• 로컬:  `pip install openai`\n"
        "• 배포:  requirements.txt 에  openai  추가 후 재배포"
    )

def call_gpt(system_prompt: str, user_prompt: str, max_tokens: int = 256):
    """OpenAI GPT 호출 헬퍼 – API Key 는 사이드바 입력"""
    if not GPT_ENABLED:
        return "(openai 모듈 없음)"
    api_key = st.session_state.get("openai_api_key", "")
    if not api_key:
        st.warning("사이드바에 OpenAI API Key를 입력해주세요.")
        return "(API Key 미입력)"
    try:
        client = OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            max_tokens=max_tokens,
            temperature=0.7,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        st.error(f"[GPT 오류] {e}")
        return f"[GPT 오류] {e}"

########################  페이지·글꼴·글씨  ####################
st.set_page_config(
    page_title="고등학교 2학년 물리학1 전류의 자기장",
    page_icon="🧲",
    layout="wide"
)
st.markdown("""
<style>
html, body, [class*="st-"] { font-size:18px !important; }
</style>
""", unsafe_allow_html=True)

# ---- 한글 폰트 설정 ----
FONT_DIR = Path(__file__).parent / "fonts"
FONT_DIR.mkdir(exist_ok=True)
font_path = FONT_DIR / "NanumGothic-Regular.ttf"
from matplotlib import rcParams
if font_path.exists():
    font_manager.fontManager.addfont(str(font_path))
    rcParams["font.family"] = font_manager.FontProperties(fname=str(font_path)).get_name()
else:
    st.warning("⚠️ NanumGothic-Regular.ttf 폰트가 없습니다. fonts 폴더에 추가하면 한글이 깨지지 않습니다.")
rcParams["axes.unicode_minus"] = False

########################  유틸 (safe_img, GSheet)  #################
BASE_DIR = Path(__file__).parent
def safe_img(src: str, **kwargs):
    # 절대경로 대신 파일명만으로 이미지를 찾도록 수정
    cand = [
        BASE_DIR / "image" / src,
        BASE_DIR / src
    ]
    for p in cand:
        if p.exists():
            st.image(str(p), **kwargs)
            return
    st.warning(f"⚠️ 'image' 폴더에 파일 없음: {src}")

def append_row_to_gsheet(row_data):
    """Google Sheets에 한 행을 추가합니다. (st.secrets 사용)"""
    try:
        import gspread
        from google.oauth2.service_account import Credentials

        creds_dict = st.secrets["gcp_service_account"]
        scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
        client = gspread.authorize(creds)
        spreadsheet = client.open("MagFieldResponses")
        sheet = spreadsheet.sheet1
        sheet.append_row(row_data, value_input_option="USER_ENTERED")
        return True
    except gspread.exceptions.GSpreadException as e:
        st.sidebar.error(f"GSheet 오류: {e}")
        return False
    except Exception as e:
        # Key가 없는 등 다른 에러
        st.sidebar.error(f"GSheet 기록 실패: {e}")
        return False

########################  차시·메뉴 정의  ########
steps_1_all = [
    "메인 화면", "학습 목표", "자기장 시뮬레이션",
    "기본 개념 문제 (1차시)",
    "전류의 자기장 실험1 : 직선 도선 주위의 자기장 확인하기",
    "전류의 자기장 실험2 : 원형 도선 주위의 자기장 확인하기",
    "전류의 자기장 실험3 : 솔레노이드 주위의 자기장 확인하기",
    "실험 결과 작성하기",
]
steps_2 = [
    "2차시 학습 목표", "기본 개념 문제 (2차시)", "전류에 의한 자기장 이론 정리",
    "예제 풀이", "수능응용 문제", "탐구 과제", "피드백 / 정리하기",
]
steps_all = steps_1_all + steps_2
steps_1_menu = steps_1_all[1:] # 메인 화면은 메뉴에 표시 안 함
N1, N2 = len(steps_1_menu), len(steps_2)

########################  세션 상태  ###########################
if "done" not in st.session_state: st.session_state.done = [False] * len(steps_all)
if "current" not in st.session_state: st.session_state.current = 0
if "student_info" not in st.session_state:
    st.session_state.student_info = {"학번": "", "성명": "", "이동반": ""}
if "roster" not in st.session_state: st.session_state.roster = []

# 실험 페이지 상태 초기화
for i in range(1, 4):
    if f"exp{i}_text" not in st.session_state: st.session_state[f"exp{i}_text"] = ""
    if f"exp{i}_submitted" not in st.session_state: st.session_state[f"exp{i}_submitted"] = False
    if f"exp{i}_feedback" not in st.session_state: st.session_state[f"exp{i}_feedback"] = ""
if "report_submitted" not in st.session_state: st.session_state.report_submitted = False


########################  사이드바 구성  ########################
with st.sidebar:
    st.subheader("🗝️ OpenAI API Key")
    st.text_input("Key 입력", key="openai_api_key", type="password", placeholder="sk-…")
    if st.session_state.get("openai_api_key", "").startswith("sk-") and len(st.session_state.openai_api_key) > 50:
        st.success("✅ API Key 입력 확인!")


    st.markdown("---")
    st.subheader("학습자 정보")
    for k in ("학번", "성명", "이동반"):
        st.session_state.student_info[k] = st.sidebar.text_input(
            k, st.session_state.student_info[k], key=f"in_{k}")

    if st.sidebar.button("저장"):
        info = st.session_state.student_info
        tag = f"{info['학번']} {info['성명']}".strip()
        if info["학번"] and info["성명"]:
            now_str = datetime.datetime.now().strftime("%y-%m-%d %H:%M")
            full_tag = f"{tag} ({now_str})"
            if not any(tag in r for r in st.session_state.roster):
                st.session_state.roster.append(full_tag)
            log_data = [datetime.datetime.now().isoformat(), *info.values(), "정보 입력"]
            if append_row_to_gsheet(log_data):
                st.sidebar.success("저장 완료!")
        else:
            st.sidebar.warning("학번·성명을 입력하세요.")
    
    st.markdown("#### 🗂️ 접속 확인")
    for tag in st.session_state.roster or ["_아직 없음_"]:
        st.markdown(f"- {tag}")
    st.markdown("---")


st.sidebar.success("💡 아래 버튼을 클릭하면 해당 내용으로 이동합니다. 진행을 완료하면 ✅가 표시됩니다.")

st.sidebar.markdown("#### 수업 내용")
st.sidebar.caption("""
1차시 : 전류의 자기장 실험  
2차시 : 전류의 자기작용 이론 정리
""")
if st.sidebar.button("🤖 AI 챗봇 (첫 화면)"):
    st.session_state.current = 0
    st.rerun()

p1 = sum(st.session_state.done[1:1 + N1]) / N1 if N1 > 0 else 0
st.sidebar.markdown(f"### 1차시 진행률 : {int(p1 * 100)}%")
st.sidebar.progress(p1)
for i, n in enumerate(steps_1_menu, start=1):
    label = f"{'✅' if st.session_state.done[i] else '○'} {n}"
    if st.sidebar.button(label, key=f"btn1_{i}"):
        st.session_state.current = i
        st.session_state.done[i] = True
        st.rerun()

p2 = sum(st.session_state.done[len(steps_1_all):]) / N2 if N2 > 0 else 0
st.sidebar.markdown(f"### 2차시 진행률 : {int(p2 * 100)}%")
st.sidebar.progress(p2)
for i, n in enumerate(steps_2, start=len(steps_1_all)):
    label = f"{'✅' if st.session_state.done[i] else '○'} {n}"
    if st.sidebar.button(label, key=f"btn2_{i}"):
        st.session_state.current = i
        st.session_state.done[i] = True
        st.rerun()

step_name = steps_all[st.session_state.current]
st.header(f"📝 {step_name}")

########################  페이지 함수들 (상세 콘텐츠)  ################
def page_intro_physics():
    st.title("물리학1")
    st.header("(2)단원 물질과 전자기장")
    st.subheader("전류의 자기작용")
    st.markdown("---")
    
    st.title("💡 전자기장과 우리 생활")
    st.markdown("""
    1820년, 덴마크의 물리학자 **한스 크리스티안 외르스테드(Hans Christian Ørsted)**는 강의 중 놀라운 현상을 발견합니다.
    전류가 흐르는 전선 주위에서 나침반의 바늘이 움직이는 것을 목격한 것입니다.
    이 우연한 발견은 이전까지 별개의 현상으로 여겨졌던 **전기**와 **자기**가 사실은 깊은 관련이 있음을 최초로 증명한 역사적인 순간이었습니다.
    
    외르스테드의 발견은 전자기학의 시대를 열었고, 이는 오늘날 우리가 사용하는 모터, 발전기, 스피커, 전자석 등 수많은 기술의 기초가 되었습니다.
    이 단원에서는 전류가 어떻게 자기장을 만들어내는지, 그 원리를 탐구하고 우리 생활에 어떻게 적용되는지 알아봅니다.
    """)
    safe_img("oersted_experiment.png", caption="외르스테드의 실험(1820): 전기와 자기의 연결고리를 발견하다")

    st.markdown("---")
    c1, c2 = st.columns(2)
    with c1:
        safe_img("speaker.webp", caption="스피커: 코일에 흐르는 전류와 자석의 상호작용으로 소리를 만듭니다.", use_column_width=True)
    with c2:
        safe_img("crane.jpg", caption="전자석 기중기: 강한 전류를 흘려보내 무거운 쇠붙이를 들어 올립니다.", use_column_width=True)

    st.markdown("#### 💬 GPT와 대화하기")
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    for role, msg in st.session_state.chat_history:
        st.chat_message(role).write(msg)
    if prompt := st.chat_input("전류·자기장에 대해 궁금한 점을 물어보세요"):
        st.session_state.chat_history.append(("user", prompt))
        st.chat_message("user").write(prompt)
        with st.chat_message("assistant"):
            with st.spinner("GPT가 답변 중…"):
                ans = call_gpt(
                    "You are a helpful physics tutor. Answer in Korean, clearly and friendly.",
                    prompt, max_tokens=500)
                st.write(ans)
                st.session_state.chat_history.append(("assistant", ans))

def page_goal():
    st.markdown("""
    ### 1차시 학습 목표
    1. 전류에 의한 자기 작용이 일상생활에서 적용되는 다양한 예를 찾아 그 원리를 설명할 수 있다.
    2. 직선, 원형, 솔레노이드 도선 주위에 전류가 흐를 때 생기는 자기장의 모양을 설명할 수 있다.
    """)
    
def page_goal_2():
    st.markdown("""
    ### 2차시 학습 목표
    1. 직선 전류, 원형 전류, 솔레노이드에서 생성되는 자기장의 **방향**과 **세기**를 파악한다.
    2. 전자기장 원리가 적용된 일상생활의 다양한 사례를 탐색하고 설명한다.
    """)

def page_simulation():
    L, R = st.columns(2)
    with L:
        safe_img("magnet_lines_compass.png", caption="막대자석 자기력선·나침반")
    with R:
        st.markdown("**자기장**: 자기력이 작용하는 공간")
        st.markdown("**자기력선**: 눈에 보이지 않는 자기장을 나타낸 가상의 선")
        st.markdown("""∙ N극에서 S극으로 향하는 폐곡선  
∙ 갈라지거나 교차하지 않음  
∙ 간격이 좁을수록 자기장 세기 ↑  
∙ 한 점에서의 접선 방향 = 그 점의 자기장 방향""")

    st.markdown("---")
    st.markdown("### ⚡ 막대자석 주위 자기력선 시뮬레이션")
    st.markdown("자석의 세기, 방향, 시각화 옵션을 조절하며 자기장의 특징을 관찰해보세요.")

    c1, c2 = st.columns([1, 3])
    with c1:
        strength = st.slider("🔧 막대자석 세기", 0.5, 5.0, 1.0, 0.1)
        orient = st.selectbox("자석 축", ["세로(z)", "가로(x)"], 0)
        dens = st.slider("화살표 밀도", 15, 40, 25, 5)
        show_f = st.checkbox("자기력선", True)
        show_c = st.checkbox("자기장 세기(색)", True)
        show_v = st.checkbox("자기장 방향(화살표)", True)

    mag_len, mag_w = 1.2, 0.4
    if orient == "세로(z)": north = np.array([0, mag_len / 2]); south = -north
    else: north = np.array([mag_len / 2, 0]); south = -north

    x = np.linspace(-3, 3, dens); y = np.linspace(-3, 3, dens); X, Y = np.meshgrid(x, y)
    RX, RY = X - north[0], Y - north[1]; SX, SY = X - south[0], Y - south[1]
    rN = np.sqrt(RX ** 2 + RY ** 2) + 1e-9; rS = np.sqrt(SX ** 2 + SY ** 2) + 1e-9
    Bx = strength * (RX / rN ** 3 - SX / rS ** 3); By = strength * (RY / rN ** 3 - SY / rS ** 3)
    
    if orient == "세로(z)": inside = (np.abs(X) < mag_w / 2) & (np.abs(Y) < mag_len / 2)
    else: inside = (np.abs(X) < mag_len/2) & (np.abs(Y) < mag_w/2)
    B_mag = np.sqrt(Bx**2 + By**2)
    if np.any(inside): Bx[inside], By[inside], B_mag[inside] = 0, 0, 0
    
    with c2:
        fig, ax = plt.subplots(figsize=(7, 7))
        ax.set_aspect('equal'); ax.set_xlim(-3, 3); ax.set_ylim(-3, 3); ax.grid(True, ls='--', alpha=0.3)
        if orient == "세로(z)":
            ax.add_patch(patches.Rectangle((-mag_w / 2, 0), mag_w, mag_len / 2, fc="#DC143C", ec="k", zorder=10))
            ax.add_patch(patches.Rectangle((-mag_w / 2, -mag_len / 2), mag_w, mag_len / 2, fc="#4169E1", ec="k", zorder=10))
        else:
            ax.add_patch(patches.Rectangle((0, -mag_w / 2), mag_len / 2, mag_w, fc="#DC143C", ec="k", zorder=10))
            ax.add_patch(patches.Rectangle((-mag_len / 2, -mag_w / 2), mag_len / 2, mag_w, fc="#4169E1", ec="k", zorder=10))
        ax.text(north[0], north[1] + 0.2, "N", color="black", ha="center", weight="bold")
        ax.text(south[0], south[1] - 0.2, "S", color="black", ha="center", weight="bold")
        
        if show_c:
            cmap = LinearSegmentedColormap.from_list("mag", ["white", "skyblue", "royalblue", "navy"])
            # 자기장 세기가 거리에 따라 급격히 변하므로 로그 스케일로 색상 표현
            cf = ax.contourf(X, Y, np.log10(B_mag + 1), levels=20, cmap=cmap, alpha=0.7)
        if show_f: ax.streamplot(X, Y, Bx, By, color="k", density=1.5, linewidth=1, zorder=5)
        if show_v: ax.quiver(X, Y, Bx / (B_mag+1e-9), By / (B_mag+1e-9), B_mag, cmap="viridis", scale=40, width=0.004)

        ax.set_title("막대자석 주변 자기장")
        st.pyplot(fig)

    st.markdown("---")
    st.markdown("### 🧲↔️🧲 두 자석의 상호작용 시뮬레이션")
    st.markdown("두 자석 사이의 거리를 조절하며 합성 자기장이 어떻게 변하는지 관찰해보세요.")
    
    c1, c2 = st.columns([1, 3])
    with c1:
        interaction = st.radio("자석 배치", ["N극-S극 (인력)", "N극-N극 (척력)"])
        distance = st.slider("두 자석 중심 사이 거리", 1.5, 4.0, 2.5, 0.1)
        strength2 = st.slider("자석 세기 (동일)", 0.5, 3.0, 1.0, 0.1, key="s2")

    x = np.linspace(-4, 4, 30); y = np.linspace(-3, 3, 25); X, Y = np.meshgrid(x, y)
    
    # 첫번째 자석 (왼쪽)
    n1 = np.array([-distance/2, 0]); s1 = np.array([-distance/2 - 0.8, 0])
    B_x1 = strength2 * ((X - n1[0]) / ((X - n1[0])**2 + (Y - n1[1])**2)**1.5 - (X - s1[0]) / ((X - s1[0])**2 + (Y - s1[1])**2)**1.5)
    B_y1 = strength2 * ((Y - n1[1]) / ((X - n1[0])**2 + (Y - n1[1])**2)**1.5 - (Y - s1[1]) / ((X - s1[0])**2 + (Y - s1[1])**2)**1.5)

    # 두번째 자석 (오른쪽)
    if interaction == "N극-S극 (인력)":
        s2 = np.array([distance/2, 0]); n2 = np.array([distance/2 + 0.8, 0])
    else: # N극-N극
        n2 = np.array([distance/2, 0]); s2 = np.array([distance/2 + 0.8, 0])

    B_x2 = strength2 * ((X - n2[0]) / ((X - n2[0])**2 + (Y - n2[1])**2)**1.5 - (X - s2[0]) / ((X - s2[0])**2 + (Y - s2[1])**2)**1.5)
    B_y2 = strength2 * ((Y - n2[1]) / ((X - n2[0])**2 + (Y - n2[1])**2)**1.5 - (Y - s2[1]) / ((X - s2[0])**2 + (Y - s2[1])**2)**1.5)
    
    # 합성 자기장
    Bx_total, By_total = B_x1 + B_x2, B_y1 + B_y2
    B_mag_total = np.sqrt(Bx_total**2 + By_total**2)

    with c2:
        fig2, ax2 = plt.subplots(figsize=(9, 6))
        ax2.set_aspect('equal'); ax2.set_xlim(-4, 4); ax2.set_ylim(-3, 3); ax2.grid(True, ls='--', alpha=0.3)
        ax2.streamplot(X, Y, Bx_total, By_total, color='k', density=2.0, linewidth=1)
        
        # 자석 그리기
        ax2.add_patch(patches.Rectangle((s1[0], -0.2), 0.8, 0.4, fc='#4169E1', ec='k'))
        ax2.add_patch(patches.Rectangle((n1[0], -0.2), 0, 0.4, fc='#DC143C', ec='k')) # N극 표시
        if interaction == "N극-S극 (인력)":
            ax2.add_patch(patches.Rectangle((s2[0], -0.2), 0.8, 0.4, fc='#4169E1', ec='k'))
        else:
            ax2.add_patch(patches.Rectangle((n2[0], -0.2), 0.8, 0.4, fc='#DC143C', ec='k', zorder=10))
            ax2.add_patch(patches.Rectangle((s2[0], -0.2), 0, 0.4, fc='#4169E1', ec='k'))
            
        ax2.set_title(f"두 자석의 합성 자기장 ({interaction})")
        st.pyplot(fig2)


def page_basic_1():
    safe_img("magnet_quiz_1.png", width=600)
    ans = st.text_input("A 지점에 있는 나침반의 N극이 가리키는 방향은? (동, 서, 남, 북 중 선택)")
    if st.button("채점"):
        ok = "동" in ans
        if ok: st.success("🎉 정답입니다!")
        else: st.error("❌ 오답입니다. 자기력선은 N극에서 나와서 S극으로 들어갑니다. A지점에서 자기력선의 접선 방향(나아가는 방향)을 생각해보세요.")


def page_exp(title: str, label_code: str, exp_num: int):
    info = {
        "실험1": {"img": "exp_straight_wire.png", "caption": "직선 도선 주위의 나침반 관찰하기 : 그림처럼 회로를 연결하고 스위치를 닫았을 때, 직선 도선 주위에 있는 나침반의 N극이 어떻게 움직이는지 관찰한다. "},
        "실험2": {"img": "exp_circular_wire.png", "caption": "원형 도선 중심·주위의 나침반 관찰하기 : 그림처럼 회로를 연결하고 스위치를 닫았을 때, 원형 도선의 가운데에 있는 나침반의 N극이 어떻게 움직이는지 관찰한다."},
        "실험3": {"img": "exp_solenoid.png", "caption": "솔레노이드 내부·외부의 나침반 관찰하기 : 그림처럼 회로를 연결하고 스위치를 닫았을 때, 솔레노이드 중심축에 위치한 나침반의 N극이 어떻게 움직이는지 관찰한다."},
    }[label_code]

    st.markdown(f"### {title}")
    safe_img(info["img"], caption=info["caption"])

    text_key = f"exp{exp_num}_text"
    submitted_key = f"exp{exp_num}_submitted"
    feedback_key = f"exp{exp_num}_feedback"
    
    # 제출되지 않았을 때만 입력 UI 활성화
    if not st.session_state[submitted_key]:
        obs = st.text_area("전류가 흐를 때, 나침반의 N극이 어떻게 움직이는지 설명하시오.", 
                           value=st.session_state[text_key], height=150, key=f"ta_{label_code}")
        st.session_state[text_key] = obs
        
        if st.session_state[text_key]:
            st.success("✅ 입력 완료")

        if st.button("제출 및 GPT 피드백 받기", key=f"btn_{label_code}"):
            if st.session_state[text_key]:
                with st.spinner("GPT가 피드백을 생성 중입니다..."):
                    system_prompt = "You are a physics teacher providing feedback. The student has described their observation of a magnetics experiment. Analyze their description, point out good observations, and suggest what they could describe more specifically (e.g., direction, relation to current). Respond concisely in Korean."
                    user_prompt = f"다음은 학생의 '{title}' 실험 관찰 기록입니다: '{st.session_state[text_key]}'. 이 내용에 대해 피드백해주세요."
                    feedback = call_gpt(system_prompt, user_prompt, max_tokens=200)
                    st.session_state[feedback_key] = feedback
                
                st.session_state[submitted_key] = True
                log_data = [datetime.datetime.now().isoformat(), *st.session_state.student_info.values(), label_code, st.session_state[text_key][:300], feedback]
                append_row_to_gsheet(log_data)
                st.rerun() # 상태 변경 후 UI 갱신
            else:
                st.warning("관찰한 내용을 입력해주세요.")
    
    # 제출된 후에는 내용과 피드백을 보여주고 수정 버튼 제공
    if st.session_state[submitted_key]:
        st.markdown("---")
        st.markdown("##### 📝 나의 관찰 기록")
        st.info(st.session_state[text_key])
        st.markdown("##### 🤖 GPT 피드백")
        st.success(st.session_state[feedback_key])
        if st.button("수정하기", key=f"edit_{label_code}"):
            st.session_state[submitted_key] = False
            st.rerun()

def page_report():
    ## GSheet 헤더 예시:
    ## Timestamp, 학번, 성명, 이동반, 구분, 보고서내용1, 보고서내용2, 보고서내용3, GPT피드백
    ## 예시 데이터:
    ## 2023-10-27T12:00:00, 20901, 홍길동, 물리A, 실험결과보고서, "전류계를 연결하고...", "전류 I와 자기장 B는 비례...", "새로운 아이디어는...", "피드백 내용..."

    st.info("세 가지 항목을 모두 작성하고 마지막 '최종 보고서 제출' 버튼을 눌러주세요.")

    if not st.session_state.report_submitted:
        txt1 = st.text_area("(1) 직선 전류가 만드는 자기장의 세기에 영향을 미치는 요소를 확인할 수 있는 실험 방법을 요약하시오.\n[※ 새로운 실험을 설계하거나, 검색한 실험 방법을 설명하면 됩니다.]", height=150, key="rep1")
        txt2 = st.text_area("(2) 직선 전류가 만드는 자기장의 세기에 영향을 미치는 요소와 자기장 세기의 관계를 설명하시오.", height=150, key="rep2")
        txt3 = st.text_area("(3) 새로운 아이디어 제시, 자신의 역할, 잘하거나 좋았던 점을 추가로 작성하시오.", height=150, key="rep3")

        if st.button("🔬 최종 보고서 제출 및 GPT 요약 받기", type="primary"):
            if txt1 and txt2 and txt3:
                with st.spinner("GPT가 보고서를 요약하고 피드백을 생성 중입니다..."):
                    full_report = f"항목1: {txt1}\n\n항목2: {txt2}\n\n항목3: {txt3}"
                    system_prompt = "You are a helpful physics teaching assistant. A student has submitted a lab report. Briefly summarize the key points of their report and provide one constructive feedback for improvement. Respond in Korean."
                    user_prompt = f"다음은 학생의 실험 결과 보고서입니다:\n{full_report}\n\n이 보고서의 내용을 간략히 요약하고, 건설적인 피드백을 한 가지 제시해주세요."
                    feedback = call_gpt(system_prompt, user_prompt, max_tokens=300)
                
                # 세션 상태에 저장
                st.session_state.report_text1 = txt1
                st.session_state.report_text2 = txt2
                st.session_state.report_text3 = txt3
                st.session_state.report_feedback = feedback
                st.session_state.report_submitted = True

                # 구글 시트에 기록
                log_data = [
                    datetime.datetime.now().isoformat(),
                    *st.session_state.student_info.values(),
                    "실험결과보고서",
                    txt1[:500], txt2[:500], txt3[:500], feedback[:500]
                ]
                append_row_to_gsheet(log_data)
                st.rerun()
            else:
                st.warning("세 항목을 모두 작성해야 제출할 수 있습니다.")

    if st.session_state.report_submitted:
        st.success("보고서가 성공적으로 제출되었습니다. 아래는 제출된 내용입니다.")
        st.markdown("---")
        st.markdown("#### (1) 실험 방법 요약")
        st.text(st.session_state.get("report_text1", ""))
        st.markdown("#### (2) 요소와 관계 설명")
        st.text(st.session_state.get("report_text2", ""))
        st.markdown("#### (3) 추가 아이디어 및 소감")
        st.text(st.session_state.get("report_text3", ""))
        st.markdown("---")
        st.markdown("### 🤖 GPT 종합 피드백")
        st.info(st.session_state.get("report_feedback", ""))
        st.warning("제출이 완료되어 더 이상 수정할 수 없습니다.")

def page_basic_2():
    safe_img("basic_quiz_2.png")
    st.markdown("""그림은 직선 도선 아래 나침반 자침을 **북-남 방향**으로 맞춘 실험 장치이다. 가변 저항을 조절하며 도선 전류와 자침 움직임을 관찰하였다.""")
    st.markdown("**1. 실험 과정에서 관찰한 내용으로 옳지 않은 것은?**")
    opts = ["① 스위치가 열려 있을 때 자침의 극은 북쪽을 가리킨다.", "② 스위치를 닫으면 자침의 극은 동쪽으로 움직인다.", "③ 전류를 증가시키면 자침의 극은 남쪽을 가리킨다.", "④ 전류를 증가시키면 자침의 극이 회전한 각도가 증가한다.", "⑤ 전류의 방향을 반대로 바꾸면 자침의 극은 서쪽으로 움직인다."]
    sel = st.radio("선택", opts, index=None, key="basic2_sel")
    if st.button("채점(2차시)"):
        ok = sel is not None and sel.startswith("③")
        if ok: st.success("🎉 정답입니다!")
        else: st.error("❌ 오답입니다. 다시 생각해보세요.")
        append_row_to_gsheet([datetime.datetime.now().isoformat(), *st.session_state.student_info.values(), "기본2", sel, ok])
        st.markdown(r"""<br>**풀이**  
① 전류가 없으면 자침은 지구 자기장에 의해 **북쪽**을 가리킨다. (O)  
② 스위치를 닫으면 오른손 법칙에 따라 전류에 의한 자기장이 **동쪽**으로 작용하여 자침이 동쪽으로 회전한다. (O)  
④ 전류 \(I\)가 증가하면 전류에 의한 자기장 \(B\)도 강해져 회전 각도가 커진다. (O)  
⑤ 전류 방향을 반대로 하면 자기장 방향도 반대(**서쪽**)가 되어 자침이 서쪽으로 회전한다. (O)  
③ 전류가 흐를 때 자기장은 지구 자기장(북)과 도선 자기장(동)의 **벡터 합성**으로 **북동쪽**을 향한다. 자침이 남쪽을 가리키는 일은 없다. (X)""")

def page_theory():
    st.markdown("## ⊙ 전류가 만드는 자기장 — 앙페르(오른나사) 법칙")
    safe_img("ampere_law_overview.png", caption="앙페르 법칙 개념도")

    st.markdown("---")
    st.markdown("### 1. 무한히 긴 **직선 도선** 시뮬레이션")
    st.latex(r"B = k \frac{I}{r} \quad (k = \frac{\mu_0}{2\pi})")
    
    c1, c2 = st.columns([1, 2])
    with c1:
        current_I = st.slider("전류의 세기 (I)", 0.1, 5.0, 2.0, key="i_str")
        current_dir = st.radio("전류의 방향", ["나오는 방향 (⊙)", "들어가는 방향 (⊗)"], key="dir_str")

    fig, ax = plt.subplots(figsize=(6, 6))
    ax.set_aspect('equal'); ax.set_xlim(-5, 5); ax.set_ylim(-5, 5)
    
    # 도선 표시
    symbol = '⊙' if current_dir == "나오는 방향 (⊙)" else '⊗'
    ax.add_patch(patches.Circle((0, 0), 0.3, color='gray'))
    ax.text(0, 0, symbol, ha='center', va='center', fontsize=20, weight='bold')

    # 자기장 시각화
    x = np.linspace(-5, 5, 20); y = np.linspace(-5, 5, 20); X, Y = np.meshgrid(x, y)
    r = np.sqrt(X**2 + Y**2) + 1e-9
    B_mag = current_I / r
    # 오른손 법칙에 따른 방향
    dir_sign = 1 if current_dir == "나오는 방향 (⊙)" else -1
    Bx = -dir_sign * Y / r * B_mag
    By = dir_sign * X / r * B_mag
    ax.streamplot(X, Y, Bx, By, color=B_mag, cmap='plasma', linewidth=1.5, density=1.5)
    ax.set_title("직선 전류 주위 자기장")
    with c2:
        st.pyplot(fig)

    st.markdown("---")
    st.markdown("### 2. **원형 도선** (중심) 시뮬레이션")
    st.latex(r"B_{center} = k' \frac{I}{R} \quad (k' = \frac{\mu_0}{2})")
    
    c1, c2 = st.columns([1, 2])
    with c1:
        current_I_circ = st.slider("전류의 세기 (I)", 0.1, 5.0, 2.0, key="i_circ")
        radius_R = st.slider("도선 반지름 (R)", 0.5, 3.0, 1.5, key="r_circ")
        
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.set_xlim(-4, 4); ax.set_ylim(-3, 3); ax.set_aspect('equal')
    
    # 원형 도선 (옆에서 본 모습)
    ax.add_patch(patches.Ellipse((0, radius_R), 0.5, 0.2, color='gray'))
    ax.add_patch(patches.Ellipse((0, -radius_R), 0.5, 0.2, color='gray'))
    ax.text(0.5, radius_R, '⊗', ha='center', va='center', fontsize=15) # 위쪽 들어감
    ax.text(0.5, -radius_R, '⊙', ha='center', va='center', fontsize=15) # 아래쪽 나옴

    # 자기장 시각화
    x = np.linspace(-4, 4, 20); y = np.linspace(-3, 3, 20); X, Y = np.meshgrid(x, y)
    # Biot-Savart 근사
    B_center_mag = current_I_circ / radius_R
    Bx = B_center_mag * (1 / (1 + (X/radius_R)**2)**1.5)
    By = np.zeros_like(Bx)
    ax.streamplot(X, Y, Bx, By, color=np.log(Bx+1), cmap='plasma', linewidth=1.5, density=2)
    ax.set_title(f"원형 전류 중심 자기장 (B ∝ {current_I_circ/radius_R:.2f})")
    with c2:
        st.pyplot(fig)

    st.markdown("---")
    st.markdown("### 3. **솔레노이드** (내부) 시뮬레이션")
    st.latex(r"B_{internal} = \mu_0 n I \quad\bigl(n=\tfrac{N}{L}\text{, 단위 길이당 감은 수}\bigr)")
    
    c1, c2 = st.columns([1, 2])
    with c1:
        current_I_sol = st.slider("전류의 세기 (I)", 0.1, 5.0, 2.0, key="i_sol")
        n_density = st.slider("단위 길이당 감은 수 (n)", 5, 50, 20, key="n_sol")
        
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.set_xlim(-5, 5); ax.set_ylim(-3, 3)

    # 솔레노이드 코일 그리기
    sol_len = 8; sol_h = 2
    ax.add_patch(patches.Rectangle((-sol_len/2, -sol_h/2), sol_len, sol_h, fill=False, ec='k', lw=2))
    for i in np.linspace(-sol_len/2, sol_len/2, int(n_density/5)):
        ax.text(i, sol_h/2, '⊗', ha='center', va='center')
        ax.text(i, -sol_h/2, '⊙', ha='center', va='center')

    # 자기장
    x = np.linspace(-5, 5, 20); y = np.linspace(-3, 3, 20); X, Y = np.meshgrid(x, y)
    Bx = np.zeros_like(X)
    By = np.zeros_like(Y)
    inside = (np.abs(X) < sol_len/2) & (np.abs(Y) < sol_h/2)
    B_mag_sol = current_I_sol * n_density
    Bx[inside] = B_mag_sol
    
    ax.streamplot(X, Y, Bx, By, color='k', linewidth=1.5, density=1.0)
    ax.set_title(f"솔레노이드 내부 자기장 (B ∝ {B_mag_sol:.1f})")
    with c2:
        st.pyplot(fig)

def page_example():
    safe_img("example_quiz_1.png", use_column_width=True)
    st.markdown("""그림은 세 학생 민수, 철수, 영희가 칠판에 그려진 전류가 흐르는 가늘고 무한히 긴 직선 도선 주위의 P점과 Q점에 생기는 자기장에 대해 대화하는 모습을 나타낸 것이다. **문제**: P점과 Q점에서 발생하는 자기장에 대해 옳게 설명한 사람만을 있는 대로 고른 것은?""")
    opts = ["① 민수", "② 철수", "③ 민수, 철수", "④ 민수, 영희", "⑤ 민수, 철수, 영희"]
    sel = st.radio("선택", opts, index=None, key="ex_sel")
    if st.button("채점 예제"):
        ok = sel is not None and sel.startswith("⑤")
        if ok: st.success("🎉 정답입니다! (⑤)")
        else: st.error("❌ 오답입니다. 다시 생각해보세요.")
        append_row_to_gsheet([datetime.datetime.now().isoformat(), *st.session_state.student_info.values(), "예제", sel, ok])
        st.markdown("""**해설**
* **민수**: *“자기장의 세기는 전류의 세기에 비례한다.”* (✔️ 옳음. \(B \propto I\))
* **철수**: *“앙페르 법칙(오른나사 법칙)에 따라 전류 방향이 바뀌면 자기장 방향도 바뀐다.”* (✔️ 옳음)
* **영희**: *“자기장의 세기는 도선으로부터의 수직 거리에 반비례한다.”* (✔️ 옳음. \(B \propto 1/r\), 따라서 P점의 자기장이 Q점보다 세다)
→ 세 명 모두 옳으므로 **⑤ 민수, 철수, 영희**가 정답입니다.""")

def page_suneung():
    safe_img("suneung_quiz_fig.png", caption="세 도선 A·B·C와 점 P, Q")
    st.markdown(r"""**1.** 그림과 같이 무한히 긴 직선 도선 **A, B, C** ($I_{0},\, I_{B},\, I_{0}$)가 $xy$ 평면 위에 고정되어 있다. **A** 전류의 방향은 $-x$ 축이다.  
표는 점 **P, Q**에서 세 도선 전류가 만드는 자기장 세기를 나타낸다 (점 P에서 A 전류의 $B = B_{0}$).  
다음 \<보기\>에서 옳은 내용을 **모두** 고르시오.""")
    st.markdown(r"""<보기>  
ㄱ. $I_{B}=I_{0}$  
ㄴ. C 전류 방향은 $-y$ 방향이다.  
ㄷ. Q점에서 A·B·C 전류에 의한 총 $\vec{B}$ 방향은 $+z$ ( $xy$ 평면에 수직 )이다.""")
    opts = ["① ㄱ", "② ㄷ", "③ ㄱ, ㄴ", "④ ㄴ, ㄷ", "⑤ ㄱ, ㄴ, ㄷ"]
    sel = st.radio("선택", opts, index=None, key="sat_sel")
    if st.button("채점 응용"):
        ok = sel is not None and sel.startswith("②")
        if ok: st.success("🎉 정답입니다! (② ㄷ)")
        else: st.error("❌ 오답입니다.")
        append_row_to_gsheet([datetime.datetime.now().isoformat(), *st.session_state.student_info.values(), "응용", sel, ok])
        safe_img("suneung_quiz_solution.png", caption="해설", use_column_width=True)

def page_essay():
    safe_img("motor_structure.png", caption="전동기 구조와 작동 개념")
    safe_img("force_on_wire.png", caption="자기장 속 도선이 받는 힘 (F = I L × B)")
    st.markdown("---")

    st.subheader("탐구 과제 – GPT와 토론하며 전동기 원리 탐구하기")
    st.markdown("자기장 안에서 전류가 흐르는 도선이 받는 힘을 설명하고, **전동기의 원리를 탐구**하여 아래 채팅창에 작성하고 GPT와 토론해보세요. GPT가 여러분의 생각을 발전시킬 수 있도록 질문을 던질 것입니다.")
    
    if "essay_history" not in st.session_state:
        st.session_state.essay_history = []
    
    for role, msg in st.session_state.essay_history:
        st.chat_message(role).write(msg)
        
    if prompt := st.chat_input("전동기 원리에 대한 자신의 생각을 작성해보세요."):
        st.session_state.essay_history.append(("user", prompt))
        st.chat_message("user").write(prompt)
        with st.chat_message("assistant"):
            with st.spinner("GPT가 답변을 생성 중입니다..."):
                ans = call_gpt(
                    "You are an encouraging physics mentor for Korean high-school students, using the Socratic method. The student is exploring the principles of an electric motor. Your goal is to guide them to a deeper understanding, not just give the answer. Ask thought-provoking questions, challenge their assumptions gently, and prompt them to connect different concepts (e.g., 'That's a great start! Why does the coil keep rotating instead of stopping?'). Respond in Korean.",
                    prompt, max_tokens=400)
                st.write(ans)
                st.session_state.essay_history.append(("assistant", ans))

def page_feedback():
    st.subheader("피드백 / 정리하기 – GPT와 함께 학습 내용 정리")
    st.markdown("오늘 배운 내용 중 가장 중요하다고 생각하는 점, 어려웠던 점, 또는 더 궁금한 점을 GPT에게 이야기하며 학습을 마무리하세요. GPT가 여러분의 생각을 정리하고 답변해 줄 것입니다.")
    
    if "feedback_history" not in st.session_state:
        st.session_state.feedback_history = [
            ("assistant", "안녕하세요! 오늘 '전류의 자기장' 수업 어떠셨나요? 가장 기억에 남는 내용이나 어려웠던 점이 있다면 편하게 이야기해주세요. 제가 정리를 도와드릴게요.")
        ]
        
    for role, msg in st.session_state.feedback_history:
        st.chat_message(role).write(msg)
        
    if prompt := st.chat_input("수업 소감이나 질문을 자유롭게 남겨보세요."):
        st.session_state.feedback_history.append(("user", prompt))
        st.chat_message("user").write(prompt)
        with st.chat_message("assistant"):
            with st.spinner("GPT가 답변을 준비 중입니다..."):
                ans = call_gpt(
                    "You are a friendly and helpful physics tutor. The student is giving feedback on a lesson about magnetism from current. Summarize their key points, answer their questions clearly, and give them encouragement for their learning journey. Respond in Korean.",
                    prompt, max_tokens=500)
                st.write(ans)
                st.session_state.feedback_history.append(("assistant", ans))
                # GSheet에 학생 피드백 기록
                append_row_to_gsheet([datetime.datetime.now().isoformat(), *st.session_state.student_info.values(), "피드백(GPT)", prompt[:500]])

########################  페이지 라우팅  ################
PAGES = {
    "메인 화면": page_intro_physics,
    "학습 목표": page_goal,
    "2차시 학습 목표": page_goal_2,
    "자기장 시뮬레이션": page_simulation,
    "기본 개념 문제 (1차시)": page_basic_1,
    "전류의 자기장 실험1 : 직선 도선 주위의 자기장 확인하기": lambda: page_exp("전류의 자기장 실험1", "실험1", 1),
    "전류의 자기장 실험2 : 원형 도선 주위의 자기장 확인하기": lambda: page_exp("전류의 자기장 실험2", "실험2", 2),
    "전류의 자기장 실험3 : 솔레노이드 주위의 자기장 확인하기": lambda: page_exp("전류의 자기장 실험3", "실험3", 3),
    "실험 결과 작성하기": page_report,
    "기본 개념 문제 (2차시)": page_basic_2,
    "전류에 의한 자기장 이론 정리": page_theory,
    "예제 풀이": page_example,
    "수능응용 문제": page_suneung,
    "탐구 과제": page_essay,
    "피드백 / 정리하기": page_feedback,
}

# 현재 선택된 step_name에 해당하는 페이지 함수를 실행
if step_name in PAGES:
    PAGES[step_name]()
else:
    page_intro_physics() # 혹시 모를 예외 발생 시 첫 페이지로