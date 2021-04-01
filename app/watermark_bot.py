# -*- coding: utf-8 -*-
import hashlib
import io
import logging
import os

import aiofiles
import piexif
from aiogram import Bot, Dispatcher, executor, types
from PIL import Image, ImageDraw, ImageEnhance, ImageFont, ImageSequence

logging.basicConfig(level=logging.ERROR)

bot = Bot(token=os.getenv('TOKEN'))
dp = Dispatcher(bot)

watermark_text = os.getenv('WATERMARK')


def watermark(img, new_fname, text, color):
    '''
    Рисует водяной знак и сохраняет изображение.
    '''
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


def gif_watermark(img, new_fname, text, color):
    '''
    Рисует водяной знак на GIF-ке и сохраняет изображение.
    '''
    frames = []
    for frame in ImageSequence.Iterator(img):
        frame = frame.convert('RGBA')
        wm = Image.new('RGBA', frame.size, (0, 0, 0, 0))
        fontsize = max(frame.size[1] // 100 * 12, 24)
        font = ImageFont.truetype('Vera_Crouz.ttf', fontsize)
        indent = fontsize // 6
        w, h = font.getsize(text)
        text_position = (frame.size[0] - w - indent, frame.size[1] - h - indent)
        draw = ImageDraw.Draw(wm)
        draw.text(text_position, text, font=font, fill=color)
        del draw
        frame = Image.alpha_composite(frame, wm)
        b = io.BytesIO()
        frame.save(b, format='GIF')
        frame = Image.open(b)
        frames.append(frame)
    out_path = 'images/out/{}/{}'.format(color, new_fname)
    frames[0].save(out_path, save_all=True, append_images=frames[1:])


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


@dp.message_handler(commands=['start', 'help'])
async def send_welcome(message):
    await message.answer('Отправь мне изображение, как документ! Жду ⏳')


@dp.message_handler(content_types=types.ContentType.DOCUMENT)
async def send_watermark(message):
    '''
    Сохраняет png и jpeg документы. Обрабатывает, кэширует, отправляет обратно.
    '''
    if message.document.mime_type not in ('image/png', 'image/jpeg', 'image/gif'):
        await message.reply('Сорри, я умею только JPG, PNG и GIF 😕')
        return
    file = await bot.get_file(message.document.file_id)
    downloaded_file = await bot.download_file(file.file_path)
    path = 'images/' + message.document.file_name
    async with aiofiles.open(path, 'wb') as f:
        await f.write(downloaded_file.read())

    is_gif = message.document.mime_type == 'image/gif'
    fname = md5(path) + ('.gif' if is_gif else '.jpg')

    if fname not in os.listdir('images/out/black'):
        if is_gif:
            image = Image.open(path)
        else:
            image = Image.open(path).convert('RGBA')

        # Если в Exif есть тег Orientation, то поворачиваем изображение
        try:
            exif_dict = piexif.load(image.info['exif'])
            orientation = exif_dict['0th'][274]
        except KeyError:
            orientation = None
        rotate_values = {3: 180, 6: 270, 8: 90}
        if orientation in rotate_values:
            image = image.rotate(rotate_values[orientation], expand=True)

        if is_gif:
            gif_watermark(image, fname, watermark_text, 'black')
            gif_watermark(image, fname, watermark_text, 'white')
        else:
            watermark(image, fname, watermark_text, 'black')
            watermark(image, fname, watermark_text, 'white')

    for i in ('black', 'white'):
        wm_file = await aiofiles.open(f'images/out/{i}/{fname}', 'rb')
        await message.answer_document(wm_file)


@dp.message_handler(commands=['size'])
async def send_info(message):
    data_size = round(all_files_size() / 1048576, 2)
    await message.answer('Размер всех фотографий: {} МБ'.format(data_size))


@dp.message_handler()
async def send_idk(message):
    await message.reply('Ну и что мне с этим делать?')


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)