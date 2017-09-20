'''
This script is used to test the capture idft.
'''
import urllib3
import capture
import cv2
import numpy as np

http = urllib3.PoolManager()

while True:
	data = http.request('GET', 'http://zhjwxk.cic.tsinghua.edu.cn/login-jcaptcah.jpg?captchaflag=login1').data
	img = cv2.imdecode(np.array(np.fromstring(data, np.uint8), dtype='uint8'), cv2.IMREAD_ANYCOLOR)
	print(capture.Detector_single_image(img))
	cv2.imshow('captrue', img)
	cv2.waitKey(0)