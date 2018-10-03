#!/usr/bin/env python
from __future__ import print_function

import struct
import os
import sys
import yaml
import json
#import csv
#import numpy as np
import time
import xmltodict
import re
#from tifffile import imsave
import numpy as np
from libtiff import TIFF
#import anymarkup
#import xml.etree.ElementTree as et
#import untangle
#import scipy.misc
#import skimage
#from skimage import io
#zlib is used by the write PNG function

def save_safe_yaml(data,filename):
    with open(filename, 'w') as outfile:
        yaml.safe_dump(data, outfile, default_flow_style=False)
def save_yaml(data,filename):
    with open(filename, 'w') as outfile:
        yaml.dump(data, outfile, default_flow_style=False)
def print_hex(astr):
  hexs=" ".join("{:02x}".format(ord(c)) for c in astr)
  print ("[{}]".format( hexs))

def print_safe_yaml(data):
  print (yaml.safe_dump(data , default_flow_style=False))
def print_yaml(data):
  print (yaml.dump(data , default_flow_style=False))

  
def read_TIA_EMI_XML(filename,datablock,imagesizex,imagesizey):
  base=os.path.splitext(filename)[0]
  parts=re.search('^(.+)(_\d)$',base)
  if(parts and parts.group(2)):
    base=parts.group(1)
    #print(parts.group(0),parts.group(1),parts.group(2),base)
  emi_file= base +'.emi'
  XML_file= base +'.xml'
  YAML_file= base +'.yaml'
  xml_dict={}
  try:
        f=open(emi_file,'rb')
        file_size=os.path.getsize(emi_file)
        if(file_size<len(datablock)):
          return 0
        print("\nEMI file is found: <{}>. File size: {} bytes".format(emi_file,file_size))
        f.seek(0)
        raw = f.read(file_size)
        f.close
        mark=struct.pack('<ii',imagesizex,imagesizey)
        d1024= mark+ datablock[:256] #the data segment in emi file starts with x,y dimensions, datablock is same as in the SER. Here using first 256 byte for locating
        seg=raw.find(d1024)
        print("In EMI file: datablock start at {}-{}".format(seg+8,seg+8+len(datablock)))
        if(seg>0):
          #print('searching for XML')
          searchseg=raw[seg+8+len(datablock):file_size]
          #print (len(searchseg))
          start=searchseg.find('<ObjectInfo>')
          end=searchseg.find('</ObjectInfo>')
          xmltext=searchseg[start:end+15] #also write 0D0A at end
          #print (xmltext)
          
          if(len(xmltext)>20): 
            print("XML data found, saving as {} and {}\n".format(XML_file,YAML_file))
            x=open(XML_file,'wb')
            x.write(xmltext)
            x.close()
            xml_dict=parse_xml(xmltext)
            save_safe_yaml(xml_dict,YAML_file)
        
  finally:
    pass
  return xml_dict
  
def print_xml_data(xml_dict):
  for k,v in (xml_dict['ObjectInfo']['AcquireInfo']).iteritems():
    print ('{:>30s}\t{}'.format(k,v))
  
  print ('{0:>30s}\t[{2}\t{1}]'.format('Pixel X,Y',xml_dict['ObjectInfo']['DetectorPixelHeight'],  xml_dict['ObjectInfo']['DetectorPixelWidth']))
  print ('{0:>30s}\t{1}'.format('Tilt1',xml_dict['ObjectInfo']['ExperimentalConditions']['MicroscopeConditions']['Tilt1']))
  print ('{0:>30s}\t{1}'.format('Tilt2',xml_dict['ObjectInfo']['ExperimentalConditions']['MicroscopeConditions']['Tilt2']))
  
  magnification=1
  defocus=0
  kV=-1
  for k in xml_dict['ObjectInfo']['ExperimentalDescription']['Root']['Data']:
    if(k['Unit']==None):
      k['Unit']=''
    if(k['Label']=='Magnification'):
      magnification=int(k['Value'])
    if(k['Label']=='Defocus'):
      defocus=float(k['Value'])
    if(k['Label']=='High tension'):
      kV=int(k['Value'])
    
    print ('{:>30s}\t{} {}'.format(k['Label'],k['Value'],k['Unit']))
  if(xml_dict['ObjectInfo']['AcquireInfo']['CameraNamePath']=='BM-Ceta'): 
    #Ceta-16M pixel size 14um, 9counts/primary electrno @200kV; 6 counts/e @300kV; readout 320Mp/s; 4kx4k 1fps; 2kx2k 8fps 1kx1k 18fps 512x512 25fps; Dupy cycle 99% in rolling shutter mode
    pixsize=14.0 #um
    apix=pixsize*10000/magnification
    print ('{:>30s}\t{} (calculated from 14um pixel / {})'.format('Apix',(apix),magnification))
    return (apix,magnification,defocus,kV)
    
