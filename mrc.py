#!/usr/bin/env python


#zhijie.li@utoronto.ca


from __future__ import print_function

import numpy as np
import os
import struct
import io
import argparse
import sys
import common
import re

NUMPY_MODE = {
        0: np.dtype(np.int8),
        1: np.dtype(np.int16),
        2: np.dtype(np.float32),
        6: np.dtype(np.uint16),
        np.dtype(np.int8):    0,
        np.dtype(np.int16):   1,
        np.dtype(np.float32): 2,
        np.dtype(np.uint16):  6
       }

DSIZE_TABLE={
                0 : 1,
                1 : 2,
                2 : 4,  #normally should be this
                3  : 4,
                4 : 8,
                6 : 2
  }
MODE_TABLE_HUMAN={  0 : "8-bit signed integer (range -128 to 127)",
                1 : "16-bit Int (2 Bytes)",
                2 : "32-bit Real (4 Bytes)",  #normally should be this
                3  : "Complex 16-bit (4 Bytes)",
                4 : "Complex 32-bit  (8 Bytes)",
                5 : "mode 5: unkown",
                6 : "16-bit unsigned Int (2 Bytes)"
  }
###RELION recently introduced mode 101:4-bit int for movies

HEADER_PACK_TABLE={     'MRC_NX'            : [   0 , 4	  ,'<i'  ,    0 ], #[start,end,type,default]
                        'MRC_NY'            : [   4 , 8	  ,'<i'  ,    0 ],
                        'MRC_NZ'            : [   8 , 12  ,'<i'  ,    0 ],
                        'MRC_MAPMODE'       : [  12 , 16	,'<i'  ,    2 ],
                        'MRC_NXSTART'       : [  16 , 20	,  '<f',    0 ],
                        'MRC_NYSTART'       : [  20 , 24	,  '<f',    0 ],
                        'MRC_NZSTART'       : [  24 , 28	,  '<f',    0 ],
                        'MRC_MX'            : [  28 , 32	,'<i'  ,    0 ],
                        'MRC_MY'            : [  32 , 36	,'<i'  ,    0 ],
                        'MRC_MZ'            : [  36 , 40	,'<i'  ,    0 ],
                        'MRC_CELL_A'        : [  40 , 44	,  '<f',    0 ],
                        'MRC_CELL_B'        : [  44 , 48  ,  '<f',    0 ],
                        'MRC_CELL_C'        : [  48 , 52  ,  '<f',    0 ],
                        'MRC_CELL_ALPHA'    : [  52 , 56	,  '<f',   90 ],
                        'MRC_CELL_BETA'     : [  56 , 60  ,  '<f',   90 ],
                        'MRC_CELL_GAMMA'    : [  60 , 64  ,  '<f',   90 ],
                        'MRC_MAPC'          : [  64 , 68  ,'<i'  ,    1 ],
                        'MRC_MAPR'          : [  68 , 72  ,'<i'  ,    2 ],
                        'MRC_MAPS'          : [  72 , 76  ,'<i'  ,    3 ],
                        'MRC_DMIN'          : [  76 , 80	,  '<f',    0 ],
                        'MRC_DMAX'          : [  80 , 84	,  '<f',    0 ],
                        'MRC_DMEAN'         : [  84 , 88	,  '<f',    0 ],
                        'MRC_ISPG'          : [  88 , 92  ,'<i'  ,  401 ],
                        'MRC_NSYMBT'        : [  92 , 96  ,'<i'  ,    0 ],
                        'MRC_EXTTYP'        : [ 104 , 108 ,'4s'   ,'MRCO'],
                        'MRC_NVERSION'      : [ 108 , 112 ,'<i'  , 20140],
                        'MRC_ORIX'          : [ 196 , 200 ,  '<f',    0 ],
                        'MRC_ORIY'          : [ 200 , 204 ,  '<f',    0 ],
                        'MRC_ORIZ'          : [ 204 , 208 ,  '<f',    0 ],
                        'MRC_MAP_STR'       : [ 208 , 212 ,'4s'  ,'MAP '],
                        'MRC_MACHST_STRING' : [ 212 , 214 ,'2s'  ,'DA'  ],
                        'MRC_RMS'           : [ 216 , 220 ,  '<f',   -1 ],
                        'MRC_NLABL'         : [ 220 , 224 ,'<i'  ,    0 ],
                        'MRC_LABEL'         : [ 224 ,1024 ,'800s',chr(0)*800]
                   }
HEADER_ENTRIES_MINIMAL=( #save as  HEADER_PACK_TABLE.keys() but ordered
                 'MRC_NX'            ,
                 'MRC_NY'            ,
                 'MRC_NZ'            ,
                 'MRC_MAPMODE'       ,
                 'MRC_NXSTART'       ,
                 'MRC_NYSTART'       ,
                 'MRC_NZSTART'       ,
                 'MRC_MX'            ,
                 'MRC_MY'            ,
                 'MRC_MZ'            ,
                 'MRC_CELL_A'        ,
                 'MRC_CELL_B'        ,
                 'MRC_CELL_C'        ,
                 'MRC_CELL_ALPHA'    ,
                 'MRC_CELL_BETA'     ,
                 'MRC_CELL_GAMMA'    ,
                 'MRC_MAPC'          ,
                 'MRC_MAPR'          ,
                 'MRC_MAPS'          ,
                 'MRC_DMIN'          ,
                 'MRC_DMAX'          ,
                 'MRC_DMEAN'         ,
                 'MRC_ISPG'          ,
                 'MRC_NSYMBT'        ,
                 'MRC_EXTTYP'        ,
                 'MRC_NVERSION'      ,
                 'MRC_ORIX'          ,
                 'MRC_ORIY'          ,
                 'MRC_ORIZ'          ,
                 'MRC_MAP_STR'       ,
                 'MRC_MACHST_STRING' ,
                 'MRC_RMS'           ,
                 'MRC_NLABL'         ,
                 'MRC_LABEL'         ,
               )

EXTRA_HEADER_ENTRIES=(
                 'labelshort'        ,
                 'endianness'        ,
                 'MRC_apixX'         ,
                 'MRC_apixY'         ,
                 'MRC_apixZ'         ,
                 'MRC_EXTRA'         ,
                 'MRC_MACHST_INT'    ,
                 'ori_1024'
               )
