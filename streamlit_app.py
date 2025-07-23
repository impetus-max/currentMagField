# =====================================================================
#   고2 물리 – 전류의 자기장  ▶  ‘참여형’ Streamlit 수업 앱  (rev 5)
# =====================================================================
import streamlit as st, numpy as np, matplotlib.pyplot as plt
from matplotlib import font_manager
import os, datetime, time

# ---------------- (선택) Google-Sheets 기록 --------------------------
def append_row_to_gsheet(row):
    try:
        import gspread, oauth2client.service_account
        creds_path = os.getenv("GSHEET_JSON", "")
        if not os.path.exists(creds_path):
            return
        scope = ["https://www.googleapis.com/auth/spreadsheets",
                 "https://www.googleapis.com/auth/drive"]
        creds = oauth2client.service_account.ServiceAccountCredentials \
                .from_json_keyfile_name(creds_path, scope)
        gspread.authorize(creds).open("MagFieldResponses") \
               .sheet1.append_row(row, value_input_option="USER_ENTERED")
    except Exception:
        pass
# --------------------------------------------------------------------

# ---------------- 한글 폰트 -----------------------------------------
FONT_DIR = "/workspaces/currentMagField/fonts"
for w in ("Regular", "Bold", "ExtraBold"):
    fp = f"{FONT_DIR}/NanumGothic-{w}.ttf"
    if os.path.exists(fp):
        font_manager.fontManager.addfont(fp)
if os.path.exists(f"{FONT_DIR}/NanumGothic-Regular.ttf"):
    plt.rcParams["font.family"] = font_manager.FontProperties(
        fname=f"{FONT_DIR}/NanumGothic-Regular.ttf").get_name()
plt.rcParams["axes.unicode_minus"] = False
# --------------------------------------------------------------------

# ---------------- 차시·메뉴 -----------------------------------------
steps_1 = [
    "물리학1 전류의 자기작용",     # 👈 인트로 첫 화면 추가!
    "수업 소개",
    "학습 목표",
    "전류의 자기장 개념 확인",
    "기본 개념 문제 (1차시)",
    "전류의 자기장 실험1 : 직선 도선 주위의 자기장 확인하기",
    "전류의 자기장 실험2 : 원형 도선 주위의 자기장 확인하기",
    "전류의 자기장 실험3 : 솔레노이드 주위의 자기장 확인하기",
    "실험 결과 작성하기",
]
steps_2 = [
    "기본 개념 문제 (2차시)",
    "전류에 의한 자기장 이론 정리",
    "예제 풀이",
    "수능응용 문제",
    "탐구 과제",
    "피드백 요약",
]
steps  = steps_1 + steps_2
N1, N2 = len(steps_1), len(steps_2)
# --------------------------------------------------------------------

# ---------------- 세션 상태 -----------------------------------------
if "done"         not in st.session_state: st.session_state.done   = [False]*len(steps)
if "current"      not in st.session_state: st.session_state.current = 0
if "student_info" not in st.session_state:
    st.session_state.student_info = {"학번":"", "성명":"", "이동반":""}
if "roster" not in st.session_state: st.session_state.roster = []
# --------------------------------------------------------------------

# ---------------- 사이드바 : 게시판 + 입력 --------------------------
with st.sidebar:
    # 접속 학생 게시판
    st.markdown("#### 🗂️ 접속 학생")
    if st.session_state.roster:
        for tag in st.session_state.roster:
            st.markdown(f"- {tag}")
    else:
        st.markdown("_아직 없음_")
    st.markdown("---")

st.sidebar.title("📚 전류의 자기장")
st.sidebar.success("버튼을 누르면 해당 차시로 이동하며 ✅ 로 표시됩니다.")

st.sidebar.subheader("학습자 정보")
for k in ("학번","성명","이동반"):
    st.session_state.student_info[k] = st.sidebar.text_input(
        k, st.session_state.student_info[k], key=f"info_{k}")
if st.sidebar.button("정보 저장"):
    info = st.session_state.student_info
    tag  = f"{info['학번']} {info['성명']}"
    if tag and tag not in st.session_state.roster:
        st.session_state.roster.append(tag)
        append_row_to_gsheet([datetime.datetime.now().isoformat(),
                              *info.values(), "정보 입력"])
        st.sidebar.success("저장 완료!")

st.sidebar.divider()

# ---- 1차시 ---------------------------------------------------------
p1 = sum(st.session_state.done[:N1]) / N1
st.sidebar.markdown(f"### 1차시 수업 진행률 : {int(p1*100)} %")
st.sidebar.progress(p1)
for i, name in enumerate(steps_1):
    label = f"{'✅' if st.session_state.done[i] else '○'} {name}"
    if st.sidebar.button(label, key=f"btn1_{i}"):
        st.session_state.current, st.session_state.done[i] = i, True

