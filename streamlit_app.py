import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
from matplotlib import font_manager
import matplotlib.patches as patches
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.transforms import Affine2D
import os, datetime

# ──────────────────  페이지·글꼴·글씨  ────────────────────────────
st.set_page_config(page_title="고등학교 2학년 물리학1 전류의 자기장",
                   page_icon="🧲", layout="wide")
st.markdown("""
<style>
html,body,[class*="st-"]{font-size:18px!important;}
</style>""", unsafe_allow_html=True)

FONT_DIR="/workspaces/currentMagField/fonts"
for w in ("Regular","Bold","ExtraBold"):
    fp=f"{FONT_DIR}/NanumGothic-{w}.ttf"
    if os.path.exists(fp):
        font_manager.fontManager.addfont(fp)
reg=f"{FONT_DIR}/NanumGothic-Regular.ttf"
if os.path.exists(reg):
    plt.rcParams["font.family"]=font_manager.FontProperties(fname=reg).get_name()
plt.rcParams["axes.unicode_minus"]=False


# ──────────────────  유틸  ────────────────────────────────────────
from pathlib import Path
BASE_DIR = Path(__file__).parent          # streamlit_app.py 가 있는 폴더

def safe_img(src: str, **kwargs):
    """
    src : ① '/workspaces/…/speaker.webp' 같은 절대경로
          ② 'image/speaker.webp'   (프로젝트 상대폴더)
          ③ 'speaker.webp'         (image 폴더 내부 파일명)
    어느 형태로 호출해도, 존재하는 첫 경로를 찾아 이미지를 표시한다.
    """
    # 1) 인자로 받은 값을 그대로 시도
    cand = [Path(src)]

    # 2) 절대경로였으면 → 파일명만 추출해 ./image/ 로 재시도
    cand.append(BASE_DIR / "image" / Path(src).name)

    # 3) 상대경로였으면 ./    , ./image/ 두 군데 모두 시도
    if not Path(src).is_absolute():
        cand.append(BASE_DIR / src)          # ./image/abc.png 처럼 이미 상대라면 동일
        cand.append(BASE_DIR / "image" / src)

    # 실제 존재하는 첫 경로로 출력
    for p in cand:
        if p.exists():
            st.image(str(p), **kwargs)
            return

    # 전부 실패 → 경고
    st.warning(f"⚠️ 파일 없음: {Path(src).name}")


def append_row_to_gsheet(row):
    try:
        import gspread, oauth2client.service_account
        cred=os.getenv("GSHEET_JSON","")
        if not os.path.exists(cred): return
        scope=["https://www.googleapis.com/auth/spreadsheets",
               "https://www.googleapis.com/auth/drive"]
        creds=oauth2client.service_account.ServiceAccountCredentials.\
              from_json_keyfile_name(cred,scope)
        gspread.authorize(creds).open("MagFieldResponses").sheet1.append_row(
            row,value_input_option="USER_ENTERED")
    except Exception as e:
        st.sidebar.error(f"GSheet 기록 실패: {e}")

# ──────────────────  차시·메뉴  ───────────────────────────────────
steps_1_all=[
    "물리학1 전류의 자기작용","수업 소개","학습 목표","자기장 개념 확인",
    "기본 개념 문제 (1차시)",
    "전류의 자기장 실험1 : 직선 도선 주위의 자기장 확인하기",
    "전류의 자기장 실험2 : 원형 도선 주위의 자기장 확인하기",
    "전류의 자기장 실험3 : 솔레노이드 주위의 자기장 확인하기",
    "실험 결과 작성하기",
]
steps_2=[
    "기본 개념 문제 (2차시)","전류에 의한 자기장 이론 정리",
    "예제 풀이","수능응용 문제","탐구 과제","피드백 / 정리하기",
]
steps_all=steps_1_all+steps_2
steps_1_menu=steps_1_all[1:]
N1,N2=len(steps_1_menu),len(steps_2)

# ──────────────────  세션 상태  ───────────────────────────────────
if "done" not in st.session_state: st.session_state.done=[False]*len(steps_all)
if "current" not in st.session_state: st.session_state.current=0
if "student_info" not in st.session_state:
    st.session_state.student_info={"학번":"","성명":"","이동반":""}
