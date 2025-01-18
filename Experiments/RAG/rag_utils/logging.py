import os


# https://github.com/teddylee777/langchain-teddynote/blob/main/langchain_teddynote/logging.py
def langsmith(project_name=None, set_enable=True):
    """
    LangSmith 추적을 설정하고 활성화/비활성화합니다.

    Args:
        project_name (str, optional): LangSmith 프로젝트 이름. 기본값은 None입니다.
        set_enable (bool, optional): 추적 활성화 여부. 기본값은 True입니다.

    Returns:
        None

    Raises:
        None

    Notes:
        - LangChain API Key가 환경 변수에 설정되어 있어야 합니다.
        - API Key가 설정되지 않은 경우 안내 메시지를 출력합니다.
        - 추적이 활성화되면 LangSmith API 엔드포인트와 프로젝트 이름이 설정됩니다.

    Example:
        langsmith("my_project")  # LangSmith 추적을 "my_project"로 활성화
        langsmith(set_enable=False)  # LangSmith 추적을 비활성화
    """

    if set_enable:
        result = os.environ.get("LANGCHAIN_API_KEY")
        if result is None or result.strip() == "":
            print("LangChain API Key가 설정되지 않았습니다. 참고: https://wikidocs.net/250954")
            return
        os.environ["LANGCHAIN_ENDPOINT"] = "https://api.smith.langchain.com"  # LangSmith API 엔드포인트
        os.environ["LANGCHAIN_TRACING_V2"] = "true"  # true: 활성화
        os.environ["LANGCHAIN_PROJECT"] = project_name  # 프로젝트명
        print(f"LangSmith 추적을 시작합니다.\n[프로젝트명]\n{project_name}")
    else:
        os.environ["LANGCHAIN_TRACING_V2"] = "false"  # false: 비활성화
        print("LangSmith 추적을 하지 않습니다.")
