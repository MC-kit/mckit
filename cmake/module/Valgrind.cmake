# Modern CMake for C++, p.320
function(AddValgrind target)
    find_program(VALGRIND_PATH valgrind)
    if (VALGRIND_PATH)
        add_custom_target(valgrind
            COMMAND ${VALGRIND_PATH} --leak-check=yes
            $<TARGET_FILE:${target}>
            WORKING_DIRECTORY ${CMAKE_BINARY_DIR}
        )
    else()
        message(WARNING "valgrind not found")
    endif()
endfunction()