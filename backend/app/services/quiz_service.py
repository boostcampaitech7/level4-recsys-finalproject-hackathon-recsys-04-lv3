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
    아래 텍스트를 기반으로 수능 수준의 O/X 퀴즈 5개를 만들어주세요. 
    다음 조건을 충족해야 합니다:
    1. 질문은 개념 이해와 문제 해결 능력을 평가할 수 있어야 합니다.
    2. 정답이 "O"인 문제와 "X"인 문제의 비율은 균형 있게 구성해주세요.
    3. 질문의 난이도는 수능 수준에 맞춰 구체적이고 사고를 요하는 내용을 포함해야 합니다.
    4. 각 질문의 정답에 대한 설명은 간결하지만 충분히 납득 가능하게 작성해주세요.

    응답은 반드시 JSON 형식으로 반환하세요. 형식은 다음과 같습니다:
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