MRC_CCP4={
    'MRC_NX'                : 'c'             ,
    'MRC_NY'                : 'r'             ,
    'MRC_NZ'                : 's'             ,
    'MRC_MAPMODE'           : 'mapmode'       ,
    'MRC_NXSTART'           : 'nxstart'       ,
    'MRC_NYSTART'           : 'nystart'       ,
    'MRC_NZSTART'           : 'nzstart'       ,
    'MRC_MX'                : 'nx'            ,
    'MRC_MY'                : 'ny'            ,
    'MRC_MZ'                : 'nz'            ,
    'MRC_CELL_A'            : 'x'             ,
    'MRC_CELL_B'            : 'y'             ,
    'MRC_CELL_C'            : 'z'             ,
    'MRC_CELL_ALPHA'        : 'alpha'         ,
    'MRC_CELL_BETA'         : 'beta'          ,
    'MRC_CELL_GAMMA'        : 'gamma'         ,
    'MRC_MAPC'              : 'mapc'          ,
    'MRC_MAPR'              : 'mapr'          ,
    'MRC_MAPS'              : 'maps'          ,
    'MRC_DMIN'              : 'amin'         ,
    'MRC_DMAX'              : 'amax'         ,
    'MRC_DMEAN'             : 'amean'         ,
    'MRC_ISPG'              : 'ispg'          ,
    'MRC_NSYMBT'            : 'nsymbt'        ,
    'MRC_EXTTYP'            : 'exttyp'        ,
    'MRC_NVERSION'          : 'nversion'      ,
    'MRC_ORIX'              : 'orix'          ,
    'MRC_ORIY'              : 'oriy'          ,
    'MRC_ORIZ'              : 'oriz'          ,
    'MRC_MAP_STR'           : 'map_str'       ,
    'MRC_MACHST_STRING'     : 'machst_string' ,
    'MRC_RMS'               : 'arms'          ,
    'MRC_NLABL'             : 'nlabl'         ,
    'MRC_LABEL'             : 'label'         
  }

def tiff_to_mrc(filename,args):
  (root,ext,base,file_dir)=common.find_dir(filename)
  base_ns=re.sub(r' ',r'_',base)
  print(base_ns)
  
  from EM_tiff import read_tiff
  data=read_tiff(filename)
  print(data.dtype,data.shape)
  amin=data.min()
  amax=data.max()
  arms=data.std()
  amean=data.mean()
  infstr=base_ns
  desc_data=''
  (ysize,xsize)=data.shape
  save_tif_mrc(data,args,'',infstr,desc_data,amax,amin,amean,arms,ysize,xsize,args.Apix)



def save_tif_mrc(data,args,filename,infstr,desc_data,amax,amin,amean,arms,ysize,xsize,apix):
  tif_name=filename+infstr+'.oridata.tif'
  tif8_name=filename+infstr+'.uint8.tif'
  mrc_name=filename+infstr+'.mrc'
  if(apix<=0):
    apix=1.00

  try:
      import EM_tiff
  except ImportError as e:
      print ("library file EM_tiff.py not found in search path. Make sure it is in save dir as the TIA_dump.py.")
      print(sys.path)
      return
  if(args.invtif8==True or args.tif8==True ):
    binned=data.reshape(ysize,xsize)
    if(args.bin !=None and int(args.bin)>1):
      from EM_tiff import bindata
      binned=bindata(data.reshape(ysize,xsize),int(args.bin))
      
    if(args.invtif8==True): 
      neg_data=binned*(-1) #invert
      tif8_name=filename+infstr+'.inv_uint8.tif'
      EM_tiff.save_tiff8(neg_data,desc_data,tif8_name,0,0,neg_data.shape[0],neg_data.shape[1],udate=True,sigma=args.sigma)     
    if(args.tif8==True): 
      EM_tiff.save_tiff8(binned,desc_data,tif8_name,0,0,binned.shape[0],binned.shape[1],udate=True,sigma=args.sigma)     
      
    

  if(args.tif == True):
    if(np.issubdtype(data.dtype, np.integer)):
      if(amin>=0 and amax<65536):
        data=data.astype(np.uint16)
      if(0>amin>=-65536/2 and amax<65536/2):
        data=data.astype(np.int16)
  
    EM_tiff.save_tiff16_no_rescaling(data,desc_data,tif_name,amax,amin,ysize,xsize)
    print("Saved original data to TIFF <{}> as {}\n".format(tif_name,data.dtype))  
      
    
    
  if(args.mrc == True  or args.tif2mrc==True):
    if(args.invmrc):
      data *=(-1)
      temp=amin
      amin=-amax
      amax=-temp
      amean=amean
      mrc_name=filename+infstr+'_inv.mrc'
      
    twoD_to_mrc(data,ysize,xsize,amin,amax,amean,arms,mrc_name,ext_text=desc_data,apix=apix)



def twoD_to_mrc(data,ysize,xsize,amin,amax,amean,arms,mrc_name,ext_text='',apix=1.0):
  '''Automatically determine if the data can be reduced to int16 or int8 and save data to mrc file. If data is not int, conversion will not be done.'''
  
  to_type=np.float32
  
  #if(data.dtype == np.int64  or data.dtype == np.int32  or data.dtype==np.int16 or     data.dtype == np.uint64 or data.dtype == np.uint32 or data.dtype==np.uint16):
  if(np.issubdtype(data.dtype, np.integer)):
    if(amax < 128 and amin >= -128):
      to_type=np.int8
      print("saving data as int8 MRC (mode 0)")

    elif(amax < 65536 and amin >= 0):
        to_type=np.uint16
        print("saving data as uint16 MRC (mode 6)")
    elif(amax < 65536/2 and amin >= -65536/2):
        to_type=np.int16
        print("saving data as int16 MRC (mode 1)")
  if( to_type==np.float32):
      print("saving data as float32 MRC (mode 2)")

  d1=data.reshape(1,ysize,xsize)
  data_out=d1
  if(d1.dtype != to_type):
    data_out = d1.astype(to_type) 
  
  save_mrc(mrc_name,data_out, desc=ext_text,hdr_apix=apix,hdr_max=amax,hdr_min=amin,hdr_mean=amean,hdr_rms=arms,update_stats=True)

  
def simple_write_mrc(mrc_name,header,exthdr,data_3d): #simple because header is only a 1024-byte string
      if(len(header)!=1024):
        print("error, header lenth wrong: {}".format(len(header)))
        return
        
      with open(mrc_name, 'wb') as f:
        if(hasattr(np.ndarray,'tobytes')): #better, but only exists in newer numpy
          #print("using ndarry.tobytes()")
          f.write(header)
          f.write(exthdr)
          f.write(data_3d.tobytes())
        else:
          #print("ndarry.tobytes() not availble, using alternative")
          f.write(header)
          f.write(exthdr)
          f.write(ndary_tobytes(data_3d))
          
          


    
######################################################################header_inf gen
def gen_blank_header_inf_dic():
  '''generate fresh blank header_inf dictionary'''
  
  header_inf={}
  for k in HEADER_PACK_TABLE.keys():
    header_inf[k]=HEADER_PACK_TABLE[k][3]
  header_inf['endianness']='LE'
  header_inf=make_alias_dic(header_inf)
  return header_inf                                           
