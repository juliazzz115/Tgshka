"""
Telegram Message Loader для веб-версии
Версия 4 - с очередью для БД операций
"""

import asyncio
import sqlite3
import time
import threading
import queue
import sys
from datetime import datetime, timedelta, timezone
from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.tl.types import User, Chat, Channel

# Глобальная очередь для операций с БД
_db_queue = queue.Queue()
_db_worker_thread = None
_db_worker_running = False
_db_connection = None
_db_worker_lock = threading.Lock()  # Защита от одновременного запуска воркеров


def _db_worker():
    """Воркер для выполнения операций с БД в отдельном потоке"""
    global _db_connection, _db_worker_running

    try:
        # Создаём одно постоянное соединение для этого потока
        print(f"[DB Worker] Starting DB worker thread {threading.current_thread().name}")
        _db_connection = sqlite3.connect("telegram_messages_web.db", timeout=30.0, check_same_thread=False)
        _db_connection.execute('PRAGMA journal_mode=DELETE')  # Отключаем WAL для простоты
        _db_connection.execute('PRAGMA synchronous=NORMAL')   # Быстрее записи
        print("[DB Worker] Database connection established")

        while _db_worker_running:
            try:
                # Получаем задачу из очереди (ждём макс 1 секунду)
                func, result_queue = _db_queue.get(timeout=1.0)

                try:
                    # Выполняем функцию
                    result = func(_db_connection)
                    result_queue.put(('success', result))
                except Exception as e:
                    print(f"[DB Worker] Error executing DB operation: {e}")
                    result_queue.put(('error', e))
                finally:
                    _db_queue.task_done()
            except queue.Empty:
                continue

        # Закрываем соединение при остановке
        if _db_connection:
            _db_connection.close()
            print("[DB Worker] Database connection closed")
    except Exception as e:
        print(f"[DB Worker] Fatal error in DB worker: {e}")
        _db_worker_running = False


def _start_db_worker():
    """Запустить воркер БД если он ещё не запущен"""
    global _db_worker_thread, _db_worker_running

    # Thread-safe проверка и запуск
    with _db_worker_lock:
        if not _db_worker_running:
            print("[DB Worker] Starting new DB worker thread")
            _db_worker_running = True
            _db_worker_thread = threading.Thread(target=_db_worker, daemon=True)
            _db_worker_thread.start()
            time.sleep(0.1)  # Даём воркеру время запуститься
        else:
            print("[DB Worker] Worker already running")


def _execute_in_queue(func, timeout=30.0):
    """Выполнить функцию в очереди БД"""
    _start_db_worker()

    result_queue = queue.Queue()
    _db_queue.put((func, result_queue))

    try:
        status, result = result_queue.get(timeout=timeout)
        if status == 'error':
            raise result
        return result
    except queue.Empty:
        raise TimeoutError("Database operation timed out")


