import os
import openai

from dotenv import load_dotenv

load_dotenv()

openai.api_key = os.getenv("OPENAI_API_KEY")


class ChatGPT:
    def __init__(self):
        self.model = "gpt-3.5-turbo"
        self.temperature = 0.5

    def whisper(self, audio_path):
        audio_file = open(audio_path, "rb")
        transcript = openai.Audio.transcribe("whisper-1", audio_file)
        return transcript["text"]

    def translate(self, text, language):
        prompt = f"""'{text}'
        Help me to translate this sentence to {language}, only target language, no need original language."""
        response = openai.ChatCompletion.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=self.temperature
        )
        return response['choices'][0]['message']['content']
