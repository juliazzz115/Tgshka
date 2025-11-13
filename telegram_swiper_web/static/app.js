/**
 * Telegram Swiper v3 - Web App Logic
 * С поддержкой touch свайпов для мобильных
 */

// Global state
let dialogs = [];
let currentIndex = 0;
let socket = null;

// Touch/drag state
let startX = 0;
let startY = 0;
let currentX = 0;
let currentY = 0;
let isDragging = false;

/**
 * Запросить разрешение на уведомления
 */
function requestNotificationPermission() {
    if ('Notification' in window && Notification.permission === 'default') {
        Notification.requestPermission().then(permission => {
            console.log('Notification permission:', permission);
        });
    }
}

/**
 * Показать уведомление о новых диалогах
 */
function showNotification(dialogsCount) {
    if ('Notification' in window && Notification.permission === 'granted') {
        new Notification('Telegram Swiper', {
            body: `Найдено ${dialogsCount} новых диалогов`,
            icon: '/static/telegram-icon.png',
            badge: '/static/telegram-icon.png'
        });
    }
}

/**
 * Показать визуальное уведомление внутри приложения
 */
function showVisualNotification(message) {
    // Создаем элемент уведомления
    const notification = document.createElement('div');
    notification.className = 'visual-notification';
    notification.textContent = message;
    document.body.appendChild(notification);

    // Показываем
    setTimeout(() => notification.classList.add('show'), 10);

    // Скрываем через 3 секунды
    setTimeout(() => {
        notification.classList.remove('show');
        setTimeout(() => notification.remove(), 300);
    }, 3000);
}

/**
 * Инициализация при загрузке страницы
 */
window.addEventListener('DOMContentLoaded', () => {
    console.log('🚀 Telegram Swiper v3 started');

    // Подключаем WebSocket
    connectWebSocket();

    // Проверяем статус
    checkStatus();

    // Загружаем конфигурацию
    loadConfig();
});

/**
 * WebSocket подключение
 */
function connectWebSocket() {
    socket = io();

    socket.on('connect', () => {
        console.log('✅ WebSocket connected');
    });

    socket.on('dialogs_updated', (data) => {
        console.log('📨 Dialogs updated:', data);

        // Показываем уведомление если есть новые диалоги
        if (data.dialogs && data.dialogs.length > 0) {
            // Browser notification (если разрешено)
            showNotification(data.dialogs.length);
            // Визуальное уведомление (всегда работает)
            showVisualNotification(`Найдено ${data.dialogs.length} новых диалогов!`);
        }

        dialogs = data.dialogs;
        currentIndex = 0;
        updateDisplay();
    });
}

/**
 * Проверка статуса подключения
 */
async function checkStatus() {
    try {
        const response = await fetch('/api/status');
        const data = await response.json();

        if (data.connected) {
            showMainPanel();
            loadStats();
        } else {
            // Проверяем есть ли сохраненные API ключи
            const configResponse = await fetch('/api/config');
            const configData = await configResponse.json();

            if (configData.api_id && configData.has_api_hash) {
                // API ключи есть, но не авторизован - показываем панель авторизации
                showAuthPanel();
            } else {
                // Нет API ключей - показываем панель настроек
                // Она уже показана по умолчанию
            }
        }
    } catch (error) {
        console.error('Status check error:', error);
    }
}

/**
 * Загрузить конфигурацию
 */
async function loadConfig() {
    try {
        const response = await fetch('/api/config');
        const data = await response.json();

        if (data.api_id) {
            document.getElementById('api-id').value = data.api_id;
        }
    } catch (error) {
        console.error('Config load error:', error);
    }
}

/**
 * Сохранить конфигурацию и подключиться
 */
async function saveConfig() {
    const apiId = document.getElementById('api-id').value.trim();
    const apiHash = document.getElementById('api-hash').value.trim();

    if (!apiId || !apiHash) {
        alert('Заполните все поля!');
        return;
    }

    try {
        // Сохраняем конфигурацию
        await fetch('/api/config', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ api_id: apiId, api_hash: apiHash })
        });

        // Подключаемся
        const response = await fetch('/api/connect', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({})
        });

        const data = await response.json();

        if (data.authorized) {
            // Уже авторизован
            showMainPanel();
            loadStats();
        } else {
            // Нужна авторизация
            showAuthPanel();
        }

    } catch (error) {
        alert('Ошибка: ' + error.message);
    }
}

