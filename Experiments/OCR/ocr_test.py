import io
import re
import time
import requests
import fitz
from openai import OpenAI
from PIL import Image
from PIL import ImageOps

class OCR_PREPRO():
    """
    __init__: OCR API 요청을 위한 기본 설정을 초기화
    img_base: 원본 이미지를 OCR API에 전달하여 텍스트를 추출
    img_gray: 이미지를 그레이스케일로 변환한 후 OCR을 수행
    img_quality: 이미지 품질을 50%로 낮춘 후 OCR을 수행
    img_gray_quality: 이미지를 그레이스케일로 변환한 후 품질을 50%로 낮추고 OCR을 수행
    pdf_base: 원본 PDF를 OCR API에 전달하여 텍스트를 추출
    pdf_gray: PDF를 그레이스케일로 변환한 후 OCR을 수행
    pdf_quality: PDF 품질을 50%로 낮춘 후 OCR을 수행
    pdf_gray_quality: PDF를 그레이스케일로 변환한 후 품질을 50%로 낮추고 OCR을 수행

    """
    def __init__(self, api_key):
        self.url = "https://api.upstage.ai/v1/document-ai/ocr"
        self.headers = {"Authorization": f"Bearer {api_key}"}

    def img_base(self, filename):
        start_time = time.perf_counter()
        files = {"document": open(filename, "rb")}
        response = requests.post(self.url, headers=self.headers, files=files)
        
        end_time = time.perf_counter()
        return response.json()["text"], (end_time - start_time) * 1000

    def img_gray(self, filename):
        start_time = time.perf_counter()
        with Image.open(filename) as img:
            img = ImageOps.exif_transpose(img)
            grayscale_img = img.convert("L")

            with io.BytesIO() as buffer:
                grayscale_img.save(buffer, format="JPEG")
                buffer.seek(0)
                grayscale_bytes = buffer.read()

        files = {"document": ("test_1.jpg", grayscale_bytes, "image/jpeg")}
        response = requests.post(self.url, headers=self.headers, files=files)
        
        end_time = time.perf_counter()
        return response.json()["text"], (end_time - start_time) * 1000
    
    def img_quality(self, filename):
        start_time = time.perf_counter()
        with Image.open(filename) as img:
            img = ImageOps.exif_transpose(img)
            with io.BytesIO() as buffer:
                img.save(buffer, format="JPEG", quality=50) 
                buffer.seek(0)
                compressed_file = buffer.read()

        files = {"document": ("compressed_test_1.jpg", compressed_file, "image/jpeg")}
        response = requests.post(self.url, headers=self.headers, files=files)

        end_time = time.perf_counter()
        return response.json()["text"], (end_time - start_time) * 1000
    
    def img_gray_quality(self, filename):
        start_time = time.perf_counter()

        with Image.open(filename) as img:
            img = ImageOps.exif_transpose(img)
            grayscale_img = img.convert("L")
            
            with io.BytesIO() as buffer:
                grayscale_img.save(buffer, format="JPEG", quality=50)
                buffer.seek(0)
                compressed_file = buffer.read()

        files = {"document": ("compressed_test_1.jpg", compressed_file, "image/jpeg")}
        response = requests.post(self.url, headers=self.headers, files=files)

        end_time = time.perf_counter()
        return response.json()["text"], (end_time - start_time) * 1000
    
    def pdf_base(self, filename):
        start_time = time.perf_counter()
        files = {"document": open(filename, "rb")}
        response = requests.post(self.url, headers=self.headers, files=files)
        
        end_time = time.perf_counter()
        return response.json()["text"], (end_time - start_time) * 1000
    
    def pdf_gray(self, filename):
        start_time = time.perf_counter()
        doc = fitz.open(filename)
        output_pdf = fitz.open()

        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            
            pix = page.get_pixmap()
            
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            
            with io.BytesIO() as buffer:
                img.convert("L").save(buffer, format="JPEG")
                buffer.seek(0)
                
                rect = fitz.Rect(0, 0, pix.width, pix.height)
                new_page = output_pdf.new_page(width=pix.width, height=pix.height)
                new_page.insert_image(rect, stream=buffer.getvalue())

        with io.BytesIO() as pdf_buffer:
            output_pdf.save(pdf_buffer)
            pdf_buffer.seek(0)
            
            files = {"document": ("gray.pdf", pdf_buffer, "application/pdf")}
            response = requests.post(self.url, headers=self.headers, files=files)
        end_time = time.perf_counter()
        
        return response.json()["text"], (end_time - start_time) * 1000
    
    def pdf_quality(self, filename):
        start_time = time.perf_counter()
        doc = fitz.open(filename)
        output_pdf = fitz.open()

        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            
            pix = page.get_pixmap()
            
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            
            with io.BytesIO() as buffer:
                img.save(buffer, format="JPEG", quality=50)
                buffer.seek(0)
                
                rect = fitz.Rect(0, 0, pix.width, pix.height)
                new_page = output_pdf.new_page(width=pix.width, height=pix.height)
                new_page.insert_image(rect, stream=buffer.getvalue())

        with io.BytesIO() as pdf_buffer:
            output_pdf.save(pdf_buffer)
            pdf_buffer.seek(0)
            
            files = {"document": ("quality.pdf", pdf_buffer, "application/pdf")}
            response = requests.post(self.url, headers=self.headers, files=files)
        end_time = time.perf_counter()
        
        return response.json()["text"], (end_time - start_time) * 1000
    
    def pdf_gray_quality(self, filename):
        start_time = time.perf_counter()
        doc = fitz.open(filename)
        output_pdf = fitz.open()

        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            
            pix = page.get_pixmap()
            
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            
            with io.BytesIO() as buffer:
                img.convert("L").save(buffer, format="JPEG", quality=50)
                buffer.seek(0)
                
                rect = fitz.Rect(0, 0, pix.width, pix.height)
                new_page = output_pdf.new_page(width=pix.width, height=pix.height)
                new_page.insert_image(rect, stream=buffer.getvalue())

        with io.BytesIO() as pdf_buffer:
            output_pdf.save(pdf_buffer)
            pdf_buffer.seek(0)
            
            files = {"document": ("gray_quality.pdf", pdf_buffer, "application/pdf")}
            response = requests.post(self.url, headers=self.headers, files=files)
        end_time = time.perf_counter()
        
        return response.json()["text"], (end_time - start_time) * 1000

