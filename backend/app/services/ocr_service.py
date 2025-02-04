from fastapi import UploadFile, HTTPException
import requests
from app.core.config import settings
from openai import OpenAI
import os

async def perform_ocr(file: UploadFile) -> str:
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

    headers = {
        "Authorization": f"Bearer {os.environ['UPSTAGE_API_KEY']}"
    }
    
    files = {"document": file.file}
    response = requests.post(settings.UPSTAGE_OCR_URL, headers=headers, files=files)
    
    if response.status_code == 200:
        response.encoding = 'utf-8'
        response_data = response.json()
        
        return response_data["text"]
    else:
        raise HTTPException(
            status_code=response.status_code,
            detail=f"OCR failed: {response.text}"
        )