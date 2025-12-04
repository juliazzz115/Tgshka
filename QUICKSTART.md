# ⚡ Быстрый старт

## Все что нужно сделать:

### 1. Установить (2 минуты)
```bash
git clone <repo-url>
cd Tgshka
chmod +x install.sh
./install.sh
```

### 2. Ввести данные при запросе:
- **API ID** и **API Hash** с https://my.telegram.org
- **Код из Telegram** для авторизации
- **Номер канала** из списка

### 3. Готово!

Система работает в фоне. **Ничего больше не нужно делать.**

---

## Получить Telegram API (30 секунд)

1. https://my.telegram.org
2. Войти → "API development tools"
3. Создать приложение
4. Скопировать API ID и API Hash

---

## После установки

✅ Система запущена в фоне
✅ Автозапуск при загрузке настроен
✅ Проверка канала каждые 30 минут
✅ Уведомления появятся автоматически

**Ничего запускать не нужно!**

---

## Управление

### Linux
```bash
# Статус
systemctl --user status telegram-notifications

# Логи
journalctl --user -u telegram-notifications -f
```

### macOS
```bash
# Статус
launchctl list | grep telegram

# Логи
tail -f ~/Library/Logs/telegram-notifications.log
```

---

## Как выглядит уведомление

📢 Появляется окно поверх всех окон
❌ Нельзя закрыть без подтверждения
✅ Нажать кнопку 2 раза (или Enter 2 раза)
🔄 Готово!

---

Вот и все! Проще некуда.