if "roster" not in st.session_state: st.session_state.roster=[]

# ──────────────────  사이드바  ────────────────────────────────────
with st.sidebar:
    st.markdown("#### 🗂️ 접속 학생")
    for tag in st.session_state.roster or ["_아직 없음_"]: st.markdown(f"- {tag}")
    st.markdown("---")
st.sidebar.title("📚 전류의 자기장")
st.sidebar.subheader("학습자 정보")
for k in ("학번","성명","이동반"):
    st.session_state.student_info[k]=st.sidebar.text_input(
        k,st.session_state.student_info[k],key=f"in_{k}")
if st.sidebar.button("정보 저장"):
    info=st.session_state.student_info
    tag=f"{info['학번']} {info['성명']}".strip()
    if info["학번"] and info["성명"]:
        if tag not in st.session_state.roster: st.session_state.roster.append(tag)
        append_row_to_gsheet([datetime.datetime.now().isoformat(),
                              *info.values(),"정보 입력"])
        st.sidebar.success("저장 완료!")
    else: st.sidebar.warning("학번·성명을 입력하세요.")

st.sidebar.divider()
st.sidebar.success("💡아래 진행 버튼을 클릭하면 해당 내용으로 이동합니다. 진행을 완료하면 ✅가 표시됩니다.")

# 진행률
p1=sum(st.session_state.done[1:1+N1])/N1
st.sidebar.markdown(f"### 1차시 진행률 : {int(p1*100)}%")
st.sidebar.progress(p1)
for i,n in enumerate(steps_1_menu,start=1):
    label=f"{'✅' if st.session_state.done[i] else '○'} {n}"
    if st.sidebar.button(label,key=f"btn1_{i}"):
        st.session_state.current,st.session_state.done[i]=i,True

p2=sum(st.session_state.done[len(steps_1_all):])/N2
st.sidebar.markdown(f"### 2차시 진행률 : {int(p2*100)}%")
st.sidebar.progress(p2)
for i,n in enumerate(steps_2,start=len(steps_1_all)):
    label=f"{'✅' if st.session_state.done[i] else '○'} {n}"
    if st.sidebar.button(label,key=f"btn2_{i}"):
        st.session_state.current,st.session_state.done[i]=i,True

step_name=steps_all[st.session_state.current]
st.header(f"📝 {step_name}")

# ──────────────────  페이지 함수들  ────────────────────────────────
def page_intro_physics():
    st.markdown("""#
---
🌟 전류가 흐르면 발생하는 자기장은 전기와 자기 현상의 연결고리입니다.""")
    c1,c2=st.columns(2)
    with c1: safe_img("/workspaces/currentMagField/image/speaker.webp",
                      caption="스피커",use_column_width=True)
    with c2: safe_img("/workspaces/currentMagField/image/crane.jpg",
                      caption="전자석 기중기",use_column_width=True)

def page_overview():
    safe_img("/workspaces/currentMagField/image/oersted_experiment.png",
             caption="외르스테드의 실험(1820)")
    st.markdown("외르스테드 실험으로부터 시작된 전류의 자기 현상은 현대 전기 문명이 나타나게 했습니다. : 개념 → 실험 → 수능 문제 순으로 학습합니다.")

def page_goal():
    st.markdown("""1. 전류에 의한 자기 작용이 일상생활에서 적용되는 다양한 예를 찾아 그 원리를 설명할 수 있다.
  
2. 전류가 만드는 자기장 방향과 세기를 구할 수 있다.""")

