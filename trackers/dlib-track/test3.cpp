#include <ctime>
#include <fstream>
#include <iostream>
#include <raspicam/raspicam.h>

#include <dlib/image_processing.h>
#include <dlib/image_transforms.h>
#include <dlib/gui_widgets.h>
#include <dlib/image_io.h>
#include <dlib/dir_nav.h>
#include <dlib/pixel.h>


using namespace dlib;
using namespace std;
using namespace raspicam;

// convert from raspicam to dlib image format, thanks mgoodings!
//void fillImageFromDataRGB( T& t_, unsigned int width, unsigned int height, unsigned char* data ) {
//  image_view< T > t( t_ );
//  t.set_size( height, width );
//  unsigned int k = 0;
//  for(unsigned int y=0;y<height;y++){
//    for(unsigned int x=0; x<width;x++){
//        rgb_pixel p;
//       p.red  = (int)data[k++];
//       p.green  = (int)data[k++];
//       p.blue  = (int)data[k++];
//        assign_pixel( t[ y ][ x ], p );
//      }
//  }
//}

template< typename T >
void fillImageFromData( T& t_, unsigned int width, unsigned int height, unsigned char* data ) {
  image_view< T > t( t_ );
  t.set_size( height, width );
  unsigned int k = 0;
  for(unsigned int y=0;y<height;y++){
    for(unsigned int x=0; x<width;x++){
        t[ y ][ x ] = data[k++];
      }
  }
}

int main(int argc, char** argv) try
{

    if (argc != 8)
    {
        cout << "Call this program like this: " << endl;
        cout << "./tracker tlx tly brx bry capture_width capture_height firstframe.jpg" << endl;
        return 1;
    }

    RaspiCam Camera;
    unsigned int width = atoi(argv[5]);
    unsigned int height = atoi(argv[6]);
    Camera.setWidth( width );
    Camera.setHeight( height );
    RASPICAM_FORMAT fmt = RASPICAM_FORMAT_GRAY; //RASPICAM_FORMAT_RGB;
    Camera.setFormat( fmt );
    if (!Camera.open()) {cerr<<"Error opening the camera"<<endl;return -1;}
    cout << "camera opened" << endl;
    usleep(40000);

    // grab our sill image from the first photo shoot, this is what we start tracking from.
    // todo: read this image from raspicam instead of the external raspistill script so we get the same first frame image output as tracker will continue to receive
    array2d<unsigned char> still_frame;
    array2d<unsigned char> still_frame_resized;
    cout << "loading still frame" << endl;
    load_image(still_frame, argv[7]);
    set_image_size(still_frame_resized, height, width);
    cout << "resizing still" << endl;
    resize_image(still_frame, still_frame_resized);
    save_jpeg(still_frame_resized, "/var/www/html/images/still3.jpg");
    cout << "saved resized still to /var/www/html/images/still3.jpg" << endl;

    correlation_tracker tracker;
    long tl1 = atol(argv[1]);
    long tl2 = atol(argv[2]);
    long br1 = atol(argv[3]);
    long br2 = atol(argv[4]);
    cout << "tracking points: " << argv[1] << argv[2] << argv[3] << argv[4] << endl;
    // Start object tracking on the defined keypoints.
//    rectangle rect;
//    rect.set_left(tl1);
//    rect.set_top(tl2);
//    rect.set_right(br1);
//    rect.set_bottom(br2);
    rectangle rect(point(tl1, tl2), point(br1, br2));
    tracker.start_track(still_frame_resized, rect);
//    tracker.start_track(still_frame_resized, centered_rect(point(93,110), 58, 86));
    //tracker.start_track(still_frame_resized, rectangle( tl1, tl2, br1, br2));


    // store our raspicam captured image in data:
    unsigned char *data=new unsigned char[  Camera.getImageTypeSize ( fmt ) ];
    cout<<"data size: "<< Camera.getImageTypeSize ( fmt ) << endl;
    // conver our raspicam image into array2d for dlib processing
    array2d<unsigned char> img;

    // Now run the tracker.  All we have to do is call tracker.update() and it will keep
    // track of the juice box!
    image_window win;

    win.set_image(still_frame_resized);
    win.clear_overlay();
    cout << "hit enter to start tracker" << endl;
    cin.get();

    while( true )
    {

        // grab our frame from the Pi camera
        Camera.grab();
        Camera.retrieve ( data, fmt );
        fillImageFromData( img, Camera.getWidth(), Camera.getHeight(), data );

        tracker.update(img);

        win.set_image(img);
        win.clear_overlay();
        win.add_overlay(tracker.get_position());

        cout << "hit enter to process next frame" << endl;
        cin.get();
    }
    delete data;
}
catch (std::exception& e)
{
    cout << e.what() << endl;
}

