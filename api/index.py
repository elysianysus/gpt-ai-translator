import os
import librosa
import hashlib

from dotenv import load_dotenv
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import (
    MessageEvent,
    TextMessage,
    AudioMessage,
    TextSendMessage,
    AudioSendMessage,
    QuickReply,
    QuickReplyButton,
    MessageAction,
)
from gtts import gTTS
from minio import Minio
from api.ai.chatgpt import ChatGPT
from api.config.configs import *

load_dotenv()

app = Flask(__name__)
environment = Environment[os.getenv("APP_ENVIRONMENT", Environment.VERCEL.value)]
if environment == Environment.DEVELOPMENT:
    app.config.from_object(DevelopmentConfig)
elif environment == Environment.PRODUCTION:
    app.config.from_object(ProductionConfig)
elif environment == Environment.VERCEL:
    app.config.from_object(ProductionForVercelConfig)

line_bot_api = LineBotApi(os.getenv("LINE_CHANNEL_ACCESS_TOKEN"))
line_handler = WebhookHandler(os.getenv("LINE_CHANNEL_SECRET"))

chatgpt = ChatGPT()

# region Language related

lang_dict = {
    "繁體中文": "Traditional Chinese",
    "簡體中文": "Simplified Chinese",
    "英文": "English",
    "日文": "Japanese",
    "韓文": "Korean",
    "越南文": "Vietnamese",
    "泰文": "Thai",
    "義大利文": "Italian",
    "西班牙文": "Spanish",
    "葡萄牙文": "Portuguese",
    "荷蘭文": "Dutch",
    "德文": "German",
    "法文": "French",
}
reverse_lang_dict = {value: key for key, value in lang_dict.items()}
# IETF language tag
ietf_lang_dict = {
    "Traditional Chinese": "zh-TW",
    "Simplified Chinese": "zh-CN",
    "English": "en",
    "Japanese": "ja",
    "Korean": "ko",
    "Vietnamese": "vi",
    "Thai": "th",
    "Italian": "it",
    "Spanish": "es",
    "Portuguese": "pt",
    "Dutch": "nl",
    "German": "de",
    "French": "fr",
}

# endregion

# region User related

user_translate_language_key = "translate_language"
user_audio_language_key = "audio_language"

user_dict = {}

# endregion


@app.route("/")
def home():
    return "OK"


@app.route("/webhook", methods=["POST"])
def callback():
    signature = request.headers["X-Line-Signature"]
    body = request.get_data(as_text=True)
    try:
        line_handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return "OK"


