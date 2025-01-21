from fastapi import UploadFile, HTTPException
import requests
from app.core.config import settings
from openai import OpenAI
import os

async def perform_ocr(file: UploadFile) -> str:
    def chat_with_solar(text):
        content = f"""
        노트 필기를 OCR을 통해 얻은 결과야. 아래의 규칙을 지켜서 출력해줘.
        1. 본문 내용은 수정하지 않는다.
        2. OCR로 인한 오타로 보이는 부분의 오타를 수정한다.
        3. OCR로 인한 띄워쓰기가 이상한 부분의 띄워쓰기를 수정한다.
        4. 본문의 의미 없는 띄워쓰기는 제거한다.
        5. 출력은 다른 설명은 필요 없고 본문만 출력한다.
        본문: 
        {text}
        """
        messages = [{"role": "user", "content": content}]
        response = chat_client.chat.completions.create(
            model="solar-pro",
            messages=messages
        )
        return response.choices[0].message.content

    allowed_formats = {
        'image/png', 
        'image/jpeg', 
        'image/jpg', 
        'application/pdf'
    }
    
    if file.content_type not in allowed_formats:
        raise HTTPException(
            status_code=400,
            detail=f"File type not supported. Supported types are: PNG, JPEG, PDF"
        )
    
    chat_client = OpenAI(api_key=os.environ['UPSTAGE_API_KEY'], base_url=settings.UPSTAGE_BASE_URL)

    headers = {
        "Authorization": f"Bearer {os.environ['UPSTAGE_API_KEY']}"
    }
    
    files = {"document": file.file}
    response = requests.post(settings.UPSTAGE_OCR_URL, headers=headers, files=files)
    
    if response.status_code == 200:
        response.encoding = 'utf-8'
        response_data = response.json()
        
        return chat_with_solar(response_data["text"])
    else:
        raise HTTPException(
            status_code=response.status_code,
            detail=f"OCR failed: {response.text}"
        )