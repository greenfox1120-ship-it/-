import re
import streamlit as st
from groq import Groq
import matplotlib.pyplot as plt
import numpy as np

# 페이지 기본 설정
st.set_page_config(
    page_title="AI 물리·수학 튜터",
    page_icon="📐",
    layout="centered"
)

st.title("📐 AI 물리·수학 튜터")
st.write("물리 및 수학 문제나 개념에 대해 자유롭게 질문해보세요! (단계별 상세 풀이와 그래프가 함께 제공됩니다)")

# 사이드바에 교과서 파일 업로드 기능 추가
st.sidebar.header("📚 교과서 자료 업로드")
uploaded_file = st.sidebar.file_uploader("교과서/참고서 텍스트 파일(.txt)을 올려주세요", type=["txt"])

textbook_context = ""
if uploaded_file is not None:
    textbook_context = uploaded_file.read().decode("utf-8")
    st.sidebar.success("교과서 내용이 성공적으로 반영되었습니다!")

# Secrets에서 API 키 불러오기
api_key = st.secrets.get("GROQ_API_KEY")

if not api_key:
    st.error("⚠️ GROQ_API_KEY가 등록되지 않았습니다. Streamlit Cloud의 Secrets 설정을 확인해 주세요.")
    st.stop()

# Groq 클라이언트 초기화
client = Groq(api_key=api_key)

# 최신 지원 모델 지정
MODEL_NAME = "openai/gpt-oss-120b"

# 세션 상태에 대화 기록 저장 (단계별 풀이 및 수식 규칙 강화)
if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "system",
            "content": (
                "당신은 친절하고 실력 있는 물리 및 수학 AI 튜터입니다. "
                "사용자의 질문에 대해 답변할 때, 반드시 아래의 [단계별 풀이 구조]를 엄격히 지켜서 작성해 주세요.\n\n"
                "[단계별 풀이 구조]\n"
                "### 1️⃣ 1단계: 문제 분석 및 조건 파악\n"
                "- 주어진 조건과 구하고자 하는 목표를 명확히 정리합니다.\n\n"
                "### 2️⃣ 2단계: 핵심 공식 및 개념\n"
                "- 이 문제를 풀기 위해 필요한 수학/물리 개념과 공식을 설명합니다.\n\n"
                "### 3️⃣ 3단계: 상세 풀이 및 계산\n"
                "- 공식을 대입하여 단계별로 풀이 과정을 자세히 보여줍니다.\n\n"
                "### 4️⃣ 4단계: 최종 정답 및 요약\n"
                "- 최종 결과와 핵심 내용을 깔끔하게 요약합니다.\n\n"
                "[수식 작성 필수 규칙]\n"
                "1. 모든 수학 및 물리 수식은 표준 LaTeX 문법을 사용하세요.\n"
                "2. 독립된 블록 수식은 $$ 수식 $$, 인라인 수식은 $ 수식 $ 형태로 작성하세요.\n"
                "3. 수식 내부나 \\sqrt, \\frac 문법 안에 불필요한 쉼표(,)나 대괄호 기호를 넣지 마세요."
            )
        }
    ]

# 수식 렌더링을 정형화하는 헬퍼 함수
def format_math_response(text: str) -> str:
    text = re.sub(r'\\\[\s*(.*?)\s*\\\]', r'$$\1$$', text, flags=re.DOTALL)
    text = re.sub(r'\\\(\s*(.*?)\s*\\\)', r'$\1$', text, flags=re.DOTALL)
    text = re.sub(r'^\s*\[\s*(.*?)\s*\]\s*$', r'$$\1$$', text, flags=re.MULTILINE)
    text = re.sub(r'(\\sqrt|\\frac)\s*,\s*', r'\1 ', text)
    return text

