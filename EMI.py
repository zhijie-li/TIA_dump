#!/usr/bin/env python
from __future__ import print_function
import common
import struct
import os,sys

import json
import xmltodict
import re
import numpy as np



def print_hex(astr):
  hexs=" ".join("{:02x}".format(ord(c)) for c in astr)
  
  print ("<{}>".format( hexs), end='\t')







def read_int8(chunk):
  value,=struct.unpack('<q',chunk[4:12])
  incr=12;
  return(value,incr)

def read_int4(chunk):
  value,=struct.unpack('<i',chunk[4:8])
  incr=8;
  return(value,incr)

def read_int2(chunk):
  value,=struct.unpack('h',chunk[4:6])
  incr=6;
  return(value,incr)

def read_uint1(chunk):
  value,=struct.unpack('B',chunk[4:5])
  incr=5;
  return(value,incr)

def read_bool(chunk):
  value,=struct.unpack('?',chunk[4:5])
  incr=5;
  return(value,incr)

def read_float8(chunk):
  value,=struct.unpack('<d',chunk[4:12])
  incr=12;
  return(value,incr)

def read_float4(chunk):
  value,=struct.unpack('<f',chunk[4:8])
  incr=8;
  return(value,incr)


def read_str(chunk):
  length,=struct.unpack('<i',chunk[4:8])
  value=chunk[8:8+length]
  incr=8+length
  return(value,incr)



  
def type_tags(chunk):
  typestr='unknown'
  o=chr(0x00)
  if(chunk==chr(0x20)+o):
    typestr='I1'
  if(chunk==chr(0x30)+o or chunk==chr(0x32)+o):
    typestr='i2'
  if(chunk==chr(0x31)+o):
    typestr='i4'
  if(chunk==chr(0x34)+o):
    typestr='i8'
  if(chunk==chr(0x41)+o):
    typestr='f8'
  if(chunk==chr(0x60)+o):
    typestr='string'
  if(chunk==chr(0x02)+chr(0x21)):
    typestr='string'
  if(chunk==chr(0x30)+chr(0x41)):
    typestr='ary_f8'
  if(chunk==chr(0x32)+chr(0x41)):
    typestr='ary_f8'
  if(chunk==chr(0x20)+chr(0x43)):
    typestr='ary_i4'
  if(chunk==chr(0x2C)+chr(0x43)):
    typestr='ary_i1'
  if(chunk==chr(0x70)+chr(0x00)):
    typestr='bool'
  if(chunk==chr(0x08)+chr(0x22)): ##datablock
    typestr='dta'
  if(chunk==chr(0x14)+chr(0x22)): ##FFT block
    typestr='dta'
  if(chunk==o+o):
    typestr='===='
  return typestr

