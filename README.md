# Инструкция
Протестировано на: Ubuntu 22.04

Тестирование проводилось на двух машинах:
1. Машина, где разворачивается контейнеризованное приложение.
2. Машина, мониторинг которой производится

На машине, на которой будет выполняться контейнеризация и разворачивание, необходимо:
1. Установить docker и docker-compose
2. Клонировать ветку docker этого репозитория с помощью команды git clone --branch docker https://github.com/tntnikitik/PT_DevOps
3. Перейти в папку клонированного репозитория.
4. В этой папке создать файл ```.env``` согласно шаблону, в который нужно внести значения для тестирования.
5. Далее в этой же папке собрать образы контейнеров с помощью команд: ```docker build -t bot_image ./bot```, ```docker build -t db_image ./db```, ```docker build -t db_repl_image ./db_repl```
7. Поднять контейнеры при помощи команды ```docker-compose up -d```
   
На машине, мониторинг которой выполняется, достаточно проверить выдачу ip-адреса и наличие сервиса ssh.

# Шаблон .env:
```
TOKEN = 6409912882:AAHUzX9_bTrw4G7aGM4C2qslhsp8RnvN5FE
RM_HOST = <ip-адрес машины, которую мониторим>
RM_PORT = 22 #В случае, если порт ssh нестандартный - изменить на свой
RM_USER = <user, под которым выполняется подключение>
RM_PASSWORD = <пароль пользователя, под которым выполняется подключение>
DB_USER = postgres        #не изменять
DB_PASSWORD = Qq12345
DB_HOST = db              #не изменять
DB_PORT = 5432            #не изменять
DB_DATABASE = db_bot      
DB_REPL_USER = repl_user  #не изменять
DB_REPL_PASSWORD = qwerty
DB_REPL_HOST = db_repl    #не изменять
DB_REPL_PORT = 5432       #не изменять
```
