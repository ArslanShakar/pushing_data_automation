# -*- coding: utf-8 -*-

import re
from html import unescape
from collections import OrderedDict

import usaddress


limit = 10000
wait_time_seconds = 1

skipped_fields = ['img', 'src', 'url', 'link', 'store_id']
rep_chars = [u'\n', u'\r', u'\t', u'\xa0', u'...', u'--']
bad_text_re = re.compile('|'.join(rep_chars))
punctuation_re = re.compile(r'[^\d.]')


def clean_price(price):
    if not any([e in price for e in ['cash back', 'discount']]):
        return punctuation_re.sub('', price)
    return price


def clean(text):
    text = re.sub(u'"', u"\u201C", unescape(text or ''))
    text = re.sub(u"'", u"\u2018", text)
    for c in rep_chars:
        text = text.replace(c, ' ')
    return re.sub(' +', ' ', text).strip().title()


def clean_all(data):
    if isinstance(data, (list, tuple)):
        for i, e in enumerate(data):
            if e and isinstance(e, str) and e.strip():
                data[i] = clean(e)
            elif e and isinstance(e, dict):
                clean_dict(e)

        return data

    elif isinstance(data, str):
        return clean(data)

    elif isinstance(data, dict):
        return clean_dict(data)
    else:
        return data


def clean_dict(data):
    for key in data or {}:
        if isinstance(data[key], str):
            if [e in key.lower() for e in skipped_fields]:
                continue
            if key == "schedule":
                data[key] = data[key].replace("\u201C", '"')
            if key in ['state']:
                data[key] = clean(data[key]).upper()
            elif key == 'address':
                data[key] = parse_address(data[key])
            elif key == 'price':
                data[key] = clean_price(data[key])
            else:
                data[key] = clean(data[key])

    return data


def parse_address(address):
    address1, city, state, zip_code = '', '', '', ''

    for value, key in usaddress.parse(address):
        value = value.replace(',', '') + ' '
        if key in ['OccupancyIdentifier', 'Recipient']:
            continue
        if key == 'PlaceName':
            city += value
        elif key == 'StateName':
            state += value
        elif key == 'ZipCode':
            zip_code += value
        else:
            address1 += value

    if not zip_code:
        zip_code = ''.join((re.findall('\d{5}', address) or re.findall('\d{4}', address))[:1])

    address_item = OrderedDict(
        address1=address1,
        city=city,
        state=state,
        zip_code=zip_code,
    )

    return ', '.join(v for k, v in clean_dict(address_item).items())


def log_info(text, pre='\n', post=''):
    print(f"{pre}{text}{post}")
