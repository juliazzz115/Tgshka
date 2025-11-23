# 🌐 Telegram Swiper - Веб-версия v3

**Полнофункциональное веб-приложение с Tinder-style свайпами!**

## 🚀 Быстрый старт

### 1. Установка зависимостей

```bash
pip3 install -r requirements.txt
```

### 2. Запуск сервера

```bash
cd backend
python3 app.py
```

### 3. Открыть в браузере

Откройте: **http://localhost:5000**

На мобильном устройстве в локальной сети: **http://\<ваш-ip\>:5000**

## ✨ Возможности

### Полный функционал v3:
- ✅ Отслеживает каждое сообщение отдельно
- ✅ Контекст диалогов (последние сообщения)
- ✅ Показывает количество непрочитанных
- ✅ Без дублей (умная БД)
- ✅ Автосканирование каждый час
- ✅ Статистика в реальном времени

### Веб-фишки:
- 🌍 Работает на любом устройстве
- 📱 Touch свайпы на мобильных
- ⌨️ Keyboard shortcuts на desktop
- 🎨 Красивый адаптивный дизайн
- 🔄 Real-time обновления через WebSocket
- 🚀 Можно развернуть на сервере

## 📂 Структура проекта

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

## 📱 На iPhone/iPad

### Вариант 1: Через локальную сеть

1. Узнайте IP вашего компьютера:
   ```bash
   # Linux/Mac
   ifconfig | grep "inet " | grep -v 127.0.0.1

   # Windows
   ipconfig
   ```

2. Откройте в Safari на iPhone:
   ```
   http://192.168.1.XXX:5000
   ```

3. Добавьте на главный экран:
   - Нажмите кнопку "Поделиться"
   - Выберите "На экран Домой"
   - Работает как нативное приложение!

### Вариант 2: Через интернет (деплой)

Разверните на https://railway.app или https://render.com - получите постоянный URL!

## 🔧 API Endpoints

```
GET  /api/status              # Статус подключения
GET  /api/config              # Настройки
POST /api/config              # Сохранить настройки
POST /api/connect             # Подключиться к Telegram
POST /api/verify_code         # Проверить код авторизации
GET  /api/dialogs?hours=24    # Загрузить диалоги
POST /api/process             # Обработать свайп
GET  /api/stats               # Статистика
POST /api/auto_scan           # Вкл/выкл автосканирование
POST /api/clear_history       # Очистить историю
```

## 💾 База данных

**SQLite (по умолчанию):**
- `telegram_messages_web.db` - отслеживание сообщений
- `web_config.json` - конфигурация

**Безопасность:**
- 🔒 Не коммитьте `.session` файлы
- 🔒 Не коммитьте `web_config.json`
- 🔒 Добавьте `.gitignore`

## 🌍 Деплой (работа 24/7)

### Railway.app (Рекомендую!)

**Бесплатно:**
- 500 часов/месяц
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

## 🐛 Troubleshooting

### Port 5000 already in use

```bash
# macOS - AirPlay использует порт 5000
# System Settings → General → AirDrop & Handoff →
# Выключите "AirPlay Receiver"

# Или измените порт в app.py:
socketio.run(app, port=8080)
```

### Module not found

```bash
pip3 install -r requirements.txt --upgrade
```

### Cannot connect to Telegram

1. Проверьте API ID/Hash на https://my.telegram.org
2. Удалите `web_session.session`
3. Перезапустите сервер

## 🎨 Кастомизация

### Цвета:

В `templates/index.html`:
```css
/* Градиент фона */
background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);

/* Кнопки */
.swipe-btn-left { background: #ff9800; }  /* Оранжевая */
.swipe-btn-right { background: #4caf50; } /* Зеленая */
```

### Интервал сканирования:

В `backend/app.py`:
```python
# Ждем 1 час
for _ in range(3600):  # 3600 = 1 час
    # Измените на 1800 для 30 минут
```

## 📊 Преимущества веб-версии

| Функция | Desktop v3 | Web v3 |
|---------|------------|--------|
| Умная проверка каждого сообщения | ✅ | ✅ |
| Контекст диалогов | ✅ | ✅ |
| Автосканирование | ✅ | ✅ |
| Работает на любом устройстве | ❌ | ✅ |
| Touch свайпы | ❌ | ✅ |
| Работа 24/7 (если на сервере) | ❌ | ✅ |
| Не нужен Python на клиенте | ❌ | ✅ |
| WebSocket real-time | ❌ | ✅ |

## 🔐 Безопасность

**Для локального использования:**
- ✅ Безопасно (работает только в вашей сети)

**Для деплоя на сервер:**
- 🔒 Добавьте аутентификацию (login/password)
- 🔒 Используйте HTTPS
- 🔒 Не коммитьте `.session` и `web_config.json` файлы
- 🔒 Используйте переменные окружения для API ключей

## 🚀 Roadmap

- [ ] Аутентификация (логин/пароль)
- [ ] Multi-user support
- [ ] Push уведомления
- [ ] Темная тема
- [ ] Экспорт в CSV/Excel
- [ ] Интеграция с CRM
- [ ] Telegram Bot для уведомлений
- [ ] Docker контейнер

## 💬 Поддержка

Вопросы? Проблемы?
1. Проверьте Troubleshooting выше
2. Смотрите полную документацию
3. Создайте Issue на GitHub

---

## 🎉 Готово!

```bash
cd telegram_swiper_web/backend
python3 app.py

# Откройте: http://localhost:5000
```

**Работает!** Начинайте свайпать!

---

Сделано с ❤️ для эффективной работы с клиентами
