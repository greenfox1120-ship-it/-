import re
import streamlit as st
from groq import Groq

# 1. 페이지 기본 설정
st.set_page_config(
    page_title="물리친다 - AI 대학형 학습 LMS",
    page_icon="⚡",
    layout="centered"
)

# 2. 메인 타이틀 & UI 헤더
st.title("⚡ 물리친다 (Pul-i-chin-da) - LMS 포털")
st.caption("대학 전공/고등 심화 교육과정 퀘스트 클리어 및 AI 자동 채점 시스템")
st.markdown("---")

# 3. 세션 상태 초기화 (단원별 클리어 여부 및 시험 문제 상태 관리)
if "cleared_units" not in st.session_state:
    st.session_state.cleared_units = {
        "📐 [수학 1단계] 공통수학 1, 2": False,
        "📐 [수학 2단계] 대수 및 기하": False,
        "📐 [수학 3단계] 미적분 I": False,
        "📐 [수학 4단계] 미적분 II": False,
        "⚛️ [물리 1단계] 힘과 운동": False,
        "⚛️ [물리 2단계] 역학과 에너지": False,
        "⚛️ [물리 3단계] 전자기": False,
        "⚛️ [물리 4단계] 양자 및 파동": False,
    }

if "current_exam_unit" not in st.session_state:
    st.session_state.current_exam_unit = None

if "exam_questions" not in st.session_state:
    st.session_state.exam_questions = ""

# 4. 사이드바 UI: 대학 LMS 스타일 단원 퀘스트 맵
st.sidebar.header("🎓 수강 과목 및 단원 퀘스트")
st.sidebar.write("단원을 클릭하여 고난도 종합 평가에 응시하세요!")

selected_unit_to_test = st.sidebar.selectbox(
    "시험 응시할 단원 선택",
    options=list(st.session_state.cleared_units.keys())
)

# 단원별 상태(⭕/❌) 시각화 및 현황판
for unit, is_cleared in st.session_state.cleared_units.items():
    badge = "⭕ [CLEAR]" if is_cleared else "❌ [LOCKED]"
    st.sidebar.text(f"{badge} {unit}")

# 전체 정복률 계산 및 프로그레스 바
total_units = len(st.session_state.cleared_units)
cleared_count = sum(1 for v in st.session_state.cleared_units.values() if v)
progress = cleared_count / total_units

st.sidebar.progress(progress)
st.sidebar.write(f"🏆 이수율: {int(progress * 100)}% ({cleared_count}/{total_units} 단원 이수)")

st.sidebar.markdown("---")

# 🌟 [LMS 핵심 기능] 선택한 단원의 10문제 시험지 발행 버튼 (수식 포맷팅 엄격 적용)
if st.sidebar.button("📄 선택 단원 고난도 시험지(10문항) 발급"):
    st.session_state.current_exam_unit = selected_unit_to_test
    
    exam_gen_prompt = (
        f"대학 전공/수능 킬러 수준의 **'{selected_unit_to_test}'** 단원 종합 평가 문제 총 10문제를 출제해 주세요.\n"
        "[출제 조건 및 수식 작성 규칙]\n"
        "1. 정확히 10문제를 출제하세요.\n"
        "2. 난이도는 매우 어렵게 하되, 복잡한 지저분한 계산 대신 핵심 개념과 직관적 논리로 깔끔하게 풀리도록 숫자를 예쁘게 설계하세요.\n"
        "3. **절대 수식을 대괄호 `[...]`나 일반 텍스트 괄호 `(...)` 안에 넣지 마세요.** 모든 수식(함수, 변수, 조건 등)은 반드시 인라인 수식 `$수식$` 또는 독립 블록 수식 `$$수식$$` 형태의 표준 LaTeX 문법만 사용하세요.\n"
        "4. 정답 및 해설은 이 출제 내용에 포함하지 마세요(학생이 제출 후 채점받을 때 제공됨)."
    )
    
    with st.spinner(f"⚡ '{selected_unit_to_test}' 시험지를 깔끔한 수식으로 출제하는 중입니다..."):
        try:
            client = Groq(api_key=st.secrets["GROQ_API_KEY"])
            response = client.chat.completions.create(
                model="openai/gpt-oss-120b",
                messages=[
                    {"role": "system", "content": "당신은 명쾌한 출제 위원 AI입니다. 수식은 반드시 LaTeX($ 또는 $$)를 사용하세요."},
                    {"role": "user", "content": exam_gen_prompt}
                ],
                temperature=0.3,
                max_completion_tokens=4096,
            )
            st.session_state.exam_questions = response.choices[0].message.content
        except Exception as e:
            st.error(f"시험지 발급 중 오류 발생: {e}")

st.sidebar.markdown("---")
st.sidebar.header("📚 강의 자료실 (교과서 패치)")
uploaded_file = st.sidebar.file_uploader("참고 텍스트 파일(.txt) 업로드", type=["txt", "TXT"])
textbook_context = ""
if uploaded_file is not None:
    textbook_context = uploaded_file.read().decode("utf-8")
    st.sidebar.success("✅ 교재 연동 완료!")

