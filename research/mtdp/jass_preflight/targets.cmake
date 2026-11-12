add_executable(mtdp_jass_preflight
    "${CMAKE_CURRENT_LIST_DIR}/preflight.cpp"
    $<TARGET_OBJECTS:jass_t3_f6_runtime>)
target_compile_features(mtdp_jass_preflight PRIVATE cxx_std_20)
target_link_libraries(mtdp_jass_preflight PRIVATE jass_lib jass_warnings)

# This target needs the experiment patch against the pinned Jass checkout.
if(MTDP_JASS_INITIAL_ONLY)
    target_compile_definitions(mtdp_jass_preflight PRIVATE MTDP_JASS_INITIAL_ONLY)
endif()

add_executable(mtdp_jass_legal_catalogue "${CMAKE_CURRENT_LIST_DIR}/legal_catalogue.cpp")
target_compile_features(mtdp_jass_legal_catalogue PRIVATE cxx_std_20)
target_link_libraries(mtdp_jass_legal_catalogue PRIVATE jass_lib jass_warnings)

add_executable(mtdp_jass_benchmark
    "${CMAKE_CURRENT_LIST_DIR}/../jass_benchmark/runner.cpp"
    $<TARGET_OBJECTS:jass_t3_f6_runtime>)
target_compile_features(mtdp_jass_benchmark PRIVATE cxx_std_20)
target_link_libraries(mtdp_jass_benchmark PRIVATE jass_lib jass_warnings)

if(MTDP_JASS_INITIAL_ONLY)
    target_compile_definitions(mtdp_jass_benchmark PRIVATE MTDP_JASS_INITIAL_ONLY)
endif()
