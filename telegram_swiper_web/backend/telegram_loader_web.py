"""
Telegram Message Loader для веб-версии
Версия 3 - отслеживает каждое сообщение отдельно
"""

import asyncio
import sqlite3
from datetime import datetime, timedelta
from telethon import TelegramClient
from telethon.tl.types import User, Chat, Channel


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
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

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
        conn.close()

    async def connect(self):
        """Подключение к Telegram"""
        self.client = TelegramClient(self.session_name, self.api_id, self.api_hash)
        await self.client.connect()

        if not await self.client.is_user_authorized():
            return False
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

    async def disconnect(self):
        """Отключение"""
        if self.client:
            await self.client.disconnect()

    def is_message_processed(self, dialog_id, message_id):
        """Проверка, обработано ли сообщение"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            SELECT action FROM processed_messages
            WHERE dialog_id = ? AND message_id = ?
        ''', (dialog_id, message_id))

        result = cursor.fetchone()
        conn.close()

        if result:
            # Если помечено как "answered" - не показывать
            # Если "mark_unread" - показывать снова
            return result[0] == "answered"
        return False

    def mark_messages_as_processed(self, dialog_id, message_ids, action="answered"):
        """Пометить сообщения как обработанные"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        timestamp = datetime.now().isoformat()

        for msg_id in message_ids:
            cursor.execute('''
                INSERT OR REPLACE INTO processed_messages
                (message_id, dialog_id, action, timestamp)
                VALUES (?, ?, ?, ?)
            ''', (msg_id, dialog_id, action, timestamp))

        conn.commit()
        conn.close()

    async def load_dialogs(self, hours_back=24):
        """Загрузить диалоги с непрочитанными сообщениями"""
        if not self.client or not await self.client.is_user_authorized():
            raise Exception("Не подключен к Telegram")

        time_limit = datetime.now() - timedelta(hours=hours_back)
        dialogs_data = []
        dialogs_scanned = 0
        total_messages = 0

        # Получаем все диалоги
        async for dialog in self.client.iter_dialogs():
            dialogs_scanned += 1

            # Пропускаем каналы и группы
            if isinstance(dialog.entity, (Chat, Channel)):
                continue

            # Получаем последние сообщения
            messages = []
            unread_messages = []

            async for message in self.client.iter_messages(dialog, limit=50):
                if message.date < time_limit:
                    break

                # Пропускаем служебные сообщения
                if not message.text:
                    continue

                # Проверяем, было ли обработано
                is_processed = self.is_message_processed(dialog.id, message.id)

                # Если сообщение от клиента и не обработано
                if not message.out and not is_processed:
                    unread_messages.append({
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

            # Если есть непрочитанные, добавляем диалог
            if unread_messages:
                total_messages += len(unread_messages)

                # Находим последнее сообщение от вас
                last_your_message = None
                for msg in messages:
                    if msg['from_me']:
                        last_your_message = msg['date']
                        break

                dialogs_data.append({
                    'dialog_id': dialog.id,
                    'dialog_name': self._get_dialog_name(dialog),
                    'unread_count': len(unread_messages),
                    'unread_messages': unread_messages,
                    'context': list(reversed(messages)),  # От старых к новым
                    'last_message_date': messages[0]['date'] if messages else '',
                    'last_your_message_date': last_your_message
                })

        # Сохраняем статистику сканирования
        self._save_scan_stats(dialogs_scanned, total_messages)

        # Сортируем по количеству непрочитанных (больше = важнее)
        dialogs_data.sort(key=lambda x: x['unread_count'], reverse=True)

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
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO scan_history (scan_time, dialogs_scanned, messages_found)
            VALUES (?, ?, ?)
        ''', (datetime.now().isoformat(), dialogs_scanned, messages_found))

        conn.commit()
        conn.close()

    def get_statistics(self):
        """Получить статистику"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Всего обработанных
        cursor.execute("SELECT COUNT(*) FROM processed_messages WHERE action = 'answered'")
        total_answered = cursor.fetchone()[0]

        # Помечено непрочитанными
        cursor.execute("SELECT COUNT(*) FROM processed_messages WHERE action = 'mark_unread'")
        total_marked = cursor.fetchone()[0]

        # Уникальных диалогов
        cursor.execute("SELECT COUNT(DISTINCT dialog_id) FROM processed_messages")
        unique_dialogs = cursor.fetchone()[0]

        # Всего сканирований
        cursor.execute("SELECT COUNT(*) FROM scan_history")
        total_scans = cursor.fetchone()[0]

        conn.close()

        return {
            'total_answered': total_answered,
            'total_marked': total_marked,
            'unique_dialogs': unique_dialogs,
            'total_scans': total_scans
        }

    def get_last_scan_time(self):
        """Получить время последнего сканирования"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            SELECT scan_time, dialogs_scanned, messages_found
            FROM scan_history
            ORDER BY id DESC LIMIT 1
        ''')

        result = cursor.fetchone()
        conn.close()

        if result:
            return {
                'time': result[0],
                'dialogs_scanned': result[1],
                'messages_found': result[2]
            }
        return None

    def clear_all_history(self):
        """Очистить всю историю"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('DELETE FROM processed_messages')
        cursor.execute('DELETE FROM dialog_tracking')
        cursor.execute('DELETE FROM scan_history')

        conn.commit()
        conn.close()


async def load_messages_web(api_id, api_hash, hours_back=24):
    """Основная функция загрузки для веб-версии"""
    loader = TelegramMessageLoaderWeb(api_id, api_hash)

    connected = await loader.connect()
    if not connected:
        raise Exception("Не удалось подключиться. Требуется авторизация.")

    dialogs = await loader.load_dialogs(hours_back)

    return dialogs, loader
