from app.domain.entities import Message
from app.domain.repositories import MessageRepository


def reply(message: Message) -> Message:
    # Escribe aquí tu solución. El texto recibido está en message.text.
    return Message(text="respondimiento", role="assistant")


def send_message(message: Message, repository: MessageRepository) -> Message:
    response = reply(message)
    repository.save([message, response])
    return response


def get_messages(repository: MessageRepository) -> list[Message]:
    return repository.list_all()
