#!/usr/bin/python

# A simple script to copy pokemon from retail carts to a computer via GTS.
# Heavily relies on the sendpkm script and the description of the GTS protocol
# from http://projectpokemon.org/wiki/GTS_protocol
#
# --Infinite Recursion

from pokehaxlib import *
from pkmlib import decode
from sys import argv, exit
from string import uppercase, lowercase, digits
from random import sample
from time import sleep
from base64 import b64decode
from binascii import hexlify
from array import array
from namegen import namegen
import os.path, subprocess, platform

def makepkm(bytes):
    ar = array('B') # Byte array to hold encrypted data
    ar.fromstring(bytes)

    # checksum is first four bytes of data, xor'd with 0x4a3b2c1d
    chksm = (eval('0x' + hexlify(ar[0:4]))) ^ 0x4a3b2c1d

    bin = ar[4:len(ar)] # Byte array for decrypt operations
    pkm = array('B')    # ...and one for the output file

    # Running decryption algorithm
    GRNG = chksm | (chksm << 16)
    for i in range(len(bin)):
        GRNG = (GRNG * 0x45 + 0x1111) & 0x7fffffff
        keybyte = (GRNG >> 16) & 0xff
        pkm.append((bin[i] ^ keybyte) & 0xff)

    pkm = pkm[4:len(pkm)]
    pkm = pkm[0:236].tostring()
    pkm = decode(pkm)

    return pkm

def save(path, data):
    saved = False
    folder = 'Pokemon' + os.sep

    while not saved:
        saved = True
        if os.path.isfile(folder + path):
            print '%s already exists! Delete?' % path
            response = raw_input().lower()
            if response != 'y' and response != 'yes':
                print 'Enter new filename: (press enter to cancel save) '
                path = raw_input()
                if path == '':
                    print 'Not saved'
                    return
                if not path.strip().lower().endswith('.pkm'):
                    path += '.pkm'
                saved = False

#   try:
    f = open(folder + path, 'wb')
#   except:
#       print 'Cannot write to file %s' % path
#       print 'Returning to main menu'
#       return
    f.write(data)
    f.close()
    print '%s saved successfully; returning to main menu.' % path

def getpkm():
    token = 'c9KcX1Cry3QKS2Ai7yxL6QiQGeBGeQKR'
    sent = False
    print 'Ready to receive from NDS'
    while not sent:
        sock, req = getReq()
        a = req.action

        if len(req.getvars) == 1: sendResp(sock, token)
        elif a == 'info':
            sendResp(sock, '\x01\x00')
            print 'Connection Established.'
        elif a == 'setProfile': sendResp(sock, '\x00' * 8)
        elif a == 'result': sendResp(sock, '\x05\x00')
        elif a == 'delete': sendResp(sock, '\x01\x00')
        elif a == 'search': sendResp(sock, '')
        elif a == 'post':
            sendResp(sock, '\x0c\x00')
            print 'Receiving Pokemon...'
            data = req.getvars['data']
            bytes = b64decode(data.replace('-', '+').replace('_', '/'))
            decrypt = makepkm(bytes)
            filename = namegen(decrypt[0x48:0x5e])
            filename += '.pkm'
            save(filename, decrypt)
            sent = True
