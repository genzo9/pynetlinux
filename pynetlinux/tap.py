import fcntl
import os
import struct

from pynetlinux import ifconfig
from pynetlinux import util

# From linux/if_tun.h

# Ioctl defines
TUNSETNOCSUM  = 0x400454c8
TUNSETDEBUG   = 0x400454c9
TUNSETIFF     = 0x400454ca
TUNSETPERSIST = 0x400454cb
TUNSETOWNER   = 0x400454cc
TUNSETLINK    = 0x400454cd

# TUNSETIFF ifr flags
IFF_TUN       = 0x0001
IFF_TAP		  = 0x0002
IFF_NO_PI	  = 0x1000
IFF_ONE_QUEUE = 0x2000


class Tap(ifconfig.Interface):
    """
    An object representing a Linux tap device. This object can be used as an
    argument to select().

    See Documentation/networking/tuntap.txt in the linux kernel source for
    (some) programming information.
    """
    
    # See ifconfig.py for details of ifr struct
    def __init__(self, name=None, blocking=True):
        '''If name is None, the kernel will allocate a device name of the form tap#,
        where # is the lowest unused tap device number.'''
        flags = os.O_RDWR
        if not blocking:
            flags |= os.O_NONBLOCK
        self._fileno = os.open("/dev/net/tun", flags)

        if util.PY3:
            self.fd = os.fdopen(self._fileno, 'w+b', buffering=0)
        else:
            self.fd = os.fdopen(self._fileno, 'w+b')

        if name is None:
            name = b""

        # TAP device with no packet information.
        ifreq = struct.pack("16sH", name, IFF_TAP | IFF_NO_PI)
        res = fcntl.ioctl(self.fd, TUNSETIFF, ifreq)
        self.name = struct.unpack("16sH", res)[0].strip(b'\x00')
        
        fcntl.ioctl(self.fd, TUNSETNOCSUM, 1)
        ifconfig.Interface.__init__(self, self.name)
    
    def persist(self):
        fcntl.ioctl(self.fd, TUNSETPERSIST, 1)
    
    def unpersist(self):
        fcntl.ioctl(self.fd, TUNSETPERSIST, 0)

    def fileno(self):
        return self._fileno
    
    def read(self, n):
        return os.read(self.fileno(), n)
    
    def write(self, data):
        return os.write(self.fileno(), data)
    
    def close(self):
        self.fd.close()

