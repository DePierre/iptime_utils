#!/usr/bin/env python
from __future__ import print_function
import sys
import zlib
import gzip
import struct
import tarfile
import logging


__author__ = 'Tao "depierre" Sauvage'


HEADER_SIZE = 0x30
MAGIC_INDEX = 0
MAGIC_STRING = b'raw_nv'
SIZE_COMPRESSED_INDEX = 0x10
SUM_INDEX = 0x14
VERSION_INDEX = 0x18
FS_ID_INDEX = 0x1c


def dump_header(header):
    """Dump ipTIME custom header."""
    magic_string = header[MAGIC_INDEX:MAGIC_INDEX + len(MAGIC_STRING)]
    if magic_string != MAGIC_STRING:
        logging.warning('\t[~] magic string is different: %s %s' % (magic_string, MAGIC_STRING))
    size = header[SIZE_COMPRESSED_INDEX:SIZE_COMPRESSED_INDEX + 4]
    sum_gz = header[SUM_INDEX:SUM_INDEX + 4]
    version = header[VERSION_INDEX:VERSION_INDEX + 4]
    fs_id = header[FS_ID_INDEX:FS_ID_INDEX + 4]
    logging.info('\t\tMagic: %s' % magic_string)
    logging.info('\t\tSize of gz (compressed): %d' % struct.unpack('<I', size))
    logging.info('\t\tSum of gz bytes: 0x%04X' % struct.unpack('<I', sum_gz))
    logging.info('\t\tVersion(?): 0x%04X' % struct.unpack('<I', version))
    logging.info('\t\tFS id: 0x%04X' % struct.unpack('<I', fs_id))


def compute_sum(gz):
    """Simple sum of bytes in gzip file used as a checksum by ipTIME."""
    res = sum(c for c in bytearray(gz))
    logging.info('\t\tComputed sum: 0x%04X' % res)
    return res


def build_header(gz):
    """Build ipTIME custom header."""
    header = MAGIC_STRING + b'\x00' * (16 - len(MAGIC_STRING))
    header += struct.pack('<I', len(gz))
    header += struct.pack('<I', compute_sum(gz))
    header += struct.pack('<I', 0x7FD0)
    header += struct.pack('<I', 0x10000)
    header += b'\x00' * 16
    return header


def extract(filename):
    """Extract ipTIME backup configuration file .cfg"""
    logging.info('Extracting ipTIME configuration...')
    with open(filename, 'rb') as f:
        outer_gz = f.read()
    # Bug in ipTIME?
    # Sometimes the configuration file starts with 0x0d 0x0a, which seem to be from the HTTP header, not the conf
    if outer_gz.startswith(b'\x0d\x0a'):
        logging.info('\t [~] Removing \\r\\n at the beginning of config file (bug in ipTIME firmware).')
        outer_gz = outer_gz[2:]
    # 1. First layer is gzip and contains ipTIME custom header and the tar.gz configuration files
    logging.info('\t[+] Extracting outer gzip')
    data = zlib.decompress(outer_gz, 16 + zlib.MAX_WBITS)
    header, tar_gz = data[:HEADER_SIZE], data[HEADER_SIZE:]
    logging.info('\t[+] Dumping extracted header')
    dump_header(header)
    with open('a.header', 'wb') as f:
        f.write(header)  # For debug.
    # 2. Second layer is a tar.gz and contains the actual configuration files
    with open('b.tar.gz', 'wb') as f:
        f.write(tar_gz)
    logging.info('\t[+] Extracting inner tar.gz tarball')
    tar = tarfile.open('b.tar.gz')
    tar.extractall()
    tar.close()


def make_tarfile(output_filename, source_dir):
    """Create tarball from directory. See: http://stackoverflow.com/a/17081026"""
    with tarfile.open(output_filename, "w:gz") as tar:
        tar.add(source_dir, arcname='etc/')


def pack(filename):
    """Re-pack configuration files from ./etc/ to ipTIME backup file format."""
    logging.info('Packing new configuration files...')
    logging.info('\t[+] Create tarball of ./etc/')
    make_tarfile('b.tar.gz', './etc/')
    with open('b.tar.gz', 'rb') as f:
        gz = f.read()
    logging.info('\t[+] Generating new ipTIME header')
    header = build_header(gz)
    logging.info('\t[+] Creating outer gzip file')
    with gzip.open(filename, 'wb', compresslevel=9) as f:
        f.write(header + gz)


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format='%(message)s')
    logging.info('PoC for extracting/repacking ipTIME backup configuration file')
    logging.warning('Warning: only tested on ipTIME n704 v3, firmware version 9.98.6')

    if len(sys.argv) < 3 or (len(sys.argv) == 2 and sys.argv[1] in ['-h', '--h', '--help']):
        logging.error('Usage: %s -e|-c <config.cfg>' % sys.argv[0])
        sys.exit(-1)

    if sys.argv[1] == '-e':  # Extraction
        extract(sys.argv[2])
        logging.info('Extraction successful. You can now edit configuration files in ./etc/')
        logging.info('Use -c to pack the new configuration')
    elif sys.argv[1] == '-c':  # Repack
        pack(sys.argv[2])
        logging.info('Packing successful. You can now upload the configuration file to ipTIME router.')
