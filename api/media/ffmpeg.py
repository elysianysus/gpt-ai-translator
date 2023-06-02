import os
import requests
from urllib.parse import urljoin

from dotenv import load_dotenv

load_dotenv()


class FFmpeg:
    def __init__(self):
        self.endpoint = os.getenv("FFMPEG_API_ENDPOINT")

    def get_media_duration(self, media_path):
        files = {"file": open(media_path, "rb")}
        response = requests.post(urljoin(self.endpoint, "/probe"), files=files)
        return response.json()["format"]["duration"]