def read_EMI_header(file_chunk,args):
  datamet=0
  total=len(file_chunk)
  
  if(file_chunk[:2] != 'JK'):
    print("EMI magic words test failure,exit now")
    exit(0)
  offset=12 #start from 12  
  prestr=''
  preoff=offset
  
  data_ndarray=np.ndarray(1)
  xml_list=[]
  xml_dict={}
  while(offset<total-2):
      if (args.v):print("{:08x}:".format(offset),end='\t')
      typestr=type_tags(file_chunk[offset:offset+2])
      if(typestr=='dta'): #datablock 
        offset-=5
        
        if (args.v):print_hex(file_chunk[offset:offset+21])
        
        dta_type=ord(file_chunk[offset+4]) ###need a lot of tests here '0x06' int32 '0x09' complex float32 (FFT)
        
        dta_size,dta_x,dta_y=struct.unpack("<iii",file_chunk[offset+9:offset+21])

        dta_size-=8 #8bytes used for x and y
        dta_start=offset+21
        if (args.v):print("datatype {} {} {} {}".format( dta_type,dta_size,dta_x,dta_y))
        if(dta_type==6):
          data_ndarray=np.fromstring(file_chunk[dta_start:dta_start+dta_size],dtype=np.int32)

          if (args.v):print("datablock found: X{} Y{} start{} {}bytes".format(dta_x,dta_y,dta_start,dta_size))
          if (args.v):print_hex(file_chunk[dta_start:dta_start+16])
          if (args.v):print('\n...')
          if (args.v):print_hex(file_chunk[dta_start+dta_size-16:dta_start+dta_size])
          if (args.v):print()
        if(dta_type==9):
          #data_ndarray=np.fromstring(file_chunk[dta_start:dta_start+dta_size],dtype=np.complex64) #noneed to read

          if (args.v):print("Complex datablock found: X{} Y{} start{} {}bytes".format(dta_x,dta_y,dta_start,dta_size))
          if (args.v):print_hex(file_chunk[dta_start:dta_start+16])
          if (args.v):print('\n...')
          if (args.v):print_hex(file_chunk[dta_start+dta_size-16:dta_start+dta_size])
          if (args.v):print()
        offset+=dta_size+21+4

      if(typestr=='unknown'):
        if (args.v):print_hex(file_chunk[offset:offset+4])
        if (args.v):print('!!!!!!!!unknown')
        offset+=4
      if(typestr=='===='):
        if (args.v):print_hex(file_chunk[offset:offset+2])
        if (args.v):print(typestr)
        offset+=2
      if(typestr=='I1' or typestr=='bool' ):
        val,incr=read_uint1(file_chunk[offset:offset+200])
        if (args.v):print_hex(file_chunk[offset:offset+incr])
        if (args.v):print("{} [{}]".format(typestr,val))
        offset+=incr
      if(typestr=='i2'):
        val,incr=read_int2(file_chunk[offset:offset+200])
        if (args.v):print_hex(file_chunk[offset:offset+incr])
        if (args.v):print("{} [{}]".format(typestr,val))
        offset+=incr
      if(typestr=='i4'):
        val,incr=read_int4(file_chunk[offset:offset+200])
        if (args.v):print_hex(file_chunk[offset:offset+incr])
        if (args.v):print("{} [{}]".format(typestr,val))
        offset+=incr
      if(typestr=='i8'):
        val,incr=read_int8(file_chunk[offset:offset+200])
        if (args.v):print_hex(file_chunk[offset:offset+incr])
        if (args.v):print("{} [{}]".format(typestr,val))
        offset+=incr
      if(typestr=='f8'):
        val,incr=read_float8(file_chunk[offset:offset+200])
        if (args.v):print_hex(file_chunk[offset:offset+incr])
        if (args.v):print("{} [{}]".format(typestr,val))
        offset+=incr
      if(typestr=='string'):
        val,incr=read_str(file_chunk[offset:offset+20000])
        if (args.v):print_hex(file_chunk[offset:offset+incr])
        if (args.v):print("{} [{}]".format(typestr,val))
        if(len(val)>50 and val.find('ObjectInfo>')>0):
          xml_list.append(val)
          #if (args.v):print(">>>>>>>>\n{}<<<<<<<<<<<".format(val))
          
        offset+=incr
      if(typestr=='ary_i1' or typestr=='ary_i4' or typestr=='ary_i8' or typestr=='ary_f8'):
        if (args.v):print_hex(file_chunk[offset:offset+incr])
        if (args.v):print("{}".format(typestr))
        offset+=4
      if(preoff==offset):
        if (args.v):print(typestr)
        exit()
      prestr=typestr
      preoff=offset  
      
  return xml_list,data_ndarray #data_ndarray is int32


