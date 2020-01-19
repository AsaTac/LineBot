import PIL
from PIL import Image
import sys
sys.path.append('/path/to/dir')

import pyocr
import pyocr.builders

tools = pyocr.get_available_tools()
if len(tools) == 0:
    print("No OCR tool found")
    sys.exit(1)
tool = tools[0]
print("Will use tool '%s'" % (tool.get_name()))

langs = tool.get_available_languages()
print("Available languages: %s" % ", ".join(langs))

def getISBNfromPicture(picture):
    txt = tool.image_to_string(
        Image.open(picture),
        lang='eng',
        builder=pyocr.builders.TextBuilder()
    )
    print(txt)
    print(txt)
    if len(txt) > 15:
        txtLines = txt.splitlines()
        ISBN = [txtLine for txtLine in txtLines if 'ISBN' in txtLine]
        if len(ISBN) == 1:
            ISBNCode = ISBN[0].replace('ISBN','')
            print(ISBNCode)
        else:
            print('ISBNが見つかりません')
    else:
        print('画像が読み取れません。画像に影があると読み取れない場合があります')

#getISBNfromPicture('IMG_0003.jpeg')