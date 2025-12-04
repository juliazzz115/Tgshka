# Telegram Desktop Notifications

Обязательные уведомления из Telegram канала на рабочий стол. **Один раз настроил - работает всегда.**

## 🎯 Что это?

Получайте сообщения из вашего Telegram канала как **обязательные уведомления** на компьютере.
- ❌ Нельзя закрыть без подтверждения
- ✅ Работает автоматически в фоне
- 🔄 Проверка каждые 30 минут
- 💾 Не показывает одно сообщение дважды

## ⚡ Быстрая установка (2 минуты)

```bash
# 1. Скачать
git clone <repository-url>
cd Tgshka

# 2. Запустить установку
chmod +x install.sh
./install.sh
```

**Готово!** Система работает в фоне автоматически. Ничего больше делать не нужно.

## 📋 Что делает install.sh?

1. Устанавливает зависимости
2. Спрашивает Telegram API ID и Hash (один раз)
3. Помогает выбрать канал
4. Настраивает автозапуск (systemd/launchd)
5. Запускает в фоне

После установки **ничего не нужно запускать** - все работает само!

## 🔑 Получение Telegram API

Нужно один раз:
1. Откройте https://my.telegram.org
2. Войдите с номером телефона
3. "API development tools" → создайте приложение
4. Скопируйте **API ID** и **API Hash**

## 💡 Как работают уведомления

1. ⏰ Каждые 30 минут проверяет канал
2. 📨 Новое сообщение → появляется окно поверх всех окон
3. ❌ Нельзя закрыть крестиком!
4. ✅ Нужно нажать кнопку **ДВА РАЗА** (или Enter/Space)
5. 🔄 Следующее сообщение появится автоматически

## ⚙️ Управление

### Linux
```bash
# Проверить статус
systemctl --user status telegram-notifications

# Остановить
systemctl --user stop telegram-notifications

# Запустить
systemctl --user start telegram-notifications

# Логи
journalctl --user -u telegram-notifications -f
```

### macOS
```bash
# Остановить
launchctl unload ~/Library/LaunchAgents/com.telegram.notifications.plist

# Запустить
launchctl load ~/Library/LaunchAgents/com.telegram.notifications.plist

# Логи
tail -f ~/Library/Logs/telegram-notifications.log
```

## 🔧 Изменить интервал проверки

По умолчанию: **30 минут**

В файле `telegram_desktop_notifications.py` строка 263:
```python
await self.monitor.start_monitoring(check_interval=1800)
```

Примеры:
- **15 минут**: `check_interval=900`
- **1 час**: `check_interval=3600`

После изменения перезапустите сервис.

## ❓ Проблемы

**Ошибка установки зависимостей:**
```bash
pip3 install --upgrade pip
pip3 install -r requirements.txt
```

**Окно не появляется (Linux):**
```bash
sudo apt-get install python3-tk
```

**Сбросить авторизацию:**
```bash
rm channel_monitor.session telegram_config.json
./install.sh
```