#def process_xml(xmltext,XML_file,YAML_file):
#            print("XML data found, saving as {} and {}\n".format(XML_file,YAML_file))
#            x=open(XML_file,'wb')
#            x.write(xmltext)
#            x.close()
#            xml_dict=parse_xml(xmltext)
#            save_safe_yaml(xml_dict,YAML_file)
#



  
#def read_TIA_EMI_XML(filename,datablock,imagesizex,imagesizey):
#  base=os.path.splitext(filename)[0]
#  parts=re.search('^(.+)(_\d)$',base)
#  if(parts and parts.group(2)):
#    base=parts.group(1)
#    #print(parts.group(0),parts.group(1),parts.group(2),base)
#  emi_file= base +'.emi'
#  XML_file= base +'.xml'
#  YAML_file= base +'.yaml'
#  xml_dict={}
#  try:
#        f=open(emi_file,'rb')
#        file_size=os.path.getsize(emi_file)
#        if(file_size<len(datablock)):
#          return 0
#        print("\nEMI file is found: <{}>. File size: {} bytes".format(emi_file,file_size))
#        f.seek(0)
#        raw = f.read(file_size)
#        f.close
#        mark=struct.pack('<ii',imagesizex,imagesizey)
#        d1024= mark+ datablock[:256] #the data segment in emi file starts with x,y dimensions, datablock is same as in the SER. Here using first 256 byte for locating
#        seg=raw.find(d1024)
#        print("In EMI file: datablock start at {}-{}".format(seg+8,seg+8+len(datablock)))
#        if(seg>0):
#          #print('searching for XML')
#          searchseg=raw[seg+8+len(datablock):file_size]
#          #print (len(searchseg))
#          start=searchseg.find('<ObjectInfo>')
#          end=searchseg.find('</ObjectInfo>')
#          xmltext=searchseg[start:end+15] #also write 0D0A at end
#          #print (xmltext)
#          
#          if(len(xmltext)>20): 
#            print("XML data found, saving as {} and {}\n".format(XML_file,YAML_file))
#            x=open(XML_file,'wb')
#            x.write(xmltext)
#            x.close()
#            xml_dict=parse_xml(xmltext)
#            save_safe_yaml(xml_dict,YAML_file)
#        
#  finally:
#    pass
#  return xml_dict
  
def print_xml_data(xml_dict):
  magnification=1
  defocus=0
  kV=-1
  C2=0
  nP='uP'
  spot=5
  DwellTimePath=0

  for k,v in (xml_dict['ObjectInfo']['AcquireInfo']).iteritems():
    print ('{:>30s}\t{}'.format(k,v))
    if(k=='DwellTimePath'):
      DwellTimePath=float(v)

  print ('{0:>30s}\t[{2}\t{1}]'.format('Pixel X,Y',xml_dict['ObjectInfo']['DetectorPixelHeight'],  xml_dict['ObjectInfo']['DetectorPixelWidth']))
  print ('{0:>30s}\t{1}'.format('Tilt1',xml_dict['ObjectInfo']['ExperimentalConditions']['MicroscopeConditions']['Tilt1']))
  print ('{0:>30s}\t{1}'.format('Tilt2',xml_dict['ObjectInfo']['ExperimentalConditions']['MicroscopeConditions']['Tilt2']))
  
  for k in xml_dict['ObjectInfo']['ExperimentalDescription']['Root']['Data']:
    if(k['Unit']==None):
      k['Unit']=''
    if(k['Label']=='Magnification'):
      magnification=int(k['Value'])
    if(k['Label']=='Defocus'):
      defocus=float(k['Value'])
    if(k['Label']=='High tension'):
      kV=int(k['Value'])
    if(k['Label']=='Intensity'):
      C2=float(k['Value'])
    if(k['Label']=='Mode'):
      nP=k['Value'][4:6]
    if(k['Label']=='Spot size'):
      spot=int(k['Value'])
      
    
    print ('{:>30s}\t{} {}'.format(k['Label'],k['Value'],k['Unit']))
  if(xml_dict['ObjectInfo']['AcquireInfo']['CameraNamePath']=='BM-Ceta'): 
    #Ceta-16M pixel size 14um, 9counts/primary electrno @200kV; 6 counts/e @300kV; readout 320Mp/s; 4kx4k 1fps; 2kx2k 8fps 1kx1k 18fps 512x512 25fps; Dupy cycle 99% in rolling shutter mode
    pixsize=14.0 #um
    apix=pixsize*10000/magnification
    print ('{:>30s}\t{} (calculated from 14um pixel / {})'.format('Apix',(apix),magnification))
    return (apix,magnification,defocus,kV,C2,nP,spot,DwellTimePath)
    
def parse_xml(xmltext):
    #print(xmltext)
    dic=xmltodict.parse(xmltext)
    dic1=json.dumps(dic)
    dic2=json.loads(dic1)
    #print_safe_yaml(dic2)
    return dic2


