import logging
import datetime
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import Application, CommandHandler, ContextTypes, ConversationHandler, MessageHandler, filters

# Константы для состояний
MENU, ASSETS, PASSIVES, HOUSES, CARS, MY_ITEMS = range(6)

# Словарь для хранения игр пользователей
games = {}

class Game:
    def __init__(self):
        self.balance = 1000  # Начальный баланс пользователя
        self.earn_times = []
        self.assets = {
            'Ларёк': {'price': 3000, 'income': 50},
            'Супермаркет': {'price': 10000, 'income': 200},
            'Строительная фирма': {'price': 17000, 'income': 1000}
        }
        self.passives = {
            'Золото': 500, 'Серебро': 200, 'Медь': 50,
            'Дешевая квартира': 40000, 'Средняя квартира': 90000, 'Дорогая квартира': 140000,
            'Дешевый дом': 50000, 'Средний дом': 110000, 'Дорогой дом': 190000, 'Вилла': 250000,
            'Акции': 500, 'Криптовалюта': 500
        }
        self.houses = {
            'Дешевая квартира': 40000, 'Средняя квартира': 90000, 'Дорогая квартира': 140000,
            'Дешевый дом': 50000, 'Средний дом': 110000, 'Дорогой дом': 190000, 'Вилла': 250000
        }
        self.cars = {'Дешевая машина': 15000, 'Средняя машина': 45000, 'Дорогая машина': 100000}
        self.user_assets = []
        self.user_passives = []
        self.user_houses = []
        self.user_cars = []
        self.current_context = None
        self.last_income_time = datetime.datetime.now()

    def show_balance(self, user_name):
        self.update_income()  # обновляем баланс перед его отображением
        return f"{user_name}, ваш баланс: {self.balance} долларов"

    def earn_money(self, user_name):
        now = datetime.datetime.now()
        self.earn_times = [time for time in self.earn_times if now - time < datetime.timedelta(hours=2)]
        if len(self.earn_times) < 10:
            self.balance += 500
            self.earn_times.append(now)
            return f"{user_name}, вы заработали 500 долларов."
        else:
            return f"{user_name}, вы можете зарабатывать только 10 раз в 2 часа."

    def show_passives(self, user_name):
        response = f"{user_name}, список пассивов:\n"
        for passive, price in self.passives.items():
            response += f"{passive}: {price} долларов\n"
        self.current_context = 'buy_passive'
        return response

    def buy_passive(self, passive_name, user_name):
        passive_name_lower = passive_name.lower()
        matched_passive = next((name for name in self.passives if name.lower() == passive_name_lower), None)
        
        if matched_passive and self.balance >= self.passives[matched_passive]:
            self.balance -= self.passives[matched_passive]
            self.user_passives.append(matched_passive)
            return f"{user_name}, вы купили {matched_passive}."
        else:
            return f"{user_name}, недостаточно средств или неверное имя пассива."

    def show_assets(self, user_name):
        response = f"{user_name}, список активов:\n"
        for asset, details in self.assets.items():
            response += f"{asset}: {details['price']} долларов, доход: {details['income']} долларов в час\n"
        self.current_context = 'buy_asset'
        return response

    def buy_asset(self, asset_name, user_name):
        asset_name_lower = asset_name.lower()
        matched_asset = next((name for name in self.assets if name.lower() == asset_name_lower), None)
        
        if matched_asset and self.balance >= self.assets[matched_asset]['price']:
            self.balance -= self.assets[matched_asset]['price']
            self.user_assets.append(matched_asset)
            return f"{user_name}, вы купили {matched_asset}."
        else:
            return f"{user_name}, недостаточно средств или неверное имя актива."

    def sell_item(self, item_name, user_name):
        if item_name in self.user_assets:
            self.balance += int(self.assets[item_name]['price'] * 0.85)
            self.user_assets.remove(item_name)
            return f"{user_name}, вы продали {item_name}."
        elif item_name in self.user_passives:
            self.balance += int(self.passives[item_name] * 0.85)
            self.user_passives.remove(item_name)
            return f"{user_name}, вы продали {item_name}."
        else:
            return f"{user_name}, у вас нет такого актива или пассива."

    def show_houses(self, user_name):
        response = f"{user_name}, список домов:\n"
        for house, price in self.houses.items():
            response += f"{house}: {price} долларов\n"
        self.current_context = 'buy_house'
        return response

    def buy_house(self, house_name, user_name):
        house_name_lower = house_name.lower()
        matched_house = next((name for name in self.houses if name.lower() == house_name_lower), None)
        
        if matched_house and self.balance >= self.houses[matched_house]:
            self.balance -= self.houses[matched_house]
            self.user_houses.append(matched_house)
            return f"{user_name}, вы купили {matched_house}."
        else:
            return f"{user_name}, недостаточно средств или неверное имя дома."

    def create_company(self, company_name, user_name):
        return f"{user_name}, вы создали компанию {company_name}."

    def show_cars(self, user_name):
        response = f"{user_name}, список машин:\n"
        for car, price in self.cars.items():
            response += f"{car}: {price} долларов\n"
        self.current_context = 'buy_car'
        return response

    def buy_car(self, car_name, user_name):
        car_name_lower = car_name.lower()
        matched_car = next((name for name in self.cars if name.lower() == car_name_lower), None)
        
        if matched_car and self.balance >= self.cars[matched_car]:
            self.balance -= self.cars[matched_car]
            self.user_cars.append(matched_car)
            return f"{user_name}, вы купили {matched_car}."
        else:
            return f"{user_name}, недостаточно средств или неверное имя машины."

    def show_my_items(self, user_name):
        response = f"{user_name}, ваши покупки:\n"
        response += "Пассивы:\n" + "\n".join(self.user_passives) + "\n"
        response += "Активы:\n" + "\n".join(self.user_assets) + "\n"
        response += "Дома:\n" + "\n".join(self.user_houses) + "\n"
        response += "Машины:\n" + "\n".join(self.user_cars) + "\n"
        return response

    def update_income(self):
        now = datetime.datetime.now()
        hours_passed = (now - self.last_income_time).total_seconds() // 3600
        if hours_passed >= 1:
            total_income = sum(self.assets[asset]['income'] for asset in self.user_assets) * hours_passed
            self.balance += total_income
            self.last_income_time = now

    def execute_command(self, command, user_name):
        command = command.lower()  # Приводим команду к нижнему регистру
        response = ""

        if self.current_context:
            if self.current_context == 'buy_passive':
                response = self.buy_passive(command, user_name)
            elif self.current_context == 'buy_asset':
                response = self.buy_asset(command, user_name)
            elif self.current_context == 'buy_house':
                response = self.buy_house(command, user_name)
            elif self.current_context == 'buy_car':
                response = self.buy_car(command, user_name)
            self.current_context = None
        else:
            if command in ['б', 'баланс', '/balance']:
                response = self.show_balance(user_name)
            elif command in ['заработать', '/earn']:
                response = self.earn_money(user_name)
            elif command in ['пассивы', '/buy_passives']:
                response = self.show_passives(user_name)
            elif command in ['активы', '/buy_assets']:
                response = self.show_assets(user_name)
            elif command in ['дома', '/buy_houses']:
                response = self.show_houses(user_name)
            elif command in ['машины', '/buy_cars']:
                response = self.show_cars(user_name)
            elif command in ['мои покупки', '/my_items']:
                response = self.show_my_items(user_name)
            else:
                response = f"{user_name}, неизвестная команда."

        return response

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    chat_id = update.message.chat.id
    if chat_id not in games:
        games[chat_id] = Game()

    reply_keyboard = [['Баланс', 'Заработать'], ['Активы', 'Пассивы'], ['Дома', 'Машины'], ['Мои покупки']]

    await update.message.reply_text(
        "Привет! Я ваш игровой финансовый бот. Команды:\n"
        "/start - старт\n"
        "/balance - Ваш баланс\n"
        "/earn - Заработать\n"
        "/my_items - Мои покупки\n"
        "/buy_assets - Купить активы\n"
        "/buy_passives - Купить пассивы\n"
        "/buy_houses - Купить дома\n"
        "/buy_cars - Купить машину",
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
    )
    return MENU

