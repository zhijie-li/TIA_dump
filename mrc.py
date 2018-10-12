#
#The MRC writing functions are modified from pyEM (https://github.com/asarnow/pyem) under GPL. 
#
#The modifications allow using the 10x80Byte blocks in the header for saving notes, and using arbitrary amount of 80B blocks after the 1024Bytes for longer notes. 
#These still comply with MRC2014 format. 
#But simplistic MRC readers that do not consider possibility of extended header may have troubles.
#SO try not use a extended header! (800B can save a lot of notes already)
#
#
#===GPL regarding modified source===
#
# 5. Conveying Modified Source Versions.
#
#  You may convey a work based on the Program, or the modifications to
#produce it from the Program, in the form of source code under the
#terms of section 4, provided that you also meet all of these conditions:
#
#    a) The work must carry prominent notices stating that you modified
#    it, and giving a relevant date.
#
#    b) The work must carry prominent notices stating that it is
#    released under this License and any conditions added under section
#    7.  This requirement modifies the requirement in section 4 to
#    "keep intact all notices".
#
#    c) You must license the entire work, as a whole, under this
#    License to anyone who comes into possession of a copy.  This
#    License will therefore apply, along with any applicable section 7
#    additional terms, to the whole of the work, and all its parts,
#    regardless of how they are packaged.  This License gives no
#    permission to license the work in any other way, but it does not
#    invalidate such permission if you have separately received it.
#
#    d) If the work has interactive user interfaces, each must display
#    Appropriate Legal Notices; however, if the Program has interactive
#    interfaces that do not display Appropriate Legal Notices, your
#    work need not make them do so.
#
#  A compilation of a covered work with other separate and independent
#works, which are not by their nature extensions of the covered work,
#and which are not combined with it such as to form a larger program,
#in or on a volume of a storage or distribution medium, is called an
#"aggregate" if the compilation and its resulting copyright are not
#used to limit the access or legal rights of the compilation's users
#beyond what the individual works permit.  Inclusion of a covered work
#in an aggregate does not cause this License to apply to the other
#parts of the aggregate.
#
import numpy as np
import os
import struct
import io

MODE = {
        0: np.dtype(np.int8), 
        1: np.dtype(np.int16), 
        2: np.dtype(np.float32), 
        6: np.dtype(np.uint16),
        np.dtype(np.int8):    0,
        np.dtype(np.int16):   1, 
        np.dtype(np.float32): 2, 
        np.dtype(np.uint16):  6
       }

HEADER_LEN = int(256)  # Bytes.


def mrc_header(shape, dtype=np.float32, psz=1.0):
    header = np.zeros(HEADER_LEN / 4, dtype=np.int32)
    header_f = header.view(np.float32)
    header[:3] = shape
    if np.dtype(dtype) not in MODE:
        raise ValueError("Invalid dtype for MRC")
    header[3] = MODE[np.dtype(dtype)]
    header[7:10] = header[:3]  # mx, my, mz (grid size)
    header_f[10:13] = psz * header[:3]  # xlen, ylen, zlen
    header_f[13:16] = 90.0  # CELLB
    header[16:19] = 1, 2, 3  # Axis order.
    header_f[19:22] = 1, 0, -1  # Convention for unreliable  values.
    header[26] = ord('M')+ord('R')*256+ord('C')*256*256+ord('O')*256*256*256
    header[27] = 20140  # Version 2014-0.
    header_f[49:52] = 0, 0, 0  # Default origin.
    header[52] = ord('M')+ord('A')*256+ord('P')*256*256+ord(' ')*256*256*256
    header[53] = 17476  # 0x00004444 for little-endian.
    header_f[54] = -1  # Convention for unreliable RMS value.
    return header

def mrc_header_gen(data, psz=1.0, origin=None, amin=None, amax=None, amean=None,arms=None):
    
    r,c=data.shape[:1]
    s=1
    if(data.shape[2]): s=data.shape[2] #in case data is only 2D


    if np.dtype(dtype) not in MODE:
        raise ValueError("Invalid dtype for MRC")

    map_mode = MODE[data.dtype]
    


    
    
def mrc_header_complete(data, psz=1.0, origin=None, amin=None, amax=None, amean=None,arms=None):
    header = mrc_header(data.shape, data.dtype, psz=psz)
    header_f = header.view(np.float32)
    if(amin==None): amin=data.min()
    if(amax==None): amax=data.max()
    if(amean==None): amean=data.mean()      
    if(arms==None): amrms=data.std()      
      
    header_f[19:22] = [amin,amax,amean]
    header_f[54]=arms 
    #stdev is very close to rmsd for a image. Being single precision float they are indistinguishable
    #data_dev=data-amean
    #rmsd=np.sqrt(data_dev.dot(data_dev)/xsize/ysize) #datasize is large enough to use stdev instead
    if origin is None:
        header_f[49:52] = (0, 0, 0)
    elif origin is "center":
        header_f[49:52] = psz * header[:3] / 2
    else:
        header_f[49:52] = origin
    return header

def label_gen(header, label_str):
  length=len(label_str)
  if(length>(1024-256)):
      header[55]=1024-256
      return label_str[:(1024-256)]
  blc=int(length/80)
  if(length%80>0): 
    blc+=1
  header[55]=blc  
  hdr_label=label_str + chr(0) *(1024-256-length)
  return hdr_label
  