@line_handler.add(MessageEvent, message=TextMessage)
def handle_text_message(event):
    user_id = event.source.user_id
    if not (user_exists(user_id)):
        init_user_lang(user_id)
    user_input = event.message.text
    if (user_input == "/setting") or (user_input == "設定"):
        flex_message = TextSendMessage(
            text="請選擇語音辨識後的翻譯語言（我方語言）",
            quick_reply=QuickReply(
                items=[
                    QuickReplyButton(
                        action=MessageAction(label="繁體中文", text="設定辨識翻譯 " + "繁體中文")
                    ),
                    QuickReplyButton(
                        action=MessageAction(label="簡體中文", text="設定辨識翻譯 " + "簡體中文")
                    ),
                    QuickReplyButton(
                        action=MessageAction(label="英文", text="設定辨識翻譯 " + "英文")
                    ),
                    QuickReplyButton(
                        action=MessageAction(label="日文", text="設定辨識翻譯 " + "日文")
                    ),
                    QuickReplyButton(
                        action=MessageAction(label="韓文", text="設定辨識翻譯 " + "韓文")
                    ),
                    QuickReplyButton(
                        action=MessageAction(label="越南文", text="設定辨識翻譯 " + "越南文")
                    ),
                    QuickReplyButton(
                        action=MessageAction(label="泰文", text="設定辨識翻譯 " + "泰文")
                    ),
                    QuickReplyButton(
                        action=MessageAction(label="義大利文", text="設定辨識翻譯 " + "義大利文")
                    ),
                    QuickReplyButton(
                        action=MessageAction(label="西班牙文", text="設定辨識翻譯 " + "西班牙文")
                    ),
                    QuickReplyButton(
                        action=MessageAction(label="葡萄牙文", text="設定辨識翻譯 " + "葡萄牙文")
                    ),
                    QuickReplyButton(
                        action=MessageAction(label="荷蘭文", text="設定辨識翻譯 " + "荷蘭文")
                    ),
                    QuickReplyButton(
                        action=MessageAction(label="德文", text="設定辨識翻譯 " + "德文")
                    ),
                    QuickReplyButton(
                        action=MessageAction(label="法文", text="設定辨識翻譯 " + "法文")
                    ),
                ]
            ),
        )
        line_bot_api.reply_message(event.reply_token, flex_message)

    elif "設定辨識翻譯" in user_input:
        # Set audio language by user
        user_dict[user_id][user_audio_language_key] = lang_dict[
            user_input.split(" ")[1]
        ]
        flex_message = TextSendMessage(
            text="請選擇打字後的翻譯語言（對方語言）",
            quick_reply=QuickReply(
                items=[
                    QuickReplyButton(
                        action=MessageAction(label="繁體中文", text="設定打字翻譯 " + "繁體中文")
                    ),
                    QuickReplyButton(
                        action=MessageAction(label="簡體中文", text="設定打字翻譯 " + "簡體中文")
                    ),
                    QuickReplyButton(
                        action=MessageAction(label="英文", text="設定打字翻譯 " + "英文")
                    ),
                    QuickReplyButton(
                        action=MessageAction(label="日文", text="設定打字翻譯 " + "日文")
                    ),
                    QuickReplyButton(
                        action=MessageAction(label="韓文", text="設定打字翻譯 " + "韓文")
                    ),
                    QuickReplyButton(
                        action=MessageAction(label="越南文", text="設定打字翻譯 " + "越南文")
                    ),
                    QuickReplyButton(
                        action=MessageAction(label="泰文", text="設定打字翻譯 " + "泰文")
                    ),
                    QuickReplyButton(
                        action=MessageAction(label="義大利文", text="設定打字翻譯 " + "義大利文")
                    ),
                    QuickReplyButton(
                        action=MessageAction(label="西班牙文", text="設定打字翻譯 " + "西班牙文")
                    ),
                    QuickReplyButton(
                        action=MessageAction(label="葡萄牙文", text="設定打字翻譯 " + "葡萄牙文")
                    ),
                    QuickReplyButton(
                        action=MessageAction(label="荷蘭文", text="設定打字翻譯 " + "荷蘭文")
                    ),
                    QuickReplyButton(
                        action=MessageAction(label="德文", text="設定打字翻譯 " + "德文")
                    ),
                    QuickReplyButton(
                        action=MessageAction(label="法文", text="設定打字翻譯 " + "法文")
                    ),
                ]
            ),
        )
        line_bot_api.reply_message(event.reply_token, flex_message)

    elif "設定打字翻譯" in user_input:
        # Set translate language by user
        user_dict[user_id][user_translate_language_key] = lang_dict[
            user_input.split(" ")[1]
        ]
        # Format response message
        audio_language = user_dict[user_id][user_audio_language_key]
        translate_language = user_dict[user_id][user_translate_language_key]
        response_text = f"""設定完畢！
我方語言：{reverse_lang_dict[audio_language]}（{audio_language}）
對方語言：{reverse_lang_dict[translate_language]}（{translate_language}）"""
        line_bot_api.reply_message(
            event.reply_token, TextSendMessage(text=response_text)
        )

    elif (user_input == "/current-setting") or (user_input == "目前設定"):
        # Format response message
        audio_language = user_dict[user_id][user_audio_language_key]
        translate_language = user_dict[user_id][user_translate_language_key]
        response_text = f"""我方語言：{reverse_lang_dict[audio_language]}（{audio_language}）
對方語言：{reverse_lang_dict[translate_language]}（{translate_language}）"""
        line_bot_api.reply_message(
            event.reply_token, TextSendMessage(text=response_text)
        )

    else:
        # Translate result from user input
        translated_text = chatgpt.translate(
            user_input, user_dict[user_id][user_translate_language_key]
        )
        line_bot_api.reply_message(
            event.reply_token, TextSendMessage(text=translated_text)
        )
        if os.getenv("APP_PUSH_TRANSLATED_TEXT_AUDIO_ENABLED", "false") == "true":
            translated_text_audio_path = os.path.join(
                app.config.get("AUDIO_TEMP_PATH"), f"{event.message.id}.m4a"
            )
            # Translated result to audio file
            tts = gTTS(
                translated_text,
                lang=ietf_lang_dict[user_dict[user_id][user_translate_language_key]],
            )
            tts.save(translated_text_audio_path)
            # Operate audio file with minio
            clean_audios(user_id)
            upload_audio(user_id, translated_text_audio_path)
            translated_text_audio_url = get_audio_url(
                user_id, translated_text_audio_path
            )
            # translated_text_audio_duration = (
            #     get_audio_duration(translated_text_audio_path) * 1000
            # )
            line_bot_api.push_message(
                user_id,
                AudioSendMessage(
                    original_content_url=translated_text_audio_url,
                    duration=30000,
                ),
            )


