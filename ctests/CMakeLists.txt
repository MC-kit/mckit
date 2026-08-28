
add_executable(test_box main.cpp)
target_link_libraries(test_box geometry_objs)
add_test(NAME test_box COMMAND test_box)