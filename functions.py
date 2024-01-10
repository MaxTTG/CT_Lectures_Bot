import telebot

from config import CT_LECTURES_YT_ID, GOOGLE_SERV_ACC

from googleapiclient.discovery import build, Resource
from google.oauth2 import service_account

gdrive: Resource
youtube: Resource


# Запуск сервисов гугл
def runGoogleServices() -> None:
    runYT()
    runGD()


################################
#     Конвертация id папок     #
# Используется для callback'ов #
################################
folder_link_to_ids = dict()
folder_ids_to_link = dict()


# Преобразование индекса из GD в некоторый внутренний номер
def links_to_ids(links: list) -> list:
    global folder_ids_to_link, folder_link_to_ids
    ids = []
    for link in links:
        try:
            ids.append(folder_link_to_ids[link])
        except KeyError:
            new_id = str(len(folder_link_to_ids))
            folder_link_to_ids[link] = new_id
            folder_ids_to_link[new_id] = link
            ids.append(new_id)
    return ids


# Преобразование некоторого внутреннего номера в индекс GD
def ids_to_links(ids: list) -> list:
    global folder_ids_to_link
    return [folder_ids_to_link.get(id_) for id_ in ids]


################
# Google Drive #
################

# Подключение Google Drive API v3
def runGD() -> None:
    global gdrive
    gdrive_credentials = service_account.Credentials.from_service_account_file(
        'ct-lectures-c1afb70e9aa2.json',
        scopes=['https://www.googleapis.com/auth/drive']
    )
    gdrive = build('drive', 'v3', credentials=gdrive_credentials)


# Если подаётся ярлык, возвращает id настоящего файла/папки; иначе возвращает получаемую ссылку
def getTrueItemId(itemId: str) -> str:
    global gdrive
    temp = gdrive.files().get(fileId=itemId).execute()
    if temp['mimeType'].split('.')[-1] == 'shortcut':
        return gdrive.files().get(fileId=itemId, fields='shortcutDetails(targetId)').execute()['shortcutDetails'][
            'targetId']
    else:
        return itemId


# Получает содержимое папки по индексу GD
def getGDFiles(itemId: str) -> {list, str}:
    global gdrive
    path = getTrueItemId(itemId)
    response = gdrive.files().list(
        q=f'"{path}" in parents',
        fields='files(id, mimeType, name)'
    ).execute()

    items = []
    for item in response['files']:
        item_id = item['id']
        item_type = item['mimeType'].split('.')[-1]
        item_title = item['name']
        items.append({'title': item_title, 'id': item_id, 'type': item_type})

    return items


# Получение имён файлов в GD папке по id
def getGDFile(itemId: str) -> {list, str}:
    global gdrive
    return gdrive.files().get(fileId=itemId, fields='name').execute()['name']


# Сборка сообщения для отправки: текст и все кнопки
def getGDMessage(itemIdTrace: list) -> {str, telebot.types.InlineKeyboardMarkup}:
    itemId = itemIdTrace[-1]
    items = getGDFiles(ids_to_links([itemId])[0])
    message_text = ''
    inline_markup = telebot.types.InlineKeyboardMarkup(row_width=1)
    if items:
        for item in items:
            if item['type'] in {'folder', 'shortcut'}:
                cbdata = f'gd {" ".join(itemIdTrace)} {links_to_ids([item["id"]])[0]}'
                inline_markup.add(
                    telebot.types.InlineKeyboardButton(
                        text=item['title'],
                        callback_data=cbdata
                    )
                )
            else:
                message_text += f'<a href="https://drive.google.com/file/d/{item["id"]}">{item["title"]}</a>\n\n'
    else:
        message_text = 'В вашей папке ничего не найдено 😔'
    if not message_text:
        message_text = 'В папке файлов нет :('
    if len(itemIdTrace) > 1:
        inline_markup.add(
            telebot.types.InlineKeyboardButton(
                text='Назад',
                callback_data=f'gd {" ".join(itemIdTrace[:-1])}'
            )
        )
    return message_text, inline_markup


# Получение абсолютно всех файлов с путями из папки folder
def getAllFilesFromGD(folder: str) -> list:
    files = getGDFiles(folder)
    filesIds = []
    files = sorted(files, key=lambda x: x['type'])

    for file in files:
        if file['type'] not in ['shortcut', 'folder']:
            filesIds.append(file['id'])
        else:
            subfiles = [folder + '/' + f for f in getAllFilesFromGD(file['id'])]
            filesIds.extend(subfiles)

    return filesIds


###########
# YouTube #
###########
# Подключение YouTube data API v3
def runYT() -> None:
    global youtube
    youtube_credentials = service_account.Credentials.from_service_account_file(
        'ct-lectures-c1afb70e9aa2.json',
        scopes=['https://www.googleapis.com/auth/youtube.force-ssl']
    )
    youtube = build('youtube', 'v3', credentials=youtube_credentials)


# Поиск на YT канале по запросу prompt
def searchYT(prompt: str) -> list:
    global youtube
    response = youtube.search().list(
        part='snippet',
        channelId=CT_LECTURES_YT_ID,
        type='video,playlist',
        q=prompt,
        order='title',
        maxResults=50
    ).execute()

    items = []
    for item in response.get('items', []):
        item_id = item.get('id', {}).get('videoId', None)

        if item_id:
            item_title = item['snippet']['title']
            item_url = f'https://www.youtube.com/watch?v={item_id}'
            items.append({'title': item_title, 'url': item_url, 'type': 'video'})

    for item in response.get('items', []):
        item_id = item.get('id', {}).get('playlistId', None)

        if item_id:
            item_title = item['snippet']['title']
            item_url = f'https://www.youtube.com/playlist?list={item_id}'
            items.append({'title': item_title, 'url': item_url, 'type': 'playlist'})

    return items
