# Turn off updates with FetchContent if offline
# see https://github.com/SpontanCombust/cmake-fetchcontent-offline

function(FetchContent_DisconnectedIfOffline)
    if(WIN32)
        execute_process(
            COMMAND ping www.google.com -n 2
            OUTPUT_QUIET
            ERROR_QUIET
            RESULT_VARIABLE NO_CONNECTION
        )
    else()
        execute_process(
            COMMAND ping www.google.com -c 2
            OUTPUT_QUIET
            ERROR_QUIET
            RESULT_VARIABLE NO_CONNECTION
        )
    endif()

    if(NO_CONNECTION EQUAL 0)
        set(FETCHCONTENT_FULLY_DISCONNECTED OFF PARENT_SCOPE)
        set(FETCHCONTENT_OFFLINE_MODE FALSE PARENT_SCOPE)
    else()
        set(FETCHCONTENT_FULLY_DISCONNECTED ON PARENT_SCOPE)
        set(FETCHCONTENT_OFFLINE_MODE TRUE PARENT_SCOPE)
        message(WARNING "FetchContent module is now in offline mode. Dependencies won't be downloaded or updated until the internet connection is regained.")
    endif()
endfunction()