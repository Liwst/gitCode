#include "circle.h"

//ÉèÖÃ°ë¾¶
void Circle::set_R(int R) {
	m_R = R;
}
int Circle::get_R() {
	return m_R;
}
//ÉèÖÃÔ²ĞÄ
void Circle::set_center(Point center) {
	m_Center = center;

}
Point Circle::get_center() {
	return m_Center;
}
