# texts.py

# Ошибки прав
NO_EDITING_RIGHTS_USER = "🚫 У вас нет прав редактировать этого пользователя."
NO_VIEWING_RIGHTS = "🚫 У вас нет прав просматривать этого пользователя."
NO_EDITING_RIGHTS = "🚫 Нет прав для редактирования."

# Форматы и подтверждения
INCORRECT_FORMAT_FOR = "❌ Неверный формат значения для {param}"
PARAMETER_FOR_UPDATED = "✅ Параметр {param} успешно обновлён: {value}"
ACCESS_UPDATED = "✅ Доступ пользователя @{username} установлен до {date}"

# Пользовательские данные
NOT_FOUND_IN_THE_DATABASE = "❌ Пользователь {target_username} не найден."
COULDNT_GET_THE_DATA_FOR = "❌ Не удалось получить данные пользователя {target_username}."
AN_ERROR_OCCURRED_IN_RECEIVING_DATA = "❌ Произошла ошибка при получении информации."

# Сообщения для системы прав
RIGHTS_USER_NOT_FOUND = "❌ У вас нет доступа. Пользователь {username} не найден в базе данных."
RIGHTS_NO_ACCESS_TO_COMMAND = "🚫 У вас нет доступа к этой команде."
RIGHTS_SELF_ONLY_RESTRICTION = "🚫 Вы можете изменять данные только для себя."

# Сообщения аутентификации
AUTH_NO_USERNAME = "❌ Для использования бота требуется Telegram username"
AUTH_NOT_REGISTERED = "🔒 Доступ запрещён. Ваш username не зарегистрирован"
AUTH_ACCESS_EXPIRED = "⛔️ Ваш доступ истёк. Обратитесь к администратору для продления."

# Специальные значения
NO_ACCESS = "нет доступа"
THERE_IS_NO_SET_PERIOD = "период не установлен"

# Даты
DAYS_FROM = "{dates_count} дней (с {start_date} по {end_date})"

# Информация о пользователе
INFO_PARAMS_SELF = "ℹ️ Информация параметров"
INFO_PARAMS_OTHER = "ℹ️ Информация параметров пользователя {display_name}"
RIGHTS_LINE = "Права: {rights}\n"
USER_INFO = """{header}

Параметры пользователя:
Доступ до: {access_until}
{rights_line}
Параметры запросы:
Даты: {dates_text}
Максимум дней оборота: {turnover_days_max}
Минимальная выручка: {revenue_min}
Категория: {category}
Порог падения: {drop_percent}%
"""

# Подсказки для редактирования
EDIT_PROMPT = "✏️ Введите новое значение для {param}:"
CHOOSE_DAYS = "📅 Отчет за послдение:"
CHOOSE_RIGHTS = "🛠 Выберите права:"
ACCESS_SETTINGS = "🔑 Настройка доступа:"
ACCESS_FOREVER = "Бессрочно"
REMOVE_ACCESS = "Удалить доступ"

# Системные сообщения
INCORRECT_DATA = "❌ Некорректные данные."
INCORRECT_FORMAT = "❌ Некорректный формат данных."
UNKNOWN_COMMAND = "❌ Неизвестная команда."
GENERIC_ERROR = "❌ Произошла ошибка."

# Названия параметров
RIGHTS = "🛠 Уровень прав"
TURNOVER_DAYS_MAX = "📈 Оборот до дн."
REVENUE_MIN = "💰Мин.выручка"
CATEGORY = "🏷 Категория"
DATES = "📅 Даты запроса"
PERCENT_TEXT = "📉 % падения остатков"
ACCESS_UNTIL = "🔑 Доступ до"

# Сообщения для отчётов
REPORT_GENERATION_IN_PROGRESS = "⏳ Формируем отчёт..."
REPORT_GENERATION_FAILED = "❌ Не удалось сформировать отчёт"
REPORT_LIMIT_EXCEEDED = "Превышены лимиты, товаров в запросе - {category_count}.\nИзмени параметры запроса либо сузь категорию"

# Новые переменные для new_user.py
NEWUSER_MISSING_USERNAME = "❌ Укажите имя пользователя: /newuser username"
NEWUSER_ALREADY_EXISTS = "⚠️ Пользователь {target_username} уже существует."
NEWUSER_INIT_ERROR = "❌ Ошибка при инициации создания пользователя."
NEWUSER_CREATION_ERROR = "❌ Ошибка при создании пользователя."
NEWUSER_CREATION_HEADER = "🆕 Создание пользователя {username}\nВыберите срок доступа:"
NEWUSER_CREATED = "✅ Пользователь {username} создан.\n🔑 Доступ до: {access_until}"

# Опции доступа для создания пользователя
ACCESS_OPTION_1_DAY = "+1 день"
ACCESS_OPTION_14_DAYS = "+14 дней"
ACCESS_OPTION_30_DAYS = "+30 дней"
ACCESS_OPTION_90_DAYS = "+90 дней"