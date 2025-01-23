#quiz_service.py
from openai import OpenAI
from app.core.config import settings
import os
import json
from typing import List, Dict

chat_client = OpenAI(api_key=os.environ['UPSTAGE_API_KEY'], base_url=settings.UPSTAGE_BASE_URL)

async def generate_quiz(raw_text: str) -> List[Dict[str, str]]:
    """
    raw_text를 기반으로 O/X 퀴즈 5개를 생성하고 반환합니다.
    :param raw_text: 노트의 원본 텍스트
    :return: 퀴즈 리스트 (질문, 답변, 설명 포함)
    """
    content = f"""
    아래의 텍스트를 기반으로 O/X 퀴즈 5개를 만들어주세요. 
    응답은 JSON 형식으로만 반환해야 하며, 형식은 다음과 같습니다:
    [
        {{"question": "질문 내용", "answer": "O 또는 X", "explanation": "정답에 대한 간단한 설명"}},
        ...
    ]
    텍스트:
    {raw_text}
    """

    messages = [{"role": "user", "content": content}]
    
    # OpenAI를 통해 퀴즈 생성 요청
    response = chat_client.chat.completions.create(
        model="solar-pro",
        messages=messages
    )
    
    quiz_data = response.choices[0].message.content.strip()
    
    if not quiz_data:
        raise Exception("Received empty quiz data from OpenAI")

    # JSON으로 바로 파싱
    try:
        quizzes = json.loads(quiz_data)
    except json.JSONDecodeError as e:
        print("JSON Decode Error:", e)
        raise Exception("Failed to parse quiz data as JSON")

    return quizzes
