import os

from dotenv import load_dotenv
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, AudioMessage, TextSendMessage, AudioSendMessage, QuickReply, QuickReplyButton, MessageAction
from api.ai.chatgpt import ChatGPT
from api.config.configs import *

load_dotenv()

app = Flask(__name__)
app.config.from_object(ProductionForVercelConfig)

line_bot_api = LineBotApi(os.getenv("LINE_CHANNEL_ACCESS_TOKEN"))
line_handler = WebhookHandler(os.getenv("LINE_CHANNEL_SECRET"))

chatgpt = ChatGPT()

# region Language related

lang_dict = {
    "繁體中文": "Traditional Chinese",
    "英文": "English",
    "日文": "Japanese",
    "韓文": "Korean",
    "法文": "French",
    "泰文": "Thai",
    "義大利文": "Italian",
    "西班牙文": "Spanish",
    "荷蘭文": "Dutch",
    "德文": "German"
}
reverse_lang_dict = {value: key for key, value in lang_dict.items()}

# endregion

# region User related

user_translate_language_key = 'translate_language'
user_audio_language_key = 'audio_language'

user_dict = {}

# endregion


@app.route('/')
def home():
    return 'Translator now working...'


@app.route('/webhook', methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)
    try:
        line_handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return 'OK'


@line_handler.add(MessageEvent, message=TextMessage)
def handle_text_message(event):
    user_id = event.source.user_id
    if not (user_exists(user_id)):
        init_user_lang(user_id)
    user_input = event.message.text
    if (user_input == "/setting") or (user_input == "設定"):
        flex_message = TextSendMessage(text="請選擇語音辨識後的翻譯語言（我方語言）",
                                       quick_reply=QuickReply(items=[
                                           QuickReplyButton(action=MessageAction(
                                               label="繁體中文", text="設定辨識翻譯 " + "繁體中文")),
                                           QuickReplyButton(action=MessageAction(
                                               label="英文", text="設定辨識翻譯 " + "英文")),
                                           QuickReplyButton(action=MessageAction(
                                               label="日文", text="設定辨識翻譯 " + "日文")),
                                           QuickReplyButton(action=MessageAction(
                                               label="韓文", text="設定辨識翻譯 " + "韓文")),
                                           QuickReplyButton(action=MessageAction(
                                               label="法文", text="設定辨識翻譯 " + "法文")),
                                           QuickReplyButton(action=MessageAction(
                                               label="泰文", text="設定辨識翻譯 " + "泰文")),
                                           QuickReplyButton(action=MessageAction(
                                               label="義大利文", text="設定辨識翻譯 " + "義大利文")),
                                           QuickReplyButton(action=MessageAction(
                                               label="西班牙文", text="設定辨識翻譯 " + "西班牙文")),
                                           QuickReplyButton(action=MessageAction(
                                               label="荷蘭文", text="設定辨識翻譯 " + "荷蘭文")),
                                           QuickReplyButton(action=MessageAction(
                                               label="德文", text="設定辨識翻譯 " + "德文")),
                                       ]))
        line_bot_api.reply_message(event.reply_token, flex_message)

    elif ("設定辨識翻譯" in user_input):
        # Set audio language by user
        user_dict[user_id][user_audio_language_key] = lang_dict[user_input.split(" ")[
            1]]
        flex_message = TextSendMessage(text="請選擇打字後的翻譯語言（對方語言）",
                                       quick_reply=QuickReply(items=[
                                           QuickReplyButton(action=MessageAction(
                                               label="繁體中文", text="設定打字翻譯 " + "繁體中文")),
                                           QuickReplyButton(action=MessageAction(
                                               label="英文", text="設定打字翻譯 " + "英文")),
                                           QuickReplyButton(action=MessageAction(
                                               label="日文", text="設定打字翻譯 " + "日文")),
                                           QuickReplyButton(action=MessageAction(
                                               label="韓文", text="設定打字翻譯 " + "韓文")),
                                           QuickReplyButton(action=MessageAction(
                                               label="法文", text="設定打字翻譯 " + "法文")),
                                           QuickReplyButton(action=MessageAction(
                                               label="泰文", text="設定打字翻譯 " + "泰文")),
                                           QuickReplyButton(action=MessageAction(
                                               label="義大利文", text="設定打字翻譯 " + "義大利文")),
                                           QuickReplyButton(action=MessageAction(
                                               label="西班牙文", text="設定打字翻譯 " + "西班牙文")),
                                           QuickReplyButton(action=MessageAction(
                                               label="荷蘭文", text="設定打字翻譯 " + "荷蘭文")),
                                           QuickReplyButton(action=MessageAction(
                                               label="德文", text="設定打字翻譯 " + "德文")),
                                       ]))
        line_bot_api.reply_message(event.reply_token, flex_message)

    elif ("設定打字翻譯" in user_input):
        # Set translate language by user
        user_dict[user_id][user_translate_language_key] = lang_dict[user_input.split(" ")[
            1]]
        # Format response message
        audio_language = user_dict[user_id][user_audio_language_key]
        translate_language = user_dict[user_id][user_translate_language_key]
        response_text = f"""設定完畢！
我方語言：{reverse_lang_dict[audio_language]}（{audio_language}）
對方語言：{reverse_lang_dict[translate_language]}（{translate_language}）"""
        line_bot_api.reply_message(
            event.reply_token, TextSendMessage(text=response_text))

    elif (user_input == "/current-setting") or (user_input == "目前設定"):
        # Format response message
        audio_language = user_dict[user_id][user_audio_language_key]
        translate_language = user_dict[user_id][user_translate_language_key]
        response_text = f"""我方語言：{reverse_lang_dict[audio_language]}（{audio_language}）
對方語言：{reverse_lang_dict[translate_language]}（{translate_language}）"""
        line_bot_api.reply_message(
            event.reply_token, TextSendMessage(text=response_text))

    else:
        # Translate result from user input
        translated_text = chatgpt.translate(
            user_input, user_dict[user_id][user_translate_language_key])
        line_bot_api.reply_message(
            event.reply_token, TextSendMessage(text=translated_text))


@line_handler.add(MessageEvent, message=AudioMessage)
def handle_audio_message(event):
    user_id = event.source.user_id
    if not (user_exists(user_id)):
        init_user_lang(user_id)
    # Read voice message for whisper api input
    message_id = event.message.id
    user_audio_path = os.path.join(app.config.get(
        'AUDIO_BASE_PATH'), f'{message_id}.m4a')
    with open(user_audio_path, 'wb') as f:
        f.write(line_bot_api.get_message_content(message_id).content)
    whispered_text = chatgpt.whisper(user_audio_path)
    if (os.path.exists(user_audio_path)):
        os.remove(user_audio_path)
    # Translate result from whisper api output
    translated_text = chatgpt.translate(
        whispered_text, user_dict[user_id][user_audio_language_key])
    line_bot_api.reply_message(
        event.reply_token, TextSendMessage(text=translated_text))


def user_exists(user_id):
    return user_id in user_dict


def init_user_lang(user_id):
    user_dict[user_id] = {
        user_translate_language_key: 'Japanese',
        user_audio_language_key: 'Traditional Chinese'
    }


if __name__ == '__main__':
    app.run()
