# -*- coding: utf-8 -*-
import os
import hashlib
import telebot
import piexif
from PIL import Image, ImageFont, ImageDraw, ImageEnhance

bot = telebot.TeleBot('TOKEN')


def watermark(img, new_fname, color):
    '''
    Рисует водяной знак и сохраняет изображение.
    '''
    text = '@ijustkate_'
    wm = Image.new('RGBA', img.size, (0, 0, 0, 0))
    fontsize = img.size[1] // 100 * 12
    font = ImageFont.truetype('Vera_Crouz.ttf', fontsize)
    indent = fontsize // 6
    w, h = font.getsize(text)
    text_position = (img.size[0] - w - indent, img.size[1] - h - indent)
    draw = ImageDraw.Draw(wm, 'RGBA')
    draw.text(text_position, text, font=font, fill=color)
    alpha = wm.split()[3]
    alpha = ImageEnhance.Brightness(alpha).enhance(0.45)
    wm.putalpha(alpha)
    out_path = 'images/out/{}/{}'.format(color, new_fname)
    Image.composite(wm, img, wm).save(out_path, 'JPEG')


def all_files_size():
    '''
    Считает размер всех изображений.
    '''
    size = 0
    for dirpath, _dirnames, filenames in os.walk('images'):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            size += os.path.getsize(fp)
    return size


def md5(path):
    '''
    Считает хэш изображений по кускам, ибо картинка может не влазить в RAM.
    '''
    with open(path, 'rb') as f:
        md5hash = hashlib.md5()
        for chunk in iter(lambda: f.read(4096), b''):
            md5hash.update(chunk)
    return md5hash.hexdigest()


@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.send_message(message.chat.id, 'Отправь мне изображение, как документ! Жду ⏳')


@bot.message_handler(content_types=['document'])
def send_watermark(message):
    '''
    Сохраняет png и jpeg документы. Обрабатывает, кэширует, отправляет обратно.
    '''
    if message.document.mime_type not in ('image/png', 'image/jpeg'):
        bot.reply_to(message, 'Сорри, я умею только JPG и PNG 😕')
        return
    file = bot.get_file(message.document.file_id)
    downloaded_file = bot.download_file(file.file_path)
    path = 'images/' + message.document.file_name
    with open(path, 'wb') as f:
        f.write(downloaded_file)

    fname = md5(path) + '.jpg'

    if fname not in os.listdir('images/out/black'):
        image = Image.open(path).convert('RGB')

        # Если в Exif есть тег Orientation, то поворачиваем изображение
        try:
            exif_dict = piexif.load(image.info['exif'])
            orientation = exif_dict['0th'][274]
        except KeyError:
            orientation = None
        rotate_values = {3: 180, 6: 270, 8: 90}
        if orientation in rotate_values:
            image = image.rotate(rotate_values[orientation], expand=True)

        watermark(image, fname, 'black')
        watermark(image, fname, 'white')

    for i in ('black', 'white'):
        document = open('images/out/{}/{}'.format(i, fname), 'rb')
        bot.send_document(message.chat.id, document)


@bot.message_handler(commands=['size'])
def send_info(message):
    data_size = round(all_files_size() / 1048576, 2)
    bot.send_message(message.chat.id, 'Размер всех фотографий: {} МБ'.format(data_size))


@bot.message_handler(func=lambda message: True)
def echo_all(message):
    bot.reply_to(message, 'Ну и что мне с этим делать?')


bot.polling()
