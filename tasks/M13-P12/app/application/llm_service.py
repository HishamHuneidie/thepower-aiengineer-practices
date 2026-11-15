"""
Service with LLM utils
- Image to text
- Audio to text
"""

from app.domain.entities import Audio, Image, Message
from ollama import chat
import whisper
from tempfile import NamedTemporaryFile
from dotenv import load_dotenv
import os
from gtts import gTTS


load_dotenv()


IMAGE_MODEL_ID = os.getenv('IMAGE_MODEL_ID')
GENER_MODEL_ID = os.getenv('GENER_MODEL_ID')


class LLMService:

    def read_audio(self, audio: Audio) -> str:
        """Use a LLM model to transcribe this audio"""

        try:
            model = whisper.load_model('base', device='cpu')

            with NamedTemporaryFile() as temporal:
                temporal.write(audio.getvalue())
                temporal.flush()

                response = model.transcribe(temporal.name, fp16=False)

                return response['text']
        except:
            return ''


    def read_image(self, image: Image) -> str:
        """Use a LLM model to transcribe this image"""

        try:
            content = image.read()

            response = chat(model=IMAGE_MODEL_ID, messages=[{
                'role': 'user',
                'content': """
                    Describe this image and transcribe all text in it. 
                    Return just the text in the image.
                    If there is no text then return empty string
                """,
                'images': [content],
            }])

            return response.message.content
        except Exception as e:
            return ''


    def reply(self, message: Message) -> str:
        """Replies a user message"""

        system_message = """
            Answer user message.
            There will be three possible sections: user message, audio transcript and image transcript.
            Order of priority from instructions to context: user message, audio transcript and image transcript.
            What is a user message: Main instruction.
            What is an audio transcript: Secondary instruction or context.
            What is an image transcript: Context.
            
            MANDATORY AND CONSTRAINTS:
            - You MUST reply with less than 80 characters NO MATTER WHAT.
        """

        human_message = f"""
            User message:
            {message.text}
            ---
            
            Audio transcript:
            {message.audio_transcript or 'None'}
            ---
            
            Image transcript:
            {message.image_transcript or 'None'}
            ---
        """

        try:
            response = chat(model=GENER_MODEL_ID, messages=[
                {'role': 'system', 'content': system_message},
                {'role': 'user', 'content': human_message},
            ])

            return response.message.content
        except Exception as e:
            return ''


    def generate_audio(self, text: str) -> Audio|None:
        """Use a LLM model to transcribe this audio"""

        audio = Audio()

        try:
            gTTS(text=text, lang='es', slow=False).write_to_fp(audio)
            audio.seek(0)

            return audio
        except Exception as e:
            print(e)
            return None
