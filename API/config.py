"""
    Config
"""

"""======= Main ======="""
WEB_PREFIX = "http://zhjwxk.cic.tsinghua.edu.cn/"
"""======= Main ======="""


"""======= Urls ======="""
CAPTCHAR_PATH = WEB_PREFIX + "login-jcaptcah.jpg?captchaflag=login1"
LOGIN_PAGE = WEB_PREFIX + "xklogin.do"
#LOGIN_POST_PAGE = WEB_PREFIX + "j_acegi_formlogin_xsxk.do"
LOGIN_POST_PAGE = 'https://zhjwxk.cic.tsinghua.edu.cn:443/j_acegi_formlogin_xsxk.do'
"""======= Urls ======="""


DEBUG = False
