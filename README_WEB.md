# 🌐 Telegram Swiper - Веб-версия

**Полнофункциональное веб-приложение с Tinder-style свайпами!**

## 🎯 Что это?

Веб-версия Telegram Message Swiper - работает в любом браузере, на любом устройстве!

```
                Desktop                 Mobile
┌─────────────────────────────┐  ┌──────────────────┐
│  Drag & Drop карточки       │  │  Touch свайпы    │
│  Keyboard shortcuts         │  │  Как в Tinder    │
│  ← → Space                  │  │  👆 💨          │
└─────────────────────────────┘  └──────────────────┘
                 ↓                        ↓
            Flask Backend
         (Python + Telethon)
                 ↓
          ✅ Работает 24/7
```

## ⚡ Быстрый старт (3 минуты)

```bash
# 1. Установка
cd telegram_swiper_web
pip3 install -r requirements.txt

# 2. Запуск
cd backend
python3 app.py

# 3. Открыть
# http://localhost:5000
```

**Готово!** 🚀

## ✨ Возможности

### Полный функционал v3:
- ✅ Отслеживает каждое сообщение отдельно
- ✅ Контекст диалогов (последние сообщения)
- ✅ Показывает количество непрочитанных
- ✅ Без дублей (умная БД)
- ✅ Автосканирование каждый час
- ✅ Статистика в реальном времени

### + Веб-фишки:
- 🌍 Работает на любом устройстве
- 📱 Touch свайпы на мобильных
- ⌨️ Keyboard shortcuts на desktop
- 🎨 Красивый адаптивный дизайн
- 🔄 Real-time обновления
- 🚀 Можно развернуть на сервере

## 📱 На iPhone/iPad

### Вариант 1: Через локальную сеть

1. Узнайте IP вашего Mac:
   ```bash
   ifconfig | grep "inet " | grep -v 127.0.0.1
   ```

2. Откройте в Safari на iPhone:
   ```
   http://192.168.1.XXX:5000
   ```

3. Добавьте на главный экран → работает как приложение!

### Вариант 2: Через интернет (Railway)

1. Разверните на https://railway.app (бесплатно)
2. Получите постоянный URL
3. Открывайте откуда угодно!

## 🌍 Деплой (работа 24/7)

### Railway.app (Рекомендую!)

**Бесплатно:**
- 500 часов/месяц (17+ дней)
- Автоматический деплой
- HTTPS из коробки

**Как:**
1. Создайте аккаунт: https://railway.app
2. New Project → Deploy from GitHub
3. Готово! Получаете URL типа: `https://your-app.railway.app`

### Render.com

**Бесплатно:**
- Unlimited hours (но засыпает после 15 мин простоя)

**Как:**
1. https://render.com → New Web Service
2. Connect GitHub
3. Build: `pip install -r requirements.txt`
4. Start: `cd backend && python app.py`
5. Deploy!

## 🎮 Управление

### Desktop:
```
←     = Пометить непрочитанным (вернется при новом сканировании)
→     = Обработано (убрать навсегда)
Space = Обработано (быстро)
Мышь  = Drag & Drop карточки
```

### Mobile:
```
👈 Свайп влево  = Пометить непрочитанным
👉 Свайп вправо = Обработано
```

## 📂 Структура

```
telegram_swiper_web/
├── backend/
│   ├── app.py                    # Flask API + WebSocket
│   └── telegram_loader_web.py    # Telegram интеграция
│
├── templates/
│   └── index.html                # UI (адаптивный!)
│
├── static/
│   └── app.js                    # Логика + свайпы
│
├── requirements.txt              # Python зависимости
└── README.md                     # Документация
```

## 🔧 API Endpoints

```
GET  /api/status              # Статус подключения
GET  /api/config              # Настройки
POST /api/config              # Сохранить настройки
POST /api/connect             # Подключиться к Telegram
GET  /api/dialogs?hours=24    # Загрузить диалоги
POST /api/process             # Обработать свайп
GET  /api/stats               # Статистика
POST /api/auto_scan           # Вкл/выкл автосканирование
POST /api/clear_history       # Очистить историю
```

## 💾 База данных

**SQLite (по умолчанию):**
- `telegram_messages_web.db` - сообщения Telegram
- `web_app.db` - данные приложения

**PostgreSQL (для продакшена):**
Легко мигрировать - замените SQLite на Postgres в коде.

## 🎨 Кастомизация

### Цвета:

В `templates/index.html`:
```css
/* Градиент фона */
background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);

/* Кнопки */
.btn-left { background: #ff9800; }  /* Оранжевая */
.btn-right { background: #4caf50; } /* Зеленая */
```

### Интервал сканирования:

В `backend/app.py`:
```python
for _ in range(3600):  # 3600 = 1 час
    # Измените на 1800 для 30 минут
```

## 📊 Сравнение версий

| Функция | Desktop v3 | Web |
|---------|------------|-----|
| Умная проверка каждого сообщения | ✅ | ✅ |
| Контекст диалогов | ✅ | ✅ |
| Автосканирование | ✅ | ✅ |
| Работает на любом устройстве | ❌ | ✅ |
| Touch свайпы | ❌ | ✅ |
| Работа 24/7 (если на сервере) | ❌ | ✅ |
| Не нужен Python | ❌ | ✅ |
| Drag & Drop | Частично | ✅ |

## 🐛 Troubleshooting

### cryptg ошибка (GLIBC_2.26)

```bash
pip3 uninstall cryptg
pip3 install -r requirements.txt
# Приложение будет работать без cryptg!
```

### Port 5000 занят

```bash
# macOS - AirPlay использует порт 5000
# System Settings → General → AirDrop & Handoff → 
# Выключите "AirPlay Receiver"

# Или измените порт в app.py:
socketio.run(app, port=8080)
```

### Не могу подключиться к Telegram

1. Проверьте API ID/Hash на https://my.telegram.org
2. Удалите `web_session.session`
3. Перезапустите сервер

## 🔐 Безопасность

**Для локального использования:**
- ✅ Безопасно (работает только в вашей сети)

**Для деплоя на сервер:**
- 🔒 Добавьте аутентификацию (login/password)
- 🔒 Используйте HTTPS
- 🔒 Не коммитьте `.session` файлы

## 🚀 Roadmap

- [ ] Аутентификация (логин/пароль)
- [ ] Multi-user support
- [ ] Push уведомления
- [ ] Темная тема
- [ ] Экспорт в CSV/Excel
- [ ] Интеграция с CRM
- [ ] Telegram Bot для уведомлений

## 📖 Документация

- [WEB_QUICKSTART.md](WEB_QUICKSTART.md) - Быстрый старт
- [README.md](telegram_swiper_web/README.md) - Полная документация
- [VERSION_COMPARISON.md](VERSION_COMPARISON.md) - Сравнение версий

## 💬 Поддержка

Вопросы? Проблемы?
1. Проверьте Troubleshooting выше
2. Смотрите полную документацию
3. Создайте Issue

---

## 🎉 Готово!

```bash
cd telegram_swiper_web/backend
python3 app.py

# Откройте: http://localhost:5000
```

**Работает!** Начинайте свайпать! 👆💨

---

Сделано с ❤️ для эффективной работы с клиентами
