# Injected into Gearmulator's top-level project via CMAKE_PROJECT_gearmulator_INCLUDE,
# so our tools build against its libraries without modifying the checkout.
# virusLib is defined later in the configure, which is fine: link targets resolve at generate time.
add_subdirectory(${CMAKE_CURRENT_LIST_DIR}/virusRender ${CMAKE_BINARY_DIR}/virusRender)
