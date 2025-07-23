# =====================================================================
#   고2 물리 – 전류의 자기장  ▶  ‘참여형’ Streamlit 수업 앱  (rev 4)
# =====================================================================
#  변경 요약
#  • 사이드바를 ‘1차시 / 2차시’ 두 구역으로 분리 + 각 진행률 막대
#  • “버튼 누르면 … ✅” 안내문 → 사이드바 제목 바로 아래로 이동
#  • 빨간 ✗ 제거 (미완료 ○ / 완료 ✅ 만 표시)
#  • 메뉴 구조를 요청한 순서로 재편성
# ---------------------------------------------------------------------
#  requirements.txt
#       streamlit==1.35.0
#       numpy==1.26.4
#       matplotlib==3.9.0
#       gspread==6.0.2         # ← 선택(구글 시트 기록용)
#       oauth2client==4.1.3    # ← 선택
# =====================================================================

import streamlit as st, numpy as np, matplotlib.pyplot as plt
from matplotlib import font_manager
import os, datetime

# -------------------- 0. (선택) Google-Sheet 연결 --------------------
def append_row_to_gsheet(row: list):
    try:
        import gspread, oauth2client.service_account
        creds_path = os.getenv("GSHEET_JSON", "")
        if not os.path.exists(creds_path):
            return
        scope = ["https://www.googleapis.com/auth/spreadsheets",
                 "https://www.googleapis.com/auth/drive"]
        creds = oauth2client.service_account.ServiceAccountCredentials.\
                from_json_keyfile_name(creds_path, scope)
        gc = gspread.authorize(creds)
        sh = gc.open("MagFieldResponses")
        sh.sheet1.append_row(row, value_input_option="USER_ENTERED")
    except Exception:
        pass  # 시트 연결 실패 시 앱 중단 없이 무시
# --------------------------------------------------------------------

# -------------------- 1. 한글 폰트 등록 -----------------------------
FONT_DIR = "/workspaces/currentMagField/fonts"
for w in ("Regular", "Bold", "ExtraBold"):
    fp = f"{FONT_DIR}/NanumGothic-{w}.ttf"
    if os.path.exists(fp):
        font_manager.fontManager.addfont(fp)
if os.path.exists(f"{FONT_DIR}/NanumGothic-Regular.ttf"):
    plt.rcParams["font.family"] = \
        font_manager.FontProperties(fname=f"{FONT_DIR}/NanumGothic-Regular.ttf").get_name()
plt.rcParams["axes.unicode_minus"] = False
# --------------------------------------------------------------------

# -------------------- 2. 차시·메뉴 구성 -----------------------------
steps_1 = [
    "수업 소개",
    "학습 목표",
    "학습자 정보 입력",
    "전류의 자기장 개념 확인",
    "기본 개념 문제",
    "전류의 자기장 실험1 : 직선 도선 주위의 자기장 확인하기",
    "전류의 자기장 실험2 : 원형 도선 주위의 자기장 확인하기",
    "전류의 자기장 실험3 : 솔레노이드 주위의 자기장 확인하기",
    "실험 결과 작성하기"
]
steps_2 = [
    "기본 개념 문제",
    "전류에 의한 자기장 이론 정리",
    "예제 풀이",
    "수능응용 문제",
    "탐구 과제",
    "피드백 요약"
]
steps = steps_1 + steps_2            # 전체 순서(페이지 라우팅 목적)
N1, N2 = len(steps_1), len(steps_2)

# -------------------- 3. 세션 상태 -------------------------------
if "done" not in st.session_state:
    st.session_state.done = [False]*len(steps)
if "current" not in st.session_state:
    st.session_state.current = 0
if "student_info" not in st.session_state:
    st.session_state.student_info = {"학번":"", "성명":"", "이동반":""}
if "roster" not in st.session_state:          # ▶ 모든 학생 목록 저장
    st.session_state.roster = []              #  (["23001 김OO", ...])

# -------------------- 4-A.  사이드바 상단 : 학번 / 이름 입력 --------
st.sidebar.title("📚 전류의 자기장")
st.sidebar.success("버튼을 누르면 해당 차시로 이동하며 ✅ 로 표시됩니다.")

