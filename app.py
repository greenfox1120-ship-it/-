import re
import streamlit as st
from groq import Groq

# 페이지 기본 설정
st.set_page_config(
    page_title="물리친다 - AI 물리·수학 튜터",
    page_icon="⚡",
    layout="centered"
)

# 메인 타이틀 & 배너 UI
st.title("⚡ 물리친다 (Pul-i-chin-da)")
st.caption("어려운 물리·수학 문제, AI 튜터와 함께 시원하게 물리치자!")
st.markdown("---")

# 사이드바 UI
st.sidebar.header("📚 교과서·참고서 패치")
st.sidebar.write("내 교과서 맞춤형으로 문제를 해결해보세요.")
uploaded_file = st.sidebar.file_uploader("텍스트 파일(.txt) 업로드", type=["txt"])

textbook_context = ""
if uploaded_file is not None:
    textbook_context = uploaded_file.read().decode("utf-8")
    st.sidebar.success("✅ 교과서 내용이 장착되었습니다!")

st.sidebar.markdown("---")
st.sidebar.info("💡 **팁**: 질문 시 '자세히 풀어줘'라고 요청하면 4단계 핵심 분석이 시작됩니다.")

# Secrets에서 API 키 불러오기
api_key = st.secrets.get("GROQ_API_KEY")

if not api_key:
    st.error("⚠️ GROQ_API_KEY가 등록되지 않았습니다. Streamlit Cloud의 Secrets 설정을 확인해 주세요.")
    st.stop()

# Groq 클라이언트 초기화
client = Groq(api_key=api_key)

# 최신 지원 모델 지정
MODEL_NAME = "openai/gpt-oss-120b"

# 세션 상태 대화 기록 초기화 (시스템 프롬프트 & UI 페르소나 적용)
if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "system",
            "content": (
                "당신은 어려운 물리와 수학 문제를 시원하게 해결해주는 열정적이고 명쾌한 AI 튜터 '물리친다'입니다. "
                "사용자의 질문에 대해 답변할 때, 반드시 아래의 [4단계 격파 스텝] 구조를 엄격히 지켜서 작성해 주세요.\n\n"
                "[4단계 격파 스텝]\n"
                "### 🥊 1단계: 문제 분석 및 핵심 조건\n"
                "- 주어진 조건과 구하고자 하는 목표를 명확하게 정돈합니다.\n\n"
                "### 💡 2단계: 필수 공식 및 개념 파악\n"
                "- 이 문제를 공략하기 위해 꼭 필요한 수학/물리 개념과 공식을 제시합니다.\n\n"
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

# 수식 렌더링을 정형화하는 헬퍼 함수
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

# 이전 대화 내용 화면에 표시
for msg in st.session_state.messages:
    if msg["role"] != "system":
        with st.chat_message(msg["role"]):
            st.markdown(format_math_response(msg["content"]))

# 사용자 질문 입력
if user_input := st.chat_input("물리치고 싶은 문제나 개념을 입력하세요! (예: 등가속도 운동 공식 설명해줘)"):
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    # API 전송 payload 구성
    system_content = st.session_state.messages[0]["content"]
    if textbook_context:
        system_content += f"\n\n[참고 교과서 내용]\n{textbook_context}"

    payload_messages = [{"role": "system", "content": system_content}]
    recent_msgs = [m for m in st.session_state.messages[1:] if m["role"] != "system"][-6:]
    payload_messages.extend(recent_msgs)

    # AI 답변 생성
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
