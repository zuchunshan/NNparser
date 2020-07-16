# -*- coding: utf-8 -*-
"""
Created on Mon Jul  6 10:33:46 2020

@author: LL
"""
import tensorflow.keras as keras
import numpy as np
import  pandas as pd
import utils.formattable as ft

def headgen(isconv):
    # to do: adjust the names according to models
    paralist = []
    if isconv:     
        dim =3 # 4 dim tensor: BHWC, no B
        linput=['I0_'+str(i) for i in range(dim)] + ['I1_'+str(i) for i in range(dim)]
        loutput=['O_'+str(i) for i in range(dim)]
        lweights = ['K_1','K_2','S_1','S_2','p_1','p_2']
        largs =['SizeI','SizeO','SizeW','OpGemm','OpElem','OpActi']
        row0 = ['layer','type'] +linput + loutput + lweights + largs+['Misc']

    else:
        dim=2 # 3 dim: B+ 1XW vector,no B
        linput=['I0_'+str(i) for i in range(dim)] + ['I1_'+str(i) for i in range(dim)]
        loutput=['O_'+str(i) for i in range(dim)]
        lweights = []
        largs =['SizeI','SizeO','SizeW','OpGemm','OpElem','OpActi']
        row0 = ['layer','type'] +linput + loutput + lweights + largs+['Misc']

    paralist.append(row0)
    # paralist.append(row1)
    return paralist

def inputgen(x,inp0,inp1,extin):
    # input tensors
    if not isinstance(x.input, list): # single input
        datai0=1
        for i in range(1,4,1):
            try:
                inp0[i-1]=x.input.shape[i]                
            except IndexError:
                None
        for item in inp0:
            if isinstance(item,int):
                datai0=datai0*item            
        datai=(datai0)
    elif len(x.input)>1:       # 2 inputs
        datai0=1
        for i in range(1,4,1):            
            try:
                inp0[i-1]=x.input[0].shape[i]
            except IndexError:
                None
        for item in inp0:
            if isinstance(item,int):
                datai0=datai0*item 
        datai1=1
        for i in range(1,4,1):
            try:
                inp1[i-1]=x.input[1].shape[i]
            except IndexError:
                None
        for item in inp1:
            if isinstance(item,int):
                datai1=datai1*item 
        datai=(datai0+datai1)
        if len(x.input)>2:
            for inp in x.input_shape[2:]:
                tmp = inp[1:]
                dtmp = 1
                for item in tmp:
                    if isinstance(item,int):
                        dtmp=dtmp*item
                datai += dtmp
                extin = extin + str(tmp) + ', '
            extin = extin[:-1]
    return inp0,inp1,datai,extin

def outputgen(x,out,extin):            
    # output: 
    if not isinstance(x.output, list): 
        # single output：2d vector or 4d tensor: batch x oh x ow x oc
        datao=1
        for i in range(1,4,1):            
            try:
                out[i-1]=x.output.shape[i]
            except IndexError:
                None
        for item in out:
            if isinstance(item,int):
                datao=datao*item     
    else: # output0,size of more outputs
        datao=1
        for i in range(1,4,1):            
            try:
                out[i-1]=x.output[0].shape[i]
            except IndexError:
                None
        for item in out:
            if isinstance(item,int):
                datao=datao*item 
        if len(x.output)>1:
            extin += ';' # addtional output
        for i in range(1,len(x.output),1):
            dtmp=1 
            tmp=x.output[i].shape
            for item in tmp:
                if isinstance(item,int):
                    dtmp=dtmp*item
            datao +=dtmp
            extin += str(tmp) + ','
        extin = extin[:-1]
    ltype = str(type(x)).split(".")[-1].split("'")[0]
    if ltype:
         if ltype=='MultiHeadAttention': #attentio layer
                     # outputs: features of a sentence
            seqlen = x.input_shape[1]
            datao= datao*seqlen
            out[0] = seqlen # to fix output dim1 = None
         
    return out,datao,extin

def getweightsize(x,dataw):    
    weights=x.get_weights()
    if len(weights)>0: 
        dataw=0
        for item in weights:
            dataw += np.prod(item.shape)
    return dataw

