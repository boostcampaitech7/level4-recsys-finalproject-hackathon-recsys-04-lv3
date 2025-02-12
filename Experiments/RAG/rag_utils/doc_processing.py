from PyPDF2 import PdfReader, PdfWriter


def pdf_slicing(file_path, pages):
    """
    PDF 파일에서 특정 페이지 범위를 추출하여 새로운 PDF 파일로 저장합니다.

    Args:
        file_path (str): 원본 PDF 파일의 경로
        pages (tuple): 추출할 페이지 범위 (시작 페이지, 끝 페이지)

    Returns:
        None: 함수는 새로운 PDF 파일을 생성하지만 아무것도 반환하지 않습니다.

    Example:
        pdf_slicing("./data/example.pdf", (5, 20))
        # 'example_page_5-20.pdf' 파일이 생성됩니다.
    """

    reader = PdfReader(file_path)
    writer = PdfWriter()
    page_range = range(pages[0], pages[1] + 1)

    for page_num, page in enumerate(reader.pages, 1):
        if page_num in page_range:
            writer.add_page(page)

    with open(f"{file_path[:-4]}_page_{pages[0]}-{pages[1]}.pdf", "wb") as out:
        writer.write(out)