def parse_xml(xmltext):
    dic=xmltodict.parse(xmltext)
    dic1=json.dumps(dic)
    dic2=json.loads(dic1)
    #print_safe_yaml(dic2)
    return dic2


def read_TIA_SER_header(header_data,filesize):
  '''
  Interprets TIA SER file (.ser) header, based on http://www3.ntu.edu.sg/home/cbb/info/TIAformat/TIAseriesformat.pdf and http://www3.ntu.edu.sg/home/cbb/info/TIAformat/index.html
  '''

  
  ByteOrder,\
  SeriesID,\
  SeriesVersion,\
  DataTypeID,\
  TagTypeID,\
  TotalNumberElements,\
  ValidNumberElements,\
  = struct.unpack("<hhhiiii", header_data[:22])
  TagType='2D-position + Time'
  if(TagTypeID==0x4152):
    TagType='Time Only'
  OK = 1
  if(ByteOrder!=0x4949 or SeriesID != 0x0197):
    print ("Magic word check failed, exit\n")
    OK=0
    exit(0)
  if(DataTypeID!=0x4122):
    print ("Data is 1-D array, not image, exit\n")
    OK=0
    exit(0)
  OffsetArrayOffset=512
  NumberDimensions=0
  Dim_array_offset=34
  
  if(SeriesVersion==0x0210):
    OffsetArrayOffset,\
    NumberDimensions\
    =struct.unpack("<ii", header_data[22:22+8])
    Dim_array_offset=30
  if(SeriesVersion==0x0220):
    OffsetArrayOffset,\
    NumberDimensions\
    =struct.unpack("<qi", header_data[22:22+12])
  if(TotalNumberElements>1):
    print("Currently only 1 element is supported. exit\n")
    exit()
  
  Dim_array=read2_dimention_array(header_data,Dim_array_offset)
  
  DTA_offset,=struct.unpack("<q", header_data[Dim_array['end_position'] : Dim_array['end_position']+8])
  Tag_offset,=struct.unpack("<q", header_data[Dim_array['end_position'] +8: Dim_array['end_position']+16])
  
  header_inf={
  'ByteOrder'             : ByteOrder               ,
  'SeriesID'              : SeriesID                ,
  'SeriesVersion'         : SeriesVersion           ,
  'DataTypeID'            : DataTypeID              ,
  'TagTypeID'             : TagTypeID               ,
  'TagType'               : TagType                 ,
  'TotalNumberElements'   : TotalNumberElements     ,
  'ValidNumberElements'   : ValidNumberElements     ,
  'OffsetArrayOffset'     : OffsetArrayOffset       ,
  'NumberDimensions'      : NumberDimensions        ,
  'DimensionSize'         :  Dim_array['DimensionSize'],     
  #'CalibrationOffset'     :  Dim_array['CalibrationOffset'], 
  #'CalibrationDelta'      :  Dim_array['CalibrationDelta'],  
  #'CalibrationElement'    :  Dim_array['CalibrationElement'],
  #'DescriptionLength'     :  Dim_array['DescriptionLength'],  
  #'Descritpion'           :  Dim_array['Descritpion'],        
  #'UnitsLength'           :  Dim_array['UnitsLength'],        
  #'Units'                 :  Dim_array['Units']              ,
  'dim'                    :  Dim_array,
  'DataOffset'             :  DTA_offset,
  'Tag_offset'             :  Tag_offset
  }
  print_yaml(header_inf)
  return header_inf