def gen_header_inf_dic_from_data(data,apix=1.00,origin=[0,0,0]):
  '''generate blank header_inf dictionary from data'''
  z,y,x=data.shape
  
  header_inf=gen_blank_header_inf_dic()
  header_inf.update(  { 'MRC_NX'            :   x  ,
                        'MRC_NY'            :   y  ,
                        'MRC_NZ'            :   z  ,
                        'MRC_MAPMODE'       :   NUMPY_MODE[data.dtype]  ,
                        'MRC_NXSTART'       :   0  ,
                        'MRC_NYSTART'       :   0  ,
                        'MRC_NZSTART'       :   0  ,
                        'MRC_MX'            :   x  ,
                        'MRC_MY'            :   y  ,
                        'MRC_MZ'            :   z  ,
                        'MRC_CELL_A'        :   x*apix  ,
                        'MRC_CELL_B'        :   y*apix  ,
                        'MRC_CELL_C'        :   z*apix  ,
                        'MRC_CELL_ALPHA'    :   90  ,
                        'MRC_CELL_BETA'     :   90  ,
                        'MRC_CELL_GAMMA'    :   90  ,
                        'MRC_MAPC'          :   1  ,
                        'MRC_MAPR'          :   2  ,
                        'MRC_MAPS'          :   3  ,
                        'MRC_DMIN'          :   0  ,
                        'MRC_DMAX'          :   0  ,
                        'MRC_DMEAN'         :   0  ,
                        'MRC_ISPG'          : 401  ,
                        'MRC_NSYMBT'        :   0  ,
                        'MRC_EXTTYP'        :'MRCO',
                        'MRC_NVERSION'      :20140 ,
                        'MRC_ORIX'          :   origin[0]  ,
                        'MRC_ORIY'          :   origin[1]  ,
                        'MRC_ORIZ'          :   origin[2]  ,
                        'MRC_RMS'           :  -1  ,
                        'MRC_NLABL'         :   0  ,
                        'MRC_apixX'         :   apix  ,
                        'MRC_apixY'         :   apix  ,
                        'MRC_apixZ'         :   apix   })
  header_inf=make_alias_dic(header_inf)
  return header_inf

def update_header_inf(header_inf0,header_inf):
  modifiable=[ 'MRC_NXSTART'    ,
               'MRC_NYSTART'    ,
               'MRC_NZSTART'    ,
               'MRC_CELL_A'     ,
               'MRC_CELL_B'     ,
               'MRC_CELL_C'     ,
               'MRC_CELL_ALPHA' ,
               'MRC_CELL_BETA'  ,
               'MRC_CELL_GAMMA' ,
               'MRC_MAPC'       ,
               'MRC_MAPR'       ,
               'MRC_MAPS'       ,
               'MRC_DMIN'       ,
               'MRC_DMAX'       ,
               'MRC_DMEAN'      ,
               'MRC_ISPG'       ,
               'MRC_ORIX'       ,
               'MRC_ORIY'       ,
               'MRC_ORIZ'       ,
               'MRC_RMS'        ]
  for k in modifiable:
    if k in header_inf.keys():
      header_inf0[k]=header_inf[k]
  return   header_inf0


def complete_header_inf(header_inf):
  template=gen_blank_header_inf_dic()
  template=update_header_inf(template,header_inf)
  return template

def update_stats_header_inf(data,header_inf):
  amin=data.min()
  amax=data.max()
  arms=data.std()
  amean=data.mean()
  header_inf.update(dict(zip(('MRC_DMIN','MRC_DMAX','MRC_DMEAN','MRC_RMS'),(amin,amax,amean,arms))))
  header_inf=make_alias_dic(header_inf)
  print("==========Stats in header updated==========")
  print(gen_info(header_inf))
  print("===========================================")
  return header_inf

def make_alias_dic(header_inf): #
  for k in MRC_CCP4.keys():
    v=MRC_CCP4[k]
    if(k in header_inf.keys()):
    
      header_inf[v]=header_inf[k]
  
  return header_inf

####################header generation##################
def gen_blank_hdr1024():
  '''generate fresh blank header, everything will be zero'''
  hdr_1024_str=chr(0) *1024
  #hdr_1024_str[208:214]='MAP DA'
  for k in HEADER_PACK_TABLE.keys():
    s=HEADER_PACK_TABLE[k][0]
    e=HEADER_PACK_TABLE[k][1]
    t=HEADER_PACK_TABLE[k][2]
    v=HEADER_PACK_TABLE[k][3]
    hdr_1024_str=hdr_1024_str[ :s]+struct.pack(t,v)+hdr_1024_str[ e:]
  return hdr_1024_str


def mrc_header1024_from_dic(header_inf): 
  '''fresh header from header_inf dictionary only'''
  hdr_1024_str=gen_blank_hdr1024()
  
  for k in HEADER_PACK_TABLE.keys():
    if(k in header_inf.keys()):
      s=HEADER_PACK_TABLE[k][0]
      e=HEADER_PACK_TABLE[k][1]
      t=HEADER_PACK_TABLE[k][2]
      v=header_inf[k]
    hdr_1024_str=hdr_1024_str[ :s]+struct.pack(t,v)+hdr_1024_str[ e:]
  return hdr_1024_str

def mrc_header1024_from_data3d(data_3d,apix=1.00): 
  '''fresh header from header_inf dictionary only'''
  if data_3d.dtype not in NUMPY_MODE:
     Print("Error!! Invalid dtype for MRC. Not saving!!")
     return
  if(len(data_3d.shape)!=3): #won't save 1D data
     print("Error!! data.shape appears to be {}. Needs to be 3D.".format(data.shape))
     return
  
  hdr_1024_str=gen_blank_hdr1024()
  
  header_inf=gen_header_inf_dic_from_data(data_3d,apix=apix)
    
  for k in HEADER_PACK_TABLE.keys():
    if(k in header_inf.keys()):
      s=HEADER_PACK_TABLE[k][0]
      e=HEADER_PACK_TABLE[k][1]
      t=HEADER_PACK_TABLE[k][2]
      v=header_inf[k]
      #print(s,e,t,v,k)
      hdr_1024_str=hdr_1024_str[ :s]+struct.pack(t,v)+hdr_1024_str[e:]
  return hdr_1024_str,header_inf


def modify_header1024_by_header_inf(hdr_1024_str,header_inf):
  modifiable=[ 'MRC_NXSTART'    ,
               'MRC_NYSTART'    ,
               'MRC_NZSTART'    ,
               'MRC_CELL_A'     ,
               'MRC_CELL_B'     ,
               'MRC_CELL_C'     ,
               'MRC_CELL_ALPHA' ,
               'MRC_CELL_BETA'  ,
               'MRC_CELL_GAMMA' ,
               'MRC_MAPC'       ,
               'MRC_MAPR'       ,
               'MRC_MAPS'       ,
               'MRC_DMIN'       ,
               'MRC_DMAX'       ,
               'MRC_DMEAN'      ,
               'MRC_ISPG'       ,
               'MRC_ORIX'       ,
               'MRC_ORIY'       ,
               'MRC_ORIZ'       ,
               'MRC_RMS'        ]
  print("=====Updating header block=====")
  for k in modifiable:
    if(k in header_inf.keys()):
      s=HEADER_PACK_TABLE[k][0]
      e=HEADER_PACK_TABLE[k][1]
      t=HEADER_PACK_TABLE[k][2]
      v=header_inf[k]
      print("{:20s}    {}   {}".format(k,t,v))
      n=struct.pack(t,v)
      hdr_1024_str=hdr_1024_str[ :s]+n+hdr_1024_str[e:]
  print("===============================")
  return   hdr_1024_str
  
############################################################labels and exthdr generation
def pad_to_1024(hdr_256_str):
  return hdr_256_str+chr(0)*(1024-len(hdr_256_str))

def add_label(hdr_1024_str,desc=''):
  '''add information as labels or extended header'''
  hdr_label=''
  hdr_1024_str,hdr_label=label_gen_str(hdr_1024_str,desc)
  hdr_1024_str[224:1024]=hdr_label[:800]
  return hdr_1024_str