st.sidebar.markdown("<br>", unsafe_allow_html=True)  # 간격 2줄
st.sidebar.markdown("<br>", unsafe_allow_html=True)

# ---- 2차시 ---------------------------------------------------------
p2 = sum(st.session_state.done[N1:]) / N2
st.sidebar.markdown(f"### 2차시 수업 진행률 : {int(p2*100)} %")
st.sidebar.progress(p2)
for j, name in enumerate(steps_2, start=N1):
    label = f"{'✅' if st.session_state.done[j] else '○'} {name}"
    if st.sidebar.button(label, key=f"btn2_{j}"):
        st.session_state.current, st.session_state.done[j] = j, True
# --------------------------------------------------------------------

# ---------------- 본문 헤더 ----------------------------------------
step_name = steps[st.session_state.current]
st.header(f"📝 {step_name}")
# --------------------------------------------------------------------

# ---------------- 각 페이지 함수 ------------------------------------

def page_intro_physics():
    st.markdown("""
    # 🌟 물리학1 전류의 자기작용

    ---
    전류가 흐를 때 나타나는 자기적 효과는 전기와 자기의 연결고리이자  
    현대 과학·공학의 출발점입니다.

    *이 단원에서는 전류와 자기장, 실험, 그리고 대표 응용 사례까지  
    탐구하고 직접 체험하는 활동 중심 수업이 시작됩니다!*
    """)
    st.image("https://upload.wikimedia.org/wikipedia/commons/1/13/Magnetic_Field_Lines.png",
             caption="전류에 의한 자기장 실험: 자기력선 시각화")



def page_overview():
    st.image("/workspaces/currentMagField/image/LGDisplayExtension_4QksDd6Twe.png",
             caption="외르스테드의 전류·자기장 발견 (1820)")
    st.markdown("""
    **전류가 흐르면 나침반이 돌아간다!**  
    외르스테드 실험으로 시작된 ‘전류의 자기장’을 두 차시에 걸쳐  
    개념 → 실험 → 수능 문제까지 완전 정복합니다.
    """)

def page_goal():
    st.markdown("""
    ### 학습 목표  
    1. 자기장의 기본 개념 파악  
    2. 전류가 만드는 **자기장 방향·크기** 이해  
    3. 직선·원형·솔레노이드가 만드는 **자기장 세기 계산**  
    """)

# --- 개념 + 시뮬레이터 ----------------------------------------------
def page_concept():
    st.subheader("자기장 / 자기력선 개념")
    colL, colR = st.columns(2)
    with colL:
        st.image("/workspaces/currentMagField/image/1601_4534_219.png",
                 caption="막대자석 철가루 실험")
    with colR:
        st.markdown("""
        **자기장**: 자석·전류 주위 힘의 공간  
        **자기력선**: N→S, 교차❌  
        **오른손 법칙**: 엄지(전류) → 손가락(자기장)
        """)
    st.markdown("---")
    st.markdown("### ⚡ 자기장 시뮬레이터")

    mode        = st.radio("자석 종류", ["막대자석", "지구"], horizontal=True)
    auto_rotate = st.checkbox("Auto Rotate", value=False)
    needle_w    = st.slider("자침 두께", 0.5, 3.0, 1.2, 0.1)

    x = np.linspace(-2, 2, 20)
    y = np.linspace(-3, 3, 30)
    X, Y = np.meshgrid(x, y)

    theta = (int(time.time()*20) % 360 if auto_rotate else 0) * np.pi/180
    Xr = X*np.cos(theta) - Y*np.sin(theta)
    Yr = X*np.sin(theta) + Y*np.cos(theta)

    def dipole_B(X, Y, M=1):
        r2 = X**2 + Y**2
        with np.errstate(divide='ignore', invalid='ignore'):
            Bx = M * (3*X*Y) / (r2**2)
            By = M * (2*Y**2 - X**2) / (r2**2)
            mask = r2 < 0.09          # 중심 과다값 제거
            Bx[mask], By[mask] = 0, 0
        return Bx, By

    Bx, By = dipole_B(Xr, Yr, M=1 if mode=="막대자석" else 2)

    fig, ax = plt.subplots(figsize=(4,6))
    ax.set_aspect("equal"); ax.axis("off")
    ax.set_xlim(-2,2); ax.set_ylim(-3,3)

    if mode=="막대자석":
        ax.add_patch(plt.Rectangle((-0.15,-1),0.3,2,color="red"))
        ax.add_patch(plt.Rectangle((-0.15, 1),0.3,1,color="blue"))
        ax.text(0, 2.1,"N",color="blue",ha="center"); ax.text(0,-2.1,"S",color="red",ha="center")
    else:
        ax.add_patch(plt.Circle((0,0),1.3,color="green",alpha=.3))
        ax.text(0,1.5,"북극",color="blue",ha="center"); ax.text(0,-1.5,"남극",color="red",ha="center")

    ax.quiver(X, Y, Bx, By, color="royalblue",
              angles="xy", scale_units="xy", scale=8, width=needle_w/800)
    st.pyplot(fig)
