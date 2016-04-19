#
# This is a CMake makefile.  You can find the cmake utility and
# information about it at http://www.cmake.org
#


cmake_minimum_required(VERSION 2.8.4)

SET(CMAKE_PREFIX_PATH /usr/local/lib/cmake/ CACHE PATH "libs")
PROJECT(examples)

find_package(raspicam REQUIRED)

include(dlib/cmake)

#ADD_EXECUTABLE(test test.cpp)
#TARGET_LINK_LIBRARIES(test dlib )

#ADD_EXECUTABLE(test2 test2.cpp)
#TARGET_LINK_LIBRARIES(test2 dlib )

ADD_EXECUTABLE(test3 test3.cpp)
TARGET_LINK_LIBRARIES(test3 dlib ${raspicam_LIBS})




