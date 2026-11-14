"""
Work with images.
- Retrieve
- Read
"""
from app.application.multimedia_service import MultimediaService
from app.domain.entities import Image
from app.infrastructure.files import get_file


class ImageService(MultimediaService):

    def get(self, name: str) -> Image:
        """Download file from MinIO"""
        content, mine = get_file(name)

        return Image(content)


    def read(self, image: Image) -> str:
        """Read text inside the image"""

        return self.llm_service.read_image(image)