def read2_dimention_array(header_data,Dim_array_offset):

  DimensionSize,\
  CalibrationOffset,\
  CalibrationDelta,\
  CalibrationElement,\
  DescriptionLength\
  = struct.unpack("<iddii", header_data[Dim_array_offset:Dim_array_offset+28])
  #print_hex(header_data[Dim_array_offset+0:Dim_array_offset+28])
  
  Descritpion  = header_data[Dim_array_offset+28:Dim_array_offset+28+DescriptionLength]
  UnitsLength,  = struct.unpack("<i", header_data[Dim_array_offset+28+DescriptionLength:Dim_array_offset+28+DescriptionLength+4])
  end =Dim_array_offset+28+DescriptionLength+4+UnitsLength
  Units        = header_data[end-UnitsLength : end]
  
  Dim_array ={
  'DimensionSize'         :  DimensionSize,     
  'CalibrationOffset'     :  CalibrationOffset, 
  'CalibrationDelta'      :  CalibrationDelta,  
  'CalibrationElement'    :  CalibrationElement,
  'DescriptionLength'     :  DescriptionLength,  
  'Descritpion'           :  Descritpion,        
  'UnitsLength'           :  UnitsLength,        
  'Units'                 :  Units,              
  'end_position'          :  end
  }

  return Dim_array

  
def read5_data(header_data,offset):
  CalibrationOffsetX,  \
  CalibrationDeltaX,   \
  CalibrationElementX, \
  CalibrationOffsetY,  \
  CalibrationDeltaY,   \
  CalibrationElementY, \
  DataType,            \
  ArraySizeX,          \
  ArraySizeY           \
  =          struct.unpack("<ddiddihii", header_data[offset:offset+50])

  #print_hex(header_data[offset+0:offset+8])
  #print_hex(header_data[offset+8:offset+16])

  #print_hex(header_data[offset+20:offset+28])
  #print_hex(header_data[offset+28:offset+36])

  data_header={
  'CalibrationOffsetX'    : CalibrationOffsetX,  \
  'CalibrationDeltaX'     : CalibrationDeltaX,   \
  'CalibrationElementX'   : CalibrationElementX, \
  'CalibrationOffsetY'    : CalibrationOffsetY,  \
  'CalibrationDeltaY'     : CalibrationDeltaY,   \
  'CalibrationElementY'   : CalibrationElementY, \
  'DataType'              : DataType,            \
  'ArraySizeX'            : ArraySizeX,          \
  'ArraySizeY'            : ArraySizeY           \
  }
  print_yaml( data_header)
  return data_header
  
def save_tiff8(buff,desc_data,tif_name,amax,ysize,xsize):
  data = np.asarray(buff,dtype=np.float32) 
  d0=data*255/amax
  d1=d0.reshape(ysize,xsize)
  d2=d1.astype(np.uint8)
  #print("{} {} {}".format(d2[0][0], d2.shape,d2.dtype))
  tiff = TIFF.open(tif_name, mode='w')
  tiff.write_image(d2)
  tiff.close()

def save_tiff16(buff,desc_data,tif_name,amax,ysize,xsize):
  data = np.asarray(buff,dtype=np.float32) 
  d0=data*65535/amax
  d1=d0.reshape(ysize,xsize)
  d2=d1.astype(np.uint16)
  #print("{} {} {}".format(d2[0][0], d2.shape,d2.dtype))
  tiff = TIFF.open(tif_name, mode='w')
  tiff.write_image(d2)
  tiff.close()

