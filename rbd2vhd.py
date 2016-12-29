#!/usr/bin/python
#
# Copyright (C) Roman V. Posudnevskiy (ramzes_r@yahoo.com)
#
# This program is free software; you can redistribute it and/or modify 
# it under the terms of the GNU Lesser General Public License as published 
# by the Free Software Foundation; version 2.1 only.
#
# This program is distributed in the hope that it will be useful, 
# but WITHOUT ANY WARRANTY; without even the implied warranty of 
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the 
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth math.floor, Boston, MA  02110-1301  USA

from struct import *
import uuid
import sys, getopt
import re
import time
#import ctypes

SECTOR_SIZE = 512
VHD_DEFAULT_BLOCK_SIZE = 2097152
VHD_DYNAMIC_HARDDISK_TYPE = 0x00000003# Dynamic hard disk
VHD_DIFF_HARDDISK_TYPE = 0x00000004# Differencing hard disk

#-- VHD FOOTTER FIELDs --#
_vhd_footter_cookie_                 = 0
_vhd_footter_features_               = 1
_vhd_footter_file_format_version_    = 2
_vhd_footter_data_offset_            = 3
_vhd_footter_time_stamp_             = 4
_vhd_footter_creator_application_    = 5
_vhd_footter_creator_version_        = 6
_vhd_footter_creator_host_os_        = 7
_vhd_footter_original_size_          = 8
_vhd_footter_current_size_           = 9
_vhd_footter_disk_geometry_          = 10
_vhd_footter_disk_type_              = 11
_vhd_footter_checksum_               = 12
_vhd_footter_unique_iq_              = 13
_vhd_footter_saved_state_            = 14
#-- VHD FOOTTER FIELDs --#

#-- VHD DISK GEOMETRY FIELs --#
_vhd_disk_geometry_cylinders_            = 0
_vhd_disk_geometry_heads_                = 1
_vhd_disk_geometry_sectors_per_cylinder_ = 2
#-- VHD DISK GEOMETRY FIELs --#

#-- DYNAMIC DISK HEADER FIELDs --#
_dynamic_disk_header_cookie_                    = 0
_dynamic_disk_header_data_offset_               = 1
_dynamic_disk_header_table_offset_              = 2
_dynamic_disk_header_header_version_            = 3
_dynamic_disk_header_max_table_entries_         = 4
_dynamic_disk_header_block_size_                = 5
_dynamic_disk_header_checksum_                  = 6
_dynamic_disk_header_parent_unique_id_          = 7
_dynamic_disk_header_parent_time_stamp_         = 8
_dynamic_disk_header_parent_unicode_name_       = 10
_dynamic_disk_header_parent_locator_entry_1_    = 11
_dynamic_disk_header_parent_locator_entry_2_    = 12
_dynamic_disk_header_parent_locator_entry_3_    = 13
_dynamic_disk_header_parent_locator_entry_4_    = 14
_dynamic_disk_header_parent_locator_entry_5_    = 15
_dynamic_disk_header_parent_locator_entry_6_    = 16
_dynamic_disk_header_parent_locator_entry_7_    = 17
_dynamic_disk_header_parent_locator_entry_8_    = 18
#-- DYNAMIC DISK HEADER FIELDs --#

#-- BATMAP FIELDs --#
_batmap_cookie_      = 0
_batmap_offset_      = 1
_batmap_size_        = 2
_batmap_version_     = 3
_batmap_checksum_    = 4
_batmap_marker_      = 5
#-- BATMAP FIELDs --#

#-- PARENT LOCATOR ENTRY FIELD --#
_parent_locator_platform_code_          = 0
_parent_locator_platform_data_space_    = 1
_parent_locator_platform_data_length_   = 2
_parent_locator_platform_data_offset_   = 4
#-- PARENT LOCATOR ENTRY FIELD --#_

#-- DISK TYPES --#
_disk_type_none                     = 0
_disk_type_fixed_hard_disk          = 2
_disk_type_dynamic_hard_disk        = 3
_disk_type_differencing_hard_disk   = 4
#-- DISK TYPES --#

#-- PLATFORM CODEs --#
_platform_code_None_    = 0x0
_platform_code_Wi2r_    = 0x57693272
_platform_code_Wi2k_    = 0x5769326B
_platform_code_W2ru_    = 0x57327275
_platform_code_W2ku_    = 0x57326B75
_platform_code_Mac_     = 0x4D616320
_platform_code_MacX_    = 0x4D616358
#-- PLATFORM CODEs --#

VHD_FOTTER_FORMAT = "!8sIIQI4sIIQQ4sII16sB427s"
VHD_FOTTER_RECORD_SIZE = 512
VHD_DISK_GEOMETRY_FORMAT = "!HBB"
VHD_DISK_GEOMETRY_RECORD_SIZE = 4
VHD_DYNAMIC_DISK_HEADER_FORMAT = "!8sQQIIII16sII512s24s24s24s24s24s24s24s24s256s"
VHD_DYNAMIC_DISK_HEADER_RECORD_SIZE = 1024
VHD_PARENT_LOCATOR_ENTRY_FORMAT = "!IIIIQ"
VHD_PARENT_LOCATOR_ENTRY_RECORD_SIZE = 24
VHD_BATMAP_HEADER_FORMAT = "!8sQIIIB"
VHD_BATMAP_HEADER_SIZE = 29