def add_exthdr(hdrstr,ext_str=''):
  length=len(ext_str)
  extblc_len=0
  ext_hdr=''
  if(length>0):
    if(length%80>0):
      extblc_len=(int(length/80)+1)*80 #always use blocks of 80byes to be consistent with ccp4 map
    else:
      extblc_len=length
  hdrstr[92:96]=struct.pack("<i",extblc_len)
  ext_hdr=ext_str + chr(0) *(extblc_len-length)
  return  hdrstr,ext_hdr


def label_gen_str(hdrstr, label_str):
  length=len(label_str)
  if(length>800):
      hdrstr[220:224]=struct.pack('<i',800)
      return hdrstr,label_str[:800] #cut the begining into the label part
  blc=int(length/80)
  if(length%80>0):
    blc+=1
  hdrstr[220:224]=struct.pack('<i',blc)
  hdr_label=label_str + chr(0) *(800-length)
  return hdrstr,hdr_label








###############end of new header generation#############


def mrc_header1024(data,header_inf={}, desc='', exthdr='',hdr_apix=1.00,update_stats=False):

  if data.dtype not in NUMPY_MODE:
     Print("Error!! Invalid dtype for MRC. Not saving!!")
     return
  if(len(data.shape)<2): #won't save 1D data
     print("Error!! data.shape appears to be {}".format(data.shape))
     return
  
  hdr_1024_str,header_inf0 = mrc_header1024_from_data3d(data,apix=hdr_apix)
  
  if(len(header_inf.keys())==0):
    header_inf=header_inf0
  else:
    header_inf=update_header_inf(header_inf0,header_inf)
    
  if(update_stats):
    print ("\nupdating stats from data\n")
    update_stats_header_inf(data,header_inf)
  
  if(len(header_inf.keys())>0):
    hdr_1024_str = modify_header1024_by_header_inf(hdr_1024_str,header_inf)

  if(desc!=''):
    hdr_1024_str= add_label (hdr_1024_str,desc=desc)

  if(exthdr!=''):
    hdr_1024_str,exthdr= add_exthdr (hdr_1024_str,ext_hdr=exthdr)
  
    
  return hdr_1024_str,exthdr

    
def save_mrc(mrc_name,data,header_inf={}, desc='',hdr_max=None,hdr_min=None,hdr_mean=None,hdr_rms=None,hdr_apix=None,update_stats=False,ispg=None): #note: take 'C' array order, different from pyem
  '''
  requires np.ndarray arranged in [z][y][x] ('C' order)
  '''
  if (len(data.shape)!=3):
    print("data to be saved in MRC Need to be converted to 3D first\n")
    return
  #hdr_1024_str,exthdr=mrc_header1024(data,header_inf=header_inf, hdr_max=hdr_max,hdr_min=hdr_min,hdr_mean=hdr_mean,hdr_rms=hdr_rms,hdr_apix=hdr_apix,x=x,y=y,z=z,ud=ud,ispg=ispg)
  if hdr_max is not None:
    header_inf['MRC_DMAX']=hdr_max
  if hdr_min is not None:
    header_inf['MRC_DMIN']=hdr_min
  if hdr_mean is not None:
    header_inf['MRC_DMEAN']=hdr_mean
  if hdr_rms is not None:
    header_inf['MRC_RMS']=hdr_rms
  if ispg is not None:
    header_inf['MRC_ISPG']=ispg

  
  hdr_1024_str,exthdr=mrc_header1024(data,header_inf=header_inf,desc=desc,update_stats=update_stats,hdr_apix=hdr_apix)
  
  h_i=parse_MRC2014_header(hdr_1024_str,print_inf=True)
  #print(gen_info(h_i))
  with open(mrc_name, 'wb') as f:
      f.write(hdr_1024_str)
      f.write(exthdr)
      f.write(data.tobytes())
      f.close()
  
######################################################################
def calculate_apix(header_inf):
  [nx,ny,nz,   mapmode,      nxstart, nystart, nzstart,      mx, my, mz,   \
  cella, cellb, cellc, cellalpha,cellbeta,cellgamma,    \
  mapc,mapr,maps,      dmin,dmax,dmean,      ispg, nsymbt ,exttyp, nversion, orix,oriy,oriz,mapstr,machst_string,rms,nlbl,label] \
   =  [header_inf[k] for k in HEADER_ENTRIES_MINIMAL]
 
  apixX,apixY,apixZ=(0,0,0)
  if(mx!=0)  :
    apixX=cella/mx
  if(my!=0)  :
    apixY=cellb/my
  if(mz!=0)  :
    apixZ=cellc/mz
  return (apixX,apixY,apixZ)  

  
def gen_info(header_inf):
  (  nx             ,    \
     ny             ,    \
     nz             ,    \
     mapmode       ,     \
     nxstart       ,     \
     nystart       ,     \
     nzstart       ,     \
     mx            ,     \
     my            ,     \
     mz            ,     \
     cella             , \
     cellb             , \
     cellc             , \
     cellalpha         , \
     cellbeta          , \
     cellgamma         , \
     mapc          ,     \
     mapr          ,     \
     maps          ,     \
     dmin          ,     \
     dmax          ,     \
     dmean         ,     \
     ispg          ,     \
     nsymbt        ,     \
     exttyp        ,     \
     nversion      ,     \
     orix          ,     \
     oriy          ,     \
     oriz          ,     \
     map_str       ,     \
     machst_string ,     \
     rms          ,      \
     nlabl         ,     \
     label                 )=[header_inf[k] for k in HEADER_ENTRIES_MINIMAL]
  import re
  p = re.compile(b'\x00')
  labelshort=p.sub('', label)
  p = re.compile(b'\s+$')
  labelshort=p.sub('', labelshort)
  p = re.compile(b'^\s+')
  labelshort=p.sub('', labelshort)

  
  (apixX,apixY,apixZ)  =calculate_apix(header_inf)
  endianness='LE'
  machst_string=header_inf['MRC_MACHST_STRING']
  
  if (machst_string[:2] !='DD' and machst_string[:2] !='DA' ):
    endianness='BE'
    
  outlist= \
  'c, r, s(nx, ny, nz):     [{}\t{}\t{}]\n'.format(nx,ny,nz) +\
  'start x, y, z:           [{}\t{}\t{}]\n'.format(nxstart,nystart,nzstart)  +\
  'c,r,s => x,y,z:          [{}\t{}\t{}]\n'.format(mapc,mapr,maps) +\
  'mx, my, mz:              [{}\t{}\t{}]\n'.format(mx,my,mz) +\
  'origins x, y, z:         [{}\t{}\t{}]\n'.format(orix,oriy,oriz) +\
  'a, b, c:                 [{:.2f}\t{:.2f}\t{:.2f}]\n'.format(cella,cellb,cellc) +\
  'alpha, beta, gamma:      [{:.2f}\t{:.2f}\t{:.2f}]\n'.format(cellalpha,cellbeta,cellgamma) +\
  'dmin, dmax:              [{:.4f}\t{:.4f}]   \n'.format(dmin,dmax,dmean) + \
  'dmean, rms:              [{:.4f}\t{:.4f}]   \n'.format(dmean,rms) + \
  'ispg, nsymbt:            [{}\t{}]\n'.format(ispg,nsymbt) + \
  'map_str:                 [{}]\n'.format(map_str) +\
  'machst_string:           [{:}]\n'.format(machst_string) +\
  'nlabl                    [{}]\n'.format(nlabl) +\
  'label                    [{}]\n'.format(labelshort) +\
  'Mapmode:                 [{} => {}]\n'.format(str(mapmode),MODE_TABLE_HUMAN[mapmode]) +\
  'Apix:                    [X {} Y {} Z {}]\n'.format(apixX,apixY,apixZ) +\
  'Endianness:              [{}]\n'.format(endianness)
  return outlist

