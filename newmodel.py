# -*- coding: utf-8 -*-
"""
Created on Tue Aug 11 10:19:50 2020

@author: LL
"""


def pymodel():
    import torch   
    depth=6
    isconv = True
    import sys    
    # absolute path of the model file
    model_path = 'your path'
    model_path = 'D:\ll\github\mlperf-inference\others\edge\object_detection\ssd_mobilenet\pytorch'
    sys.path.append(model_path)
    
    # load model
    from ssd_mobilenet_v1 import create_mobilenetv1_ssd
    model = create_mobilenetv1_ssd(91)
    # define the inputs for the tensor
    x = torch.rand(1,3, 300, 300)
    # excute the model 
    y = model(x)

    # define the input tensor for parser
    # input is formatted as a tuple (tensors, args)
    # tensors is list of input tensors (if multiple inputs)
    # args is the list of paramters/settings for model excution (if any)
    inputs =([x],)    
    sys.path.remove(model_path)    

    return inputs, model, depth, isconv,y


def tfmodel():
    isconv = True
    import sys    
    # absolute path of the model file
    model_path = 'D:\\tmp'
    sys.path.append(model_path)
    from simpleconv import simpleconv
    model = simpleconv()    
    return model,isconv