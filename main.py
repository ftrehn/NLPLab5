import telebot
import requests

API_TOKEN = '8239287995:AAEmSCWpXwyC2XhLuI4dnyAq74rU_JbXdOE'

bot = telebot.TeleBot(API_TOKEN)
user_contexts = {}

SYSTEM_PROMPT = {
    "role": "system",
    "content": "Ты самый умный ассистент в мире. Отвечай на русском языке."
}

@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.chat.id
    user_contexts[user_id] = [SYSTEM_PROMPT]

    welcome_text = (
        "Привет! Я ваш Telegram бот с поддержкой контекста.\n"
        "Доступные команды:\n"
        "/start - Перезапуск\n"
        "/model - Узнать название модели\n"
        "/clear - Очистить историю диалога (забыть контекст)"
    )
    bot.reply_to(message, welcome_text)


@bot.message_handler(commands=['model'])
def send_model_name(message):
    try:
        response = requests.get('http://localhost:1234/v1/models')
        if response.status_code == 200:
            model_info = response.json()
            model_name = model_info['data'][0]['id']
            bot.reply_to(message, f" Используемая модель: {model_name}")
        else:
            bot.reply_to(message, 'Не удалось получить информацию о модели.')
    except Exception as e:
        bot.reply_to(message, f'Ошибка соединения с LM Studio: {e}')


@bot.message_handler(commands=['clear'])
def clear_context(message):
    user_id = message.chat.id
    user_contexts[user_id] = [SYSTEM_PROMPT]
    bot.reply_to(message, " История диалога очищена.")


@bot.message_handler(func=lambda message: True)
def handle_message(message):
    user_id = message.chat.id
    user_query = message.text

    if user_id not in user_contexts:
        user_contexts[user_id] = [SYSTEM_PROMPT]

    user_contexts[user_id].append({
        "role": "user",
        "content": user_query
    })

    request = {
        "messages": user_contexts[user_id],
        "temperature": 0.7,
        "max_tokens": 500,
        "stream": False
    }

    try:
        response = requests.post(
            'http://localhost:1234/v1/chat/completions',
            json=request
        )

        if response.status_code == 200:
            response_data = response.json()
            assistant_message = response_data['choices'][0]['message']['content']

            bot.reply_to(message, assistant_message)

            user_contexts[user_id].append({
                "role": "assistant",
                "content": assistant_message
            })
        else:
            bot.reply_to(message, f'Ошибка API LM Studio: {response.status_code}')

    except Exception as e:
        bot.reply_to(message, f'Произошла ошибка: {e}')


# Запуск бота
if __name__ == '__main__':
    bot.polling(none_stop=True)
