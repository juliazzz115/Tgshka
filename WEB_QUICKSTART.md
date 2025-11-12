# 🚀 Веб-приложение - Быстрый старт

## За 3 минуты до запуска!

### Шаг 1: Установка (30 секунд)

```bash
cd telegram_swiper_web
pip3 install -r requirements.txt
```

**Если ошибка с cryptg:**
```bash
pip3 uninstall cryptg
pip3 install -r requirements.txt
```

### Шаг 2: Запуск (10 секунд)

```bash
cd backend
python3 app.py
```

Увидите:
```
🚀 Starting Telegram Swiper Web App...
📱 Open: http://localhost:5000
🔧 Press Ctrl+C to stop
```

### Шаг 3: Открыть в браузере

Откройте: **http://localhost:5000**

### Шаг 4: Настройка

1. Введите API ID и API Hash
2. Нажмите "Сохранить и подключиться"
3. Введите номер телефона
4. Введите код из Telegram
5. Готово! 🎉

---

## 🎮 Как использовать

### Desktop (Mac/PC):
- **←** = Пометить непрочитанным
- **→** или **Space** = Обработано
- **Мышь** = Drag & Drop карточки

### Mobile (iPhone/iPad):
- **Свайп влево** = Пометить непрочитанным
- **Свайп вправо** = Обработано

---

## 📱 Открыть на iPhone

### 1. Узнайте IP вашего Mac:

```bash
ifconfig | grep "inet " | grep -v 127.0.0.1
```

Вы увидите что-то вроде: `inet 192.168.1.100`

### 2. Откройте на iPhone в Safari:

```
http://192.168.1.100:5000
```

(Замените 192.168.1.100 на ваш IP)

### 3. Добавьте на главный экран:

- Нажмите кнопку "Поделиться" (квадрат со стрелкой)
- Выберите "На экран Домой"
- Теперь приложение работает как нативное! 🎉

---

## 🌍 Деплой на сервер (работа 24/7)

### Railway.app (БЕСПЛАТНО!)

1. **Регистрация:**
   - Зайдите на https://railway.app
   - Sign up (можно через GitHub)

2. **Создание проекта:**
   - New Project → "Deploy from GitHub repo"
   - Выберите репозиторий с вашим кодом
   - Railway автоматически определит Python

3. **Готово!**
   - Railway даст вам URL типа: `https://your-app.railway.app`
   - Приложение работает 24/7!
   - Бесплатно на 500 часов/месяц (хватит с запасом)

### Или Render.com (тоже бесплатно!)

1. Зайдите на https://render.com
2. New → Web Service
3. Connect GitHub репозиторий
4. Build: `pip install -r requirements.txt`
5. Start: `cd backend && python app.py`
6. Deploy!

---

## 💡 Преимущества веб-версии

✅ **Работает везде:**
   - Mac, Windows, Linux
   - iPhone, iPad, Android
   - Любой браузер

✅ **Не нужно устанавливать:**
   - Только открыть ссылку
   - Работает сразу

✅ **Работает 24/7:**
   - Если развернуть на сервере
   - Даже когда Mac выключен

✅ **Touch свайпы:**
   - На мобильных как в Tinder
   - Быстро и удобно

✅ **Автообновления:**
   - Каждый час сканирует
   - Работает в фоне

---

## 🐛 Проблемы?

### "Port 5000 already in use"
```bash
# Найти процесс
lsof -i :5000

# Убить
kill -9 <PID>

# Или запустить на другом порту
# В app.py измените: port=8080
```

### "Module not found"
```bash
pip3 install -r requirements.txt --upgrade
```

### "Cannot connect to Telegram"
1. Проверьте API ID/Hash
2. Удалите `web_session.session`
3. Перезапустите приложение

---

## 📊 Полная документация

Смотрите: `telegram_swiper_web/README.md`

---

**Готово!** Откройте http://localhost:5000 и начинайте! 🚀
