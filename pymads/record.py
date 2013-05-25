'''
This file is part of Pymads.

Pymads is free software: you can redistribute it and/or modify
it under the terms of the GNU Lesser General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

Pymads is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Lesser General Public License for more details.

You should have received a copy of the GNU Lesser General Public License
along with Pymads.  If not, see <http://www.gnu.org/licenses/>
'''

import struct
from socket import inet_pton, AF_INET, AF_INET6
from pymads import const
from pymads import utils

class Record(object):
    ''' Represents a DNS record. '''

    def __init__(self, domain_name, rdata, 
                    rtype="A", rttl=1800, rclass="IN"):
        '''
            domain_name : A straightforward FQDN or PQDN
            rdata       : For most records, just IP string.
            rtype       : Record type. Usually A or AAAA.
            rttl        : Time-to-live (expiration data).
            rclass      : Almost always IN for Internet.
        '''
        self.domain_name = domain_name
        self.rdata  = rdata
        self.rtype  = const.get_label(const.RECORD_TYPES, rtype)
        self.rttl   = int(rttl)
        self.rclass = const.get_label(const.RECORD_CLASSES, rclass)
        self.rdata_packed = self.pack_rdata()

    @property
    def rtypecode(self):
        return const.RECORD_TYPES[self.rtype]

    @property
    def rclasscode(self):
        return const.RECORD_CLASSES[self.rclass]

    def __hash__(self):
        return hash((
            self.domain_name,
            self.rdata,
            self.rtype,
            self.rttl,
            self.rclass,
        ))

    def pack_rdata(self):
        '''
        Create the binary representation of the rdata for use in responses.
        '''
        # TODO : Support more special output types
        if self.rtype == 'A':
            return inet_pton(AF_INET, self.rdata)
        elif self.rtype == 'AAAA':
            return inet_pton(AF_INET6, self.rdata)
        else:
            return utils.byteify(self.rdata)

    def pack(self):
        '''
        Formats the resource fields to be used in the response packet.
        '''

        r  = utils.labels2str(utils.byteify(x) for x in self.domain_name.split('.'))
        r += struct.pack(
            "!HHIH",
             self.rtypecode,
             self.rclasscode,
             self.rttl,
             len(self.rdata_packed)
        )
        r += self.rdata_packed
        return r

    def unpack(self, source):
        '''
        Decodes data into instance properties
        '''
        offset, labels = utils.str2labels(source)
        self.domain_name = '.'.join(labels)
        self.rtypecode, self.rclasscode, self.rttl, rdata_len = struct.unpack("!HHIH", source[offset:offset+5])
        offset += 5
        self.rdata = self.unpack_rdata(
            source[offset:offset+rdata_len]
        )
        return offset + rdata_len