# ―― 🎓 학번·이름·반 입력란 (항상 표시) ――
st.sidebar.subheader("학습자 정보")
for k in ("학번", "성명", "이동반"):
    st.session_state.student_info[k] = st.sidebar.text_input(
        k, st.session_state.student_info[k], key=f"info_{k}")

# 저장 버튼 : 누르면 Google Sheets + 로컬 roster 에 등록
if st.sidebar.button("정보 저장", key="save_info"):
    info = st.session_state.student_info
    tag  = f"{info['학번']} {info['성명']}"
    if tag and tag not in st.session_state.roster:
        st.session_state.roster.append(tag)
        append_row_to_gsheet([datetime.datetime.now().isoformat(),
                              *info.values(), "정보 입력"])
        st.sidebar.success("저장 완료!")

st.sidebar.divider()


# ---- 1차시 진행률 + 메뉴 ------------------------------------------
p1 = sum(st.session_state.done[:N1]) / N1           # ✅ p1 사용
st.sidebar.markdown(f"### 1차시 수업 진행률 : {int(p1*100)} %")
st.sidebar.progress(p1)

for i, name in enumerate(steps_1):                  # ✅ steps_1 사용
    label = f"{'✅' if st.session_state.done[i] else '○'} {name}"
    if st.sidebar.button(label, key=f"btn1_{i}"):   # ✅ btn1_ 로 고유 키
        st.session_state.current = i
        st.session_state.done[i] = True
# --------------------------------------------------------------------
# ↘ 간격 추가 (1차시 마지막 버튼 ↔ 2차시 진행률 막대)
st.sidebar.markdown("<br>", unsafe_allow_html=True)   # ← 줄 간격 1
st.sidebar.markdown("<br>", unsafe_allow_html=True)   # ← 줄 간격 2
# ---- 2차시 진행률 + 메뉴 ------------------------------------------
p2 = sum(st.session_state.done[N1:]) / N2
st.sidebar.markdown(f"### 2차시 수업 진행률 : {int(p2*100)} %")
st.sidebar.progress(p2)

for j, name in enumerate(steps_2, start=N1):
    label = f"{'✅' if st.session_state.done[j] else '○'} {name}"
    if st.sidebar.button(label, key=f"btn2_{j}"):   # btn2_ (중복 방지)
        st.session_state.current = j
        st.session_state.done[j] = True
# --------------------------------------------------------------------


# -------------------- 5. 본문 헤더 -------------------------------
step_name = steps[st.session_state.current]
st.header(f"📝 {step_name}")