# --------------------------------------------------------------------
def page_basic_1():
    q = st.radio("자기력선 방향은?", ["N→S", "S→N"])
    if st.button("채점 (1차시)"):
        st.success("정답") if q=="N→S" else st.error("오답")
        append_row_to_gsheet([datetime.datetime.now().isoformat(),
                              *st.session_state.student_info.values(),"기본1",q])

def page_exp(label):
    st.markdown(label)
    st.image("https://upload.wikimedia.org/wikipedia/commons/3/32/Magnetic_field_due_to_current.png",
             caption="나침반으로 확인한 원형 자기력선 예시")
    obs = st.text_area("관찰 내용")
    if st.button("제출"):
        append_row_to_gsheet([datetime.datetime.now().isoformat(),
                              *st.session_state.student_info.values(),label.split()[0],obs[:50]])
        st.success("제출 완료!")

def page_report():
    txt = st.text_area("세 실험 결과 비교·정리")
    if st.button("결과 제출"):
        append_row_to_gsheet([datetime.datetime.now().isoformat(),
                              *st.session_state.student_info.values(),"실험 결과",txt[:100]])
        st.success("제출 완료!")

# ---- 2차시 ---------------------------------------------------------
def page_basic_2():
    q = st.radio("솔레노이드 내부 B 식은?", ["μ₀ n I","μ₀I/2R"])
    if st.button("채점 (2차시)"):
        st.success("정답") if q=="μ₀ n I" else st.error("오답")
def page_theory():
    st.markdown("""
    ### 전류에 의한 자기장 공식  
    | 형태 | B | 비고 |
    |------|---|------|
    | 직선 도선 | \(B=\\frac{\\mu_0 I}{2\\pi r}\)| \(r\): 거리 |
    | 원형 도선 중심 | \(B=\\frac{\\mu_0 I}{2R}\)| \(R\): 반지름 |
    | 솔레노이드 내부 | \(B=\\mu_0 n I\)| \(n=N/L\) |
    """, unsafe_allow_html=True)
def page_example():
    val = st.number_input("전류 2 A, 거리 5 cm → B (T)", format="%.6f")
    if st.button("채점 예제"):
        B = round(4*np.pi*1e-7/(2*np.pi)*2/0.05,6)
        st.success(f"정답 {B}") if abs(val-B)<1e-6 else st.error(f"오답, 정답 {B}")
def page_suneung():
    sel = st.radio("반지름 0.1 m, 3 A 원형 도선 중심 B?",["6×10⁻⁶","1.2×10⁻⁵","6×10⁻⁵","1.2×10⁻⁴","3.8×10⁻⁶"])
    if st.button("채점 응용"):
        st.success("정답 1.2×10⁻⁵") if sel.startswith("1.2") else st.error("오답")
def page_essay():
    st.text_area("외르스테드 실험 설명 + 실생활 응용 1가지")
def page_feedback():
    st.text_area("수업 소감·질문·어려웠던 점")

# ---------------- 페이지 매핑 ---------------------------------------
PAGES = {
    # 1차시
    "수업 소개": page_overview,
    "학습 목표": page_goal,
    "전류의 자기장 개념 확인": page_concept,
    "기본 개념 문제 (1차시)": page_basic_1,
    "전류의 자기장 실험1 : 직선 도선 주위의 자기장 확인하기":
        lambda: page_exp("실험1 : 직선 도선 B 관찰"),
    "전류의 자기장 실험2 : 원형 도선 주위의 자기장 확인하기":
        lambda: page_exp("실험2 : 원형 도선 B 관찰"),
    "전류의 자기장 실험3 : 솔레노이드 주위의 자기장 확인하기":
        lambda: page_exp("실험3 : 솔레노이드 B 관찰"),
    "실험 결과 작성하기": page_report,
    # 2차시
    "기본 개념 문제 (2차시)": page_basic_2,
    "전류에 의한 자기장 이론 정리": page_theory,
    "예제 풀이": page_example,
    "수능응용 문제": page_suneung,
    "탐구 과제": page_essay,
    "피드백 요약": page_feedback,
}
# ---------------- 실행 ----------------------------------------------
PAGES[step_name]()
