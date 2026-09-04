# Modern CMake for C++, p311
function(Format target directory)
    find_program(CLANG_FORMAT_PATH clang-format)
    if (CLANG_FORMAT_PATH)
        set(EXPRESSION h hpp hh c cc cxx cpp)
        list(TRANSFORM EXPRESSION PREPEND "${directory}/*.")
        file(GLOB_RECURSE SOURCE_FILES FOLLOW_SYMLINKS
            LIST_DIRECTORIES false ${EXPRESSION}
        )
        add_custom_command(TARGET ${target} PRE_BUILD COMMAND
            ${CLANG_FORMAT_PATH} -i --style=file ${SOURCE_FILES}
        )
    else()
        message(WARNING "lang-format not found")
    endif()
endfunction()