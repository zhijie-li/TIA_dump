# TIA_dump
dump data from FEI TIA .SER .EMI files
TIA .SER file format interpretation is based on 
http://www3.ntu.edu.sg/home/cbb/info/TIAformat/TIAseriesformat.pdf 
and 
http://www3.ntu.edu.sg/home/cbb/info/TIAformat/index.html



.EMI format:

TIA .EMI file format is not disclosed by FEI. However it contains a exact same copy of the data block as that found in the .ser file. In front of the datablock, 1 byte carries the datatype '06'
12 bytes code 3 x int4 numbers:
*signed* int4 [datablocksize+8]=x*y*4+8 ( *signed because -2 has been observed in an image with max=2500*)
int4 [x] (pixels width, probably signed too)
int4 [y] (pixels height)



On a CCD camera, the recorded readings normally are well below 65535(16 bit). The saturation value can also be found in the EMI file as a int4 number(see below). As the data array is saved as *signed* int4 (*see above*), for almost all numbers the two upper bytes are always 00 00. Only in rare cases, when negative nubmers are recorded the upper two bytes are non-zero (for example, -2 would be 'fe ff ff ff'). This should also help validating the datablock.






Datatype tags (my guesses)

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





[begining of file]
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

1x int 1 =6 ####datatype =6 meaning 4-byte int signed
4B '08220202'unknown
12B 3xint4 datasize+8bytes width hight
<dataarray>

[calibration offsets and deltas]

following the dataarray (x * y int4 numbers), there are 4 unknow bytes: 02 41 00 03, this is likely the node (C struct header) for the calibration values, which are two groups of 3 number each (f8 f8 i4 f8 f8 i4)
Each of the 6 numbers follow a 4-byte node:
[00] datatype (int1), , '41'=float8, '31'=int4
[01] '00'
[02] '??' unknown 
[03] '??' unkown
This node ends with two bytes '00 00'


[the XML]
The XML block contains some interesting microscope settings. This can be easily found by looking for the <ObjectInfo></ObjectInfo> pairs. Two bytes, '0D 0A', follow the </ObjectInfo> tag.

The XML block is found immediately after the filename string.

The node starts with '32 00 42 04', then '02 00'. The XML is saved as a '60 00' -string.


[end of file]
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
=	'00 00'
	(now -157 from end)
	1x '70 00'
	1x int2	'30 00 20 07'	'02 00'
	1x int2 '30 00 21 07'	'00 00'

	1x '70 00'
	1x '41 00' ('00 00 00 00 00 00 F0 3F=1.0) 
	1x '70 00'

	1x int4 	'31 00 36 07'		'0F 00 00 00'  int4=15

=	'00 00'

	1x int4 	'31 00 04 08'		'01 00 00 00'
	3x '70 00'
	1x '60 00' 'Real Space'
	'86 42 02 0A' 
	'30 00 00 01'	'03 00'
=	'00 00'
	'82 42 04 0A'
	'60 00' 'Electrons'
	'41 00 10 01' float=1.0
=	'00 00'
2x '70 00'
=	'00 00'
'03 4D 00 08 00 00 00 00'