/**
 * Отправить код авторизации
 */
async function sendCode() {
    const phone = document.getElementById('phone').value.trim();

    if (!phone) {
        alert('Введите номер телефона!');
        return;
    }

    try {
        const response = await fetch('/api/connect', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ phone })
        });

        const data = await response.json();

        if (data.code_sent) {
            document.getElementById('code-input').classList.remove('hidden');
            alert('Код отправлен! Проверьте Telegram.');
        }

    } catch (error) {
        alert('Ошибка: ' + error.message);
    }
}

/**
 * Проверить код
 */
async function verifyCode() {
    const phone = document.getElementById('phone').value.trim();
    const code = document.getElementById('code').value.trim();
    const password = document.getElementById('password').value.trim();

    if (!phone || !code) {
        alert('Заполните все поля!');
        return;
    }

    try {
        // Отправляем запрос с кодом и паролем (если есть)
        const requestBody = { phone, code };
        if (password) {
            requestBody.password = password;
        }

        const response = await fetch('/api/verify_code', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(requestBody)
        });

        const data = await response.json();

        if (data.success) {
            showMainPanel();
            loadStats();
        } else if (data.need_password) {
            // Требуется пароль 2FA
            document.getElementById('password-input').classList.remove('hidden');
            alert('⚠️ Требуется пароль двухфакторной аутентификации!\n\nВведите пароль, который вы установили в настройках безопасности Telegram.');
        } else {
            alert('Ошибка: ' + (data.error || 'Неверный код!'));
        }

    } catch (error) {
        alert('Ошибка: ' + error.message);
    }
}

/**
 * Показать панель настроек
 */
function showSettingsPanel() {
    document.getElementById('settings-panel').classList.remove('hidden');
    document.getElementById('auth-panel').classList.add('hidden');
    document.getElementById('main-panel').classList.add('hidden');
    document.getElementById('stats-panel').classList.add('hidden');
}

/**
 * Показать панель авторизации
 */
function showAuthPanel() {
    document.getElementById('settings-panel').classList.add('hidden');
    document.getElementById('auth-panel').classList.remove('hidden');
    document.getElementById('main-panel').classList.add('hidden');
    document.getElementById('stats-panel').classList.add('hidden');
}

/**
 * Показать главную панель
 */
function showMainPanel() {
    document.getElementById('settings-panel').classList.add('hidden');
    document.getElementById('auth-panel').classList.add('hidden');
    document.getElementById('main-panel').classList.remove('hidden');
    document.getElementById('stats-panel').classList.remove('hidden');
}

/**
 * Загрузить диалоги
 */
async function loadDialogs(hours = 24) {
    // Запрашиваем разрешение на уведомления при первой загрузке
    requestNotificationPermission();

    try {
        const response = await fetch(`/api/dialogs?hours=${hours}`);
        const data = await response.json();

        if (data.success) {
            dialogs = data.dialogs;
            currentIndex = 0;

            updateCounter(data.total, data.total_unread);
            updateDisplay();
            loadStats();

            // Показываем визуальное уведомление если есть новые диалоги
            if (data.dialogs && data.dialogs.length > 0) {
                showVisualNotification(`Найдено ${data.dialogs.length} диалогов`);
            }
        } else {
            alert('Ошибка: ' + data.error);
        }

    } catch (error) {
        alert('Ошибка загрузки: ' + error.message);
    }
}

/**
 * Обновить счетчики
 */
function updateCounter(total, unread) {
    document.getElementById('counter').textContent = `${currentIndex} / ${total}`;
    document.getElementById('unread-count').textContent = `📊 Диалогов: ${total}`;
}

/**
 * Обновить отображение
 */
function updateDisplay() {
    const container = document.getElementById('card-container');
    container.innerHTML = '';

    if (currentIndex >= dialogs.length) {
        showCompletion();
        return;
    }

    // Показываем текущую и следующую карточку (для плавности)
    for (let i = 0; i < 2 && (currentIndex + i) < dialogs.length; i++) {
        const dialog = dialogs[currentIndex + i];
        const card = createCard(dialog, i);
        container.appendChild(card);
    }

    // Обновляем счетчик
    const totalUnread = dialogs.slice(currentIndex).reduce((sum, d) => sum + d.unread_count, 0);
    updateCounter(dialogs.length, totalUnread);
}