class TEXT_CONTROL():
    def __init__(self, api_key):
        self.chat_client = OpenAI(api_key=api_key, base_url="https://api.upstage.ai/v1/solar")

    def chat_with_solar(self, text):
        start_time = time.perf_counter()
        """
        OCR을 통해 얻은 노트 필기 결과를 Solar AI 모델을 사용하여 정제된 텍스트로 변환하는 함수.

        Args:
            chat_client: Solar AI 모델과의 채팅을 수행할 클라이언트 객체.
            text (String): OCR로 변환된 원본 텍스트.

        Returns:
            text (String): 정제된 본문 텍스트
        """
        content = f"""
        노트 필기를 OCR을 통해 얻은 결과야. 아래의 규칙을 지켜서 출력해줘.
        1. 본문 내용은 수정하지 않는다.
        2. OCR로 인한 띄워쓰기가 이상한 부분의 띄워쓰기를 수정한다.
        3. 본문의 의미 없는 띄워쓰기는 제거한다.
        4. 출력은 다른 설명은 필요 없고 본문만 출력한다.
        본문: 
        {text}
        """
        messages = [{"role": "user", "content": content}]
        response = self.chat_client.chat.completions.create(
            model="solar-pro",
            messages=messages
        )
        end_time = time.perf_counter()
        return response.choices[0].message.content, (end_time - start_time) * 1000
    
    def str_to_txt(self, filename, text):
        """
        문자열을 UTF-8 인코딩된 텍스트 파일로 저장하는 함수.

        Args:
            filename (String): 저장할 파일의 이름 (확장자 없이 입력하면 ".txt"가 자동 추가됨).
            text (String): 파일에 저장할 문자열 데이터.
        """
        filename = filename + ".txt"
        with open(filename, "w", encoding="utf-8") as file:
            file.write(text)
    
    def calculate_accuracy_and_remaining(self, target, ocr):
        """
        target과 ocr 리스트를 비교하여 정답률과 각 리스트에 남은 항목을 반환합니다.
        
        Args:
            target (list): 비교 대상이 되는 리스트.
            ocr (list): 참조 리스트.
        
        Returns:
            tuple: 
                - 정답률 (float)
                - ocr에 남은 항목 (list)
                - target에 남은 항목 (list)
        """
        # 초기 길이 저장
        target_len_before = len(target)

        # target에서 ocr에 있는 항목을 제거
        target_remaining = [name for name in target if name not in ocr]

        # ocr에서 target에 없는 항목 제거
        ocr_remaining = [name for name in ocr if name not in target]

        # 정답률 계산
        target_len_after = len(target_remaining)
        accuracy = ((target_len_before - target_len_after) / target_len_before) * 100

        return accuracy, ocr_remaining, target_remaining

    def read_txt_file(self, file_path):
        """
        텍스트 파일을 읽고 내용을 띄어쓰기 기준으로 배열로 변환합니다.

        Args:
            file_path (str): 불러올 txt 파일 경로

        Returns:
            list: 공백을 기준으로 나눈 문자열 리스트
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read()
                content = re.sub(r'[^\w\s]', ' ', content).strip()
            words = [word for word in content.split() if word]
            return words
        except FileNotFoundError:
            print(f"파일을 찾을 수 없습니다: {file_path}.txt")
            return []
        except Exception as e:
            print(f"오류 발생: {e}")
            return []

class OCR_TEST():
    def __init__(self, api_key, loop, filename, target):
        self.ocr_prepro = OCR_PREPRO(api_key)
        self.text_control = TEXT_CONTROL(api_key)
        self.loop = loop
        self.filename = filename
        self.target_list = self.text_control.read_txt_file(target)
        
    def img_test(self):
        score = [0, 0, 0, 0, 0]
        time_sum = [0, 0, 0, 0, 0]

        for _ in range(0, self.loop):
            test = ["", "", "", "", ""]

            ocr_methods = [
                self.ocr_prepro.img_base,
                self.ocr_prepro.img_gray,
                self.ocr_prepro.img_quality,
                self.ocr_prepro.img_gray_quality
            ]

            for i, method in enumerate(ocr_methods):
                result, time_taken = method(self.filename)
                test[i] = result
                time_sum[i] += time_taken

            base_result, base_time = self.ocr_prepro.img_base(self.filename)
            chat_result, chat_time = self.text_control.chat_with_solar(base_result)

            test[4] = chat_result
            time_sum[4] += base_time + chat_time

            for i in range(5):
                score[i] += self.text_control.calculate_accuracy_and_remaining(self.target_list, test[i])[0]

        print(f"img accuracy test(%): \n\t base: {score[0]/self.loop} \n\t gray: {score[1]/self.loop} \n\t quality: {score[2]/self.loop} \n\t gray+quality: {score[3]/self.loop} \n\t base+LLM: {score[4]/self.loop}")
        print(f"img time test(ms): \n\t base: {time_sum[0]/self.loop} \n\t gray: {time_sum[1]/self.loop} \n\t quality: {time_sum[2]/self.loop} \n\t gray+quality: {time_sum[3]/self.loop} \n\t base+LLM: {time_sum[4]/self.loop}")
        
    def pdf_test(self):
        score = [0, 0, 0, 0, 0]
        time_sum = [0, 0, 0, 0, 0]

        for _ in range(0, self.loop):
            test = ["", "", "", "", ""]

            pdf_methods = [
                self.ocr_prepro.pdf_base,
                self.ocr_prepro.pdf_gray,
                self.ocr_prepro.pdf_quality,
                self.ocr_prepro.pdf_gray_quality
            ]

            for i, method in enumerate(pdf_methods):
                result, time_taken = method(self.filename)
                test[i] = result
                time_sum[i] += time_taken

            base_result, base_time = self.ocr_prepro.pdf_base(self.filename)
            chat_result, chat_time = self.text_control.chat_with_solar(base_result)

            test[4] = chat_result
            time_sum[4] += base_time + chat_time

            for i in range(5):
                score[i] += self.text_control.calculate_accuracy_and_remaining(self.target_list, test[i])[0]

        print(f"pdf accuracy test(%): \n\t base: {score[0]/self.loop} \n\t gray: {score[1]/self.loop} \n\t quality: {score[2]/self.loop} \n\t gray+quality: {score[3]/self.loop} \n\t base+LLM: {score[4]/self.loop}")
        print(f"pdf time test(ms): \n\t base: {time_sum[0]/self.loop} \n\t gray: {time_sum[1]/self.loop} \n\t quality: {time_sum[2]/self.loop} \n\t gray+quality: {time_sum[3]/self.loop} \n\t base+LLM: {time_sum[4]/self.loop}")

if __name__ == "__main__":
    api_key = ""
    loop = 1 
    filename = ".pdf | .jpg"
    target = ".txt"

    test = OCR_TEST(api_key, loop, filename, target)
    if filename[-4:len(filename)] == ".pdf":
        test.pdf_test()
    else:
        test.img_test()