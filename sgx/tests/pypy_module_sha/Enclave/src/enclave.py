from ffi import ffi
import _sha as sha

@ffi.def_extern()
def test_sha():
    t = AppTestSHA()
    for k, v in AppTestSHA.__dict__.items():
        if k.startswith("test_"):
            print "[+] testing", k
            v(t)

class AppTestSHA(object):

    def __init__(self):
        self.sha = sha

    def test_digest_size(self):
        """
        Check some numeric values from the sha module.
        """
        assert self.sha.blocksize == 1
        assert self.sha.digest_size == 20
        assert self.sha.digestsize == 20
        d = self.sha.new()
        assert d.digest_size == 20
        assert d.digestsize == 20

    def test_SHAType(self):
        """
        Test the two ways to construct an sha object.
        """
        sha = self.sha
        d = sha.new()
        assert isinstance(d, sha.SHAType)

    def test_shaobject(self):
        """
        Feed example strings into a sha object and check the digest and
        hexdigest.
        """
        sha = self.sha
        cases = (
          ("",
           "da39a3ee5e6b4b0d3255bfef95601890afd80709"),
          ("a",
           "86f7e437faa5a7fce15d1ddcb9eaeaea377667b8"),
          ("abc",
           "a9993e364706816aba3e25717850c26c9cd0d89d"),
          ("message digest",
           "c12252ceda8be8994d5fa0290a47231c1d16aae3"),
          ("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789",
           "761c457bf73b14d27e9e9265c46f4b4dda11f940"),
          ("1234567890" * 8,
           "50abf5706a150990a08b2c5ea40fa0e585554732"),
          ("1234567890"*999,
           "eaaca5490568fde98d8dc553d9566bdc602fde4a"),
        )
        for input, expected in cases:
            d = sha.new(input)
            assert d.hexdigest() == expected
    #         assert d.digest() == expected.decode('hex')

    def test_copy(self):
        """
        Test the copy() method.
        """
        sha = self.sha
        d1 = sha.new()
        d1.update("abcde")
        d2 = d1.copy()
        d2.update("fgh")
        d1.update("jkl")
        assert d1.hexdigest() == 'f5d13cf6341db9b0e299d7b9d562de9572b58e5d'
        assert d2.hexdigest() == '425af12a0743502b322e93a015bcf868e324d56a'

    def test_buffer(self):
        """
        Test passing a buffer object.
        """
        sha = self.sha
        d1 = sha.new(buffer("abcde"))
        d1.update(buffer("jkl"))
        assert d1.hexdigest() == 'f5d13cf6341db9b0e299d7b9d562de9572b58e5d'

def raises(expected_exception, *args, **kwargs):
    func = args[0]
    try:
        func(*args[1:], **kwargs)
    except expected_exception:
        return True
    message = "DID NOT RAISE {}".format(expected_exception)
    print message
    assert False, message
