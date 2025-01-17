import py
from rpython.translator import cdir
from rpython.translator.tool.cbuild import ExternalCompilationInfo
from rpython.rtyper.lltypesystem import lltype, llmemory, rffi
from rpython.rtyper.extregistry import ExtRegistryEntry
from rpython.rlib.objectmodel import not_rpython

# these functions manipulate directly the GIL, whose definition does not
# escape the C code itself
translator_c_dir = py.path.local(cdir)

eci = ExternalCompilationInfo(
    includes = ['src/thread.h'],
    separate_module_files = [translator_c_dir / 'src' / 'thread.c'],
    include_dirs = [translator_c_dir],
    post_include_bits = ['#define RPY_WITH_GIL'])

llexternal = rffi.llexternal

def _gil_allocate(): pass

def _gil_yield_thread(): pass

def _gil_release(): pass

def _gil_acquire(): pass

def gil_fetch_fastgil(): pass

# ____________________________________________________________


def invoke_after_thread_switch(callback):
    """Invoke callback() after a thread switch.

    This is a hook used by pypy.module.signal.  Several callbacks should
    be easy to support (but not right now).

    This function should be called from the translated RPython program
    (i.e. *not* at module level!), but registers the callback
    statically.  The exact point at which invoke_after_thread_switch()
    is called has no importance: the callback() will be called anyway.
    """
    print "NOTE: invoke_after_thread_switch() is meant to be translated "
    print "and not called directly.  Using some emulation."
    global _emulated_after_thread_switch
    _emulated_after_thread_switch = callback

_emulated_after_thread_switch = None

@not_rpython
def _after_thread_switch():
    if _emulated_after_thread_switch is not None:
        _emulated_after_thread_switch()


class Entry(ExtRegistryEntry):
    _about_ = invoke_after_thread_switch

    def compute_result_annotation(self, s_callback):
        assert s_callback.is_constant()
        callback = s_callback.const
        bk = self.bookkeeper
        translator = bk.annotator.translator
        if hasattr(translator, '_rgil_invoke_after_thread_switch'):
            assert translator._rgil_invoke_after_thread_switch == callback, (
                "not implemented yet: several invoke_after_thread_switch()")
        else:
            translator._rgil_invoke_after_thread_switch = callback
        bk.emulate_pbc_call("rgil.invoke_after_thread_switch", s_callback, [])

    def specialize_call(self, hop):
        # the actual call is not done here
        hop.exception_cannot_occur()

class Entry(ExtRegistryEntry):
    _about_ = _after_thread_switch

    def compute_result_annotation(self):
        # the call has been emulated already in invoke_after_thread_switch()
        pass

    def specialize_call(self, hop):
        translator = hop.rtyper.annotator.translator
        if hasattr(translator, '_rgil_invoke_after_thread_switch'):
            func = translator._rgil_invoke_after_thread_switch
            graph = translator._graphof(func)
            llfn = hop.rtyper.getcallable(graph)
            c_callback = hop.inputconst(lltype.typeOf(llfn), llfn)
            hop.exception_is_here()
            hop.genop("direct_call", [c_callback])
        else:
            hop.exception_cannot_occur()


def allocate():
    _gil_allocate()

def release():
    # this function must not raise, in such a way that the exception
    # transformer knows that it cannot raise!
    _gil_release()
release._gctransformer_hint_cannot_collect_ = True
release._dont_reach_me_in_del_ = True

def acquire():
    from rpython.rlib import rthread
    _gil_acquire()
    rthread.gc_thread_run()
    _after_thread_switch()
acquire._gctransformer_hint_cannot_collect_ = True
acquire._dont_reach_me_in_del_ = True

# The _gctransformer_hint_cannot_collect_ hack is needed for
# translations in which the *_external_call() functions are not inlined.
# They tell the gctransformer not to save and restore the local GC
# pointers in the shadow stack.  This is necessary because the GIL is
# not held after the call to gil.release() or before the call
# to gil.acquire().

def yield_thread():
    # explicitly release the gil, in a way that tries to give more
    # priority to other threads (as opposed to continuing to run in
    # the same thread).
    if _gil_yield_thread():
        from rpython.rlib import rthread
        rthread.gc_thread_run()
        _after_thread_switch()
yield_thread._gctransformer_hint_close_stack_ = True
yield_thread._dont_reach_me_in_del_ = True
yield_thread._dont_inline_ = True

# yield_thread() needs a different hint: _gctransformer_hint_close_stack_.
# The *_external_call() functions are themselves called only from the rffi
# module from a helper function that also has this hint.
