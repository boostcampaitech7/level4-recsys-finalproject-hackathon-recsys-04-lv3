from openai import OpenAI
from app.core.config import settings

client = OpenAI(
    api_key=settings.UPSTAGE_API_KEY,
    base_url=settings.UPSTAGE_BASE_URL
)

async def generate_basic_feedback(note_text: str) -> str:
    try:
        response = client.chat.completions.create(
            model="solar-mini",
            messages=[
                {
                    "role": "system",
                    "content": "당신은 학습을 돕는 선생님입니다. 학생의 노트에 대해 건설적인 피드백을 제공해주세요."
                },
                {
                    "role": "user",
                    "content": f"다음 노트에 대해 피드백을 제공해주세요: {note_text}"
                }
            ]
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"피드백 생성 중 오류 발생: {str(e)}"

async def generate_rag_feedback(note_text: str) -> str:
    # RAG 구현 전까지는 기본 피드백과 동일하게 처리
    return await generate_basic_feedback(note_text)