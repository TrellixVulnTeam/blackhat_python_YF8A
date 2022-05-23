from ctypes import *
import os
import socket
import struct
import sys


class IP(Structure):
    _fields_ = [
        ("version",        c_ubyte,    4),
        ("headerLen",      c_ubyte,    4),
        ("typeOfService",  c_ubyte,    8),
        ("len",            c_ushort,  16),
        ("id",             c_ushort,  16),
        ("offset",         c_ushort,  16),
        ("ttl",            c_ubyte,    8),
        ("protocol_num",   c_ubyte,    8),
        ("sum",            c_ushort,  16),
        ("src",            c_uint32,  32),
        ("dst",            c_uint32,  32),
    ]

    def __new__(cls, socket_buffer = None):
        return cls.from_buffer_copy(socket_buffer)

    def __init__(self, socket_buffer = None):
        self.src_address = socket.inet_ntoa(struct.pack("<L", self.src))
        self.dst_address = socket.inet_ntoa(struct.pack("<L", self.dst))

        self.flag = self.offset >> 13
        self.fragmentOffset = self.offset and 0xffff
        self.protocol_map = {1: "ICMP", 6: "TCP", 17: "UDP"}
        try:
            self.protocol = self.protocol_map[self.protocol_num]
        except Exception as e:
            print('%s %s is Unknown Protocol', e, self.protocol_num)
            self.protocol = str(self.protocol_num)


class ICMP(Structure):
    _fields_ = [
        ("type", c_ubyte,   8),
        ("code", c_ubyte,   8),
        ("sum",  c_ushort, 16),
        ("id",   c_ushort, 16),
        ("seq",  c_ushort, 16),
    ]

    def __new__(cls, socket_buffer = None):
        return cls.from_buffer_copy(socket_buffer)


def sniff(host):
    if os.name == 'nt':
        socket_protocol = socket.IPPROTO_IP
    else:
        socket_protocol = socket.IPPROTO_ICMP
    
    sniffer = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket_protocol)
    print(host)
    sniffer.bind((host, 0))
    sniffer.setsockopt(socket.IPPROTO_IP, socket.IP_HDRINCL, 1)

    if os.name == 'nt':
        sniffer.ioctl(socket.SIO_RCVALL, socket.RCVALL_ON)
    
    try:
        while True:
            raw_buffer = sniffer.recvfrom(65535)[0]
            ip_header = IP(raw_buffer[0:20])
            print(f'Protocol: {ip_header.protocol} | {ip_header.src_address} -> {ip_header.dst_address}')
            if ip_header.protocol == "ICMP":
                print(f'Version: {ip_header.version}')
                print(f'Header Length: {ip_header.headerLen} TTL: {ip_header.ttl}')

                offset = ip_header.headerLen * 4
                buf = raw_buffer[offset:offset+8]
                icmp_header = ICMP(buf)
                print(f'ICMP -> Type: {icmp_header.type}, Code: {icmp_header.code}')

    except KeyboardInterrupt:
        if os.name == 'nt':
            sniffer.ioctl(socket.SIO_RCVALL, socket.RCVALL_OFF)
        sys.exit()


def get_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("8.8.8.8", 80))
    ip = str(s.getsockname()[0])
    s.close()
    return ip


if __name__ == '__main__':
    if len(sys.argv) == 2:
        host = sys.argv[1]
    else:
        host = str(get_ip())
    sniff(host)