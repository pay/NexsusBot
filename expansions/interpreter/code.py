# coding: utf-8
# Porting Python3 by: paijo.ahmad@jabber.ru

#  BlackSmith mark.2
# exp_name = "interpreter" # /code.py v.x12 — ported to Python 3
#  Code © (2009-2013) by WitcherGeralt [alkorgun@gmail.com]

import subprocess as _subprocess
import os as _os

class expansion_temp(expansion):

	def __init__(self, name):
		expansion.__init__(self, name)

	opts = ("-l", "-r", "-s")

	opt_locals = opts[0]
	opt_result  = opts[1]
	opt_silent  = opts[2]

	def command_eval(self, stype, source, body, disp):
		silent = False
		if body:
			args = body.split(None, 1)
			if len(args) == 2 and args[0].lower() == self.opt_silent:
				silent = True
				body = args[1]
			try:
				answer = str(eval(str(body)))
				if not answer.strip():
					answer = repr(answer)
			except Exception:
				answer = "%s - %s" % exc_info()
		else:
			answer = "No arguments."
		if not silent:
			Answer(answer, stype, source, disp)

	def command_exec(self, stype, source, body, disp):
		silent = False
		if body:
			opts = set()
			while len(opts) < 3:
				args = body.split(None, 1)
				if len(args) != 2:
					break
				temp = args[0].lower()
				if temp not in self.opts:
					break
				opts.add(temp)
				body = args[1]
			if not all(temp in opts for temp in self.opts[-2:]):
				if self.opt_silent in opts:
					silent = True
				ns = locals() if self.opt_locals in opts else globals()
				try:
					exec(str(body + chr(10)), ns)
				except Exception:
					answer = "%s - %s" % exc_info()
				else:
					try:
						answer = str(ns.get("result", "")) if self.opt_result in opts else "Done."
					except Exception as exc:
						answer = str(exc)
			else:
				answer = "Invalid options."
		else:
			answer = "No arguments."
		if not silent:
			Answer(answer, stype, source, disp)

	def command_sh(self, stype, source, body, disp):
		if body:
			try:
				result = _subprocess.run(
					body, shell=True, capture_output=True, timeout=15,
					encoding="utf-8", errors="replace"
				)
				answer = (result.stdout or result.stderr or "").strip()
				if not answer:
					answer = "Done."
			except _subprocess.TimeoutExpired:
				answer = "Timeout."
			except Exception as e:
				answer = str(e)
		else:
			answer = "No arguments."
		Answer(answer, stype, source, disp)

	taboo = chr(42) * 2

	compile_math = compile__(r"([0-9]|[\+\-\(\/\*\)\%\^\.])")

	def command_calc(self, stype, source, body, disp):
		if body:
			if self.taboo not in body and len(body) <= 32:
				if not self.compile_math.sub("", body).strip():
					try:
						answer = str(eval(body))
					except ZeroDivisionError:
						answer = "+∞"
					except Exception:
						answer = "Error."
				else:
					answer = "Invalid expression."
			else:
				answer = "Invalid expression."
		else:
			answer = "No arguments."
		Answer(answer, stype, source, disp)

	commands = (
		(command_eval, "eval", 8,),
		(command_exec, "exec", 8,),
		(command_sh,   "sh",   8,),
		(command_calc, "calc", 2,)
	)