##
## This file is part of the libsigrokdecode project.
##
## Copyright (C) 2022 Matej Martinček <matomarss@gmail.com>
##
## This program is free software; you can redistribute it and/or modify
## it under the terms of the GNU General Public License as published by
## the Free Software Foundation; either version 2 of the License, or
## (at your option) any later version.
##
## This program is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with this program; if not, see <http://www.gnu.org/licenses/>.
##

'''
OUTPUT_PYTHON format:

Packet:
[<ptype>, <pdata>]

<ptype>:
 - 'ADDRESS
 - 'DATA'

<pdata> is the data or address byte associated with the 'ADDRESS' or 'DATA'
command.
'''

import re
import sigrokdecode as srd
from common.srdhelper import bcd2int, SrdIntEnum

class Decoder(srd.Decoder):
    api_version = 3
    id = 'i2c_extractor'
    name = 'I2C bytes extractor'
    longname = 'The I2C bytes extractor'
    desc = 'Extracts data and address bytes from I2C communication and potentially sends them to other stack-decoders'
    license = 'gplv2+'
    inputs = ['i2c']
    outputs = ['dataBytes']
    tags = ['Embedded/industrial']
    annotations = ()
    annotation_rows = ()

    def __init__(self):
        self.reset()

    def reset(self):
        self.state = 'INACTIVE'
        self.bits = []

    def start(self):
        self.out_python = self.register(srd.OUTPUT_PYTHON)


    def putp(self, data):
        self.put(self.ss, self.es, self.out_python, data)

    def send_address_byte(self, b):
        # send the address byte of type ADDRESS onto row no. 0
        self.putp(['ADDRESS', b, 0])

    def send_data_byte(self, b):
        # send the data byte of type DATA onto row no. 0
        self.putp(['DATA', b, 0])

    def decode(self, ss, es, data):
        cmd, data_byte = data

        # Collect the 'BITS' packet, then return. The next packet is
        # guaranteed to belong to these bits we just stored.
        if cmd == 'BITS':
            self.bits = data_byte
            return

        # Store the start/end samples of this I²C packet.
        self.ss, self.es = ss, es

        # State machine.
        if cmd == 'START' or cmd == 'START REPEAT':
            self.state = 'ACTIVE'
            return
        elif cmd == 'STOP':
            self.state = 'INACTIVE'
            return

        if self.state == 'ACTIVE':
            if cmd == 'ADDRESS WRITE' or cmd == 'ADDRESS READ':
                self.send_address_byte(data_byte)
            elif cmd == 'DATA WRITE' or cmd == 'DATA READ':
                self.send_data_byte(data_byte)