/**
 * Создать карточку диалога
 */
function createCard(dialog, zIndex) {
    const card = document.createElement('div');
    card.className = 'card';
    card.style.zIndex = 10 - zIndex;
    card.dataset.dialogId = dialog.dialog_id;

    // Header
    const header = document.createElement('div');
    header.className = 'card-header';

    // Создаем ссылку на Telegram
    let telegramLink = '';
    if (dialog.username) {
        // Если есть username - используем https://t.me/username
        telegramLink = `<a href="https://t.me/${dialog.username}" target="_blank" class="telegram-link">📱 Открыть в Telegram</a>`;
    } else {
        // Если нет username - используем tg://user?id=
        telegramLink = `<a href="tg://user?id=${dialog.dialog_id}" class="telegram-link">📱 Открыть в Telegram</a>`;
    }

    header.innerHTML = `
        <div class="card-title">👤 ${dialog.dialog_name}</div>
        ${telegramLink}
        <div class="card-date">📅 ${dialog.last_message_date}</div>
        ${dialog.last_your_message_date ? `<div class="card-date">✉️ Вы писали: ${dialog.last_your_message_date}</div>` : ''}
        <div class="card-info">💬 Новых сообщений: ${dialog.unread_count}</div>
    `;

    // Body
    const body = document.createElement('div');
    body.className = 'card-body';

    // История диалога
    if (dialog.context && dialog.context.length > 0) {
        const contextSection = document.createElement('div');
        contextSection.className = 'context-section';

        dialog.context.forEach(msg => {
            const messageDiv = document.createElement('div');
            messageDiv.className = `message ${msg.from_me ? 'from-me' : 'from-client'}`;
            messageDiv.innerHTML = `
                <div class="message-sender">${msg.from_me ? '→' : '←'} ${msg.sender} [${msg.date}]</div>
                <div class="message-text">${msg.text}</div>
            `;
            contextSection.appendChild(messageDiv);
        });

        body.appendChild(contextSection);
    }

    card.appendChild(header);
    card.appendChild(body);

    // Только для первой карточки добавляем обработчики
    if (zIndex === 0) {
        addSwipeHandlers(card);

        // Автопрокрутка к последним сообщениям - более агрессивный подход для мобильных
        const scrollToBottom = () => {
            const cardBody = card.querySelector('.card-body');
            if (cardBody) {
                // Находим последнее сообщение в диалоге
                const messages = cardBody.querySelectorAll('.message');
                if (messages.length > 0) {
                    const lastMessage = messages[messages.length - 1];
                    // Прокручиваем последнее сообщение в видимую область (instant, не smooth)
                    lastMessage.scrollIntoView({ behavior: 'auto', block: 'end', inline: 'nearest' });
                } else {
                    // Если сообщений нет, просто прокручиваем к концу
                    cardBody.scrollTop = cardBody.scrollHeight;
                }
            }
        };

        // Первая попытка через requestAnimationFrame (ждем рендера DOM)
        requestAnimationFrame(() => {
            requestAnimationFrame(() => {
                scrollToBottom();
                // Повторная попытка через 800мс на случай медленного рендера на мобильных
                setTimeout(scrollToBottom, 800);
            });
        });
    }

    return card;
}

/**
 * Добавить обработчики свайпов
 */
function addSwipeHandlers(card) {
    // Touch events
    card.addEventListener('touchstart', handleStart, false);
    card.addEventListener('touchmove', handleMove, false);
    card.addEventListener('touchend', handleEnd, false);

    // Mouse events (для desktop)
    card.addEventListener('mousedown', handleStart, false);
    card.addEventListener('mousemove', handleMove, false);
    card.addEventListener('mouseup', handleEnd, false);
    card.addEventListener('mouseleave', handleEnd, false);
}

/**
 * Начало свайпа
 */
function handleStart(e) {
    if (e.type === 'touchstart') {
        startX = e.touches[0].clientX;
        startY = e.touches[0].clientY;
    } else {
        startX = e.clientX;
        startY = e.clientY;
    }

    isDragging = true;
    this.classList.add('dragging');
}

/**
 * Движение свайпа
 */
