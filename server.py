import flask
from web import config
from manager import Manager
import time
import os
import pickle
from tornado.wsgi import WSGIContainer
from tornado.httpserver import HTTPServer
from tornado.ioloop import IOLoop

manager = None

app = flask.Flask(__name__, template_folder="web/templates", static_folder="web/static")
app.debug = config.debug
app.secret_key = config.secret_key


def replaceReturn(str):
    return '<br>'.join(map(lambda x:flask.escape(x) ,str.split('\n')))


def checkUserInList(uid, lst):
    find = False
    for u in lst:
        if u['name'] == uid:
            find = True
            break
    return find


@app.route("/", methods=['GET'])
def default_page():
    return flask.redirect(flask.url_for("index"))


@app.route("/index", methods=['GET'])
def index():
    return flask.render_template('index.html', timer=time.ctime())


@app.route("/account/list", methods=["POST"])
def account_list():
    users = flask.session.get('accounts', [])
    opt = []
    for user in users:
        u = manager.getUser(user['name'])
        if u is not None:
            opt.append({
                'name': u.name,
                'broken': u.broken
            })
    flask.session['accounts'] = opt
    return flask.render_template('account_list.html', users=opt)


@app.route("/account/manager", methods=["POST"])
def account_manager():
    users = flask.session.get('accounts', [])
    return flask.render_template("account_manager.html", users=users)


@app.route('/account/manager/add', methods=["POST"])
def add_account():
    uid = flask.request.form.get('uid', '')
    passwd = flask.request.form.get('pass', '')
    if uid == '' or passwd == '':
        return 'Error'
    else:
        users = flask.session.get('accounts', [])
        u = manager.addUser(uid, passwd)
        if u is not None:
            users.append({
                'name': u.name,
                'broken': u.broken
            })
            flask.session['accounts'] = users
            return 'OK'
        else:
            return 'Failed'


@app.route('/account/manager/del', methods=['POST'])
def del_account():
    uid = flask.request.form.get('uid', '')
    if uid == '':
        return 'Error'
    else:
        users = flask.session.get('accounts', [])
        if not checkUserInList(uid, users):
            return 'Error'
        manager.delUser(uid)
        # update session
        opt = []
        for user in users:
            if user['name'] != uid:
                opt.append(user)
        flask.session['accounts'] = opt
        return 'OK'


@app.route('/rooms/info', methods=['POST'])
def room_info():
    uid = flask.request.form.get('uid', '')
    if uid == '':
        return 'Error'
    else:
        user = manager.getUser(uid)
        users = flask.session.get('accounts', [])
        if not checkUserInList(uid, users):
            return 'Error'
        
        room = manager.getUserRoom(user)
        if room is None:
            rooms = manager.getRoomInfo()
            return flask.render_template("room_list.html", rooms=rooms, uid=uid)
        else:
            assert room.bans[user] is not None
            bans = room.bans[user]
            blst = []
            for course in bans.keys():
                blst.append({
                    'kch': course.kch,
                    'kxh': course.kxh,
                    'reason': bans[course]
                })
            opt = {
                'id': room.roomId,
                'name': room.name,
                'desc': replaceReturn(room.desc),
                'workers': room.workers,
                'flh': room.flh,
                'kcm': room.kcm,
                'kch': room.kch,
                'in_room': 1,
                'ban_list': blst
            }
            return flask.render_template('room_detail.html', room=opt)


@app.route('/rooms/show_detail', methods=["POST"])
def room_detail():
    rid = flask.request.form.get('rid', '')
    if rid == '':
        return 'Error'
    else:
        rid = int(rid)
        room = manager.getRoom(rid)
        if room is None:
            return 'Error'
        else:
            opt = {
                'id': room.roomId,
                'name': room.name,
                'desc': replaceReturn(room.desc),
                'workers': room.workers,
                'flh': room.flh,
                'kcm': room.kcm,
                'kch': room.kch,
                'in_room': 0
            }
            return flask.render_template('room_detail.html', room=opt)


@app.route('/rooms/add', methods=["POST", "GET"])
def add_room():
    return flask.render_template('add_room.html')


@app.route('/rooms/do_add', methods=["POST", "GET"])
def do_add_room():
    name = flask.request.form.get('name', '')
    desc = flask.request.form.get('desc', '')
    flh = flask.request.form.get('flh', '')
    kch = flask.request.form.get('kch', '')
    kcm = flask.request.form.get('kcm', '')
    uid = flask.request.form.get('uid', '')
    type = flask.request.form.get('type', '')
    users = flask.session.get('accounts', [])
    if not checkUserInList(uid, users):
        return 'Error'

    if name == '' or uid == '':
        return 'Error'
    else:
        user = manager.getUser(uid)
        if user is not None:
            type = int(type)
            if type < 0 or type > 3:
                return 'Error'
            else:
                manager.createRoom(name, desc, flh, kch, kcm, user, type)
                return 'OK'
        else:
            return 'Error'


@app.route('/rooms/join', methods=["POST"])
def join_room():
    uid = flask.request.form.get('uid', '')
    rid = flask.request.form.get('rid', '')
    
    users = flask.session.get('accounts', [])
    if not checkUserInList(uid, users):
        return 'Error'
    if uid == '' or rid == '':
        return 'Error'
    else:
        rid = int(rid)
        room = manager.getRoom(rid)
        if room is None:
            return 'Error'
        user = manager.getUser(uid)
        if user is None:
            return 'Error'
        if manager.ship[user] is not None:
            return 'Error'
        manager.joinRoom(room, user)
        return 'OK'


@app.route('/rooms/exit', methods=["POST"])
def exit_room():
    uid = flask.request.form.get('uid', '')
    users = flask.session.get('accounts', [])
    if not checkUserInList(uid, users):
        return 'Error'
    if uid == '':
        return 'Error'
    else:
        manager.exitRoom(uid)
        return 'OK'


@app.route('/rooms/add_ban', methods=["POST"])
def add_ban():
    kch = flask.request.form.get('kch', '')
    kxh = flask.request.form.get('kxh', '')
    uid = flask.request.form.get('uid', '')
    users = flask.session.get('accounts', [])
    if not checkUserInList(uid, users):
        return 'Error'
    if kch == '' or kxh == '' or uid == '':
        return 'Error'
    else:
        user = manager.getUser(uid)
        room = manager.getUserRoom(user)
        room.addBan(user, kch, kxh, "自定义禁止课程")
        return 'OK'


@app.route('/rooms/del_ban', methods=["POST"])
def del_ban():
    uid = flask.request.form.get('uid', '')
    kch = flask.request.form.get('kch', '')
    kxh = flask.request.form.get('kxh', '')
    users = flask.session.get('accounts', [])
    if not checkUserInList(uid, users):
        return 'Error'
    if kch == '' or kxh == '' or uid == '':
        return 'Error'
    else:
        user = manager.getUser(uid)
        room = manager.getUserRoom(user)
        room.delBan(user, kch, kxh)
        return 'OK'


def main():
    #app.run(host="0.0.0.0", port=8127)
    http_server = HTTPServer(WSGIContainer(app))
    http_server.listen(8127)  #flask默认的端口
    IOLoop.instance().start()

if __name__ == '__main__':
    try:
        if os.path.exists('backup.pkl'):
            tmp = pickle.load(open('backup.pkl', 'rb'))
            manager = Manager(tmp['rooms'], tmp['ship'])
        else:
            manager = Manager()
        manager.run()
        main()
    except Exception as e:
        print(e)
        manager.dump()
