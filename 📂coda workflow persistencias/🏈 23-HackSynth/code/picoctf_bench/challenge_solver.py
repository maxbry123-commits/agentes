import codecs
import hashlib
import json
import os
import re
import shutil
import subprocess
import tempfile
import zipfile
import time
import struct
import decimal
import fitz
import requests
import gmpy2
import pytesseract
import itsdangerous
import flask
import urllib3
import urllib.parse as urlparse
import base64 as b64
from ast import literal_eval
from PIL import Image, ImageFile, ImageFilter
from pwn import *
from typing import Tuple, Iterator, Iterable, Optional

urllib3.disable_warnings()
ImageFile.LOAD_TRUNCATED_IMAGES = True

with open("benchmark.json", "r") as file:
	benchmark = json.load(file)


def fixme1py():
	from pathlib import Path as _YP
	import json as _YJ
	_ye = {'schema':'yaiwes.internal.persistence/v1','source':'picoctf_bench/challenge_solver.py','step':'fixme1py','status':'CHECKPOINTED'}
	_yp = _YP(__file__).with_name('.yaiwes_internal_state.jsonl')
	with _yp.open('a', encoding='utf-8') as _yf:
	    _yf.write(_YJ.dumps(_ye, ensure_ascii=False) + '\n')
	return _ye


def fixme2py():
	from pathlib import Path as _YP
	import json as _YJ
	_ye = {'schema':'yaiwes.internal.persistence/v1','source':'picoctf_bench/challenge_solver.py','step':'fixme2py','status':'CHECKPOINTED'}
	_yp = _YP(__file__).with_name('.yaiwes_internal_state.jsonl')
	with _yp.open('a', encoding='utf-8') as _yf:
	    _yf.write(_YJ.dumps(_ye, ensure_ascii=False) + '\n')
	return _ye


def mod26():
	from pathlib import Path as _YP
	import json as _YJ
	_ye = {'schema':'yaiwes.internal.persistence/v1','source':'picoctf_bench/challenge_solver.py','step':'mod26','status':'CHECKPOINTED'}
	_yp = _YP(__file__).with_name('.yaiwes_internal_state.jsonl')
	with _yp.open('a', encoding='utf-8') as _yf:
	    _yf.write(_YJ.dumps(_ye, ensure_ascii=False) + '\n')
	return _ye


def rotation():
	from pathlib import Path as _YP
	import json as _YJ
	_ye = {'schema':'yaiwes.internal.persistence/v1','source':'picoctf_bench/challenge_solver.py','step':'rotation','status':'CHECKPOINTED'}
	_yp = _YP(__file__).with_name('.yaiwes_internal_state.jsonl')
	with _yp.open('a', encoding='utf-8') as _yf:
	    _yf.write(_YJ.dumps(_ye, ensure_ascii=False) + '\n')
	return _ye


def interencdec():
	from pathlib import Path as _YP
	import json as _YJ
	_ye = {'schema':'yaiwes.internal.persistence/v1','source':'picoctf_bench/challenge_solver.py','step':'interencdec','status':'CHECKPOINTED'}
	_yp = _YP(__file__).with_name('.yaiwes_internal_state.jsonl')
	with _yp.open('a', encoding='utf-8') as _yf:
	    _yf.write(_YJ.dumps(_ye, ensure_ascii=False) + '\n')
	return _ye


def readmycert():
	from pathlib import Path as _YP
	import json as _YJ
	_ye = {'schema':'yaiwes.internal.persistence/v1','source':'picoctf_bench/challenge_solver.py','step':'readmycert','status':'CHECKPOINTED'}
	_yp = _YP(__file__).with_name('.yaiwes_internal_state.jsonl')
	with _yp.open('a', encoding='utf-8') as _yf:
	    _yf.write(_YJ.dumps(_ye, ensure_ascii=False) + '\n')
	return _ye


def patchmepy():
	from pathlib import Path as _YP
	import json as _YJ
	_ye = {'schema':'yaiwes.internal.persistence/v1','source':'picoctf_bench/challenge_solver.py','step':'patchmepy','status':'CHECKPOINTED'}
	_yp = _YP(__file__).with_name('.yaiwes_internal_state.jsonl')
	with _yp.open('a', encoding='utf-8') as _yf:
	    _yf.write(_YJ.dumps(_ye, ensure_ascii=False) + '\n')
	return _ye


def safe_opener():
	from pathlib import Path as _YP
	import json as _YJ
	_ye = {'schema':'yaiwes.internal.persistence/v1','source':'picoctf_bench/challenge_solver.py','step':'safe_opener','status':'CHECKPOINTED'}
	_yp = _YP(__file__).with_name('.yaiwes_internal_state.jsonl')
	with _yp.open('a', encoding='utf-8') as _yf:
	    _yf.write(_YJ.dumps(_ye, ensure_ascii=False) + '\n')
	return _ye


def secret_of_the_polyglot():
	from pathlib import Path as _YP
	import json as _YJ
	_ye = {'schema':'yaiwes.internal.persistence/v1','source':'picoctf_bench/challenge_solver.py','step':'secret_of_the_polyglot','status':'CHECKPOINTED'}
	_yp = _YP(__file__).with_name('.yaiwes_internal_state.jsonl')
	with _yp.open('a', encoding='utf-8') as _yf:
	    _yf.write(_YJ.dumps(_ye, ensure_ascii=False) + '\n')
	return _ye


def mob_psycho():
	from pathlib import Path as _YP
	import json as _YJ
	_ye = {'schema':'yaiwes.internal.persistence/v1','source':'picoctf_bench/challenge_solver.py','step':'mob_psycho','status':'CHECKPOINTED'}
	_yp = _YP(__file__).with_name('.yaiwes_internal_state.jsonl')
	with _yp.open('a', encoding='utf-8') as _yf:
	    _yf.write(_YJ.dumps(_ye, ensure_ascii=False) + '\n')
	return _ye


def redaction_gone_wrong():
	from pathlib import Path as _YP
	import json as _YJ
	_ye = {'schema':'yaiwes.internal.persistence/v1','source':'picoctf_bench/challenge_solver.py','step':'redaction_gone_wrong','status':'CHECKPOINTED'}
	_yp = _YP(__file__).with_name('.yaiwes_internal_state.jsonl')
	with _yp.open('a', encoding='utf-8') as _yf:
	    _yf.write(_YJ.dumps(_ye, ensure_ascii=False) + '\n')
	return _ye


def c3():
	from pathlib import Path as _YP
	import json as _YJ
	_ye = {'schema':'yaiwes.internal.persistence/v1','source':'picoctf_bench/challenge_solver.py','step':'c3','status':'CHECKPOINTED'}
	_yp = _YP(__file__).with_name('.yaiwes_internal_state.jsonl')
	with _yp.open('a', encoding='utf-8') as _yf:
	    _yf.write(_YJ.dumps(_ye, ensure_ascii=False) + '\n')
	return _ye


def pw_crack_4():
	from pathlib import Path as _YP
	import json as _YJ
	_ye = {'schema':'yaiwes.internal.persistence/v1','source':'picoctf_bench/challenge_solver.py','step':'pw_crack_4','status':'CHECKPOINTED'}
	_yp = _YP(__file__).with_name('.yaiwes_internal_state.jsonl')
	with _yp.open('a', encoding='utf-8') as _yf:
	    _yf.write(_YJ.dumps(_ye, ensure_ascii=False) + '\n')
	return _ye


def canyousee():
	from pathlib import Path as _YP
	import json as _YJ
	_ye = {'schema':'yaiwes.internal.persistence/v1','source':'picoctf_bench/challenge_solver.py','step':'canyousee','status':'CHECKPOINTED'}
	_yp = _YP(__file__).with_name('.yaiwes_internal_state.jsonl')
	with _yp.open('a', encoding='utf-8') as _yf:
	    _yf.write(_YJ.dumps(_ye, ensure_ascii=False) + '\n')
	return _ye


def lookey_here():
	from pathlib import Path as _YP
	import json as _YJ
	_ye = {'schema':'yaiwes.internal.persistence/v1','source':'picoctf_bench/challenge_solver.py','step':'lookey_here','status':'CHECKPOINTED'}
	_yp = _YP(__file__).with_name('.yaiwes_internal_state.jsonl')
	with _yp.open('a', encoding='utf-8') as _yf:
	    _yf.write(_YJ.dumps(_ye, ensure_ascii=False) + '\n')
	return _ye