#####################read MRC#########################################
def parse_MRC2014_header(header_data,filesize=None,print_inf=True): #header_inf now only have 'MRC_XXXX' keys
  '''
  Interpreting MRC2014 file (.mrc) header. This one is specific for MRC2014.
  http://www.ccpem.ac.uk/mrc_format/mrc2014.php
  '''
  header_inf={'ori_1024':header_data[:1024]}
  OK=1
  for k in HEADER_ENTRIES_MINIMAL:
    s=HEADER_PACK_TABLE[k][0]
    e=HEADER_PACK_TABLE[k][1]
    t=HEADER_PACK_TABLE[k][2]
    header_inf[k], = struct.unpack(t,header_data[s:e])
    #print (k, header_inf[k])

  if header_inf['MRC_MAP_STR'][:3].decode() != "MAP": 
    #it really should be 'MAP ' but some programs such as motioncor2 uses \x00 instead of \x20 as the 4th character..
    print("Warning: the \"MAP(4D 41 50)\" keyword is not found at Bytes 208-210: [" + _map_str + "] \n")
    print(header_inf['MRC_MAP_STR'])
    OK =0
  if (header_inf['MRC_EXTTYP'].decode()=='CCP4'):
    print("Warning: the EXTTYPE indicats that the extended header is for a CCP4 map ")
    print (header_inf['MRC_EXTTYP'])
    OK =0
  
  [nx,ny,nz,   mapmode,      nxstart, nystart, nzstart,      mx, my, mz,   \
  cella, cellb, cellc, cellalpha,cellbeta,cellgamma,    \
  mapc,mapr,maps,      dmin,dmax,dmean,      ispg, nsymbt ,exttyp, nversion, orix,oriy,oriz,mapstr,machst_string,rms,nlbl,label] \
   =  [header_inf[k] for k in HEADER_ENTRIES_MINIMAL]

  _bytes_per_point = DSIZE_TABLE[mapmode]
  _expected_data_size = nx * ny * nz * _bytes_per_point
  _expected_file_size = _expected_data_size + 1024 + nsymbt #_nsymbt size of extended header (which follows main header) in bytes  7

  if (nsymbt % 80) != 0:
    print ( "Warning! The extended header (NSYMBT) <{} bytes> is not multiple of 80 Bytes.\n".format(nsymbt) )
  if (filesize is not None):
    if  (_expected_file_size != filesize):
      print ( "Error! The calculated file size is different from the actual size \n" )
      OK = 0
    if _expected_file_size == filesize and (nsymbt % 80) == 0:
      print ("File size check OK\n")


  endianness='LE'
  if(bytearray(machst_string)[0] & ord('\x11') ==  ord('\x11')): 
    endianness='BE'
  if (machst_string[:2] !='DD' and machst_string[:2] !='DA' ):
    print("Warning: the MACHST string check failed. This file may not be in little endian! (should be 0x44 0x44 0x00 0x00 \"DD\") or 0x44 0x41 0x00 0x00 \"DA\")")
    endianness='BE'
    OK =0

  
  
  _lskflg         = struct.unpack("<i",   header_data[96:100] )#ccp4 Xtal map only. lskflg:Flag for skew transformation, =0 none, =1 if foll
  _skwmat_string  =                       header_data[100:136] #ccp4 Xtal map only
  _skwtrn_string  =                       header_data[136:148] #ccp4 Xtal map only
  _futureuse_str  =\
  extra           =                       header_data[96:96+100]
  
  (apixX,apixY,apixZ)  =calculate_apix(header_inf)
  header_inf.update({    
    'endianness'        : endianness       ,
    'MRC_apixX'         : apixX,
    'MRC_apixY'         : apixY,
    'MRC_apixZ'         : apixZ, 
    'MRC_EXTRA'         : header_data[96:96+100] })
  if(print_inf)      :
      inflist=gen_info(header_inf)  
      print(inflist)


  if(OK==1):
    print ("All file check passed")
    
  else:
    print ("file check finished with warning")
  print ("+++++++++++++++++++++++++++++++++++++++++++++++++++++++")
  header_inf=make_alias_dic(header_inf)
  
  return      header_inf
  
  

##############################################################################


def flip_y(data_3d):
  z,y,x=data_3d.shape
  data_3d_flipped=np.ndarray((z,y,x),dtype=data_3d.dtype,order='C')
  for zz in range(z):
    for yy in range(y):
      data_3d_flipped[zz][yy]=data_3d[zz][y-1-yy]
      
  return data_3d_flipped

def flip_z(data_3d):
  z,y,x=data_3d.shape
  data_1d_flipped=np.ndarray((z,y,x),dtype=data_3d.dtype,order='C')
  for zz in range(z):
      data_1d_flipped[zz]=data_3d[z-1-zz]
      
  return data_1d_flipped
def remapping312(data_3d):
  s,r,c=data_3d.shape #size of z,y,x eg., 100,200,300
  data_3d_flipped=np.ndarray((c,s,r),dtype=data_3d.dtype,order='C')
  for xx in range(0,c): #old c-x, new c=z, length =
    for yy in range(0,r): #
      for zz in range(0,s): #
        data_3d_flipped[yy][xx][zz]=data_3d[zz][yy][xx]
  return data_3d_flipped
  
def shiftdata_center(data_3d):
  s,r,c=data_3d.shape #size of z,y,x eg., 100,200,300
  data_3d_shift=np.ndarray((s,r,c),dtype=data_3d.dtype,order='C')
  sf_s=s//2
  sf_c=c//2
  sf_r=r//2
  data_3d_shift=np.roll(data_3d,sf_c,axis=0)
  data_3d_shift=np.roll(data_3d_shift,sf_r,axis=1)
  data_3d_shift=np.roll(data_3d_shift,sf_s,axis=2)
  #data_3d_shift[:s-sf_s,:r-sf_r,:c-sf_c]=data_3d[sf_s:s,sf_r:r,sf_c:c]
  #data_3d_shift[sf_s:s,sf_r:r,sf_c:c]=data_3d[:s-sf_s,:r-sf_r,:c-sf_c]
  #data_3d_shift=data_3d[-sf_s:s-sf_s-1,-sf_r:r-sf_r-1,-sf_c:c-sf_c-1]
  #data_3d_shift[s-sf_s:,r-sf_r:,c-sf_c:]=data_3d[:-sf_s,:-sf_r,:-sf_c]
  
  print(data_3d.shape,data_3d_shift.shape)
  return data_3d_shift
