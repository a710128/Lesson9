import threading
from API import User, Course, courseTimeParser, UserException
from room import config
import time
import datetime
import re
import urllib

def make_post_headers():
    return {
        'Content-Type': 'application/x-www-form-urlencoded',
        'Charset': 'UTF-8',
        'Cache-Control': 'max-age=0'
    }

def getCourseWorker(user: User, clist: list, token: str, flh: str, kch: str, kcm: str, type: int):
    if type == 0: # RX
        post_data = config.RX_POST_STRING.format(token=token, flh=urllib.parse.quote(flh.encode('gbk')), kch=urllib.parse.quote(kch.encode('gbk')), kcm=urllib.parse.quote(kcm.encode('gbk')))
    elif type == 1: # BX
        post_data = config.BX_POST_STRING.format(token=token)
    elif type == 2: # XX
        post_data = config.XX_POST_STRING.format(token=token)
    elif type == 3: # TY
        post_data = config.TY_POST_STRING.format(token=token, kch=urllib.parse.quote(kch.encode('gbk')), kcm=urllib.parse.quote(kcm.encode('gbk')))

    for course in clist:
        if type == 0:
            post_data += "&p_rx_id={time_period}%3B".format(time_period=config.TIME_PERIOD)
        elif type == 1:
            post_data += "&p_bxk_id={time_period}%3B".format(time_period=config.TIME_PERIOD)
        elif type == 2:
            post_data += "&p_xxk_id={time_period}%3B".format(time_period=config.TIME_PERIOD)
        elif type == 3:
            post_data += "&p_rxTy_id={time_period}%3B".format(time_period=config.TIME_PERIOD)
        post_data += course.kch + '%3B' + course.kxh + '%3B'
    
    if type == 0: # RX
        data = user.request("POST", config.RX_POST_URL, body=post_data, headers=make_post_headers()).data.decode('gbk')
    elif type == 1: # BX
        data = user.request("POST", config.BX_POST_URL, body=post_data, headers=make_post_headers()).data.decode('gbk')
    elif type == 2: # XX
        data = user.request("POST", config.XX_POST_URL, body=post_data, headers=make_post_headers()).data.decode('gbk')
    elif type == 3: # TY
        data = user.request("POST", config.TY_POST_URL, body=post_data, headers=make_post_headers()).data.decode('gbk')
    
    val = re.findall(re.compile(r'name="token"\s*value="([^"]+)"', re.S), data)
    if len(val) != 1:
        try:
            while not user.login():
                pass
            return {'result': 'relogin'}  # relogin
        except UserException:
            return {'result': 'broken'}
            # this user is broken

    ret_token = val[0]
    fails = re.findall(re.compile(r'showMsg\("([^"]*)"\)'), data)

    fcourse = []
    okcourse = []
    if len(fails) == 1:
        fail = fails[0]
        cids = re.findall(re.compile(r'([^!]+)!'), fail)
        for row in cids:
            val = re.findall(re.compile(r'[^0-9SX]*([0-9SX]+)\s+([0-9]+)(.*)'), row)
            if len(val) == 0:
                val = re.findall(re.compile(r'[^0-9SX]*([0-9SX]+)课序号([0-9]+)(.*)'), row)
                if len(val) == 1:
                    kch, kxh, freason = val[0]
                    fcourse.append((Course(kch=kch, kxh=kxh), freason))
                else:
                    val = re.findall(re.compile(r'[^0-9SX]*([0-9SX]+)(.*)'), row)
                    if len(val) == 1:
                        kch, freason = val[0]
                        fcourse.append((Course(kch=kch, kxh='*'), freason))
                    else:
                        print('unknown row', row)
            else:
                kch, kxh, freason = val[0]
                if freason.find('课余量已无') == -1:
                    fcourse.append((Course(kch=kch, kxh=kxh), freason))
        for course in clist:
            find = False
            for c, _ in fcourse:
                if c == course:
                    find = True
                    break
            if not find:
                okcourse.append(course)
    elif len(fails) > 1:
        print('Unknown fails', fails)
    else:
        okcourse = clist
    return {
        'result': 'success',
        'token': ret_token,
        'course': okcourse,
        'bans': fcourse
    }


