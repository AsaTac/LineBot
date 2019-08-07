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
    title = "ようこそ"
    message = ""
    # index.html をレンダリングする
    return render_template('index.html',
                           message=message, title=title)
#    return '<img src="https://kirinwiki.com/wiki/lib/exe/fetch.php/py:tenagazaru.jpg" title="条件抽出画面">'

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

@handler.add(MessageEvent, message=LocationMessage)
def handle_location_message(event):
    try:
        latitude=str(event.message.latitude)
        longitude=str(event.message.longitude)
        print(latitude)
        print(longitude)
        my = gnavi_api(latitude,longitude)
        rests = get_json(my,event)
        template_message = make_json(rests,latitude,longitude)
#        print(template_message)
        print('start')
        reply_message(event, template_message)
    except Exception as e:
        print(e)
        raise Exception(e)


def gnavi_api(latitude,longitude):
    key = '6cc3ade918a9b1b0e2b8afdaf4bbfb0d'
    url = "https://api.gnavi.co.jp/RestSearchAPI/v3/"
    search_range = '2'
    category_l = 'RSFST09000'
    hit_per_page = '5'
    params = urllib.parse.urlencode({
        'keyid': key,
        'latitude': latitude,
        'longitude': longitude,
        'range':search_range,
        'category_l':category_l,
        'hit_per_page':hit_per_page
    })
    try:
        print(params)
        responce = urllib.request.urlopen(url + '?' + params)
        return responce.read()
    except:
        raise Exception(u'APIアクセスに失敗しました')

def get_json(data,event):
    parsed_data = json.loads(data)
    if 'error' in parsed_data:
        reply_message(
            event,
            'お店が見つかりませんでした。。。'
        )
        if 'message' in parsed_data:
            raise Exception(u'{0}'.format(parsed_data['message']))
        else:
            raise Exception(u'データ取得に失敗しました')
    total_hit_count = parsed_data.get('total_hit_count', 0)

    if total_hit_count < 1:
        reply_message(
            event,
            'お店が見つかりませんでした。。。'
        )
        raise Exception(u'指定した内容ではヒットしませんでした\nレストランデータが存在しなかったため終了します')
    rests = parsed_data['rest']
    return rests

def make_json(rests,latitude,longitude):
    columns = list()
    for rest in rests:
        opentime = rest['opentime']
        opentime = opentime[0:60]
        name = rest['name']
        address = rest['address']
        url = rest['url_mobile']
        thumbnail = rest['image_url']['shop_image1']
        tel = 'tel:'+rest['tel']
        urlGMap = 'http://maps.google.com/maps' + '?saddr=' + latitude + ',' + longitude + '&daddr=' + rest['latitude'] + ',' + rest['longitude'] + '&dirflg=w'
        
        if(opentime == ''):
            opentime = '営業時間：情報がありません'
        if(name == ''):
            name = '情報がありません'
        if(address == ''):
            address = '住所：情報がありません'
        if(url == ''):
            url = 'https://line.me'
        if(thumbnail == ''):
            thumbnail = 'https://example.com/cafe.jpg'

        column = CarouselColumn(
                    thumbnail_image_url=thumbnail,
                    text=opentime, 
                    title=name, 
                    actions=[
                        URIAction(label='詳細を表示', uri=url),
 #                       URIAction(label='電話する', uri=tel),
                        URIAction(label='経路案内', uri=urlGMap)
                ])
        columns.append(column)
        print('title:'+name)
        print('text:'+opentime)
    carousel_template = CarouselTemplate(columns)
    print(carousel_template)
    template_message = TemplateSendMessage(
    alt_text='お店が見つかりました', template=carousel_template)
    return template_message

def reply_message(event, messages):
    line_bot_api.reply_message(
        event.reply_token,
        messages=messages,
    )

if __name__ == "__main__":
    arg_parser = ArgumentParser(
        usage='Usage: python ' + __file__ + ' [--port <port>] [--help]'
    )
    arg_parser.add_argument('-p', '--port', type=int, default=5000, help='port')
    arg_parser.add_argument('-d', '--debug', default=False, help='debug')
    options = arg_parser.parse_args()
    app.run(debug=options.debug, port=options.port)
