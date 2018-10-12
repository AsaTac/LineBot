# -*- coding: utf-8 -*-

#  Licensed under the Apache License, Version 2.0 (the "License"); you may
#  not use this file except in compliance with the License. You may obtain
#  a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#  WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#  License for the specific language governing permissions and limitations
#  under the License.

from __future__ import unicode_literals

import errno
import os
import sys
import tempfile
from argparse import ArgumentParser

from flask import Flask, request, abort

from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    LineBotApiError, InvalidSignatureError
)
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage,
    SourceUser, SourceGroup, SourceRoom,
    TemplateSendMessage, ConfirmTemplate, MessageAction,
    ButtonsTemplate, ImageCarouselTemplate, ImageCarouselColumn, URIAction,
    PostbackAction, DatetimePickerAction,
    CameraAction, CameraRollAction, LocationAction,
    CarouselTemplate, CarouselColumn, PostbackEvent,
    StickerMessage, StickerSendMessage, LocationMessage, LocationSendMessage,
    ImageMessage, VideoMessage, AudioMessage, FileMessage,
    UnfollowEvent, FollowEvent, JoinEvent, LeaveEvent, BeaconEvent,
    FlexSendMessage, BubbleContainer, ImageComponent, BoxComponent,
    TextComponent, SpacerComponent, IconComponent, ButtonComponent,
    SeparatorComponent, QuickReply, QuickReplyButton
)

import urllib.request
import urllib.parse
import json

app = Flask(__name__)

# get channel_secret and channel_access_token from your environment variable
channel_secret = os.getenv('LINE_CHANNEL_SECRET', None)
channel_access_token = os.getenv('LINE_CHANNEL_ACCESS_TOKEN', None)
if channel_secret is None:
    print('Specify LINE_CHANNEL_SECRET as environment variable.')
    sys.exit(1)
if channel_access_token is None:
    print('Specify LINE_CHANNEL_ACCESS_TOKEN as environment variable.')
    sys.exit(1)

line_bot_api = LineBotApi(channel_access_token)
handler = WebhookHandler(channel_secret)

static_tmp_path = os.path.join(os.path.dirname(__file__), 'static', 'tmp')

@app.route("/")
def hello_world():
    return "hello world!"

# function for create tmp dir for download content
def make_static_tmp_dir():
    try:
        os.makedirs(static_tmp_path)
    except OSError as exc:
        if exc.errno == errno.EEXIST and os.path.isdir(static_tmp_path):
            pass
        else:
            raise


@app.route("/callback", methods=['POST'])
def callback():
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']

    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    # handle webhook body
    try:
        handler.handle(body, signature)
    except LineBotApiError as e:
        print("Got exception from LINE Messaging API: %s\n" % e.message)
        for m in e.error.details:
            print("  %s: %s" % (m.property, m.message))
        print("\n")
    except InvalidSignatureError:
        abort(400)

    return 'OK'


@handler.add(MessageEvent, message=TextMessage)
def handle_text_message(event):
    text = event.message.text

    if text == 'carousel':
        carousel_template = CarouselTemplate(columns=[
            CarouselColumn(text='hoge1', title='fuga1', actions=[
                URIAction(label='Go to line.me', uri='https://line.me'),
                PostbackAction(label='ping', data='ping')
            ]),
            CarouselColumn(text='hoge2', title='fuga2', actions=[
                PostbackAction(label='ping with text', data='ping', text='ping'),
                MessageAction(label='Translate Rice', text='米')
            ]),
        ])
        template_message = TemplateSendMessage(
            alt_text='Carousel alt text', template=carousel_template)
        print(template_message)
        line_bot_api.reply_message(event.reply_token, template_message)

@handler.add(MessageEvent, message=LocationMessage)
def handle_location_message(event):
    try:
#        print('start')
        latitude=str(event.message.latitude)
        longitude=str(event.message.longitude)
        my = gnavi_api(latitude,longitude)
        rests = do_json(my)
        template_message = sendRest(rests)
#        print(template_message)
        line_bot_api.reply_message(event.reply_token, template_message)
    except Exception as e:
        print(Exception)


def gnavi_api(latitude,longitude):
    key = '3f1eb1a6047e3a0a5a4c8120655bafcd'
    url = "https://api.gnavi.co.jp/RestSearchAPI/v3/"
    search_range = '2'
    category_l = 'RSFST09000'
    params = urllib.parse.urlencode({
        'keyid': key,
        'latitude': latitude,
        'longitude': longitude,
        'range':search_range,
        'category_l':category_l
    })
    try:
        responce = urllib.request.urlopen(url + '?' + params)
        return responce.read()
    except:
        raise Exception(u'APIアクセスに失敗しました')