class Room:
    def __init__(self, name, desc, interval=3, flh: str = '', kch: str = '', kcm: str = '', type: int = 0):
        assert isinstance(name, str) and isinstance(desc, str), "Parameter type error"
        self.name = name
        self.desc = desc
        self.interval = interval
        self.user = []
        self.__lock = threading.Lock()
        self.lastWork = dict()
        self.broken = False
        self.workers = 0
        self.type = type
        
        self.flh = flh
        self.kch = kch
        self.kcm = kcm
        self.tokens = {}
        self.bans = {}
        self.roomId = id(self)

    def getFirstToken(self, user: User):
        if config.DEBUG:
            self.tokens[user] = ""
            return
        if self.type == 0: # RX
            data = user.request('GET', config.RX_GET_URL).data.decode('gbk')
        elif self.type == 1: # BX
            data = user.request('GET', config.BX_GET_URL).data.decode('gbk')
        elif self.type == 2: # XX
            data = user.request('GET', config.XX_GET_URL).data.decode('gbk')
        elif self.type == 3: # TY
            data = user.request('GET', config.TY_GET_URL).data.decode('gbk')
        
        val = re.findall(re.compile(r'name="token"\s*value="([^"]+)"', re.S), data)
        if len(val) == 1:
            self.tokens[user] = val[0]
        else:
            self.tokens[user] = ""

    def addUser(self, user):
        assert isinstance(user, User), "Parameter type error"
        self.__lock.acquire()
        self.user.append(user)
        self.lastWork[user] = 0

        self.tokens[user] = ""
        self.bans[user] = {}
        self.getFirstToken(user)
        self.__lock.release()

    def delUser(self, user):
        assert isinstance(user, User), "Parameter type error"
        self.__lock.acquire()
        it = 0
        while it < len(self.user):
            if self.user[it] == user:
                break
            it += 1
        ret = False
        if it < len(self.user):
            del self.user[it]
            del self.lastWork[user]
            del self.tokens[user]
            del self.bans[user]
            ret = True
        else:
            print('Can\'t find user:', user.name)
        self.__lock.release()
        return ret

    def addBan(self, user: User, kch: str, kxh: str, reason: str):
        course = Course(kch=kch, kxh=kxh)
        self.bans[user][course] = reason

    def delBan(self, user: User, kch: str, kxh: str):
        course = Course(kch=kch, kxh=kxh)
        if course in self.bans[user]:
            del self.bans[user][course]

    def _workerHolder(self, user: User, clist: list):
        ret = getCourseWorker(user, clist, self.tokens[user], self.flh, self.kch, self.kcm, self.type)
        if ret['result'] == 'broken':
            return
        if ret['result'] == 'relogin':
            self.getFirstToken(user)
            return
        if ret['result'] == 'success':
            self.tokens[user] = ret['token']
            for ban, reason in ret['bans']:
                self.bans[user][ban] = reason
                print(datetime.datetime.now().strftime('%m-%d %H:%M:%S'), '[info]', 'Room:', self.name, 'User:',
                      user.name, 'course:', ban.kch, ban.kxh, 'Reason:', reason)
            for course in ret['course']:
                print(datetime.datetime.now().strftime('%m-%d %H:%M:%S'), '[info]', 'Room:', self.name, 'User:',
                      user.name, 'course:', course.kch, course.kxh)
            return
        raise AssertionError("Unknown result")
    
    def udpWorkers(self):
        self.workers = 0
        for user in self.lastWork.keys():
            if user.broken:
                continue
            self.workers += 1
    
    def getNextUser(self):
        mnUser = None
        for user in self.lastWork.keys():
            if user.broken:
                continue
            if (mnUser is None) or (self.lastWork[mnUser] > self.lastWork[user]):
                mnUser = user
        self.lastWork[mnUser] = time.time()
        if mnUser is None:
            self.broken = True
        else:
            self.broken = False

        return mnUser

    def loop(self):
        lst = 0
        while True:
            if lst == 0:
                lst = time.time()
            self.__lock.acquire()
            self.udpWorkers()
            self.__lock.release()
            if self.workers == 0:
                shouldWait = 3
            else:
                shouldWait = max((self.interval + 0.5) / self.workers - (time.time() - lst), 0.1)
            time.sleep(shouldWait)
            self.__lock.acquire()
            user = self.getNextUser()
            if user is None or self.workers == 0:
                self.__lock.release()
                return  # no user in this room
            else:
                self.run(user)
                self.__lock.release()
                lst = time.time()

    def run(self, user: User):
        assert isinstance(user, User), "Parameter type error"
        if config.DEBUG:
            time.sleep(0.6)
            print(datetime.datetime.now().strftime('%m-%d %H:%M:%S'), '[debug]', 'Room:', self.name, 'User:', user.name)
            return
        page = 0

        ret = {}
        while True:
            page += 1
            if self.type == 0: # RX
                data = user.request('POST', config.RX_POST_URL, 
                             body=config.RX_QUERY_STRING.format(page= '' if page == 1 else page,
                             token=self.tokens[user], flh=urllib.parse.quote(self.flh.encode('gbk')), kch=urllib.parse.quote(self.kch.encode('gbk')), kcm=urllib.parse.quote(self.kcm.encode('gbk'))),
                             headers=make_post_headers()).data
            elif self.type == 1: # BX
                data = user.request('GET', config.BX_GET_URL).data
            elif self.type == 2: # XX
                data = user.request('GET', config.XX_GET_URL).data
            elif self.type == 3: # TY
                data = user.request('POST', config.RX_POST_URL,
                             body=config.TY_QUERY_STRING.format(page= '' if page == 1 else page,
                             token=self.tokens[user], kch=urllib.parse.quote(self.kch.encode('gbk')), kcm=urllib.parse.quote(self.kcm.encode('gbk'))),
                             headers=make_post_headers()).data
            data = data.decode('gbk')
            val = re.findall(re.compile(r'name="token"\s*value="([^"]+)"', re.S), data)
            if len(val) != 1:
                try:
                    while not user.login():
                        pass
                    page -= 1
                    self.getFirstToken(user)
                    continue  # jump to the beginning of this loop
                except UserException:
                    break
                    # this user is broken
            self.tokens[user] = val[0]
            info = re.findall(re.compile(
                r'\[\s*"[^"]*"\s*,"([^"]+)"\s*,"([^"]+)"\s*,\s*"[^"]*"\s*,"([0-9]*)"\s*,"([^"]*)"[^\]]+\]', re.S),
                              data)
            hasUdp = True
            if len(info) < 20 or self.type == 1 or self.type == 2:
                hasUdp = False

            for kch, kxh, rest, timeList in info:
                try:
                    if int(rest) == 0:
                        hasUdp = False
                        continue
                except ValueError as e:
                    continue
                course = Course(kch=kch, kxh=kxh, time=courseTimeParser(timeList))
                ret[course] = rest
            if not hasUdp:
                break
        if len(ret) == 0:
            return  # early stop to speed up
        reqs = {}
        for u in self.user:
            reqs[u] = []

        for c in ret:
            for u in self.user:
                find = False
                for b in self.bans[u].keys():
                    if b == c:
                        find = True
                        break
                if find:
                    continue
                reqs[u].append(c)
        thds = []
        for u in reqs.keys():
            if len(reqs[u]) == 0:
                continue
            else:
                thds.append(threading.Thread(target=self._workerHolder, args=(u, reqs[u])))
        for t in thds:
            t.start()
        for t in thds:
            t.join()

    def __hash__(self):
        return hash(self.roomId)

    def __eq__(self, other):
        assert isinstance(other, (int, Room)), "Parameter type error"
        if isinstance(other, int):
            return self.roomId == other
        return self is other

    def __del__(self):
        if self.workers != 0:
            pass  # warning !

    def __copy__(self):
        raise AssertionError("Room cant be copied")

    def __deepcopy__(self, memodict={}):
        raise AssertionError("Room cant be copied")