def opscomputation(x,datao,inp0):    
    ltype = str(type(x)).split(".")[-1].split("'")[0]
    gemm=''; vect='' ; acti =''
    if ltype:
        if ltype=='BatchNormalization': # BN
            vect = datao*2 #1 elem* 1elem+
        if ltype=='Add': #add layer
            vect = datao # output tensor size
        if ltype=='LayerNormalization': #add layer
            acti = datao # output tensor size
        if ltype=='MultiHeadAttention': #attentio layer
            head = x.head_num
            seqlen,emblen = inp0[:2]
            keylen =emblen//head # feature_dim
            gemm=0; vect=0; acti=0
            #one head of one sentence
            ub = 1 if x.use_bias else 0
            # Q*K'= X*W_q*W_k'*X'
            QS = seqlen*emblen*keylen + seqlen*keylen*ub # size: seqlen*keylen
            KS = seqlen*emblen*keylen + seqlen*keylen*ub # size: seqlen*keylen
            gemm += QS+KS + seqlen*keylen*seqlen
            # / sqrt(kenlen)
            vect += seqlen*seqlen
            # softmax
            acti += seqlen*seqlen 
            # f(Q*K') * (x*W_v), Wv emblen*keylen (same dim on W_q,W_k,W_v)
            VS = seqlen*emblen*keylen + seqlen*keylen*ub # V: seqlen*keylen
            FV = seqlen*seqlen*keylen # F(QK)*V: seqlen*keylen
            gemm += VS+FV 
            gemmoh = gemm
            vectoh = vect
            actioh = acti
            # multihead
            # concate
            keylen=keylen*head
            gemm = gemm*head
            vect = vect*head
            acti = acti*head
            # x*W_o
            gemm += seqlen*keylen*emblen + seqlen*emblen*ub
            gemm = [gemmoh, gemm]
            vect = [vectoh,vect]
            acti = [actioh, acti]
            

            
        if ltype=='LayerNormalization': #attentio layer
            seqlen,emblen = inp0[:2]
            vect=0; acti=0
            #  along last dim, emb dim
            # mean
            vect += (seqlen-1)
            # var:sum(x*x-mx)
            vect += (seqlen*3-1)
            # std: sqrt(var+epsi)
            vect += (seqlen)
            acti += (seqlen)
            # output:( x-mx)/std
            vect += (seqlen*2)
        
        if ltype=='FeedForward': #attentio layer
            seqlen,emblen = inp0[:2]
            units=x.units
            gemm=0; acti=0
            ub = 1 if x.use_bias else 0
            # w1x+b
            gemm += seqlen*emblen*units +seqlen*units*ub
            acti += seqlen*units #gelu
            # w2x+b
            gemm += seqlen*units*emblen +seqlen*emblen*ub
            acti += seqlen*emblen
        
        if ltype=='Dense':
            lens = x.input_shape[1]
            ub = 1 if x.use_bias else 0
            units=x.units
            gemm = lens*units+ units*ub#1 add 2mac
            acti = lens*ub
            
        if ltype=='Conv2D':
            gemm=np.prod(x.kernel_size)*inp0[2]*datao
            
        if ltype== 'GlobalAveragePooling2D':
            vect=datao*(inp0[0]*inp0[1]-1) #add op
            
        if ltype=='Activation':
            acti = datao  #activation functions
        
        if ltype=='DepthwiseConv2D':
            gemm=np.prod(x.kernel_size)*datao
        
        if ltype=='MaxPooling2D':
            vect=datao*(np.prod(x.pool_size)-1) #max op
    return gemm,vect,acti

def pararetrival(x):
    conf = x.get_config()  
    kh = ''; kw=''; sh = ''; sw=''; ph = ''; pw=''
    # Conv2d, MaxPooling2D, 
    if isinstance(x, keras.layers.Conv2D):
        # kernel size
        kh, kw = x.kernel_size
        # stride size
        sh, sw = x.strides
        # padding
        if conf['padding']=='valid':
            ph=0
            pw=0
        elif conf['padding']=='same':
            ph=kh//2
            pw=kw//2
    
 
    if isinstance(x, keras.layers.DepthwiseConv2D):
        # kernel size
        kh, kw = x.kernel_size
        # stride size
        sh, sw = x.strides
        # padding
        if conf['padding']=='valid':
            ph=0
            pw=0
        elif conf['padding']=='same':
            ph=kh//2
            pw=kw//2
           
    if isinstance(x, keras.layers.MaxPooling2D): # ignore GlobalAveragePooling2D
        # kernel size
        kh, kw = x.pool_size
        # stride size
        sh, sw = x.strides
        # padding
        if conf['padding']=='valid':
            ph=0
            pw=0
        elif conf['padding']=='same':
            ph=kh//2
            pw=kw//2
    return kh,kw,sh,sw,ph,pw


