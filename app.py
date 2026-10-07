import streamlit as st
from groq import Groq

# 페이지 기본 설정
st.set_page_config(
    page_title="AI 물리·수학 튜터",
    page_icon="📐",
    layout="centered"
)

st.title("📐 AI 물리·수학 튜터")
st.write("물리 및 수학 문제나 개념에 대해 자유롭게 질문해보세요!")

# Secrets에서 API 키 불러오기
api_key = st.secrets.get("GROQ_API_KEY")

if not api_key:
    st.error("⚠️ GROQ_API_KEY가 등록되지 않았습니다. Streamlit Cloud의 Secrets 설정을 확인해 주세요.")
    st.stop()

# Groq 클라이언트 초기화
client = Groq(api_key=api_key)

# 최신 지원 모델 지정
MODEL_NAME = "openai/gpt-oss-120b"

# 세션 상태에 대화 기록 저장
if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "system",
            "content": "당신은 친절하고 실력 있는 물리 및 수학 AI 튜터입니다. 사용자의 질문에 맞춰 단계별로 이해하기 쉽게 설명해 주세요."
        }
    ]

# 이전 대화 내용 화면에 표시 (system 메시지 제외)
for msg in st.session_state.messages:
    if msg["role"] != "system":
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

# 사용자 질문 입력
if user_input := st.chat_input("질문을 입력하세요 (예: 이차방정식 근의 공식 설명해줘)"):
    # 사용자 메시지 추가 및 출력
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    # AI 답변 생성
    with st.chat_message("assistant"):
        with st.spinner("생각 중..."):
            try:
                response = client.chat.completions.create(
                    model=MODEL_NAME,
                    messages=st.session_state.messages,
                    temperature=0.7,
                )
                ai_answer = response.choices[0].message.content
                st.markdown(ai_answer)
                
                # AI 답변 대화 기록에 저장
                st.session_state.messages.append({"role": "assistant", "content": ai_answer})
            except Exception as e:
                st.error(f"API 호출 중 오류가 발생했습니다: {e}")