def ext_hdr(header,ext_str):
  length=len(ext_str)
  extblc_len=0
  ext_hdr=''
  header[23]=0
  if(length>0):
    if(length%80>0):
      header[23]=extblc_len=(int(length/80)+1)*80 #always use blocks of 80byes to be consistent with ccp4 map
    else:
      header[23]=extblc_len=length
      
    ext_hdr=ext_str + chr(0) *(extblc_len-length)    
  return ext_hdr


def ndary_tobytes(ndary):
  '''
  equivalent to ndarry.tobytes
  this is for older version of numpy
  '''
  fmtstr={
    np.dtype(np.int8):     'b'       ,   #signed 1-byte integer	
    np.dtype(np.int16):    'h'       ,   #Signed 2-byte integer	 
    np.dtype(np.int32):    'i'       ,   #Signed 4-byte integer	 
    np.dtype(np.float32):  'f'       ,   #4-byte float	 
    np.dtype(np.uint16):   'd'       ,   #8-byte float	
  }
  

  #fmt=fmtstr[ndary.dtype]
  #onedary=ndary.reshape(ndary.size)
  #a=onedary.tolist()
  #bstring= struct.pack(fmt * len(a),*a)  
  #===========method2========
  #based on https://stackoverflow.com/questions/43925624/fastest-method-to-dump-numpy-array-into-string
  tmp = io.BytesIO()
  np.save(tmp, ndary)
  #ndary.tofile(tmp)
  
  bstring=tmp.getvalue()
  #the npy header length is saved in bytes 9 and 10 in the header, total headerlength = 6(0x93NUMPY)+2(vv)+2(LL)+header_length
  start=10+ord(bstring[9])*256+ord(bstring[8]) #normally 80
  #print( start)
  return bstring[start:]  

def save_mrc(mrc_name,data, desc='',hdr_max=-1,hdr_min=0,hdr_mean=-1,hdr_rms=-1,hdr_apix=1.0,):
  '''
  requires np.ndarray arranged in [z][y][x] ('C' order)
  '''
  if data.dtype not in MODE:
      raise ValueError("Invalid dtype for MRC")
  hdr_max=data[0,:,:].max()            #only use first frame for stats
  hdr_min=data[0,:,:].min()
  hdr_mean=data[0,:,:].mean()
  hdr_rms=data[0,:,:].std()
  hdr_256=mrc_header_complete(data, amax=hdr_max,amin=hdr_min,amean=hdr_mean,arms=hdr_rms,psz=hdr_apix) #first 256 bytes
  ext_header=''
  hdr_label=''
  if(len(desc)<(1024-256)):
    hdr_label=label_gen(hdr_256,desc)
  else:
    hdr_label=label_gen(hdr_256,'')
    ext_header=ext_hdr(hdr_256,desc)

  with open(mrc_name, 'wb') as f:
    if(hasattr(np.ndarray,'tobytes')): #better, but only exists in newer numpy
      #print("using ndarry.tobytes()")
      f.write(hdr_256.tobytes())
      f.write(hdr_label)
      f.write(ext_header)
      f.write(data.tobytes())
    else:
      #print("ndarry.tobytes() not availble, using alternative")
      f.write(ndary_tobytes(hdr_256))
      f.write(hdr_label)
      f.write(ext_header)
      f.write(ndary_tobytes(data))
      




# HEADER FORMAT
# 0      (0,4)      NX  number of columns (fastest changing in map)
# 1      (4,8)      NY  number of rows
# 2      (8,12)     NZ  number of sections (slowest changing in map)
# 3      (12,16)    MODE  data type:
#                       0   image: signed 8-bit bytes range -128 to 127
#                       1   image: 16-bit halfwords
#                       2   image: 32-bit reals
#                       3   transform: complex 16-bit integers
#                       4   transform: complex 32-bit reals
# 4      (16,20)    NXSTART number of first column in map
# 5      (20,24)    NYSTART number of first row in map
# 6      (24,28)    NZSTART number of first section in map
# 7      (28,32)    MX      number of intervals along X
# 8      (32,36)    MY      number of intervals along Y
# 9      (36,40)    MZ      number of intervals along Z
# 10-13  (40,52)    CELLA   cell dimensions in angstroms
# 13-16  (52,64)    CELLB   cell angles in degrees
# 16     (64,68)    MAPC    axis corresp to cols (1,2,3 for X,Y,Z)
# 17     (68,72)    MAPR    axis corresp to rows (1,2,3 for X,Y,Z)
# 18     (72,76)    MAPS    axis corresp to sections (1,2,3 for X,Y,Z)
# 19     (76,80)    DMIN    minimum density value
# 20     (80,84)    DMAX    maximum density value
# 21     (84,88)    DMEAN   mean density value
# 22     (88,92)    ISPG    space group number, 0 for images or 1 for volumes
# 23     (92,96)    NSYMBT  number of bytes in extended header
# 24-49  (96,196)   EXTRA   extra space used for anything
#           26  (104)   EXTTYP      extended header type("MRCO" for MRC)
#           27  (108)   NVERSION    MRC format version (20140)
# 49-52  (196,208)  ORIGIN  origin in X,Y,Z used for transforms
# 52     (208,212)  MAP     character string 'MAP ' to identify file type
# 53     (212,216)  MACHST  machine stamp
# 54     (216,220)  RMS     rms deviation of map from mean density
# 55     (220,224)  NLABL   number of labels being used
# 56-256 (224,1024) LABEL(80,10)    10 80-character text labels
