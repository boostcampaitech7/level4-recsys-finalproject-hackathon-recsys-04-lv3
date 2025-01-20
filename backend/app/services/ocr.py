from fastapi import UploadFile, HTTPException
import requests
from app.core.config import settings

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
    
    url = "https://api.upstage.ai/v1/document-ai/ocr"
    headers = {
        "Authorization": f"Bearer {settings.UPSTAGE_API_KEY}"
    }
    
    files = {"document": file.file}
    response = requests.post(url, headers=headers, files=files)
    
    if response.status_code == 200:
        return response.json().get('text', '')
    else:
        raise HTTPException(
            status_code=response.status_code,
            detail=f"OCR failed: {response.text}"
        )