# 질문 내용에 맞춰 자동으로 그래프를 그려주는 함수
def generate_math_plot(user_query: str):
    fig, ax = plt.subplots(figsize=(8, 4))
    query_lower = user_query.lower()
    
    try:
        if "이차" in query_lower or "포물선" in query_lower or "근의 공식" in query_lower or "x^2" in query_lower:
            x = np.linspace(-10, 10, 400)
            y = x**2 - 4*x + 3
            ax.plot(x, y, label="$y = x^2 - 4x + 3$", color="blue", linewidth=2)
            ax.axhline(0, color="black", linewidth=1, linestyle="--")
            ax.axvline(0, color="black", linewidth=1, linestyle="--")
            ax.set_title("이차함수 그래프 예시")
            ax.set_xlabel("x")
            ax.set_ylabel("y")
            ax.grid(True, linestyle=":", alpha=0.7)
            ax.legend()
        elif "삼각" in query_lower or "sin" in query_lower or "cos" in query_lower:
            x = np.linspace(0, 2 * np.pi, 400)
            ax.plot(x, np.sin(x), label="y = sin(x)", color="green", linewidth=2)
            ax.plot(x, np.cos(x), label="y = cos(x)", color="orange", linewidth=2, linestyle="--")
            ax.set_title("삼각함수 그래프")
            ax.set_xlabel("x")
            ax.set_ylabel("y")
            ax.grid(True, linestyle=":", alpha=0.7)
            ax.legend()
        elif "속도" in query_lower or "가속도" in query_lower or "물리" in query_lower or "운동" in query_lower:
            t = np.linspace(0, 5, 100)
            v0 = 0
            g = 9.8
            s = v0 * t + 0.5 * g * t**2
            ax.plot(t, s, label="자유낙하 거리 ($s = \\frac{1}{2}gt^2$)", color="purple", linewidth=2)
            ax.set_title("시간에 따른 이동 거리 그래프")
            ax.set_xlabel("시간 t (s)")
            ax.set_ylabel("거리 s (m)")
            ax.grid(True, linestyle=":", alpha=0.7)
            ax.legend()
        else:
            x = np.linspace(-10, 10, 400)
            y = np.sin(x) / (x + 1e-5)
            ax.plot(x, y, label="싱크 함수 (Sinc function)", color="red", linewidth=2)
            ax.set_title("수학 함수 시각화")
            ax.set_xlabel("x")
            ax.set_ylabel("y")
            ax.grid(True, linestyle=":", alpha=0.7)
            ax.legend()
            
        st.pyplot(fig)
    except Exception as e:
        st.info("그래프를 생성하는 중 오류가 발생했습니다.")
    finally:
        plt.close(fig)

# 이전 대화 내용 화면에 표시 (system 메시지 제외)
for msg in st.session_state.messages:
    if msg["role"] != "system":
        with st.chat_message(msg["role"]):
            st.markdown(format_math_response(msg["content"]))

# 사용자 질문 입력
if user_input := st.chat_input("질문을 입력하세요 (예: 이차방정식 근의 공식 설명해줘)"):
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    # API에 전달할 메시지 조합 (시스템 메시지 + 업로드된 교과서 내용 + 최근 대화)
    system_content = st.session_state.messages[0]["content"]
    if textbook_context:
        system_content += f"\n\n[참고 교과서 내용]\n{textbook_context}"

    payload_messages = [{"role": "system", "content": system_content}]
    recent_msgs = [m for m in st.session_state.messages[1:] if m["role"] != "system"][-6:]
    payload_messages.extend(recent_msgs)

    # AI 답변 생성
    with st.chat_message("assistant"):
        with st.spinner("단계별 분석 및 그래프 생성 중..."):
            try:
                # 1. 그래프 먼저 출력
                generate_math_plot(user_input)

                # 2. AI 텍스트 답변 생성
                response = client.chat.completions.create(
                    model=MODEL_NAME,
                    messages=payload_messages,
                    temperature=0.3,
                    max_completion_tokens=2048,
                )
                ai_answer = response.choices[0].message.content
                
                formatted_answer = format_math_response(ai_answer)
                st.markdown(formatted_answer)
                
                # AI 답변 대화 기록에 저장
                st.session_state.messages.append({"role": "assistant", "content": formatted_answer})
            except Exception as e:
                st.error(f"API 호출 중 오류가 발생했습니다: {e}")