# ─── page_concept : 막대자석 시뮬레이터 ───────────────────────────
def page_concept():
    L,R=st.columns(2)
    with L:
        safe_img("/workspaces/currentMagField/image/magnet_lines_compass.png",
                 caption="막대자석 자기력선·나침반")
    with R:
        st.markdown("**자기장**: 자기력이 작용하는 공간")
        st.markdown("**자기력선**: 눈에 보이지 않는 자기장을 나타낸 가상의 선")
        st.markdown("""∙ N극에서 S극으로 향하는 폐곡선  
∙ 갈라지거나 교차하지 않음  
∙ 간격이 좁을수록 자기장 세기 ↑  
∙ 한 점에서의 접선 방향 = 그 점의 자기장 방향""")

    st.markdown("---")
    st.markdown("### ⚡막대자석 주위 자기력선 시뮬레이션")

    orient = st.sidebar.selectbox("자석 축",["세로(z)","가로(x)","대각"],0)
    dens   = st.sidebar.slider("화살표 밀도",15,40,25,5)
    show_f = st.sidebar.checkbox("자기력선",True)
    show_c = st.sidebar.checkbox("색상",True)
    show_v = st.sidebar.checkbox("화살표",True)
    strength=st.slider("🔧 막대자석 단극 세기 조절",0.5,3.0,1.0,0.1)

    mag_len,mag_w=1.2,0.4
    if orient=="세로(z)":
        north=np.array([0,mag_len/2]); south=-north
    elif orient=="가로(x)":
        north=np.array([mag_len/2,0]); south=-north
    else:
        north=np.array([mag_len/2*np.cos(np.pi/4),mag_len/2*np.sin(np.pi/4)]); south=-north

    x=np.linspace(-3,3,dens); y=np.linspace(-3,3,dens); X,Y=np.meshgrid(x,y)
    RX,RY=X-north[0],Y-north[1]; SX,SY=X-south[0],Y-south[1]
    rN=np.sqrt(RX**2+RY**2)+1e-9; rS=np.sqrt(SX**2+SY**2)+1e-9
    Bx=strength*(RX/rN**3 - SX/rS**3); By=strength*(RY/rN**3 - SY/rS**3)

    inside=(np.abs(X)<mag_w/2)&(np.abs(Y)<mag_len/2)
    Bx[inside]=0; By[inside]=strength
    B=np.sqrt(Bx**2+By**2); B[inside]=np.max(B)*0.7

    fig,ax=plt.subplots(figsize=(6,6))
    ax.set_aspect('equal'); ax.set_xlim(-3,3); ax.set_ylim(-3,3)
    ax.grid(True,ls='--',alpha=0.3)

    if orient=="세로(z)":
        ax.add_patch(patches.Rectangle((-mag_w/2,0),mag_w,mag_len/2,
                                       fc="#DC143C",ec="k"))
        ax.add_patch(patches.Rectangle((-mag_w/2,-mag_len/2),mag_w,mag_len/2,
                                       fc="#4169E1",ec="k"))
    elif orient=="가로(x)":
        ax.add_patch(patches.Rectangle((0,-mag_w/2),mag_len/2,mag_w,
                                       fc="#DC143C",ec="k"))
        ax.add_patch(patches.Rectangle((-mag_len/2,-mag_w/2),mag_len/2,mag_w,
                                       fc="#4169E1",ec="k"))
    else:
        t=Affine2D().rotate_deg(45)+ax.transData
        ax.add_patch(patches.Rectangle((-mag_w/2,0),mag_w,mag_len/2,
                                       fc="#DC143C",ec="k",transform=t))
        ax.add_patch(patches.Rectangle((-mag_w/2,-mag_len/2),mag_w,mag_len/2,
                                       fc="#4169E1",ec="k",transform=t))
    ax.text(north[0],north[1]+0.2,"N",color="white",ha="center",weight="bold")
    ax.text(south[0],south[1]-0.2,"S",color="white",ha="center",weight="bold")

    if show_c:
        cmap=LinearSegmentedColormap.from_list("mag",["white","skyblue","royalblue","navy"])
        cf=ax.contourf(X,Y,B,levels=30,cmap=cmap,alpha=0.6)
        fig.colorbar(cf,ax=ax,shrink=0.8,label="|B|")
    if show_f:
        ax.streamplot(X, Y, Bx, By, color="k",
                    density=1.2*strength, linewidth=1)

    if show_v: ax.quiver(X,Y,Bx/B,By/B,B,cmap="viridis",scale=20/strength,width=0.002)

    ax.set_title("막대자석 주변 자기력선")
    st.pyplot(fig)

# ─── 기본 개념 문제 (1차시) ───────────────────────────────────────
def page_basic_1():
    safe_img("/workspaces/currentMagField/image/magnet_quiz_1.png")
    ans=st.text_input("A 지점에 있는 나침반의 N극이 가리키는 방향은?")
    if st.button("채점"):
        ok="동" in ans
        # ── before ───────────────────────────────────────────────
