#! python3
# -*- coding : utf-8 -*-
"""Load WebPage and find KeyWord"""
import re
import urllib.request
import codecs
from os import makedirs
from os import path
from shutil import rmtree

class LocalException(Exception):
    """
    このプログラム内でのみ使用する例外クラス
    """
    def __init__(self, value):
        super(LocalException, self).__init__(self, value)
        self.value = value

    def __str__(self):
        return repr(self.value)

def question_yes_or_no(question):
    """単純なYes/Noをユーザーから取得する"""
    re_yes = re.compile(r'\s*Y.*', re.IGNORECASE)
    re_no = re.compile(r'\s*N.*', re.IGNORECASE)
    anser = None
    while anser is None:
        ans = input(question + '(Y/N)?:')
        if re_yes.match(ans):
            anser = True
        elif re_no.match(ans):
            anser = False
    return anser

def download_web(url):
    """Download from URL"""
    print("Download : " + url)
    try:
        with urllib.request.urlopen(url) as response:
            html = response.read()
    except ValueError:
        print("ERROR! \n")
        raise LocalException("不正なURLです : " + url)
    else:
        print("Download : Comp \n")
    return html

def find_word(fname, word, encording='utf-8'):
    """
    ファイルから指定したワードを検索する
    """
    fdiff = codecs.open(fname, "r", encording)
    sret = []
    for line in fdiff:
        if re.match(".*"+word+".*", line, re.IGNORECASE):
            sret.append(line)
    return sret

### プログラム本編 ###
def download_driver(url, savedir):
    """
    Let'sNoteシリーズのドライバページから、ドライバーを取得するプログラム
    """
    re_table = r'.*table.*(CF-.*?)用.*(Windows.*) 導入済みドライバー.*'
    re_number = r'<td.*align="center".*?>(\s*\d+)</td>'
    re_priority = r'<td.*align="center".*?>(.+)</td>'
    re_name = r'<td.*?class="bg03".*?>(.*?)(<br>.*|</td>)'
    re_link = r'<td><a title=".*?href="(.+exe)">.*'
    re_comment_start = r'.*<!--(?!.*?-->).*'
    re_comment_end = r'.*-->(?!.*?<!--).*'

    class Driver():
        """ドライバの一項目"""
        def __init__(self):         # コンストラクタ
            self.priority = ""
            self.name = ""
            self.link = ""

        def __str__(self):
            return self.priority + ":" + self.name + "\n\t" + self.link

        def download(self, idx, place):
            """ファイルをダウンロードする"""
            if not path.exists(place):
                makedirs(place)
            urllib.request.urlretrieve(self.link, place + "\\" + str(idx) + "_" + self. get_name())

        def get_name(self):
            """名前を取得する"""
            return self.priority + "_" + self.name + ".exe"

        def check(self):
            """正しい値が入っているかチェックする"""
            flag = True
            if not self.__check_str__(self.priority):
                flag = False
            else:
                self.priority = re.sub(r"\<.*?\>", "", self.priority)
            if not self.__check_str__(self.name):
                flag = False
            else:
                self.name = re.sub(r"\<.*?\>", "_", self.name)
            if not self.__check_str__(self.link):
                flag = False
            return flag

        def __check_str__(self, tgt):
            flag = True
            if not isinstance(tgt, str):
                flag = False
            elif tgt == "":
                flag = False
            return flag

    class DriverList():
        """ドライバのリスト"""
        def __init__(self, model="", osbit=""):
            self.model = model
            self.os_bit = osbit
            self.drivers = {}

        def add(self, index, driver):
            """ドライバ定義を追加する"""
            if driver.check():
                self.drivers.update({index:driver})

        def download(self, place, forcerm=None):
            """ファイルをダウンロードする"""
            place = place + "\\" + self.model + "\\" + self.os_bit
            if path.exists(place):
                if forcerm is None:
                    if question_yes_or_no(place + "にあるファイルは削除されます。\nよろしいですか"):
                        forcerm = True
                    else:
                        forcerm = False

                if forcerm:
                    rmtree(place, True)
                else:
                    print("中断しました")
                    return -1

            print("Download : " + self.model + "_" + self.os_bit)
            for idx, drv in self.drivers.items():
                print("("+str(idx)+"/"+str(len(self.drivers)+1)+")Downloading : "+drv.name)
                drv.download(idx, place)
            return 0

        def __str__(self):
            ret = "model : " + self.model + "\n"
            ret += "os    : " + self.os_bit
            for idx, drv in self.drivers.items():
                ret += "\n\t" + str(idx) + " " + str(drv) + "\n"
            return ret

    tmp = download_web(url)
    tmp = tmp.decode("sjis")
    tmp = re.sub('<td', '\n<td', tmp, 0)
    tmp = re.sub('/td>', '/td>\n', tmp, 0)
    tmp = tmp.split("\n")
    sret = []
    tmpdrv = None
    tmpidx = 0
    in_comment = False

    for line in tmp:
        line = line.strip()

        if re.match(re_table, line, re.IGNORECASE):
            model = re.sub(re_table, "\\1", line)
            osbit = re.sub(re_table, "\\2", line)
            sret.append(DriverList(model, osbit))

        if in_comment:
            if re.match(re_comment_end, line, re.IGNORECASE):
                in_comment = False
        else:
            if re.match(re_number, line, re.IGNORECASE):
                tmpidx = int(re.sub(re_number, "\\1", line))
            elif re.match(re_comment_start, line, re.IGNORECASE):
                in_comment = True

            if re.match(re_priority, line, re.IGNORECASE):
                tmpdrv = Driver()
                tmpdrv.priority = re.sub(re_priority, "\\1", line)

            if re.match(re_name, line, re.IGNORECASE):
                tmpdrv.name = re.sub(re_name, "\\1", line)

            if re.match(re_link, line, re.IGNORECASE):
                tmpdrv.link = re.sub(re_link, "\\1", line)
                sret[len(sret)-1].add(tmpidx, tmpdrv)
                tmpdrv = Driver()

    forcerm = None
    for dat in sret:
        print(dat)
        if dat.download(savedir, forcerm) == -1:
            forcerm = False
        else:
            forcerm = True
    return sret

def main():
    """Panasonicのドライバを取得する"""
    re_url = re.compile(r'http://askpc.panasonic.co.jp/s/download/install.*')
    url = None
    while url is None:
        iurl = input('URL? :')
        if re_url.match(iurl.strip()):
            url = iurl.strip()
    pwd = path.dirname(path.abspath(__file__))
    download_driver(url, pwd + "/Download")

##################################################
try:
    main()
except LocalException as excep:
    print("### Catch LocalException Error ! ###\n")
    print(excep)
    print("\nProgram is Assert\n")

print("Comp.")


