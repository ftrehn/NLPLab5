import telebot
import requests
import jsons
from Class_ModelResponse import ModelResponse

# Замените 'YOUR_BOT_TOKEN' на ваш токен от BotFather
API_TOKEN = '8239287995:AAEmSCWpXwyC2XhLuI4dnyAq74rU_JbXdOE'
bot = telebot.TeleBot(API_TOKEN)
user_contexts = {}

# Команды
@bot.message_handler(commands=['start'])
def send_welcome(message):
    welcome_text = (
        "Привет! Я ваш Telegram бот.\n"
        "Доступные команды:\n"
        "/start - вывод всех доступных команд\n"
        "/model - выводит название используемой языковой модели\n"
        "/clear - очистить контекст модели\n"
        "Отправьте любое сообщение, и я отвечу с помощью LLM модели."
    )
    bot.reply_to(message, welcome_text)


@bot.message_handler(commands=['model'])
def send_model_name(message):
    # Отправляем запрос к LM Studio для получения информации о модели
    response = requests.get('http://localhost:1234/v1/models')

    if response.status_code == 200:
        model_info = response.json()
        model_name = model_info['data'][0]['id']
        bot.reply_to(message, f"Используемая модель: {model_name}")
    else:
        bot.reply_to(message, 'Не удалось получить информацию о модели.')


@bot.message_handler(func=lambda message: True)
def handle_message(message):
    user_id = message.chat.id
    user_query = message.text

    if user_id not in user_contexts:
        user_contexts[user_id] = [
            {"role": "system", "content": "Ты самый умный в мире ассистент."}
        ]

    user_contexts[user_id].append({
        "role": "user",
        "content": user_query
    })

    request = {
        "messages": user_contexts[user_id],
        "temperature": 0.7,
        "max_tokens": -1,
        "stream": False
    }

    try:
        response = requests.post(
            'http://localhost:1234/v1/chat/completions',
            json=request
        )

        if response.status_code == 200:
            model_response = jsons.loads(response.text, ModelResponse)
            assistant_message = model_response.choices[0].message.content

            bot.reply_to(message, assistant_message)

            user_contexts[user_id].append({
                "role": "assistant",
                "content": assistant_message
            })
        else:
            bot.reply_to(message, 'Ошибка API LM Studio')
    except Exception as e:
        bot.reply_to(message, f'Произошла ошибка: {e}')


@bot.message_handler(commands=['clear'])
def clear_context(message):
    user_id = message.chat.id
    user_contexts[user_id] = [] # Очистка списка
    bot.reply_to(message, "История диалога очищена.")

# Запуск бота
if __name__ == '__main__':
    bot.polling(none_stop=True)