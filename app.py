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
st.caption("어려운 고등학교 물리·수학 문제, AI 튜터와 함께 시원하게 물리치자!")
st.markdown("---")

# 3. 사이드바 UI: 고등학교 물리·수학 퀘스트 정복 지도
st.sidebar.header("🗺️ 물리·수학 퀘스트 정복 지도")
st.sidebar.write("단원별 문제를 정복하고 클리어 체크를 해보세요!")

# 세션 상태에 한국 고등학교 교육과정 단원 목록 초기화
if "cleared_units" not in st.session_state:
    st.session_state.cleared_units = {
        # [물리학 I / II]
        "⚛️ [물리] 1. 역학과 에너지 (등가속도/운동량/열역학)": False,
        "⚛️ [물리] 2. 물질과 전자기장 (전기력/원자/전자기 유도)": False,
        "⚛️ [물리] 3. 파동과 정보 통신 (굴절/간섭/빛과 물질의 이중성)": False,
        "⚛️ [물리] 4. 돌림힘과 역학적 평형 (심화 역학)": False,
        # [수학 I / II / 미적분]
        "📐 [수학] 1. 지수함수와 로그함수": False,
        "📐 [수학] 2. 삼각함수와 활용": False,
        "📐 [수학] 3. 수열과 수학적 귀납법": False,
        "📐 [수학] 4. 함수의 극한과 연속": False,
        "📐 [수학] 5. 다항함수의 미분법과 적분법": False,
        "📐 [수학] 6. 미적분 (여러 가지 미분법/정적분의 활용)": False,
    }

# 사이드바 단원별 체크리스트 렌더링
for unit in st.session_state.cleared_units:
    is_checked = st.sidebar.checkbox(unit, value=st.session_state.cleared_units[unit])
    st.session_state.cleared_units[unit] = is_checked

# 전체 정복률 계산 및 프로그레스 바 표시
total_units = len(st.session_state.cleared_units)
cleared_count = sum(1 for v in st.session_state.cleared_units.values() if v)
progress = cleared_count / total_units

st.sidebar.progress(progress)
st.sidebar.write(f"🏆 전체 정복률: {int(progress * 100)}% ({cleared_count}/{total_units} 단원 완료)")

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
                "2. 문장 중간에 들어가는 짧은 수식은 반드시 인라인 형태인 $수식$ (예: $f(x)=0$)으로만 쓰세요. 문장 중간에 블록 형태인 $$를 쓰지 마세요.\n"
                "3. 수식이 독립된 한 줄을 차지해야 할 때만 블록 형태인 $$수식$$을 사용하세요.\n"
                "4. 수식 내부나 \\sqrt, \\frac 문법 안에 불필요한 쉼표(,)나 대괄호 기호를 넣지 마세요."
            )
        }
    ]

# 8. 수식 LaTeX 렌더링 정형화 헬퍼 함수
def format_math_response(text: str) -> str:
    text = re.sub(r'([^\s])\$\$', r'\1 $$', text)
    text = re.sub(r'\$\$([^\s])', r'$$ \1', text)
    
    def clean_inline_math(match):
        inner = match.group(1)
        if '\n' not in inner and len(inner) < 60:
            return f"${inner}$"
        return f"$$\n{inner}\n$$"
    
    text = re.sub(r'\$\$(.*?)\$\$', clean_inline_math, text, flags=re.DOTALL)
    text = re.sub(r'\\\[\s*(.*?)\s*\\\]', r'$$\1$$', text, flags=re.DOTALL)
    text = re.sub(r'\\\(\s*(.*?)\s*\\\)', r'$\1$', text, flags=re.DOTALL)
    text = re.sub(r'(\\sqrt|\\frac)\s*,\s*', r'\1 ', text)
    return text

# 9. 기존 대화 출력
for msg in st.session_state.messages:
    if msg["role"] != "system":
        with st.chat_message(msg["role"]):
            st.markdown(format_math_response(msg["content"]))

# 10. 사용자 입력 처리 및 API 호출
if user_input := st.chat_input("물리치고 싶은 문제나 개념을 입력하세요! (예: 등가속도 운동 공식 설명해줘, 미분계수 구하는 법)"):
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    # 시스템 프롬프트에 업로드된 교과서 컨텍스트 동적 추가
    system_content = st.session_state.messages[0]["content"]
    if textbook_context:
        system_content += f"\n\n[참고 교과서 내용]\n{textbook_context}"

    payload_messages = [{"role": "system", "content": system_content}]
    recent_msgs = [m for m in st.session_state.messages[1:] if m["role"] != "system"][-6:]
    payload_messages.extend(recent_msgs)

    # AI 응답 생성
    with st.chat_message("assistant"):
        with st.spinner("⚡ '물리친다' 튜터가 문제를 정복하는 중..."):
            try:
                response = client.chat.completions.create(
                    model=MODEL_NAME,
                    messages=payload_messages,
                    temperature=0.3,
                    max_completion_tokens=4096,
                )
                ai_answer = response.choices[0].message.content
                
                formatted_answer = format_math_response(ai_answer)
                st.markdown(formatted_answer)
                
                st.session_state.messages.append({"role": "assistant", "content": formatted_answer})
            except Exception as e:
                st.error(f"API 호출 중 오류가 발생했습니다: {e}")
