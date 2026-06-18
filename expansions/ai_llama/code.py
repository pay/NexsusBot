# coding: utf-8
# Porting Python3 by: paijo.ahmad@jabber.ru

#  Nexsus Safety — AI Expansion (llama.cpp / tinyllama)
# exp_name = "ai_llama" # /code.py v.x2

import subprocess
import os
import platform

class expansion_temp(expansion):

	def __init__(self, name):
		expansion.__init__(self, name)
		# Auto-detect platform dan set path sesuai
		self._setup_paths()

	# ── Konfigurasi default ──────────────────────────────────────
	MAX_TOKENS = 200    # jumlah token output maksimal
	THREADS    = 4      # jumlah CPU threads
	TIMEOUT    = 90     # timeout subprocess (detik)
	MAX_INPUT  = 500    # batas panjang input user (karakter)

	# Noise yang perlu difilter dari output llama-cli
	NOISE = (
		"[ Prompt:", "[ Generation:", "[Prompt:", "[Generation:",
		"available commands:", "build      :", "model      :",
		"modalities :", "/exit", "/regen", "/clear", "/read", "/glob",
	)

	def _setup_paths(self):
		"""Auto-detect platform: Termux vs WSL/Linux."""
		termux_home = "/data/data/com.termux/files/home"
		if os.path.isdir(termux_home):
			# ── Termux (Android) ───────────────────────────────
			self.MODEL_PATH = "%s/models/tinyllama.gguf" % termux_home
			self.LLAMA_CLI  = "llama-cli"  # sudah di PATH setelah pkg install
			self.THREADS    = 4
		else:
			# ── WSL / Linux ────────────────────────────────────
			home = os.path.expanduser("~")
			self.MODEL_PATH = "%s/models/tinyllama.gguf" % home
			# Coba beberapa lokasi umum build llama.cpp
			for candidate in (
				"%s/llama.cpp/build/bin/llama-cli" % home,
				"/usr/local/bin/llama-cli",
				"llama-cli",
			):
				if os.path.isfile(candidate) or candidate == "llama-cli":
					self.LLAMA_CLI = candidate
					break
			self.THREADS = os.cpu_count() or 4

	AnsBase = (
		"⚠️ Tulis pertanyaan setelah perintah.",        # 0
		"⏳ AI timeout — coba lagi.",                    # 1
		"❌ llama-cli tidak ditemukan. Cek instalasi.",  # 2
		"❌ Model tidak ditemukan:\n  %s",               # 3
		"❌ Error AI: %s",                               # 4
		"❌ Input terlalu panjang (maks %d karakter).",  # 5
		"\U0001f916 AI sedang memproses...",             # 6
	)

	def _clean_output(self, raw, prompt):
		"""Filter noise dari output llama-cli dan hapus ulangan prompt."""
		lines = []
		for line in raw.splitlines():
			s = line.strip()
			if not s or s == ">":
				continue
			if any(s.startswith(n) for n in self.NOISE):
				continue
			lines.append(s)
		out = "\n".join(lines).strip()
		# Hapus ulangan prompt di awal (llama-cli kadang echo prompt)
		if out.startswith(prompt):
			out = out[len(prompt):].strip()
		return out

	def _tanya_llama(self, prompt):
		"""Query llama.cpp, return teks jawaban atau pesan error."""
		if not os.path.isfile(self.MODEL_PATH):
			return self.AnsBase[3] % self.MODEL_PATH
		if len(prompt) > self.MAX_INPUT:
			return self.AnsBase[5] % self.MAX_INPUT
		try:
			cmd = [
				self.LLAMA_CLI,
				"-m", self.MODEL_PATH,
				"-p", prompt,
				"-n", str(self.MAX_TOKENS),
				"-t", str(self.THREADS),
				"--log-disable",
				"-no-cnv",
			]
			result = subprocess.run(
				cmd,
				capture_output=True,
				text=True,
				timeout=self.TIMEOUT,
			)
			out = self._clean_output(result.stdout, prompt)
			if out:
				return out
			err = result.stderr.strip()
			if err:
				return self.AnsBase[4] % err[:200]
			return self.AnsBase[4] % "no output"
		except subprocess.TimeoutExpired:
			return self.AnsBase[1]
		except FileNotFoundError:
			return self.AnsBase[2]
		except Exception as e:
			return self.AnsBase[4] % str(e)[:200]

	# ── Commands ─────────────────────────────────────────────────

	def command_ai(self, stype, source, body, disp):
		"""ai <pertanyaan> — tanya AI lokal (llama.cpp)."""
		body = body.strip()
		if not body:
			return Answer(self.AnsBase[0], stype, source, disp)
		jawaban = self._tanya_llama(body)
		Answer(jawaban, stype, source, disp)

	def command_aiconfig(self, stype, source, body, disp):
		"""
		aiconfig              — tampilkan konfigurasi
		aiconfig model=<path> — ganti path model
		aiconfig tokens=<n>   — jumlah token output
		aiconfig threads=<n>  — jumlah CPU threads
		aiconfig timeout=<n>  — timeout detik
		aiconfig binary=<path>— path llama-cli
		"""
		if not body.strip():
			info = (
				"\n  Platform : %s\n"
				"  Binary   : %s\n"
				"  Model    : %s\n"
				"  Tokens   : %d\n"
				"  Threads  : %d\n"
				"  Timeout  : %ds\n"
				"  Model OK : %s"
			) % (
				"Termux" if os.path.isdir("/data/data/com.termux") else "WSL/Linux",
				self.LLAMA_CLI,
				self.MODEL_PATH,
				self.MAX_TOKENS,
				self.THREADS,
				self.TIMEOUT,
				"✅" if os.path.isfile(self.MODEL_PATH) else "❌ tidak ditemukan",
			)
			return Answer(info, stype, source, disp)

		changed = []
		for part in body.split():
			if "=" not in part:
				continue
			key, val = part.split("=", 1)
			key = key.lower().strip()
			val = val.strip()
			if   key == "model"             : self.MODEL_PATH = val;            changed.append("model → %s" % val)
			elif key == "binary"            : self.LLAMA_CLI  = val;            changed.append("binary → %s" % val)
			elif key == "tokens"  and val.isdigit(): self.MAX_TOKENS = int(val); changed.append("tokens → %s" % val)
			elif key == "threads" and val.isdigit(): self.THREADS    = int(val); changed.append("threads → %s" % val)
			elif key == "timeout" and val.isdigit(): self.TIMEOUT    = int(val); changed.append("timeout → %ss" % val)

		Answer(("Updated: " + ", ".join(changed)) if changed else AnsBase[2],
		       stype, source, disp)

	commands = (
		(command_ai,       "ai",       1,),  # semua user
		(command_aiconfig, "aiconfig", 7,),  # admin only
	)