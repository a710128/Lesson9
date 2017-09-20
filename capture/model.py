import tensorflow as tf
from keras.models import *
from keras.layers import *
from keras import backend as K
import numpy as np
import random
import datetime
import cPickle
import os
import gc
import string
characters = string.digits + string.ascii_lowercase+string.ascii_uppercase + ' '
width, height, n_len, n_class = 200, 60, 6, len(characters)

def make_parallel(model, gpu_count):
    import tensorflow as tf
    def get_slice(data, idx, parts):
        import tensorflow as tf
        shape = tf.shape(data)
        size = tf.concat([ shape[:1] // parts, shape[1:] ],axis=0)
        stride = tf.concat([ shape[:1] // parts, shape[1:]*0 ],axis=0)
        start = stride * idx
        return tf.slice(data, start, size)

    outputs_all = []
    for i in range(len(model.outputs)):
        outputs_all.append([])
    #Place a copy of the model on each GPU, each getting a slice of the batch
    for i in range(gpu_count):
        with tf.device('/gpu:%d' % i):
            with tf.name_scope('tower_%d' % i) as scope:
                inputs = []
                #Slice each input into a piece for processing on this GPU
                j=0
                for x in model.inputs:
                    input_shape = tuple(x.get_shape().as_list())[1:]
                    slice_n = Lambda(get_slice, output_shape=input_shape, arguments={'idx':i,'parts':gpu_count},name='input_%d_%d' %(i,j))(x)
                    inputs.append(slice_n) 
                    j=j+1
                outputs = model(inputs)
                if not isinstance(outputs, list):
                    outputs = [outputs]        
                #Save all the outputs for merging back together later
                for l in range(len(outputs)):
                    outputs_all[l].append(outputs[l])
    with tf.device('/cpu:0'):
        merged = []
        for outputs in outputs_all:
            merged.append(concatenate(outputs,axis=0,name='loss_tensor'))
        return Model(inputs=model.inputs, outputs=merged)
    
def ctc_lambda_func(args):
    y_pred, labels, input_length, label_length = args
    y_pred = y_pred[:, 2:, :]
    return K.ctc_batch_cost(labels, y_pred, input_length, label_length)

def get_model(gpu_num=1):
    input_tensor = Input((width, height, 3),name="input_tensor")
    x = input_tensor
    for i in range(3):
        x = Conv2D(32,(3, 3), activation='relu')(x)
        x = Conv2D(32, (3, 3), activation='relu')(x)
        x = MaxPooling2D(pool_size=(2, 2))(x)

    conv_shape = x.get_shape()
    x = Reshape(name="x_shape_tensor",target_shape=(int(conv_shape[1]), int(conv_shape[2]*conv_shape[3])))(x)
    x = Dense(32, activation='relu')(x)

    lstm_1 = LSTM(128, return_sequences=True, name='lstm1')(x)
    lstm_1b = LSTM(128, return_sequences=True, go_backwards=True,name='lstm1_b')(x)
    lstm1_merged = add([lstm_1, lstm_1b])

    lstm_2 = LSTM(128, return_sequences=True,name='lstm2')(lstm1_merged)
    lstm_2b = LSTM(128, return_sequences=True, go_backwards=True, name='lstm2_b')(lstm1_merged)
    x = concatenate([lstm_2, lstm_2b])
    x = Dropout(0.25)(x)
    x = Dense(n_class, activation='softmax',name="output_tensor")(x)


    labels = Input(name='the_labels', shape=[n_len], dtype='float32')
    input_length = Input(name='input_length', shape=[1], dtype='int64')
    label_length = Input(name='label_length', shape=[1], dtype='int64')
    loss_out = Lambda(ctc_lambda_func, output_shape=(1,), name='ctc')([x, labels, input_length, label_length])
    model = Model(inputs=[input_tensor, labels, input_length, label_length], outputs=[loss_out],name="base_model")
    if gpu_num > 1:
        model = make_parallel(model,gpu_num)
        model.compile(loss={'loss_tensor': lambda y_true, y_pred: y_pred}, optimizer='adadelta')
    else:
        model.compile(loss={'ctc': lambda y_true, y_pred: y_pred}, optimizer='adadelta')
    return model