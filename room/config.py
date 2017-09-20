"""
    Config
"""

"""======= Main ======="""
WEB_PREFIX = "http://zhjwxk.cic.tsinghua.edu.cn/"
TIME_PERIOD = "2017-2018-1"
"""======= Main ======="""


"""======= Urls ======="""
RX_POST_URL = WEB_PREFIX + "xkBks.vxkBksXkbBs.do"
RX_GET_URL = WEB_PREFIX + "xkBks.vxkBksXkbBs.do?m=rxSearch&p_xnxq=" + TIME_PERIOD + "&tokenPriFlag=rx&is_zyrxk=1"

BX_POST_URL = WEB_PREFIX + "xkBks.vxkBksXkbBs.do"
BX_GET_URL = WEB_PREFIX + "xkBks.vxkBksXkbBs.do?m=bxSearch&p_xnxq=" + TIME_PERIOD + "&tokenPriFlag=bx"

XX_POST_URL = WEB_PREFIX + "xkBks.vxkBksXkbBs.do"
XX_GET_URL = WEB_PREFIX + "xkBks.vxkBksXkbBs.do?m=xxSearch&p_xnxq=" + TIME_PERIOD + "&tokenPriFlag=xx"

TY_GET_URL = WEB_PREFIX + "xkBks.vxkBksXkbBs.do?m=tySearch&p_xnxq=" + TIME_PERIOD + "&tokenPriFlag=ty"
TY_POST_URL = WEB_PREFIX + "xkBks.vxkBksXkbBs.do"
"""======= Urls ======="""

"""======= Reqs ======="""
RX_QUERY_STRING = 'm=rxSearch&page={page}&token={token}&p_sort.p1=bkskyl' + \
                  '&p_sort.p2=&p_sort.asc1=false&p_sort.asc2=true&p_xnxq=' +\
                  TIME_PERIOD + '&is_zyrxk=&tokenPriFlag=rx&p_kch={kch}&p_kcm={kcm}' + \
                  '&p_kkdwnm=&p_kctsm={flh}&p_rxklxm=&goPageNumber=0'

RX_POST_STRING = "m=saveRxKc&page=&token={token}&p_sort.p1=bkskyl&p_sort.p2=" + \
                 "&p_sort.asc1=false&p_sort.asc2=true&p_xnxq=" + TIME_PERIOD + \
                 "&is_zyrxk=&tokenPriFlag=rx&p_kch={kch}&p_kcm={kcm}&p_kkdwnm=&p_kctsm={flh}&p_rxklxm="

BX_POST_STRING = "m=saveBxKc&token={token}&p_xnxq=" + TIME_PERIOD + "&tokenPriFlag=bx&page=&p_kch=&p_kcm="
XX_POST_STRING = "m=saveXxKc&token={token}&p_xnxq=" + TIME_PERIOD + "&tokenPriFlag=xx&page=&p_kch=&p_kcm="

TY_QUERY_STRING = 'm=tySearch&page={page}&token={token}&p_sort.p1=bkskyl' + \
                  '&p_sort.p2=&p_sort.asc1=false&p_sort.asc2=true&p_xnxq=' + \
                  TIME_PERIOD + '&rxTyType=&tokenPriFlag=ty&p_kch={kch}&p_kxh=&p_kcm={kcm}&goPageNumber=1'
TY_POST_STRING = 'm=saveTyKc&page=&token={token}&p_sort.p1=&p_sort.p2=&p_sort.asc1=true&p_sort.asc2=true&p_xnxq=' + \
                 TIME_PERIOD + '&rxTyType=&tokenPriFlag=ty&p_kch={kch}&p_kxh=&p_kcm={kcm}&goPageNumber=1'
"""======= Reqs ======="""

DEBUG = False
