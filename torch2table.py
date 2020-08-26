# -*- coding: utf-8 -*-
"""
Created on Mon Jul  5  2020

@author: LL
"""
import nnutils.pytools as pt

# Tested Models
# 1. torchvision: 
#    alexnet, vgg11, vgg13, vgg16, vgg19, vgg11_bn, vgg_13 bn, vgg16_bn,
#   vgg19_bn, resnet18, resnet34, resnet50, resnet101, resnet152, 
#   squeezenet1_0, squeezenet1_1, densenet121, densenet_169, densenet_201
#   densenet_161,  googlenet, shufflenet_v2_x'n'_'n', mobilenet_v2
#   resnext50_32x4d, resnext101_32x8d, wide_resnet50_2, wide_resnet101_2
#   mnasnet'n'_'n'

# 2. Recomendation:
#    dlrm

# 3. Detection: maskrcnn, ssd_mobilenet, ssd_r34
# 4. RNN: lstm,gru
# 5. NLP: gnmt

import argparse
parser = argparse.ArgumentParser()
parser.add_argument("-n","--nnname", help="Neural Network to be parsed",
                    default='alexnet')
parser.add_argument("-b","--batchsize", help="Batch Sized",
                    default=1, type=int)
parser.add_argument("-e","--BPE", help="Byte per element",
                    default=1, type=int)
parser.add_argument("--model", help="name of new model",
                    default='ssd_mob', type=str)
args = parser.parse_args()


# producing the table of the model paramter list
(ms, depth, isconv,y) = pt.modelLst(vars(args))    
ms = pt.tableGen(ms,depth,isconv)

# exporting the table at //output//torch//
if args.nnname == 'newmodel':
    nnname = args.model
else:
    nnname = args.nnname
    
pt.tableExport(ms,nnname,y)