function(AddClangTidy target)
  find_program(CLANG_TIDY_PATH clang-tidy)
  if(CLANG_TIDY_PATH)
    set_target_properties(
      ${target}
      PROPERTIES CXX_CLANG_TIDY "${CLANG_TIDY_PATH}"
                 # "${CLANG_TIDY_PATH};-checks=*;--warnings-as-errors=*"
    )
  else()
    message(WARNING "clang-tidy not found")
  endif()
endfunction()
