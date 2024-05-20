#  BOT TELEGRAM
import os
import BingX as bx
import telebot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton


TELEGRAM_TOKEN = '6251375701:AAEOs-ofzo6KK5wZa4SujL84uJPdYQdGNkM'
CARPETA = 'datos'
coins = {}

bot = telebot.TeleBot(TELEGRAM_TOKEN)
    

@bot.message_handler(commands=['start'])
def start(message):
    resetCoins()
    markup = InlineKeyboardMarkup()

    markup.add(InlineKeyboardButton("Añadir activo", callback_data='addCoins'))
    if  getCoins( message.chat.id ) is None:
        print(os.getcwd())
        open(f'{os.getcwd()}/{CARPETA}/{message.chat.id}.txt', 'w' )
        bot.send_message(message.chat.id, "Hola trader !BIENVENIDO!\nPuedo obtener el precio de los activos en BingX."
                      +" Para obtener el precio de un activo primero debes agregarlo a tu lista de seguimiento con el comando:"
                      +"\n/addCoins.", reply_markup=markup)
    else:
        markup.add(InlineKeyboardButton("Obtener precio", callback_data='price'))
        bot.send_message(message.chat.id, "Hola de nuevo! Si tienes dudas utiliza el comando:\n/help", reply_markup=markup)


@bot.callback_query_handler(func=lambda call: True)
def handle_command(call):
    # Obtén el comando seleccionado a través de call.data
    command = call.data
    # Realiza las acciones correspondientes al comando seleccionado
    if command == 'addCoins':
        # Acciones para el comando 1
        addCoins( call.message)
    elif command == 'addCoin':
        # Acciones para el comando 2
        addCoin( call.message)
    elif command == 'price':
        # Acciones para el comando 3
        price( call.message)
    elif command == 'update':
        try:
            msg = call.message
            symbol = extractSymbol(msg.text)
            markup = InlineKeyboardMarkup()
            markup.add(InlineKeyboardButton("Actualizar", callback_data='update'))
            bot.edit_message_text(chat_id=msg.chat.id, message_id=msg.message_id, text=f"{symbol}: {bx.obtener_precio_crypto(symbol)}", reply_markup=markup)
        except telebot.apihelper.ApiTelegramException:
            pass

    bot.answer_callback_query(call.id, "Comando ejecutado")
    
@bot.message_handler(commands=['addCoins'])
def addCoins( message):
    bot.send_message(message.chat.id, "Escriba el par que desea agregar.\n\n   Formato: 'BTC-USDT'")
    bot.register_next_step_handler( message, addCoin)
    

def addCoin( message):
    symbol = extractSymbol( message.text)
    print(symbol)
    if bx.obtener_precio_crypto( symbol) == None:
        bot.send_message(message.chat.id, "El par no existe, por favor revise el formato especificado")
        return
    coins = getCoins(message.chat.id) # obtiene los coins del usuario
    if coins is not None:
        if symbol in coins:
            bot.send_message(message.chat.id, "El par ya esta agregado") # si el par ya esta agregado
            return
    with open(f'{os.getcwd()}/{CARPETA}/{message.chat.id}.txt', 'a' ) as archivo:
        archivo.write( symbol + '\n' )
        archivo.close()
        resetCoins()
    bot.reply_to(message, f"El par {symbol} ha sido agregado")
     


@bot.message_handler(commands=['price'])
def price( message):
    coins = getCoins(message.chat.id) # obtiene los coins del usuario
    if  coins == None:
        bot.send_message(message.chat.id, "No hay monedas agregadas, agregue algunas para empezar")
        addCoins( message)
    else:
        board = ReplyKeyboardMarkup(row_width=2, resize_keyboard=True, one_time_keyboard=True)
        for coin in coins:
            board.add(
                KeyboardButton(coin)
            )
        bot.send_message(message.chat.id, "Seleccione el par:", reply_markup=board)
        bot.register_next_step_handler( message, getPrice)


@bot.message_handler(content_types=['text'])
def getPrice( message):
    markup = InlineKeyboardMarkup()
    if coins is not None and message.text in coins:
        markup.add(InlineKeyboardButton("Actualizar", callback_data='update'))
        price = bx.obtener_precio_crypto( message.text)
        bot.send_message(message.chat.id, f"{message.text}: {price}", reply_markup=markup)
    else:
        markup.add(InlineKeyboardButton("Añadir activo", callback_data='addCoin'))
        bot.send_message(message.chat.id, f"Opss! No puedo  encontrar el par {message.text}."
                         +" Asegurate de haberlo agregado a tu lista de seguimiento o actualiza tu lista con el comando:\n/price",
                         reply_markup=markup)


def extractSymbol(message:str):
    if message.__contains__('-USDT'): # si el mensaje contiene USDT
        msg = message.split('-USDT')[0] # devuelve el simbolo
        symbol = f"{msg.split(' ')[-1]}-USDT"
        return symbol


def getCoins( chat_id):
    global coins
    if coins is not None and coins.__len__() > 0:
        return coins
    try:
        with open( f'{os.getcwd()}/{CARPETA}/{chat_id}.txt', 'r' ) as archivo:
            con = ''
            while True:
                contenido = archivo.readline() 
                if contenido:
                    con += contenido
                else:
                    archivo.close()
                    if con.__len__() == 0:
                        return None
                    coins = con.split( '\n' )
                    return coins
    except FileNotFoundError:
        return None

def resetCoins():
    global coins
    coins = None


if  __name__ == '__main__':
    print(os.getcwd())
    if not os.path.exists(os.getcwd()+'/'+CARPETA):
        os.mkdir(CARPETA) # crea la carpeta si no existe
        print("Se creó la carpeta")
    bot.infinity_polling()






# with open( f'{carpeta}/dato.txt', 'a' ) as archivo:
#     for  i in range(10):
#         archivo.write( f'Hola mundo {i}\n' )
  
