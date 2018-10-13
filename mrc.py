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

HEADER_LEN = int(256)  # Bytes.


def mrc_header(shape, dtype=np.float32, psz=1.0):
    header = np.zeros(HEADER_LEN / 4, dtype=np.int32)
    header_f = header.view(np.float32)
    header[:3] = shape
    if np.dtype(dtype) not in NUMPY_MODE:
        raise ValueError("Invalid dtype for MRC")
    header[3] = NUMPY_MODE[np.dtype(dtype)]
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


    if np.dtype(dtype) not in NUMPY_MODE:
        raise ValueError("Invalid dtype for MRC")

    map_mode = NUMPY_MODE[data.dtype]





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
  if data.dtype not in NUMPY_MODE:
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





def parse_MRC2014_header(header_data,filesize):
  '''
  Interpreting MRC2014 file (.mrc) header. This one is specific for MRC2014.
  http://www.ccpem.ac.uk/mrc_format/mrc2014.php
  '''
  nx,ny,nz, \
  mapmode,    \
  nxstart, nystart, nzstart,    \
  mx, my, mz,   \
  cella, cellb, cellc, cellalpha,cellbeta,cellgamma,    \
  mapc,mapr,maps,    \
  dmin,dmax,dmean,    \
  ispg, nsymbt \
  = struct.unpack("<iiiiiiiiiiffffffiiifffii", header_data[:96])

  _lskflg         = struct.unpack("<i",   header_data[96:100] )#ccp4 Xtal map only. lskflg:Flag for skew transformation, =0 none, =1 if foll
  _skwmat_string  =                       header_data[100:136] #ccp4 Xtal map only
  _skwtrn_string  =                       header_data[136:148] #ccp4 Xtal map only
  _futureuse_str  =\
  extra           =                       header_data[96:96+100]
  exttyp          =                       header_data[104:104+4]
  nversion        =                       header_data[108:108+4]
  orix,oriy,oriz, = struct.unpack("<fff", header_data[196:196+12]) # this is defined only in MRC 2014, not in ccp4 maps
  map_str         =                       header_data[208:208+4]   #'MAP '
  machst_string   =                       header_data[212:212+4]
  machst,         = struct.unpack("<i",   header_data[212:212+4] ) #"in practice it is safe to use 0x44 0x44 0x00 0x00 for little endian machines",  68*256+68=17476, or 'DD' as string. Sometimes (serialEM) it can be 0x44 0x41:'DA',16708 
  rms,            = struct.unpack( "f" ,  header_data[216:216+4])
  nlabl,          = struct.unpack( "i" ,  header_data[220:220+4])  #need to use i, 'l' will cause problem on some 64bit system(linux 64)
  label           =                       header_data[224:224+800]



  OK = 1
  #some checks
  #1 "MAP "
  if   map_str[:3].decode() != "MAP": #the .decode() part: because _map_str is byte literal... b'MAP'
    #it really should be 'MAP ' but some programs such as motioncor2 uses \x00 instead of \x20 as the 4th character..
    print("Warning: the \"MAP(4D 41 50)\" keyword is not found at Bytes 208-210: [" + _map_str + "] \n")
    print (map_str)
    OK =0
  if (exttyp.decode()=='CCP4'):
    print("Warning: the EXTTYPE indicats that the extended header is for a CCP4 map ")
    print (exttype)
    OK =0
