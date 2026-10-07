import os
import re
import numpy as np
import matplotlib.pyplot as plt
import streamlit as st
from groq import Groq

# 1. 페이지 기본 설정
st.set_page_config(
    page_title="⚡ AI 물리·수학 전문 도우미",
    page_icon="⚡",
    layout="wide"
)

# 2. 대화 기록 저장소 초기화
if "messages" not in st.session_state:
    st.session_state.messages = []

# 3. API 키 자동 로드 (환경 변수 우선 -> secrets.toml 안전 탐색)
api_key = os.environ.get("GROQ_API_KEY", "")

if not api_key:
    try:
        api_key = st.secrets.get("GROQ_API_KEY", "")
    except Exception:
        api_key = ""

# 4. 사이드바 설정 영역
with st.sidebar:
    st.header("⚙️ 앱 설정")
    
    if api_key:
        st.success("✅ API Key가 자동으로 인식되었습니다.")
    else:
        st.error("⚠️ API Key를 찾을 수 없습니다. OS 환경 변수나 secrets.toml을 확인해 주세요.")
    
    st.divider()
    
    # 설명 난이도 선택
    st.subheader("🎓 설명 난이도 설정")
    difficulty = st.selectbox(
        "난이도 선택",
        ["초급 (중학생 수준 / 쉬운 비유)", "중급 (고등 물리Ⅰ·Ⅱ 및 수학 수준)", "고급 (대학 물리 및 고등 수학)"]
    )
    
    if "초급" in difficulty:
        level_instruction = "중학생도 쉽게 이해할 수 있도록 일상적인 예시와 쉬운 용어로 설명해줘."
    elif "중급" in difficulty:
        level_instruction = "고등학교 물리 및 수학 교과 과정에 맞춰 정석적으로 설명해줘."
    else:
        level_instruction = "대학 일반물리학 및 고등 수학 수준에 맞춰 엄밀한 유도와 원리를 포함해 설명해줘."

    # 동적 그래프 생성을 위한 시스템 프롬프트
    system_instruction = f"""너는 오직 **물리학 및 수학 분야만 다루는 전문 튜터 AI**야. 모든 답변은 한국어로 작성해야 해.

[영역 제한 규칙]:
- 물리 및 수학 범주를 벗어난 질문(국어, 영어, 역사, 코딩, 일상 대화 등)이 들어오면 다음 거절 문구만 정확히 출력해:
  "⚠️ 죄송합니다. 저는 **물리 및 수학 전용 AI 튜터**입니다. 물리나 수학 관련 질문만 입력해 주세요."

[난이도 지침]: {level_instruction}

[답변 작성 규칙]:
1. 수식을 쓸 때 대괄호([ ])나 (\\dfrac...) 형태를 절대 사용하지 마라.
2. 독립된 중요 수식은 반드시 앞뒤로 줄바꿈을 한 뒤 `$$` 로 감싸서 작성하라.
3. `\\dfrac` 문법은 쓰지 말고 기본 `\\frac` 문법만 사용하라.
4. **그래프 시각화 필수 규칙**:
   질문과 연관된 수식/개념을 표현할 수 있는 **Matplotlib 파이썬 코드**를 답변 맨 밑에 ```python ... ``` 블록으로 작성하라.
   - 코드 내부에는 `plt.savefig`나 `plt.show()`를 쓰지 마라.
   - `fig, ax = plt.subplots()` 객체를 생성하고 `ax.plot()` 등으로 그려라.
   - 격자(`ax.grid(True)`), 축 라벨(`ax.set_xlabel`, `ax.set_ylabel`)을 포함하라.
   - 그래프 텍스트(라벨, 제목 등)는 한글 깨짐 방지를 위해 반드시 영어(English)로 작성하라.

[답변 형식 순서]:
💡 **핵심 수식**

$$ 수식 내용 $$

📝 **단계별 풀이 및 설명**

설명 내용...

✅ **최종 정답**

$$ 최종 답 수식 $$

```python
# 파이썬 matplotlib 그래프 생성 코드
import numpy as np
import matplotlib.pyplot as plt
fig, ax = plt.subplots(figsize=(5, 4))
# ... 그래프 그리기 로직 ...
```"""

    st.divider()
    
    if st.button("🧹 대화 내용 초기화", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

# 5. 수식 후처리 함수
def clean_latex(text: str) -> str:
    text = text.replace(r'\dfrac', r'\frac')
    text = text.replace(r'\displaystyle', '')
    text = text.replace(r'$$', '\n\n$$\n\n')
    return text

# 6. 동적 코드 실행을 통한 그래프 출력 함수
def render_dynamic_graph(text: str):
    code_match = re.search(r'```python\s*(.*?)\s*```', text, re.DOTALL)
    if code_match:
        code_str = code_match.group(1)
        clean_text = re.sub(r'```python\s*.*?\s*```', '', text, flags=re.DOTALL)
        
        local_vars = {}
        try:
            exec(code_str, {"np": np, "plt": plt}, local_vars)
            if "fig" in local_vars:
                fig = local_vars["fig"]
                return clean_text, fig
        except Exception:
            pass
    return text, None

# 7. 메인 화면
st.title("⚡ AI 물리·수학 전문 도우미")
st.caption(f"현재 설정된 난이도: **{difficulty.split()[0]}** | 📌 **물리·수학 질문 전용**")

# 대화 내용 표시
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if "fig" in message and message["fig"] is not None:
            st.pyplot(message["fig"])

# 입력 처리
if prompt := st.chat_input("물리나 수학 문제를 입력하세요..."):
    if not api_key:
        st.error("API Key가 설정되어 있지 않습니다. 시스템 환경 변수나 secrets.toml을 설정해 주세요.")
    else:
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            client = Groq(api_key=api_key.strip())
            
            candidate_models = ["llama-3.3-70b-versatile", "llama-3.1-8b-instant", "gemma2-9b-it"]
            
            messages_to_send = [{"role": "system", "content": system_instruction}]
            for msg in st.session_state.messages:
                messages_to_send.append({"role": msg["role"], "content": msg["content"]})

            success = False
            errors = []
            full_response = ""
            fig = None

            for model_name in candidate_models:
                try:
                    completion = client.chat.completions.create(
                        model=model_name,
                        messages=messages_to_send,
                        stream=False
                    )
                    
                    raw_content = completion.choices[0].message.content or ""
                    processed_text = clean_latex(raw_content)
                    clean_text, fig = render_dynamic_graph(processed_text)
                    
                    message_placeholder.markdown(clean_text)
                    
                    if fig is not None:
                        st.subheader("📊 맞춤 시각화 그래프")
                        st.pyplot(fig)
                        
                    success = True
                    full_response = clean_text
                    break
                except Exception as e:
                    errors.append(f"[{model_name}] {e}")
                    continue

            if not success:
                error_details = "\n".join(errors) if errors else "알 수 없는 오류"
                full_response = (
                    "⚠️ **API 호출 실패**\n\n"
                    "등록된 API Key가 유효한지 확인해 주시거나, Groq 서비스 상태를 확인해 주세요.\n\n"
                    f"**상세 에러 로그:**\n```\n{error_details}\n```"
                )
                message_placeholder.markdown(full_response)

        msg_data = {"role": "assistant", "content": full_response}
        if fig is not None:
            msg_data["fig"] = fig
        st.session_state.messages.append(msg_data)