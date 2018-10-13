#!/usr/bin/env python
from __future__ import print_function

import struct
import os
import sys
import numpy as np

import yaml
import json
import time
  
import re
#tell user to install xmltodict

#import csv
#from tifffile import imsave
#import anymarkup
#import xml.etree.ElementTree as et
#import untangle
#import scipy.misc
#import skimage
#from skimage import io
#zlib is used by the write PNG function

def read_xmlfile(XML_file):
  if(os.path.isfile(XML_file)):
    x=open(XML_file,'rb')
    xmltext=x.read(os.path.getsize(XML_file))
    xml_dict=parse_xml(xmltext)
    x.close()
    return xml_dict,xmltext
  else:
    return {},''

def read_yamlfile(YAML_file):
  yaml_dict={}
  yamltxt={}
  with open(YAML_file, 'r') as stream:
    yamltext=stream.read(os.path.getsize(XML_file))
    try:
        yaml_dict=yaml.load(stream)
    except yaml.YAMLError as exc:
        print(exc)
  return yaml_dict,yamltxt
  
def save_safe_yaml(data,filename):
    yamltext=yaml.safe_dump(data , default_flow_style=False)
    with open(filename, 'w') as outfile:
        yaml.safe_dump(data, outfile, default_flow_style=False)
    return yamltext
def save_yaml(data,filename):
    with open(filename, 'w') as outfile:
        yaml.dump(data, outfile, default_flow_style=False)
def print_hex(astr):
  hexs=" ".join("{:02x}".format(ord(c)) for c in astr)
  print ("[{}]".format( hexs))

def print_safe_yaml(data):
  yamltext=yaml.safe_dump(data , default_flow_style=False)
  print (yamltext)
  return yamltext
def print_yaml(data):
  print (yaml.dump(data , default_flow_style=False))

  
def read_TIA_EMI_XML(base,datablock,imagesizex,imagesizey):
  base=base
  emi_file= base +'.emi'
  XML_file= base +'.xml'
  YAML_file= base +'.yaml'
  xml_dict={}
  xmltext=''
  yamltext=''
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
        
        
        if(seg>0):
          print("In EMI file: datablock start at {}-{}".format(seg+8,seg+8+len(datablock)))

          searchseg=raw[seg+8+len(datablock):file_size]
          print (len(searchseg))
          start=searchseg.find('<ObjectInfo>'.encode('utf-8'))
          end=searchseg.find('</ObjectInfo>')
          xmltext=searchseg[start:end+15] #also write 0D0A at end
          #print (xmltext)
          
          if(len(xmltext)>20): 
            print("XML data found, saving as {} and {}\n".format(XML_file,YAML_file))
            xml_dict=parse_xml(xmltext)
            
            if(os.path.isfile(XML_file)):
              print ("XML file already exists. Skipping")
            else:
              x=open(XML_file,'wb')
              x.write(xmltext)
              x.close()
            if(os.path.isfile(YAML_file)):
              print ("YAML file already exists. Skipping")
            else:
              yamltext=save_safe_yaml(xml_dict,YAML_file)
            
        else:
          print("datablock not found or different from the .ser file, abort processing the EMI file")
  except IOError:
    print ("EMI file is not found")
  return xml_dict,xmltext,yamltext
  
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
    dic2={}
    try:
      import xmltodict
      dic=xmltodict.parse(xmltext)
      dic1=json.dumps(dic)
      dic2=json.loads(dic1)
    except ImportError:
      print ("\n!!! This program needs module <xmltodict> for interpreting XML data. You can install xmltodict by:\n pip install xmltodict\n")
      pass

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
  numpy_dtypechart={
        1  : np.uint8        ,    #1 - Unsigned 1-byte integer	
        2  : np.uint16       ,    #2 - Unsigned 2-byte integer	
        3  : np.uint32       ,    #3 - Unsigned 4-byte integer	
        4  : np.int8         ,    #4 - Signed 1-byte integer	
        5  : np.int16        ,    #5 - Signed 2-byte integer	
        6  : np.int32        ,    #6 - Signed 4-byte integer	
        7  : np.float32      ,    #7 - 4-byte float	
        8  : np.float64           #8 - 8-byte float	
  }
  return typechart[typenumber],sizechart[typenumber],fmtchart[typenumber],numpy_dtypechart[typenumber]

def get_namebase(filename):
    base=os.path.splitext(filename)[0]
    parts=re.search('^(.+)(_\d+)$',base)
    if(parts and parts.group(2)):
      base=parts.group(1)
    #print(parts.group(0),parts.group(1),parts.group(2),base)
    return base
    