def shiftdata(data_3d,sf_s,sf_r,sf_c):
  s,r,c=data_3d.shape #size of z,y,x eg., 100,200,300
  data_3d_shift=np.ndarray((s,r,c),dtype=data_3d.dtype,order='C')
  data_3d_shift=np.roll(data_3d,sf_c,axis=0)
  data_3d_shift=np.roll(data_3d_shift,sf_r,axis=1)
  data_3d_shift=np.roll(data_3d_shift,sf_s,axis=2)
  #data_3d_shift[:s-sf_s,:r-sf_r,:c-sf_c]=data_3d[sf_s:s,sf_r:r,sf_c:c]
  #data_3d_shift[sf_s:s,sf_r:r,sf_c:c]=data_3d[:s-sf_s,:r-sf_r,:c-sf_c]
  #data_3d_shift=data_3d[-sf_s:s-sf_s-1,-sf_r:r-sf_r-1,-sf_c:c-sf_c-1]
  #data_3d_shift[s-sf_s:,r-sf_r:,c-sf_c:]=data_3d[:-sf_s,:-sf_r,:-sf_c]
  
  print(data_3d.shape,data_3d_shift.shape)
  return data_3d_shift
  
def analyze_EPU_exthdr(exthdr):

  if (len(exthdr)< 0x300): #should be 0xc0000=786432
    return ''

  infstr=''
  size= struct.unpack("<i",exthdr[:4])
  if (size < 0x300): #should be 0xc0000=786432
    return ''

  Application    = exthdr[52:52+16]
  
  
  if(Application[:3].lower() != 'FEI'.lower()):
    print(Application[:3])
    return ''


  (HT,dose)=  struct.unpack('<dd',exthdr[84:84+16])
  HT/=1000 #to kV
  dose /= 10**20 #e/m2 to e/A2
  
  Microscope_type=exthdr[20:36]
  (Alpha,beta,x,y,z)=struct.unpack('<ddddd',exthdr[100:100+8*5])
  [xum,yum,zum]=[a * 1e6 for a in (x,y,z)] #to um
  
  (ApixX,ApixY)=(struct.unpack('<dd',exthdr[156:156+8*2]) )
  ApixX*=1e10
  ApixY*=1e10
  
  (defocus,stem_defocus,applied_defocus)=struct.unpack('<ddd',exthdr[220:220+8*3]) 
  defocus  *=1e6
  stem_defocus  *=1e6
  applied_defocus  *=1e6
    
  Probe='uP'
  if(1==struct.unpack('<i',exthdr[284:284+4])):
    Probe='nP'
  
  Magnification,=struct.unpack('<d',exthdr[289:289+8])
  Magnification/=1000 #kx
  
  Spot,=struct.unpack('<i',exthdr[309:309+4])
  Intensity,Convergence=struct.unpack('<dd',exthdr[321:321+16])
  Illumination_mode=exthdr[337:337+16]
  #EFTEM
  Slit_width,=struct.unpack('<d',exthdr[355:355+8])
  (IsX,IsY,BsX,BsY,Integration_time)=struct.unpack('<ddddd',exthdr[387:387+8*5])
  Ceta_noise_reduction,=struct.unpack('?',exthdr[467]) #boolean
  Ceta_frames_summed,=struct.unpack('<i',exthdr[468:468+4]) #boolean
  (DDD_counting,DDD_align)=struct.unpack('??',exthdr[472:474])
  print (Application,Microscope_type)
  print ("HT: {} dose: {} e/A2".format(HT,dose))
  print ("ApixX: {} ApixY: {}".format(ApixX,ApixY))
  print ("Defocus: {} um  Applied defocus: {} um".format(defocus,applied_defocus))
  print ("Spot index {}".format(Spot))
  print ('Intensity,Convergence,Illumination_mode: {} {} {}'.format(  Intensity,Convergence,Illumination_mode))
  print ('IsX,IsY,BsX,BsY,Integration_time {} {} {} {} {}'.format(IsX,IsY,BsX,BsY,Integration_time))
  print ('Ceta_noise_reduction,Ceta_frames_summed: {} {}'.format(Ceta_noise_reduction,Ceta_frames_summed))
  print ('DDD_counting,DDD_align: {} {}'.format(DDD_counting,DDD_align))
  print()
  
  infstr='_{:3.0f}kV_{:3.1f}kx_{:3.1f}um-{:3.1f}um_{}{}_{:4.2f}'.format(HT,Magnification,defocus,applied_defocus,Probe,Spot,Intensity)
  infstr='_{:3.1f}um-{:3.1f}um_{}{}_{:4.2f}'.format(defocus,applied_defocus,Probe,Spot,Intensity)
  
  print (infstr)
  
  return infstr
  
  
def proc(filename,args,gain_1d):
    
    
    (root,ext,mrcname,file_dir)=common.find_dir(filename)
    file_size=os.path.getsize(filename)
    #print ((root,ext,mrcname,file_dir),sep='\n')
    if(args.Apix == None):
      args.Apix=1.00
    if(args.tif2mrc ): #keep filename, convert to mrc and reture
      if( ext == '.tif' or
          ext == '.tiff' or
          ext == '.TIF' or
          ext == '.TIFF' ):
        print('converting {} to mrc format'.format(filename))
        print('Supplied Apix = {}, if not correct, use --Apix'.format(args.Apix))
        tiff_to_mrc(filename,args)
      else:
        print("The input file does not have .tif/.tiff as extension. Not processing.")
      return


        

    header_inf,exthdr,data_1d=read_MRC2014(filename)
    
    x,y,z=header_inf['c'],header_inf['r'],header_inf['s']
    
    writenew=False
    mrc_name=root
    if(args.gain is not None):
      data_1d=np.multiply(data_1d,gain_1d,dtype=np.float32)
      #data_1d=np.divide(data_1d,gain_1d,dtype=np.float32)
      mrc_name+='.gain'
      writenew=True
    data_3d=data_1d.reshape(z,y,x)

    
    if(len(exthdr)>0):
      print("Extended header found: {} Bytes, using {} Bytes".format(len(exthdr),header_inf['nsymbt']))
    header=header_inf['ori_1024']

