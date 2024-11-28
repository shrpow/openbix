# farmbix

SaaS-решение для автопрокачки аккаунтов в криптоскамине от Binance — Moonbix.

Тулза не выстрелила, но это не мешает мне считать её одним из самых классных проектов в моём портфолио =)

## деплой

### автоматический (CI/CD)

Настраиваем секреты, создаём на сервере юзера с доступом к докеру и ssh, помещаем исходники в `/home/deploy/farmbix`, заполняем `.env`ы и нажимаем кнопочку запуска в панели экшенов

### ручной (тестовый)

Всё сводится к заполнению `.env`ов и запуску одной команды

```
docker compose up -d --build
```

### ручной (разработка)

Разворачиваем Mongo DB, заполняем `.env`ы и запускаем `__main__.py` нужных сервисов