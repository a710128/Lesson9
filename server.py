import flask
from web import config
from manager import Manager
import time
import os
import pickle


manager = None

app = flask.Flask(__name__, template_folder="web/templates", static_folder="web/static")
app.debug = config.debug
app.secret_key = config.secret_key


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
        manager.delUser(uid)
        # update session
        users = flask.session.get('accounts', [])
        opt = []
        for user in users:
            if user['name'] != uid:
                opt.append(user)
        flask.session['accounts'] = opt
        return 'OK'


def main():
    app.run(host="0.0.0.0", port=8127)

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
