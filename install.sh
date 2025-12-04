#!/bin/bash

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "======================================="
echo "  УСТАНОВКА TELEGRAM УВЕДОМЛЕНИЙ"
echo "======================================="
echo ""

# Определить текущую директорию
INSTALL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$INSTALL_DIR"

echo "Директория установки: $INSTALL_DIR"
echo ""

# Установка зависимостей
echo -e "${YELLOW}Шаг 1/4: Установка зависимостей...${NC}"
pip3 install -r requirements.txt
if [ $? -ne 0 ]; then
    echo -e "${RED}Ошибка установки зависимостей!${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Зависимости установлены${NC}"
echo ""

# Настройка Telegram
echo -e "${YELLOW}Шаг 2/4: Настройка Telegram API${NC}"
echo ""

if [ -f "telegram_config.json" ]; then
    echo -e "${GREEN}Конфигурация уже существует!${NC}"
    read -p "Перенастроить? (y/n): " reconfigure
    if [ "$reconfigure" != "y" ]; then
        echo "Используем существующую конфигурацию"
    else
        rm -f telegram_config.json
    fi
fi

if [ ! -f "telegram_config.json" ]; then
    echo "Получите API credentials:"
    echo "1. Откройте https://my.telegram.org"
    echo "2. Войдите с номером телефона"
    echo "3. Перейдите в 'API development tools'"
    echo "4. Создайте приложение"
    echo ""
    read -p "API ID: " api_id
    read -p "API Hash: " api_hash

    # Создать конфигурацию
    cat > telegram_config.json <<EOF
{
  "api_id": "$api_id",
  "api_hash": "$api_hash"
}
EOF
    echo -e "${GREEN}✓ Конфигурация сохранена${NC}"
fi
echo ""

# Определить ОС и создать сервис
echo -e "${YELLOW}Шаг 3/4: Настройка автозапуска...${NC}"

# Проверка ОС
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    # Linux - systemd
    echo "Обнаружена система: Linux"

    # Создать systemd сервис
    SERVICE_FILE="$HOME/.config/systemd/user/telegram-notifications.service"
    mkdir -p "$HOME/.config/systemd/user"

    cat > "$SERVICE_FILE" <<EOF
[Unit]
Description=Telegram Desktop Notifications
After=network.target

[Service]
Type=simple
WorkingDirectory=$INSTALL_DIR
ExecStart=/usr/bin/python3 $INSTALL_DIR/telegram_desktop_notifications.py
Restart=always
RestartSec=10

[Install]
WantedBy=default.target
EOF

    # Включить и запустить сервис
    systemctl --user daemon-reload
    systemctl --user enable telegram-notifications.service
    systemctl --user start telegram-notifications.service

    echo -e "${GREEN}✓ Systemd сервис создан и запущен${NC}"
    echo ""
    echo "Управление сервисом:"
    echo "  Статус:  systemctl --user status telegram-notifications"
    echo "  Стоп:    systemctl --user stop telegram-notifications"
    echo "  Старт:   systemctl --user start telegram-notifications"
    echo "  Логи:    journalctl --user -u telegram-notifications -f"

elif [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS - launchd
    echo "Обнаружена система: macOS"

    PLIST_FILE="$HOME/Library/LaunchAgents/com.telegram.notifications.plist"

    cat > "$PLIST_FILE" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.telegram.notifications</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/bin/python3</string>
        <string>$INSTALL_DIR/telegram_desktop_notifications.py</string>
    </array>
    <key>WorkingDirectory</key>
    <string>$INSTALL_DIR</string>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>$HOME/Library/Logs/telegram-notifications.log</string>
    <key>StandardErrorPath</key>
    <string>$HOME/Library/Logs/telegram-notifications-error.log</string>
</dict>
</plist>
EOF

    # Загрузить сервис
    launchctl unload "$PLIST_FILE" 2>/dev/null
    launchctl load "$PLIST_FILE"

    echo -e "${GREEN}✓ LaunchAgent создан и запущен${NC}"
    echo ""
    echo "Управление сервисом:"
    echo "  Стоп:    launchctl unload $PLIST_FILE"
    echo "  Старт:   launchctl load $PLIST_FILE"
    echo "  Логи:    tail -f ~/Library/Logs/telegram-notifications.log"

else
    echo -e "${YELLOW}Автозапуск не настроен (неизвестная ОС)${NC}"
    echo "Запускайте вручную: python3 telegram_desktop_notifications.py"
fi

echo ""

# Первый запуск для настройки канала
echo -e "${YELLOW}Шаг 4/4: Первичная настройка${NC}"
echo ""
echo "Сейчас откроется интерактивная настройка для:"
echo "  - Авторизации в Telegram"
echo "  - Выбора канала для мониторинга"
echo ""
read -p "Нажмите Enter для продолжения..."

# Временно остановить сервис для первичной настройки
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    systemctl --user stop telegram-notifications.service
elif [[ "$OSTYPE" == "darwin"* ]]; then
    launchctl unload "$PLIST_FILE" 2>/dev/null
fi

# Запустить настройку
python3 telegram_desktop_notifications.py

# Перезапустить сервис
echo ""
echo -e "${YELLOW}Перезапуск сервиса...${NC}"
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    systemctl --user start telegram-notifications.service
    echo -e "${GREEN}✓ Сервис запущен${NC}"
elif [[ "$OSTYPE" == "darwin"* ]]; then
    launchctl load "$PLIST_FILE"
    echo -e "${GREEN}✓ Сервис запущен${NC}"
fi

echo ""
echo "======================================="
echo -e "${GREEN}  ✓ УСТАНОВКА ЗАВЕРШЕНА!${NC}"
echo "======================================="
echo ""
echo "Система настроена и работает в фоне!"
echo ""
echo "Теперь при получении сообщений из канала"
echo "будут появляться обязательные уведомления."
echo ""
echo "Проверка: каждые 30 минут"
echo ""