#process and save new map 
    if(args.histogram):
      amax= data_3d.max()
      amin= data_3d.min()
      print(amax,amin)
      
      (his_count,his_bins)=np.histogram(data_3d, bins=amax-amin,range=(amin,amax))
      
      print(len(his_count),len(his_bins))
      hs=np.array([his_bins[:-1],his_count])
        
      print (hs.shape)
      hs=hs.astype(int)
      with open(mrc_name+'.csv', 'w') as csv_f:
        np.savetxt(csv_f, hs.transpose(), fmt='%s', delimiter=',', newline='\n' )
      
    
    if(args.EPU or len(exthdr)>0):
      infstr=''
      if(len(exthdr)>0):
        infstr=analyze_EPU_exthdr(exthdr)
      else:
        print("No extended header found")
      mrc_name+=infstr

    if(args.removeExthdr ):
      if(len(exthdr)==0):
        print("No extended header found")
      else:  
        with open(mrc_name+'_extheader.txt', 'wb') as f:
          f.write(exthdr)
          f.close()
        exthdr=''
        writenew=True
        newheader=header[:92]+struct.pack('<i',0)+header[96:]
        header=newheader
        mrc_name+='.noExt'
      
    if(args.sigmaclip is not None):
        if(header_inf['arms']<=0):
          header_inf['arms']=data_3d.std()
        clipmin=header_inf['amean']-header_inf['arms']*args.sigmaclip
        clipmax=header_inf['amean']+header_inf['arms']*args.sigmaclip
        tmptype=data_3d.dtype
        
        data_clip=np.clip(data_3d, clipmin,clipmax)
        mrc_name+='.sigmaclip{}'.format(args.sigmaclip)
        data_3d=data_clip.astype(tmptype, order='K', casting='unsafe', subok=True, copy=True)
        
        newmin=data_3d.min()
        newmax=data_3d.max()
        newmean=data_3d.mean()
        newrms= data_3d.std()
        newheader=header[:76]+\
                struct.pack('<fff',newmin,newmax,newmean) +\
                header[88:216] +\
                struct.pack('<f',newrms) +\
                header[220:1024]
        header=newheader
        
        writenew=True

    if(args.sigma_denoise is not None):
        if(header_inf['arms']<=0):
          header_inf['arms']=data_3d.std()

        clipmin=header_inf['amean']+header_inf['arms']*args.sigma_denoise
        clipmax=header_inf['amean']-header_inf['arms']*args.sigma_denoise
        tmptype=data_3d.dtype
        
        data_clip=np.clip(data_3d, clipmin,header_inf['amax']+1)
        #data_clip2=np.clip(data_3d, header_inf['amin']-1,clipmax)
        #data_clip=data_clip1+data_clip2
        
        mrc_name+='.denoise'

        data_3d=data_clip.astype(tmptype, order='K', casting='unsafe', subok=True, copy=True)
        
        newmin=data_3d.min()
        newmax=data_3d.max()
        newmean=data_3d.mean()
        newrms= data_3d.std()
        newheader=header[:76]+\
                struct.pack('<fff',newmin,newmax,newmean) +\
                header[88:216] +\
                struct.pack('<f',newrms) +\
                header[220:1024]
        header=newheader
        
        writenew=True
        
    if(args.cropMAP is not None):
      
      mrc_name+='.cropped'
      (x1,x2,y1,y2,z1,z2)      =args.cropMAP
      print ("cropiing map: X {}-{} Y {}-{} Z {}-{}".format(x1,x2,y1,y2,z1,z2))
      data_crop=data_3d
      if(0<=x1<x2<header_inf['c']):
        data_crop=data_crop[:,:,x1:x2+1]
        print (data_crop.shape)
      if(0<=y1<y2<header_inf['r']):
        data_crop=data_crop[:,y1:y2+1,:]
        print (data_crop.shape)
      if(0<=z1<z2<header_inf['s']):
        data_crop=data_crop[z1:z2+1]
        print (data_crop.shape)
      data_3d=data_crop
      print (data_3d.shape)
      hdr_256=mrc_header256(data_3d, apix=header_inf['MRC_apixX'],ud=True,ispg=header_inf['ispg'])
      
      header=ndary_tobytes(hdr_256)+header[256:1024]
      
        
      writenew=True


    if(args.clipneg):
        clipmin=0
        tmptype=data_3d.dtype
        
        data_clip=np.clip(data_3d, 0,None)
        mrc_name+='.clipneg'
        data_3d=data_clip.astype(tmptype, order='K', casting='unsafe', subok=True, copy=True)
        
        newmin=data_3d.min()
        newmax=data_3d.max()
        newmean=data_3d.mean()
        newrms= data_3d.std()
        newheader=header[:76]+\
                struct.pack('<fff',newmin,newmax,newmean) +\
                header[88:216] +\
                struct.pack('<f',newrms) +\
                header[220:1024]
        header=newheader
        
        writenew=True

        
    if(args.flipY):
      data_3d=flip_y(data_3d)
      mrc_name+='.Yflip'
      writenew=True
    if(args.flipZ):
      data_3d=flip_z(data_3d)
      mrc_name+='.Zflip'
      writenew=True
    if(args.remap312 or args.hardcenter):
      writenew=True
      data_3d=remapping312(data_3d)
      newheader=header[:64]+\
                struct.pack('<iii',3,1,2) +\
                header[76:88]+\
                struct.pack('<i',1)+\
                header[92:1024]
      mrc_name+='.ccp4_P1'
      header=newheader
      
    if(args.ori_center):
      writenew=True
      mrc_name+='.ori_center'
      header_inf['nxstart']=-header_inf['c']/2
      header_inf['nystart']=-header_inf['r']/2
      header_inf['nzstart']=-header_inf['s']/2

      newheader=header[:16]+\
                struct.pack('<iii',header_inf['nxstart'],header_inf['nystart'],header_inf['nzstart']) +\
                header[28:1024]
      header=newheader

    if(args.shift is not None):
      writenew=True
      (sf_s,sf_r,sf_c)=args.shift
      
      data_3d=shiftdata(data_3d,sf_s,sf_r,sf_c)
        
      mrc_name+='.shift_x{}y{}z{}'.format(sf_s,sf_r,sf_c)


    if(args.hardcenter): 
      #remap321 will be done(above) to change to P1 and follow CCP4 convention 312 mapping, then shift the datablocks. changes to header are all done in the remapping
      #Z is still the primary symmetry axis, but it is on column now.
      writenew=True
      mrc_name+='.hard_center' #indicate it is faking a crystal
      data_3d=shiftdata_center(data_3d)
  

    mrc_name+='.mrc'
    if(writenew==True):
      simple_write_mrc(mrc_name,header,exthdr,data_3d)
    
      
def linear_interpolarte(data3d,factor): #expande map with a integer factor
    from scipy import interpolate
    z,y,x=data_3d.shape
    data_3d_exp=np.ndarray((z*factor,y*factor,x*factor),dtype=data_3d.dtype,order='C')
    #edge
    #face
    #body
      
    return data_3d_exp
    
def sumall(args):
  sumdata=np.zeros((4096*4096),dtype=np.float32)
  c=0  
  for filename in args.mrc_files:
    c+=1
    header_inf,exthdr,data_1d=read_MRC2014(filename)
    sumdata+=data_1d
  avedata=sumdata/c
  sd=sumdata.reshape((4096,4096))
  ad=avedata.reshape((4096,4096))
  save_mrc('ave.mrc',ad,update_stats=True)
  save_mrc('sum.mrc',sd,update_stats=True)
######################################################################  
def read_FEI_gain(filename):
    file_size=os.path.getsize(filename)
    if 4096*4096*4+49!=file_size:
      print ("Error, not 1 sampling gain reference for (4096x4096): {}".format(file_size))
      exit()
    try:
        f=open(filename,'rb')
        f.seek(49)
        gain_1d=np.fromfile(f,dtype=np.float32,count=4096*4096)
    finally:
      f.close()
    return gain_1d

