# =====================================================================
#  고2 물리 – 전류의 자기장 **참여형 수업 앱**  (Streamlit)
#  ▪ 왼쪽 사이드바 ─ ‘수업 진행률(%)+단계별 ○/✅ + 단계 이동’
#  ▪ 단계 버튼을 누르면 자동으로 ✅ 체크(완료 저장)
#  ▪ 객관식‧계산‧서술‧업로드 활동 → 즉시 채점 / 피드백
# ---------------------------------------------------------------------
#  • 필수 패키지  : streamlit, numpy, matplotlib
#  • requirements.txt 예시
#       streamlit==1.35.0
#       numpy==1.26.4
#       matplotlib==3.9.0
#  • 실행        :  streamlit run streamlit_app.py
# =====================================================================

import streamlit as st                    # Streamlit UI 프레임워크
import numpy as np                        # 수치 계산
import matplotlib.pyplot as plt           # (확장용) 그래프 출력
# ================================================================
#  [폰트 설정]  ─  3 종의 ‘나눔고딕’(Regular · Bold · ExtraBold) 등록
# ================================================================
import matplotlib.pyplot as plt
from matplotlib import font_manager
import os

FONT_LIST = [                                         # ★ 추가·변경 가능
    "/workspaces/currentMagField/fonts/NanumGothic-Regular.ttf",
    "/workspaces/currentMagField/fonts/NanumGothic-Bold.ttf",
    "/workspaces/currentMagField/fonts/NanumGothic-ExtraBold.ttf"
]

found_fonts = []                                      # 실제로 존재하는 폰트만 저장
for fp in FONT_LIST:
    if os.path.exists(fp):                            # 경로가 존재하면
        font_manager.fontManager.addfont(fp)          # matplotlib에 등록
        found_fonts.append(                           # 등록된 폰트 이름 추출
            font_manager.FontProperties(fname=fp).get_name()
        )

# -------- 기본 폰트 지정: Regular → 없으면 Bold → 없으면 첫 번째 ----------
if found_fonts:                                       # 하나라도 등록되면
    default_font = None
    for candidate in ["NanumGothic",                  # Regular
                      "NanumGothic Bold",             # Bold
                      "NanumGothic ExtraBold"]:       # ExtraBold
        if candidate in found_fonts:
            default_font = candidate
            break
    if default_font is None:                          # 위 이름이 모두 다를 경우
        default_font = found_fonts[0]                 # 첫 번째 폰트 사용

    plt.rcParams["font.family"] = default_font        # 전역 기본 폰트 설정
    plt.rcParams["axes.unicode_minus"] = False        # − 부호 깨짐 방지


from matplotlib import font_manager       # 한글 폰트 등록
import os                                 # 폰트 경로 존재 여부 확인

# ------------------------ [A] 한글 폰트 설정 ------------------------
FONT_PATH = "/workspaces/currentMagField/fonts/NanumGothic-Bold.ttf"
if os.path.exists(FONT_PATH):             # 폰트 파일이 실제로 존재하면
    font_manager.fontManager.addfont(FONT_PATH)
    plt.rcParams["font.family"] = font_manager.FontProperties(fname=FONT_PATH).get_name()
    plt.rcParams["axes.unicode_minus"] = False
# --------------------------------------------------------------------

# ------------------------ [B] 수업 단계 목록 ------------------------
steps = [
    "도입·목표", "흥미 유발", "자기장 개념", "실험① 자기력선 관찰",
    "오른손 법칙", "핵심 공식", "빈칸 퀴즈", "기본 개념 문제",
    "대표 예제(계산)", "수능·응용 문제", "서술·탐구 과제", "피드백·요약"
]
N = len(steps)

# ------------------------ [C] 세션 상태 초기화 ------------------------
if "done" not in st.session_state:        # 단계 완료 여부
    st.session_state.done = [False] * N
if "current" not in st.session_state:     # 현재 열람 단계 인덱스
    st.session_state.current = 0

# ------------------------ [D] 사이드바 (메뉴 + 진행률) -----------------
st.sidebar.title("📚 전류의 자기장")

progress = sum(st.session_state.done) / N
st.sidebar.markdown(f"**수업 진행률: {int(progress*100)} %**")
st.sidebar.progress(progress)
st.sidebar.divider()

for idx, name in enumerate(steps):
    c1, c2 = st.sidebar.columns([0.15, 0.85])
    # (1) 체크박스 (○/✅ 표시용)
    checked = c1.checkbox("", value=st.session_state.done[idx], key=f"chk_{idx}")
    st.session_state.done[idx] = checked
    # (2) 단계 이동 버튼 (누르면 자동 완료)
    label = f"{'✅' if checked else '○'} {name}"
    if c2.button(label, key=f"btn_{idx}"):
        st.session_state.current = idx
        st.session_state.done[idx] = True

st.sidebar.divider()
st.sidebar.info("단계 버튼을 누르거나 체크박스를 눌러 완료를 표시하세요.")

# ------------------------ [E] 본문 헤더 ------------------------------
step = steps[st.session_state.current]
st.header(f"📝 {step}")