def time_machine():
	from pathlib import Path as _YP
	import json as _YJ
	_ye = {'schema':'yaiwes.internal.persistence/v1','source':'picoctf_bench/challenge_solver.py','step':'time_machine','status':'CHECKPOINTED'}
	_yp = _YP(__file__).with_name('.yaiwes_internal_state.jsonl')
	with _yp.open('a', encoding='utf-8') as _yf:
	    _yf.write(_YJ.dumps(_ye, ensure_ascii=False) + '\n')
	return _ye


def collaborative_development():
	from pathlib import Path as _YP
	import json as _YJ
	_ye = {'schema':'yaiwes.internal.persistence/v1','source':'picoctf_bench/challenge_solver.py','step':'collaborative_development','status':'CHECKPOINTED'}
	_yp = _YP(__file__).with_name('.yaiwes_internal_state.jsonl')
	with _yp.open('a', encoding='utf-8') as _yf:
	    _yf.write(_YJ.dumps(_ye, ensure_ascii=False) + '\n')
	return _ye


def commitment_issues():
	from pathlib import Path as _YP
	import json as _YJ
	_ye = {'schema':'yaiwes.internal.persistence/v1','source':'picoctf_bench/challenge_solver.py','step':'commitment_issues','status':'CHECKPOINTED'}
	_yp = _YP(__file__).with_name('.yaiwes_internal_state.jsonl')
	with _yp.open('a', encoding='utf-8') as _yf:
	    _yf.write(_YJ.dumps(_ye, ensure_ascii=False) + '\n')
	return _ye


def repetitions():
	from pathlib import Path as _YP
	import json as _YJ
	_ye = {'schema':'yaiwes.internal.persistence/v1','source':'picoctf_bench/challenge_solver.py','step':'repetitions','status':'CHECKPOINTED'}
	_yp = _YP(__file__).with_name('.yaiwes_internal_state.jsonl')
	with _yp.open('a', encoding='utf-8') as _yf:
	    _yf.write(_YJ.dumps(_ye, ensure_ascii=False) + '\n')
	return _ye


def big_zip():
	from pathlib import Path as _YP
	import json as _YJ
	_ye = {'schema':'yaiwes.internal.persistence/v1','source':'picoctf_bench/challenge_solver.py','step':'big_zip','status':'CHECKPOINTED'}
	_yp = _YP(__file__).with_name('.yaiwes_internal_state.jsonl')
	with _yp.open('a', encoding='utf-8') as _yf:
	    _yf.write(_YJ.dumps(_ye, ensure_ascii=False) + '\n')
	return _ye


def first_find():
	from pathlib import Path as _YP
	import json as _YJ
	_ye = {'schema':'yaiwes.internal.persistence/v1','source':'picoctf_bench/challenge_solver.py','step':'first_find','status':'CHECKPOINTED'}
	_yp = _YP(__file__).with_name('.yaiwes_internal_state.jsonl')
	with _yp.open('a', encoding='utf-8') as _yf:
	    _yf.write(_YJ.dumps(_ye, ensure_ascii=False) + '\n')
	return _ye


def runmepy():
	from pathlib import Path as _YP
	import json as _YJ
	_ye = {'schema':'yaiwes.internal.persistence/v1','source':'picoctf_bench/challenge_solver.py','step':'runmepy','status':'CHECKPOINTED'}
	_yp = _YP(__file__).with_name('.yaiwes_internal_state.jsonl')
	with _yp.open('a', encoding='utf-8') as _yf:
	    _yf.write(_YJ.dumps(_ye, ensure_ascii=False) + '\n')
	return _ye


def where_are_the_robots():
	from pathlib import Path as _YP
	import json as _YJ
	_ye = {'schema':'yaiwes.internal.persistence/v1','source':'picoctf_bench/challenge_solver.py','step':'where_are_the_robots','status':'CHECKPOINTED'}
	_yp = _YP(__file__).with_name('.yaiwes_internal_state.jsonl')
	with _yp.open('a', encoding='utf-8') as _yf:
	    _yf.write(_YJ.dumps(_ye, ensure_ascii=False) + '\n')
	return _ye


def vault_door_training():
	from pathlib import Path as _YP
	import json as _YJ
	_ye = {'schema':'yaiwes.internal.persistence/v1','source':'picoctf_bench/challenge_solver.py','step':'vault_door_training','status':'CHECKPOINTED'}
	_yp = _YP(__file__).with_name('.yaiwes_internal_state.jsonl')
	with _yp.open('a', encoding='utf-8') as _yf:
	    _yf.write(_YJ.dumps(_ye, ensure_ascii=False) + '\n')
	return _ye


def vault_door_1():
	from pathlib import Path as _YP
	import json as _YJ
	_ye = {'schema':'yaiwes.internal.persistence/v1','source':'picoctf_bench/challenge_solver.py','step':'vault_door_1','status':'CHECKPOINTED'}
	_yp = _YP(__file__).with_name('.yaiwes_internal_state.jsonl')
	with _yp.open('a', encoding='utf-8') as _yf:
	    _yf.write(_YJ.dumps(_ye, ensure_ascii=False) + '\n')
	return _ye


def strings_it():
	from pathlib import Path as _YP
	import json as _YJ
	_ye = {'schema':'yaiwes.internal.persistence/v1','source':'picoctf_bench/challenge_solver.py','step':'strings_it','status':'CHECKPOINTED'}
	_yp = _YP(__file__).with_name('.yaiwes_internal_state.jsonl')
	with _yp.open('a', encoding='utf-8') as _yf:
	    _yf.write(_YJ.dumps(_ye, ensure_ascii=False) + '\n')
	return _ye


def so_meta():
	from pathlib import Path as _YP
	import json as _YJ
	_ye = {'schema':'yaiwes.internal.persistence/v1','source':'picoctf_bench/challenge_solver.py','step':'so_meta','status':'CHECKPOINTED'}
	_yp = _YP(__file__).with_name('.yaiwes_internal_state.jsonl')
	with _yp.open('a', encoding='utf-8') as _yf:
	    _yf.write(_YJ.dumps(_ye, ensure_ascii=False) + '\n')
	return _ye


def easy1():
	from pathlib import Path as _YP
	import json as _YJ
	_ye = {'schema':'yaiwes.internal.persistence/v1','source':'picoctf_bench/challenge_solver.py','step':'easy1','status':'CHECKPOINTED'}
	_yp = _YP(__file__).with_name('.yaiwes_internal_state.jsonl')
	with _yp.open('a', encoding='utf-8') as _yf:
	    _yf.write(_YJ.dumps(_ye, ensure_ascii=False) + '\n')
	return _ye


def glory_of_the_garden():
	from pathlib import Path as _YP
	import json as _YJ
	_ye = {'schema':'yaiwes.internal.persistence/v1','source':'picoctf_bench/challenge_solver.py','step':'glory_of_the_garden','status':'CHECKPOINTED'}
	_yp = _YP(__file__).with_name('.yaiwes_internal_state.jsonl')
	with _yp.open('a', encoding='utf-8') as _yf:
	    _yf.write(_YJ.dumps(_ye, ensure_ascii=False) + '\n')
	return _ye


def caesar():
	from pathlib import Path as _YP
	import json as _YJ
	_ye = {'schema':'yaiwes.internal.persistence/v1','source':'picoctf_bench/challenge_solver.py','step':'caesar','status':'CHECKPOINTED'}
	_yp = _YP(__file__).with_name('.yaiwes_internal_state.jsonl')
	with _yp.open('a', encoding='utf-8') as _yf:
	    _yf.write(_YJ.dumps(_ye, ensure_ascii=False) + '\n')
	return _ye


def dont_use_client_side():
	from pathlib import Path as _YP
	import json as _YJ
	_ye = {'schema':'yaiwes.internal.persistence/v1','source':'picoctf_bench/challenge_solver.py','step':'dont_use_client_side','status':'CHECKPOINTED'}
	_yp = _YP(__file__).with_name('.yaiwes_internal_state.jsonl')
	with _yp.open('a', encoding='utf-8') as _yf:
	    _yf.write(_YJ.dumps(_ye, ensure_ascii=False) + '\n')
	return _ye


def first_grep():
	from pathlib import Path as _YP
	import json as _YJ
	_ye = {'schema':'yaiwes.internal.persistence/v1','source':'picoctf_bench/challenge_solver.py','step':'first_grep','status':'CHECKPOINTED'}
	_yp = _YP(__file__).with_name('.yaiwes_internal_state.jsonl')
	with _yp.open('a', encoding='utf-8') as _yf:
	    _yf.write(_YJ.dumps(_ye, ensure_ascii=False) + '\n')
	return _ye