@line_handler.add(MessageEvent, message=AudioMessage)
def handle_audio_message(event):
    user_id = event.source.user_id
    if not (user_exists(user_id)):
        init_user_lang(user_id)
    # Read voice message for whisper api input
    message_id = event.message.id
    user_audio_path = os.path.join(
        app.config.get("AUDIO_TEMP_PATH"), f"{message_id}.m4a"
    )
    with open(user_audio_path, "wb") as f:
        f.write(line_bot_api.get_message_content(message_id).content)
    whispered_text = chatgpt.whisper(user_audio_path)
    if os.path.exists(user_audio_path):
        os.remove(user_audio_path)
    # Translate result from whisper api output
    translated_text = chatgpt.translate(
        whispered_text, user_dict[user_id][user_audio_language_key]
    )
    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=translated_text))


def user_exists(user_id):
    return user_id in user_dict


def init_user_lang(user_id):
    user_dict[user_id] = {
        user_translate_language_key: "Japanese",
        user_audio_language_key: "Traditional Chinese",
    }


def get_minio_client():
    client = Minio(
        os.getenv("MINIO_ENDPOINT"),
        access_key=os.getenv("MINIO_ACCESS_KEY"),
        secret_key=os.getenv("MINIO_SECRET_KEY"),
    )
    return client


def clean_audios(user_id):
    client = get_minio_client()
    bucket_name = os.getenv("MINIO_BUCKET", "gpt-ai-translator")
    objects = client.list_objects(
        bucket_name, prefix=hashlib.sha256(user_id.encode()).hexdigest(), recursive=True
    )
    for object in objects:
        client.remove_object(bucket_name, object.object_name)


def upload_audio(user_id, audio_path):
    client = get_minio_client()
    bucket_name = os.getenv("MINIO_BUCKET", "gpt-ai-translator")
    object_name = f"/{hashlib.sha256(user_id.encode()).hexdigest()}/{os.path.basename(audio_path)}"
    if not client.bucket_exists(bucket_name):
        client.make_bucket(bucket_name)
    client.fput_object(bucket_name, object_name, audio_path)


def get_audio_url(user_id, audio_path):
    client = get_minio_client()
    bucket_name = os.getenv("MINIO_BUCKET", "gpt-ai-translator")
    object_name = f"/{hashlib.sha256(user_id.encode()).hexdigest()}/{os.path.basename(audio_path)}"
    return client.presigned_get_object(bucket_name, object_name)


def get_audio_duration(audio_path):
    return librosa.get_duration(path=audio_path)


if __name__ == "__main__":
    app.run()
