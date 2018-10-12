from __future__ import print_function

import numpy as np


def save_tiff8(buff,desc_data,tif_name,amax,amin,ysize,xsize):
  '''
  save numpy ndarray as 8bit image
  will rescale from min to max
  '''
  try:
    from libtiff import TIFF
  except ImportError, e:
    print ("Need <libtiff> for saving TIFF files:\n  pip install libtiff  ")
    return

  data = np.asarray(buff,dtype=np.float32) 
  d0=data*255/(amax-amin)
  d1=d0.reshape(ysize,xsize)
  d2=d1.astype(np.uint8)
  #print("{} {} {}".format(d2[0][0], d2.shape,d2.dtype))
  tiff = TIFF.open(tif_name, mode='w')
  tiff.write_image(d2,compression='lzw')
  tiff.close()

def save_tiff16(buff,desc_data,tif_name,amax,amin,ysize,xsize):
  try:
    from libtiff import TIFF
  except ImportError, e:
    print ("Need <libtiff> for saving TIFF files:\n  pip install libtiff  ")
    return

  data = np.asarray(buff,dtype=np.float32) 
  d0=data*65535/(amax-amin)
  d1=d0.reshape(ysize,xsize)
  d2=d1.astype(np.uint16)
  #print("{} {} {}".format(d2[0][0], d2.shape,d2.dtype))
  tiff = TIFF.open(tif_name, mode='w')
  tiff.write_image(d2,compression='lzw')
  tiff.close()

def save_tiff16_no_rescaling(buff,desc_data,tif_name,amax,amin,ysize,xsize):
  try:
    from libtiff import TIFF
  except ImportError, e:
    print ("Need <libtiff> for saving TIFF files:\n  pip install libtiff  ")
    return

  data = np.asarray(buff,dtype=np.uint16) 
  d2=data.reshape(ysize,xsize)
  tiff = TIFF.open(tif_name, mode='w')
  tiff.write_image(d2,compression='lzw')
  tiff.close()

#####################
def save_PNG(outfile,buf,header_inf,bit,mode,rmscut=0):
    amean,arms,amin,amax,x,y,z=header_inf['amean'],header_inf['arms'],header_inf['amin'],header_inf['amax'],header_inf['c'],header_inf['r'],header_inf['s']
    
    if rmscut >0:
        cutoff=rmscut*arms #normally 6rms will cover >99.99% pixels
        print("Generating PNG using RMS cutoff = {} ".format(rmscut))
        zeropoint=amin if (amean-cutoff)<amin else (amean-cutoff) #use amin if 6 rms is smaller than amin
        maxpoint=amax if (amean+cutoff)>amax else (amean+cutoff) #same, to maximize constrast
    if rmscut <=0:
        print("Generating PNG with {} = 0 {} = 255".format(amin,amax))
        zeropoint=amin
        maxpoint=amax
    if zeropoint!=maxpoint:
        scale=255/(maxpoint-zeropoint)
    else: 
        scale=0
    


    buf1=''
    for p in buf:
        if p<=zeropoint:
           buf1+=(chr(0)) 
        elif p>=maxpoint:
           buf1+=(chr(255)) 
        else:
            buf1+=(chr (int (scale*(p-zeropoint))))
    
    imdata = png_data(buf1, x, y,bit,mode)
    with open(outfile, 'wb') as fd:        
        fd.write(imdata)        
        fd.close
#################
def png_data(buf, width, height,bit,mode):
    """ buf: must be bytes or a bytearray in Python3.x,
        a regular string in Python2.x.
    """
    import zlib, struct
    bpp=0 #byte per pixel
    if  mode == 0:
        bpp = 1 * bit / 8  #GrayScale
    if  mode == 6:
        bpp = 4 * bit / 8                                                                        #RGBA
    if  mode == 2:
        bpp = 3 * bit / 8                                                                        #RGB

    # reverse the vertical line order and add null bytes at the start
    width_byte = width *bpp 
    
    s=(height) * width_byte
    raw_data = b''.join(
        chr(0) + buf[span : span + width_byte]  for span in range(0,s-1, width_byte)
    )

    def png_pack(png_tag, data):
        chunk_head = png_tag + data
        return (struct.pack("!I", len(data)) +
                chunk_head +
                struct.pack("!I", 0xFFFFFFFF & zlib.crc32(chunk_head)))
    #tEXt_data=b''.join([chr(10),chr(10),'##################not-so-secret message########################',chr(10),chr(10),chr(0),msg,chr(10),chr(10),"##end of message##",chr(10)])
    
    
    return b''.join([
        chr(137),b'PNG',chr(13),chr(10),chr(26),chr(10),
        png_pack(b'IHDR', struct.pack("!2I5B", width, height, bit, mode, 0, 0, 0)), # bit 0 palette  bit 1 color bit 2 alpha: 00000111
        #png_pack(b'tEXt', tEXt_data),
        png_pack(b'IDAT', zlib.compress(raw_data, 9)),
        png_pack(b'IEND', b'')])