def GetModel(nnname):
    isconv = True

    import tensorflow.keras.applications as nn
 
    if hasattr(nn,nnname):
        model = getattr(nn, nnname)(weights=None)
        
    # efficientnet: B0-B7
    elif nnname[:-2] == 'EfficientNet':
        import tfmodels.efficientnet.tfkeras as nn
        model = getattr(nn, nnname)(weights=None)
    
    # TF2.x Models:
    elif nnname == 'ncf':
        import tfmodels.ncf as nn
        name = 'ncfmodel'
        model = getattr(nn, name)(istrain=False)
        isconv = False
    
    elif nnname == 'din':
        import tfmodels.din as nn
        name = 'din'
        _, model = getattr(nn, name)(item_count=63001, cate_count=801, hidden_units=128)
        isconv = False
    
    elif nnname == 'bert':
        isconv =False
        from keras_bert import get_base_dict, get_model, compile_model
        # Build token dictionary
        token_dict = get_base_dict()
        training = False
        if training:
            model = get_model(token_num=len(token_dict),training=training)
        else:
            # Revise lib\site-packages\keras_bert\bert.py: line164
            # "return inputs, transformed" -> "return inputs, transformed,model"
            _,_,model = get_model(token_num=len(token_dict),training=training)
         
        compile_model(model)
    return model,isconv

def ListGen(model,isconv):
    paralist=headgen(isconv)
    for x in model.layers: #model.layers[::-1]
         # no batch, hxwxc
        inp0=['']*3; inp1=['']*3; out=['']*3
        kh = ''; kw=''; sh = ''; sw=''; ph = ''; pw=''
        extin=''
        datai=''; datao=''; dataw=''
        gemm=''; vect='' ; acti =''
        ltype = str(type(x)).split(".")[-1].split("'")[0]
        # if x.name=='Encoder-1-FeedForward':
        #     print(x.name)
        #print(x.name)
        
        # input tensor & size
        (inp0, inp1, datai, extin) = inputgen(x,inp0,inp1,extin)
        # output tensor & size
        (out,datao,extin) = outputgen(x,out,extin)
        # weight size
        dataw = getweightsize(x,dataw)
        # # of ops: gemm, elememwise, activiation(transcendental functions)
        (gemm, vect, acti) = opscomputation(x,datao,inp0)
        # conv tensor
        (kh, kw, sh, sw, ph, pw) = pararetrival(x)
       
        xtype=str(type(x))
        if xtype.find('Embedding')>0:
            # todo: inputdim??
            vocalsize = inp0[0]
            embsize = out[0]
            seqlen = inp0[0]
         
        # if isinstance(x, keras.layers.Lambda):
        #     print('')
            
        if isconv:
            new_row = [x.name,ltype]+ inp0+inp1+out+[kh,kw,sh,sw,ph,pw,datai,datao,dataw,gemm,vect,acti,extin]
            paralist.append(new_row)
        else:
            doublerow = False
            dim=2
            if isinstance(gemm,list): 
                if doublerow: # multihead attention: tow rows
                    new_row = [x.name,ltype]+ inp0[:dim]+inp1[:dim]+out[:dim]+[datai,datao,dataw,gemm[0],vect[0],acti[0],extin]
                    paralist.append(new_row)
                    new_row = ['']*11+[gemm[1],vect[1],acti[1]]+['']
                    paralist.append(new_row)
                else:
                    new_row = [x.name,ltype]+ inp0[:dim]+inp1[:dim]+out[:dim]+[datai,datao,dataw,gemm[1],vect[1],acti[1],extin]
                    paralist.append(new_row)
            else:
                new_row = [x.name,ltype]+ inp0[:dim]+inp1[:dim]+out[:dim]+[datai,datao,dataw,gemm,vect,acti,extin]
                paralist.append(new_row)
    return paralist


def tableExport(paralist,nnname):
    df = pd.DataFrame(paralist)
    paraout = './/outputs//tf//'+nnname+'.xlsx'  
    with pd.ExcelWriter(paraout) as writer:
        df.to_excel(writer,sheet_name='details')
        # dfsum.to_excel(writer,sheet_name='summary',index=Flase)
        writer.save()
    writer.close()
    
    maxVal=ft.SumTable(paraout)
    ft.FormatTable(paraout,maxVal)