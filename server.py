import flask
from web import config
from manager import Manager
import time

manager = Manager()
manager.run()

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
    # use session here
    users = flask.session.get('accounts', [])
    return flask.render_template('account_list.html', users=users)


@app.route("/account/manager", methods=["POST"])
def account_manager():
    return flask.render_template("account_manager.html")


def main():
    app.run(host="0.0.0.0", port=8127)

if __name__ == '__main__':
    main()