# st.success("🎉 정답입니다!") if ok else st.error("❌ 오답입니다. 다시 생각해보세요.")

# ── after (수정) ─────────────────────────────────────────
        if ok:
            st.success("🎉 정답입니다!")
        else:
            st.error("❌ 오답입니다. 다시 생각해보세요.")

        
# ─── 실험 1·2·3 공통 함수 ────────────────────────────────────────
# ─── 실험 공통 함수 ───────────────────────────────────────
def page_exp(question_text: str, label_code: str):
    info = {
        "실험1": { "img":"/workspaces/currentMagField/image/exp_straight_wire.png",
                   "caption":"직선 도선 주위의 나침반 관찰하기 : 그림처럼 회로를 연결하고 스위치를 닫았을 때, 직선 도선 주위에 있는 나침반의 N극이 어떻게 움직이는지 관찰한다. " },
        "실험2": { "img":"/workspaces/currentMagField/image/exp_circular_wire.png",
                   "caption":"원형 도선 중심·주위의 나침반 관찰하기 : 그림처럼 회로를 연결하고 스위치를 닫았을 때, 원형 도선의 가운데에 있는 나침반의 N극이 어떻게 움직이는지 관찰한다." },
        "실험3": { "img":"/workspaces/currentMagField/image/exp_solenoid.png",
                   "caption":"솔레노이드 내부·외부의 나침반 관찰하기 : 그림처럼 회로를 연결하고 스위치를 닫았을 때, 솔레노이드 중심축에 위치한 나침반의 N극이 어떻게 움직이는지 관찰한다." },
    }[label_code]

    st.markdown(f"### {label_code}")
    safe_img(info["img"], caption=info["caption"])

    # ── 레이블에서 question_text 제거 ───────────────────
    obs = st.text_area(
        "전류가 흐를 때, 나침반의 N극이 어떻게 움직이는지 설명하시오.",
        height=150,
        key=f"ta_{label_code}"
    )

    if st.button("제출", key=f"btn_{label_code}"):
        if obs:
            append_row_to_gsheet([
                datetime.datetime.now().isoformat(),
                *st.session_state.student_info.values(),
                label_code, obs[:300]
            ])
            st.success("제출 완료")
        else:
            st.warning("내용 입력")


# ─── 실험 결과 작성하기 – 3개 파트 ────────────────────────────────
def page_report():
    txt1=st.text_area("(1) 직선 전류가 만드는 자기장의 세기에 영향을 미치는 요소를 확인할 수 있는 실험 방법을 요약하시오.\n"
                      "[※ 새로운 실험을 설계하거나, 검색한 실험 방법을 설명하면 됩니다.]",
                      height=150,key="rep1")
    if st.button("제출 (1)"):
        if txt1:
            append_row_to_gsheet([datetime.datetime.now().isoformat(),
                                  *st.session_state.student_info.values(),"실험결과1",txt1[:500]])
            st.success("제출 완료 (1)")
        else: st.warning("내용 입력")

    st.markdown("---")
    txt2=st.text_area("(2) 직선 전류가 만드는 자기장의 세기에 영향을 미치는 요소와 자기장 세기의 관계를 설명하시오.",
                      height=150,key="rep2")
    if st.button("제출 (2)"):
        if txt2:
            append_row_to_gsheet([datetime.datetime.now().isoformat(),
                                  *st.session_state.student_info.values(),"실험결과2",txt2[:500]])
            st.success("제출 완료 (2)")
        else: st.warning("내용 입력")

    st.markdown("---")
    txt3=st.text_area("(3) 새로운 아이디어 제시, 자신의 역할, 잘하거나 좋았던 점을 추가로 작성하시오.",
                      height=150,key="rep3")
    if st.button("제출 (3)"):
        if txt3:
            append_row_to_gsheet([datetime.datetime.now().isoformat(),
                                  *st.session_state.student_info.values(),"실험결과3",txt3[:500]])
            st.success("제출 완료 (3)")
        else: st.warning("내용 입력")