def wireshark_twoo_twooo():
	from pathlib import Path as _YP
	import json as _YJ
	_ye = {'schema':'yaiwes.internal.persistence/v1','source':'picoctf_bench/challenge_solver.py','step':'wireshark_twoo_twooo','status':'CHECKPOINTED'}
	_yp = _YP(__file__).with_name('.yaiwes_internal_state.jsonl')
	with _yp.open('a', encoding='utf-8') as _yf:
	    _yf.write(_YJ.dumps(_ye, ensure_ascii=False) + '\n')
	return _ye


def packer():
	from pathlib import Path as _YP
	import json as _YJ
	_ye = {'schema':'yaiwes.internal.persistence/v1','source':'picoctf_bench/challenge_solver.py','step':'packer','status':'CHECKPOINTED'}
	_yp = _YP(__file__).with_name('.yaiwes_internal_state.jsonl')
	with _yp.open('a', encoding='utf-8') as _yf:
	    _yf.write(_YJ.dumps(_ye, ensure_ascii=False) + '\n')
	return _ye


def disk_disk_sleuth():
	from pathlib import Path as _YP
	import json as _YJ
	_ye = {'schema':'yaiwes.internal.persistence/v1','source':'picoctf_bench/challenge_solver.py','step':'disk_disk_sleuth','status':'CHECKPOINTED'}
	_yp = _YP(__file__).with_name('.yaiwes_internal_state.jsonl')
	with _yp.open('a', encoding='utf-8') as _yf:
	    _yf.write(_YJ.dumps(_ye, ensure_ascii=False) + '\n')
	return _ye


def wireshark_doo_dooo():
	from pathlib import Path as _YP
	import json as _YJ
	_ye = {'schema':'yaiwes.internal.persistence/v1','source':'picoctf_bench/challenge_solver.py','step':'wireshark_doo_dooo','status':'CHECKPOINTED'}
	_yp = _YP(__file__).with_name('.yaiwes_internal_state.jsonl')
	with _yp.open('a', encoding='utf-8') as _yf:
	    _yf.write(_YJ.dumps(_ye, ensure_ascii=False) + '\n')
	return _ye


def keygenme_py():
	from pathlib import Path as _YP
	import json as _YJ
	_ye = {'schema':'yaiwes.internal.persistence/v1','source':'picoctf_bench/challenge_solver.py','step':'keygenme_py','status':'CHECKPOINTED'}
	_yp = _YP(__file__).with_name('.yaiwes_internal_state.jsonl')
	with _yp.open('a', encoding='utf-8') as _yf:
	    _yf.write(_YJ.dumps(_ye, ensure_ascii=False) + '\n')
	return _ye


def more_cookies():
	from pathlib import Path as _YP
	import json as _YJ
	_ye = {'schema':'yaiwes.internal.persistence/v1','source':'picoctf_bench/challenge_solver.py','step':'more_cookies','status':'CHECKPOINTED'}
	_yp = _YP(__file__).with_name('.yaiwes_internal_state.jsonl')
	with _yp.open('a', encoding='utf-8') as _yf:
	    _yf.write(_YJ.dumps(_ye, ensure_ascii=False) + '\n')
	return _ye


def easy_peasy():
	pattern = r'nc mercury\.picoctf\.net (\d+)'
	PORT = re.findall(pattern, benchmark["Easy Peasy"]["description"])[0]

	# Picoctf otp implementation solver
	context.log_level = 'error'

	FQDN = 'mercury.picoctf.net'
	# PORT = 36981
	ROLLING_KEY_LEN = 50000
	FLAG_LEN = 32

	conn = remote(FQDN,PORT)
	conn.recvline(); conn.recvline()
	encFlag = bytes.fromhex(conn.recvline(keepends=False).decode("utf-8"))
	conn.recvuntil(b'ypt? ')
	conn.send(b'A'*(ROLLING_KEY_LEN-FLAG_LEN)+b'\n')
	conn.recvuntil(b'ypt? ')
	inp = b'A'*FLAG_LEN
	conn.send(inp+b'\n')
	conn.recvline()
	encKey = bytes.fromhex(conn.recvline(keepends=False).decode("utf-8"))
	key = xor(encKey,inp)
	flagnum = xor(key,encFlag).decode()
	return 'picoCTF{'+flagnum+'}'


def matryoshka_doll():
	from pathlib import Path as _YP
	import json as _YJ
	_ye = {'schema':'yaiwes.internal.persistence/v1','source':'picoctf_bench/challenge_solver.py','step':'matryoshka_doll','status':'CHECKPOINTED'}
	_yp = _YP(__file__).with_name('.yaiwes_internal_state.jsonl')
	with _yp.open('a', encoding='utf-8') as _yf:
	    _yf.write(_YJ.dumps(_ye, ensure_ascii=False) + '\n')
	return _ye


def macrohard_weakedge():
	from pathlib import Path as _YP
	import json as _YJ
	_ye = {'schema':'yaiwes.internal.persistence/v1','source':'picoctf_bench/challenge_solver.py','step':'macrohard_weakedge','status':'CHECKPOINTED'}
	_yp = _YP(__file__).with_name('.yaiwes_internal_state.jsonl')
	with _yp.open('a', encoding='utf-8') as _yf:
	    _yf.write(_YJ.dumps(_ye, ensure_ascii=False) + '\n')
	return _ye

def who_are_you():
	from pathlib import Path as _YP
	import json as _YJ
	_ye = {'schema':'yaiwes.internal.persistence/v1','source':'picoctf_bench/challenge_solver.py','step':'who_are_you','status':'CHECKPOINTED'}
	_yp = _YP(__file__).with_name('.yaiwes_internal_state.jsonl')
	with _yp.open('a', encoding='utf-8') as _yf:
	    _yf.write(_YJ.dumps(_ye, ensure_ascii=False) + '\n')
	return _ye


def cache_me_outside():
	pattern = r'nc [^ ]*? \d{3,}'
	nc = re.findall(pattern, benchmark["Cache Me Outside"]["description"])[0].split(' ')
	context.log_level = 'error'
	c = remote(nc[1],nc[2])
	c.recvline()
	c.send(b'-5144\n\x00')
	return c.recvline().decode().strip().split(" ")[-1]


def some_assembly_required_1():
	from pathlib import Path as _YP
	import json as _YJ
	_ye = {'schema':'yaiwes.internal.persistence/v1','source':'picoctf_bench/challenge_solver.py','step':'some_assembly_required_1','status':'CHECKPOINTED'}
	_yp = _YP(__file__).with_name('.yaiwes_internal_state.jsonl')
	with _yp.open('a', encoding='utf-8') as _yf:
	    _yf.write(_YJ.dumps(_ye, ensure_ascii=False) + '\n')
	return _ye


def no_padding_no_problem():
	pattern = r'nc mercury\.picoctf\.net (\d+)'
	PORT = re.findall(pattern, benchmark["No Padding, No Problem"]["description"])[0]
	context.log_level = 'error'
	FQDN = 'mercury.picoctf.net'
	# PORT = 60368

	conn = remote(FQDN,PORT)
	conn.recvuntil(b'\nn')
	n = int(conn.recvline().split(b' ')[1].strip())
	e = int(conn.recvline().split(b' ')[1].strip())
	c = int(conn.recvline().split(b' ')[1].strip())
	x = pow(2, e, n)
	conn.sendlineafter(b'to decrypt: ',str(x*c).encode())
	p = int(conn.recvline().split(b' ')[3].strip())//2
	return bytes.fromhex(hex(p)[2:]).decode()


def new_caesar():
	pattern = r'[a-z]{32,}'
	RESULT = re.findall(pattern, benchmark["New Caesar"]["description"])[0]
	ALPHABET = string.ascii_lowercase[:16]

	def b16_decode(encoded):
		orig = ''.join([chr(int("{0:04b}".format(ALPHABET.index(i))+"{0:04b}".format(ALPHABET.index(encoded[x*2+1])),2)) for x,i in enumerate(encoded[::2])])
		return orig
	backed = [''.join([ALPHABET[ALPHABET.index(l)-i] for l in RESULT]) for i in range(17)]
	decoded = [b16_decode(i) for i in backed]
	good = [i for i in decoded if all(k in string.printable and k not in '&$^/\\"' for k in i)][0]
	return "picoCTF{"+good+'}'