def read_MRC2014(filename):
    header_inf={}
    exthdr=''
    data_1d=np.ndarray(0)
    print("\nReading MRC file <{}>\n".format (filename))
    try:
        f=open(filename,'rb')
        f.seek(0)
        header = f.read(1024)
        header_inf=parse_MRC2014_header(header,filesize=os.path.getsize(filename),print_inf=True)
        #print(gen_info(header_inf))
        if header_inf['MRC_NSYMBT']>0:
          exthdr = f.read(header_inf['MRC_NSYMBT'])                       
        x,y,z=header_inf['MRC_NX'],header_inf['MRC_NY'],header_inf['MRC_NZ']            
        data_1d=np.fromfile(f,dtype=NUMPY_MODE[header_inf['MRC_MAPMODE']],count=x*y*z)               
    finally:                 
      f.close()
    return header_inf,exthdr,data_1d
#######################################################################  
  
class mrc_file():
  def __init__(self):
    self.header_inf={}
    self.exthdr=''
    self.data_3d=np.zeros(1)
    self.file_info={}
    
    self.mapmode=2
    self.crs=[0,0,0]
    
    
  def info(self):
    inflist=gen_info(self.header_inf)  
    print(inflist)
    return inflist

  def update_header_block1024(self):
    hdr_1024_str, ext_hdr = mrc_header1024(self.data_3d, header_inf=self.header_inf)
    
    self.header_inf['hdr_1024']=hdr_1024_str
    if(len(self.header_inf['hdr_1024'])!=1024):
      print( "Header length ERROR!!!!")
    
    
  def update_header_key_value(self,k,v):
    self.header_inf[k]=v
    self.update_header_block1024()
    pass

  def update_stats(self):
    update_stats_header_inf(self.data_3d,self.header_inf)
    
  def read(self,filename):
    (root,ext,mrcname,file_dir)=common.find_dir(filename)
    self.file_info={'root':root,'ext':ext,'mrcname':mrcname,'file_dir':file_dir, 'file_size':os.path.getsize(filename)}
    
    self.header_inf,self.exthdr,self.data_1d=read_MRC2014(filename)
    
    self.crs[:3]=self.header_inf['c'],self.header_inf['r'],self.header_inf['s']#c,r,s ->x,y,z (1,2,3 in fact. In crystallography remapping is needed)
    self.data_3d=self.data_1d.reshape(self.crs[::-1])
    self.mapmode=self.header_inf['MRC_MAPMODE']
    self.apix=self.header_inf['MRC_apixX']
    
    self.header_inf['hdr_1024']=self.header_inf['ori_1024']
    
    self.info()    
    
  def write(self,filename,data_3d,header_inf):
    
    
    
    pass
  def auto_write(self,filename):
    
    
    pass

  
def main():
    print('MRC lib and tools       <zhijie.li@utoronto.ca>')

    parser = argparse.ArgumentParser(description='MRC file reading and manipulation')


    parser.add_argument("mrc_files",metavar='.mrc files',nargs='+',type=str, help="The .mrc files to process.")
    parser.add_argument("--gain", help="Gain reference (FEI raw format)", type=str, metavar="N")


    
    parser.add_argument("-flipY",action='store_true',default=False, help="flip map in Y direction (causing handedness to change)")
    parser.add_argument("-flipZ",action='store_true',default=False, help="flip map in Z direction (causing handedness to change)")
    parser.add_argument("-remap312",action='store_true',default=False, help="change the c r s mapping from c-x r-y s-z(123) to c-z r-x s-y(312) resulting map should look same in chimera but data order is changed. Header will also have P1 in SG")
    parser.add_argument("-ori_center",action='store_true',default=False, help="shift the center of the map to (0,0,0) - by changing the map's origin (words 5-7) in header.")
    parser.add_argument("-hardcenter",action='store_true',default=False, help="shift the center of the map to (0,0,0) - by moving the data block and changing Space Group to CCP4-P1")
    parser.add_argument("-sumall",action='store_true',default=False, help="sumall mrc files")

    parser.add_argument("-mrc",action='store_true',default=False, help="save MRC file")
    parser.add_argument("-tif2mrc",action='store_true',default=False, help="convert tif to MRC, need --Apix to set Apix, otherwise it will be 1.00.")
    parser.add_argument("--Apix", help="Apix",nargs='?', default=1.00, type=float, metavar="N")
    parser.add_argument("-tif8",action='store_true',default=False, help="save a scaled 8bit TIFF file for visualization. ") #this one is not really used in this program
    parser.add_argument("-tif",action='store_true',default=False, help="save data to TIFF file. ") #this one is not really used in this program
    parser.add_argument("-invtif8",action='store_true',default=False, help="invert contrast in the resulting 8bit TIFF file. ") #this one is not really used in this program
    parser.add_argument("-invmrc",action='store_true',default=False, help="invert contrast in the resulting MRC file. Same as the --multi=-1 option in exproc2d.py. TIFF files are not affected.")
    parser.add_argument("--bin", help="Binning factor for uint8.tif, needs to be positive integer", type=int,default=2, metavar="N")
    parser.add_argument("--sigma", help="rescale tiff8 image by sigma",                        type=float, metavar="N")

    parser.add_argument("-clipneg",action='store_true',default=False, help="remove negative values from data (so that GCTF won't have trouble)")
    parser.add_argument("--sigmaclip", help="clip original data by sigma value", type=float, metavar="N")
    parser.add_argument("--sigma_denoise", help="denoise original data by sigma value", type=float, metavar="N")
    parser.add_argument("--cropMAP", help="crop the map by X1,X2,Y2,Y2,Z1,Z2, negative number indicates no-cropping", nargs=6,type=int, metavar="N")

    parser.add_argument("-removeExthdr",action='store_true',default=False, help="remove extended header (for compatibility)")
    parser.add_argument("-EPU",action='store_true',default=False, help="analyze EPU extended header and add information to filaname")
    parser.add_argument("-histogram",action='store_true',default=False, help="generate histogram data from mrc file")
    parser.add_argument("--shift", help="Shift map matrix by x y z (all int)",nargs=3, type=int, metavar="(X, Y, Z)")
    
  #  parser.add_argument("--bin", help="Binning factor, needs to be positive integer",                        type=int, metavar="N")
    #parser.add_argument("--sigma", help="Rescaling, how many sigmas",                        type=float, metavar="N")

    args=parser.parse_args()                           


    gain_1d=np.ones(4096*4096,dtype=np.float32)
    if args.sumall:
      
      sumall(args)
        
    
    else:
      gain_1d_Yflip=np.ones((4096,4096))
      if(args.gain is not None):
        gain_1d=read_FEI_gain(args.gain)
        gain_2d=gain_1d.reshape((4096,4096))
        gain_3d=gain_1d.reshape((1,4096,4096))
        gain_3d_Yflip=flip_y(gain_3d)
        gain_1d_Yflip=gain_3d_Yflip.reshape(4096*4096)
        from EM_tiff import save_tiff8
        fileroot=args.gain
        gmax=gain_1d.max()
        gmin=gain_1d.min()
        gmean=gain_1d.mean()
        grms=gain_1d.std()
        print(gmax,gmin,gmean,grms)
        save_tiff8(gain_3d_Yflip[0],'',fileroot+'.tif',gmax,gmin,4096,4096)

      for filename in args.mrc_files:
        proc(filename,args,gain_1d_Yflip)

if __name__ == '__main__':
  main()
  
  