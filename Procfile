web: . /opt/venv/bin/activate && cd telegram_swiper_web/backend && gunicorn --worker-class=gthread --workers=1 --threads=1 --bind 0.0.0.0:$PORT app:app
