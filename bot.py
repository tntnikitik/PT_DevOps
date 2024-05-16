import logging
import re
import paramiko
import os
import psycopg2
from psycopg2 import Error
from pathlib import Path
from telegram import Update, ForceReply
from dotenv import load_dotenv
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, ConversationHandler

KEY = 1



connection = None
load_dotenv()

token = os.getenv('TOKEN')
host = os.getenv('RM_HOST')
port = os.getenv('RM_PORT')
username = os.getenv('RM_USER')
password = os.getenv('RM_PASSWORD')
host_db = os.getenv('DB_HOST')
port_db = os.getenv('DB_PORT')
username_db = os.getenv('DB_USER')
password_db = os.getenv('DB_PASSWORD')
database = os.getenv('DB_DATABASE')
db_repl_user = os.getenv('DB_REPL_USER')

logging.basicConfig(
    filename='log.txt', format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

logger = logging.getLogger(__name__)


def start(update: Update, context):
    user = update.effective_user
    update.message.reply_text(f'Привет {user.full_name}!')


def helpCommand(update: Update, context):
    update.message.reply_text('Help!')


def findPhoneNumbersCommand(update: Update, context):
    update.message.reply_text('Введите текст для поиска телефонных номеров: ')

    return 'find_phone_number'

def findEmailCommand(update: Update, context):
    update.message.reply_text('Введите текст для поиска Email-адресов: ')

    return 'find_email'

def verifyPasswordCommand(update: Update, context):
    update.message.reply_text('Введите пароль для проверки: ')

    return 'verify_password'

def getAptListCommand(update: Update, context):
    update.message.reply_text('Введите "ALL", чтобы вывести список всех пакетов\nИЛИ\nВведите имя пакета, чтобы получить информацию о нем')
    return 'get_apt_list'


def find_phone_number (update: Update, context):
    user_input = update.message.text

    phoneNumRegex = re.compile(r'(?:\+7|8)(?:(?:\(|\ \(|)\d{3}(?:\)|\)\ |)|[- ]?\d{3}[- ]?)(?:\d{3}[- ]?)(?:\d{2}[- ]?)(?:\d{2})')
    phoneNumberList = phoneNumRegex.findall(user_input)
    uniquePhones = []
    if not phoneNumberList:
        update.message.reply_text('Телефонные номера не найдены')
        return ConversationHandler.END
    else:
        phoneNumbers = ''
        for i in range(len(phoneNumberList)):
            if phoneNumberList[i] not in phoneNumbers:
                phoneNumbers += f'{i+1}. {phoneNumberList[i]}\n'
                uniquePhones.append(phoneNumberList[i])
        context.user_data[KEY] = uniquePhones
        update.message.reply_text(phoneNumbers + '\n/yes, чтобы записать\n/no для отказа')
        return 'write_confirm'
    
def write_confirmed_phones (update: Update, context):
    plist = context.user_data.get(KEY, [])
    if len(plist) > 0:
        connection = psycopg2.connect(user=username_db,
                                      password=password_db,
                                      host=host_db,
                                      port=port_db,
                                      database=database)
    
        try:
            cursor = connection.cursor()
            for phone_number in plist:
                cursor.execute("INSERT INTO phones (phone) VALUES " + "('" + phone_number + "')" + ";")
            connection.commit()
            logging.info("Команда успешно выполнена")
            update.message.reply_text('Успешная запись!')
        except (Exception, Error) as error:
            logging.error("Ошибка при работе с PostgreSQL: %s", error)
            update.message.reply_text('Ошибка записи!')
        finally:
            if connection is not None:
                cursor.close()
                connection.close()
            logging.info("Соединение с PostgreSQL закрыто")
            context.user_data[KEY] = None
            return ConversationHandler.END
    else:
        context.user_data[KEY] = None
        return ConversationHandler.END


def write_cancelled(update: Update, context):
    context.user_data[KEY] = None
    update.message.reply_text('Отказ от записи')
    return ConversationHandler.END

def find_email (update: Update, context):
    user_input = update.message.text

    emailRegex = re.compile(r'[a-zA-Z0-9._-]+@[a-zA-Z0-9-.]+\.[a-zA-Z]{2,}')
    emailList = emailRegex.findall(user_input)
    uniqueEmails = []
    if not emailList:
        update.message.reply_text('Email-адреса не найдены:')
        return ConversationHandler.END
    else:
        emails = ''
        for i in range(len(emailList)):
            if emailList[i] not in emails:
                emails += f'{i+1}. {emailList[i]}\n'
                uniqueEmails.append(emailList[i])
        context.user_data[KEY] = uniqueEmails
        update.message.reply_text(emails + '\n/yes, чтобы записать\n/no для отказа')
        return 'write_confirm'
    
def write_confirmed_emails (update: Update, context):
    elist = context.user_data.get(KEY, [])
    if len(elist) > 0:
        connection = psycopg2.connect(user=username_db,
                                      password=password_db,
                                      host=host_db,
                                      port=port_db,
                                      database=database)
    
        try:
            cursor = connection.cursor()
            for email_number in elist:
                cursor.execute("INSERT INTO emails (email) VALUES " + "('" + email_number + "')" + ";")
            connection.commit()
            logging.info("Команда успешно выполнена")
            update.message.reply_text('Успешная запись!')
        except (Exception, Error) as error:
            logging.error("Ошибка при работе с PostgreSQL: %s", error)
            update.message.reply_text('Ошибка записи!')
        finally:
            if connection is not None:
                cursor.close()
                connection.close()
            logging.info("Соединение с PostgreSQL закрыто")
            context.user_data[KEY] = None
            return ConversationHandler.END
            
    else:
        context.user_data[KEY] = None
        return ConversationHandler.END
    

def verify_password (update: Update, context):
    user_input = update.message.text

    passRegex = r'(?=.*[a-z])(?=.*[A-Z])(?=.*[0-9])(?=.*[!@#$%^&*])[0-9a-zA-Z!@#$%^&*()]{8,}'
    
    if re.match(passRegex, user_input):
        update.message.reply_text('Пароль сложный')
    else:
        update.message.reply_text('Пароль простой')

    return ConversationHandler.END

def sshConnect(command):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(hostname=host, username=username, password=password, port=port)
    stdin, stdout, stderr = client.exec_command(command)
    data = stdout.read() + stderr.read()
    client.close()
    data = str(data).replace('\\n', '\n').replace('\\t', '\t')[2:-1]
    return data
def sshConnectMaster(command):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(hostname=host_db, username="master", password="master", port=port)
    stdin, stdout, stderr = client.exec_command(command)
    data = stdout.read() + stderr.read()
    client.close()
    data = str(data).replace('\\n', '\n').replace('\\t', '\t')[2:-1]
    return data

def get_release (update: Update, context):
    update.message.reply_text(sshConnect('lsb_release -a'))
    return ConversationHandler.END

def get_uname (update: Update, context):
    update.message.reply_text(sshConnect('uname -a'))
    return ConversationHandler.END

def get_uptime (update: Update, context):
    update.message.reply_text(sshConnect('uptime -p'))
    return ConversationHandler.END

def get_df (update: Update, context):
    update.message.reply_text(sshConnect('df -ah'))
    return ConversationHandler.END

def get_free (update: Update, context):
    update.message.reply_text(sshConnect('free -wh'))
    return ConversationHandler.END

def get_mpstat (update: Update, context):
    update.message.reply_text(sshConnect('mpstat -P ALL'))
    return ConversationHandler.END

def get_w (update: Update, context):
    update.message.reply_text(sshConnect('w'))
    return ConversationHandler.END

def get_auths (update: Update, context):
    update.message.reply_text(sshConnect('tail /var/log/auth.log'))
    return ConversationHandler.END

def get_critical (update: Update, context):
    update.message.reply_text(sshConnect('journalctl -p 2 | tail -n5'))
    return ConversationHandler.END

def get_ps (update: Update, context):
    update.message.reply_text(sshConnect('ps -A u | head -n20'))
    return ConversationHandler.END

def get_ss (update: Update, context):
    update.message.reply_text(sshConnect('ss -a | head -n20'))
    return ConversationHandler.END

def get_apt_list (update: Update, context):
    user_input = update.message.text
    if (user_input=='ALL'):
        update.message.reply_text(sshConnect('apt list --installed | head -n20'))
    else:
        AntiRCERegex = re.compile(r'^[a-z0-9.-]+')
        secured = AntiRCERegex.search(user_input)
        update.message.reply_text(sshConnect('apt show ' + secured.group()))
    return ConversationHandler.END

def get_services (update: Update, context):
    update.message.reply_text(sshConnect('systemctl list-units --state=running --no-pager'))
    return ConversationHandler.END

def get_repl_logs (update: Update, context):
    update.message.reply_text(sshConnectMaster('cat /var/log/postgresql/postgresql-15-main.log | grep repl_user | tail -n20'))
    return ConversationHandler.END

def get_phone_numbers (update: Update, context):
    try:
        connection = psycopg2.connect(user=username_db,
                                      password=password_db,
                                      host=host_db,
                                      port=port_db,
                                      database=database)

        cursor = connection.cursor()
        cursor.execute("SELECT * FROM phones;")
        data = cursor.fetchall()
        for row in data:
            update.message.reply_text(row)
            #print(row)  
        logging.info("Получение phones - УСПЕХ")
    except (Exception, Error) as error:
        logging.error("Ошибка при работе с PostgreSQL: %s", error)
    finally:
        if connection is not None:
            cursor.close()
            connection.close()
    return ConversationHandler.END

def get_emails (update: Update, context):
    try:
        connection = psycopg2.connect(user=username_db,
                                      password=password_db,
                                      host=host_db,
                                      port=port_db,
                                      database=database)
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM emails;")
        data = cursor.fetchall()
        for row in data:
            update.message.reply_text(row) 
            #print(row) 
        logging.info("Получение emalis - УСПЕХ")
    except (Exception, Error) as error:
        logging.error("Ошибка при работе с PostgreSQL: %s", error)
    finally:
        if connection is not None:
            cursor.close()
            connection.close()
    return ConversationHandler.END


def main():
    updater = Updater(token, use_context=True)

    dp = updater.dispatcher

    convHandlerFindPhoneNumbers = ConversationHandler(
        entry_points=[CommandHandler('find_phone_number', findPhoneNumbersCommand)],
        states={
            'find_phone_number': [MessageHandler(Filters.text & ~Filters.command, find_phone_number)],
            'write_confirm': [CommandHandler('yes', write_confirmed_phones), CommandHandler('no', write_cancelled)]
        },
        fallbacks=[]
    )

    convHandlerFindEmail = ConversationHandler(
        entry_points=[CommandHandler('find_email', findEmailCommand)],
        states={
            'find_email': [MessageHandler(Filters.text & ~Filters.command, find_email)],
            'write_confirm': [CommandHandler('yes', write_confirmed_emails), CommandHandler('no', write_cancelled)]
        },
        fallbacks=[]
    )

    convHandlerVerifyPassword = ConversationHandler(
        entry_points=[CommandHandler('verify_password', verifyPasswordCommand)],
        states={
            'verify_password': [MessageHandler(Filters.text & ~Filters.command, verify_password)],
        },
        fallbacks=[]
    )

    convHandlerGetRelease = ConversationHandler(
        entry_points=[CommandHandler('get_release', get_release)],
        states={
            'get_release': [MessageHandler(Filters.text & ~Filters.command, get_release)],
        },
        fallbacks=[]
    )

    convHandlerGetUname = ConversationHandler(
        entry_points=[CommandHandler('get_uname', get_uname)],
        states={
            'get_uname': [MessageHandler(Filters.text & ~Filters.command, get_uname)],
        },
        fallbacks=[]
    )

    convHandlerGetUptime = ConversationHandler(
        entry_points=[CommandHandler('get_uptime', get_uptime)],
        states={
            'get_uptime': [MessageHandler(Filters.text & ~Filters.command, get_uptime)],
        },
        fallbacks=[]
    )

    convHandlerGetDf = ConversationHandler(
        entry_points=[CommandHandler('get_df', get_df)],
        states={
            'get_df': [MessageHandler(Filters.text & ~Filters.command, get_df)],
        },
        fallbacks=[]
    )

    convHandlerGetFree = ConversationHandler(
        entry_points=[CommandHandler('get_free', get_free)],
        states={
            'get_free': [MessageHandler(Filters.text & ~Filters.command, get_free)],
        },
        fallbacks=[]
    )

    convHandlerGetMpstat = ConversationHandler(
        entry_points=[CommandHandler('get_mpstat', get_mpstat)],
        states={
            'get_mpstat': [MessageHandler(Filters.text & ~Filters.command, get_mpstat)],
        },
        fallbacks=[]
    )

    convHandlerGetW = ConversationHandler(
        entry_points=[CommandHandler('get_w', get_w)],
        states={
            'get_w': [MessageHandler(Filters.text & ~Filters.command, get_w)],
        },
        fallbacks=[]
    )

    convHandlerGetAuths = ConversationHandler(
        entry_points=[CommandHandler('get_auths', get_auths)],
        states={
            'get_auths': [MessageHandler(Filters.text & ~Filters.command, get_auths)],
        },
        fallbacks=[]
    )

    convHandlerGetCritical = ConversationHandler(
        entry_points=[CommandHandler('get_critical', get_critical)],
        states={
            'get_critical': [MessageHandler(Filters.text & ~Filters.command, get_critical)],
        },
        fallbacks=[]
    )

    convHandlerGetPs = ConversationHandler(
        entry_points=[CommandHandler('get_ps', get_ps)],
        states={
            'get_ps': [MessageHandler(Filters.text & ~Filters.command, get_ps)],
        },
        fallbacks=[]
    )

    convHandlerGetSs = ConversationHandler(
        entry_points=[CommandHandler('get_ss', get_ss)],
        states={
            'get_ss': [MessageHandler(Filters.text & ~Filters.command, get_ss)],
        },
        fallbacks=[]
    )

    convHandlerGetAptList = ConversationHandler(
        entry_points=[CommandHandler('get_apt_list', getAptListCommand)],
        states={
            'get_apt_list': [MessageHandler(Filters.text & ~Filters.command, get_apt_list)],
        },
        fallbacks=[]
    )

    convHandlerGetServices = ConversationHandler(
        entry_points=[CommandHandler('get_services', get_services)],
        states={
            'get_services': [MessageHandler(Filters.text & ~Filters.command, get_services)],
        },
        fallbacks=[]
    )

    convHandlerGetReplLogs = ConversationHandler(
        entry_points=[CommandHandler('get_repl_logs', get_repl_logs)],
        states={
            'get_repl_logs': [MessageHandler(Filters.text & ~Filters.command, get_repl_logs)],
        },
        fallbacks=[]
    )
    
    convHandlerGetEmails = ConversationHandler(
        entry_points=[CommandHandler('get_emails', get_emails)],
        states={
            'get_emails': [MessageHandler(Filters.text & ~Filters.command, get_emails)],
        },
        fallbacks=[]
    )

    convHandlerGetPhoneNumbers = ConversationHandler(
        entry_points=[CommandHandler('get_phone_numbers', get_phone_numbers)],
        states={
            'get_phone_numbers': [MessageHandler(Filters.text & ~Filters.command, get_phone_numbers)],
        },
        fallbacks=[]
    )
		
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("help", helpCommand))
    dp.add_handler(convHandlerFindPhoneNumbers)
    dp.add_handler(convHandlerFindEmail)
    dp.add_handler(convHandlerVerifyPassword)
    dp.add_handler(convHandlerGetRelease)
    dp.add_handler(convHandlerGetUname)
    dp.add_handler(convHandlerGetUptime)
    dp.add_handler(convHandlerGetDf)
    dp.add_handler(convHandlerGetFree)
    dp.add_handler(convHandlerGetMpstat)
    dp.add_handler(convHandlerGetW)
    dp.add_handler(convHandlerGetAuths)
    dp.add_handler(convHandlerGetCritical)
    dp.add_handler(convHandlerGetPs)
    dp.add_handler(convHandlerGetSs)
    dp.add_handler(convHandlerGetAptList)
    dp.add_handler(convHandlerGetServices)
    dp.add_handler(convHandlerGetReplLogs)
    dp.add_handler(convHandlerGetEmails)
    dp.add_handler(convHandlerGetPhoneNumbers)
		
		
    updater.start_polling()

    updater.idle()


if __name__ == '__main__':
    main()