#def read_TIA_SER_header(header_data,filesize):
#  '''
#  Interprets TIA SER file (.ser) header, based on http://www3.ntu.edu.sg/home/cbb/info/TIAformat/TIAseriesformat.pdf and http://www3.ntu.edu.sg/home/cbb/info/TIAformat/index.html
#  '''
#
#  
#  ByteOrder,\
#  SeriesID,\
#  SeriesVersion,\
#  DataTypeID,\
#  TagTypeID,\
#  TotalNumberElements,\
#  ValidNumberElements,\
#  = struct.unpack("<hhhiiii", header_data[:22])
#  TagType='2D-position + Time'
#  if(TagTypeID==0x4152):
#    TagType='Time Only'
#  OK = 1
#  if(ByteOrder!=0x4949 or SeriesID != 0x0197):
#    print ("Magic word check failed, exit\n")
#    OK=0
#    exit(0)
#  if(DataTypeID!=0x4122):
#    print ("Data is 1-D array, not image, exit\n")
#    OK=0
#    exit(0)
#  OffsetArrayOffset=512
#  NumberDimensions=0
#  Dim_array_offset=34
#  
#  if(SeriesVersion==0x0210):
#    OffsetArrayOffset,\
#    NumberDimensions\
#    =struct.unpack("<ii", header_data[22:22+8])
#    Dim_array_offset=30
#  if(SeriesVersion==0x0220):
#    OffsetArrayOffset,\
#    NumberDimensions\
#    =struct.unpack("<qi", header_data[22:22+12])
#  if(TotalNumberElements>1):
#    print("Currently only 1 element is supported. exit\n")
#    exit()
#  
#  Dim_array=read2_dimention_array(header_data,Dim_array_offset)
#  
#  DTA_offset,=struct.unpack("<q", header_data[Dim_array['end_position'] : Dim_array['end_position']+8])
#  Tag_offset,=struct.unpack("<q", header_data[Dim_array['end_position'] +8: Dim_array['end_position']+16])
#  
#  header_inf={
#  'ByteOrder'             : ByteOrder               ,
#  'SeriesID'              : SeriesID                ,
#  'SeriesVersion'         : SeriesVersion           ,
#  'DataTypeID'            : DataTypeID              ,
#  'TagTypeID'             : TagTypeID               ,
#  'TagType'               : TagType                 ,
#  'TotalNumberElements'   : TotalNumberElements     ,
#  'ValidNumberElements'   : ValidNumberElements     ,
#  'OffsetArrayOffset'     : OffsetArrayOffset       ,
#  'NumberDimensions'      : NumberDimensions        ,
#  'DimensionSize'         :  Dim_array['DimensionSize'],     
#  #'CalibrationOffset'     :  Dim_array['CalibrationOffset'], 
#  #'CalibrationDelta'      :  Dim_array['CalibrationDelta'],  
#  #'CalibrationElement'    :  Dim_array['CalibrationElement'],
#  #'DescriptionLength'     :  Dim_array['DescriptionLength'],  
#  #'Descritpion'           :  Dim_array['Descritpion'],        
#  #'UnitsLength'           :  Dim_array['UnitsLength'],        
#  #'Units'                 :  Dim_array['Units']              ,
#  'dim'                    :  Dim_array,
#  'DataOffset'             :  DTA_offset,
#  'Tag_offset'             :  Tag_offset
#  }
#  print_yaml(header_inf)
#  return header_inf
#
#def read2_dimention_array(header_data,Dim_array_offset):
#
#  DimensionSize,\
#  CalibrationOffset,\
#  CalibrationDelta,\
#  CalibrationElement,\
#  DescriptionLength\
#  = struct.unpack("<iddii", header_data[Dim_array_offset:Dim_array_offset+28])
#  #print_hex(header_data[Dim_array_offset+0:Dim_array_offset+28])
#  
#  Descritpion  = header_data[Dim_array_offset+28:Dim_array_offset+28+DescriptionLength]
#  UnitsLength,  = struct.unpack("<i", header_data[Dim_array_offset+28+DescriptionLength:Dim_array_offset+28+DescriptionLength+4])
#  end =Dim_array_offset+28+DescriptionLength+4+UnitsLength
#  Units        = header_data[end-UnitsLength : end]
#  
#  Dim_array ={
#  'DimensionSize'         :  DimensionSize,     
#  'CalibrationOffset'     :  CalibrationOffset, 
#  'CalibrationDelta'      :  CalibrationDelta,  
#  'CalibrationElement'    :  CalibrationElement,
#  'DescriptionLength'     :  DescriptionLength,  
#  'Descritpion'           :  Descritpion,        
#  'UnitsLength'           :  UnitsLength,        
#  'Units'                 :  Units,              
#  'end_position'          :  end
#  }
#
#  return Dim_array
#
  
