import os
import io
import requests

from fastapi import UploadFile, HTTPException
from PIL import Image, ImageOps
from app.core.config import settings


async def perform_ocr(file: UploadFile) -> str:
    allowed_formats = {"image/png", "image/jpeg", "image/jpg", "application/pdf"}

    if file.content_type not in allowed_formats:
        raise HTTPException(
            status_code=400,
            detail="File type not supported. Supported types are: PNG, JPEG, PDF",
        )

    headers = {"Authorization": f"Bearer {os.environ['UPSTAGE_API_KEY']}"}

    if file.content_type == "application/pdf":
        files = {"document": file.file}
    else:
        try:
            img = Image.open(file.file)
            img = ImageOps.exif_transpose(img)
            grayscale_img = img.convert("L")

            buffer = io.BytesIO()
            grayscale_img.save(buffer, format="JPEG", quality=50)
            buffer.seek(0)

            files = {"document": buffer.getvalue()}
        except Exception as e:
            raise HTTPException(
                status_code=500, detail=f"Image processing failed: {str(e)}"
            )

    response = requests.post(settings.UPSTAGE_OCR_URL, headers=headers, files=files)

    if response.status_code == 200:
        response.encoding = "utf-8"
        response_data = response.json()
        return response_data["text"]
    else:
        raise HTTPException(
            status_code=response.status_code, detail=f"OCR failed: {response.text}"
        )