def do_json(data):
    parsed_data = json.loads(data)
    if 'error' in parsed_data:
        if 'message' in parsed_data:
            raise Exception(u'{0}'.format(parsed_data['message']))
        else:
            raise Exception(u'データ取得に失敗しました')
    total_hit_count = parsed_data.get('total_hit_count', 0)

    if total_hit_count < 1:
        raise Exception(u'指定した内容ではヒットしませんでした\nレストランデータが存在しなかったため終了します')
    rests = parsed_data['rest']
    return rests

def sendRest(rests):
    # for rest in rests:
    #     carousel_template = CarouselTemplate(columns=[
    #         CarouselColumn(text=rest['opentime'], title=rest['name'], actions=[
    #             URIAction(label='webで検索', uri=rest['url_mobile'])
    #         ]),
    #     ])
    opentime1 = rests[0]['opentime']
    name1 = rests[0]['name']
    address1 = rests[0]['address']
    url1 = rests[0]['url_mobile']
    thumbnail1 = rests[0]['image_url']['shop_image1']
    tel1 = 'tel:'+rests[0]['tel']
    urlGMap1 = 'http://maps.google.com/maps' + '?saddr=' + latitude + ',' + longitude + '&daddr=' + rests[0]['latitude'] + ',' + rests[0]['longitude'] + '&dirflg=w'
    
    opentime2 = rests[1]['opentime']
    name2 = rests[1]['name']
    address2 = rests[1]['address']
    url2 = rests[1]['url_mobile']
    thumbnail2 = rests[1]['image_url']['shop_image1']
    tel2 = 'tel:'+rests[1]['tel']
    urlGMap2 = 'http://maps.google.com/maps'+ '?saddr=' + latitude + ',' + longitude+ '&daddr=' + rests[1]['latitude'] + ',' + rests[1]['longitude'] + '&dirflg=w'

    opentime3 = rests[2]['opentime']
    name3 = rests[2]['name']
    address3 = rests[2]['address']
    url3 = rests[2]['url_mobile']
    thumbnail3 = rests[2]['image_url']['shop_image1']
    tel3 = 'tel:'+rests[2]['tel']
    urlGMap3 = 'http://maps.google.com/maps' + '?saddr=' + latitude + ',' + longitude + '&daddr=' + rests[2]['latitude'] + ',' + rests[2]['longitude'] + '&dirflg=w'

    if(opentime1 == ''):
        opentime1 = '営業時間：情報がありません'
    if(name1 == ''):
        name1 = '情報がありません'
    if(address1 == ''):
        address1 = '住所：情報がありません'
    if(url1 == ''):
        url1 = 'https://line.me'
    if(thumbnail1 == ''):
        thumbnail1 = 'https://example.com/cafe.jpg'


    if(opentime2 == ''):
        opentime2 = '営業時間：情報がありません'
    if(name2 == ''):
        name2 = '情報がありません'
    if(address2 == ''):
        address2 = '住所：情報がありません'    
    if(url2 == ''):
        url2 = 'https://line.me'
    if(thumbnail2 == ''):
        thumbnail2 = 'https://example.com/cafe.jpg'


    if(opentime3 == ''):
        opentime3 = '営業時間：情報がありません'
    if(name3 == ''):
        name3 = '情報がありません'
    if(address3 == ''):
        address3 = '住所：情報がありません'
    if(url3 == ''):
        url3 = 'https://line.me'
    if(thumbnail3 == ''):
        thumbnail3 = 'https://example.com/cafe.jpg'
    print(tel1)
    print(tel2)
    print(tel3)
    carousel_template = CarouselTemplate(columns=[
        CarouselColumn(
            thumbnail_image_url=thumbnail1,
            text=opentime1, 
            title=name1, 
            actions=[
                URIAction(label='詳細を表示', uri=url1),
                URIAction(label='電話する', uri=tel1),
                URIAction(label='経路案内', uri=urlGMap1)
        ]),
        CarouselColumn(
            thumbnail_image_url=thumbnail2,
            text=opentime2, 
            title=name2, 
            actions=[
                URIAction(label='詳細を表示', uri=url2),
                URIAction(label='電話', uri=tel2),
                URIAction(label='経路案内', uri=urlGMap2)
        ]),        
        CarouselColumn(
            thumbnail_image_url=thumbnail3,
            text=opentime3, 
            title=name3, 
            actions=[
                URIAction(label='詳細を表示', uri=url3),
                URIAction(label='電話', uri=tel3),
                URIAction(label='経路案内', uri=urlGMap3)
        ]),
    ])
    template_message = TemplateSendMessage(
        alt_text='お店が見つかりました', template=carousel_template)
    return template_message

if __name__ == "__main__":
    app.run()
