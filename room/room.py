import threading
from API import User, Course, courseTimeParser, UserException
from room import config
import time
import re


def getCourseWorker(user: User, clist: list, token: str, flh: str, kch: str, kcm: str):
    post_data = config.RX_POST_STRING.format(token=token, flh=flh, kch=kch, kcm=kcm)
    for course in clist:
        post_data += "&p_rx_id={time_period}%3B".format(time_period=config.TIME_PERIOD) + course.kch + \
                     '%3B' + course.kxh + '%3B'
    post_data += '&goPageNumber=1'
    data = user.request("POST", config.RX_POST_URL, body=post_data).data.decode('gbk')
    val = re.findall(re.compile(r'name="token" value="([^"]+)"'), data)
    if len(val) != 1:
        try:
            while not user.login():
                pass
            return {'result': 'relogin'}  # relogin
        except UserException:
            return {'result': 'broken'}
            # this user is broken

    ret_token = val[0]

    # TODO: find out courses which are failed

    return {
        'result': 'success',
        'token': ret_token,
        'course': [],   # FIXME
        'bans': []      # FIXME
    }


class Room:
    def __init__(self, name, desc, interval=3, flh: str = '', kch: str = '', kcm: str = ''):
        assert isinstance(name, str) and isinstance(desc, str), "Parameter type error"
        self.name = name
        self.desc = desc
        self.interval = interval
        self.user = []
        self.__lock = threading.Lock()
        self.lastWork = dict()
        self.broken = False
        self.workers = 0

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

        data = user.request('GET', config.RX_GET_URL).data.decode('gbk')
        val = re.findall(re.compile(r'name="token" value="([^"]+)"'), data)
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
        self.__lock.release()
        return ret

    def addBan(self, user: User, course: Course, reason: str):
        self.bans[user][course] = reason

    def _workerHolder(self, user: User, clist: list):
        ret = getCourseWorker(user, clist, self.tokens[user], self.flh, self.kch, self.kcm)
        if ret['result'] == 'broken':
            return
        if ret['result'] == 'relogin':
            self.getFirstToken(user)
            return
        if ret['result'] == 'success':
            self.tokens[user] = ret['token']
            for ban in ret['bans']:
                self.bans[user][ban] = "不能选到该课程"
            return
        raise AssertionError("Unknown result")

    def getNextUser(self):
        self.__lock.acquire()
        mnUser = None
        self.workers = 0
        for user in self.lastWork.keys():
            if user.broken:
                continue
            self.workers += 1
            if (mnUser is None) or (self.lastWork[mnUser] > self.lastWork[user]):
                mnUser = user
        self.lastWork[mnUser] = time.time()
        self.__lock.release()
        if mnUser is None:
            self.broken = True
        else:
            self.broken = False

        return mnUser

    def loop(self):
        while True:
            user = self.getNextUser()
            if user is None or self.workers == 0:
                return  # no user in this room
            else:
                time.sleep((self.interval + 0.5) / self.workers)
                self.__lock.acquire()
                self.run(user)
                self.__lock.release()

    def run(self, user: User):
        assert isinstance(user, User), "Parameter type error"
        if config.DEBUG:
            return
        page = 0

        ret = {}
        while True:
            page += 1
            data = user.request('POST', config.RX_POST_URL,
                                body=config.RX_QUERY_STRING.format(
                                    page=page, token=self.tokens[user], flh=self.flh, kch=self.kch, kcm=self.kcm))
            data = data.decode('gbk')
            val = re.findall(re.compile(r'name="token" value="([^"]+)"'), data)
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
                r'\\[\\s*"[^"]*"\\s*,"([^"]+)"\\s*,"([^"]+)"\\s*,\\s*"[^"]*"\\s*,"([0-9]*)"\\s*,"([^"]*)"[^\\]]+\\]'),
                              data)

            hasUdp = True
            for kch, kxh, rest, timeList in info:
                if rest == 0:
                    hasUdp = False
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
                if c in self.bans[u]:
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
