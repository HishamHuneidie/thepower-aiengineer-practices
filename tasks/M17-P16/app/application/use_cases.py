from app.application.llm_service import LLMService


llm_service = LLMService()


def reply(message: str) -> str:
    print(f'[user] "{message}"')

    response = llm_service.reply(message)

    print(f'[llm] "{response}"')

    return response
