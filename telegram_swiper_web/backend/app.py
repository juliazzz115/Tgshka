"""
Flask Web Server для Telegram Swiper
Версия 3 - с WebSocket поддержкой
"""

from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit
from flask_cors import CORS
import asyncio
import json
import os
import sys
import threading
import time
import nest_asyncio
from telegram_loader_web import TelegramMessageLoaderWeb

# Разрешаем вложенные event loops для совместимости с eventlet
nest_asyncio.apply()

# На macOS принудительно используем select вместо kqueue (исправляет ошибку в многопоточности)
if sys.platform == 'darwin':
    import selectors

    # Monkey-patch asyncio для использования SelectSelector на macOS
    _original_new_event_loop = asyncio.new_event_loop

    def patched_new_event_loop():
        """Создаем event loop с SelectSelector вместо KqueueSelector"""
        selector = selectors.SelectSelector()
        loop = asyncio.SelectorEventLoop(selector)
        return loop

    asyncio.new_event_loop = patched_new_event_loop

app = Flask(__name__,
            template_folder='../templates',
            static_folder='../static')
app.config['SECRET_KEY'] = 'telegram-swiper-secret-key-change-in-production'
CORS(app)
# Автоматический выбор async mode (eventlet/threading/другое)
socketio = SocketIO(app, cors_allowed_origins="*")

# Глобальное состояние
loader = None
loader_loop = None  # Event loop для loader
loader_thread = None  # Поток для loader
current_dialogs = []
auto_scan_enabled = False
auto_scan_thread = None
config_file = "web_config.json"


def load_config():
    """Загрузить конфигурацию"""
    if os.path.exists(config_file):
        try:
            with open(config_file, 'r') as f:
                return json.load(f)
        except:
            pass
    return {}


def save_config(config):
    """Сохранить конфигурацию"""
    with open(config_file, 'w') as f:
        json.dump(config, f)


@app.route('/')
def index():
    """Главная страница"""
    return render_template('index.html')


@app.route('/api/status')
def api_status():
    """Статус подключения"""
    global loader

    if loader and loader.client:
        return jsonify({
            'connected': True,
            'auto_scan': auto_scan_enabled
        })

    return jsonify({
        'connected': False,
        'auto_scan': auto_scan_enabled
    })


@app.route('/api/config', methods=['GET', 'POST'])
def api_config():
    """Получить/сохранить настройки"""
    if request.method == 'GET':
        config = load_config()
        # Не отправляем api_hash клиенту (безопасность)
        return jsonify({
            'api_id': config.get('api_id', ''),
            'has_api_hash': bool(config.get('api_hash'))
        })

    if request.method == 'POST':
        data = request.json
        config = {
            'api_id': data.get('api_id', ''),
            'api_hash': data.get('api_hash', '')
        }
        save_config(config)
        return jsonify({'success': True})


def run_async_in_loader_thread(coro):
    """Запустить async код в выделенном потоке loader (использует один event loop)"""
    global loader_loop, loader_thread

    result = {'value': None, 'error': None, 'done': False}

    def execute():
        try:
            result['value'] = asyncio.run_coroutine_threadsafe(coro, loader_loop).result()
        except Exception as e:
            result['error'] = e
        finally:
            result['done'] = True

    # Если нет выделенного потока, создаем
    if loader_loop is None or not loader_loop.is_running():
        def run_event_loop():
            global loader_loop
            loader_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loader_loop)
            loader_loop.run_forever()

        loader_thread = threading.Thread(target=run_event_loop, daemon=True)
        loader_thread.start()
        time.sleep(0.1)  # Даем время на запуск loop

    # Запускаем coroutine в существующем event loop
    future = asyncio.run_coroutine_threadsafe(coro, loader_loop)

    try:
        return future.result(timeout=30)  # Таймаут 30 секунд
    except Exception as e:
        raise e


@app.route('/api/connect', methods=['POST'])
def api_connect():
    """Подключиться к Telegram"""
    global loader

    config = load_config()

    if not config.get('api_id') or not config.get('api_hash'):
        return jsonify({'error': 'API ID и API Hash не настроены'}), 400

    try:
        # Создаем loader
        loader = TelegramMessageLoaderWeb(
            int(config['api_id']),
            config['api_hash']
        )

        # Проверяем авторизацию в выделенном потоке loader
        connected = run_async_in_loader_thread(loader.connect())

        if connected:
            return jsonify({'success': True, 'authorized': True})
        else:
            # Нужна авторизация
            data = request.json
            phone = data.get('phone')

            if not phone:
                return jsonify({'success': True, 'authorized': False, 'need_phone': True})

            # Отправляем код в том же потоке
            run_async_in_loader_thread(loader.send_code_request(phone))

            return jsonify({
                'success': True,
                'authorized': False,
                'code_sent': True
            })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/verify_code', methods=['POST'])
def api_verify_code():
    """Проверить код авторизации"""
    global loader

    if not loader:
        return jsonify({'error': 'Сначала инициализируйте подключение'}), 400

    try:
        data = request.json
        phone = data.get('phone')
        code = data.get('code')
        password = data.get('password')  # Опциональный пароль для 2FA

        if not phone or not code:
            return jsonify({'error': 'Укажите телефон и код'}), 400

        # Авторизуемся в отдельном потоке
        if password:
            # Если есть пароль - используем его для 2FA
            run_async_in_loader_thread(loader.sign_in(phone, code, password=password))
        else:
            # Обычная авторизация
            run_async_in_loader_thread(loader.sign_in(phone, code))

        return jsonify({'success': True})

    except Exception as e:
        error_msg = str(e)
        # Проверяем, требуется ли 2FA пароль
        if 'password is required' in error_msg.lower() or 'two-steps' in error_msg.lower():
            return jsonify({
                'error': error_msg,
                'need_password': True
            }), 400
        return jsonify({'error': error_msg}), 500


