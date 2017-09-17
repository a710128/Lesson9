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
"""======= Urls ======="""

"""======= Reqs ======="""
RX_QUERY_STRING = 'm=rxSearch&page={page}&token={token}&p_sort.p1=bkskyl' + \
                  '&p_sort.p2=&p_sort.asc1=false&p_sort.asc2=true&p_xnxq=' +\
                  TIME_PERIOD + '&is_zyrxk=&tokenPriFlag=rx&p_kch={kch}&p_kcm={kcm}' + \
                  '&p_kkdwnm=&p_kctsm={flh}&p_rxklxm=&goPageNumber=0'

RX_POST_STRING = "m=saveRxKc&page=&token={token}&p_sort.p1=bkskyl&p_sort.p2=" + \
                 "&p_sort.asc1=false&p_sort.asc2=true&p_xnxq=" + TIME_PERIOD + \
                 "&is_zyrxk=&tokenPriFlag=rx&p_kch={kch}&p_kcm={kcm}&p_kkdwnm=&p_kctsm={flh}&p_rxklxm="
"""======= Reqs ======="""

DEBUG = True