#-- RBD DIFF v1 META AND DATA FIELDs --#
RBD_HEADER = "rbd diff v1\n"
RBD_DIFF_RECORD_TAG = "!c"
RBD_DIFF_META_SNAP = "I"
RBD_DIFF_META_SIZE = "Q"
RBD_DIFF_DATA = "QQ"
#-- RBD DIFF v1 META AND DATA FIELDs --#

def get_size_aligned_to_sector_boundary(size):
    if size%512>0:
        aligned_size = ((bitmap_size//512)+1)*512
    else:
        aligned_size = size
    return aligned_size

def get_vhd_footer_b(vhdfile):
    vhdfile.seek(0, 0)
    _buffer_ = vhdfile.read(VHD_FOTTER_RECORD_SIZE)
    return unpack(VHD_FOTTER_FORMAT, _buffer_)

def get_vhd_footer_e(vhdfile):
    vhdfile.seek(-get_size_aligned_to_sector_boundary(VHD_FOTTER_RECORD_SIZE), 2)
    _buffer_ = vhdfile.read(VHD_FOTTER_RECORD_SIZE)
    return unpack(VHD_FOTTER_FORMAT, _buffer_)

def get_vhd_batmap(vhdfile, dynamic_disk_header):
    vhdfile.seek(get_size_aligned_to_sector_boundary(VHD_FOTTER_RECORD_SIZE + VHD_DYNAMIC_DISK_HEADER_RECORD_SIZE + dynamic_disk_header[_dynamic_disk_header_max_table_entries_]*4), 0)
    _buffer_ = vhdfile.read(VHD_BATMAP_HEADER_SIZE)
    return unpack(VHD_BATMAP_HEADER_FORMAT, _buffer_)    

def get_dynamic_disk_header(vhdfile):
    vhdfile.seek(get_size_aligned_to_sector_boundary(VHD_FOTTER_RECORD_SIZE), 0)
    _buffer_ = vhdfile.read(VHD_DYNAMIC_DISK_HEADER_RECORD_SIZE)
    return unpack(VHD_DYNAMIC_DISK_HEADER_FORMAT, _buffer_)

def get_parent_locator(vhdfile, parent_locator_entry):
    vhdfile.seek(parent_locator_entry[_parent_locator_platform_data_offset_], 0)
    _buffer_ = vhdfile.read(parent_locator_entry[_parent_locator_platform_data_length_])
    return unpack("!%ds" % parent_locator_entry[_parent_locator_platform_data_length_], _buffer_)

def print_vhd_batmap(batmap):
    print("------------------ BATMAP -----------------------------------------")
    print("VHD BATMAP: Cookie = %s" % batmap[_batmap_cookie_])
    print("VHD BATMAP: Offset = 0x%016x" % batmap[_batmap_offset_])
    print("VHD BATMAP: Size = %d" % batmap[_batmap_size_])
    print("VHD BATMAP: Version = 0x%08x" % batmap[_batmap_version_])
    print("VHD BATMAP: Checksum = 0x%08x" % batmap[_batmap_checksum_])
    print("VHD BATMAP: Marker = 0x%02x" % batmap[_batmap_marker_])
    print("-------------------------------------------------------------------")

def print_dynamic_disk_header(vhdfile, dynamic_disk_header):
    print("------------------ DYNAMIC DISK HEADER -----------------------------------------")
    print("VHD DYNAMIC DISK HEADER: Cookie = %s" % dynamic_disk_header[_dynamic_disk_header_cookie_])
    print("VHD DYNAMIC DISK HEADER: Data Offset = 0x%016x" % dynamic_disk_header[_dynamic_disk_header_data_offset_])
    print("VHD DYNAMIC DISK HEADER: Table Offset = 0x%016x" % dynamic_disk_header[_dynamic_disk_header_table_offset_])
    print("VHD DYNAMIC DISK HEADER: Header version = 0x%08x" % dynamic_disk_header[_dynamic_disk_header_header_version_])
    print("VHD DYNAMIC DISK HEADER: Max Table Entries = 0x%08x" % dynamic_disk_header[_dynamic_disk_header_max_table_entries_])
    print("VHD DYNAMIC DISK HEADER: Block Size = 0x%08x" % dynamic_disk_header[_dynamic_disk_header_block_size_])
    print("VHD DYNAMIC DISK HEADER: Checksum = 0x%08x" % dynamic_disk_header[_dynamic_disk_header_checksum_])
    print("VHD DYNAMIC DISK HEADER: Parent Unique ID = %s" % uuid.UUID(bytes=dynamic_disk_header[_dynamic_disk_header_parent_unique_id_]))
    print("VHD DYNAMIC DISK HEADER: Timestamp = 0x%08x" % dynamic_disk_header[_dynamic_disk_header_parent_time_stamp_])
    print("VHD DYNAMIC DISK HEADER: Parent Unicode Name = %s" % dynamic_disk_header[_dynamic_disk_header_parent_unicode_name_])
    parent_locator_entry = unpack(VHD_PARENT_LOCATOR_ENTRY_FORMAT, dynamic_disk_header[_dynamic_disk_header_parent_locator_entry_1_])
    print("VHD DYNAMIC DISK HEADER: Parent Locator Entry 1 ( Platform Code = 0x%08x, Platform Data Space = %i, Platform Data Length = %i, Platform Data Offset = 0x%016x ) " % (parent_locator_entry[_parent_locator_platform_code_],parent_locator_entry[_parent_locator_platform_data_space_],parent_locator_entry[_parent_locator_platform_data_length_],parent_locator_entry[_parent_locator_platform_data_offset_]))
    print("VHD DYNAMIC DISK HEADER: Parent Locator Entry 1 = \'%s\'" % get_parent_locator(vhdfile, parent_locator_entry))
    parent_locator_entry = unpack(VHD_PARENT_LOCATOR_ENTRY_FORMAT, dynamic_disk_header[_dynamic_disk_header_parent_locator_entry_2_])
    print("VHD DYNAMIC DISK HEADER: Parent Locator Entry 2 ( Platform Code = 0x%08x, Platform Data Space = %i, Platform Data Length = %i, Platform Data Offset = 0x%016x ) " % (parent_locator_entry[_parent_locator_platform_code_],parent_locator_entry[_parent_locator_platform_data_space_],parent_locator_entry[_parent_locator_platform_data_length_],parent_locator_entry[_parent_locator_platform_data_offset_]))
    print("VHD DYNAMIC DISK HEADER: Parent Locator Entry 2 = \'%s\'" % get_parent_locator(vhdfile, parent_locator_entry))
    parent_locator_entry = unpack(VHD_PARENT_LOCATOR_ENTRY_FORMAT, dynamic_disk_header[_dynamic_disk_header_parent_locator_entry_3_])
    print("VHD DYNAMIC DISK HEADER: Parent Locator Entry 3 ( Platform Code = 0x%08x, Platform Data Space = %i, Platform Data Length = %i, Platform Data Offset = 0x%016x ) " % (parent_locator_entry[_parent_locator_platform_code_],parent_locator_entry[_parent_locator_platform_data_space_],parent_locator_entry[_parent_locator_platform_data_length_],parent_locator_entry[_parent_locator_platform_data_offset_]))
    print("VHD DYNAMIC DISK HEADER: Parent Locator Entry 3 = \'%s\'" % get_parent_locator(vhdfile, parent_locator_entry))
    parent_locator_entry = unpack(VHD_PARENT_LOCATOR_ENTRY_FORMAT, dynamic_disk_header[_dynamic_disk_header_parent_locator_entry_4_])
    print("VHD DYNAMIC DISK HEADER: Parent Locator Entry 4 ( Platform Code = 0x%08x, Platform Data Space = %i, Platform Data Length = %i, Platform Data Offset = 0x%016x ) " % (parent_locator_entry[_parent_locator_platform_code_],parent_locator_entry[_parent_locator_platform_data_space_],parent_locator_entry[_parent_locator_platform_data_length_],parent_locator_entry[_parent_locator_platform_data_offset_]))
    print("VHD DYNAMIC DISK HEADER: Parent Locator Entry 4 = \'%s\'" % get_parent_locator(vhdfile, parent_locator_entry))
    parent_locator_entry = unpack(VHD_PARENT_LOCATOR_ENTRY_FORMAT, dynamic_disk_header[_dynamic_disk_header_parent_locator_entry_5_])
    print("VHD DYNAMIC DISK HEADER: Parent Locator Entry 5 ( Platform Code = 0x%08x, Platform Data Space = %i, Platform Data Length = %i, Platform Data Offset = 0x%016x ) " % (parent_locator_entry[_parent_locator_platform_code_],parent_locator_entry[_parent_locator_platform_data_space_],parent_locator_entry[_parent_locator_platform_data_length_],parent_locator_entry[_parent_locator_platform_data_offset_]))
    print("VHD DYNAMIC DISK HEADER: Parent Locator Entry 5 = \'%s\'" % get_parent_locator(vhdfile, parent_locator_entry))
    parent_locator_entry = unpack(VHD_PARENT_LOCATOR_ENTRY_FORMAT, dynamic_disk_header[_dynamic_disk_header_parent_locator_entry_6_])
    print("VHD DYNAMIC DISK HEADER: Parent Locator Entry 6 ( Platform Code = 0x%08x, Platform Data Space = %i, Platform Data Length = %i, Platform Data Offset = 0x%016x ) " % (parent_locator_entry[_parent_locator_platform_code_],parent_locator_entry[_parent_locator_platform_data_space_],parent_locator_entry[_parent_locator_platform_data_length_],parent_locator_entry[_parent_locator_platform_data_offset_]))
    print("VHD DYNAMIC DISK HEADER: Parent Locator Entry 6 = \'%s\'" % get_parent_locator(vhdfile, parent_locator_entry))
    parent_locator_entry = unpack(VHD_PARENT_LOCATOR_ENTRY_FORMAT, dynamic_disk_header[_dynamic_disk_header_parent_locator_entry_7_])
    print("VHD DYNAMIC DISK HEADER: Parent Locator Entry 7 ( Platform Code = 0x%08x, Platform Data Space = %i, Platform Data Length = %i, Platform Data Offset = 0x%016x ) " % (parent_locator_entry[_parent_locator_platform_code_],parent_locator_entry[_parent_locator_platform_data_space_],parent_locator_entry[_parent_locator_platform_data_length_],parent_locator_entry[_parent_locator_platform_data_offset_]))
    print("VHD DYNAMIC DISK HEADER: Parent Locator Entry 7 = \'%s\'" % get_parent_locator(vhdfile, parent_locator_entry))
    parent_locator_entry = unpack(VHD_PARENT_LOCATOR_ENTRY_FORMAT, dynamic_disk_header[_dynamic_disk_header_parent_locator_entry_8_])
    print("VHD DYNAMIC DISK HEADER: Parent Locator Entry 8 ( Platform Code = 0x%08x, Platform Data Space = %i, Platform Data Length = %i, Platform Data Offset = 0x%016x ) " % (parent_locator_entry[_parent_locator_platform_code_],parent_locator_entry[_parent_locator_platform_data_space_],parent_locator_entry[_parent_locator_platform_data_length_],parent_locator_entry[_parent_locator_platform_data_offset_]))
    print("VHD DYNAMIC DISK HEADER: Parent Locator Entry 8 = \'%s\'" % get_parent_locator(vhdfile, parent_locator_entry))
    #print(dynamic_disk_header)
    print("--------------------------------------------------------------------------------")

def print_vhd_footer(vhd_footer):
    print("------------------ VHD FOOTER-----------------------------------------")
    print("VHD FOOTER: Cookie = %s" % vhd_footer[_vhd_footter_cookie_])
    print("VHD FOOTER: Features = 0x%08x" % vhd_footer[_vhd_footter_features_])
    print("VHD FOOTER: File Format Version = 0x%08x" % vhd_footer[_vhd_footter_file_format_version_])
    print("VHD FOOTER: Data Offset = 0x%08x" % vhd_footer[_vhd_footter_data_offset_])
    print("VHD FOOTER: Timestamp = 0x%08x" % vhd_footer[_vhd_footter_time_stamp_])
    print("VHD FOOTER: Creator Application = %s" % vhd_footer[_vhd_footter_creator_application_])
    print("VHD FOOTER: Creator Version = 0x%08x" % vhd_footer[_vhd_footter_creator_version_])
    print("VHD FOOTER: Creator Host OS = 0x%08x" % vhd_footer[_vhd_footter_creator_host_os_])
    print("VHD FOOTER: Original Size = %i" % vhd_footer[_vhd_footter_original_size_])
    print("VHD FOOTER: Current Size = %i" % vhd_footer[_vhd_footter_current_size_])
    vhd_disk_geometry = unpack(VHD_DISK_GEOMETRY_FORMAT, vhd_footer[_vhd_footter_disk_geometry_])
    print("VHD FOOTER: Disk Geometry (Cylinders = %i, Heads = %i, Sectors per cylinder = %s)" % (vhd_disk_geometry[_vhd_disk_geometry_cylinders_],vhd_disk_geometry[_vhd_disk_geometry_heads_],vhd_disk_geometry[_vhd_disk_geometry_sectors_per_cylinder_]))
    print("VHD FOOTER: Disk Type = 0x%08x" % vhd_footer[_vhd_footter_disk_type_])
    print("VHD FOOTER: Checksum = 0x%08x" % vhd_footer[_vhd_footter_checksum_])
    print("VHD FOOTER: Unique ID = %s" % uuid.UUID(bytes=vhd_footer[_vhd_footter_unique_iq_]))
    print("VHD FOOTER: Saved State = 0x%02x" % vhd_footer[_vhd_footter_saved_state_])
    #print(vhd_footer)
    print("----------------------------------------------------------------------")

def gen_vhd_footer_struct(disk_type, image_size, uuid, checksum):
    disk_geometry_struct = gen_disk_geometry(image_size)
    disk_geometry = pack(VHD_DISK_GEOMETRY_FORMAT, disk_geometry_struct[0], disk_geometry_struct[1], disk_geometry_struct[2])
    reserved = ''
    for i in range(427):
        reserved = reserved + pack('!c', chr(0))
    footer_struct = ('conectix', 0x00000002, 0x00010000, 0x00000200, time.time(), 'tap', 0x00010003, 0x00000000, image_size, image_size, disk_geometry, disk_type, checksum, uuid, 0, reserved)
    return footer_struct

def gen_vhd_dynamic_disk_header_struct(table_offset, image_size, checksum, parent_uuid, parent_unicode_name):
    max_tab_entries = image_size / VHD_DEFAULT_BLOCK_SIZE
    reserved = ''
    for i in range(256):
        reserved = reserved + pack('!c', chr(0))
    parent_locator_entry_1_struct = (0x4d616358, 512, 49, 0, 0x0000000000005c00) #MacX
    parent_locator_entry_1 = pack(VHD_PARENT_LOCATOR_ENTRY_FORMAT, *parent_locator_entry_1_struct)
    parent_locator_entry_2_struct = (0x57326b75, 512, 84, 0, 0x0000000000005e00) #W2ku
    parent_locator_entry_2 = pack(VHD_PARENT_LOCATOR_ENTRY_FORMAT, *parent_locator_entry_2_struct)
    parent_locator_entry_3_struct = (0x57327275, 512, 84, 0, 0x0000000000006000) #W2ru
    parent_locator_entry_3 = pack(VHD_PARENT_LOCATOR_ENTRY_FORMAT, *parent_locator_entry_3_struct)
    parent_locator_entry_empty_struct = (0x00000000, 0, 0, 0, 0) #empty
    parent_locator_entry_empty = pack(VHD_PARENT_LOCATOR_ENTRY_FORMAT, *parent_locator_entry_empty_struct)
    header_struct = ('cxsparse', 0xffffffffffffffff, table_offset, 0x00010000, max_tab_entries, VHD_DEFAULT_BLOCK_SIZE, checksum, parent_uuid, time.time(), 0x00000000, parent_unicode_name, parent_locator_entry_1, parent_locator_entry_2, parent_locator_entry_3, parent_locator_entry_empty, parent_locator_entry_empty, parent_locator_entry_empty, parent_locator_entry_empty, parent_locator_entry_empty, reserved)
    return header_struct

def gen_vhd_checksum(vhd_record):
    checksum = 0
    b = bytearray()
    b.extend(vhd_record)
    for index in range(VHD_FOTTER_RECORD_SIZE):
        checksum += b[index]
    checksum = ~checksum + 2**32
    return checksum
    
def gen_disk_geometry(image_size):
    totalSectors = image_size / SECTOR_SIZE
    if totalSectors > 65535*16*255:
        totalSectors = 65535*16*255
    if totalSectors >= 65535*16*255:
        sectorsPerTrack = 255
        heads = 16
        cylinderTimesHeads = totalSectors / sectorsPerTrack
    else:
        sectorsPerTrack = 17
        cylinderTimesHeads = totalSectors / sectorsPerTrack
        heads = (cylinderTimesHeads + 1023) / 1024
        if heads < 4:
            heads = 4
        if (cylinderTimesHeads >= (heads * 1024)) | (heads > 16):
            sectorsPerTrack = 31
            heads = 16
            cylinderTimesHeads = totalSectors / sectorsPerTrack
        if cylinderTimesHeads >= (heads * 1024):
            sectorsPerTrack = 63
            heads = 16
            cylinderTimesHeads = totalSectors / sectorsPerTrack
    cylinders = cylinderTimesHeads / heads
    geometry = (cylinders, heads, sectorsPerTrack)
    #print "totalSectors = %d, Cyliders = %d, heads = %d, sectors per track = %d" % (totalSectors, cylinders, heads, sectorsPerTrack)
    return geometry

def gen_vhd_bat_empty_table(image_size):
    battab_list = []
    max_tab_entries = image_size / VHD_DEFAULT_BLOCK_SIZE
    for battab_index in range(max_tab_entries):
        battab_list.append(0xffffffff)
    return battab_list

def gen_vhd_bat_table(battab_list):
    max_tab_entries = len(battab_list)
    bat = ''
    for battab_index in range(max_tab_entries):
        bat = bat + pack('!I', battab_list[battab_index])
    return bat

def get_bat_table(vhdfile, table_offset, max_table_entries, block_size):
    vhdfile.seek(table_offset, 0)
    _format_ = "!%iI" % max_table_entries
    return unpack(_format_,vhdfile.read(max_table_entries*4))

def get_bitmap_size(dynamic_disk_header):
    sectors_in_block = dynamic_disk_header[_dynamic_disk_header_block_size_]/SECTOR_SIZE 
    bitmap_size = sectors_in_block/8
    if bitmap_size%512>0:
        bitmap_size=((bitmap_size//512)+1)*512
    return bitmap_size

def get_sector_bitmap_and_data(vhdfile, data_block_offset, block_size):
    sectors_in_block = block_size/512 
    bitmap_size = sectors_in_block/8
    if bitmap_size%512>0:
        bitmap_size=((bitmap_size//512)+1)*512
    _format_ = "!%is%is" % (bitmap_size,block_size)
    #print (_format_)
    vhdfile.seek((data_block_offset)*512, 0)
    BUFFER=vhdfile.read(bitmap_size+block_size)
    bitmap_and_data=unpack(_format_,BUFFER)
    _format_ = "!"
    for i in range(sectors_in_block):
        _format_ = _format_ + "512s"
    data = unpack(_format_,bitmap_and_data[1])
    return [bitmap_and_data[0],data]

def get_bitarray_from_bitmap(bitmap, bitmap_size):
    bitarray = []
    _bitmap_ = bytearray()
    _bitmap_.extend(bitmap)
    for bitmap_index in range(bitmap_size):
        for bit_index in range(8):
            offset = 128 >> bit_index
            if (_bitmap_[bitmap_index] & offset) > 0:
                bitarray.append(1)
            else:
                bitarray.append(0)
    return bitarray

def gen_empty_bitarray_for_bitmap(bitmap_size):
    bitarray = []
    #bitmap = bytearray()
    for bitmap_index in range(bitmap_size):
        for bit_index in range(8):
            bitarray.append(0)
    return bitarray

def raw_byte_offset_of_sector(block_number, sector_in_block, block_size, sector_size):
    return block_number*block_size+sector_in_block*sector_size

def raw_sector_offset_of_sector(block_number, sector_in_block, block_size, sector_size):
    sector_per_block = block_size / sector_size
    return block_number*sector_per_block+sector_in_block

def get_rbd_header(rbdfile):
    rbdfile.seek(0, 0)
    _buffer_ = rbdfile.read(len(RBD_HEADER))
    return _buffer_

def rbd2vhd(rbd, vhd):
    VHD_FH = open(vhd, "wb")
    RBDDIFF_FH = open(rbd, "rb")
    rbd_header = get_rbd_header(RBDDIFF_FH)
    
    rbd_meta_read_finished = 0
    vhd_headers_written = 0
    blocks_bitmaps = {}
    from_snap_name = ''
    to_snap_name = ''
    allocated_block_count=0
    
    while True:
        record_tag = RBDDIFF_FH.read(1)
        #record_tag = unpack("!c", record)
        if not record_tag:
            print "RBD: -EOF-"
            break
        else:
            #print "RBD Record TAG = \'%c\'" % record_tag
            if record_tag == "e":
                print "RBD: EOF"
                break
            if record_tag == "f":
                record = RBDDIFF_FH.read(4)
                snap_name_length = unpack('!'+RBD_DIFF_META_SNAP,record)
                record = RBDDIFF_FH.read(snap_name_length)
                from_snap_name = unpack("!%ds" % snap_name_length,record)
                print "RBD: From snap = %s" % from_snap_name
            elif record_tag == "t":
                record = RBDDIFF_FH.read(4)
                snap_name_length = unpack('!'+RBD_DIFF_META_SNAP,record)
                record = RBDDIFF_FH.read(snap_name_length)
                to_snap_name = unpack("!%ds" % snap_name_length,record)
                print "RBD: To snap = %s" % from_snap_name
            elif record_tag == "s":
                record = RBDDIFF_FH.read(8)
                image_size = int(unpack('!'+RBD_DIFF_META_SIZE,record)[0])
                print "RBD: Image size = %d" % image_size
            elif record_tag == "w":
                record = RBDDIFF_FH.read(16)
                _record_ = unpack('!'+RBD_DIFF_DATA,record)
                offset = _record_[0]
                length = _record_[1]
                record = RBDDIFF_FH.read(length)
                data = unpack("!%ds" % length, record)
                print "RBD: Data offset = 0x%08x and length = %d" % (offset, length)
                if rbd_meta_read_finished == 0:
                    rbd_meta_read_finished = 1
            elif record_tag == "z":
                record = RBDDIFF_FH.read(16)
                _record_ = unpack('!'+RBD_DIFF_DATA,record)
                offset = _record_[0]
                length = _record_[1]
                record = ''
                for i in range(length):
                    record = record + pack('!c', chr(0))
                print "RBD: Zero data offset = 0x%08x and length = %d" % (offset, length)
                if rbd_meta_read_finished == 0:
                    rbd_meta_read_finished = 1
                data = unpack("!%ds" % length, record)
            else:
                print "RBD: Error while reading"
            
            if (rbd_meta_read_finished == 1) & (vhd_headers_written == 0):
                if from_snap_name:
                        parent_uuid = uuid.UUID(from_snap_name)
                else:
                        parent_uuid = uuid.UUID('00000000-0000-0000-0000-000000000000')
                if to_snap_name:
                    image_uuid = uuid.UUID(to_snap_name)
                else:
                    image_uuid = uuid.UUID('00000000-0000-0000-0000-000000000000')
                vhd_footer_struct = gen_vhd_footer_struct(VHD_DIFF_HARDDISK_TYPE, image_size, image_uuid.bytes, 0)
                VHD_FOOTER = pack(VHD_FOTTER_FORMAT, *vhd_footer_struct)
                checksum = gen_vhd_checksum(VHD_FOOTER)
                vhd_footer_struct = gen_vhd_footer_struct(VHD_DIFF_HARDDISK_TYPE, image_size, image_uuid.bytes, checksum)
                #print "checksum %d = 0x%08x" % (checksum, checksum)
                VHD_FOOTER = pack(VHD_FOTTER_FORMAT, *vhd_footer_struct)
                
                dynamic_disk_header_struct = gen_vhd_dynamic_disk_header_struct(0x0000000000000600, image_size, 0, parent_uuid.bytes, "%s.vhd" % str(parent_uuid))
                DYNAMIC_DISK_HEADER = pack(VHD_DYNAMIC_DISK_HEADER_FORMAT, *dynamic_disk_header_struct)
                checksum = gen_vhd_checksum(DYNAMIC_DISK_HEADER)
                dynamic_disk_header_struct = gen_vhd_dynamic_disk_header_struct(0x0000000000000600, image_size, checksum, parent_uuid.bytes, "%s.vhd" % str(parent_uuid))
                DYNAMIC_DISK_HEADER = pack(VHD_DYNAMIC_DISK_HEADER_FORMAT, *dynamic_disk_header_struct)
                BAT_STRUCT = gen_vhd_bat_empty_table(10737418240)
                BAT = gen_vhd_bat_table(BAT_STRUCT)
    
                VHD_FH.write(VHD_FOOTER)
                VHD_FH.write(DYNAMIC_DISK_HEADER)
                VHD_FH.write(BAT)
                data_offset = VHD_FH.tell()
                
                print_vhd_footer(vhd_footer_struct)
                print_dynamic_disk_header(dynamic_disk_header_struct)
                
                vhd_headers_written = 1
                block_bitmap_size = get_bitmap_size(dynamic_disk_header_struct)
                
            if (rbd_meta_read_finished == 1) & (vhd_headers_written == 1):
                #write data
                databytearray = bytearray()
                databytearray.extend(data[0])
                SectorPerBlock = VHD_DEFAULT_BLOCK_SIZE / SECTOR_SIZE
                print "SectorPerBlock = %d, offset = %d, length = %d" % (SectorPerBlock, offset, length)
                for _offset_ in range(offset,offset+length):
                    #print "_offset _= %d" % _offset_
                    RawSectorNumber = _offset_ / SECTOR_SIZE
                    BlockNumber = RawSectorNumber // (VHD_DEFAULT_BLOCK_SIZE//SECTOR_SIZE)
                    SectorInBlock = RawSectorNumber % SectorPerBlock
                    
                    if blocks_bitmaps.has_key(BlockNumber):
                        if blocks_bitmaps[BlockNumber][SectorInBlock] == 0:
                            del blocks_bitmaps[BlockNumber][SectorInBlock]
                            blocks_bitmaps[BlockNumber].insert(SectorInBlock, 1)
                    else:
                        blocks_bitmaps[BlockNumber] = gen_empty_bitarray_for_bitmap(block_bitmap_size)
                        del blocks_bitmaps[BlockNumber][SectorInBlock]
                        blocks_bitmaps[BlockNumber].insert(SectorInBlock, 1)
                    
                    #print "VHD BlockNumber %d" % BlockNumber
                    
                    if BAT_STRUCT[BlockNumber] == 0xffffffff:
                        block_offset_in_sectors = (data_offset+(allocated_block_count*VHD_DEFAULT_BLOCK_SIZE))/SECTOR_SIZE + SectorInBlock
                        block_offset_in_bytes = block_offset_in_sectors * SECTOR_SIZE
                        BAT_STRUCT[BlockNumber] = block_offset_in_sectors
                        allocated_block_count = allocated_block_count + 1
                        VHD_FH.seek(block_offset_in_bytes, 0)
                        print "VHD position %d; BlockNumber %d" % (BAT_STRUCT[BlockNumber], BlockNumber)
                    
                    VHD_FH.write(pack('!B', databytearray[_offset_ - offset]))
    # rewrite BAT
    VHD_FH.write(VHD_FOOTER)
    VHD_FH.seek(VHD_FOTTER_RECORD_SIZE+VHD_DYNAMIC_DISK_HEADER_RECORD_SIZE, 0)
    BAT = gen_vhd_bat_table(BAT_STRUCT)
    VHD_FH.write(BAT)
    
    VHD_FH.close
    RBDDIFF_FH.close
    return 0

def vhd2rbd(vhd, rbd):
    #VHD_FH = open("/run/sr-mount/e0f1d862-1e8a-df94-2bd2-3260732d6702/41cd1cc1-97b3-4774-83d3-6208bca53cb3.vhd", "rb")
    #VHD_FH = open("/run/sr-mount/e0f1d862-1e8a-df94-2bd2-3260732d6702/75d74d1e-31d8-487a-820b-7d0f8014af60.vhd", "rb")
    #RBDDIFF_FH = open("/run/sr-mount/e0f1d862-1e8a-df94-2bd2-3260732d6702/75d74d1e-31d8-487a-820b-7d0f8014af60.rbddiff", "wb")
    
    VHD_FH = open(vhd, "rb")
    RBDDIFF_FH = open(rbd, "wb")
    
    VHD_FOOTER = get_vhd_footer_b(VHD_FH)
    print_vhd_footer(VHD_FOOTER)
    DYNAMIC_DISK_HEADER = get_dynamic_disk_header(VHD_FH)
    print_dynamic_disk_header(VHD_FH, DYNAMIC_DISK_HEADER)
    BATMAP = get_vhd_batmap(VHD_FH, DYNAMIC_DISK_HEADER)
    print_vhd_batmap(BATMAP)
    BLOCK_SIZE = DYNAMIC_DISK_HEADER[_dynamic_disk_header_block_size_]
    
    BAT_TABLE = get_bat_table(VHD_FH, DYNAMIC_DISK_HEADER[_dynamic_disk_header_table_offset_], DYNAMIC_DISK_HEADER[_dynamic_disk_header_max_table_entries_], DYNAMIC_DISK_HEADER[_dynamic_disk_header_block_size_])
    # Write RBD diff header
    #print("Writing RBD diff header ...")
    RBDDIFF_FH.write(RBD_HEADER)
    # Write RBD Size record
    #print("Writing RBD Size record ...")
    rbddiff_image_size = pack(RBD_DIFF_RECORD_TAG+RBD_DIFF_META_SIZE, 's', VHD_FOOTER[_vhd_footter_current_size_])
    RBDDIFF_FH.write(rbddiff_image_size)
    
    
    total_changed_sectors = 0
    total_changed_sectors_ = 0
    raw_first_sector = 0
    raw_last_sector = 0
    in_block_first_sector = 0
    in_block_last_sector = 0
    for block_index in range(DYNAMIC_DISK_HEADER[_dynamic_disk_header_max_table_entries_]):
        if BAT_TABLE[block_index] != 0xffffffff:
            DATA_BLOCK = get_sector_bitmap_and_data(VHD_FH, BAT_TABLE[block_index], BLOCK_SIZE)
            
            BITMAP_SIZE = get_bitmap_size(DYNAMIC_DISK_HEADER)
            print "BLOCK_NUMBER %d" % block_index
            
            BITARRAY = get_bitarray_from_bitmap(DATA_BLOCK[0], BITMAP_SIZE)
            #print (BITARRAY)
            for sector_in_block_index in range(BITMAP_SIZE*8):
                #print("bit_index - %d, value = %d" % (sector_in_block_index,BITARRAY[sector_in_block_index]))
                if BITARRAY[sector_in_block_index] == 1:
                    ##print("Sector: %d" % sector_in_block_index)
                    #print("DATA: ", DATA_BLOCK[1][sector_in_block_index])
                    #print("sector_in_block_index - %d" % sector_in_block_index)
                    total_changed_sectors_ = total_changed_sectors_ + 1
                    if raw_first_sector == 0:
                        raw_first_sector = raw_sector_offset_of_sector(block_index, sector_in_block_index, BLOCK_SIZE, SECTOR_SIZE)
                        in_block_first_sector = sector_in_block_index
                        raw_last_sector = 0
                else:
                    if (raw_last_sector == 0) & (raw_first_sector != 0) :
                        raw_last_sector = raw_sector_offset_of_sector(block_index, sector_in_block_index-1, BLOCK_SIZE, SECTOR_SIZE)
                        in_block_last_sector = sector_in_block_index-1
                        #print("\tRaw From sector %d to sector %d" % (raw_first_sector, raw_last_sector))
                        #print("\tInBlock From sector %d to sector %d" % (in_block_first_sector, in_block_last_sector))
                        
                        # Write RBD data record header
                        #print("Writing RBD data record header ...")
                        rbddiff_data_header = pack(RBD_DIFF_RECORD_TAG+RBD_DIFF_DATA, 'w', raw_first_sector*512,(raw_last_sector-raw_first_sector+1)*512)
                        #print("\tSectors: %d" % (raw_last_sector-raw_first_sector+1))
                        #print("\tBytes: %d" % ((raw_last_sector-raw_first_sector+1)*512))
                        RBDDIFF_FH.write(rbddiff_data_header)
                        for sector_index in range(in_block_first_sector, in_block_last_sector+1):
                            # Write RBD data record data
                            #print("Writing RBD data record data ...")
                            #print("Writing Sector: %d" % sector_index)
                            total_changed_sectors = total_changed_sectors + 1
                            #print("DATA: ", DATA_BLOCK[1][sector_index])
                            rbddiff_data = pack("!512s",DATA_BLOCK[1][sector_index])
                            RBDDIFF_FH.write(rbddiff_data)
                        
                        raw_first_sector = 0
                        raw_last_sector = 0
                        in_block_first_sector = 0
                        in_block_last_sector = 0
            if (sector_in_block_index == BITMAP_SIZE*8-1) and (raw_first_sector != 0) :
                raw_last_sector = raw_sector_offset_of_sector(block_index, sector_in_block_index, BLOCK_SIZE, SECTOR_SIZE)
                in_block_last_sector = sector_in_block_index
                #print("\tRaw From sector %d to sector %d" % (raw_first_sector, raw_last_sector))
                #print("\tInBlock From sector %d to sector %d" % (in_block_first_sector, in_block_last_sector))
                
                # Write RBD data record header
                #print("Writing RBD data record header ...")
                rbddiff_data_header = pack(RBD_DIFF_RECORD_TAG+RBD_DIFF_DATA, 'w', raw_first_sector*512,(raw_last_sector-raw_first_sector+1)*512)
                #print("\tSectors: %d" % (raw_last_sector-raw_first_sector+1))
                #print("\tBytes: %d" % ((raw_last_sector-raw_first_sector+1)*512))
                RBDDIFF_FH.write(rbddiff_data_header)
                for sector_index in range(in_block_first_sector, in_block_last_sector+1):
                    # Write RBD data record data
                    #print("Writing RBD data record data ...")
                    #print("Writing Sector: %d" % sector_index)
                    total_changed_sectors = total_changed_sectors + 1
                    #print("DATA: ", DATA_BLOCK[1][sector_index])
                    rbddiff_data = pack("!512s",DATA_BLOCK[1][sector_index])
                    RBDDIFF_FH.write(rbddiff_data)
                
                raw_first_sector = 0
                raw_last_sector = 0
                in_block_first_sector = 0
                in_block_last_sector = 0
            
    #DATA = DATA_BLOCK[1]
            
    #for bitmap_index in range(0, BITMAP_SIZE-1):
    #    if BITMAP[bitmap_index] != 0:
    #        print "BAT[%i] - BITMAP[%i] => 0x%02x" % (bat_index, bitmap_index, BITMAP[bitmap_index])
    print("Total changed sectors: %d - %d" % (total_changed_sectors,total_changed_sectors_))
    print("Total changed bytes: %d - %d" % ((total_changed_sectors*512),(total_changed_sectors_*512)))
    
    RBDDIFF_FH.write('e')
    
    VHD_FH.close
    RBDDIFF_FH.close
    return 0
#-------------------------------------------------------------------------------------------------------------------------------------------------------#
def main(argv):
    vhd_file = ''
    rbd_file = ''
    cmdname = sys.argv[0]
    regex = re.compile('.*/*.*/')
    cmdname = regex.sub('', cmdname)
    regex = re.compile('\.\w+')
    cmdname = regex.sub('', cmdname)
    
    if len(sys.argv) > 1:
        try:
            opts, args = getopt.getopt(argv,"hv:r:",["vhd=","rbd="])
        except getopt.GetoptError:
            print "Usage:"
            print '\tvhd2rbd -v <vhd_file> -r <rbd_file>'
            print '\trbd2vhd -r <rbd_file> -v <vhd_file>'
            sys.exit(2)
        for opt, arg in opts:
            if opt == '-h':
                print "Usage:"
                print '\tvhd2rbd -v <vhd_file> -r <rbd_file>'
                print '\trbd2vhd -r <rbd_file> -v <vhd_file>'
                sys.exit()
            elif opt in ("-v", "--vhd"):
                vhd_file = arg
            elif opt in ("-r", "--rbd"):
                rbd_file = arg
        print 'VHD file is \'%s\'' % vhd_file
        print 'RBD file is \'%s\'' % rbd_file
        
        if (cmdname == 'vhd2rbd'):
            vhd2rbd(vhd_file, rbd_file)
        elif(cmdname == 'rbd2vhd'):
            rbd2vhd(rbd_file, vhd_file)
            pass
    else:
            print "Usage:"
            print '\tvhd2rbd -v <vhd_file> -r <rbd_file>'
            print '\trbd2vhd -r <rbd_file> -v <vhd_file>'

if __name__ == "__main__":
   main(sys.argv[1:])
