#################################################################################
#################################################################################
#################################################################################
#######                                                                   #######
#######                          RADON TRANSFORM                          #######
#######                                                                   #######
#######        Author: Filippo Arcadu, arcusfil@gmail.com, 01/03/2013     #######
#######                                                                   #######
#################################################################################
#################################################################################
#################################################################################




####  PYTHON MODULES
from __future__ import division,print_function
import time
import datetime
import argparse
import sys
import os
import numpy as np
import scipy as sci
import scipy.interpolate as scint
from scipy import misc




####  MY PYTHON MODULES
import myImageIO as io
import myImageDisplay as dis
import myImageProcess as proc

import filters as fil
import bspline_functions as bfun
import class_projectors_bspline as cpb  




####  MY FORMAT VARIABLES
myfloat = np.float32




####  CONSTANTS
eps = 1e-8




##########################################################
##########################################################
####                                                  ####
####             GET INPUT ARGUMENTS                  ####
####                                                  ####
##########################################################
##########################################################

def getArgs():
    parser = argparse.ArgumentParser(description='Inverse Radon Transform B-Splines -- FBP',
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    
    parser.add_argument('-Di', '--pathin', dest='pathin', default='./',
                        help='Specify path to input data')    
    
    parser.add_argument('-i', '--sino', dest='sino',
                        help='Specify name of input reco')
    
    parser.add_argument('-Do', '--pathout', dest='pathout',
                        help='Specify path to output data') 
    
    parser.add_argument('-o', '--reco', dest='reco',
                        help='Specify name of output reconstruction')
    
    parser.add_argument('-n', '--nang', dest='nang', type=int, default=180,
                        help='Select the number of projection angles ( default: 180 projections )') 
    
    parser.add_argument('-g', '--geometry', dest='geometry',default='0',
                        help='Specify projection geometry; @@@@@@@@@@@@@@@@@@@@@@@'
                             +' -g 0 --> equiangular projections between 0 and 180 degrees (default);'
                             +' @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@'
                             +' -g angles.txt use a list of angles (in degrees) saved in a text file')
    
    parser.add_argument('-c',dest='ctr', type=myfloat,
                        help='Specify the center of rotation ( default = the middle pixel of the image )') 
    
    parser.add_argument('-e',dest='edge_padding', action='store_true',
                        help='Enable edge padding for local tomography') 

    parser.add_argument('-f',dest='filt', default='ram-lak',
                        help='Select interpolation scheme: \
                              ram-lak , shepp-logan , cosine , hamming , '
                              + ' hanning , none, convolv')

    parser.add_argument('-dpc',dest='dpc', action='store_true',
                        help='Enable DPC reconstruction')  
    
    parser.add_argument('-w',dest='bspline_degree', type=int , default=3,
                        help='Select B-Spline degree')

    parser.add_argument('-z',dest='lut_size', type=int , default=2048,
                        help='Select size of the B-spline look-up-table')  

    parser.add_argument('-p',dest='plot', action='store_true',
                        help='Display check-plots during the run of the code')


    args = parser.parse_args()
    

    ##  Exit of the program in case the compulsory arguments, 
    ##  are not specified
    if args.sino is None:
        parser.print_help()
        print('ERROR: Input sino name not specified!')
        sys.exit()  
    
    
    return args




##########################################################
##########################################################
####                                                  ####
####                        IRADON                    ####
####                                                  ####
##########################################################
########################################################## 

def fbp_bspline( sino , angles , ctr , filt , lut ,  proj_support_y ,
                 bspline_degree , rd , plot ):
    
    ##  Initialize backprojector
    n = sino.shape[1];  a = angles.copy()
    tp = cpb.projectors( n , a ,  bspline_degree=3 , proj_support_y=4 , 
                          radon_degree=rd , filt=filt , plot=plot )



    ##  Get number of angles
    nang , npix = sino.shape
    pp = np.array( [ lut.shape[1] , proj_support_y ] , dtype=myfloat )



    ##  Pre-calculate sin and cos values
    cos = np.cos( angles )
    sin = np.sin( angles )


    
    ##  Create grid of coordinates for the reconstruction
    x = np.arange( - ( npix * 0.5  - 1 ) , npix * 0.5 + 1 )
    x = np.kron( np.ones( ( npix , 1 ) ) , x ) 
    y = np.rot90( x )


    
    ##  Filtered Backprojection
    sino = sino.astype( myfloat )
    lut = lut.astype( myfloat )
    angles = angles.astype( myfloat )

    time1 = time.time()
    reco = tp.fbp( sino ) 
    time2 = time.time() 

    reco *= np.pi / ( 2.0 *nang )

    reco[:,:] = bfun.convert_from_bspline_to_pixel_basis( reco , bspline_degree )       
        
    
    return reco 




##########################################################
##########################################################
####                                                  ####
####                    SAVE SINOGRAM                 ####
####                                                  ####
##########################################################
##########################################################

def saveReco( reco , args ):
    if args.pathout is None:
        pathout = args.pathin
    else:
        pathout = args.pathout
    
    if args.reco is None:
        filename = args.sino
        filename = filename[:len(filename)-4]
        filename += '_ang' + str( args.nang ) + '_fbp_bspline' + \
                    str( args.bspline_degree ) + \
                    '_' + args.filt + '_rec.DMP'
        filename = pathout + filename
    else:
        filename = pathout + args.reco

    io.writeImage( filename , reco )




##########################################################
##########################################################
####                                                  ####
####                       MAIN                       ####
####                                                  ####
##########################################################
##########################################################

def main():
    ##  Initial print
    print('\n')
    print('#######################################')
    print('#############    PY-FBP   #############')
    print('#######################################')
    print('\n')


    ##  Get the startimg time of the reconstruction
    startTime = time.time()



    ##  Get input arguments
    args = getArgs()



    ##  Get path to input reco
    pathin = args.pathin



    ##  Get input reco
    ##  You assume the reco to be square
    sino_name = pathin + args.sino
    sino = io.readImage( sino_name )
    npix = sino.shape[1]
    nang = sino.shape[0]

    print('\nInput sino:\n', sino_name)
    print('Number of projection angles: ', nang)
    print('Number of pixels: ', npix)



    ##  Show reco
    if args.plot is True:
        dis.plot( sino , 'Sinogram' )



    ##  Get projection geometry  
    if args.geometry == '0':
        angles = np.arange( nang )
        angles = ( angles * 180.0 )/myfloat( nang )
        print('\nDealing with equally angularly spaced projections in [0,180)')

    else:
        geometryfile = pathin + args.geometry
        angles = np.fromfile( geometryfile , sep="\t" )
        nang = len( angles )
        print('\nReading list of projection angles: ', geometryfile)

    print('Number of projection angles: ', nang)



    ##  Get center of rotation
    print('\nCenter of rotation placed at pixel: ', args.ctr) 

    if args.ctr is None:
        ctr = npix * 0.5 + 1
    else:
        ctr = args.ctr  
        sino = proc.sinoRotAxisCorrect( sino , ctr )
        ctr = npix * 0.5 + 1




    ##  Enable edge padding
    if args.edge_padding is True:
        npix_old = sino.shape[1]
        sino = proc.edgePadding( sino , 0.5 )
        npix = sino.shape[1]
        i1 = int( ( npix - npix_old ) * 0.5 )
        i2 = i1 + npix_old      
        ctr += i1

    

    ##  Get filter type
    filt = args.filt
    if filt == 'ram-lak':
        print('\nSelected filter: RAM-LAK')
    elif filt == 'shepp-logan':
        print('\nSelected filter: SHEPP-LOGAN')
    elif filt == 'cosine':
        print('\nSelected filter: COSINE')
    elif filt == 'hamming':
        print('\nSelected filter: HAMMING')
    elif filt == 'hanning':
        print('\nSelected filter: HANNING')
    elif filt == 'none':
        print('\nSelected filter: NONE')
    elif filt == 'convolve':
        print('\nSelected filter: CONVOLUTION with IFT of RAM-LAK') 
    else:
        print('\nWARNING: ', filt,' does not correspond to any available \
                 filter; RAM-LAK is automatically chosen')
        filt = 'ram-lak' 



    ##  Get B-Spline setting
    bspline_degree = args.bspline_degree
    nsamples_y = args.lut_size
    proj_support_y = bspline_degree + 1

    if args.dpc is False:
        rt_degree = 0
    else:
        rt_degree = 1

    print('\nB-Spline degree selected: ', bspline_degree)
    print('LUT density: ', nsamples_y)
    print('B-Spline support: ', proj_support_y)
    print('Radon transform degree: ', rt_degree)
    print('\nAngles:\n' , angles )



    ##  Precalculate look-up-table for B-spline
    lut = bfun.init_lut_bspline( nsamples_y , angles , bspline_degree ,
                                 rt_degree , proj_support_y )

    

    ##  Compute iradon transform
    print('\nPerforming Filtered Backprojection ....\n')
    reco = fbp_bspline( sino , angles , ctr , filt , lut ,
                        proj_support_y , bspline_degree , 
                        rt_degree , args.plot )



    ##  Remove edge padding
    if args.edge_padding is True:
        reco = reco[i1:i2,i1:i2]     

    

    ##  Show sino     
    if args.plot is True:
        dis.plot( reco , 'Reconstruction' )



    ##  Save sino
    saveReco( reco , args )

    

    ##  Time elapsed for the computation of the radon transform
    endTime = time.time()
    print('\n\nTime elapsed: ', (endTime-startTime)/60.0)
    print('\n')




##########################################################
##########################################################
####                                                  ####
####                    CALL TO MAIN                  ####
####                                                  ####
##########################################################
##########################################################    

if __name__ == '__main__':
    main()
