import re
import streamlit as st
from groq import Groq

# 1. 페이지 기본 설정
st.set_page_config(
    page_title="물리친다 - AI 물리·수학 튜터",
    page_icon="⚡",
    layout="centered"
)

# 2. 메인 타이틀 & UI 헤더
st.title("⚡ 물리친다 (Pul-i-chin-da)")
st.caption("체계적인 4단계 교육과정으로 고등학교 수학·물리 정복하기!")
st.markdown("---")

# 3. 사이드바 UI: 수학 & 물리 4단계 체계적 퀘스트 정복 지도
st.sidebar.header("🗺️ 과목별 4단계 퀘스트 맵")
st.sidebar.write("단원을 순서대로 클리어하며 정복해 보세요!")

# 세션 상태에 수학/물리 4단계 단원 목록 초기화
if "cleared_units" not in st.session_state:
    st.session_state.cleared_units = {
        # --- 수학 4단계 체계 ---
        "📐 [수학 1단계] 공통수학 1, 2 (다항식/방정식/함수)": False,
        "📐 [수학 2단계] 대수 및 기하 (지수·로그/삼각함수/벡터·이차곡선)": False,
        "📐 [수학 3단계] 미적분 I (함수의 극한과 연속/미분법)": False,
        "📐 [수학 4단계] 미적분 II (여러 가지 함수의 미분과 적분)": False,
        
        # --- 물리 4단계 체계 ---
        "⚛️ [물리 1단계] 힘과 운동 (속도·가속도/뉴턴 법칙)": False,
        "⚛️ [물리 2단계] 역학과 에너지 (일·에너지 보존/운동량)": False,
        "⚛️ [물리 3단계] 전자기 (전기장/자기장/전자기 유도)": False,
        "⚛️ [물리 4단계] 양자 및 파동 (빛과 물질의 이중성/현대 물리)": False,
    }

# 사이단바 단원별 체크리스트 렌더링
for unit in st.session_state.cleared_units:
    is_checked = st.sidebar.checkbox(unit, value=st.session_state.cleared_units[unit])
    st.session_state.cleared_units[unit] = is_checked

# 전체 정복률 계산 및 프로그레스 바 표시
total_units = len(st.session_state.cleared_units)
cleared_count = sum(1 for v in st.session_state.cleared_units.values() if v)
progress = cleared_count / total_units

st.sidebar.progress(progress)
st.sidebar.write(f"🏆 전체 정복률: {int(progress * 100)}% ({cleared_count}/{total_units} 단계 완료)")

st.sidebar.markdown("---")

# 4. 사이드바: 교과서·참고서 텍스트 파일 패치
st.sidebar.header("📚 교과서·참고서 패치")
uploaded_file = st.sidebar.file_uploader("참고할 텍스트 파일(.txt) 업로드", type=["txt", "TXT"])

textbook_context = ""
if uploaded_file is not None:
    textbook_context = uploaded_file.read().decode("utf-8")
    st.sidebar.success("✅ 교과서 내용이 장착되었습니다!")

# 5. Secrets에서 API 키 검증
api_key = st.secrets.get("GROQ_API_KEY")

if not api_key:
    st.error("⚠️ GROQ_API_KEY가 등록되지 않았습니다. Streamlit Cloud의 Secrets 설정을 확인해 주세요.")
    st.stop()

# 6. Groq 클라이언트 및 모델 설정
client = Groq(api_key=api_key)
MODEL_NAME = "openai/gpt-oss-120b"

# 7. 세션 상태 및 페르소나/시스템 프롬프트 초기화
if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "system",
            "content": (
                "당신은 대한민국 고등학교 수학 및 물리 문제를 시원하게 해결해주는 열정적이고 명쾌한 AI 튜터 '물리친다'입니다. "
                "사용자의 질문에 대해 답변할 때, 반드시 아래의 [4단계 격파 스텝] 구조를 엄격히 지켜서 작성해 주세요.\n\n"
                "[4단계 격파 스텝]\n"
                "### 🥊 1단계: 문제 분석 및 핵심 조건\n"
                "- 주어진 조건과 구하고자 하는 목표를 명확하게 정돈합니다.\n\n"
                "### 💡 2단계: 필수 공식 및 개념 파악\n"
                "- 이 문제를 공략하기 위해 꼭 필요한 고등학교 수학/물리 개념과 공식을 제시합니다.\n\n"
                "### 🔍 3단계: 단계별 상세 계산 및 정복 과정\n"
                "- 공식을 대입하여 한 단계씩 명확하고 쉽게 풀이 과정을 보여줍니다.\n\n"
                "### 🎯 4단계: 최종 정답 및 3줄 요약\n"
                "- 최종 결과와 가장 핵심이 되는 포인트 3가지를 깔끔하게 요약합니다.\n\n"
                "[수식 작성 필수 규칙]\n"
                "1. 모든 수학 및 물리 수식은 표준 LaTeX 문법을 사용하세요.\n"
                "2. 문장 중간에 들어가는 짧은 수식은 반드시 인라인 형태인 \$수식$ (예: $f(x)=0$)으로만 쓰세요. 문장 중간에 블록 형태인 $\$를 쓰지 마세요.\n"
                "3. 수식이 독립된 한 줄을 차지해야 할 때만 블록 형태인 $$수식$$을 사용하세요.\n"
                "4. 수식 내부나 \\sqrt, \\frac 문법 안에 불필요한 쉼표(,)나 대괄호 기호를 넣지 마세요."
            )
        }
    ]

# 8. 수식 LaTeX 렌더링 정형화 헬퍼 함수
def format_math_response(text: str) -> str:
    text = re.sub(r'([^\s])\$\$', r'\1 \$\$', text)
