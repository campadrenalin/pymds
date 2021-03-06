from pymads.errors import *
from pymads.extern import unittest

class TestErrors(unittest.TestCase):

    def test_int_constructor(self):
        e = DnsError(0)
        self.assertEquals(e.code,  0)
        self.assertEquals(e.label, 'NOERROR')

        e = DnsError(1)
        self.assertEquals(e.code,  1)
        self.assertEquals(e.label, 'FORMERR')

        e = DnsError(5)
        self.assertEquals(e.code,  5)
        self.assertEquals(e.label, 'REFUSED')

        msg =  "You're gonna have one."
        e = DnsError(0xe, msg)
        self.assertEquals(e.code,  0xe)
        self.assertEquals(e.label, 'BADTIME')
        self.assertEquals(e.args, ('BADTIME', 0xe, msg))

    def test_str_constructor(self):
        e = DnsError('NOERROR')
        self.assertEquals(e.code, 0)
        self.assertEquals(e.label, 'NOERROR')        

        e = DnsError('REFUSED')
        self.assertEquals(e.code,  5)
        self.assertEquals(e.label, 'REFUSED')

        msg =  "You're gonna have one."
        e = DnsError('BADTIME', msg)
        self.assertEquals(e.code,  0xe)
        self.assertEquals(e.label, 'BADTIME')
        self.assertEquals(e.args, ('BADTIME', 0xe, msg))

    def test_repr(self):
        self.assertEquals(
            repr(DnsError(3)),
            "DnsError('NXDOMAIN', 3)"
        )
        self.assertEquals(
            repr(DnsError(2, "Wrench in the works")),
            "DnsError('SERVFAIL', 2, 'Wrench in the works')"
        )

class TestConverter(unittest.TestCase):
    def setUp(self):
        import logging
        try:
            from StringIO import StringIO
        except ImportError:
            from io import StringIO

        # Setup a logger that writes to a string only
        self.io = StringIO()
        handler = logging.StreamHandler(self.io)
        log = logging.getLogger('test')
        log.propagate = False
        log.setLevel(logging.DEBUG)
        log.addHandler(handler)
        handler.setFormatter(
            logging.Formatter(fmt="[%(levelname)s:%(name)s]%(message)s")
        )

    def test_dnserr(self):
        with self.assertRaises(DnsError) as assertion:
            with ErrorConverter((3,)):
                raise DnsError(1)
        
        self.assertEquals(
            repr(assertion.exception),
            "DnsError('FORMERR', 1)"
        )

    def test_diverr(self):
        with self.assertRaises(DnsError) as assertion:
            with ErrorConverter((3,)):
                return 1/0

        # Determine normal args for this exception...
        # varies by Python version
        with self.assertRaises(ZeroDivisionError) as zdiv:
            1/0
        # Fuck Python 2.
        if isinstance(zdiv.exception, Exception):
            correct_args = zdiv.exception.args
        else:
            correct_args = (zdiv.exception,)

        exc = assertion.exception
        self.assertEquals(
            ('NXDOMAIN', 3) + correct_args,
            exc.args
        )

    def test_customerr(self):
        with self.assertRaises(DnsError) as assertion:
            with ErrorConverter((1,), 'test'):
                raise Exception()

        # Check logged information
        msg = self.io.getvalue()
        self.assertTrue(msg.find('[DEBUG:test]') == 0)
        self.assertTrue(msg.find('Exception') > -1)

        self.assertEquals(
            repr(assertion.exception),
            "DnsError('FORMERR', 1)"
        )

        with self.assertRaises(DnsError) as assertion:
            with ErrorConverter((1,)):
                raise Exception('ABC')
        
        self.assertEquals(
            repr(assertion.exception),
            "DnsError('FORMERR', 1, 'ABC')"
        )

        with self.assertRaises(DnsError) as assertion:
            with ErrorConverter((1,)):
                raise Exception('ABC', 123)
        
        self.assertEquals(
            repr(assertion.exception),
            "DnsError('FORMERR', 1, 'ABC', 123)"
        )

    def test_badinit(self):
        # Someone forgot that the first argument is an iterable...
        with self.assertRaises(TypeError) as assertion:
            with ErrorConverter(1):
                raise Exception()
        
        self.assertIn(
            "'int' object is not iterable",
            repr(assertion.exception)
        )