# ─── 기본 개념 문제 (2차시) ─────────────────────────────────────
def page_basic_2():
    # 문제 그림
    safe_img(
        "/workspaces/currentMagField/image/basic_quiz_2.png")

    # 지문
    st.markdown("""
그림은 직선 도선 아래 나침반 자침을 **북-남 방향**으로 맞춘 실험 장치이다.  
가변 저항을 조절하며 도선 전류와 자침 움직임을 관찰하였다.
""")

    st.markdown("**1. 실험 과정에서 관찰한 내용으로 옳지 않은 것은?**")

    opts = [
        "① 스위치가 열려 있을 때 자침의 극은 북쪽을 가리킨다.",
        "② 스위치를 닫으면 자침의 극은 동쪽으로 움직인다.",
        "③ 전류를 증가시키면 자침의 극은 남쪽을 가리킨다.",
        "④ 전류를 증가시키면 자침의 극이 회전한 각도가 증가한다.",
        "⑤ 전류의 방향을 반대로 바꾸면 자침의 극은 서쪽으로 움직인다.",
    ]
    sel = st.radio("선택", opts, index=0, key="basic2_sel")

    if st.button("채점(2차시)"):
        ok = sel.startswith("③")      # 정답: ③

        # 오류 방지를 위해 if-else 로 분리
        if ok:
            st.success("정답")
        else:
            st.error("오답")

        append_row_to_gsheet([
            datetime.datetime.now().isoformat(),
            *st.session_state.student_info.values(),
            "기본2", sel, ok
        ])

        # 풀이·해설
        st.markdown(r"""
<풀이>  

① 전류가 없으면 자침은 지구 자기장에 의해 **북쪽**을 가리킨다.  
② 스위치를 닫으면 전류에 의한 자기장이 **동쪽**으로 작용 ⇒ 자침 동쪽 회전.  
④ 전류 \(I\) ↑ ⇒ 전류 자기장 \(B\) ↑ ⇒ 회전 각도 ↑.  
⑤ 전류 방향 ↔ ⇒ 전류 자기장 **서쪽** ⇒ 자침 서쪽 회전.  

③의 경우, 지구 \(B\)(북) + 전류 \(B\)(동)을 합성하면 **북-동 방향**이므로  
자침이 **남쪽**을 가리키지는 않는다 ⇒ 옳지 않은 진술.
""")


# ─── 전류에 의한 자기장 이론 정리 ──────────────────────────────
def page_theory():
    st.markdown("## ⊙ 전류가 만드는 자기장 — 앙페르(오른나사) 법칙")

    # ── 공통 개념 그림 ─────────────────────────────────────
    safe_img(
        "/workspaces/currentMagField/image/ampere_law_overview.png",
        caption="앙페르 법칙 개념도")

    # 1️⃣ 직선 도선 -------------------------------------------------
    st.markdown("### 1. 무한히 긴 **직선 도선**")
    st.latex(r"B=\frac{\mu_0 I}{2\pi r}")
    safe_img(
        "/workspaces/currentMagField/image/right_hand_rule_straight.png",
        caption="오른나사(오른손) 법칙으로 방향 구하기")
    st.markdown("""
* **방향** : 전류 방향을 오른손 **엄지**로, 휘감는 **네 손가락**이 자기장 방향  
* **세기** : 전류 \(I\) ∝, 거리 \(r^{-1}\) ∝ \(B\)
""")

    # 2️⃣ 원형 도선 중심 -------------------------------------------
    st.markdown("### 2. **원형 도선** (도선 중심)")
    st.latex(r"B=\frac{\mu_0 I}{2R}")

    # ── 원형 도선 그림 2장 (좌·우) ─────────────────────────
    c1, c2 = st.columns(2)
    with c1:
        safe_img(
            "/workspaces/currentMagField/image/circular_wire_center.png",
            caption="원형 도선 중심의 자기장")
    with c2:
        safe_img(
            "/workspaces/currentMagField/image/circular_wire_pattern.png",
            caption="원형 도선의 자기력선 패턴")

    st.markdown("""
* **방향** : 오른손 네 손가락을 전류 방향으로 감으면 **엄지**가 중심축 \(B\)  
* **세기** : 전류 \(I\) ∝, 반지름 \(R^{-1}\) ∝ \(B\)
""")

    # 3️⃣ 솔레노이드 내부 ------------------------------------------
    st.markdown("### 3. **솔레노이드** (긴 코일) 내부")
    st.latex(r"B=\mu_0 n I \quad\bigl(n=\tfrac{N}{L}\bigr)")
    safe_img(
        "/workspaces/currentMagField/image/solenoid_direction.png",
        caption="솔레노이드 전류·자기장 방향")
    st.markdown("""
* **방향** : 전류 방향으로 오른손 손가락을 감으면 **엄지**가 축 방향 \(B\)  
* **특징** : 내부 균일장, \(B ∝ nI\)
""")
    safe_img(
        "/workspaces/currentMagField/image/solenoid_iron_filings.png",
        caption="솔레노이드 주변 철가루 분포")

        # ── 요약 ─────────────────────────────────────────────
    st.markdown("---")
    st.markdown(r"""
#### ◎ 핵심 관계 요약
- **직선 도선** : $B \propto \dfrac{I}{r}$
- **원형 도선** : $B \propto \dfrac{I}{R}$
- **솔레노이드** : $B \propto nI$

👍 전류를 키우거나, 도선을 가까이 하거나, 코일을 촘촘히 감으면 **자기장이 더 세진다**.
""")