class TelegramMessageLoaderWeb:
    def __init__(self, api_id, api_hash, session_name="web_session"):
        self.api_id = api_id
        self.api_hash = api_hash
        self.session_name = session_name
        self.client = None
        self.db_path = "telegram_messages_web.db"
        self.init_database()

    def init_database(self):
        """Инициализация базы данных"""
        def _init(conn):
            cursor = conn.cursor()

            # Таблица для хранения сессии Telegram (вместо SQLite файла)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS telegram_session (
                    id INTEGER PRIMARY KEY CHECK (id = 1),
                    session_string TEXT
                )
            ''')

            # Таблица для отслеживания обработанных сообщений
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS processed_messages (
                    message_id INTEGER,
                    dialog_id INTEGER,
                    action TEXT,
                    timestamp TEXT,
                    PRIMARY KEY (message_id, dialog_id)
                )
            ''')

            # Таблица для отслеживания диалогов
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS dialog_tracking (
                    dialog_id INTEGER PRIMARY KEY,
                    dialog_name TEXT,
                    last_message_id INTEGER,
                    last_check_time TEXT
                )
            ''')

            # Таблица для статистики сканирований
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS scan_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    scan_time TEXT,
                    dialogs_scanned INTEGER,
                    messages_found INTEGER
                )
            ''')

            conn.commit()
            return None

        _execute_in_queue(_init)

    def _load_session_string(self):
        """Загрузить строку сессии из БД"""
        def _load(conn):
            cursor = conn.cursor()
            cursor.execute('SELECT session_string FROM telegram_session WHERE id = 1')
            result = cursor.fetchone()
            return result[0] if result else None

        return _execute_in_queue(_load)

    def _save_session_string(self, session_string):
        """Сохранить строку сессии в БД"""
        def _save(conn):
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO telegram_session (id, session_string)
                VALUES (1, ?)
            ''', (session_string,))
            conn.commit()
            print(f"[Session] Saved session string to DB")
            return None

        _execute_in_queue(_save)

    async def connect(self):
        """Подключение к Telegram с использованием StringSession"""
        # Загружаем сохраненную сессию
        session_string = self._load_session_string()

        if session_string:
            print("[Session] Loading existing session from DB")
            session = StringSession(session_string)
        else:
            print("[Session] Creating new session")
            session = StringSession()

        self.client = TelegramClient(session, self.api_id, self.api_hash)
        await self.client.connect()

        if not await self.client.is_user_authorized():
            return False

        # Сохраняем сессию после успешного подключения
        session_string = self.client.session.save()
        self._save_session_string(session_string)

        return True

    async def send_code_request(self, phone):
        """Отправить запрос кода"""
        return await self.client.send_code_request(phone)

    async def sign_in(self, phone, code, password=None):
        """Авторизация с поддержкой 2FA"""
        if password:
            # Если есть пароль 2FA, сначала вводим код, потом пароль
            try:
                await self.client.sign_in(phone, code)
            except:
                # Если требуется 2FA, вводим пароль
                await self.client.sign_in(password=password)
        else:
            # Обычная авторизация
            await self.client.sign_in(phone, code)

        # Сохраняем сессию после успешной авторизации
        session_string = self.client.session.save()
        self._save_session_string(session_string)
        print("[Session] Session saved after successful sign-in")

    async def disconnect(self):
        """Отключение"""
        if self.client:
            await self.client.disconnect()

    def clear_session(self):
        """Удалить сохраненную сессию"""
        def _clear(conn):
            cursor = conn.cursor()
            cursor.execute('DELETE FROM telegram_session WHERE id = 1')
            conn.commit()
            print("[Session] Session cleared from DB")
            return None

        _execute_in_queue(_clear)

    def is_message_processed(self, dialog_id, message_id):
        """Проверка, обработано ли сообщение"""
        def _query(conn):
            cursor = conn.cursor()
            cursor.execute('''
                SELECT action FROM processed_messages
                WHERE dialog_id = ? AND message_id = ?
            ''', (dialog_id, message_id))
            return cursor.fetchone()

        result = _execute_in_queue(_query)

        if result:
            # Если помечено как "answered" - не показывать
            # Если "mark_unread" - показывать снова
            return result[0] == "answered"
        return False

    def get_last_processed_message_id(self, dialog_id):
        """Получить ID последнего обработанного сообщения в диалоге"""
        def _query(conn):
            cursor = conn.cursor()
            cursor.execute('''
                SELECT last_message_id FROM dialog_tracking
                WHERE dialog_id = ?
            ''', (dialog_id,))
            result = cursor.fetchone()
            return result[0] if result else 0

        return _execute_in_queue(_query)

    def set_last_processed_message_id(self, dialog_id, message_id, dialog_name):
        """Сохранить ID последнего обработанного сообщения в диалоге"""
        def _write(conn):
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO dialog_tracking
                (dialog_id, dialog_name, last_message_id, last_check_time)
                VALUES (?, ?, ?, ?)
            ''', (dialog_id, dialog_name, message_id, datetime.now().isoformat()))
            conn.commit()
            return None

        _execute_in_queue(_write)
        print(f"[Dialog] Set last_processed_message_id for {dialog_name}: {message_id}")

    def get_processed_messages_for_dialog(self, dialog_id, message_ids):
        """Получить все обработанные сообщения для диалога (bulk запрос) - DEPRECATED"""
        # Теперь используем get_last_processed_message_id вместо этого
        if not message_ids:
            return set()

        def _query(conn):
            cursor = conn.cursor()
            # Создаём placeholder для IN clause
            placeholders = ','.join('?' * len(message_ids))
            cursor.execute(f'''
                SELECT message_id FROM processed_messages
                WHERE dialog_id = ? AND message_id IN ({placeholders}) AND action = 'answered'
            ''', (dialog_id, *message_ids))
            return set(row[0] for row in cursor.fetchall())

        return _execute_in_queue(_query)

    def mark_messages_as_processed(self, dialog_id, message_ids, action="answered"):
        """Пометить сообщения как обработанные"""
        def _write(conn):
            cursor = conn.cursor()
            timestamp = datetime.now().isoformat()

            for msg_id in message_ids:
                cursor.execute('''
                    INSERT OR REPLACE INTO processed_messages
                    (message_id, dialog_id, action, timestamp)
                    VALUES (?, ?, ?, ?)
                ''', (msg_id, dialog_id, action, timestamp))

            conn.commit()
            return None

        _execute_in_queue(_write)

    async def load_dialogs(self, hours_back=24):
        """Загрузить диалоги с непрочитанными сообщениями"""
        print(f"[load_dialogs] Starting, hours_back={hours_back}")

        if not self.client:
            print("[load_dialogs] ERROR: No client")
            raise Exception("Клиент не создан")

        print("[load_dialogs] Checking authorization...")
        is_auth = await self.client.is_user_authorized()
        print(f"[load_dialogs] Client authorized: {is_auth}")

        if not is_auth:
            raise Exception("Не подключен к Telegram")

        # Вычисляем время начала проверки: вчера в 17:00 по польскому времени (16:00 UTC, так как Польша UTC+1)
        now = datetime.now(timezone.utc)
        yesterday = now.date() - timedelta(days=1)
        time_limit = datetime.combine(yesterday, datetime.min.time().replace(hour=16), tzinfo=timezone.utc)

        sys.stderr.write(f"[load_dialogs] Time filter: from {time_limit} (16:00 UTC = 17:00 Poland time) to {now}\n")
        sys.stderr.flush()

        dialogs_data = []
        dialogs_scanned = 0
        total_messages = 0

        print("[load_dialogs] Starting to iterate dialogs...")

        # Получаем диалоги (лимит 100 для баланса между полнотой и скоростью)
        async for dialog in self.client.iter_dialogs(limit=100):
            dialogs_scanned += 1
            if dialogs_scanned % 10 == 0:
                print(f"[load_dialogs] Processed {dialogs_scanned} dialogs...")

            # Пропускаем каналы и группы
            if isinstance(dialog.entity, (Chat, Channel)):
                print(f"[load_dialogs] Skipping {dialog.name} (channel/group)")
                continue

            print(f"[load_dialogs] Processing user dialog: {dialog.name}")

            # Шаг 1: Собираем все сообщения из диалога
            all_messages = []
            async for message in self.client.iter_messages(dialog, limit=50):
                if message.date < time_limit:
                    break
                if message.text:  # Пропускаем служебные
                    all_messages.append(message)

            if not all_messages:
                print(f"[load_dialogs] Dialog {dialog.name}: no text messages, skipping")
                continue

            # Шаг 2: Получаем ID последнего обработанного сообщения в диалоге
            last_processed_id = self.get_last_processed_message_id(dialog.id)

            # Получаем количество непрочитанных сообщений в диалоге
            unread_count = dialog.unread_count if hasattr(dialog, 'unread_count') else 0

            # Определяем ID последнего прочитанного сообщения через unread_count
            # Собираем только входящие сообщения для определения границы
            incoming_messages = [msg for msg in all_messages if not msg.out]

            # Если есть непрочитанные, то последние unread_count входящих сообщений - непрочитанные
            # Остальные входящие - прочитанные
            if unread_count > 0 and len(incoming_messages) > unread_count:
                # Последнее прочитанное сообщение - это (количество входящих - количество непрочитанных)-ое сообщение
                last_read_index = len(incoming_messages) - unread_count - 1
                read_inbox_max_id = incoming_messages[last_read_index].id if last_read_index >= 0 else 0
            elif unread_count == 0 and incoming_messages:
                # Все входящие сообщения прочитаны - берем ID последнего
                read_inbox_max_id = incoming_messages[0].id  # Первое в списке = последнее по времени
            else:
                # Все непрочитанные или нет входящих
                read_inbox_max_id = 0

            sys.stderr.write(f"[load_dialogs] Dialog {dialog.name}: {len(all_messages)} messages, {len(incoming_messages)} incoming, unread_count={unread_count}, last_processed_id={last_processed_id}, read_inbox_max_id={read_inbox_max_id}\n")
            sys.stderr.flush()

            # Шаг 3: Фильтруем сообщения - показываем только новые (с id > last_processed_id)
            messages = []
            pending_messages = []  # Входящие сообщения, требующие обработки

            for message in all_messages:
                # Показываем только ПРОЧИТАННЫЕ в Telegram входящие сообщения, которые еще не обработаны в приложении
                # not message.out - входящее сообщение (не от меня)
                # message.id <= read_inbox_max_id - прочитано в Telegram (используем наш вычисленный read_inbox_max_id)
                # message.id > last_processed_id - еще не обработано в приложении

                if not message.out and message.id <= read_inbox_max_id and message.id > last_processed_id:
                    sys.stderr.write(f"  -> Adding message ID={message.id} (read, not processed yet)\n")
                    sys.stderr.flush()
                    pending_messages.append({
                        'id': message.id,
                        'text': message.text,
                        'date': message.date.strftime('%Y-%m-%d %H:%M:%S'),
                        'time': message.date.strftime('%H:%M')
                    })

                # Собираем контекст (последние 10 сообщений)
                if len(messages) < 10:
                    messages.append({
                        'id': message.id,
                        'text': message.text,
                        'date': message.date.strftime('%H:%M'),
                        'from_me': message.out,
                        'sender': 'Вы' if message.out else self._get_dialog_name(dialog)
                    })

            # Если есть необработанные сообщения, добавляем диалог
            if pending_messages:
                total_messages += len(pending_messages)

                # Находим последнее сообщение от вас
                last_your_message = None
                for msg in messages:
                    if msg['from_me']:
                        last_your_message = msg['date']
                        break

                dialogs_data.append({
                    'dialog_id': dialog.id,
                    'dialog_name': self._get_dialog_name(dialog),
                    'unread_count': len(pending_messages),
                    'unread_messages': pending_messages,
                    'context': list(reversed(messages)),  # От старых к новым
                    'last_message_date': messages[0]['date'] if messages else '',
                    'last_your_message_date': last_your_message
                })

        # Сохраняем статистику сканирования
        print(f"[load_dialogs] Saving scan stats: {dialogs_scanned} dialogs, {total_messages} messages")
        self._save_scan_stats(dialogs_scanned, total_messages)

        # Сортируем по количеству непрочитанных (больше = важнее)
        dialogs_data.sort(key=lambda x: x['unread_count'], reverse=True)

        print(f"[load_dialogs] Returning {len(dialogs_data)} dialogs with unread messages")
        return dialogs_data

    def _get_dialog_name(self, dialog):
        """Получить имя диалога"""
        if isinstance(dialog.entity, User):
            if dialog.entity.first_name and dialog.entity.last_name:
                return f"{dialog.entity.first_name} {dialog.entity.last_name}"
            elif dialog.entity.first_name:
                return dialog.entity.first_name
            elif dialog.entity.username:
                return f"@{dialog.entity.username}"
        return "Unknown"

    async def mark_dialog_as_unread(self, dialog_id):
        """Пометить диалог как непрочитанный в Telegram"""
        try:
            entity = await self.client.get_entity(dialog_id)
            await self.client.send_read_acknowledge(entity, clear_mentions=False)
        except:
            pass

    def _save_scan_stats(self, dialogs_scanned, messages_found):
        """Сохранить статистику сканирования"""
        def _write(conn):
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO scan_history (scan_time, dialogs_scanned, messages_found)
                VALUES (?, ?, ?)
            ''', (datetime.now().isoformat(), dialogs_scanned, messages_found))
            conn.commit()
            return None

        _execute_in_queue(_write)

    def get_statistics(self):
        """Получить статистику по диалогам"""
        def _query(conn):
            cursor = conn.cursor()

            # Всего отслеживаемых диалогов
            cursor.execute("SELECT COUNT(*) FROM dialog_tracking")
            total_dialogs = cursor.fetchone()[0]

            # Обработанных диалогов (где last_message_id > 0)
            cursor.execute("SELECT COUNT(*) FROM dialog_tracking WHERE last_message_id > 0")
            processed_dialogs = cursor.fetchone()[0]

            # Всего сканирований
            cursor.execute("SELECT COUNT(*) FROM scan_history")
            total_scans = cursor.fetchone()[0]

            # Последнее сканирование
            cursor.execute('''
                SELECT dialogs_scanned, messages_found
                FROM scan_history
                ORDER BY id DESC LIMIT 1
            ''')
            last_scan = cursor.fetchone()
            last_dialogs_scanned = last_scan[0] if last_scan else 0
            last_messages_found = last_scan[1] if last_scan else 0

            return {
                'total_dialogs': total_dialogs,
                'processed_dialogs': processed_dialogs,
                'total_scans': total_scans,
                'last_dialogs_scanned': last_dialogs_scanned,
                'last_messages_found': last_messages_found
            }

        return _execute_in_queue(_query)

    def get_last_scan_time(self):
        """Получить время последнего сканирования"""
        def _query(conn):
            cursor = conn.cursor()
            cursor.execute('''
                SELECT scan_time, dialogs_scanned, messages_found
                FROM scan_history
                ORDER BY id DESC LIMIT 1
            ''')
            result = cursor.fetchone()

            if result:
                return {
                    'time': result[0],
                    'dialogs_scanned': result[1],
                    'messages_found': result[2]
                }
            return None

        return _execute_in_queue(_query)

    def clear_all_history(self):
        """Очистить всю историю"""
        def _write(conn):
            cursor = conn.cursor()
            cursor.execute('DELETE FROM processed_messages')
            cursor.execute('DELETE FROM dialog_tracking')
            cursor.execute('DELETE FROM scan_history')
            conn.commit()
            return None

        _execute_in_queue(_write)


async def load_messages_web(api_id, api_hash, hours_back=24):
    """Основная функция загрузки для веб-версии"""
    loader = TelegramMessageLoaderWeb(api_id, api_hash)

    connected = await loader.connect()
    if not connected:
        raise Exception("Не удалось подключиться. Требуется авторизация.")

    dialogs = await loader.load_dialogs(hours_back)

    return dialogs, loader