def get_datatype(typenumber):
  typechart={
        1  : '1 - Unsigned 1-byte integer' ,
        2  : '2 - Unsigned 2-byte integer' ,
        3  : '3 - Unsigned 4-byte integer' ,
        4  : '4 - Signed 1-byte integer	 ' ,
        5  : '5 - Signed 2-byte integer	 ' ,
        6  : '6 - Signed 4-byte integer	 ' ,
        7  : '7 - 4-byte float	         ' ,
        8  : '8 - 8-byte float	         ' ,
        9  : '9 - 8-byte complex	       ' ,
        10 : '10 - 16-byte complex       ' 
  }  
  sizechart={
        1  : 1        ,   #1 - Unsigned 1-byte integer	
        2  : 2        ,   #2 - Unsigned 2-byte integer	
        3  : 4        ,   #3 - Unsigned 4-byte integer	
        4  : 1        ,   #4 - Signed 1-byte integer	
        5  : 2        ,   #5 - Signed 2-byte integer	
        6  : 4        ,   #6 - Signed 4-byte integer	
        7  : 4        ,   #7 - 4-byte float	
        8  : 8        ,   #8 - 8-byte float	
        9  : 8        ,   #9 - 8-byte complex	
        10 : 16           #10 - 16-byte complex
  }
  fmtchart={
        1  : 'B'       ,    #1 - Unsigned 1-byte integer	
        2  : 'H'       ,    #2 - Unsigned 2-byte integer	
        3  : 'I'       ,    #3 - Unsigned 4-byte integer	
        4  : 'b'       ,    #4 - Signed 1-byte integer	
        5  : 'h'       ,    #5 - Signed 2-byte integer	
        6  : 'i'       ,    #6 - Signed 4-byte integer	
        7  : 'f'       ,    #7 - 4-byte float	
        8  : 'd'       ,    #8 - 8-byte float	
        9  : 'ff'      ,     #9 - 8-byte complex	
        10 : 'dd'           #10 - 16-byte complex
  }
  return typechart[typenumber],sizechart[typenumber],fmtchart[typenumber]
  
def process_ser_file(filename):
      f=open(filename,'rb')
      file_size=os.path.getsize(filename)
      #print("File size: {} bytes".format(file_size))
      try:
          f.seek(0)
          raw = f.read(file_size)
          if raw:
              
              header_inf=read_TIA_SER_header(raw[:2048],file_size)
              data_header=read5_data(raw[:2048],header_inf['DataOffset'])
              ysize,xsize=(data_header['ArraySizeY'],data_header['ArraySizeX'])
              
              datatype,point_bytes,datafmt=get_datatype(data_header['DataType'])
              datasize=ysize*xsize*point_bytes #bytes in data array

              fmt='<'+str(ysize*xsize)+datafmt;

              print ('datatype: [{}]\ndatasize: {} byte           format charctor: \'{}\''.format(datatype,point_bytes,datafmt))
              print ('format string "{}"'.format(fmt))
              print()
              
              #data=struct.unpack(fmt, raw[header_inf['DataOffset']+50:header_inf['DataOffset']+50+datasize])
              data=np.fromstring(raw[header_inf['DataOffset']+50:header_inf['DataOffset']+50+datasize],dtype=np.int32)
              amax=data.max()
              amin=data.min()
              amean=data.mean()
              print ("min: {}\t max: {} \t mean:{}".format(amin,amax,amean))
#              if(amin<0 or amax >65535):
#                count1=0
#                count2=0
#                for i in data:
#                  if i>65535:
#                    count1+=1
#                  if i<0:
#                    count2+=1
#                print ("{} pixels are >65535, {} pixels are negative".format(count1,count2))
              if(header_inf['TagTypeID']==0x4152): #just time, really not worth reading
                mark,=tag_time,=struct.unpack('<h', raw[header_inf['Tag_offset']:header_inf['Tag_offset']+2])
                tag_time,=struct.unpack('<i', raw[header_inf['Tag_offset']+4:header_inf['Tag_offset']+4+4])
                print(time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(tag_time+6*3600))) #somthing wrong with MSB TIA time.
                #print(time.time(),time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time())))
                #print ('\n{}\n'.format(mark))
              xml_dict=read_TIA_EMI_XML(filename,raw[header_inf['DataOffset']+50:header_inf['DataOffset']+50+datasize],ysize,xsize)
              apix,magnification,defocus,kV=print_xml_data(xml_dict)
              desc_data=xml_dict
              infstr='_{:3.2f}Ap_{:d}KX_{}um_{:d}kV_mean{:d}'.format(apix,int(magnification/1000),defocus,kV,int(amean))
              tif_name=filename+infstr+'.tif'
              
              save_tiff8(data,desc_data,tif_name,amax,ysize,xsize)     
#              hs=np.histogram(data,bins=amax-amin) 
#              print(hs)                                     
#              for i in range(amax-amin):
#                  print ("{} {} {}".format(i,hs[0][i],hs[1][i]))
      finally:
          f.close()


############################main##################
def main():

    
    if len(sys.argv)>1 and sys.argv[1]:
      files=sys.argv[1:]
      
    else: 
      print ("Please provide .ser file as arguments")
      sys.exit(0)
    
    for filename in files:
      process_ser_file(filename)

#####################3
main()