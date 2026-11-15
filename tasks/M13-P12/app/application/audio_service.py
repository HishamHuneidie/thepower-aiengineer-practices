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
        content, mine = get_file(name)

        return Audio(content)


    def read(self, audio: Audio) -> str:
        """Convert speech to text"""

        return self.llm_service.read_audio(audio)


    def generate(self, text: str) -> Audio|None:
        """Convert text to speech"""

        return self.llm_service.generate_audio(text)