# 5. API 키 검증 및 클라이언트 설정
api_key = st.secrets.get("GROQ_API_KEY")
if not api_key:
    st.error("⚠️ GROQ_API_KEY가 등록되지 않았습니다. Streamlit Secrets를 확인해 주세요.")
    st.stop()

client = Groq(api_key=api_key)
MODEL_NAME = "openai/gpt-oss-120b"

# 6. 세션 대화 히스토리 초기화
if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "system",
            "content": (
                "당신은 대학 LMS 및 AI 튜터 '물리친다'입니다. "
                "모든 수식은 절대 대괄호 `[...]`로 감싸지 말고 표준 LaTeX(`$`, `$$`)로만 작성하세요. "
                "학생의 답안을 채점할 때 각 문제별 O/X를 판정하고, 전체 점수를 산출해 주세요. "
                "만약 7문제 이상 맞추거나 완벽히 이해했다면 '🎉 [합격/클리어] 이 단원을 정복했습니다!' 메시지를 포함해 주세요."
            )
        }
    ]

# 7. 수식 정형화 헬퍼 함수 (대괄호/괄호로 잘못 감싸진 수식도 LaTeX로 자동 교정)
def format_math_response(text: str) -> str:
    # 잘못 들어간 대괄호 수식 패턴 교정 ([ f(x) = ... ] 형태를 $$ f(x) = ... $$ 로 변환)
    text = re.sub(r'\[\s*([a-zA-Z].*?)\s*\]', r'$$\1$$', text)
    
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

# 8. 메인 화면: 발급된 시험지 표시 및 답안 제출 시스템
if st.session_state.current_exam_unit:
    st.markdown(f"### 📋 현재 응시 중인 시험: `{st.session_state.current_exam_unit}`")
    with st.container():
        st.markdown(format_math_response(st.session_state.exam_questions))
    
    st.markdown("---")
    st.subheader("✍️ 답안 제출 및 AI 자동 채점")
    with st.form("exam_submit_form"):
        student_answers = st.text_area("1번부터 10번까지의 정답 및 풀이를 작성해 주세요 (예: 1번: 3, 2번: 15 ...)", height=150)
        submit_button = st.form_submit_button("🚀 답안 제출 및 채점 요청")
        
        if submit_button:
            if not student_answers.strip():
                st.warning("⚠️ 답안을 입력해 주세요!")
            else:
                grading_query = (
                    f"학생이 [{st.session_state.current_exam_unit}] 시험에 대한 다음 답안을 제출했습니다.\n"
                    f"출제된 문제와 학생 답안을 비교하여 각 문항별 채점(O/X)과 상세 해설을 제공하고, 합격 여부(7문제 이상 정답 시 클리어)를 판정해 주세요.\n\n"
                    f"[학생 제출 답안]\n{student_answers}"
                )
                st.session_state.messages.append({"role": "user", "content": grading_query})
                
                with st.spinner("🔍 AI 교수자가 답안을 정밀 채점하는 중입니다..."):
                    try:
                        payload = [{"role": "system", "content": st.session_state.messages[0]["content"]}]
                        payload.extend(st.session_state.messages[1:])
                        response = client.chat.completions.create(
                            model=MODEL_NAME,
                            messages=payload,
                            temperature=0.3,
                            max_completion_tokens=4096,
                        )
                        result_text = format_math_response(response.choices[0].message.content)
                        st.session_state.messages.append({"role": "assistant", "content": result_text})
                        
                        if "클리어" in result_text or "합격" in result_text:
                            st.session_state.cleared_units[st.session_state.current_exam_unit] = True
                            st.success(f"🎉 축하합니다! [{st.session_state.current_exam_unit}] 단원이 공식 클리어(⭕)되었습니다!")
                        
                        st.rerun()
                    except Exception as e:
                        st.error(f"채점 중 오류 발생: {e}")

# 9. 대화 기록 출력
st.markdown("---")
st.subheader("💬 AI 튜터 Q&A 및 피드백 로그")
for msg in st.session_state.messages:
    if msg["role"] != "system":
        with st.chat_message(msg["role"]):
            st.markdown(format_math_response(msg["content"]))

# 10. 일반 채팅 입력
if user_input := st.chat_input("추가로 궁금한 개념이나 질문을 입력하세요!"):
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)
    
    system_content = st.session_state.messages[0]["content"]
    if textbook_context:
        system_content += f"\n\n[참고 교과서 내용]\n{textbook_context}"
        
    payload = [{"role": "system", "content": system_content}]
    payload.extend([m for m in st.session_state.messages[1:] if m["role"] != "system"][-6:])
    
    with st.chat_message("assistant"):
        with st.spinner("⚡ 튜터가 답변을 작성 중입니다..."):
            try:
                response = client.chat.completions.create(
                    model=MODEL_NAME,
                    messages=payload,
                    temperature=0.3,
                    max_completion_tokens=4096,
                )
                ai_answer = format_math_response(response.choices[0].message.content)
                st.markdown(ai_answer)
                st.session_state.messages.append({"role": "assistant", "content": ai_answer})
            except Exception as e:
                st.error(f"오류 발생: {e}")
