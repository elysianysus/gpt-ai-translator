import os

from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, AudioMessage, TextSendMessage, AudioSendMessage, QuickReply, QuickReplyButton, MessageAction
from api.ai.chatgpt import ChatGPT
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

line_bot_api = LineBotApi(os.getenv("LINE_CHANNEL_ACCESS_TOKEN"))
line_handler = WebhookHandler(os.getenv("LINE_CHANNEL_SECRET"))

chatgpt = ChatGPT()

# region Language related

translate_language = "Japanese"
audio_language = "Traditional Chinese"

lan_dic = {
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
reverse_lan_dict = {value: key for key, value in lan_dic.items()}

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
    global translate_language, audio_language
    user_input = event.message.text
    if (user_input == "設定"):
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
        audio_language = lan_dic[user_input.split(" ")[1]]
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
        translate_language = lan_dic[user_input.split(" ")[1]]
        response = f"""設定完畢！
我方語言：{reverse_lan_dict[audio_language]}（{audio_language}）
對方語言：{reverse_lan_dict[translate_language]}（{translate_language}）"""
        line_bot_api.reply_message(
            event.reply_token, TextSendMessage(text=response))

    elif (user_input == "目前設定"):
        response = f"""我方語言：{reverse_lan_dict[audio_language]}（{audio_language}）
對方語言：{reverse_lan_dict[translate_language]}（{translate_language}）"""
        line_bot_api.reply_message(
            event.reply_token, TextSendMessage(text=response))

    else:
        response = chatgpt.translate(user_input, translate_language)
        line_bot_api.reply_message(
            event.reply_token, TextSendMessage(text=response))


@line_handler.add(MessageEvent, message=AudioMessage)
def handle_audio_message(event):
    global translate_language, audio_language
    message_id = event.message.id
    message_content = line_bot_api.get_message_content(message_id)
    user_audio_path = f'/tmp/{message_id}.m4a'
    with open(user_audio_path, 'wb') as f:
        f.write(message_content.content)
    whisper_text = chatgpt.whisper(user_audio_path)
    if (os.path.exists(user_audio_path)):
        os.remove(user_audio_path)
    response_text = chatgpt.translate(whisper_text, audio_language)
    line_bot_api.reply_message(
        event.reply_token, TextSendMessage(text=response_text))


if __name__ == '__main__':
    app.run()