function handleMove(e) {
    if (!isDragging) return;

    e.preventDefault();

    if (e.type === 'touchmove') {
        currentX = e.touches[0].clientX;
        currentY = e.touches[0].clientY;
    } else {
        currentX = e.clientX;
        currentY = e.clientY;
    }

    const deltaX = currentX - startX;
    const deltaY = currentY - startY;
    const rotation = deltaX * 0.1; // Небольшой поворот

    this.style.transform = `translate(${deltaX}px, ${deltaY}px) rotate(${rotation}deg)`;
    this.style.transition = 'none';
}

/**
 * Конец свайпа
 */
function handleEnd(e) {
    if (!isDragging) return;

    isDragging = false;
    this.classList.remove('dragging');

    const deltaX = currentX - startX;
    const threshold = 100; // Минимальное расстояние для свайпа

    if (Math.abs(deltaX) > threshold) {
        if (deltaX > 0) {
            // Свайп вправо
            animateSwipe(this, 'right');
            processSwipe('answered');
        } else {
            // Свайп влево
            animateSwipe(this, 'left');
            processSwipe('mark_unread');
        }
    } else {
        // Вернуть карточку на место
        this.style.transform = '';
        this.style.transition = 'transform 0.3s';
    }

    startX = 0;
    startY = 0;
    currentX = 0;
    currentY = 0;
}

/**
 * Анимация свайпа
 */
function animateSwipe(card, direction) {
    card.style.transition = 'transform 0.3s, opacity 0.3s';
    card.classList.add(`swiped-${direction}`);

    setTimeout(() => {
        currentIndex++;
        updateDisplay();
    }, 300);
}

/**
 * Свайп влево (кнопка)
 */
function swipeLeft() {
    const card = document.querySelector('.card');
    if (card) {
        animateSwipe(card, 'left');
        processSwipe('mark_unread');
    }
}

/**
 * Свайп вправо (кнопка)
 */
function swipeRight() {
    const card = document.querySelector('.card');
    if (card) {
        animateSwipe(card, 'right');
        processSwipe('answered');
    }
}

/**
 * Обработать свайп на сервере
 */
async function processSwipe(action) {
    if (currentIndex >= dialogs.length) return;

    const dialog = dialogs[currentIndex - 1]; // -1 потому что уже инкрементировали

    try {
        await fetch('/api/process', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                dialog_id: dialog.dialog_id,
                action: action
            })
        });

        // Обновляем статистику
        loadStats();

    } catch (error) {
        console.error('Process error:', error);
    }
}

/**
 * Показать экран завершения
 */
function showCompletion() {
    const container = document.getElementById('card-container');
    container.innerHTML = `
        <div class="completion">
            <h2>🎉 Все диалоги обработаны!</h2>
            <p>Обработано ${dialogs.length} диалогов</p>
            <p style="margin-top: 20px;">Нажмите "Загрузить сообщения" для обновления</p>
        </div>
    `;
}

/**
 * Загрузить статистику
 */
async function loadStats() {
    try {
        const response = await fetch('/api/stats');
        const data = await response.json();

        if (data.success) {
            document.getElementById('stat-total-dialogs').textContent = data.stats.total_dialogs;
            document.getElementById('stat-processed-dialogs').textContent = data.stats.processed_dialogs;
            document.getElementById('stat-scans').textContent = data.stats.total_scans;
        }

    } catch (error) {
        console.error('Stats error:', error);
    }
}

/**
 * Выйти из аккаунта
 */
async function logout() {
    if (!confirm('Вы уверены что хотите выйти?')) {
        return;
    }

    try {
        const response = await fetch('/api/logout', {
            method: 'POST'
        });
        const data = await response.json();

        if (data.success) {
            alert('Вы вышли из аккаунта');
            location.reload();
        } else {
            alert('Ошибка выхода: ' + (data.error || 'Unknown error'));
        }
    } catch (error) {
        alert('Ошибка выхода: ' + error.message);
    }
}

/**
 * Очистить историю
 */
async function clearHistory() {
    if (!confirm('Вы уверены? Это удалит ВСЮ историю обработанных сообщений!')) {
        return;
    }

    try {
        const response = await fetch('/api/clear_history', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });

        const data = await response.json();

        if (data.success) {
            alert('История очищена!');
            loadStats();
        }

    } catch (error) {
        alert('Ошибка: ' + error.message);
    }
}
