import copy
import re
import urllib

import cv2
import numpy as np
import urllib3

from . import config
from .course import Course, courseTimeParser
import datetime
import threading
from queue import Queue


urllib3.disable_warnings()


def capture_idft_worker(qin):
    from . import capture
    while True:
        img, qout = qin.get()
        ret = capture.Detector_single_image(img)
        qout.put(ret)

queue_input = Queue()
capture_thd = threading.Thread(target=capture_idft_worker, args=(queue_input,))
capture_thd.setDaemon(True)
capture_thd.start()

def multhrdFunc(img):
	qout = Queue()
	queue_input.put((img, qout))
	ret = qout.get()
	return ret

class UserException(Exception):
    def __init__(self, msg, err):
        super(UserException, self).__init__()
        self.msg = msg
        self.err = err
    
    def __str__(self):
        return "UserError : " + self.msg

    def __repr__(self):
        return '<UserException msg : "%s", errcode : %d>' % (self.msg, self.errcode)


def udpCookie(old_cookie, new_str):
    ret = copy.copy(old_cookie)
    for sub in new_str.split(','):
        key, val = sub.split(';')[0].split('=', 1)
        ret[key] = val
    return ret


def parseCookie(cookie):
    ret = ''
    for key in cookie:
        ret += key + '=' + cookie[key] + '; '
    if ret[-2:] == '; ':
        ret = ret[: -2]
    return ret


def getCap(data):
    img = cv2.imdecode(np.array(np.fromstring(data, np.uint8), dtype='uint8'), cv2.IMREAD_ANYCOLOR)
    return img
    '''
    while True:
        cv2.imshow('captcha', img)
        key = cv2.waitKey(0)
    '''


def makeHeader(cookie=''):
    if isinstance(cookie, dict):
        c = parseCookie(cookie)
    else:
        c = cookie
    if c != '':
        return {
            'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:34.0) Gecko/20100101 Firefox/34.0',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Connection': 'keep-alive',
            'Cookie': c
        }
    else:
        return {
            'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:34.0) Gecko/20100101 Firefox/34.0',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Connection': 'keep-alive'
        }


class User:
    def __init__(self, name, passwd):
        self.name = name
        self.passwd = passwd
        self.cookie = {}
        self.courses = []
        self.broken = False
        try:
            ctr = 0
            while not self.login():
                ctr += 1
                if ctr > 20:
                    raise UserException('Unknown Error', -1)
        except UserException as e:
            print('User:', self.name, 'Error:', e)
            self.broken = True

    def login(self, veriFunc=multhrdFunc) -> bool:
        """
        Login, use vertFunc to get the verification code
        :param veriFunc: a function input: Image(numpy), output: Verification Code (str)
        :return: True if success
        """
        if config.DEBUG:
            print("User : %s login!" % self.name)
            return True
		
        if self.broken:
            raise UserException("Broken user", 3)
        self.cookie = {}
        http = urllib3.PoolManager()
        # get cookie and capture
        res = http.request('GET', config.CAPTCHAR_PATH,
                           headers=makeHeader())
        if 'Set-Cookie' in res.headers:
            self.cookie = udpCookie(self.cookie, res.headers['Set-Cookie'])
        else:
            self.broken = True
            raise UserException("Failed to get initial cookies!", 0)

        # visit login page
        http.request('GET', config.LOGIN_PAGE, headers=makeHeader(self.cookie))

        if not callable(veriFunc):
            self.broken = True
            raise UserException("No default verification function now!", 1)
        req_body = urllib.parse.urlencode({
            'j_username': self.name,
            'j_password': self.passwd,
            'captchaflag': 'login1',
            '_login_image_': veriFunc(getCap(res.data))
        })
        res = http.request('POST', config.LOGIN_POST_PAGE,
                headers=dict(makeHeader(self.cookie), **{
                    'Content-Type': 'application/x-www-form-urlencoded',
                    'Charset': 'UTF-8',
                    'Origin': config.WEB_PREFIX,
                    'Referer': config.LOGIN_PAGE,
                    'Cache-Control': 'max-age=0'
            }), body= req_body, redirect=False
        )
        # success
        if 'Location' in res.headers and res.headers['Location'].find('/zhjw.do') != -1:
            return True
        if ('Location' in res.headers and res.headers['Location'].find('login_error=error') != -1):
            self.broken = True
            raise UserException("Wrong username or password!", 2)
        # failure
        return False

    def udpCourses(self):
        if config.DEBUG:
            print("User : %s update courses!" % self.name)
            return
        http = urllib3.PoolManager()
        res = http.request('GET', config.COURSE_TABLE_PAGE, headers=makeHeader(self.cookie))
        data = res.data.decode("GBK")
        ret = re.findall(re.compile(r'<span class="trunk">([^<]*)</span>'), data)
        if len(ret) == 0 or len(ret) % 13 != 0:
            return False
        cs = []
        for i in range(13, len(ret), 13):
            cs.append(Course(kch=ret[i + 1], kxh=ret[i + 2], teacher=ret[i + 4],
                             name=ret[i], score=int(ret[i + 6]), time= courseTimeParser(ret[i + 5])))
        self.courses = cs
        return True

    def request(self, method: str, url: str, headers=None, **kwargs):
        if headers is None:
            headers = {}
        assert isinstance(method, str) and isinstance(url, str) and isinstance(headers, dict), "Parameter type error"
        http = urllib3.PoolManager()
        ret = http.request(method, url, headers=dict(makeHeader(self.cookie), **headers), **kwargs)
        if ret is None:
            print(datetime.datetime.now().strftime('%m-%d %H:%M:%S'), '[error]', 'User:', self.name,
                  'request error', 'url:', url, 'headers:', dict(makeHeader(self.cookie), **headers), 'args:', kwargs)
        return ret

    def __str__(self):
        return self.name

    def __repr__(self):
        return  '<User %s, cookie=%s, broken=%s>' % (self.name, str(self.cookie), str(self.broken))

    def __hash__(self):
        return hash(self.name)

    def __eq__(self, other):
        return self.name == other.name
