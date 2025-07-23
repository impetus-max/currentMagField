# =====================================================================
#  고2 물리 – 전류의 자기장  ▶  참여형 Streamlit 수업 앱
# =====================================================================
#  좌측 사이드바 : ‘수업 진행률(%) + 단계별 ○/✅ + 단계 이동’
#  단계 버튼을 누르면 자동 ✅ 체크  /  객관식·계산·서술·업로드 즉시 채점
# ---------------------------------------------------------------------
#  requirements.txt (예시)
#       streamlit==1.35.0
#       numpy==1.26.4
#       matplotlib==3.9.0
#  실행 :  streamlit run streamlit_app.py
# =====================================================================

import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
from matplotlib import font_manager
import os

# ------------------------- [1] 한글 폰트 3종 등록 ---------------------
FONT_LIST = [
    "/workspaces/currentMagField/fonts/NanumGothic-Regular.ttf",
    "/workspaces/currentMagField/fonts/NanumGothic-Bold.ttf",
    "/workspaces/currentMagField/fonts/NanumGothic-ExtraBold.ttf"
]
found = []
for fp in FONT_LIST:
    if os.path.exists(fp):
        font_manager.fontManager.addfont(fp)
        found.append(font_manager.FontProperties(fname=fp).get_name())

if found:
    base_font = None
    for cand in ["NanumGothic", "NanumGothic Bold", "NanumGothic ExtraBold"]:
        if cand in found:
            base_font = cand
            break
    if base_font is None:
        base_font = found[0]
    plt.rcParams["font.family"] = base_font
    plt.rcParams["axes.unicode_minus"] = False
# --------------------------------------------------------------------

# ------------------------- [2] 단계 목록 -----------------------------
steps = [
    "도입·목표", "흥미 유발", "자기장 개념", "실험① 자기력선 관찰",
    "오른손 법칙", "핵심 공식", "빈칸 퀴즈", "기본 개념 문제",
    "대표 예제(계산)", "수능·응용 문제", "서술·탐구 과제", "피드백·요약"
]
N = len(steps)

if "done" not in st.session_state:
    st.session_state.done = [False]*N
if "current" not in st.session_state:
    st.session_state.current = 0

# ------------------------- [3] 사이드바 ------------------------------
st.sidebar.title("📚 전류의 자기장")

progress = sum(st.session_state.done)/N
st.sidebar.markdown(f"**수업 진행률: {int(progress*100)} %**")
st.sidebar.progress(progress)
st.sidebar.divider()

for i, name in enumerate(steps):
    c1, c2 = st.sidebar.columns([0.15, 0.85])
    checked = c1.checkbox("", value=st.session_state.done[i], key=f"chk{i}")
    st.session_state.done[i] = checked
    label = f"{'✅' if checked else '○'} {name}"
    if c2.button(label, key=f"btn{i}"):
        st.session_state.current = i
        st.session_state.done[i] = True

st.sidebar.divider()
st.sidebar.info("버튼을 누르면 해당 차시로 이동하며 ✅ 완료 처리됩니다.")

# ------------------------- [4] 본문 헤더 ------------------------------
step = steps[st.session_state.current]
st.header(f"📝 {step}")

# ------------------------- [5] 단계별 페이지 --------------------------
def page_intro():
    st.subheader("학습 목표")
    st.markdown("""
    1. **전류의 자기장** 개념·방향·크기 정확 이해  
    2. 직선·원형·솔레노이드 **대표 공식** 암기·활용  
    3. 실험·계산 예제로 개념 검증  
    4. **수능·실생활** 응용 문제 해결 및 서술 탐구
    """)

def page_hook():
    st.subheader("전류가 자기장을 만든다!")
    st.image("https://img.youtube.com/vi/TMGPLS09iYk/0.jpg",
             caption="외르스테드 실험 (썸네일)")
    st.markdown("[영상 전체 보기](https://www.youtube.com/watch?v=TMGPLS09iYk)")
    st.text_area("💡 왜 이런 현상이 생길까요? 자유롭게 적어 보세요")

def page_concept():
    st.subheader("자기장 · 자기력선")
    st.image("https://upload.wikimedia.org/wikipedia/commons/1/13/Magnetic_Field_Lines.png",
             caption="막대자석 철가루 실험")
    st.markdown("""
    * **자기장**: 자석·전류 주위 힘의 공간 (벡터장)  
    * **자기력선**: 방향·세기 시각화 (N→S)  
    * **오른손 법칙**: 엄지 = 전류, 손가락 = 자기장
    """)
    st.text_area("자기력선 특징(밀도·방향 등)을 정리해 보세요")

def page_exp1():
    st.subheader("실험① : 자기력선 관찰")
    st.file_uploader("실험 사진/영상 업로드 (.png .jpg .mp4)")
    st.slider("가상 전류(A)", 0, 10, 2)
    st.slider("관찰 거리(cm)", 1, 20, 5)
    st.text_area("📑 관찰 결과·느낀 점")

def page_rhs():
    st.subheader("오른손 법칙 퀴즈")
    choice = st.radio("x축(+) 전류 → 자기장은?",
                      ["시계방향 원", "반시계방향 원", "+z (화면 밖)", "-z (화면 안)"])
    if st.button("정답 확인"):
        st.success("정답: +z") if choice.startswith("+z") else st.error("오답! 엄지 방향과 손가락 감는 방향을 확인")

def page_formula():
    st.subheader("대표 공식")
    st.latex(r'''B_{\text{직선}}=\frac{\mu_0}{2\pi}\frac{I}{r}''')
    st.latex(r'''B_{\text{원형}}=\frac{\mu_0 I}{2R}''')
    st.latex(r'''B_{\text{솔레노이드}}=\mu_0 n I''')
    st.info("μ₀ = 4π × 10⁻⁷ T·m/A")

def page_blank():
    st.subheader("빈칸 채우기 퀴즈")
    ans = st.text_input("직선 도선 공식 분자에 들어갈 상수 기호는?")
    if st.button("채점"):
        st.success("정답!") if ans.strip() == "μ₀" else st.error("오답: μ₀")

def page_basic():
    st.subheader("기본 개념 문제")
    q = st.radio("자기력선 방향은?", ["S→N", "N→S"])
    if st.button("채점"):
        st.success("정답") if q == "N→S" else st.error("오답")

def page_example():
    st.subheader("대표 예제 (직선 도선)")
    user = st.number_input("전류 2 A, 거리 5 cm → B (T)", format="%.6f")
    if st.button("채점 예제"):
        mu0 = 4*np.pi*1e-7
        B = mu0/(2*np.pi)*2/0.05
        B = round(B, 6)
        st.success(f"정답 {B}") if abs(user-B)<1e-6 else st.error(f"오답, 정답 {B}")

def page_suneung():
    st.subheader("수능·응용 문제")
    sel = st.radio("반지름 0.1 m, 3 A 원형 도선 중심 B?",
                   ["6×10⁻⁶", "1.2×10⁻⁵", "6×10⁻⁵", "1.2×10⁻⁴", "3.8×10⁻⁶"])
    if st.button("채점 수능"):
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

# ------------------------- [6] 매핑 & 실행 ---------------------------
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
pages[step]()