# ------------------------ [F] 단계별 콘텐츠 함수 ----------------------
def page_intro():
    st.subheader("학습 목표")
    st.markdown("""
    1. **전류의 자기장** 개념·방향·크기를 정확히 이해  
    2. 직선·원형·솔레노이드 **대표 공식** 암기·활용  
    3. 실험·계산 예제로 개념 검증  
    4. **수능·실생활** 응용 문제 해결 및 서술 탐구
    """)

def page_hook():
    st.subheader("전기와 자기의 관계")
    thumb = "https://img.youtube.com/vi/TMGPLS09iYk/0.jpg"
    st.image(thumb, caption="전류가 흐르면 나침반이 움직인다!")
    st.markdown("[영상 전체 보기](https://www.youtube.com/watch?v=TMGPLS09iYk)")
    st.text_area("💡 왜 이런 현상이 생길까요? 자유롭게 작성")

def page_concept():
    st.subheader("자기장 · 자기력선")
    st.image("C:/Users/dongbuk/Downloads/71kk81RTB8L._AC_SL1500_.jpg",,
             caption="막대자석 철가루 실험")
    st.markdown("""
    * **자기장**: 자석·전류 주위 힘의 공간  
    * **자기력선**: 방향·세기를 보이게 하는 가상선 (N→S)  
    * **오른손 법칙**: 엄지 = 전류, 손가락 = 자기장
    """)
    st.text_area("자기력선의 특징(밀도·방향 등)을 정리")

def page_exp1():
    st.subheader("실험① : 자기력선 관찰")
    st.file_uploader("실험 사진/영상 업로드 (.png .jpg .mp4)")
    st.slider("가상 전류(A)", 0, 10, 2)
    st.slider("관찰 거리(cm)", 1, 20, 5)
    st.text_area("📑 관찰 결과·느낀 점 기록")

def page_rhs():
    st.subheader("오른손 법칙 퀴즈")
    ans = st.radio(
        "x축(+) 전류 → 자기장은?",
        ["시계방향 원", "반시계방향 원", "+z (화면 밖)", "-z (화면 안)"]
    )
    if st.button("정답 확인-RHR"):
        st.success("정답: +z") if ans.startswith("+z") else st.error("오답! 엄지→, 손가락 감기 방향을 기억")

def page_formula():
    st.subheader("대표 공식")
    st.latex(r'''B_{\text{직선}}=\frac{\mu_0}{2\pi}\frac{I}{r}''')
    st.latex(r'''B_{\text{원형}}=\frac{\mu_0 I}{2R}''')
    st.latex(r'''B_{\text{솔레노이드}}=\mu_0 n I''')
    st.info("μ₀ = 4π×10⁻⁷ T·m/A")

def page_blank():
    st.subheader("빈칸 채우기 – 초스피드 암기")
    x = st.text_input("직선 도선 공식 분자 상수?")
    if st.button("채점-빈칸"):
        st.success("정답!") if x.strip() == "μ₀" else st.error("오답: μ₀")

def page_basic():
    st.subheader("기본 개념 문제")
    q = st.radio("자기력선 방향은?", ["S→N", "N→S"])
    if st.button("채점-기본"):
        st.success("정답") if q == "N→S" else st.error("오답")

def page_example():
    st.subheader("대표 계산 예제 (직선 도선)")
    val = st.number_input("전류 2 A, 거리 5 cm  →  B (T)", format="%.6f")
    if st.button("채점-예제"):
        mu0 = 4 * np.pi * 1e-7
        B = mu0 / (2 * np.pi) * 2 / 0.05
        B = round(B, 6)
        st.success(f"정답! {B}") if abs(val - B) < 1e-6 else st.error(f"오답, 정답 {B}")

def page_suneung():
    st.subheader("수능·응용 문제")
    sel = st.radio("반지름 0.1 m, 3 A 원형 도선 중심 B 는?",
                   ["6×10⁻⁶", "1.2×10⁻⁵", "6×10⁻⁵", "1.2×10⁻⁴", "3.8×10⁻⁶"])
    if st.button("채점-수능"):
        st.success("정답 1.2×10⁻⁵") if sel.startswith("1.2") else st.error("오답, 정답 1.2×10⁻⁵ T")

def page_essay():
    st.subheader("서술·탐구 과제")
    st.text_area("① 외르스테드 실험 설명")
    st.text_area("② 전류 방향 반전 시 자기장 변화")
    if st.button("서술 제출"):
        st.success("제출 완료! 피드백 예정")

def page_feedback():
    st.subheader("피드백·요약")
    st.text_area("수업 소감·질문·어려웠던 점")
    if st.button("피드백 제출"):
        st.success("감사합니다! 답변 드리겠습니다.")

# ------------------------ [G] 단계–함수 매핑 --------------------------
pages = {
    steps[0]: page_intro,
    steps[1]: page_hook,
    steps[2]: page_concept,
    steps[3]: page_exp1,
    steps[4]: page_rhs,
    steps[5]: page_formula,
    steps[6]: page_blank,
    steps[7]: page_basic,
    steps[8]: page_example,
    steps[9]: page_suneung,
    steps[10]: page_essay,
    steps[11]: page_feedback
}

# ------------------------ [H] 현재 단계 본문 출력 ---------------------
pages[step]()                                 # 선택된 단계 함수 실행