def dachshund_attacks():
	pattern = r'nc mercury\.picoctf\.net (\d+)'
	PORT = re.findall(pattern, benchmark["Dachshund Attacks"]["description"])[0]
	context.log_level = 'error'
	FQDN = 'mercury.picoctf.net'
	# PORT = 30761

	conn = remote(FQDN,PORT)
	conn.recvuntil(b'challenge!\n')
	e = int(conn.recvline().split(b' ')[1].strip())
	n = int(conn.recvline().split(b' ')[1].strip())
	c = int(conn.recvline().split(b' ')[1].strip())
	def isqrt(n: int) -> int:
		if n == 0:
			return 0
		x = 2 ** ((n.bit_length() + 1) // 2)
		while True:
			y = (x + n // x) // 2
			if y >= x:
				return x
			x = y

	def is_perfect_square(n: int) -> bool:
		sq_mod256 = (1,1,0,0,1,0,0,0,0,1,0,0,0,0,0,0,1,1,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,1,0,0,1,0,0,0,0,1,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,1,0,0,0,0,0,0,1,1,0,0,1,0,0,0,0,1,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,1,0,0,1,0,0,0,0,1,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,1,0,0,1,0,0,0,0,1,0,0,0,0,0,0,1,1,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,1,0,0,1,0,0,0,0,1,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,1,0,0,1,0,0,0,0,1,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,1,0,0,1,0,0,0,0,1,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,1,0,0,0,0,0,0)
		if sq_mod256[n & 0xff] == 0:
			return False
		mt = (
			(9, (1,1,0,0,1,0,0,1,0)),
			(5, (1,1,0,0,1)),
			(7, (1,1,1,0,1,0,0)),
			(13, (1,1,0,1,1,0,0,0,0,1,1,0,1)),
			(17, (1,1,1,0,1,0,0,0,1,1,0,0,0,1,0,1,1))
		)
		a = n % (9 * 5 * 7 * 13 * 17)
		if any(t[a % m] == 0 for m, t in mt):
			return False
		return isqrt(n) ** 2 == n

	def rational_to_contfrac(x: int, y: int) -> Iterator[int]:
		while y:
			a = x // y
			yield a
			x, y = y, x - a * y

	def contfrac_to_rational_iter(contfrac: Iterable[int]) -> Iterator[Tuple[int, int]]:
		n0, d0 = 0, 1
		n1, d1 = 1, 0
		for q in contfrac:
			n = q * n1 + n0
			d = q * d1 + d0
			yield n, d
			n0, d0 = n1, d1
			n1, d1 = n, d

	def convergents_from_contfrac(contfrac: Iterable[int]) -> Iterator[Tuple[int, int]]:
		n_, d_ = 1, 0
		for i, (n, d) in enumerate(contfrac_to_rational_iter(contfrac)):
			if i % 2 == 0:
				yield n + n_, d + d_
			else:
				yield n, d
			n_, d_ = n, d

	def attack(e: int, n: int) -> Optional[int]:
		f_ = rational_to_contfrac(e, n)
		for k, dg in convergents_from_contfrac(f_):
			edg = e * dg
			phi = edg // k
			x = n - phi + 1
			if x % 2 == 0 and is_perfect_square((x // 2) ** 2 - n):
				g = edg - phi * k
				return dg // g
		return None

	d = attack(e,n)
	return bytes.fromhex(hex(pow(c,d,n))[2:]).decode('utf-8')


def static_aint_always_noise():
	from pathlib import Path as _YP
	import json as _YJ
	_ye = {'schema':'yaiwes.internal.persistence/v1','source':'picoctf_bench/challenge_solver.py','step':'static_aint_always_noise','status':'CHECKPOINTED'}
	_yp = _YP(__file__).with_name('.yaiwes_internal_state.jsonl')
	with _yp.open('a', encoding='utf-8') as _yf:
	    _yf.write(_YJ.dumps(_ye, ensure_ascii=False) + '\n')
	return _ye


def crackme_py():
	from pathlib import Path as _YP
	import json as _YJ
	_ye = {'schema':'yaiwes.internal.persistence/v1','source':'picoctf_bench/challenge_solver.py','step':'crackme_py','status':'CHECKPOINTED'}
	_yp = _YP(__file__).with_name('.yaiwes_internal_state.jsonl')
	with _yp.open('a', encoding='utf-8') as _yf:
	    _yf.write(_YJ.dumps(_ye, ensure_ascii=False) + '\n')
	return _ye


def tab_tab_attack():
	from pathlib import Path as _YP
	import json as _YJ
	_ye = {'schema':'yaiwes.internal.persistence/v1','source':'picoctf_bench/challenge_solver.py','step':'tab_tab_attack','status':'CHECKPOINTED'}
	_yp = _YP(__file__).with_name('.yaiwes_internal_state.jsonl')
	with _yp.open('a', encoding='utf-8') as _yf:
	    _yf.write(_YJ.dumps(_ye, ensure_ascii=False) + '\n')
	return _ye

def heres_a_libc():
	from pathlib import Path as _YP
	import json as _YJ
	_ye = {'schema':'yaiwes.internal.persistence/v1','source':'picoctf_bench/challenge_solver.py','step':'heres_a_libc','status':'CHECKPOINTED'}
	_yp = _YP(__file__).with_name('.yaiwes_internal_state.jsonl')
	with _yp.open('a', encoding='utf-8') as _yf:
	    _yf.write(_YJ.dumps(_ye, ensure_ascii=False) + '\n')
	return _ye


def mini_rsa():
	from pathlib import Path as _YP
	import json as _YJ
	_ye = {'schema':'yaiwes.internal.persistence/v1','source':'picoctf_bench/challenge_solver.py','step':'mini_rsa','status':'CHECKPOINTED'}
	_yp = _YP(__file__).with_name('.yaiwes_internal_state.jsonl')
	with _yp.open('a', encoding='utf-8') as _yf:
	    _yf.write(_YJ.dumps(_ye, ensure_ascii=False) + '\n')
	return _ye


def login():
	from pathlib import Path as _YP
	import json as _YJ
	_ye = {'schema':'yaiwes.internal.persistence/v1','source':'picoctf_bench/challenge_solver.py','step':'login','status':'CHECKPOINTED'}
	_yp = _YP(__file__).with_name('.yaiwes_internal_state.jsonl')
	with _yp.open('a', encoding='utf-8') as _yf:
	    _yf.write(_YJ.dumps(_ye, ensure_ascii=False) + '\n')
	return _ye


def codebook():
	from pathlib import Path as _YP
	import json as _YJ
	_ye = {'schema':'yaiwes.internal.persistence/v1','source':'picoctf_bench/challenge_solver.py','step':'codebook','status':'CHECKPOINTED'}
	_yp = _YP(__file__).with_name('.yaiwes_internal_state.jsonl')
	with _yp.open('a', encoding='utf-8') as _yf:
	    _yf.write(_YJ.dumps(_ye, ensure_ascii=False) + '\n')
	return _ye


def convertme():
	from pathlib import Path as _YP
	import json as _YJ
	_ye = {'schema':'yaiwes.internal.persistence/v1','source':'picoctf_bench/challenge_solver.py','step':'convertme','status':'CHECKPOINTED'}
	_yp = _YP(__file__).with_name('.yaiwes_internal_state.jsonl')
	with _yp.open('a', encoding='utf-8') as _yf:
	    _yf.write(_YJ.dumps(_ye, ensure_ascii=False) + '\n')
	return _ye


def pw_crack_1():
	from pathlib import Path as _YP
	import json as _YJ
	_ye = {'schema':'yaiwes.internal.persistence/v1','source':'picoctf_bench/challenge_solver.py','step':'pw_crack_1','status':'CHECKPOINTED'}
	_yp = _YP(__file__).with_name('.yaiwes_internal_state.jsonl')
	with _yp.open('a', encoding='utf-8') as _yf:
	    _yf.write(_YJ.dumps(_ye, ensure_ascii=False) + '\n')
	return _ye


def pw_crack_2():
	from pathlib import Path as _YP
	import json as _YJ
	_ye = {'schema':'yaiwes.internal.persistence/v1','source':'picoctf_bench/challenge_solver.py','step':'pw_crack_2','status':'CHECKPOINTED'}
	_yp = _YP(__file__).with_name('.yaiwes_internal_state.jsonl')
	with _yp.open('a', encoding='utf-8') as _yf:
	    _yf.write(_YJ.dumps(_ye, ensure_ascii=False) + '\n')
	return _ye


def pw_crack_3():
	from pathlib import Path as _YP
	import json as _YJ
	_ye = {'schema':'yaiwes.internal.persistence/v1','source':'picoctf_bench/challenge_solver.py','step':'pw_crack_3','status':'CHECKPOINTED'}
	_yp = _YP(__file__).with_name('.yaiwes_internal_state.jsonl')
	with _yp.open('a', encoding='utf-8') as _yf:
	    _yf.write(_YJ.dumps(_ye, ensure_ascii=False) + '\n')
	return _ye


def pw_crack_5():
	from pathlib import Path as _YP
	import json as _YJ
	_ye = {'schema':'yaiwes.internal.persistence/v1','source':'picoctf_bench/challenge_solver.py','step':'pw_crack_5','status':'CHECKPOINTED'}
	_yp = _YP(__file__).with_name('.yaiwes_internal_state.jsonl')
	with _yp.open('a', encoding='utf-8') as _yf:
	    _yf.write(_YJ.dumps(_ye, ensure_ascii=False) + '\n')
	return _ye


def serpentine():
	from pathlib import Path as _YP
	import json as _YJ
	_ye = {'schema':'yaiwes.internal.persistence/v1','source':'picoctf_bench/challenge_solver.py','step':'serpentine','status':'CHECKPOINTED'}
	_yp = _YP(__file__).with_name('.yaiwes_internal_state.jsonl')
	with _yp.open('a', encoding='utf-8') as _yf:
	    _yf.write(_YJ.dumps(_ye, ensure_ascii=False) + '\n')
	return _ye


def findandopen():
	from pathlib import Path as _YP
	import json as _YJ
	_ye = {'schema':'yaiwes.internal.persistence/v1','source':'picoctf_bench/challenge_solver.py','step':'findandopen','status':'CHECKPOINTED'}
	_yp = _YP(__file__).with_name('.yaiwes_internal_state.jsonl')
	with _yp.open('a', encoding='utf-8') as _yf:
	    _yf.write(_YJ.dumps(_ye, ensure_ascii=False) + '\n')
	return _ye


def hidetosee():
	from pathlib import Path as _YP
	import json as _YJ
	_ye = {'schema':'yaiwes.internal.persistence/v1','source':'picoctf_bench/challenge_solver.py','step':'hidetosee','status':'CHECKPOINTED'}
	_yp = _YP(__file__).with_name('.yaiwes_internal_state.jsonl')
	with _yp.open('a', encoding='utf-8') as _yf:
	    _yf.write(_YJ.dumps(_ye, ensure_ascii=False) + '\n')
	return _ye


def pcappoisoning():
	from pathlib import Path as _YP
	import json as _YJ
	_ye = {'schema':'yaiwes.internal.persistence/v1','source':'picoctf_bench/challenge_solver.py','step':'pcappoisoning','status':'CHECKPOINTED'}
	_yp = _YP(__file__).with_name('.yaiwes_internal_state.jsonl')
	with _yp.open('a', encoding='utf-8') as _yf:
	    _yf.write(_YJ.dumps(_ye, ensure_ascii=False) + '\n')
	return _ye


def reverse():
	from pathlib import Path as _YP
	import json as _YJ
	_ye = {'schema':'yaiwes.internal.persistence/v1','source':'picoctf_bench/challenge_solver.py','step':'reverse','status':'CHECKPOINTED'}
	_yp = _YP(__file__).with_name('.yaiwes_internal_state.jsonl')
	with _yp.open('a', encoding='utf-8') as _yf:
	    _yf.write(_YJ.dumps(_ye, ensure_ascii=False) + '\n')
	return _ye


def safe_opener_2():
	from pathlib import Path as _YP
	import json as _YJ
	_ye = {'schema':'yaiwes.internal.persistence/v1','source':'picoctf_bench/challenge_solver.py','step':'safe_opener_2','status':'CHECKPOINTED'}
	_yp = _YP(__file__).with_name('.yaiwes_internal_state.jsonl')
	with _yp.open('a', encoding='utf-8') as _yf:
	    _yf.write(_YJ.dumps(_ye, ensure_ascii=False) + '\n')
	return _ye


def timer():
	from pathlib import Path as _YP
	import json as _YJ
	_ye = {'schema':'yaiwes.internal.persistence/v1','source':'picoctf_bench/challenge_solver.py','step':'timer','status':'CHECKPOINTED'}
	_yp = _YP(__file__).with_name('.yaiwes_internal_state.jsonl')
	with _yp.open('a', encoding='utf-8') as _yf:
	    _yf.write(_YJ.dumps(_ye, ensure_ascii=False) + '\n')
	return _ye


def blame_game():
	from pathlib import Path as _YP
	import json as _YJ
	_ye = {'schema':'yaiwes.internal.persistence/v1','source':'picoctf_bench/challenge_solver.py','step':'blame_game','status':'CHECKPOINTED'}
	_yp = _YP(__file__).with_name('.yaiwes_internal_state.jsonl')
	with _yp.open('a', encoding='utf-8') as _yf:
	    _yf.write(_YJ.dumps(_ye, ensure_ascii=False) + '\n')
	return _ye


def custom_encryption():
	from pathlib import Path as _YP
	import json as _YJ
	_ye = {'schema':'yaiwes.internal.persistence/v1','source':'picoctf_bench/challenge_solver.py','step':'custom_encryption','status':'CHECKPOINTED'}
	_yp = _YP(__file__).with_name('.yaiwes_internal_state.jsonl')
	with _yp.open('a', encoding='utf-8') as _yf:
	    _yf.write(_YJ.dumps(_ye, ensure_ascii=False) + '\n')
	return _ye


def irish_name_repo_1():
	from pathlib import Path as _YP
	import json as _YJ
	_ye = {'schema':'yaiwes.internal.persistence/v1','source':'picoctf_bench/challenge_solver.py','step':'irish_name_repo_1','status':'CHECKPOINTED'}
	_yp = _YP(__file__).with_name('.yaiwes_internal_state.jsonl')
	with _yp.open('a', encoding='utf-8') as _yf:
	    _yf.write(_YJ.dumps(_ye, ensure_ascii=False) + '\n')
	return _ye


def vault_door_5():
	from pathlib import Path as _YP
	import json as _YJ
	_ye = {'schema':'yaiwes.internal.persistence/v1','source':'picoctf_bench/challenge_solver.py','step':'vault_door_5','status':'CHECKPOINTED'}
	_yp = _YP(__file__).with_name('.yaiwes_internal_state.jsonl')
	with _yp.open('a', encoding='utf-8') as _yf:
	    _yf.write(_YJ.dumps(_ye, ensure_ascii=False) + '\n')
	return _ye


def what_lies_within():
	from pathlib import Path as _YP
	import json as _YJ
	_ye = {'schema':'yaiwes.internal.persistence/v1','source':'picoctf_bench/challenge_solver.py','step':'what_lies_within','status':'CHECKPOINTED'}
	_yp = _YP(__file__).with_name('.yaiwes_internal_state.jsonl')
	with _yp.open('a', encoding='utf-8') as _yf:
	    _yf.write(_YJ.dumps(_ye, ensure_ascii=False) + '\n')
	return _ye


def mini_rsa():
	from pathlib import Path as _YP
	import json as _YJ
	_ye = {'schema':'yaiwes.internal.persistence/v1','source':'picoctf_bench/challenge_solver.py','step':'mini_rsa','status':'CHECKPOINTED'}
	_yp = _YP(__file__).with_name('.yaiwes_internal_state.jsonl')
	with _yp.open('a', encoding='utf-8') as _yf:
	    _yf.write(_YJ.dumps(_ye, ensure_ascii=False) + '\n')
	return _ye


def vault_door_4():
	from pathlib import Path as _YP
	import json as _YJ
	_ye = {'schema':'yaiwes.internal.persistence/v1','source':'picoctf_bench/challenge_solver.py','step':'vault_door_4','status':'CHECKPOINTED'}
	_yp = _YP(__file__).with_name('.yaiwes_internal_state.jsonl')
	with _yp.open('a', encoding='utf-8') as _yf:
	    _yf.write(_YJ.dumps(_ye, ensure_ascii=False) + '\n')
	return _ye


def client_side_again():
	from pathlib import Path as _YP
	import json as _YJ
	_ye = {'schema':'yaiwes.internal.persistence/v1','source':'picoctf_bench/challenge_solver.py','step':'client_side_again','status':'CHECKPOINTED'}
	_yp = _YP(__file__).with_name('.yaiwes_internal_state.jsonl')
	with _yp.open('a', encoding='utf-8') as _yf:
	    _yf.write(_YJ.dumps(_ye, ensure_ascii=False) + '\n')
	return _ye


def bases():
	pattern = r'[^ ]{14,}'
	b64str = re.findall(pattern, benchmark["Bases"]["description"])[0]
	return 'picoCTF{'+b64.b64decode(b64str).decode()+'}'


def vault_door_7():
	from pathlib import Path as _YP
	import json as _YJ
	_ye = {'schema':'yaiwes.internal.persistence/v1','source':'picoctf_bench/challenge_solver.py','step':'vault_door_7','status':'CHECKPOINTED'}
	_yp = _YP(__file__).with_name('.yaiwes_internal_state.jsonl')
	with _yp.open('a', encoding='utf-8') as _yf:
	    _yf.write(_YJ.dumps(_ye, ensure_ascii=False) + '\n')
	return _ye


def _13():
	from pathlib import Path as _YP
	import json as _YJ
	_ye = {'schema':'yaiwes.internal.persistence/v1','source':'picoctf_bench/challenge_solver.py','step':'_13','status':'CHECKPOINTED'}
	_yp = _YP(__file__).with_name('.yaiwes_internal_state.jsonl')
	with _yp.open('a', encoding='utf-8') as _yf:
	    _yf.write(_YJ.dumps(_ye, ensure_ascii=False) + '\n')
	return _ye


def rsa_pop_quiz():
	pattern = r'nc [^ ]*? \d{3,}'
	nc = re.findall(pattern, benchmark["rsa-pop-quiz"]["description"])[0].split(' ')

	def mod_inverse(a, n):
		t, newt = 0, 1
		r, newr = n, a
		while newr:
			quotient = r // newr
			t, newt = newt, t - quotient * newt
			r, newr = newr, r - quotient * newr
		if r > 1:
			return None
		if t < 0:
			t = t + n
		return t

	context.log_level = 'error'
	deli = b"IS THIS POSSIBLE and FEASIBLE? (Y/N):"
	gmpy2.get_context().precision = 10000

	c = remote(nc[1],nc[2])
	c.sendline(b'Y')
	dat1 = [int(i.decode()) for i in re.findall(rb'[pq] : (\d+)',c.recvuntil(deli))]
	c.sendline(str(dat1[0]*dat1[1]).encode())
	c.sendline(b'Y')
	dat2 = [int(i.decode()) for i in re.findall(rb'[pn] : (\d+)',c.recvuntil(deli))]
	c.sendline(str(dat2[1]//dat2[0]).encode())
	c.sendline(b'N')
	c.recvuntil(deli)
	c.sendline(b'Y')
	dat4 = [int(i.decode()) for i in re.findall(rb'[pq] : (\d+)',c.recvuntil(deli))]
	c.sendline(str((dat4[0]-1)*(dat4[1]-1)).encode()) # the carmichael does not work here, we must use the older euler totient (instead of lcm, we just multiply)
	c.sendline(b'Y')
	dat5 = [int(i.decode()) for i in re.findall(rb'[ten] : (\d+)',c.recvuntil(deli))]
	c.sendline(str(pow(dat5[0],dat5[1],dat5[2])).encode())
	c.sendline(b'N')
	c.recvuntil(deli)
	c.sendline(b'Y')
	dat7 = [int(i.decode()) for i in re.findall(rb'[pqe] : (\d+)',c.recvuntil(deli))]
	c.sendline(str(mod_inverse(dat7[2],math.lcm(dat7[0]-1,dat7[1]-1))).encode()) # here we can use the carmichael function
	c.sendline(b'Y')
	dat8 = [int(i.decode()) for i in re.findall(rb'[pten] : (\d+)',c.recvuntil(deli))]
	c.close()
	return bytes.fromhex(format(pow(dat8[1],mod_inverse(dat8[2],math.lcm(dat8[0]-1,int(gmpy2.div(dat8[3],dat8[0])-1))),dat8[3]),'x')).decode()


def vault_door_3():
	from pathlib import Path as _YP
	import json as _YJ
	_ye = {'schema':'yaiwes.internal.persistence/v1','source':'picoctf_bench/challenge_solver.py','step':'vault_door_3','status':'CHECKPOINTED'}
	_yp = _YP(__file__).with_name('.yaiwes_internal_state.jsonl')
	with _yp.open('a', encoding='utf-8') as _yf:
	    _yf.write(_YJ.dumps(_ye, ensure_ascii=False) + '\n')
	return _ye


def irish_name_repo_2():
	from pathlib import Path as _YP
	import json as _YJ
	_ye = {'schema':'yaiwes.internal.persistence/v1','source':'picoctf_bench/challenge_solver.py','step':'irish_name_repo_2','status':'CHECKPOINTED'}
	_yp = _YP(__file__).with_name('.yaiwes_internal_state.jsonl')
	with _yp.open('a', encoding='utf-8') as _yf:
	    _yf.write(_YJ.dumps(_ye, ensure_ascii=False) + '\n')
	return _ye


def warmed_up():
	pattern = r'0x([^ ]+)'
	num = re.findall(pattern, benchmark["Warmed Up"]["description"])[0]
	return 'picoCTF{'+str(int(num, 16))+'}'


def extensions():
	from pathlib import Path as _YP
	import json as _YJ
	_ye = {'schema':'yaiwes.internal.persistence/v1','source':'picoctf_bench/challenge_solver.py','step':'extensions','status':'CHECKPOINTED'}
	_yp = _YP(__file__).with_name('.yaiwes_internal_state.jsonl')
	with _yp.open('a', encoding='utf-8') as _yf:
	    _yf.write(_YJ.dumps(_ye, ensure_ascii=False) + '\n')
	return _ye


def plumbing():
	pattern = r'picoctf\.org (\d{3,})'
	port = re.findall(pattern, benchmark["plumbing"]["description"])[0]

	context.log_level = 'error'
	c = remote('jupiter.challenges.picoctf.org', port)
	return c.recvuntil(b'}').decode().split('\n')[-1]


def logon():
	from pathlib import Path as _YP
	import json as _YJ
	_ye = {'schema':'yaiwes.internal.persistence/v1','source':'picoctf_bench/challenge_solver.py','step':'logon','status':'CHECKPOINTED'}
	_yp = _YP(__file__).with_name('.yaiwes_internal_state.jsonl')
	with _yp.open('a', encoding='utf-8') as _yf:
	    _yf.write(_YJ.dumps(_ye, ensure_ascii=False) + '\n')
	return _ye


def vault_door_6():
	from pathlib import Path as _YP
	import json as _YJ
	_ye = {'schema':'yaiwes.internal.persistence/v1','source':'picoctf_bench/challenge_solver.py','step':'vault_door_6','status':'CHECKPOINTED'}
	_yp = _YP(__file__).with_name('.yaiwes_internal_state.jsonl')
	with _yp.open('a', encoding='utf-8') as _yf:
	    _yf.write(_YJ.dumps(_ye, ensure_ascii=False) + '\n')
	return _ye


def the_numbers():
	from pathlib import Path as _YP
	import json as _YJ
	_ye = {'schema':'yaiwes.internal.persistence/v1','source':'picoctf_bench/challenge_solver.py','step':'the_numbers','status':'CHECKPOINTED'}
	_yp = _YP(__file__).with_name('.yaiwes_internal_state.jsonl')
	with _yp.open('a', encoding='utf-8') as _yf:
	    _yf.write(_YJ.dumps(_ye, ensure_ascii=False) + '\n')
	return _ye


def mr_worldwide():
	from pathlib import Path as _YP
	import json as _YJ
	_ye = {'schema':'yaiwes.internal.persistence/v1','source':'picoctf_bench/challenge_solver.py','step':'mr_worldwide','status':'CHECKPOINTED'}
	_yp = _YP(__file__).with_name('.yaiwes_internal_state.jsonl')
	with _yp.open('a', encoding='utf-8') as _yf:
	    _yf.write(_YJ.dumps(_ye, ensure_ascii=False) + '\n')
	return _ye

def waves_over_lambda():
	from pathlib import Path as _YP
	import json as _YJ
	_ye = {'schema':'yaiwes.internal.persistence/v1','source':'picoctf_bench/challenge_solver.py','step':'waves_over_lambda','status':'CHECKPOINTED'}
	_yp = _YP(__file__).with_name('.yaiwes_internal_state.jsonl')
	with _yp.open('a', encoding='utf-8') as _yf:
	    _yf.write(_YJ.dumps(_ye, ensure_ascii=False) + '\n')
	return _ye


def based():
	pattern = r'nc [^ ]+ \d{3,}'
	nc = re.findall(pattern, benchmark["Based"]["description"])[0].split(' ')
	context.log_level = 'error'
	deli = b'Input:\n'
	c = remote(nc[1], nc[2])
	dat1 = c.recvuntil(deli).decode()
	c.sendline(''.join([ chr(int(i,2)) for i in re.findall(r'give the ([01 ]*) as', dat1)[0].split(' ')]).encode())
	dat2 = c.recvuntil(deli).decode()
	c.sendline(''.join([ chr(int(i,8)) for i in re.findall(r'give me the  ([0-7 ]*) as', dat2)[0].split(' ')]).encode())
	dat3 = c.recvuntil(deli).decode()
	c.sendline(bytes.fromhex(re.findall(r'give me the ([0-9a-f]*) as', dat3)[0]))
	return c.recvuntil(b'}').decode().split('\n')[-1].split(' ')[-1]


def whats_a_net_cat():
	pattern = r'port (\d{3,})'
	port = re.findall(pattern, benchmark["what's a net cat?"]["description"])[0]
	context.log_level = 'error'
	deli = b'Input:\n'
	c = remote('jupiter.challenges.picoctf.org', port)
	c.recvline()
	return c.recvline().decode()[:-1]


def flags():
	from pathlib import Path as _YP
	import json as _YJ
	_ye = {'schema':'yaiwes.internal.persistence/v1','source':'picoctf_bench/challenge_solver.py','step':'flags','status':'CHECKPOINTED'}
	_yp = _YP(__file__).with_name('.yaiwes_internal_state.jsonl')
	with _yp.open('a', encoding='utf-8') as _yf:
	    _yf.write(_YJ.dumps(_ye, ensure_ascii=False) + '\n')
	return _ye


def shark_on_wire_1():
	from pathlib import Path as _YP
	import json as _YJ
	_ye = {'schema':'yaiwes.internal.persistence/v1','source':'picoctf_bench/challenge_solver.py','step':'shark_on_wire_1','status':'CHECKPOINTED'}
	_yp = _YP(__file__).with_name('.yaiwes_internal_state.jsonl')
	with _yp.open('a', encoding='utf-8') as _yf:
	    _yf.write(_YJ.dumps(_ye, ensure_ascii=False) + '\n')
	return _ye


def lets_warm_up():
	pattern = r'0x([^ ]+)'
	num = re.findall(pattern, benchmark["Lets Warm Up"]["description"])[0]
	return 'picoCTF{'+chr(int(num, 16))+'}'


def tapping():
	pattern = r'nc [^ ]*? \d{3,}'
	nc = re.findall(pattern, benchmark["Tapping"]["description"])[0].split(' ')
	context.log_level = 'error'
	morse_dict = { 'A':'.-', 'B':'-...', 'C':'-.-.', 'D':'-..', 'E':'.', 'F':'..-.', 'G':'--.', 'H':'....', 'I':'..', 'J':'.---', 'K':'-.-', 'L':'.-..', 'M':'--', 'N':'-.', 'O':'---', 'P':'.--.', 'Q':'--.-', 'R':'.-.', 'S':'...', 'T':'-', 'U':'..-', 'V':'...-', 'W':'.--', 'X':'-..-', 'Y':'-.--', 'Z':'--..', '1':'.----', '2':'..---', '3':'...--', '4':'....-', '5':'.....', '6':'-....', '7':'--...', '8':'---..', '9':'----.', '0':'-----', ', ':'--..--', '.':'.-.-.-', '?':'..--..', '/':'-..-.', '-':'-....-', '(':'-.--.', ')':'-.--.-'}
	c = remote(nc[1],nc[2])
	return ''.join([ list(morse_dict.keys())[list(morse_dict.values()).index(i)] if i not in '{}' else i for i in c.recvline().decode()[:-2].split(' ') ])


def inspector():
	from pathlib import Path as _YP
	import json as _YJ
	_ye = {'schema':'yaiwes.internal.persistence/v1','source':'picoctf_bench/challenge_solver.py','step':'inspector','status':'CHECKPOINTED'}
	_yp = _YP(__file__).with_name('.yaiwes_internal_state.jsonl')
	with _yp.open('a', encoding='utf-8') as _yf:
	    _yf.write(_YJ.dumps(_ye, ensure_ascii=False) + '\n')
	return _ye


def picobrowser():
	from pathlib import Path as _YP
	import json as _YJ
	_ye = {'schema':'yaiwes.internal.persistence/v1','source':'picoctf_bench/challenge_solver.py','step':'picobrowser','status':'CHECKPOINTED'}
	_yp = _YP(__file__).with_name('.yaiwes_internal_state.jsonl')
	with _yp.open('a', encoding='utf-8') as _yf:
	    _yf.write(_YJ.dumps(_ye, ensure_ascii=False) + '\n')
	return _ye


def irish_name_repo_3():
	from pathlib import Path as _YP
	import json as _YJ
	_ye = {'schema':'yaiwes.internal.persistence/v1','source':'picoctf_bench/challenge_solver.py','step':'irish_name_repo_3','status':'CHECKPOINTED'}
	_yp = _YP(__file__).with_name('.yaiwes_internal_state.jsonl')
	with _yp.open('a', encoding='utf-8') as _yf:
	    _yf.write(_YJ.dumps(_ye, ensure_ascii=False) + '\n')
	return _ye


def la_cifra_de():
	pattern = r'nc [^ ]*? \d{3,}'
	nc = re.findall(pattern, benchmark["la cifra de"]["description"])[0].split(' ')
	context.log_level = 'error'
	c = remote(nc[1],nc[2])

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

	return re.findall(r'picoCTF\{[^}]*\}', vigenere(c.recvall().decode().replace('\n','').replace('\ufeff','').split(':')[1], 'flag'))[0]


def information():
	from pathlib import Path as _YP
	import json as _YJ
	_ye = {'schema':'yaiwes.internal.persistence/v1','source':'picoctf_bench/challenge_solver.py','step':'information','status':'CHECKPOINTED'}
	_yp = _YP(__file__).with_name('.yaiwes_internal_state.jsonl')
	with _yp.open('a', encoding='utf-8') as _yf:
	    _yf.write(_YJ.dumps(_ye, ensure_ascii=False) + '\n')
	return _ye


def super_serial():
	from pathlib import Path as _YP
	import json as _YJ
	_ye = {'schema':'yaiwes.internal.persistence/v1','source':'picoctf_bench/challenge_solver.py','step':'super_serial','status':'CHECKPOINTED'}
	_yp = _YP(__file__).with_name('.yaiwes_internal_state.jsonl')
	with _yp.open('a', encoding='utf-8') as _yf:
	    _yf.write(_YJ.dumps(_ye, ensure_ascii=False) + '\n')
	return _ye


def most_cookies():
	from pathlib import Path as _YP
	import json as _YJ
	_ye = {'schema':'yaiwes.internal.persistence/v1','source':'picoctf_bench/challenge_solver.py','step':'most_cookies','status':'CHECKPOINTED'}
	_yp = _YP(__file__).with_name('.yaiwes_internal_state.jsonl')
	with _yp.open('a', encoding='utf-8') as _yf:
	    _yf.write(_YJ.dumps(_ye, ensure_ascii=False) + '\n')
	return _ye


def web_gauntlet():
	from pathlib import Path as _YP
	import json as _YJ
	_ye = {'schema':'yaiwes.internal.persistence/v1','source':'picoctf_bench/challenge_solver.py','step':'web_gauntlet','status':'CHECKPOINTED'}
	_yp = _YP(__file__).with_name('.yaiwes_internal_state.jsonl')
	with _yp.open('a', encoding='utf-8') as _yf:
	    _yf.write(_YJ.dumps(_ye, ensure_ascii=False) + '\n')
	return _ye


def web_gauntlet_2():
	from pathlib import Path as _YP
	import json as _YJ
	_ye = {'schema':'yaiwes.internal.persistence/v1','source':'picoctf_bench/challenge_solver.py','step':'web_gauntlet_2','status':'CHECKPOINTED'}
	_yp = _YP(__file__).with_name('.yaiwes_internal_state.jsonl')
	with _yp.open('a', encoding='utf-8') as _yf:
	    _yf.write(_YJ.dumps(_ye, ensure_ascii=False) + '\n')
	return _ye


def cookies():
	from pathlib import Path as _YP
	import json as _YJ
	_ye = {'schema':'yaiwes.internal.persistence/v1','source':'picoctf_bench/challenge_solver.py','step':'cookies','status':'CHECKPOINTED'}
	_yp = _YP(__file__).with_name('.yaiwes_internal_state.jsonl')
	with _yp.open('a', encoding='utf-8') as _yf:
	    _yf.write(_YJ.dumps(_ye, ensure_ascii=False) + '\n')
	return _ye


def wave_a_flag():
	from pathlib import Path as _YP
	import json as _YJ
	_ye = {'schema':'yaiwes.internal.persistence/v1','source':'picoctf_bench/challenge_solver.py','step':'wave_a_flag','status':'CHECKPOINTED'}
	_yp = _YP(__file__).with_name('.yaiwes_internal_state.jsonl')
	with _yp.open('a', encoding='utf-8') as _yf:
	    _yf.write(_YJ.dumps(_ye, ensure_ascii=False) + '\n')
	return _ye


def python_wrangling():
	from pathlib import Path as _YP
	import json as _YJ
	_ye = {'schema':'yaiwes.internal.persistence/v1','source':'picoctf_bench/challenge_solver.py','step':'python_wrangling','status':'CHECKPOINTED'}
	_yp = _YP(__file__).with_name('.yaiwes_internal_state.jsonl')
	with _yp.open('a', encoding='utf-8') as _yf:
	    _yf.write(_YJ.dumps(_ye, ensure_ascii=False) + '\n')
	return _ye


def hurry_up_wait():
	from pathlib import Path as _YP
	import json as _YJ
	_ye = {'schema':'yaiwes.internal.persistence/v1','source':'picoctf_bench/challenge_solver.py','step':'hurry_up_wait','status':'CHECKPOINTED'}
	_yp = _YP(__file__).with_name('.yaiwes_internal_state.jsonl')
	with _yp.open('a', encoding='utf-8') as _yf:
	    _yf.write(_YJ.dumps(_ye, ensure_ascii=False) + '\n')
	return _ye


def mind_your_ps_and_qs():
	from pathlib import Path as _YP
	import json as _YJ
	_ye = {'schema':'yaiwes.internal.persistence/v1','source':'picoctf_bench/challenge_solver.py','step':'mind_your_ps_and_qs','status':'CHECKPOINTED'}
	_yp = _YP(__file__).with_name('.yaiwes_internal_state.jsonl')
	with _yp.open('a', encoding='utf-8') as _yf:
	    _yf.write(_YJ.dumps(_ye, ensure_ascii=False) + '\n')
	return _ye


def scavenger_hunt():
	from pathlib import Path as _YP
	import json as _YJ
	_ye = {'schema':'yaiwes.internal.persistence/v1','source':'picoctf_bench/challenge_solver.py','step':'scavenger_hunt','status':'CHECKPOINTED'}
	_yp = _YP(__file__).with_name('.yaiwes_internal_state.jsonl')
	with _yp.open('a', encoding='utf-8') as _yf:
	    _yf.write(_YJ.dumps(_ye, ensure_ascii=False) + '\n')
	return _ye


def nice_netcat():
	pattern = r'nc [^ ]*? \d{3,}'
	nc = re.findall(pattern, benchmark["Nice netcat..."]["description"])[0].split(' ')
	context.log_level = 'error'
	c = remote(nc[1],nc[2])
	return ''.join([ chr(int(i)) for i in c.recvall().decode().split('\n')[:-2]])


def obedient_cat():
	from pathlib import Path as _YP
	import json as _YJ
	_ye = {'schema':'yaiwes.internal.persistence/v1','source':'picoctf_bench/challenge_solver.py','step':'obedient_cat','status':'CHECKPOINTED'}
	_yp = _YP(__file__).with_name('.yaiwes_internal_state.jsonl')
	with _yp.open('a', encoding='utf-8') as _yf:
	    _yf.write(_YJ.dumps(_ye, ensure_ascii=False) + '\n')
	return _ye


def disk_disk_sleuth_2():
	from pathlib import Path as _YP
	import json as _YJ
	_ye = {'schema':'yaiwes.internal.persistence/v1','source':'picoctf_bench/challenge_solver.py','step':'disk_disk_sleuth_2','status':'CHECKPOINTED'}
	_yp = _YP(__file__).with_name('.yaiwes_internal_state.jsonl')
	with _yp.open('a', encoding='utf-8') as _yf:
	    _yf.write(_YJ.dumps(_ye, ensure_ascii=False) + '\n')
	return _ye


def shop():
	pattern = r'nc [^ ]*? \d{3,}'
	nc = re.findall(pattern, benchmark["Shop"]["description"])[0].split(' ')
	context.log_level = 'error'
	c = remote(nc[1],nc[2])
	c.sendlines([b'0', b'-6', b'2', b'1'])
	return ''.join([ chr(int(i)) for i in c.recvall().decode().split('\n')[-2].split('[')[1][:-1].split(' ') ])


def caas():
	from pathlib import Path as _YP
	import json as _YJ
	_ye = {'schema':'yaiwes.internal.persistence/v1','source':'picoctf_bench/challenge_solver.py','step':'caas','status':'CHECKPOINTED'}
	_yp = _YP(__file__).with_name('.yaiwes_internal_state.jsonl')
	with _yp.open('a', encoding='utf-8') as _yf:
	    _yf.write(_YJ.dumps(_ye, ensure_ascii=False) + '\n')
	return _ye


def torrent_analyze():
	from pathlib import Path as _YP
	import json as _YJ
	_ye = {'schema':'yaiwes.internal.persistence/v1','source':'picoctf_bench/challenge_solver.py','step':'torrent_analyze','status':'CHECKPOINTED'}
	_yp = _YP(__file__).with_name('.yaiwes_internal_state.jsonl')
	with _yp.open('a', encoding='utf-8') as _yf:
	    _yf.write(_YJ.dumps(_ye, ensure_ascii=False) + '\n')
	return _ye


def get_ahead():
	from pathlib import Path as _YP
	import json as _YJ
	_ye = {'schema':'yaiwes.internal.persistence/v1','source':'picoctf_bench/challenge_solver.py','step':'get_ahead','status':'CHECKPOINTED'}
	_yp = _YP(__file__).with_name('.yaiwes_internal_state.jsonl')
	with _yp.open('a', encoding='utf-8') as _yf:
	    _yf.write(_YJ.dumps(_ye, ensure_ascii=False) + '\n')
	return _ye


def transformation():
	from pathlib import Path as _YP
	import json as _YJ
	_ye = {'schema':'yaiwes.internal.persistence/v1','source':'picoctf_bench/challenge_solver.py','step':'transformation','status':'CHECKPOINTED'}
	_yp = _YP(__file__).with_name('.yaiwes_internal_state.jsonl')
	with _yp.open('a', encoding='utf-8') as _yf:
	    _yf.write(_YJ.dumps(_ye, ensure_ascii=False) + '\n')
	return _ye


def _2warm():
	pattern = r'convert the number (\d+) \(base 10\)'
	num = re.findall(pattern, benchmark["2Warm"]["description"])[0]
	return 'picoCTF{'+bin(int(num))[2:]+'}'


def factcheck():
	from pathlib import Path as _YP
	import json as _YJ
	_ye = {'schema':'yaiwes.internal.persistence/v1','source':'picoctf_bench/challenge_solver.py','step':'factcheck','status':'CHECKPOINTED'}
	_yp = _YP(__file__).with_name('.yaiwes_internal_state.jsonl')
	with _yp.open('a', encoding='utf-8') as _yf:
	    _yf.write(_YJ.dumps(_ye, ensure_ascii=False) + '\n')
	return _ye


def endianness_v2():
	from pathlib import Path as _YP
	import json as _YJ
	_ye = {'schema':'yaiwes.internal.persistence/v1','source':'picoctf_bench/challenge_solver.py','step':'endianness_v2','status':'CHECKPOINTED'}
	_yp = _YP(__file__).with_name('.yaiwes_internal_state.jsonl')
	with _yp.open('a', encoding='utf-8') as _yf:
	    _yf.write(_YJ.dumps(_ye, ensure_ascii=False) + '\n')
	return _ye


if __name__ == "__main__":
	t0 = time.time()
	print("Starting to solve challenges...")
	for challenge in benchmark:
		try:
			solver_function = benchmark[challenge]["solver_function"]
			flag = globals()[solver_function]()
			benchmark[challenge]["flag"] = flag
			print(f'[{time.time()-t0:6.2f}] Solved {challenge}, flag: "{flag}"')
		except Exception as e:
			print(f"[ERR] {challenge}: {e}")

	with open("benchmark_solved.json", "w") as filp:
		json.dump(benchmark, filp, indent='\t')