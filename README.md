# TIA_dump

dump data from FEI TIA .SER .EMI files
TIA .SER file format interpretation is based on 
http://www3.ntu.edu.sg/home/cbb/info/TIAformat/TIAseriesformat.pdf 
and 
http://www3.ntu.edu.sg/home/cbb/info/TIAformat/index.html

A mrc file is going to be generated containing the original data, in int16 format(as CCD never needs >65536/2 levels). Two tif files are also generated, one containing the original data, one containing recaled uint8 data for viewing.
The original data will be multiplied by -1 (phase revsersal, same as "e2proc2d.py --multi=-1") so that it can be directly used in cryosparc.

If EMI file is found, the xml section will be extracted and saved as .xml file. An easier-to-read YAML will be generated too.

# .EMI format:

TIA .EMI file format is not disclosed by FEI. However it contains a exact same copy of the data block as that found in the .ser file. 

In front of the datablock, 1 byte carries the datatype '06', 12 bytes code 3 x int4 numbers:
```
   int4 [datablocksize+8]=x*y*4+8
   int4 [x] (pixels width)
   int4 [y] (pixels height)
```


On a CCD camera, the recorded readings normally are well below 65535(16 bit). The saturation value can also be found in the EMI file as a int4 number(see below). As the data array is saved as *signed* int4 (*because -2 has been encountered in image with max=2500*), for almost all numbers the two upper bytes are always 00 00. Only in rare cases, when negative nubmers are recorded the upper two bytes are non-zero (for example, -2 would be 'fe ff ff ff'). Converting to signed int16 should be safe but if converting to 16bit grayscale images such as TIFF16, remember to change the negative values to 0 (should have no real effect to the image because these values appear at most once per image).



## Datatype tags (my guesses)

```
   [type '70 00'] boolen. 4+1 bytes. 
   [type '20 00'] int1, 4+1 bytes
   [type '30 00'] int2, 4+2 bytes.
   [type '31 00'] int4, 4+4 bytes.
   [type '34 00'] int8, 4+8 bytes
   [type '41 00'] float8, 4+8 bytes.
   [type '60 00'] string. 8 + len(str) bytes. length saved as int4 at bytes 4-8.
   [type '30 41'] array of float8
   [type '32 41'] array of float8
   [type '20 43'] array of int4 (31)
   [type '2C 43'] array of int1
   ['00 00'] separater
```




## [begining of file]
```
   12B	'4A 4B 00 02 00 00 00 00 04 4D 01 00'
   28B	string 'hh.mm.ss CCD Acquire'
   19B string (version) 'a.bb.c.dddd'
   19B string (version) 'a.bb.c.dddd'
   24B 3x empty strings
   14B string 'Normal'
   10B 2x boolen
   8B 1x int4
   1x bool
   4B '34 43 02 07' unknown (2d array?)
   4B '2C 43 00 01' # array of int1
   15B 	3x'20 00' 5B each
   2B= '00 00'
   4B '2C 43 10 01' # array of int1
   15B 	3x'20 00' 5B each
   2B = '00 00'
   
   4B '02 21 40 01' unkown type
   4B 	int4 '0C 00 00 00' =12
   4B 	int4 '08 00 00 00' =8
   8B 	'FF'x8
   
   8B int4 =1
   8B int4 =3
   2B = '00 00'
   5B bool
   12B unkown '50 43 ...'
   12B f8 
   2B = '00 00'
   4B '20 43 00 07'
   32B	4x int4
   2B = '00 00'
   14B '56 44 10 07' unknown
   28B string 'Normal Image Display'
   10B 2x bool
   
   4B '2C 43 00 03'
   15B	3x 5B '20 00' int1
   2B = '00 00'
   
   4B '2C 43 02 03'
   15B	3x 5B '20 00' int1
   2B = '00 00'
   
   4B '2C 43 04 03'
   15B	3x 5B '20 00' int1
   2B = '00 00'
   
   8B int4 =0
   10B 2x bool
   2B ='00 00'
   4B '02 45 00 01' unknown
   
   14B 'Normal'
   10B 2xbool
   2B ='00 00'
   4B '-2 45 00 01'
   14B 'Normal'
   10B 2xbool
   8B 2x int4
   12B float8
   4B '42 43 06 04' array of array?
   4B '2C 43 00 01'
   15B	3x 5B '20 00' int1
   2B = '00 00'
   
   4B '40 43 00 02' array of something
   12B float8=1.0
   4B '2C 43'
   15B 3x int1 =255 (-1?)
   
   
   10B = '00'x10
   
   4B '40 45 10 06'
   34B 'Acquire Image Display'
   4B '20 43' arry of int4
   72B 9x int4
   
   	
   4B '32 41 04 06'
   60B 5xfloat8
   2B ='00 00'
   
   5B 1x bool
   
   
   28B 'Normal Image Display'
   
   10B 2xbool
   8B int4=0
   5B 1bool
   8B int4=0
   5B 1bool
   8B int4=2
   4B 'B0 49 10 06'
   20B 'Acquire CCD '
   5B 1bool
   4B '60 41 42 00' unknown
   1x bool
   3x int4 (=1, 25385 SaturationPoint,ffffffff) 
   1x bool
   4x int4 (=0,0,0,1)
   5x bool
   4x float8
   12B int8'34 00 22 01'
   24B 3x int4  (=1,MaxPossiblePixelValue,ffffffff)  
   2B ='00 00'
```
## [Image data]

The image blocks start with:
```
    2B '00 00'		   ending last segment
    4B '20 00 00 02'	   annoucing a int8
    1x int 1               datatype =6 means 4-byte int signed
    4B '08 22 02 02'       unknown, likely datablock node tag
    12B 3xint4             datasize+8bytes, width, hight
   
    <dataarray> of datasize bytes
```

