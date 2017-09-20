#encoding=utf-8
import os.path as _Os_path

from model import get_model
from model import characters
from model import width
from model import height
from model import n_len
from keras.models import *
from keras.layers import *
from keras import backend as K
import cv2
from StringIO import StringIO
import numpy as np

import tensorflow as tf 


def Detector_single_image(image , model_dir = 'model.predict_new.h5'):
	img = cv2.resize(image, (width, height))

	X_test = np.zeros((1, width, height, 3), dtype=np.int16)
	X_test[0]=img.transpose(1,0,2)

	y_pred = predict_model.predict(X_test)
	y_pred = y_pred[:,2:,:]
        
	text_list = K.get_value(K.ctc_decode(y_pred, input_length=np.ones(y_pred.shape[0])*y_pred.shape[1], )[0][0])[:, :n_len]

	out = ''.join([characters[x] for x in text_list[0]])

	print(out)

'''
example1
predict_model = load_model('model.predict_new.h5')
Detector_single_image('/home/liujiashuo/Desktop/img/2BFT.jpg')
Detector_single_image('/home/liujiashuo/Desktop/img/2B3KV.jpg')
Detector_single_image('/home/liujiashuo/Desktop/img/2B4F.jpg')

example2
Detector_multi_images('/home/liujiashuo/Desktop/TEST' , 16)

'''


        






