# coding: utf-8
# Porting Python3 by: paijo.ahmad@jabber.ru

#  BlackSmith mark.2 → Nexsus Port (Python 3 / Slixmpp)
# exp_name = "alias" # /code.py v.x3 (ported)
#  Id: 35~3c
#  Original © (2012-2013) by WitcherGeralt [alkorgun@gmail.com]
#  Ported to Python 3 / slixmpp by Nexsus Project 2026
#
# CATATAN PORTING (baca sebelum dipakai):
#  - Fitur auto-fetch version/capabilities (XEP-0092/0115) saat user join
#    DIHILANGKAN sesuai kesepakatan. Alias event "join" tetap trigger, tapi
#    variabel version/name/os/caps/caps_ver akan kosong (None). Event
#    "version" (trigger terpisah setelah IQ version-fetch) TIDAK ada lagi.
#  - xmpp_raise() (NodeProcessed dari xmpppy) dihapus — tidak ada padanan
#    langsung di Slixmpp untuk skenario ini. Efek sampingnya: setelah macro
#    dieksekusi, alias event "message" tetap diproses juga untuk pesan yang
#    sama (redundan tapi tidak merusak).
#  - database() → Database (class bawaan NexsusBot, fungsinya sama).
#  - cefile() dipertahankan sebagai no-op (Termux modern unicode-safe).
#  - Membutuhkan 2 patch di NexsusBot.py (sudah diterapkan by user):
#      1) "05eh" mengirim scode asli (301/307) alih-alih None.
#      2) Macro.__contains__ dipanggil dengan tuple (command, chat).
#  - Handler "06eh"/"07eh"/"08eh" (nick/role/status change) didaftarkan,
#    TAPI belum dikonfirmasi apakah core NexsusBot.py benar-benar memanggil
#    call_efunctions untuk ketiga event ini. Jika core tidak memanggilnya,
#    alias event nick/role/status tidak akan pernah trigger (bukan error,
#    cuma tidak aktif). Cek dengan:
#      grep -n 'call_efunctions("06eh"\|call_efunctions("07eh"\|call_efunctions("08eh"' NexsusBot.py

from random import randrange, choice


def sub_desc(body, ls, sub=str()):
    if isinstance(ls, dict):
        for x, z in list(ls.items()):
            body = body.replace(x, z)
    else:
        for x in ls:
            if isinstance(x, (list, tuple)):
                if len(x) > 1:
                    body = body.replace(*x[:2])
                else:
                    body = body.replace(x[0], sub)
            else:
                body = body.replace(x, sub)
    return body


def cefile(path):
    # Fix: pengaman nama file untuk filesystem ASCII-only lama.
    # Termux modern (Android) sudah unicode-safe → no-op aman.
    return path