# ─── 예제 풀이 ─────────────────────────────────────────────
def page_example():
    safe_img("/workspaces/currentMagField/image/example_quiz_1.png", use_column_width=True)
    st.markdown("""
그림은 세 학생 민수, 철수, 영희가 칠판에 그려진 전류가 흐르는 가늘고 무한히 긴 직선 도선 주위의 P점과 Q점에 생기는 자기장에 대해 대화하는 모습을 나타낸 것이다.

> **문제**  
> P점과 Q점에서 발생하는 자기장에 대해 옳게 설명한 사람만을 있는 대로 고른 것은?
""")

    opts = [
        "① 민수", "② 철수", "③ 민수, 철수",
        "④ 민수, 영희", "⑤ 민수, 철수, 영희"
    ]
    sel = st.radio("선택", opts, index=0, key="ex_sel")

    if st.button("채점 예제"):
        ok = sel.startswith("⑤")            # ← 정답은 ⑤
        if ok:
            st.success("정답 (⑤)")
        else:
            st.error("오답")

        # ── 해설 추가 ───────────────────────────────────
        st.markdown("""
**해설**

* **민수**: *“자기장의 세기는 전류의 세기에 비례한다.”*  
  ✔️ 옳다 – \(B ∝ I\)

* **철수**: *“앙페르 법칙(오른나사 법칙)에 따라 전류 방향이 바뀌면 자기장 방향도 바뀐다.”*  
  ✔️ 옳다 – 방향 역전

* **영희**: *“자기장의 세기는 도선으로부터의 수직 거리에 반비례한다.”*  
  ✔️ 옳다 – \(B ∝ 1/r\) (따라서 P \(>\) Q)

→ 세 명 모두 옳으므로 **⑤ 민수, 철수, 영희**가 정답.
""")

        append_row_to_gsheet([
            datetime.datetime.now().isoformat(),
            *st.session_state.student_info.values(),
            "예제", sel, ok
        ])