Similarly, the FFT image blocks use the same layout:
``` 
    2B '00 00'		   ending last segment
    4B '20 00 00 02'	   annoucing a int8
    1x int 1               datatype =9 means 8-byte complex (float32x2)
    4B '14 22 02 02'       unknown, likely datablock node tag
    12B 3xint4             datasize+8bytes, width, hight
   
    <dataarray> of datasize bytes
```


## [calibration offsets and deltas]

Following the dataarray (x * y int4 numbers), there are 4 unknow bytes: '02 41 00 03', this is likely the node tag for the calibration data.

Example:
```
   040003fb:	<02 41 00 03>	!!!!!!!!unknown
   040003ff:	<41 00 00 01 79 09 16 44 60 da 9a be>	f8 [-4.00141349465e-07] #=2048*1.954
   0400040b:	<41 00 20 01 00 08 16 44 60 da ea 3d>	f8 [1.95381518293e-10]  #73KX, 14um pixel gives 1.92A per pixel, close enough.
   04000417:	<31 00 40 01 00 00 00 00>	i4 [0]
   0400041f:	<41 00 10 01 79 09 16 44 60 da 9a be>	f8 [-4.00141349465e-07]
   0400042b:	<41 00 30 01 00 08 16 44 60 da ea 3d>	f8 [1.95381518293e-10]
   04000437:	<31 00 50 01 00 00 00 00>	i4 [0]
   0400043f:	<00 00>	====
```
The Calibration deltas are the dimensions of single pixels in meter. 1e-10 meter= 1 Angstrom. 
Offsets are the center of the detector. These numbers should be delta*(-width/2) and delta*(-height/2). On a 4096x4096 detector such as Ceta, this will be delta*2048.


## [the XML]

The XML block is found immediately after the filename string. The node starts with '32 00 42 04', then '02 00'. The XML is saved as a '60 00' -string.

The XML block contains some interesting microscope settings. This can also be easily found by looking for the <ObjectInfo></ObjectInfo> pairs. 


A section in the XML is tagged 'TrueImageHeaderInfo'. When expanded, looks like this (nothing really useful):
```
  Data:
  - Index: '5'
    Value: '0'
  - Index: '6'
    Value: '0'
  - Index: '7'
    Value: '4'
  - Index: '8'
    Value: '9950328'  #instrument serial
  - Index: '9'
    Value: '120'      #KV
  - Index: '10'
    Value: '0'
  - Index: '11'
    Value: '0'
  - Index: '12'
    Value: '0'
  - Index: '13'
    Value: '0'
  - Index: '14'
    Value: '0'
  - Index: '15'
    Value: '-980.276524783974'   
  - Index: '17'
    Value: '0'
  - Index: '18'
    Value: '0'
  - Index: '19'
    Value: '0'
  - Index: '22'
    Value: '0'
  - Index: '23'
    Value: '0'
  - Index: '24'
    Value: '0'
  - Index: '25'
    Value: '0'
  - Index: '26'
    Value: '0'
  - Index: '27'
    Value: '0'
  - Index: '30'
    Value: '73000'   #magnification
  - Index: '31'
    Value: '0'
  - Index: '32'
    Value: '0'
  - Index: '33'
    Value: '1'
  - Index: '34'
    Value: '0'
  - Index: '35'
    Value: '3'
  - Index: '36'
    Value: '3'
  - Index: '37'
    Value: '0'
  - Index: '39'
    Value: '0'
  - Index: '40'
    Value: '0'
  - Index: '41'
    Value: '0'
  - Index: '42'
    Value: '0'
  - Index: '43'
    Value: '0'
  - Index: '44'
    Value: '0'
  - Index: '45'
    Value: '0.000049140135'
  - Index: '46'
    Value: '2.07470280000001E-05'
  - Index: '47'
    Value: '-0.00003084864'
  - Index: '48'
    Value: '-1.45330000000119E-04'
  - Index: '49'
    Value: '0'
  - Index: '54'
    Value: '0'
  - Index: '55'
    Value: '0'
  - Index: '56'
    Value: '0'
  - Index: '57'
    Value: '0'
  - Index: '58'
    Value: '0'
  - Index: '59'
    Value: '0'
  - Index: '60'
    Value: '0'
  - Index: '61'
    Value: '0'
```

## [end of file]
```
	string 'Normal' (14B)
	2x '70 00' (2x5B)
	1x int4	'31 00 06 05'	'01 00 00 00' 
	1x '70 00'
	'30 41 00 07'
	 	2x '41 00 ?? ??' float8  
	'00 00'

	3x '41 00 ?? ??' float 8 numbers (0.5, 1.0,1.0) 
	2x '70 00'
	'32 41 08 07' node
		5x float8(60bytes) (,,,,0.0)
	'00 00'
	(now -157 from end)
	1x '70 00'
	1x int2	'30 00 20 07'	'02 00'
	1x int2 '30 00 21 07'	'00 00'

	1x '70 00'
	1x '41 00' ('00 00 00 00 00 00 F0 3F=1.0) 
	1x '70 00'

	1x int4 	'31 00 36 07'		'0F 00 00 00'  int4=15

  '00 00'

	1x int4 	'31 00 04 08'		'01 00 00 00'
	3x '70 00'
	1x '60 00' 'Real Space'
	'86 42 02 0A' 
	'30 00 00 01'	'03 00'
  '00 00'
	'82 42 04 0A'
	'60 00' 'Electrons'
	'41 00 10 01' float=1.0
  '00 00'
2x '70 00'
  '00 00'
'03 4D 00 08 00 00 00 00'
```
