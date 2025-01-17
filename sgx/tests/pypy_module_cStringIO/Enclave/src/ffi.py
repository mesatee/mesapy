import sgx_cffi
import _cffi_backend as backend

ffi = sgx_cffi.FFI(backend)

ffi.embedding_api("void test_cStringIO();")
with open("enclave.py") as f:
    ffi.embedding_init_code(f.read())
ffi.set_source("ffi", "")
ffi.emit_c_code("ffi.c")
