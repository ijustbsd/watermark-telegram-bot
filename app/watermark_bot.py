# -*- coding: utf-8 -*-
import asyncio
import hashlib
import logging
import os
import subprocess

import aiofiles
import piexif
from aiogram import Bot, Dispatcher, executor, types

logging.basicConfig(level=logging.ERROR)

bot = Bot(token=os.getenv('TOKEN'))
dp = Dispatcher(bot)

watermark_text = os.getenv('WATERMARK')


async def watermark(fname, new_fname, text, color, rotate):
    """Draw watermark and save image."""
    ffmpeg_filter = ':'.join([
        'drawtext=fontfile=Vera_Crouz.ttf',
        f"text='{text}'",
        f'fontcolor={color}@0.45',
        'fontsize=h*0.12',
        f'x=w-tw-h*0.12/6:y=h-th-h*0.12/6,rotate={rotate}'
    ])
    save_path = f'images/out/{color}/{new_fname}'

    p1 = subprocess.Popen(
        f'ffmpeg -i "{fname}" -vf "{ffmpeg_filter}" -y {save_path}',
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
        shell=True
    )

    while True:
        try:
            p1.communicate(timeout=.1)
            break
        except subprocess.TimeoutExpired:
            await asyncio.sleep(1)

    return p1.returncode


def all_files_size():
    """Return the size of all images."""
    size = 0
    for dirpath, _dirnames, filenames in os.walk('images'):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            size += os.path.getsize(fp)
    return size


def md5(path):
    """Calculates the hash of images in chunks, since the picture may not fit into RAM."""
    with open(path, 'rb') as f:
        md5hash = hashlib.md5()
        for chunk in iter(lambda: f.read(4096), b''):
            md5hash.update(chunk)
    return md5hash.hexdigest()


@dp.message_handler(commands=['start', 'help'])
async def send_welcome(message):
    await message.answer('Отправь мне изображение, как документ! Жду ⏳')


@dp.message_handler(content_types=[
    types.ContentType.ANIMATION,
    types.ContentType.DOCUMENT,
    types.ContentType.VIDEO
])
async def send_watermark(message):
    msg_file = message.video if message.content_type == 'video' else message.document
    file_type, file_ext = msg_file.mime_type.split('/')
    file = await bot.get_file(msg_file.file_id)
    downloaded_file = await bot.download_file(file.file_path)
    path = 'images/' + msg_file.file_name + '.' + file_ext
    async with aiofiles.open(path, 'wb') as f:
        await f.write(downloaded_file.read())

    fname = md5(path) + '.' + file_ext
    rotate = 0

    if fname not in os.listdir('images/out/black'):
        if file_type == 'image':
            try:
                exif_dict = piexif.load(path)
            except piexif.InvalidImageDataError:
                exif_dict = {}
            # Если в Exif есть тег Orientation, то поворачиваем изображение
            try:
                orientation = exif_dict['0th'][274]
            except KeyError:
                orientation = None
            rotate_values = {3: 'PI', 6: '3*PI/4', 8: 'PI/2'}
            if orientation in rotate_values:
                rotate = rotate_values[orientation]

    for c in ('black', 'white'):
        code = await watermark(path, fname, watermark_text, c, rotate)
        if code:
            await message.answer('Что-то пошло не так, попробуйте ещё раз 😔')
            return
        wm_file = await aiofiles.open(f'images/out/{c}/{fname}', 'rb')
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
