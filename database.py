import tinydb
from tinydb import where

from functions import getAllFilesFromGD
from config import DB_PATH


db: tinydb.TinyDB


# Инициализация базы данных
def createDB(path: str = DB_PATH) -> tinydb.TinyDB:
    global db
    db = tinydb.TinyDB(path)

    # db.drop_tables()

    # Таблица 'Users':
    #   UserId: int - Берется из бота: message.from_user.id
    #   GDlink: str - Устанавливается командой /set в бота
    db.table('Users')

    # Таблица 'Files'
    #   RootLink: str - ID корневой папки
    #   SubLink: str - Вайл из корневой папки
    db.table('Files')

    return db


# Создание нового пользователя
def createUser(userId: int) -> bool:
    global db
    if db.table('Users').contains(where('UserId') == userId):
        return False
    else:
        # insert into Users (UserId, GDLink)
        # values (:userId, '')
        db.table('Users').insert({'UserId': userId, 'GDlink': ''})
        return True


# Установка значения для пользователя
def setUserGD(userId: int, newLink: str) -> bool:
    global db
    if not db.table('Users').contains(where('UserId') == userId):
        return False
    else:
        # update Users
        # set GDlink = :newLink
        # where UserId = :userId
        idLink = newLink.split('/')[-1]
        db.table('Users').update({'GDlink': idLink}, where('UserId') == userId)
        files = getAllFilesFromGD(idLink)
        for file in files:
            db.table('Files').insert({'RootLink': idLink, 'SubLink': file})
        return True


# Получение GoogleId папки курса
def getUserGD(userId: int) -> str:
    global db
    # select GDlink
    # from Users
    # where UserId = :userId
    return db.table('Users').get(where('UserId') == userId).get('GDlink')


# Получение всех пользователей бота
def getAllUsers() -> list:
    global db
    # select UserId
    # from Users
    return [user_data['UserId'] for user_data in db.table('Users').all()]


# Получение папок всех пользователей
def getActiveFolders() -> list:
    global db
    # select GDlink
    # from Users
    return [folder['GDlink'] for folder in db.table('Users').all()]


# Получение всех корневых папок в БД
def getDBFolders() -> list:
    global db
    # select RootLink
    # from Files
    return [folder['RootLink'] for folder in db.table('Files').all()]


# Получение списка всех файлов в бд
def getDBFiles() -> list:
    global db
    # select SubLink
    # from Files
    return [folder['SubLink'] for folder in db.table('Files')]


# Получение пользователя по его папке
def getUsersByFolder(folder: str) -> list:
    global db
    # select UserId
    # from Users
    # where GDlink = :folder
    return [user_data['UserId'] for user_data in db.table('Users').search(where('GDlink') == folder)]


# Добавление файла 'корневая_папка; путь'
def addFile(folder: str, file: str) -> None:
    global db
    # insert into Files (RootLink, SubLink)
    # values (:folder, :file)
    db.table('Files').insert({'RootLink': folder, 'SubLink': file})
