#include <iostream>
#include "box.h"
using namespace std;

// template<typename T=double, int D=NDIM>
// ostream& operator <<(ostream& os, const std::array[T, D] & a)
// {
//     return os << '[' < a[0] << ',' << a[1] << ',' << a[2] << ']';
// }
int main()
{
    const double center[NDIM] {0,0,0};
    const double ex[NDIM] {1, 0, 0};    
    const double ey[NDIM] {0, 1, 0};    
    const double ez[NDIM] {0, 0, 1};
    const double wx {2.0};
    const double wy {2.0};
    const double wz {2.0};    
    Box b;
    box_init(&b,center, ex, ey, ez, wx, wy, wz);
    cout << "Box volume:" << b.volume;
}