from app.domain.entities import Message
from app.application.audio_service import AudioService
from app.application.image_service import ImageService
from app.application.llm_service import LLMService
from app.domain.repositories import MessageRepository
from app.infrastructure.files import locate_file_name, save_file


audio_service = AudioService()
image_service = ImageService()
llm_service = LLMService()


def reply(message: Message) -> Message:
    response = llm_service.reply(message)

    return Message(text=response, role="assistant")


def send_message(message: Message, repository: MessageRepository) -> Message:
    has_audio = False

    if message.audio_path:
        has_audio = True
        audio = audio_service.get(locate_file_name(message.audio_path))
        message.audio_transcript = audio_service.read(audio)

    if message.image_path:
        image = image_service.get(locate_file_name(message.image_path))
        message.image_transcript = image_service.read(image)

    response = reply(message)

    if has_audio and response.text != '' and response.text is not None:
        generated_audio = audio_service.generate(response.text)
        if generated_audio:
            response.response_in_audio_path = save_file(generated_audio.getvalue(), 'audio/mpeg', 'audio')

    repository.save([message, response])

    return response


def get_messages(repository: MessageRepository) -> list[Message]:
    return repository.list_all()
