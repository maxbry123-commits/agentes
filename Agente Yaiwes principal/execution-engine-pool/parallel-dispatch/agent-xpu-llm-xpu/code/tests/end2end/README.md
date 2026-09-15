# Test End-to-End Correctness

The legacy Python golden-output generator has been removed. End-to-end
correctness tests should use prepared fixtures and run through the C++ test
targets only.

**Note**: The relative absolute error of floating-point number comparison is set to `3e-2`, since OpenMP may change the order of floating-point operations which are not necessarily associative. 