#def read_data(header_data,offset):
#  CalibrationOffsetX,  \
#  CalibrationDeltaX,   \
#  CalibrationElementX, \
#  CalibrationOffsetY,  \
#  CalibrationDeltaY,   \
#  CalibrationElementY, \
#  DataType,            \
#  ArraySizeX,          \
#  ArraySizeY           \
#  =          struct.unpack("<ddiddihii", header_data[offset:offset+50])
#
#  #print_hex(header_data[offset+0:offset+8])
#  #print_hex(header_data[offset+8:offset+16])
#
#  #print_hex(header_data[offset+20:offset+28])
#  #print_hex(header_data[offset+28:offset+36])
#
#  data_header={
#  'CalibrationOffsetX'    : CalibrationOffsetX,  \
#  'CalibrationDeltaX'     : CalibrationDeltaX,   \
#  'CalibrationElementX'   : CalibrationElementX, \
#  'CalibrationOffsetY'    : CalibrationOffsetY,  \
#  'CalibrationDeltaY'     : CalibrationDeltaY,   \
#  'CalibrationElementY'   : CalibrationElementY, \
#  'DataType'              : DataType,            \
#  'ArraySizeX'            : ArraySizeX,          \
#  'ArraySizeY'            : ArraySizeY           \
#  }
#  print_yaml( data_header)
#  return data_header
#
#def get_datatype(typenumber):
#  typechart={
#        1  : '1 - Unsigned 1-byte integer' ,
#        2  : '2 - Unsigned 2-byte integer' ,
#        3  : '3 - Unsigned 4-byte integer' ,
#        4  : '4 - Signed 1-byte integer	 ' ,
#        5  : '5 - Signed 2-byte integer	 ' ,
#        6  : '6 - Signed 4-byte integer	 ' ,
#        7  : '7 - 4-byte float	         ' ,
#        8  : '8 - 8-byte float	         ' ,
#        9  : '9 - 8-byte complex	       ' ,
#        10 : '10 - 16-byte complex       ' 
#  }  
#  sizechart={
#        1  : 1        ,   #1 - Unsigned 1-byte integer	
#        2  : 2        ,   #2 - Unsigned 2-byte integer	
#        3  : 4        ,   #3 - Unsigned 4-byte integer	
#        4  : 1        ,   #4 - Signed 1-byte integer	
#        5  : 2        ,   #5 - Signed 2-byte integer	
#        6  : 4        ,   #6 - Signed 4-byte integer	
#        7  : 4        ,   #7 - 4-byte float	
#        8  : 8        ,   #8 - 8-byte float	
#        9  : 8        ,   #9 - 8-byte complex	
#        10 : 16           #10 - 16-byte complex
#  }
#  fmtchart={
#        1  : 'B'       ,    #1 - Unsigned 1-byte integer	
#        2  : 'H'       ,    #2 - Unsigned 2-byte integer	
#        3  : 'I'       ,    #3 - Unsigned 4-byte integer	
#        4  : 'b'       ,    #4 - Signed 1-byte integer	
#        5  : 'h'       ,    #5 - Signed 2-byte integer	
#        6  : 'i'       ,    #6 - Signed 4-byte integer	
#        7  : 'f'       ,    #7 - 4-byte float	
#        8  : 'd'       ,    #8 - 8-byte float	
#        9  : 'ff'      ,     #9 - 8-byte complex	
#        10 : 'dd'           #10 - 16-byte complex
#  }
#  return typechart[typenumber],sizechart[typenumber],fmtchart[typenumber]
#
#
def process_emi_file(filename,args):
      f=open(filename,'rb')
      file_size=os.path.getsize(filename)
      print("File size: {} bytes".format(file_size))
      base=os.path.splitext(filename)[0]
      parts=re.search('^(.+)(_\d)$',base)
      if(parts and parts.group(2)):
        base=parts.group(1)
        #print(parts.group(0),parts.group(1),parts.group(2),base)
      base_ns=re.sub(r' ',r'_',base)
      emi_file= base_ns +'.emi'
      XML_file= base_ns +'.xml'
      YAML_file= base_ns +'.yaml'

      try:
          f.seek(0)
          raw = f.read(file_size)
          if raw:
              xmllist,data=read_EMI_header(raw,args) #data is int32
              xmltext=xmllist[0]
              if(args.v):print(xmltext)
              xml_dict=parse_xml(xmltext)
              
              trueheaderinfo=parse_xml(xml_dict['ObjectInfo']['TrueImageHeaderInfo'])
              #print_safe_yaml(trueheaderinfo)
              x=open(XML_file,'wb')
              x.write(xmltext)
              x.close()

              common.save_safe_yaml(xml_dict,YAML_file)



              if(args.clipneg):
                clipmin=0
                tmptype=data.dtype
                data_clip=np.clip(data, 0,None)
                data=data_clip.astype(tmptype, order='K', casting='unsafe', subok=True, copy=True)


              amax=data.max()
              amin=data.min()
              amean=data.mean()
              arms=data.std()

              #xml_dict=read_TIA_EMI_XML(filename,raw[header_inf['DataOffset']+50:header_inf['DataOffset']+50+datasize],ysize,xsize)
              (apix,magnification,defocus,kV,C2,nP,spot,DwellTimePath)=print_xml_data(xml_dict)
              smin=''
 #             if(amin<0):
 #               smin='neg'
              infstr='.{:d}KX_{:3.2f}s_{:3.2f}um_{:d}kV_{}{}_int{:3.1f}_x{:d}_a{:d}_i{}{:d}_r{:3.1f}'.format(int(magnification/1000),DwellTimePath,defocus,kV,nP,spot,C2,int(amax),int(amean),smin,int(amin),arms)
              ysize=int(xml_dict['ObjectInfo']['DetectorPixelHeight'])
              xsize=int(xml_dict['ObjectInfo']['DetectorPixelWidth'])
              extheader=''
              if(args.xml):
                extheader=xmltext
              from mrc import save_tif_mrc
              
              
              
              
              save_tif_mrc(data,args,base_ns,infstr,extheader,amax,amin,amean,arms,ysize,xsize,apix) #this will save tif or mrc based on args.mrc and args.tif
              
              print()

      finally:
          f.close()  