# -------------------- 6. 각 페이지 기능 ----------------------------
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
    1. 자기장의 개념 이해하기  
    2. 전류가 만드는 **자기장 방향·크기** 개념 이해하기  
    3. 직선·원형·솔레노이드 **가 만드는 자기장의 세기 구하기
    """)

def page_student():
    for k in ("학번","성명","이동반"):
        st.session_state.student_info[k] = st.text_input(k, st.session_state.student_info[k])
    if st.button("정보 저장"):
        append_row_to_gsheet([datetime.datetime.now().isoformat(),
                              *st.session_state.student_info.values(),
                              "정보 입력"])
        st.success("저장 완료!")

def page_concept():
    st.image("/workspaces/currentMagField/image/1601_4534_219.png",
             caption="막대자석 철가루 실험")
    st.markdown("""
    **자기장** : 자석·전류 주변에 형성되는 힘의 공간  
    **자기력선** : N→S 방향, 교차하지 않음  
    **오른손 법칙** : 엄지(전류) → 손가락(자기장)
    """)

def page_basic_1():
    q = st.radio("자기력선 방향은?", ["N→S", "S→N"])
    if st.button("채점 (1차시)"):
        st.success("정답") if q=="N→S" else st.error("오답")
        append_row_to_gsheet([datetime.datetime.now().isoformat(),
                              *st.session_state.student_info.values(),
                              "기본1", q])

def page_exp(label):
    st.markdown(label)
    st.image("https://upload.wikimedia.org/wikipedia/commons/3/32/Magnetic_field_due_to_current.png",
             caption="나침반으로 확인한 원형 자기력선 (예시)")
    obs = st.text_area("관찰 내용 기록")
    if st.button("제출"):
        append_row_to_gsheet([datetime.datetime.now().isoformat(),
                              *st.session_state.student_info.values(),
                              label.split(':')[0], obs[:50]])
        st.success("제출 완료!")

def page_report():
    txt = st.text_area("세 실험(직선·원형·솔레노이드) 결과 비교·정리")
    if st.button("결과 제출"):
        append_row_to_gsheet([datetime.datetime.now().isoformat(),
                              *st.session_state.student_info.values(),
                              "실험 결과", txt[:100]])
        st.success("제출 완료!")

# ------- 2차시 페이지들 --------------------------------------------
def page_basic_2():
    q = st.radio("솔레노이드 내부 자기장 B 식은?", ["μ₀ n I", "μ₀I/2R"])
    if st.button("채점 (2차시)"):
        st.success("정답") if q=="μ₀ n I" else st.error("오답")
        append_row_to_gsheet([datetime.datetime.now().isoformat(),
                              *st.session_state.student_info.values(),
                              "기본2", q])

def page_theory():
    st.markdown("""
    ### 전류에 의한 자기장 정리  
    | 형태 | 자기장 크기 \(B\) | 비고 |
    |------|------------------|------|
    | 직선 도선 | \( \displaystyle B=\frac{\mu_0 I}{2\pi r} \) | \(r\) : 거리 |
    | 원형 도선 중심 | \( \displaystyle B=\frac{\mu_0 I}{2R} \) | \(R\) : 반지름 |
    | 솔레노이드 내부 | \( B = \mu_0 n I \) | \(n=N/L\) |
    """, unsafe_allow_html=True)

def page_example():
    val = st.number_input("전류 2 A, 거리 5 cm  →  B (T)", format="%.6f")
    if st.button("채점 예제"):
        mu0=4*np.pi*1e-7; B=round(mu0/(2*np.pi)*2/0.05,6)
        st.success(f"정답 {B}") if abs(val-B)<1e-6 else st.error(f"오답, 정답 {B}")

def page_suneung():
    sel = st.radio("반지름 0.1 m, 3 A 원형 도선 중심 B?",
                   ["6×10⁻⁶","1.2×10⁻⁵","6×10⁻⁵","1.2×10⁻⁴","3.8×10⁻⁶"])
    if st.button("채점 응용"):
        st.success("정답 1.2×10⁻⁵") if sel.startswith("1.2") else st.error("오답")

def page_essay():
    st.text_area("외르스테드 실험을 설명하고, 실생활 응용 1가지를 제시하시오.")

def page_feedback():
    st.text_area("수업 소감·질문·어려웠던 점")

# -------------------- 7. 페이지 매핑 -------------------------------
PAGES = {
    # 1차시
    "수업 소개":            page_overview,
    "도입 목표":            page_goal,
    "학습자 정보 입력":      page_student,
    "전류의 자기장 개념 확인": page_concept,
    "기본 개념 문제 (1차시)": page_basic_1,
    "전류의 자기장 실험1 : 직선 도선 주위의 자기장 확인하기":
        lambda: page_exp("실험1 : 직선 도선 B 관찰"),
    "전류의 자기장 실험2 : 원형 도선 주위의 자기장 확인하기":
        lambda: page_exp("실험2 : 원형 도선 B 관찰"),
    "전류의 자기장 실험3 : 솔레노이드 주위의 자기장 확인하기":
        lambda: page_exp("실험3 : 솔레노이드 B 관찰"),
    "실험 결과 작성하기":    page_report,
    # 2차시
    "기본 개념 문제 (2차시)":  page_basic_2,
    "전류에 의한 자기장 이론 정리": page_theory,
    "예제 풀이":             page_example,
    "수능응용 문제":          page_suneung,
    "탐구 과제":             page_essay,
    "피드백 요약":           page_feedback,
}
PAGES[step_name]()
