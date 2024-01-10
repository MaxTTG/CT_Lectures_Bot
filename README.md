*Lectures Bot*

Телеграм-бот для CT Lectures

Выполнил: <b>Таразанов Максим М4139<b>

# 1) Файлы
1.1) [main.py](main.py)
    
    Точка входа; логика работы бота прописана здесь

1.2) [functions.py](functions.py)

    Файл представляет собой слой для работы с Google Drive и YouTube data API

1.3) [database.py](database.py)

    Файл представляет собой слой для работы с базой данных; используется TinyDB

1.4) [config.py](config.py)

    Содержит некоторые переменные и константы; перед началом работы необходимо установить всё соответственно коментариям

1.5) [db.json](db.json)
    
    Файл базы данных, необходимый для работы бота

1.6) [google_serv_acc_path.json (guide link)](https://cloud.google.com/iam/docs/service-account-overview)

    Файл профиля сервисного аккаунта Google; необходим для работы Google-сервисов

# 2) Для запуска требуется:

2.1) Сделать бота с помощью [BotFather](https://core.telegram.org/bots/tutorial)

2.2) [Сделать сервисный аккаунт гугл](https://cloud.google.com/iam/docs/service-account-overview) и добавить полученый файл

2.3) Заменить [соответствующие константы](config.py#L2) в config.py