@app.route('/api/dialogs')
def api_dialogs():
    """Загрузить диалоги"""
    global loader, current_dialogs

    if not loader:
        return jsonify({'error': 'Не подключен к Telegram'}), 400

    try:
        hours = request.args.get('hours', 24, type=int)

        # Используем уже авторизованный loader
        dialogs = run_async_in_loader_thread(loader.load_dialogs(hours))

        current_dialogs = dialogs

        return jsonify({
            'success': True,
            'dialogs': dialogs,
            'total': len(dialogs),
            'total_unread': sum(d['unread_count'] for d in dialogs)
        })

    except Exception as e:
        print(f"[ERROR] /api/dialogs failed: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/api/process', methods=['POST'])
def api_process():
    """Обработать свайп"""
    global loader, current_dialogs

    if not loader:
        return jsonify({'error': 'Не подключен к Telegram'}), 400

    try:
        data = request.json
        dialog_id = data.get('dialog_id')
        action = data.get('action')  # 'answered' или 'mark_unread'

        if not dialog_id or not action:
            return jsonify({'error': 'Укажите dialog_id и action'}), 400

        # Находим диалог
        dialog = next((d for d in current_dialogs if d['dialog_id'] == dialog_id), None)

        if not dialog:
            return jsonify({'error': 'Диалог не найден'}), 404

        if action == 'answered':
            # При "Обработано" - сохраняем максимальный ID сообщения
            # Диалог исчезнет, но появится снова если придут новые сообщения
            message_ids = [msg['id'] for msg in dialog['unread_messages']]
            if message_ids:
                max_message_id = max(message_ids)
                loader.set_last_processed_message_id(
                    dialog_id,
                    max_message_id,
                    dialog['dialog_name']
                )
        elif action == 'mark_unread':
            # При "Непрочитанное" - сбрасываем last_processed_message_id
            # Диалог останется в списке
            loader.set_last_processed_message_id(
                dialog_id,
                0,  # Сбрасываем, чтобы диалог остался
                dialog['dialog_name']
            )
            # Также помечаем в Telegram
            run_async_in_loader_thread(loader.mark_dialog_as_unread(dialog_id))

        return jsonify({'success': True})

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/stats')
def api_stats():
    """Статистика"""
    global loader

    if not loader:
        return jsonify({'error': 'Не подключен к Telegram'}), 400

    try:
        stats = loader.get_statistics()
        last_scan = loader.get_last_scan_time()

        return jsonify({
            'success': True,
            'stats': stats,
            'last_scan': last_scan
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/auto_scan', methods=['POST'])
def api_auto_scan():
    """Включить/выключить автосканирование"""
    global auto_scan_enabled, auto_scan_thread

    data = request.json
    enabled = data.get('enabled', False)

    auto_scan_enabled = enabled

    if enabled and not auto_scan_thread:
        auto_scan_thread = threading.Thread(target=auto_scan_worker, daemon=True)
        auto_scan_thread.start()

    return jsonify({'success': True, 'enabled': auto_scan_enabled})


@app.route('/api/clear_history', methods=['POST'])
def api_clear_history():
    """Очистить всю историю"""
    global loader

    if not loader:
        return jsonify({'error': 'Не подключен к Telegram'}), 400

    try:
        loader.clear_all_history()
        return jsonify({'success': True})

    except Exception as e:
        return jsonify({'error': str(e)}), 500


def auto_scan_worker():
    """Фоновый worker для автосканирования"""
    global auto_scan_enabled, loader, current_dialogs

    while True:
        if not auto_scan_enabled:
            time.sleep(10)
            continue

        if loader:
            try:
                # Используем уже авторизованный loader
                dialogs = run_async_in_loader_thread(loader.load_dialogs(24))

                current_dialogs = dialogs

                # Уведомляем клиентов через WebSocket
                socketio.emit('dialogs_updated', {
                    'dialogs': dialogs,
                    'total': len(dialogs),
                    'total_unread': sum(d['unread_count'] for d in dialogs)
                })

            except Exception as e:
                print(f"Auto scan error: {e}")

        # Ждем 1 час
        for _ in range(3600):
            if not auto_scan_enabled:
                break
            time.sleep(1)


@socketio.on('connect')
def handle_connect():
    """WebSocket подключение"""
    emit('connected', {'status': 'ok'})


@socketio.on('disconnect')
def handle_disconnect():
    """WebSocket отключение"""
    pass


if __name__ == '__main__':
    # Получаем порт из переменной окружения (для Railway/Render) или используем 5000
    port = int(os.environ.get('PORT', 5000))

    print("=" * 60)
    print("🚀 Starting Telegram Swiper Web App v3...")
    print("=" * 60)
    print(f"📱 Open: http://localhost:{port}")
    print(f"🌍 Network: http://<your-ip>:{port}")
    print("=" * 60)
    print("🔧 Press Ctrl+C to stop")
    print("=" * 60)

    # Для Railway/Render используем production настройки
    is_production = os.environ.get('RAILWAY_ENVIRONMENT') or os.environ.get('RENDER')

    socketio.run(
        app,
        host='0.0.0.0',
        port=port,
        debug=not is_production,
        allow_unsafe_werkzeug=True
    )