#    sys.exit()
  #2 size
  #size of map is determined by column * row * sections * bytes/point.
  #bytes/point:
  #13-16  MODE  0 8-bit signed integer (range -128 to 127)
  #1 16-bit signed integer
  #2 32-bit signed real
  #3 transform : complex 16-bit integers
  #4 transform : complex 32-bit reals
  #6 16-bit unsigned integer  2

  _bytes_per_point = DSIZE_TABLE[mapmode]
  _expected_data_size = nx * ny * nz * _bytes_per_point
  _expected_file_size = _expected_data_size + 1024 + nsymbt #_nsymbt size of extended header (which follows main header) in bytes  7

  #s= "\nfile size: " + str(filesize)  + " data block size: " + str(_expected_data_size) + "\nheader + SYMM: "+ str(1024+_nsymbt) + "\n"  + "headersize: 1024  SYMM blocks (80 Bytes each): " + str(_nsymbt) +" Bytes"
  #print(s)

  if (nsymbt % 80) != 0:
    print ( "Warning! The total size of symbol blocks is not multiples of 80 Bytes \n" )
    OK = 0
  if _expected_file_size != filesize:
    print ( "Error! The calculated file size is different from the actual size \n" )
    OK = 0
    exit()
  if _expected_file_size == filesize and (nsymbt % 80) == 0:
    print ("File size check OK")


  #3 Spacegroup
  #if _ispg <= 0 or _ispg >=400:
  #  print ( "This file does not contain a crystallographic space group\n")
  #4 endianess
  #Note 11 Bytes 213 and 214 contain 4 `nibbles' (half-bytes) indicating the
  #representation of float, complex, integer and character datatypes. Bytes 215 and
  #216 are unused. The CCP4 library contains a general representation of datatypes,
  #but in practice it is safe to use 0x44 0x44 0x00 0x00 for little endian
  #machines, and 0x11 0x11 0x00 0x00 for big endian machines. The CCP4 library uses
  #this information to automatically byte-swap data if appropriate, when
  #tranferring data files between machines.

  endianness='LE' #little endian by default
  
  if(ord(machst_string[0]) & ord('\x44') == 68 and (ord(machst_string[1]) & ord('\x44') == 68  or ord(machst_string[1]) & ord('\x41') == 65)): 
    endianness='LE'
    print("MACHST indicates LE")
  if(ord(machst_string[0]) & ord('\x11') ==  ord('\x11')): 
    endianness='BE'
  if (machst_string[:2] !='DD' and machst_string[:2] !='DA' ):
    print("Warning: the MACHST string check failed. This file may not be in little endian! (should be 0x44 0x44 0x00 0x00 \"DD\")")
    print (machst_string)
    endianness='BE'
    OK =0




  header_inf={
    'MRC_NX'                : nx             ,
    'MRC_NY'                : ny             ,
    'MRC_NZ'                : nz             ,
    'c'                 : nx             , #for backward compatibility with ccp4, everything has two keys. MRC2014 items always uppercase and start with MRC_
    'r'                 : ny             ,
    's'                 : nz             ,
    'MRC_MAPMODE'           : mapmode       ,
    'mapmode'           : mapmode       ,
    'MRC_NXSTART'           : nxstart       ,
    'MRC_NYSTART'           : nystart       ,
    'MRC_NZSTART'           : nzstart       ,
    'ncstart'           : nxstart       ,
    'nrstart'           : nystart       ,
    'nsstart'           : nzstart       ,
    'MRC_MX'                : mx            ,
    'MRC_MY'                : my            ,
    'MRC_MZ'                : mz            ,
    'nx'                : mx            ,
    'ny'                : my            ,
    'nz'                : mz            ,
    'MRC_CELL_A'            : cella             ,
    'MRC_CELL_B'            : cellb             ,
    'MRC_CELL_C'            : cellc             ,
    'MRC_CELL_ALPHA'        : cellalpha         ,
    'MRC_CELL_BETA'         : cellbeta          ,
    'MRC_CELL_GAMMA'        : cellgamma         ,
    'x'                 : cella        ,
    'y'                 : cellb        ,
    'z'                 : cellc        ,
    'alpha'             : cellalpha   ,
    'beta'              : cellbeta    ,
    'gamma'             : cellgamma   ,
    'MRC_MAPC'              : mapc          ,
    'MRC_MAPR'              : mapr          ,
    'MRC_MAPS'              : maps          ,
    'mapc'              : mapc          ,
    'mapr'              : mapr          ,
    'maps'              : maps          ,
    'MRC_DMIN'              : dmin          ,
    'MRC_DMAX'              : dmax          ,
    'MRC_DMEAN'             : dmean         ,
    'amin'              : dmin          ,
    'amax'              : dmax          ,
    'amean'             : dmean         ,
    'MRC_ISPG'              : ispg          ,
    'MRC_NSYMBT'            : nsymbt        ,
    'ispg'              : ispg          ,
    'nsymbt'            : nsymbt        ,

    'MRC_EXTRA'             : extra         ,
    'lskflg'            : _lskflg        ,
    'skwmat_string'     : _skwmat_string ,
    'skwtrn_string'     : _skwtrn_string ,
    'futureuse_str'     : _futureuse_str ,
    'MRC_EXTTYP'            : exttyp        ,
    'exttyp'            : exttyp        ,

    'MRC_NVERSION'          : nversion      ,
    'nversion'          : nversion      ,
    'MRC_ORIX'              : orix          ,
    'MRC_ORIY'              : oriy          ,
    'MRC_ORIZ'              : oriz          ,
    'orix'              : orix          ,
    'oriy'              : oriy          ,
    'oriz'              : oriz          ,
    'MRC_MAP_STR'           : map_str       ,
    'MRC_MACHST_STRING'     : machst_string ,
    'MRC_MACHST_INT'        : machst       ,
    'map_str'           : map_str       ,
    'machst_string'     : machst_string ,
    'machst_int'        : machst       ,
    'MRC_rms'               : rms          ,
    'arms'               : rms          ,
    'MRC_NLABL'             : nlabl         ,
    'MRC_LABEL'             : label         ,
    'nlabl'             : nlabl         ,
    'label'             : label         ,
    'OK'                : OK             ,
    'endianness'        : endianness
  }



  outlist= \
  'nx, ny, nz:              [{}\t{}\t{}]\n'.format(nx,ny,nz) +\
  'start x, y, z:           [{}\t{}\t{}]\n'.format(nxstart,nystart,nzstart)  +\
  'map c, r, s:             [{}\t{}\t{}]\n'.format(mapc,mapr,maps) + '\n'+\
  'mx, my, mz:              [{}\t{}\t{}]\n'.format(mx,my,mz) +\
  'origins x, y, z:         [{}\t{}\t{}]\n'.format(orix,oriy,oriz) +'\n' +\
  'a, b, c:                 [{}\t{}\t{}]\n'.format(cella,cellb,cellc) +\
  'dmin, dmax:              [{}\t{}]   \n'.format(dmin,dmax,dmean) + \
  'dmean, rms:              [{}\t{}]   \n'.format(dmean,rms) + \
  'ispg, nsymbt:            [{}\t{}]\n'.format(ispg,nsymbt) + \
  'extra:                   [{}]\n'.format(extra) + \
  'map_str:                 [' + map_str + "]\n" +\
  'machst_string:           [' + str(bytearray(machst_string)).encode('hex') + "]\n" +\
  'nlabl                    ['+ str(nlabl)        + "]\n"    +\
  'label                    ['+ label  + "]\n" +\
  'Mapmode:                 [' +str(mapmode) +"] "+ MODE_TABLE_HUMAN[mapmode] + "\n" +\
  'Endianness:              [' + endianness + "]\n " 
  print (outlist)
  if(OK==1):
    print ("file check OK")
  else:
    print ("file check failed")

  return      header_inf
  
  
def read_MRC2014(filename):
    file_size=os.path.getsize(filename)
    header_inf={}
    exthdr=''
    data_1d=np.ndarray(0)
    try:
        f=open(filename,'rb')
        f.seek(0)
        header = f.read(1024)
        header_inf=parse_MRC2014_header(header,file_size)                   
        
        if header_inf['nsymbt']>0:
          exthdr = f.read(header_inf['nsymbt'])                       
        x,y,z=header_inf['MRC_NX'],header_inf['MRC_NY'],header_inf['MRC_NZ']            
        data_1d=np.fromfile(f,dtype=NUMPY_MODE[header_inf['MRC_MAPMODE']],count=x*y*z)               
    finally:                 
      f.close()
    return header_inf,exthdr,data_1d

