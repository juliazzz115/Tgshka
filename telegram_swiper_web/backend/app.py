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
import threading
import time
import nest_asyncio
from telegram_loader_web import TelegramMessageLoaderWeb, load_messages_web

# Разрешаем вложенные event loops для совместимости с eventlet
nest_asyncio.apply()

app = Flask(__name__,
            template_folder='../templates',
            static_folder='../static')
app.config['SECRET_KEY'] = 'telegram-swiper-secret-key-change-in-production'
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

# Глобальное состояние
loader = None
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

        # Проверяем авторизацию
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        connected = loop.run_until_complete(loader.connect())

        if connected:
            return jsonify({'success': True, 'authorized': True})
        else:
            # Нужна авторизация
            data = request.json
            phone = data.get('phone')

            if not phone:
                return jsonify({'success': True, 'authorized': False, 'need_phone': True})

            # Отправляем код
            loop.run_until_complete(loader.send_code_request(phone))

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

        if not phone or not code:
            return jsonify({'error': 'Укажите телефон и код'}), 400

        # Авторизуемся
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(loader.sign_in(phone, code))

        return jsonify({'success': True})

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/dialogs')
def api_dialogs():
    """Загрузить диалоги"""
    global loader, current_dialogs

    if not loader:
        return jsonify({'error': 'Не подключен к Telegram'}), 400

    try:
        hours = request.args.get('hours', 24, type=int)

        # Загружаем диалоги
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        dialogs, _ = loop.run_until_complete(load_messages_web(
            loader.api_id,
            loader.api_hash,
            hours_back=hours
        ))

        current_dialogs = dialogs

        return jsonify({
            'success': True,
            'dialogs': dialogs,
            'total': len(dialogs),
            'total_unread': sum(d['unread_count'] for d in dialogs)
        })

    except Exception as e:
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

        # Помечаем сообщения
        message_ids = [msg['id'] for msg in dialog['unread_messages']]
        loader.mark_messages_as_processed(dialog_id, message_ids, action)

        # Если mark_unread - помечаем в Telegram
        if action == 'mark_unread':
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(loader.mark_dialog_as_unread(dialog_id))

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
                # Сканируем каждый час
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                dialogs, _ = loop.run_until_complete(load_messages_web(
                    loader.api_id,
                    loader.api_hash,
                    hours_back=24
                ))

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
