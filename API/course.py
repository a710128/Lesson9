import re


class CourseException(Exception):
    def __init__(self, msg, err):
        super(CourseException, self).__init__()
        self.msg = msg
        self.err = err

    def __str__(self):
        return "CourseError : " + self.msg

    def __repr__(self):
        return '<CourseException msg : "%s", errcode : %d>' % (self.msg, self.errcode)


def courseTimeParser(timeStr):
    assert isinstance(timeStr, str), "Parameter type error"
    timeStr, _ = re.subn('\([^)]*\)', '', timeStr)
    ret = []
    for item in timeStr.split(","):
        if item == '':
            continue
        ws, pd = item.split('-')
        ret.append((int(ws), int(pd)))
    return ret


class Course:
    def __init__(self, **kwargs):
        if 'kch' in kwargs and 'kxh' in kwargs:
            self.kch = kwargs['kch']
            self.kxh = kwargs['kxh']
        elif 'kid' in kwargs:
            vs = kwargs['kid'].split(':')
            if len(vs) != 2:
                raise CourseException("Wrong Course id parameter", 0)
            self.kch = vs[0]
            self.kxh = vs[1]
        else:
            raise CourseException("Invalid parameters when Course __init__!", 1)

        self.name = ''
        self.teacher = ''
        self.time = []
        self.score = 0
        self.feature = ''
        self.other = ''

        params = {
            'name': 'Unknown',
            'teacher': 'Unknown',
            'time': [],
            'score': 0,
            'feature': '',
            'other': ''
        }

        for key in params:
            if key in kwargs:
                if isinstance(kwargs[key], type(params[key])):
                    self.__dict__[key] = kwargs[key]
                else:
                    raise CourseException("Invalid parameters when Course __init__!", 1)
            else:
                self.__dict__[key] = params[key]

        for item in self.time:
            if (not isinstance(item, tuple)) or len(item) != 2 or (not isinstance(item[0], int)) or (not isinstance(item[1], int)):
                raise CourseException("Invalid parameters when Course __init__!", 1)

    def __eq__(self, other):
        if self.kxh == '*' or other.kxh == '*':
            return self.kch == other.kch
        return self.kch == other.kch and self.kxh == other.kxh

    def timeClash(self, other):
        if isinstance(other, tuple):
            for time in self.time:
                if time == other:
                    return True
            return False
        elif isinstance(other, Course):
            for time in self.time:
                if other.timeClash(time):
                    return True
            return False
        else:
            raise CourseException("Invalid parameters when Course timeClash!", 2)

    def __str__(self):
        ret = 'Course: %s:%s; Time : ' % (self.kch, self.kxh)
        first = True
        for wk, pd in self.time:
            if first:
                first = False
            else:
                ret += ','
            ret += '%d-%d' % (wk, pd)
        ret += '; Name: %s; Teacher: %s; Score: %d; Feature: %s; Other: %s' % (self.name, self.teacher, self.score, self.feature, self.other)
        return ret

    def __repr__(self):
        return "<" + self.__str__() + ">"

    def __hash__(self):
        return hash(self.kch + ":" + self.kxh)


