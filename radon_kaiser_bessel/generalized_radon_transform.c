//This is a matrix form of the Radon Transform. Input lives in B-spline space (sample/image is expanded in Riesz basis),
//output is represented in 'canonical' basis in Radon space (i.e pixel basis, hence the sinogram can be made visible directly)
//compile
//gcc -O3 -fPIC -c generalized_radon_transform.c -o generalized_radon_transform.o
//make shared object
//gcc -shared -Wl -o generalized_radon_transform.so  generalized_radon_transform.o
//
// Remember:
// lut_size     --->   is supposed to be even
// half_pixel   --->   it may be set to 0.5, but for npix even, 0 is better



#include <math.h>
#include <stdio.h>

int radon( float *result , float *input , int do_adjoint , float *lut , int lut_size , int npix , float *angles , int nang , float support_bspline)
{
    const float lut_step = ( lut_size * 0.5 ) / ( support_bspline * 0.5 );
    const int lut_max_index = lut_size - 1;
    const int lut_half_size = lut_size/2; 
    const double half_pixel = 0.0; 
    const double middle_right_det = 0.5 * npix + half_pixel; 
    const double middle_left_det  = 0.5 * npix - half_pixel; 
    const int delta_s_plus = (int)( 0.5 * support_bspline + 0.5 );
    
    float theta , COS , SIN , kx , ky , proj_shift , y , lut_arg_y;
    int theta_index , kx_index , ky_index , s , y_index, lut_arg_index;


    for( theta_index = 0 ; theta_index < nang ; theta_index++ )
    {
        theta = angles[theta_index];
        COS = cos(theta);
        SIN = sin(theta);
        
        for( ky_index = 0 ; ky_index < npix ; ky_index++ )
        {
            ky = -ky_index + middle_left_det;
            
            for ( kx_index = 0 ; kx_index < npix ; kx_index++ )
            {
                kx = kx_index - middle_left_det;
                proj_shift = COS * kx + SIN * ky;
                int image_index = ky_index * npix + kx_index;
                
                for ( s = -delta_s_plus ; s <= delta_s_plus ; s++ )
                {
                    y_index = (int)( proj_shift + s + middle_right_det );
                    
                    if (y_index >= npix || y_index < 0) continue;
            
                    y = y_index - middle_left_det;

                    lut_arg_y = y - proj_shift;
                    lut_arg_index = (int)( lut_arg_y * lut_step + half_pixel ) + lut_half_size;

                    if (lut_arg_index >= lut_max_index || lut_arg_index < 0) continue;

                    int sino_index = theta_index * npix + y_index;
                    int lut_arg_index_c = theta_index * lut_size + lut_arg_index;

                    if (do_adjoint)
                    	result[image_index] += input[sino_index] * lut[lut_arg_index_c];
                    else
                    	result[sino_index] += input[image_index] * lut[lut_arg_index_c];
                }
            }
        }
    }
    return 0;
}

