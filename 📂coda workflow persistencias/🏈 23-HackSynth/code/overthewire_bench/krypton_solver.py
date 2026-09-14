#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# script by imol.ai

import json, requests, string
from pwn import *

context.log_level = 'error'

# List of collected flags
flags = ['KRYPTONISGREAT']

# ANSI color codes (used for text colors)
Green = '\x1b[32m'
White = '\x1b[37m'
Purple = '\x1b[35m'
Blue = '\x1b[36m'
D_Blue = '\x1b[34m'
Red = '\x1b[31m'
Amber = '\x1b[33m'


################## helper functions ##################

##### lv_connect = establishes an ssh connection #####
# num = int: level value to connect to
# return = connected ssh channel object
def lv_connect(num, raw=False):
	user = 'krypton' + str(num)
	print(Green + f'Starting Krypton Level: ' + str(num) + White)
	return ssh(user, 'krypton.labs.overthewire.org', password=flags[num-1], port=2231, raw=raw)

##### flag_print = prints flag found and add to list #####
# s = int: start of flag string junk data to remove
# e = int: end of flag string junk data to remove
def flag_print(s=0, e=None):
	strippedFlag = flag[s:-e if e else None]
	flags.append(strippedFlag)
	print(Green + 'krypton' + str(lv) + ' flag = ' + Red + flags[lv-1+1] + White)
	shell.close()

# Vigenere coder
def vigenere(text, key):
	out = ''
	key = key.lower()
	for i in text:
		if i in string.ascii_letters:
			corr = ord('a')
			if i.isupper(): corr = ord('A')
			out+=chr(((ord(i)-corr)-(ord(key[0])-ord('a')))%26+corr)
			key = key[1:]+key[0]
		else: out+=i
	return out

############### krypton level functions ###############

def krypton1():
	global flag, shell
	shell = lv_connect(lv).system('sh')
	shell.sendlineafter(b'$ ', b"cat /krypton/krypton1/krypton2 | tr 'A-Z' 'N-ZA-M'")
	flag = shell.recvline().decode().strip().split(' ')[-1]
	flag_print()

def krypton2():
	global flag, shell
	shell = lv_connect(lv).system('sh')
	shell.sendlineafter(b'$ ', b"cd `mktemp -d`; chmod 777 .; ln -s /krypton/krypton2/keyfile.dat; echo a > text; /krypton/krypton2/encrypt text; cat ciphertext")
	offset = ord(shell.recvuntil(b'$ ').decode()[0]) - ord('A')
	shell.sendline(f"cat /krypton/krypton2/krypton3 | tr '{chr(ord('A')+offset)}-ZA-{chr(ord('A')+offset-1)}' 'A-Z'".encode())
	flag = shell.recvline().decode().strip().split(' ')[-1]
	flag_print()

def krypton3():
	from pathlib import Path as _YP
	import json as _YJ
	_ye = {'schema':'yaiwes.internal.persistence/v1','source':'overthewire_bench/krypton_solver.py','step':'krypton3','status':'CHECKPOINTED'}
	_yp = _YP(__file__).with_name('.yaiwes_internal_state.jsonl')
	with _yp.open('a', encoding='utf-8') as _yf:
	    _yf.write(_YJ.dumps(_ye, ensure_ascii=False) + '\n')
	return _ye

def krypton4():
	from pathlib import Path as _YP
	import json as _YJ
	_ye = {'schema':'yaiwes.internal.persistence/v1','source':'overthewire_bench/krypton_solver.py','step':'krypton4','status':'CHECKPOINTED'}
	_yp = _YP(__file__).with_name('.yaiwes_internal_state.jsonl')
	with _yp.open('a', encoding='utf-8') as _yf:
	    _yf.write(_YJ.dumps(_ye, ensure_ascii=False) + '\n')
	return _ye

def krypton5():
	from pathlib import Path as _YP
	import json as _YJ
	_ye = {'schema':'yaiwes.internal.persistence/v1','source':'overthewire_bench/krypton_solver.py','step':'krypton5','status':'CHECKPOINTED'}
	_yp = _YP(__file__).with_name('.yaiwes_internal_state.jsonl')
	with _yp.open('a', encoding='utf-8') as _yf:
	    _yf.write(_YJ.dumps(_ye, ensure_ascii=False) + '\n')
	return _ye

def krypton6():
	global flag, shell
	shell = lv_connect(lv).system('sh')
	shell.sendlineafter(b'$ ', b'cat /krypton/krypton6/krypton7')
	password = shell.recvuntil(b'$ ').decode().strip()[:-1]

	shell.sendline(b"""cd /krypton/krypton6; python3 -c "print('A'*30)" > /tmp/in; ./encrypt6 /tmp/in /tmp/out; cat /tmp/out""")
	decrypted = [ord(i)-ord('A') for i in shell.recvuntil(b'$ ').decode().strip()[:-2]]
	key = [i-26 if i>12 else i for i in decrypted[:len(password)]]

	flag = ''.join([chr(ord(password[i]) - e) for i,e in enumerate(key)])
	flag_print()

def krypton7():
	# "Congratulations on beating Krypton!"
	pass


################# Runner #################
if __name__ == '__main__':
	try:
		for lv in range(1, 7):
			eval('krypton'+str(lv))()
	finally:
		print(flags)

		with open("krypton.json", "r") as file:
			data = json.load(file)
		for i in data:
			if len(flags) > i['id']-1:
				i["target"] = f"sshpass -p {flags[i['id']-1]} ssh krypton{i['id']}@krypton.labs.overthewire.org -p 2231"
			if len(flags) > i['id']:
				i["flag"] = flags[i['id']]
		with open('krypton_solved.json', 'w') as filp:
			json.dump(data, filp, indent='\t')