class expansion_temp(expansion):

    def __init__(self, name):
        # Fix: check_sqlite() dihapus — tidak ada di Nexus, SQLite built-in.
        expansion.__init__(self, name)

    On = True

    AliasFile = dynamic % ("alias.db")
    ChatAliasFile = "alias.db"
    MacroHelpBase = dynamic % ("macro.db")
    ChatMacroHelpBase = "macro.db"
    HelpFile = "alias.%s.app"

    alias, macro, command, set, message, null = "alias", "macro", "command", "set", "message", "null"

    Template = {
        "macro": {},
        "message": {},
        "/me": {},
        "subject": {},
        "join": {},
        "leave": {},
        "ban": {},
        "kick": {},
        "nick": {},
        "role": {},
        "status": {}
    }

    AliasDesc = Template.copy()
    ChatAliasDesc = {}

    Taboo = {}

    Cache = {}

    conds = {
        "null": None,
        "is": lambda attr, clause: (clause == attr),
        "is_not": lambda attr, clause: (clause != attr),
        "starts": lambda attr, clause: attr.startswith(clause),
        "not_starts": lambda attr, clause: not attr.startswith(clause),
        "ends": lambda attr, clause: attr.endswith(clause),
        "not_ends": lambda attr, clause: not attr.endswith(clause),
        "cont": lambda attr, clause: (clause in attr),
        "not_cont": lambda attr, clause: (clause not in attr),
        "in": lambda attr, clause: (attr in clause),
        "not_in": lambda attr, clause: (attr not in clause),
        "len_more": lambda attr, clause: (len(attr) > clause),
        "len_less": lambda attr, clause: (len(attr) < clause),
        "re": lambda attr, clause: clause.search(attr)
    }

    flags = ("strip", "lower", "layout")

    compile_rand = compile__(r"\$rand\((\d+?),\s*(\d+?)\)")
    compile_rand_user = compile__(r"\$rand_user")
    compile_rand_choice = compile__(r"\$rand\(\[(.+?)\]\)", 16)

    rand_user = "$rand_user"
    sep = chr(124) * 2

    risky = ("outcast", "kick", "visitor")

    CharsCY = "етуоранкхсвм"
    CharsLA = "etyopahkxcbm"

    eqMap = []
    for numb, char in enumerate(CharsLA):
        eqMap.append((CharsCY[numb], char))
    eqMap = tuple(eqMap)

    del CharsCY, CharsLA

    compile_quote = compile__("<!--(.*?)-->", 16)

    attrsDesc = {
        "message": ("body", "jid", "nick", "role", "stype"),
        "/me": ("body", "jid", "nick", "role"),
        "subject": ("body", "nick"),
        "join": ("caps", "caps_ver", "jid", "nick", "role", "show", "status"),
        "leave": ("jid", "nick", "role", "reason"),
        "ban": ("jid", "nick", "role", "reason"),
        "kick": ("jid", "nick", "role", "reason"),
        "nick": ("jid", "nick", "old_nick", "role"),
        "role": ("jid", "nick", "role"),
        "status": ("jid", "nick", "role", "show", "status")
    }

    validDesc = {
        "alias": ("\t", "\n", "\r", " ", "(chat)s", "(nick)s"),
        "macro": ("(aff)s", "(arg0)s", "(arg1)s", "(arg2)s", "(arg3)s", "(args)s", "(jid)s", "(role)s", "(stype)s"),
        "message": ("(body)s", "(jid)s", "(role)s"),
        "/me": ("(body)s", "(jid)s", "(role)s"),
        "subject": ("(body)s",),
        "join": ("(caps)s", "(caps_ver)s", "(jid)s", "(role)s", "(show)s", "(status)s"),
        "leave": ("(jid)s", "(role)s", "(reason)s"),
        "ban": ("(jid)s", "(role)s", "(reason)s"),
        "kick": ("(jid)s", "(role)s", "(reason)s"),
        "nick": ("(jid)s", "(old_nick)s", "(role)s"),
        "role": ("(jid)s", "(role)s"),
        "status": ("(jid)s", "(role)s", "(show)s", "(status)s")
    }

    cmd_names = ()
    eqFuncs = {}

    # ── util ──────────────────────────────────────────────────

    def sub_rand(self, obj):
        try:
            number = str(randrange(*[int(numb) for numb in obj.groups()]))
        except Exception:
            number = "0"
        return number

    sub_rand_choice = lambda self, obj: choice((obj.group(1)).split(self.sep))

    def rand(self, chat, body):
        body = self.compile_rand_choice.sub(self.sub_rand_choice, body)
        body = self.compile_rand.sub(self.sub_rand, body)
        if chat and self.rand_user in body:
            ls = chat.get_nicks()
            body = self.compile_rand_user.sub(lambda obj: choice(ls), body)
        return body

    def four_args(self, ls, args):
        while len(args) < 4:
            args.append(ls.pop())
        return args

    def _layout(self, attr):
        return sub_desc(attr.lower(), self.eqMap)

    def prepare(self, attr, flags):
        if not flags:
            return attr
        attr = str(attr)
        if not self.eqFuncs:
            self.eqFuncs = {
                self.flags[0]: str.strip,
                self.flags[1]: str.lower,
                self.flags[2]: self._layout
            }
        for flag in flags:
            attr = self.eqFuncs[flag](attr)
        return attr

    # ── funcs (moderasi) — dipetakan di sini, bukan attribute kelas,
    #    supaya menghindari resolusi sConf.xxx saat class body dieksekusi
    #    sebelum sConf full ready ──────────────────────────────

    @property
    def funcs(self):
        return {
            "outcast": (sConf.outcast, sBase[11]),
            "none": (sConf.none, sBase[11]),
            "member": (sConf.member, sBase[11]),
            "admin": (sConf.admin, sBase[11]),
            "owner": (sConf.owner, sBase[11]),
            "kick": (sConf.kick, sBase[12]),
            "visitor": (sConf.visitor, sBase[12]),
            "participant": (sConf.participant, sBase[12]),
            "moder": (sConf.moder, sBase[12])
        }

    # ── macro engine (dipasang ke global Macro) ──────────────

    def execute_macro(self, chat, isConf, command, body, access, args):
        stype, source, nick, args, disp = args
        source = (source, chat, nick)
        answer = None
        if enough_access(chat, nick, access):
            cmd = Cmds[command]
            if cmd.isAvalable and cmd.handler:
                if isConf:
                    user = Chats[chat].get_user(nick)
                    (aff, role), jid = user.role, user.source
                else:
                    (aff, role), jid = ("none",) * 2, None
                arg0, arg1, arg2, arg3 = self.four_args([role, aff, stype, chat], args.split(None, 3))
                body = self.rand(Chats[chat] if isConf else None, body % vars())
                Info["cmd"].plus()
                cmd.handler(cmd.exp, stype, source, body, disp)
                cmd.numb.plus()
                if jid:
                    cmd.desc.add(jid)
            else:
                answer = self.AnsBase[19] % (self.name)
        else:
            answer = self.AnsBase[10]
        if answer is not None:
            Answer(answer, stype, source, disp)

    def __call__(self, chat, isConf, macro, *args):
        if not macro:
            return
        desc = self.AliasDesc[self.macro].get(macro)
        if not desc and isConf and chat in self.ChatAliasDesc:
            desc = self.ChatAliasDesc[chat][self.macro].get(macro)
        if desc:
            command, body, access = desc
            if command in Cmds:
                if not isConf or (command not in Chats[chat].oCmds and
                                   macro not in self.Taboo.get(chat, [])):
                    sThread(self.macro, self.execute_macro, (chat, isConf, command, body, access, args), macro)

    def __contains__(self, ls):
        # Dipanggil dari core sebagai (command, chat) not in Macro
        try:
            macro, chat = ls
        except Exception:
            return False
        if macro in self.AliasDesc[self.macro]:
            return True
        return chat in self.ChatAliasDesc and macro in self.ChatAliasDesc[chat][self.macro]

    def execute(self, chat, desc, Vars):
        atype, func, body = desc
        body = self.rand(chat, body % Vars)
        if atype == self.command:
            if func in Cmds and func not in chat.oCmds:
                cmd = Cmds[func]
                if cmd.isAvalable and cmd.handler:
                    source = ("%s/%s" % (chat.name, chat.nick), chat.name, chat.nick)
                    Info["cmd"].plus()
                    sThread(self.alias, cmd.handler, (cmd.exp, Vars.get("stype", sBase[1]), source, body, chat.disp), cmd.name)
                    cmd.numb.plus()
        elif atype == self.message:
            if func == sBase[0]:
                source = chat.name
            else:
                source = "%s/%s" % (chat.name, Vars["nick"])
            Message(source, body, chat.disp)
        elif func in self.funcs:
            access = get_access(chat.name, Vars["nick"])
            if access != 6 and (access < 7 or func not in self.risky):
                func_, attr_name = self.funcs[func]
                attr = Vars.get(attr_name)
                if attr:
                    func_(chat, attr, body)

    def checkConds(self, chat, event, alias, conds, Vars):
        for attr, cond, clause, flags in conds:
            if cond == self.null:
                continue
            attr = Vars.get(attr)
            if not attr:
                return False
            if cond == "re":
                id_ = str.join(chr(47), (chat, event, alias))
                if id_ in self.Cache:
                    clause = self.Cache[id_]
                else:
                    clause = self.Cache[id_] = compile__(clause)
            else:
                attr = self.prepare(attr, flags)
            if not self.conds[cond](attr, clause):
                return False
        return True

    def extract(self, chat, event, alias, desc, Vars):
        conds, desc = desc
        if self.checkConds(chat.name, event, alias, conds, Vars):
            self.execute(chat, desc, Vars)

    def process(self, chat, event, Vars):
        iterator = list(self.ChatAliasDesc.get(chat, {}).get(event, {}).items())
        chat_obj = Chats[chat]
        for alias, desc in list(self.AliasDesc[event].items()):
            self.extract(chat_obj, event, alias, desc, Vars)
        for alias, desc in iterator:
            self.extract(chat_obj, event, alias, desc, Vars)

    # ── event handlers (dipetakan dari call_efunctions di core) ──

    def alias_01eh(self, stanza, isConf, stype, source, body, isToBs, disp):
        if isConf:
            if isToBs and stype == sBase[1]:
                parts = body.split(None, 1)
                body = parts[1] if len(parts) > 1 else None
            if body:
                chat, nick = source[1:]
                user = Chats[chat].get_user(nick)
                if user:
                    role, jid = "%s/%s" % user.role, user.source
                else:
                    role, jid = None, None
                if body.startswith("/me") and len(body) > 3 and stype == sBase[0]:
                    body = body[3:].lstrip()
                    event = "/me"
                else:
                    event = "message"
                self.process(chat, event, locals())

    def alias_09eh(self, chat, nick, subject, body, disp):
        if nick and nick != get_nick(chat):
            body = subject
            self.process(chat, "subject", locals())

    def alias_04eh(self, chat, nick, jid, role, stanza_info, disp):
        # Disederhanakan: tanpa auto-fetch version/caps (lihat catatan atas).
        if not jid:
            jid = None
        role = ("%s/%s" % role) if isinstance(role, tuple) else role
        info = stanza_info or {}
        show = info.get("show")
        status = info.get("status")
        caps = None
        caps_ver = None
        self.process(chat, "join", locals())

    def alias_05eh(self, chat, nick, reason, scode, disp):
        if nick != get_nick(chat):
            user = Chats[chat].get_user(nick)
            if user:
                role, jid = "%s/%s" % user.role, user.source
            else:
                role, jid = None, None
            if scode == "301":
                event = "ban"
            elif scode == "307":
                event = "kick"
            else:
                event = "leave"
            self.process(chat, event, locals())

    def alias_06eh(self, chat, old_nick, nick, disp):
        if nick != get_nick(chat):
            user = Chats[chat].get_user(nick)
            if user:
                role, jid = "%s/%s" % user.role, user.source
            else:
                role, jid = None, None
            self.process(chat, "nick", locals())

    def alias_07eh(self, chat, nick, role, disp):
        if nick != get_nick(chat):
            jid = get_source(chat, nick)
            role = ("%s/%s" % role) if isinstance(role, tuple) else role
            self.process(chat, "role", locals())

    def alias_08eh(self, chat, nick, stanza, disp):
        if nick != get_nick(chat):
            user = Chats[chat].get_user(nick)
            if user:
                role, jid = "%s/%s" % user.role, user.source
            else:
                role, jid = None, None
            getter = getattr(stanza, "get", None)
            show = getter("show") if getter else None
            status = getter("status") if getter else None
            self.process(chat, "status", locals())

    # ── validasi ──────────────────────────────────────────────

    def checkAttr(self, event, attr, cond):
        if cond == self.null:
            return True
        return (attr in self.attrsDesc[event])

    def checkParameters(self, body, event):
        if not body:
            return True
        attrs = (self.validDesc[self.alias] + self.validDesc[event])
        for numb, symbol in enumerate(body, 1):
            if symbol == "%":
                temp = body[numb:]
                if temp and not temp.startswith(attrs):
                    return False
        return True

    def processFlags(self, flags, cond, ls=("null", "len_more", "len_less", "re")):
        if cond in ls:
            flags = ()
        else:
            flags = [flag for flag in flags.split(chr(38)) if flag in self.flags]
            if all([(flag in flags) for flag in self.flags[-2:]]):
                flags.remove(self.flags[1])
            flags = tuple(set(flags))
        return flags

    def unpack(self, conditions):
        attrs, conds, clauses, flags = [], [], [], []
        for attr, cond, clause, flags_ in conditions:
            attrs.append(attr)
            conds.append(cond)
            clauses.append("<!--%s-->" % clause)
            flags.append(str.join(chr(38), flags_) or self.null)
        return (str.join(chr(47), attrs), str.join(chr(47), conds),
                "".join(clauses), str.join(chr(47), flags))

    def get_names(self):
        if self.cmd_names:
            return self.cmd_names
        try:
            cmds = eval(get_file(os.path.join(self.path, "alias.name"))).values()
        except Exception:
            cmds = []
        cmds = set([cmd for cmd in cmds] + [self.alias])
        self.cmd_names = cmds
        return cmds

    def save_alias(self, glob, chat):
        if glob:
            file = self.AliasFile
            data = str((self.On, self.AliasDesc))
        else:
            file = chat_file(chat, self.ChatAliasFile)
            data = str((self.Taboo.get(chat, []), self.ChatAliasDesc.get(chat, self.Template.copy())))
        cat_file(file, data)

    # ── command: alias ────────────────────────────────────────

    def command_alias(self, stype, source, body, disp):
        answer = None
        glob = False
        ls = []
        if body:
            ls = body.split(None, 1)
            glob = ((ls.pop(0)).lower() == "global")
        if glob or source[1] not in self.ChatAliasDesc:
            if enough_access(source[1], source[2], 7):
                desc = self.AliasDesc
                if not glob:
                    glob = True
                elif ls:
                    body = ls[0]
                else:
                    body = ""
            else:
                body = ""
                desc = self.AliasDesc
                answer = self.AnsBase[10]
        else:
            desc = self.ChatAliasDesc[source[1]]

        if answer is None:
            arg0 = body.lower()
            if arg0 == "help":
                file = self.HelpFile % ("ru" if DefLANG in ("RU", "UA") else "en")
                try:
                    answer = get_file(os.path.join(self.path, file))
                except Exception:
                    answer = self.AnsBase[4]
            elif arg0 == "state":
                answer = self.AnsBase[int(self.On)]
            elif arg0 == "enable":
                answer = self._alias_enable(source)
            elif arg0 == "disable":
                answer = self._alias_disable(source)
            elif arg0 == "bold":
                answer = self._alias_bold(desc)
            elif body:
                answer = self._alias_modify(source, body, desc, glob)
            else:
                answer = self._alias_list(desc)

        Answer(answer, stype, source, disp)

    def _alias_enable(self, source):
        if not enough_access(source[1], source[2], 8):
            return self.AnsBase[10]
        if self.On:
            return self.AnsBase[2]
        self.On = True
        self.save_alias(True, source[1])
        for chat in list(Chats.keys()):
            self.alias_01si(chat)
        Macro.__call__ = self.__call__
        Macro.__contains__ = self.__contains__
        for inst, ls2 in self.handlers:
            self.handler_register(getattr(self, inst.__name__), ls2)
        return self.AnsBase[4]

    def _alias_disable(self, source):
        if not enough_access(source[1], source[2], 8):
            return self.AnsBase[10]
        if not self.On:
            return self.AnsBase[3]
        self.On = False
        self.save_alias(True, source[1])
        self.clear_handlers()
        self.auto_clear()
        return self.AnsBase[4]

    def _alias_bold(self, desc):
        ls_, cmds = [], []
        for event, aliases in desc.items():
            if event == self.macro:
                for name, (command, body_, access) in sorted(aliases.items()):
                    cmds.append(str.join(chr(32), (name, command, body_)).rstrip())
                continue
            for alias, (conditions, (atype, func, body_)) in sorted(aliases.items()):
                attrs, conds, clauses, flags = self.unpack(conditions)
                ls_.append(str.join(chr(32), (alias, event, attrs, conds, clauses, flags, atype, func, body_)).rstrip())
        ls_txt = ("\\->\n\n" + enumerated_list(ls_)) if ls_ else ""
        cmds_txt = ("Macro:\n\n" + enumerated_list(cmds)) if cmds else ""
        if ls_txt or cmds_txt:
            return str.join(chr(10) * 2, (ls_txt, cmds_txt))
        return self.AnsBase[4]

    def _alias_list(self, desc):
        ls_, cmds = [], []
        for event, aliases in desc.items():
            if event == self.macro:
                for name, (command, body_, access) in sorted(aliases.items()):
                    cmds.append(self.AnsBase[5] % (name, access, command, body_ or self.null))
                continue
            for alias, (conds, (atype, func, body_)) in sorted(aliases.items()):
                ls_.append(self.AnsBase[6] % (alias, event,
                    enumerated_list("%s %s '%s'\n\tflags: %s" % (a, c, cl or self.null, ", ".join(f) or self.null) for a, c, cl, f in conds),
                    " -> ".join((atype, func, body_ or self.null))))
        ls_txt = ("\\->\n\n" + str.join(chr(10) * 2, ("#{0:02} - {1}".format(numb, line) for numb, line in enumerate(ls_, 1)))) if ls_ else ""
        cmds_txt = ("Macro:\n\n" + enumerated_list(cmds)) if cmds else ""
        if ls_txt or cmds_txt:
            return str.join(chr(10) * 2, (ls_txt, cmds_txt))
        return self.AnsBase[4]

    def _alias_modify(self, source, body, desc, glob):
        parts = body.split(None, 3)
        if len(parts) < 3:
            return AnsBase[2]
        arg0 = parts.pop(0).lower()
        alias = parts.pop(0).lower()
        event = parts.pop(0).lower()
        rest = parts[0] if parts else ""

        if arg0 == "access":
            return self._alias_access(source, alias, event, desc, glob)
        if arg0 == "del":
            return self._alias_del(source, alias, event, desc, glob)

        if len(alias) > 16:
            return self.AnsBase[22]

        if arg0 == "show":
            return self._alias_show(alias, event, rest, desc)
        elif arg0 == "add":
            return self._alias_add(source, alias, event, rest, desc, glob)
        return AnsBase[2]

    def _alias_show(self, alias, event, rest, desc):
        if event not in self.Template:
            return AnsBase[2]
        if alias not in desc.get(event, {}):
            return self.AnsBase[7]
        bold = (rest.lower() == "bold")
        if event == self.macro:
            command, body_, access = desc[self.macro][alias]
            if bold:
                return str.join(chr(32), (alias, command, body_)).rstrip()
            return self.AnsBase[5] % (alias, access, command, body_ or self.null)
        conditions, (atype, func, body_) = desc[event][alias]
        if bold:
            attrs, conds, clauses, flags = self.unpack(conditions)
            return str.join(chr(32), (alias, event, attrs, conds, clauses, flags, atype, func, body_)).rstrip()
        return self.AnsBase[6] % (alias, event,
            enumerated_list("%s %s '%s'\n\tflags: %s" % (a, c, cl or self.null, ", ".join(f) or self.null) for a, c, cl, f in conditions),
            " -> ".join((atype, func, body_ or self.null)))

    def _alias_add(self, source, alias, event, rest, desc, glob):
        if not rest:
            return AnsBase[5]

        if event == self.macro:
            if alias in Cmds:
                return self.AnsBase[17] % (alias)
            sub = rest.split(None, 1)
            command = sub.pop(0).lower()
            if command not in Cmds:
                return AnsBase[10]
            if not enough_access(source[1], source[2], (8 if command in self.get_names() else Cmds[command].access)):
                return AnsBase[10]
            if not glob and alias in self.AliasDesc[self.macro]:
                return self.AnsBase[9]
            body_ = sub[0] if sub else ""
            if len(body_) > 1536:
                return self.AnsBase[12] % (1536)
            if not self.checkParameters(body_, self.macro):
                return AnsBase[6]
            access = get_access(source[1], source[2])
            if access < 8:
                cmds = [temp.name for temp in Cmds.values() if temp.access > access]
                if any(t in cmds or t in self.get_names() for t in body_.lower().split()):
                    return self.AnsBase[27]
            desc[self.macro][alias] = (command, body_, Cmds[command].access)
            self.save_alias(glob, source[1])
            return self.AnsBase[4]

        if event not in self.Template:
            return AnsBase[2]

        clauses = self.compile_quote.findall(rest)
        if not clauses:
            return self.AnsBase[20]
        stripped = self.compile_quote.sub(chr(32), rest)
        sub = stripped.split(None, 5)
        if len(sub) < 5:
            return AnsBase[2]
        attrs, conds, flags, atype, func = (a.lower() for a in sub[:5])
        body_ = sub[5] if len(sub) == 6 else ""

        valid_action = (
            (atype == self.command and func in Cmds) or
            (atype == self.set and func in self.funcs) or
            (atype == self.message and func in ("chat", "private"))
        )
        if not valid_action:
            if atype == self.command:
                return AnsBase[6]
            elif atype == self.set:
                return self.AnsBase[18]
            return self.AnsBase[19]

        if atype == self.command and not enough_access(source[1], source[2], (8 if func in self.get_names() else Cmds[func].access)):
            return AnsBase[10]

        if len(body_) > 1024:
            return self.AnsBase[12] % (1024)
        if not self.checkParameters(body_, event):
            return AnsBase[6]

        access = get_access(source[1], source[2])
        cmds = [temp.name for temp in Cmds.values() if temp.access > access] if (atype == self.command and access < 8) else None
        if cmds and any(t in cmds or t in self.get_names() for t in body_.lower().split()):
            return self.AnsBase[27]

        conds_ls = [c for c in conds.split(chr(47)) if c in self.conds]
        if "re" in conds_ls and not enough_access(source[1], source[2], 8):
            return AnsBase[10]
        if len(conds_ls) > 8:
            return self.AnsBase[15]

        attrs_ls = attrs.split(chr(47))
        flags_ls = flags.split(chr(47))
        if not (len(attrs_ls) == len(conds_ls) == len(clauses) == len(flags_ls)):
            return self.AnsBase[14]

        attrs_ls = [self.null if conds_ls[i] == self.null else a
                    for i, a in enumerate(attrs_ls) if self.checkAttr(event, a, conds_ls[i])]
        clauses = [int(c) if conds_ls[i].startswith("len") else c for i, c in enumerate(clauses)
                   if not conds_ls[i].startswith("len") or (isNumber(c) and 3 < int(c) < 10241)]
        if not (len(attrs_ls) == len(conds_ls) == len(clauses)):
            return self.AnsBase[13]

        limit = (192 if enough_access(source[1], source[2], 8) else 64)
        if not all(isinstance(c, int) or len(c) <= 64 for c in clauses):
            return self.AnsBase[12] % (limit)
        if not (conds_ls[-1] == self.null or all(clauses)):
            return self.AnsBase[11]

        for i, cond in enumerate(conds_ls):
            if cond == "re":
                try:
                    compile__(clauses[i])
                except Exception:
                    return self.AnsBase[10]

        flags_final = [self.processFlags(f, conds_ls[i]) for i, f in enumerate(flags_ls)]
        clauses_final = ["" if conds_ls[i] == self.null else self.prepare(c, flags_final[i]) for i, c in enumerate(clauses)]
        conditions = list(zip(attrs_ls, conds_ls, clauses_final, flags_final))
        desc[event][alias] = (conditions, (atype, func, body_))
        self.save_alias(glob, source[1])
        return self.AnsBase[6] % (alias, event,
            enumerated_list("%s %s '%s'\n\tflags: %s" % (a, c, cl or self.null, ", ".join(f) or self.null) for a, c, cl, f in conditions),
            " -> ".join((atype, func, body_ or self.null)))

    def _alias_access(self, source, alias, event, desc, glob):
        if not isNumber(event):
            return AnsBase[30]
        access = int(event)
        user_access = get_access(source[1], source[2])
        if not (0 < access < user_access + 1):
            return self.AnsBase[21] % (user_access)
        if alias not in desc.get(self.macro, {}):
            return self.AnsBase[7]
        command, body_, cur_access = desc[self.macro][alias]
        if not enough_access(source[1], source[2], cur_access):
            return AnsBase[10]
        desc[self.macro][alias] = (command, body_, access)
        self.save_alias(glob, source[1])
        return AnsBase[4]

    def _alias_del(self, source, alias, event, desc, glob):
        if event not in self.Template:
            return AnsBase[2]
        if alias not in desc.get(event, {}):
            return self.AnsBase[7]
        del desc[event][alias]
        self.save_alias(glob, source[1])
        return AnsBase[4]

    # ── command: macro ───────────────────────────────────────

    def command_macro(self, stype, source, body, disp):
        answer = None
        if body:
            ls = body.split()
            arg0 = ls.pop(0).lower()
            if arg0 == "taboo":
                answer = self._macro_taboo(source, ls)
            elif ls and arg0 == "help":
                answer = self._macro_help(source, ls.pop(0).lower())
            else:
                answer = AnsBase[2]
        elif self.On:
            answer = self._macro_list_all(source)
        else:
            answer = self.AnsBase[0]
        Answer(answer, stype, source, disp)

    def _macro_taboo(self, source, ls):
        if source[1] not in Chats:
            return AnsBase[0]
        oCmds = self.Taboo.setdefault(source[1], [])
        if ls:
            if not enough_access(source[1], source[2], 6):
                return AnsBase[10]
            command = ls.pop(0).lower()
            desc = self.AliasDesc[self.macro].get(command) or \
                   self.ChatAliasDesc.get(source[1], {}).get(self.macro, {}).get(command)
            if desc:
                if not enough_access(source[1], source[2], desc[2]):
                    return AnsBase[10]
                if command in oCmds:
                    oCmds.remove(command)
                    answer = self.AnsBase[28] % (command)
                else:
                    oCmds.append(command)
                    answer = self.AnsBase[29] % (command)
                self.save_alias(False, source[1])
                return answer
            elif command in oCmds:
                oCmds.remove(command)
                self.save_alias(False, source[1])
                return AnsBase[4]
            return self.AnsBase[7]
        if oCmds:
            return ", ".join(oCmds)
        return self.AnsBase[30]

    def _macro_help(self, source, command):
        desc = self.AliasDesc[self.macro].get(command)
        base = None
        if desc:
            base = self.MacroHelpBase
        elif source[1] in self.ChatAliasDesc:
            desc = self.ChatAliasDesc[source[1]][self.macro].get(command)
            if desc:
                base = chat_file(source[1], self.ChatMacroHelpBase)
        if desc and base:
            with Database(base) as db:
                db("SELECT help FROM macro WHERE name=?", (command,))
                help_ = db.fetchone()
            cmd, args_, access = desc
            if help_:
                return self.AnsBase[25] % (help_[0], access)
            return self.AnsBase[26]
        return self.AnsBase[7]

    def _macro_list_all(self, source):
        desc = {}
        for name, (command, body_, access) in sorted(self.AliasDesc[self.macro].items()):
            desc.setdefault(access, []).append(name)
        if source[1] in self.ChatAliasDesc:
            for name, (command, body_, access) in sorted(self.ChatAliasDesc[source[1]][self.macro].items()):
                desc.setdefault(access, []).append(name)
        if desc:
            ls_ = [self.AnsBase[24]]
            for access, cmds in sorted(desc.items(), reverse=True):
                ls_.append("# Access %d (total - %d):\n%s" % (access, len(cmds), ", ".join(sorted(cmds))))
            return str.join(chr(10) * 2, ls_)
        return self.AnsBase[4]

    # ── startup / per-chat init ──────────────────────────────

    def alias_00si(self):
        if initialize_file(self.AliasFile, str((True, self.Template))):
            self.On, self.AliasDesc = eval(get_file(self.AliasFile))
            if self.On:
                Macro.__call__ = self.__call__
                Macro.__contains__ = self.__contains__
            else:
                self.clear_handlers()
        if not os.path.isfile(self.MacroHelpBase):
            with Database(self.MacroHelpBase) as db:
                db("CREATE TABLE macro (name text, help text)")
                db.commit()

    def alias_01si(self, chat):
        file = chat_file(chat, self.ChatAliasFile)
        if initialize_file(file, str(([], self.Template))):
            oCmds, desc = eval(get_file(file))
        else:
            oCmds, desc = [], self.Template.copy()
        self.ChatAliasDesc[chat] = desc
        self.Taboo[chat] = oCmds
        filename = cefile(chat_file(chat, self.ChatMacroHelpBase))
        if not os.path.isfile(filename):
            with Database(filename) as db:
                db("CREATE TABLE macro (name text, help text)")
                db.commit()

    def alias_04si(self, chat):
        self.ChatAliasDesc.pop(chat, None)
        self.Taboo.pop(chat, None)

    def auto_clear(self):
        Macro.__call__ = lambda *a: None
        Macro.__contains__ = lambda *a: False

    commands = (
        (command_alias, "alias", 6,),
        (command_macro, "macro", 1,)
    )

    handlers = (
        (alias_00si, "00si"),
        (alias_01si, "01si"),
        (alias_04si, "04si"),
        (alias_01eh, "01eh"),
        (alias_09eh, "09eh"),
        (alias_04eh, "04eh"),
        (alias_05eh, "05eh"),
        (alias_06eh, "06eh"),
        (alias_07eh, "07eh"),
        (alias_08eh, "08eh")
    )
