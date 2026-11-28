# Keep the byte-pinned historical build recipe unchanged.
include("${CMAKE_CURRENT_LIST_DIR}/targets.cmake")

# Separate research-only typed-board successor oracle.
add_executable(mtdp_jass_successor_catalogue "${CMAKE_CURRENT_LIST_DIR}/successor_catalogue.cpp")
target_compile_features(mtdp_jass_successor_catalogue PRIVATE cxx_std_20)
target_link_libraries(mtdp_jass_successor_catalogue PRIVATE jass_lib jass_warnings)