def process_ser_file(filename):

      base =get_namebase(filename) #cut off the _1.ser _2.ser from filename

      EMI_filename= base +'.emi'
      XML_filename= base +'.xml'
      YAML_filename= base +'.yaml'
  
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
              
              datatype,point_bytes,datafmt,numpy_dtype=get_datatype(data_header['DataType'])
              datasize=ysize*xsize*point_bytes #bytes in data array

              fmt='<'+str(ysize*xsize)+datafmt;

              print ('datatype: [{}]\ndatasize: {} byte           format charctor: \'{}\''.format(datatype,point_bytes,datafmt))
              print ('format string "{}"'.format(fmt))
              print()
              
              #data=struct.unpack(fmt, raw[header_inf['DataOffset']+50:header_inf['DataOffset']+50+datasize])
              data=np.fromstring(raw[header_inf['DataOffset']+50:header_inf['DataOffset']+50+datasize],dtype=numpy_dtype) #for now just assume int32 data(CCD)
              
              negativelist,=np.where(data<0)
              
              if( len(negativelist) > 0):
                print("negative values found at:",negativelist,data[negativelist],"converted to 0")
                data[negativelist]=0
              
              neg_data=data*(-1) #invert
              
              amax=data.max()
              amin=data.min()
              amean=data.mean()
              arms=stdev=data.std()

              print ("min:{}\t max: {} \t mean:{}\tstdev:{}\t".format(amin,amax,amean,stdev))
              collect_time=''
              if(header_inf['TagTypeID']==0x4152): #just time, really not worth reading
                mark,=tag_time,=struct.unpack('<h', raw[header_inf['Tag_offset']:header_inf['Tag_offset']+2])
                tag_time,=struct.unpack('<i', raw[header_inf['Tag_offset']+4:header_inf['Tag_offset']+4+4])
                collect_time=time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(tag_time+6*3600))
                print(time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(tag_time+6*3600))) #somthing wrong with MSB TIA time.
                print(time.time(),time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time())))
                #print ('\n{}\n'.format(mark))
                
              xml_dict,xmltext,yamltext={},'',''
              if(os.path.isfile(EMI_filename)):
                xml_dict,xmltext,yamltext=read_TIA_EMI_XML(base,raw[header_inf['DataOffset']+50:header_inf['DataOffset']+50+datasize],ysize,xsize)
              elif(os.path.isfile(XML_filename)):
                xml_dict,xmltext=read_xmlfile(XML_filename)
              elif(os.path.isfile(YAML_filename)):
                xml_dict,xmltext=read_yamlfile(YAML_filename)
              apix,magnification,defocus,kV=(1.0,1,0,0)
              
              if(xml_dict):
                apix,magnification,defocus,kV=print_xml_data(xml_dict)
              apix_from_header=float(data_header['CalibrationDeltaX']*10000000000)
              pixel_size=apix_from_header*magnification/10000 #um
              desc_data=xmltext
              collect_time=re.sub(
                r' ',
                r'_',
                collect_time
              )
              
              collect_time_compact=line = re.sub(
                      r"[ :-]", 
                      "",            
                      collect_time       )
              print (">>>>>>",collect_time,collect_time_compact)
              infstr='_{:4.3f}Ap_{:d}KX_{}um_{:d}kV_mean{:d}_{}'.format(apix_from_header,int(magnification/1000),defocus,kV,int(amean),collect_time_compact)
              tif_name=filename+infstr+'.tif'
              tif8_name=filename+infstr+'.uint8.tif'
              mrc_name=filename+infstr+'.mrc'



#              hs=np.histogram(data,bins=amax-amin) 
#              print(hs)                                     
#              for i in range(amax-amin):
#                  print ("{} {} {}".format(i,hs[0][i],hs[1][i]))
              
              save_tiff=True
              save_mrc =True
              if(save_tiff == True):
                import EM_tiff
                EM_tiff.save_tiff8(neg_data,desc_data,tif8_name,-amin,-amax,ysize,xsize)     
                EM_tiff.save_tiff16_no_rescaling(data,desc_data,tif_name,amax,amin,ysize,xsize)     
              if(save_mrc == True):
                import mrc
                d1=data.reshape(xsize,ysize,1)
                to_type=''
                if(amax<65536/2 and amin>=0):
                  to_type=np.int16
                else:
                  to_type=np.float32
                data_16int=d1.astype(to_type)
                mrc.save_mrc(mrc_name,data_16int, desc=xmltext,hdr_apix=apix_from_header)
              #df = data.astype(np.float32) 
              #d0=df*127/amax
              #d1=d0.reshape(ysize,xsize,1)
              #d2=d1.astype(np.int8)

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