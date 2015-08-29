#!/usr/bin/env python
# -*- coding: utf-8 -*-

import StringIO
import os
import time
import shutil
import csv

from xhtml2pdf import pisa
from jinja2 import Template
import qrcode
from PIL import Image
from PIL import ImageDraw

from config import config

def load_tasks_from_csv():
    all_tasks = []
    with open('tasks.csv') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            task = {
                'id': row[config['fields']['id']],
                'project': row[config['fields']['project']],
                'title': unicode(row[config['fields']['title']], 'utf-8'),
                'importance': int(row[config['fields']['importance']])
            }
            all_tasks.append(task)

    higher = max(map(lambda one_of: one_of['importance'], all_tasks))

    one_percent = higher / 100.0
    for one_of in all_tasks:
        one_of['stars'] = round(one_of['importance'] / one_percent, 2)

    all_tasks.sort(key=lambda one_of: one_of['importance'], reverse=True)
    return list(chunks(all_tasks, 3))


def process_template(to_process):
    with open('sticker.html', 'r') as sticker:
        data = sticker.read().replace('\n', '')
        return Template(unicode(data, 'utf-8')).render(tasks=to_process)


def convert_html_to_pdf(source):
    output_filename = 'tmp/out/stickers_{}_{}.pdf' \
        .format(time.strftime('%d-%m-%y'), time.strftime('%X'))

    result_file = open(output_filename, 'w+b')

    pisa.CreatePDF(
        StringIO.StringIO(source.encode('utf-8')),
        encoding='utf-8',
        dest=result_file)

    result_file.close()
    return os.getcwd() + result_file.name


def generate_qrs(host_name, tasks_to_write):
    for page in tasks_to_write:
        for task in page:
            file_name = 'tmp/img/{}-qr.png'.format(task['id'])
            encoded_url = 'http://{}/issue/{}'.format(host_name, task['id'])
            img = qrcode.make(encoded_url)
            img.save(open(file_name, 'w+b'))


def generate_stars(tasks_to_write):
    foreground = Image.open('stars.png')
    for page in tasks_to_write:
        for task in page:
            file_name = 'tmp/img/{}-star.png'.format(task['id'])

            background = Image.new('RGBA', (440, 84), (255, 255, 255, 255))

            draw = ImageDraw.Draw(background)
            draw.rectangle(
                ((0, 0), (int(round(4.4 * task['stars'])), 84)),
                fill='black')

            Image.alpha_composite(background, foreground) \
                .save(open(file_name, 'w+b'))


def ensure_dirs():
    shutil.rmtree('tmp/img', ignore_errors=True)
    os.makedirs('tmp/img')

    if not os.path.isdir('tmp/out'):
        os.makedirs('tmp/out')


def chunks(l, n):
    for i in xrange(0, len(l), n):
        yield l[i:i + n]


if __name__ == '__main__':
    host = config['yt_host']

    print('Preparing...'),
    ensure_dirs()
    print('Done!')

    print('Loading tasks...'),
    tasks = load_tasks_from_csv()
    print('Done!')

    print('Generating QR codes...'),
    generate_qrs(host, tasks)
    print('Done!')

    print('Generating Stars...'),
    generate_stars(tasks)
    print('Done!')

    print('Generating HTML from template...'),
    stickers = process_template(tasks)
    print('Done!')

    print('Converting HTML to PDF...'),
    result = convert_html_to_pdf(stickers)
    print('Done!')

    print('\nYour result report is available here: {} '
          .format(result))