# ─── 수능응용 문제 ───────────────────────────────────────────────
def page_suneung():
    # 문제 그림(있다면)
    safe_img("/workspaces/currentMagField/image/suneung_quiz_fig.png",
             caption="세 도선 A·B·C와 점 P, Q")

        # ── 문제 지문 (LaTeX 완전 적용) ────────────────────────────
        # ── 문제 지문 (LaTeX 수식은 $ … $ 로) ───────────────────────
    st.markdown(r"""
**1.** 그림과 같이 무한히 긴 직선 도선 **A, B, C** ($I_{0},\, I_{B},\, I_{0}$)가  
$xy$ 평면 위에 고정되어 있다. **A** 전류의 방향은 $-x$ 축이다.  

표는 점 **P, Q**에서 세 도선 전류가 만드는 자기장 세기를 나타낸다  
(점 P에서 A 전류의 $B = B_{0}$).  

다음 \<보기\>에서 옳은 내용을 **모두** 고르시오.
""")

    st.markdown(r"""
<보기>  

ㄱ. $I_{B}=I_{0}$  

ㄴ. C 전류 방향은 $-y$ 방향이다.  

ㄷ. Q점에서 A·B·C 전류에 의한 총 $\vec{B}$ 방향은 $+z$  
&nbsp;&nbsp;&nbsp;&nbsp;( $xy$ 평면에 수직 )이다.
""")



    # ①~⑤ 선택지
    opts = [
        "① ㄱ",           # 1
        "② ㄷ",           # 2  ← 정답
        "③ ㄱ, ㄴ",       # 3
        "④ ㄴ, ㄷ",       # 4
        "⑤ ㄱ, ㄴ, ㄷ"    # 5
    ]
    sel = st.radio("선택", opts, index=0, key="sat_sel")

    if st.button("채점 응용"):
        ok = sel.startswith("②")          # 정답: ② ㄷ
        if ok:
            st.success("정답 (② ㄷ)")
        else:
            st.error("오답")

        # 해설 그림은 정답/오답 관계없이 항상 출력
        safe_img(
            "/workspaces/currentMagField/image/suneung_quiz_solution.png",
            caption="해설",
            use_column_width=True
        )

        append_row_to_gsheet([
            datetime.datetime.now().isoformat(),
            *st.session_state.student_info.values(),
            "응용", sel, ok
        ])


# ─── 탐구 과제 ─────────────────────────────────────────────
def page_essay():
    # 그림 1 – 전동기 개념
    safe_img(
        "/workspaces/currentMagField/image/motor_structure.png",
        caption="전동기 구조와 작동 개념")

    # 그림 2 – 자도선 힘 시각화
    safe_img(
        "/workspaces/currentMagField/image/force_on_wire.png",
        caption="자기장 속 도선이 받는 힘 (F = I L × B)")

    # 과제 입력란
    txt = st.text_area(
        "자기장 안에서 전류가 흐르는 도선이 받는 힘을 설명하고, **전동기의 원리를 탐구하시오.**",
        height=220
    )

    # 제출 버튼
    if st.button("과제 제출"):
        if txt:
            append_row_to_gsheet([
                datetime.datetime.now().isoformat(),
                *st.session_state.student_info.values(),
                "과제", txt[:500]
            ])
            st.success("제출 완료")
        else:
            st.warning("내용 입력")



# ─── 피드백 ─────────────────────────────────────────────────────
def page_feedback():
    txt=st.text_area("**수업에서 배운 점·느낀 점**을 작성하세요. **추가로 확인하고 싶은 실험**을 적어주세요.",
                     height=200)
    if st.button("피드백 제출"):
        if txt:
            append_row_to_gsheet([datetime.datetime.now().isoformat(),
                                  *st.session_state.student_info.values(),"피드백",txt[:500]])
            st.success("감사합니다")
        else: st.warning("내용 입력")

# ──────────────────  매핑 · 실행  ────────────────────────────────
PAGES={
    "물리학1 전류의 자기작용":page_intro_physics,
    "수업 소개":page_overview,
    "학습 목표":page_goal,
    "자기장 개념 확인":page_concept,
    "기본 개념 문제 (1차시)":page_basic_1,
    "전류의 자기장 실험1 : 직선 도선 주위의 자기장 확인하기":
        lambda: page_exp("직선 도선이 만드는 전류의 자기장 확인하기","실험1"),
    "전류의 자기장 실험2 : 원형 도선 주위의 자기장 확인하기":
        lambda: page_exp("원형 도선이 만드는 전류의 자기장 확인하기","실험2"),
    "전류의 자기장 실험3 : 솔레노이드 주위의 자기장 확인하기":
        lambda: page_exp("솔레노이드가 만드는 전류의 자기장 확인하기","실험3"),
    "실험 결과 작성하기":page_report,
    "기본 개념 문제 (2차시)":page_basic_2,
    "전류에 의한 자기장 이론 정리":page_theory,
    "예제 풀이":page_example,
    "수능응용 문제":page_suneung,
    "탐구 과제":page_essay,
    "피드백 / 정리하기":page_feedback,
}
PAGES[step_name]()
