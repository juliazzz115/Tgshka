# Telegram Desktop Notifications

Система обязательных desktop уведомлений из Telegram канала.

## Описание

Это приложение позволяет получать обязательные уведомления на рабочем столе из вашего Telegram канала. Уведомления **нельзя закрыть без подтверждения прочтения**, что гарантирует, что вы не пропустите важные сообщения.

### Основные возможности

- **Мониторинг Telegram канала** - автоматическая проверка новых сообщений каждые 30 минут
- **Обязательные уведомления** - окно нельзя закрыть без подтверждения
- **Очередь уведомлений** - если пришло несколько сообщений, они будут показаны по очереди
- **Отслеживание прочитанных** - прочитанные сообщения не показываются повторно
- **База данных** - SQLite для хранения состояния сообщений
- **Двойное подтверждение** - требуется два нажатия кнопки для подтверждения

## Установка

### Требования

- Python 3.7+
- Linux/macOS/Windows
- Telegram API credentials (API ID и API Hash)

### Шаги установки

1. Клонируйте репозиторий:
```bash
git clone <repository-url>
cd Tgshka
```

2. Установите зависимости:
```bash
pip3 install -r requirements.txt
```

3. Получите Telegram API credentials:
   - Перейдите на https://my.telegram.org
   - Войдите с помощью номера телефона
   - Перейдите в "API development tools"
   - Создайте новое приложение
   - Скопируйте **API ID** и **API Hash**

## Использование

### Первый запуск

Запустите приложение:
```bash
python3 telegram_desktop_notifications.py
```

При первом запуске вам будет предложено:
1. Ввести API ID и API Hash
2. Авторизоваться в Telegram (будет отправлен код подтверждения)
3. Выбрать канал для мониторинга

### Повторный запуск

При повторных запусках приложение будет использовать сохраненную конфигурацию.

### Как работает уведомление

1. Когда приходит новое сообщение из канала, на рабочем столе появляется окно
2. Окно всегда находится поверх других окон
3. Нельзя закрыть окно крестиком
4. Чтобы подтвердить прочтение:
   - Нажмите кнопку "Я ПРОЧИТАЛ(А) ЭТО СООБЩЕНИЕ" **ДВА РАЗА**
   - Или нажмите Enter/Space **ДВА РАЗА**
5. После подтверждения окно закроется
6. Если есть еще сообщения в очереди, следующее появится автоматически

## Настройка

### Интервал проверки

По умолчанию приложение проверяет новые сообщения каждые **30 минут**.

Чтобы изменить интервал, откройте `telegram_desktop_notifications.py` и измените параметр в строке:

```python
await self.monitor.start_monitoring(check_interval=1800)  # 1800 секунд = 30 минут
```

Примеры:
- 15 минут: `check_interval=900`
- 1 час: `check_interval=3600`
- 5 минут: `check_interval=300`

### Файлы конфигурации

Приложение создает следующие файлы:

- `telegram_config.json` - сохраненные API credentials и ID канала
- `channel_monitor.session` - сессия Telegram (авторизация)
- `notifications.db` - база данных SQLite с сообщениями

**ВАЖНО:** Не удаляйте `channel_monitor.session` - это ваша авторизация в Telegram!

## Архитектура

Приложение состоит из трех модулей:

### 1. telegram_channel_monitor.py
- Подключение к Telegram API
- Мониторинг канала
- Проверка новых сообщений
- База данных SQLite

### 2. mandatory_notification.py
- GUI для уведомлений (tkinter)
- Очередь уведомлений
- Блокировка закрытия окна
- Двойное подтверждение

### 3. telegram_desktop_notifications.py
- Главный скрипт
- Связывает монитор и уведомления
- Первичная настройка

## Автозапуск

### Linux (systemd)

Создайте файл `/etc/systemd/system/telegram-notifications.service`:

```ini
[Unit]
Description=Telegram Desktop Notifications
After=network.target

[Service]
Type=simple
User=your-username
WorkingDirectory=/path/to/Tgshka
ExecStart=/usr/bin/python3 telegram_desktop_notifications.py
Restart=always

[Install]
WantedBy=multi-user.target
```

Запустите сервис:
```bash
sudo systemctl enable telegram-notifications
sudo systemctl start telegram-notifications
```

### macOS (launchd)

Создайте файл `~/Library/LaunchAgents/com.telegram.notifications.plist`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.telegram.notifications</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/bin/python3</string>
        <string>/path/to/Tgshka/telegram_desktop_notifications.py</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
</dict>
</plist>
```

Загрузите сервис:
```bash
launchctl load ~/Library/LaunchAgents/com.telegram.notifications.plist
```

### Windows (Task Scheduler)

1. Откройте Task Scheduler
2. Создайте новую задачу
3. Triggers: At log on
4. Actions: Start a program
   - Program: `python.exe`
   - Arguments: `C:\path\to\Tgshka\telegram_desktop_notifications.py`

## Возможные проблемы

### Ошибка "No module named 'telethon'"

Установите зависимости:
```bash
pip3 install -r requirements.txt
```

### Ошибка авторизации Telegram

Удалите файл сессии и повторите авторизацию:
```bash
rm channel_monitor.session
python3 telegram_desktop_notifications.py
```

### Окно уведомлений не появляется

Проверьте, что у вас установлен tkinter:
```bash
# Ubuntu/Debian
sudo apt-get install python3-tk

# macOS (встроен в Python)
# Windows (встроен в Python)
```

### Уведомление не поверх других окон

На некоторых системах Linux может потребоваться установить дополнительные права для окна.

## Безопасность

- **НЕ делитесь** файлом `telegram_config.json` - он содержит ваши API credentials
- **НЕ делитесь** файлом `channel_monitor.session` - это ваша авторизация
- Добавьте эти файлы в `.gitignore`:
  ```
  telegram_config.json
  *.session
  notifications.db
  ```

## Лицензия

MIT License

## Поддержка

Если у вас возникли вопросы или проблемы, создайте Issue в репозитории.

## Автор

Создано с помощью Claude AI