############################main##################
def main():
    import argparse
    parser = argparse.ArgumentParser(description='Dump Tecnai Image Aquisition(TIA) .emi files to TIFF and/or MRC files.\n The embeded XML will be dumped too.\n')
    parser.add_argument("-tif",action='store_true',default=False, help="Output .tif file containing the original data.")
    parser.add_argument("-mrc",action='store_true',default=False, help="Output .mrc file containing the original data. If the data is int and the max value is less than 65536/2, save in int16. Otherwise float32.")
    parser.add_argument("-invmrc",action='store_true',default=False, help="invert contrast in the resulting MRC file. Same as the --multi=-1 option in exproc2d.py. TIFF files are not affected.")
    parser.add_argument("-invtif8",action='store_true',default=False, help="invert contrast in the resulting 8bit TIFF file. ")
    parser.add_argument("emi_files",metavar='.emi files',nargs='+',type=str, help="The .ser files to process.")
    parser.add_argument("-v",action='store_true',default=False, help="Verbose, print decoding information.")
    parser.add_argument("-xml",action='store_true',default=False, help="add the xml to MRC files as extended header. Some programs may not handle it properly.")
    parser.add_argument("-tif8",action='store_true',default=False, help="save a scaled 8bit TIFF file for visualization. ") #this one is not really used in this program

    parser.add_argument("-tif2mrc",action='store_true',default=False, help="convert tif to MRC, not implemented here. User mrc.py for this.")
    parser.add_argument("--Apix", help="Apix. No effect for EMI.py.",nargs='?', default=1.00, type=float, metavar="N")
    parser.add_argument("--bin", help="Binning factor for uint8.tif, needs to be positive integer", type=int,default=2, metavar="N")
    parser.add_argument("--sigma", help="rescale tiff8 image by sigma",                        type=float, metavar="N")
    parser.add_argument("-clipneg",action='store_true',default=False, help="remove negative values from data (so that GCTF won't have trouble)")
    parser.add_argument("--sigmaclip", help="clip original data by sigma value, must use -modify", type=float, metavar="N")                         

    args=parser.parse_args()
    
    
    for filename in args.emi_files:
      process_emi_file(filename,args)
      print("=========================\n\n")
    
#####################3
if __name__ == '__main__':
  main()