async def show_balance(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    chat_id = update.message.chat.id
    user_name = update.message.from_user.first_name
    result = games[chat_id].execute_command('баланс', user_name)
    await update.message.reply_text(result)
    return MENU

async def show_assets(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    chat_id = update.message.chat.id
    user_name = update.message.from_user.first_name
    result = games[chat_id].execute_command('активы', user_name)
    await update.message.reply_text(result)
    return ASSETS

async def show_passives(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    chat_id = update.message.chat.id
    user_name = update.message.from_user.first_name
    result = games[chat_id].execute_command('пассивы', user_name)
    await update.message.reply_text(result)
    return PASSIVES

async def earn_money(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    chat_id = update.message.chat.id
    user_name = update.message.from_user.first_name
    result = games[chat_id].execute_command('заработать', user_name)
    await update.message.reply_text(result)
    return MENU

async def show_houses(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    chat_id = update.message.chat.id
    user_name = update.message.from_user.first_name
    result = games[chat_id].execute_command('дома', user_name)
    await update.message.reply_text(result)
    return HOUSES

async def show_cars(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    chat_id = update.message.chat.id
    user_name = update.message.from_user.first_name
    result = games[chat_id].execute_command('машины', user_name)
    await update.message.reply_text(result)
    return CARS

def show_my_items(self, user_name):
        response = f"{user_name}, ваши покупки:\n"

        # Пассивы
        if self.user_passives:
            passive_counts = {passive: self.user_passives.count(passive) for passive in set(self.user_passives)}
            response += "Пассивы:\n"
            for passive, count in passive_counts.items():
                response += f"{passive} - {count}X\n"

        # Активы
        if self.user_assets:
            asset_counts = {asset: self.user_assets.count(asset) for asset in set(self.user_assets)}
            response += "Активы:\n"
            for asset, count in asset_counts.items():
                response += f"{asset} - {count}X\n"

        # Дома
        if self.user_houses:
            house_counts = {house: self.user_houses.count(house) for house in set(self.user_houses)}
            response += "Дома:\n"
            for house, count in house_counts.items():
                response += f"{house} - {count}X\n"

        # Машины
        if self.user_cars:
            car_counts = {car: self.user_cars.count(car) for car in set(self.user_cars)}
            response += "Машины:\n"
            for car, count in car_counts.items():
                response += f"{car} - {count}X\n"

        return response

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    chat_id = update.message.chat.id
    user_name = update.message.from_user.first_name
    user_text = update.message.text.lower()

    if chat_id not in games:
        games[chat_id] = Game()

    result = games[chat_id].execute_command(user_text, user_name)
    await update.message.reply_text(result)
    return MENU

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text(
        "До свидания! Если захотите поиграть еще, просто напишите /start.",
        reply_markup=ReplyKeyboardRemove()
    )
    return ConversationHandler.END

def main() -> None:
    application = Application.builder().token("7419713039:AAGXpz0N-OnQL5pGmMCu4bsglBhQx3xpg8A").build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            MENU: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)
            ],
            ASSETS: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)],
            PASSIVES: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)],
            HOUSES: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)],
            CARS: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)],
            MY_ITEMS: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)],
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )

    application.add_handler(conv_handler)

    # Добавляем обработчики команд
    application.add_handler(CommandHandler('balance', show_balance))
    application.add_handler(CommandHandler('earn', earn_money))
    application.add_handler(CommandHandler('buy_passives', show_passives))
    application.add_handler(CommandHandler('buy_assets', show_assets))
    application.add_handler(CommandHandler('buy_houses', show_houses))
    application.add_handler(CommandHandler('buy_cars', show_cars))
    application.add_handler(CommandHandler('my_items', show_my_items))

    application.run_polling()

if __name__ == '__main__':
    main()
