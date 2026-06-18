# coding: utf-8
# Porting Python3 by: paijo.ahmad@jabber.ru

#  BlackSmith mark.2 → Nexsus Port (Python 3 / slixmpp)
# exp_name = "get_iq" # /code.py v.x12
#  Id: 13~11c
#  Original © (2010-2013) by WitcherGeralt [alkorgun@gmail.com]
#  Ported to Python 3 / slixmpp by Nexsus Project 2026
#
#  NOTE: IQ requests menggunakan slixmpp async — dijalankan via
#        asyncio dari thread expansion, hasilnya dikembalikan sync.

import asyncio

class expansion_temp(expansion):

    def __init__(self, name):
        expansion.__init__(self, name)

    AnsBase = (
        "Pong! %.3f sec",                      # 0  ping ok
        "Pong! %s — %.3f sec",                 # 1  ping via version
        "No response.",                         # 2
        "Ping stats for %s:\n count: %s\n min: %s\n max: %s\n avg: %s",  # 3
        "No data.",                             # 4
        "%s is not in the room.",               # 5
        "Error or no response.",                # 6
        "Idle: %s — %s",                        # 7  server uptime
        "Idle: %s — %s",                        # 8  user idle
        "No matches found.",                    # 9
        "Empty vCard.",                         # 10
        "\nTotal: %d items.",                   # 11
    )

    # ── helpers ────────────────────────────────────────────────

    def _resolve_instance(self, source, instance):
        """
        Kembalikan (daftar_kandidat_target_IQ, nick/jid_display) atau (None, answer).
        Kandidat diurutkan dari yang paling mungkin direspons server:
          1. JID lengkap dengan resource (jika diketahui)
          2. JID bare (tanpa resource)
          3. Occupant JID (room@conference/nick)
        Caller mencoba tiap kandidat sampai salah satu memberi hasil.
        """
        conf = source[1]
        if instance:
            if conf in Chats and Chats[conf].isHere(instance):
                if Chats[conf].isHereTS(instance):
                    full     = get_full_source(conf, instance)
                    bare     = get_source(conf, instance)
                    occupant = "%s/%s" % (conf, instance)
                    cands = []
                    for c in (full, bare, occupant):
                        if c and c not in cands:
                            cands.append(c)
                    return (cands, bare)
                else:
                    return (None, self.AnsBase[5] % instance)
            # Bukan nick di room — terima jika JID valid (user@host) ATAU
            # domain server/component (mengandung "." tanpa spasi, mis.
            # "conversations.im", "up.conversations.im", "jabber.ru")
            if "@" in instance or ("." in instance and " " not in instance):
                return ([instance], instance)
            return (None, "'%s' not found in this room and is not a valid JID." % instance)
        # Tanpa argumen — query untuk diri sendiri (pengirim)
        full     = get_full_source(conf, source[2])
        bare     = get_source(conf, source[2])
        occupant = source[0]
        cands = []
        for c in (full, bare, occupant):
            if c and c not in cands:
                cands.append(c)
        return (cands, bare)

    async def _try_candidates(self, cands, query_func):
        """Coba tiap kandidat JID sampai ada yang merespons (bukan None)."""
        for target in cands:
            try:
                result = await query_func(target)
            except Exception:
                result = None
            if result is not None:
                return result
        return None

    def _get_client(self, disp):
        key = get_disp(disp)
        return Clients.get(key)

    def _run_iq(self, client, iq):
        """Jalankan IQ request secara blocking (max 10s)."""
        loop = getattr(client, "_loop", None)
        if not loop or not loop.is_running():
            return None
        future = asyncio.run_coroutine_threadsafe(iq.send(), loop)
        try:
            return future.result(timeout=10)
        except Exception:
            return None

    # ── ping ───────────────────────────────────────────────────

    PingStats = {}

    def command_ping(self, stype, source, body, disp):
        cands, source_ = self._resolve_instance(source, body.split()[0] if body else "")
        if cands is None:
            return Answer(source_, stype, source, disp)
        instance = cands[0]

        client = self._get_client(disp)
        if not client:
            return Answer(self.AnsBase[2], stype, source, disp)

        start = time.time()
        iq    = client.make_iq_get(ito=instance)
        iq["ping"]  # touch ping plugin
        iq.enable("ping")

        # Gunakan plugin xep_0199 langsung
        loop = getattr(client, "_loop", None)
        if not loop:
            return Answer(self.AnsBase[2], stype, source, disp)

        async def do_ping():
            try:
                await client.plugin["xep_0199"].send_ping(instance, timeout=10)
                return True
            except Exception:
                return False

        future = asyncio.run_coroutine_threadsafe(do_ping(), loop)
        try:
            ok = future.result(timeout=12)
        except Exception:
            ok = False

        elapsed = round(time.time() - start, 3)
        if ok:
            if source_:
                self.PingStats.setdefault(source_, []).append(elapsed)
            Answer(self.AnsBase[0] % elapsed, stype, source, disp)
        else:
            Answer(self.AnsBase[2], stype, source, disp)

    def command_ping_stats(self, stype, source, body, disp):
        if body:
            conf = source[1]
            if conf in Chats and Chats[conf].isHere(body):
                source_ = get_source(conf, body)
            else:
                source_ = body.lower()
        else:
            source_ = get_source(source[1], source[2])

        stats = self.PingStats.get(source_)
        if stats:
            n    = len(stats)
            mn   = min(stats)
            mx   = max(stats)
            avg  = round(sum(stats) / n, 3)
            answer = self.AnsBase[3] % (source_, str(n), str(mn), str(mx), str(avg))
        else:
            answer = self.AnsBase[4]
        Answer(answer, stype, source, disp)

    # ── time ───────────────────────────────────────────────────

    compile_tzo = compile__(r"^([-\+]+?)(\d+?):(\d+?)$")
    compile_utc = compile__(r"^(\d+?)-(\d+?)-(\d+?)[A-Z]+?(\d+?):(\d+?):(\d+?)[A-Z]*?$")

    def command_time(self, stype, source, body, disp):
        cands, _ = self._resolve_instance(source, body.split()[0] if body else "")
        if cands is None:
            return Answer(_, stype, source, disp)

        client = self._get_client(disp)
        if not client:
            return Answer(self.AnsBase[2], stype, source, disp)

        loop = getattr(client, "_loop", None)
        if not loop:
            return Answer(self.AnsBase[2], stype, source, disp)

        async def query(target):
            try:
                return await client.plugin["xep_0202"].get_entity_time(target, timeout=5)
            except Exception:
                return None

        async def do_time():
            return await self._try_candidates(cands, query)

        future = asyncio.run_coroutine_threadsafe(do_time(), loop)
        try:
            result = future.result(timeout=20)
        except Exception:
            result = None

        answer = self.AnsBase[6]
        if result:
            try:
                # Coba via stanza interface dulu (nama field bisa beda antar versi)
                for field in ("entity_time", "time"):
                    try:
                        tzo = result[field]["tzo"]
                        utc = result[field]["utc"]
                        if tzo and utc:
                            answer = "%s (UTC%s)" % (utc, tzo)
                            break
                    except Exception:
                        continue
                else:
                    # Fallback: parse XML langsung — paling reliable
                    xml = result.xml
                    ns  = "urn:xmpp:time"
                    utc_el = xml.find(".//{%s}utc" % ns)
                    tzo_el = xml.find(".//{%s}tzo" % ns)
                    if utc_el is not None and tzo_el is not None:
                        answer = "%s (UTC%s)" % (utc_el.text or "", tzo_el.text or "")
            except Exception:
                pass
        Answer(answer, stype, source, disp)

    # ── version ────────────────────────────────────────────────

    def command_version(self, stype, source, body, disp):
        # Tanpa argumen — query versi pengirim sendiri (pakai nick pengirim)
        # Dengan argumen — query ke nick/JID/domain yang disebutkan
        target = body.split()[0] if body.strip() else ""

        cands, _ = self._resolve_instance(source, target)
        if cands is None:
            return Answer(_, stype, source, disp)
        instance = cands[0]

        client = self._get_client(disp)
        if not client:
            return Answer(self.AnsBase[2], stype, source, disp)

        loop = getattr(client, "_loop", None)
        if not loop:
            return Answer(self.AnsBase[2], stype, source, disp)

        async def do_version():
            for target in cands:
                try:
                    r = await client.plugin["xep_0092"].get_version(target, timeout=5)
                    if r is not None:
                        return r
                except Exception:
                    continue
            return None

        future = asyncio.run_coroutine_threadsafe(do_version(), loop)
        try:
            result = future.result(timeout=20)
        except Exception:
            result = None

        if result:
            try:
                sv   = result["software_version"]
                name = sv["name"]    or "[None]"
                ver  = sv["version"] or "[None]"
                os_  = sv["os"]      or "[None]"
            except Exception:
                try:
                    # Fallback: parse XML langsung
                    xml  = result.xml
                    ns   = "jabber:iq:version"
                    # Cari di dalam <query xmlns="jabber:iq:version">
                    q = xml.find(".//{%s}query" % ns) or xml
                    name = (q.findtext("{%s}name"    % ns) or
                            q.findtext("name")             or "[None]").strip()
                    ver  = (q.findtext("{%s}version" % ns) or
                            q.findtext("version")          or "[None]").strip()
                    os_  = (q.findtext("{%s}os"      % ns) or
                            q.findtext("os")               or "[None]").strip()
                except Exception:
                    name = ver = os_ = "[None]"
            target = body.split()[0] if body else _
            answer = (
                "\n"
                "  Name  :  %s\n"
                "  Ver.  :  %s\n"
                "  OS    :  %s"
            ) % (name, ver, os_)
        else:
            answer = self.AnsBase[6]
        Answer(answer, stype, source, disp)

    # ── vcard ──────────────────────────────────────────────────

    VcardDesc = {
        "NICKNAME": "Nick", "GIVEN": "Name", "FAMILY": "Surname",
        "FN": "Full Name", "BDAY": "Birthday", "USERID": "e-Mail",
        "URL": "Web Page", "DESC": "Description", "NUMBER": "Phone",
        "EXTADR": "Address", "PCODE": "Post Code", "LOCALITY": "City",
        "CTRY": "Country", "ORGNAME": "Organization", "ORGUNIT": "Department"
    }

    def _get_vcard_xml(self, result):
        """
        Ekstrak XML element vCard dari IQ result slixmpp.
        Coba berbagai cara akses karena nama field berubah antar versi slixmpp:
          - result["vcard_temp"].xml  (attribute, bukan dict access)
          - XML parse langsung dari result.xml
        """
        # Cara 1: attribute langsung (bukan subscript)
        try:
            vt = result["vcard_temp"]
            xml_el = getattr(vt, "xml", None)
            if xml_el is not None:
                return xml_el
        except Exception:
            pass
        # Cara 2: parse dari result.xml — cari <vCard>
        try:
            ns = "vcard-temp"
            xml = result.xml
            for ns_uri in ("vcard-temp", "jabber:iq:vcard"):
                el = xml.find(".//{%s}vCard" % ns_uri)
                if el is None:
                    el = xml.find(".//vCard")
                if el is not None:
                    return el
        except Exception:
            pass
        return None

    def _parse_vcard_node(self, xml_el, ls):
        """Rekursif parse vCard XML element (xml.etree.ElementTree.Element)."""
        kids = list(xml_el)
        if kids:
            for child in kids:
                tag = child.tag.split("}")[-1] if "}" in child.tag else child.tag
                if tag == "PHOTO":
                    continue
                self._parse_vcard_node(child, ls)
        else:
            try:
                tag  = xml_el.tag.split("}")[-1] if "}" in xml_el.tag else xml_el.tag
                data = (xml_el.text or "").strip()
                if data and len(data) <= 512:
                    label = self.VcardDesc.get(tag, tag.capitalize())
                    ls.append("%s: %s" % (label, data))
            except Exception:
                pass

    def command_vcard(self, stype, source, body, disp):
        cands, _ = self._resolve_instance(source, body.split()[0] if body else "")
        if cands is None:
            return Answer(_, stype, source, disp)

        client = self._get_client(disp)
        if not client:
            return Answer(self.AnsBase[2], stype, source, disp)

        loop = getattr(client, "_loop", None)
        if not loop:
            return Answer(self.AnsBase[2], stype, source, disp)

        async def query(target):
            try:
                return await client.plugin["xep_0054"].get_vcard(target, timeout=5)
            except Exception:
                return None

        async def do_vcard():
            """
            Coba tiap kandidat target. Beberapa server merespons IQ vcard
            dengan vCard KOSONG (bukan error) untuk JID/resource tertentu —
            jadi kita parse tiap hasil dan pilih kandidat pertama yang
            menghasilkan field non-empty. Jika semua kosong, kembalikan
            hasil pertama yang non-None (untuk tahu "vCard kosong" vs
            "tidak ada respons sama sekali").
            """
            first_non_none = None
            for target in cands:
                result = await query(target)
                if result is None:
                    continue
                if first_non_none is None:
                    first_non_none = result
                ls = []
                try:
                    vcard_el = self._get_vcard_xml(result)
                    if vcard_el is not None:
                        self._parse_vcard_node(vcard_el, ls)
                except Exception:
                    pass
                if ls:
                    return result
            return first_non_none

        future = asyncio.run_coroutine_threadsafe(do_vcard(), loop)
        try:
            result = future.result(timeout=20)
        except Exception:
            result = None

        answer = None
        if result:
            ls = []
            try:
                vcard_el = self._get_vcard_xml(result)
                if vcard_el is not None:
                    self._parse_vcard_node(vcard_el, ls)
            except Exception:
                pass
            if ls:
                ls.insert(0, "\\->")
                text = "\n".join(ls)
                if stype == sBase[1]:
                    Message(source[1], text, disp)
                else:
                    answer = text
            else:
                answer = self.AnsBase[10]
        else:
            answer = self.AnsBase[6]
        if answer:
            Answer(answer, stype, source, disp)

    # ── idle / uptime ──────────────────────────────────────────

    def _query_last(self, client, instance):
        loop = getattr(client, "_loop", None)
        if not loop:
            return None
        async def do_last():
            try:
                result = await client.plugin["xep_0012"].get_last_activity(instance)
                return result
            except Exception:
                return None
        future = asyncio.run_coroutine_threadsafe(do_last(), loop)
        try:
            return future.result(timeout=12)
        except Exception:
            return None

    def command_uptime(self, stype, source, body, disp):
        client = self._get_client(disp)
        if not client:
            return Answer(self.AnsBase[2], stype, source, disp)
        server = body.strip() if body else client._nx_server
        result = self._query_last(client, server)
        if result:
            secs   = result.get("last_activity", {}).get("seconds", 0)
            answer = self.AnsBase[7] % (server, Time2Text(int(secs)))
        else:
            answer = self.AnsBase[6]
        Answer(answer, stype, source, disp)

    def command_idle(self, stype, source, body, disp):
        cands, source_ = self._resolve_instance(source, body.split()[0] if body else "")
        if cands is None:
            return Answer(source_, stype, source, disp)
        instance = cands[0]
        client = self._get_client(disp)
        if not client:
            return Answer(self.AnsBase[2], stype, source, disp)
        result = self._query_last(client, instance)
        if result:
            secs   = result.get("last_activity", {}).get("seconds", 0)
            answer = self.AnsBase[8] % (source_ or instance, Time2Text(int(secs)))
        else:
            answer = self.AnsBase[6]
        Answer(answer, stype, source, disp)

    # ── affiliation list ───────────────────────────────────────

    affs = ("owner", "admin", "member", "outcast")

    def command_aflist(self, stype, source, body, disp):
        answer = None
        if source[1] not in Chats:
            return Answer(self.AnsBase[6], stype, source, disp)
        if not body:
            return Answer(self.AnsBase[4], stype, source, disp)

        client = self._get_client(disp)
        if not client:
            return Answer(self.AnsBase[2], stype, source, disp)

        ls    = body.split()
        cmd   = ls.pop(0).lower()
        room  = source[1]
        loop  = getattr(client, "_loop", None)
        if not loop:
            return Answer(self.AnsBase[2], stype, source, disp)

        def get_afflist(aff):
            async def _do():
                try:
                    return await client.plugin["xep_0045"].get_affiliation_list(room, aff)
                except Exception:
                    return []
            f = asyncio.run_coroutine_threadsafe(_do(), loop)
            try:
                return f.result(timeout=15)
            except Exception:
                return []

        if cmd == "search":
            if not ls:
                return Answer(self.AnsBase[4], stype, source, disp)
            data   = ls.pop(0).lower()
            result = []
            for aff in self.affs:
                for jid in get_afflist(aff):
                    if data in str(jid).lower():
                        result.append("%s (%s)" % (jid, aff))
            if result:
                text = enumerated_list(result)
                Message(source[0], text, disp)
                if stype == sBase[1]:
                    answer = "Sent to PM."
            else:
                answer = self.AnsBase[9]
        else:
            aff  = cmd if cmd in self.affs else None
            if not aff:
                return Answer(self.AnsBase[4], stype, source, disp)
            limit = 0
            if ls and isNumber(ls[0]):
                limit = max(20, int(ls.pop(0)))
            jids  = get_afflist(aff)
            if jids:
                lines = ["%d) %s" % (i, j) for i, j in enumerate(jids, 1)
                         if not limit or i <= limit]
                if limit and len(jids) > limit:
                    lines.append("...\nTotal: %d items." % len(jids))
                text = "\n".join(lines)
                Message(source[0], text, disp)
                if stype == sBase[1]:
                    answer = "Sent to PM."
            else:
                answer = self.AnsBase[4]
        if answer:
            Answer(answer, stype, source, disp)

    # ── disco ──────────────────────────────────────────────────

    compile_disco = compile__(r"^(.+?)\((\d+?)\)$", 16)

    def command_disco(self, stype, source, body, disp):
        if not body:
            return Answer(self.AnsBase[4], stype, source, disp)

        client = self._get_client(disp)
        if not client:
            return Answer(self.AnsBase[2], stype, source, disp)

        ls     = body.split(None, 2)
        server = ls.pop(0).lower()
        limit  = 16
        filter_= None
        if ls:
            tok = ls.pop(0)
            if isNumber(tok):
                limit = min(int(tok), 256 if stype == sBase[0] else 24)
                if ls:
                    filter_ = ls.pop(0)
            else:
                filter_ = tok

        loop = getattr(client, "_loop", None)
        if not loop:
            return Answer(self.AnsBase[2], stype, source, disp)

        async def do_disco():
            try:
                return await client.plugin["xep_0030"].get_items(jid=server, timeout=10)
            except Exception:
                return None

        future = asyncio.run_coroutine_threadsafe(do_disco(), loop)
        try:
            result = future.result(timeout=12)
        except Exception:
            result = None

        if not result:
            return Answer(self.AnsBase[6], stype, source, disp)

        confs, plain = [], []
        for item in result["disco_items"]["items"]:
            jid  = str(item[0])
            name = item[2] or ""
            if filter_ and filter_ not in jid and filter_ not in name:
                continue
            m = self.compile_disco.search(name)
            if m:
                label, numb = m.groups()
                confs.append((int(numb), jid, label[:48].strip()))
            else:
                plain.append((jid, name[:48].strip()) if name else (jid,))

        confs.sort(reverse=True)
        plain.sort()
        result_lines = []
        count = 0
        for numb, jid, name in confs:
            count += 1
            if count > limit:
                break
            result_lines.append("%s (%d) [%s]" % (name, numb, jid))
        for items in plain:
            count += 1
            if count > limit:
                break
            result_lines.append(" - ".join(items))

        if result_lines:
            answer = "\\->\n" + enumerated_list(result_lines)
            total  = len(confs) + len(plain)
            if total:
                answer += self.AnsBase[11] % total
        else:
            answer = self.AnsBase[4]
        Answer(answer, stype, source, disp)

    # ── register ───────────────────────────────────────────────

    # xep_0012 (Last Activity) perlu didaftarkan jika belum
    handlers = ()

    def initialize_exp(self):
        # Daftarkan plugin xep_0012 jika belum
        for client in Clients.values():
            try:
                if "xep_0012" not in client.plugin:
                    client.register_plugin("xep_0012")
            except Exception:
                pass
        super().initialize_exp()

    commands = (
        (command_ping,         "ping",     1,),
        (command_ping_stats,   "pstat",    1,),
        (command_time,         "time",     1,),
        (command_version,      "version",  1,),
        (command_vcard,        "vcard",    2,),
        (command_uptime,       "uptime",   1,),
        (command_idle,         "idle",     1,),
        (command_aflist,       "list",     4,),
        (command_disco,        "disco",    2,),
    )