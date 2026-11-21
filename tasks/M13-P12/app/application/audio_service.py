"""
Work with audio.
- Read
- Generate
"""
from app.application.multimedia_service import MultimediaService
from app.domain.entities import Audio
from app.infrastructure.files import get_file


class AudioService(MultimediaService):

    def get(self, name: str) -> Audio:
        """Download file from MinIO"""
        content, mime = get_file(name)

        audio = Audio(content)
        audio.mime_type = mime

        return audio


    def read(self, audio: Audio) -> str:
        """Convert speech to text"""

        return self.llm_service.read_audio(audio)


    def generate(self, text: str) -> Audio:
        """Convert text to speech"""

        return self.llm_service.generate_audio(text)
