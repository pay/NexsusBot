# coding: utf-8
"""Generate ans.de.json for all 17 expansions from the exact AnsBase tuples."""

import ast
import json
import os

BASE = os.path.dirname(os.path.abspath(__file__))

EXPS = ('access basic_control bot_sends config cron exp_control game get_iq '
        'help info lang note sconf_attrs sheriff talkers user_stats wtf').split()

DE = {
    'access': {
        0:  'ℹ️ Dein Zugriff: %s',
        1:  '❌ Zugriff von %s: %s',
        2:  '❌ %s nicht gefunden.',
        3:  '❌ Die globale Zugriffsliste ist leer.',
        4:  '❌ Die lokale Zugriffsliste ist leer.',
        5:  '📋 Zugriffsliste:\n',
        6:  '❌ %s steht nicht in der Zugriffsliste.',
        7:  '❌ Die Zugriffsebene muss zwischen -1 und 8 liegen.',
        8:  '❌ Die Zugriffsebene muss zwischen 0 und 6 liegen.',
        9:  'Dieser Benutzer steht in der globalen Liste, benutze gaccess.',
        10: '❌ Benutzer %s nicht gefunden.',
    },
    'basic_control': {
        0:  '❌ [join] %s (%s) hat das Betreten von %s angefragt',
        1:  ' (Grund: %s)',
        2:  '❌ %s erfolgreich betreten.',
        3:  '❌ Betreten von %s fehlgeschlagen.',
        4:  '✅ Erledigt.',
        5:  '❌ Bereits in diesem Raum.',
        6:  '❌ Ungültige Raum-JID: %s',
        7:  'ℹ️ Hallo! Ich bin %s, eingeladen von %s.',
        8:  'ℹ️ Verlasse den Raum auf Anfrage von %s.',
        9:  '✅ %s verlassen.',
        10: '✅ %s verlassen.',
        11: 'ℹ️ Neuladen auf Anfrage von %s...',
        12: 'ℹ️ Herunterfahren auf Anfrage von %s...',
        13: ' (Reconnect-Timer aktiv)',
        14: '❌ Dispatcher offline.',
        15: '❌ Verzeichnis für %s kann nicht erstellt werden.',
        16: '❌ Fehler im Dispatcher-Thread.',
        17: '❌ Unbekannter Dispatcher: %s',
    },
    'bot_sends': {
        0:  'ℹ️ Wird geleert...',
        1:  '✅ Alle Systeme betriebsbereit.',
        2:  '❌ %s, Fehler erkannt: %d',
        3:  '❌ Fehler: %d',
        5:  '%s: %s',
        6:  'Bereits vorhanden.',
        7:  '❌ Benutzer nicht gefunden.',
        8:  'Abklingzeit: %s',
        9:  '❌ Nichts zu löschen.',
    },
    'config': {
        0:  '✅ Aktualisiert: %s',
        1:  'Nichts zu aktualisieren.',
        2:  'Aktuelle Konfiguration:\n',
        3:  '❌ Keine zusätzlichen Clients konfiguriert.',
        4:  'ℹ️ Räume werden verlassen...',
        5:  'ℹ️ Verbindung wird getrennt...',
        6:  'Neuer primärer Dispatcher: %s',
        7:  '❌ Der einzige Client kann nicht entfernt werden.',
        8:  '❌ Thread-Fehler.',
        9:  'Verbindung fehlgeschlagen.',
        10: 'Bereits verbunden.',
        11: '❌ Client nicht gefunden: %s',
        12: 'Client offline: %s',
    },
    'cron': {
        0:  'ℹ️ Cron wird ausgeführt: %s',
        1:  '❌ Kein Cron mit der ID %d.',
        2:  '❌ Intervall zu kurz oder zu wenige Wiederholungen.',
        3:  ' (+%d weitere Wiederholungen ausgeblendet)',
        4:  '📋 Zeitplan:\n%s',
        5:  '❌ Text zu lang.',
        6:  '✅ Eingeplant: %s',
        7:  '❌ Keine Cron-Aufgaben.',
        8:  'Cron-Aufgaben:\n%s',
        9:  '❌ Ungültiges Datum.',
    },
    'exp_control': {
        0:  '📋 Expansion-Info:',
        1:  'existiert',
        2:  '❌ fehlt',
        3:  'geladen',
        4:  '✅ Erledigt.',
        5:  ' Handler: %s',
        6:  '❌ nicht geladen',
        7:  '❌ Nicht gefunden.',
        8:  '📋 Expansionen:',
        9:  '\nNicht geladen (%d):\n%s',
        10: "Expansion '%s' geladen.",
        11: "❌ '%s' konnte nicht geladen werden: %s",
        13: '✅  Vorherige Version wiederhergestellt.',
        14: 'Verfügbare Handler: %s',
        15: "❌ Keine Handler in '%s'.",
        16: "❌ Befehl '%s' ist bereits aktiviert.",
        17: "❌ Befehl '%s' ist bereits deaktiviert.",
        18: '✅ Alle Befehle sind aktiviert.',
    },
    'game': {
        0:  '🎲 Unentschieden!',
        1:  '🎲 Du gewinnst! %s.',
        2:  '🎲 Ich gewinne! %s.',
    },
    'get_iq': {
        0:  'ℹ️ Pong! %.3f Sek.',
        1:  'ℹ️ Pong! %s — %.3f Sek.',
        2:  '❌ Keine Antwort.',
        3:  'Ping-Statistik für %s:\n Anzahl: %s\n min: %s\n max: %s\n avg: %s',
        4:  '❌ Keine Daten.',
        5:  '❌ %s ist nicht im Raum.',
        6:  '❌ Fehler oder keine Antwort.',
        7:  'ℹ️ Leerlauf: %s — %s',
        8:  'ℹ️ Leerlauf: %s — %s',
        9:  '❌ Keine Treffer gefunden.',
        10: 'Leere vCard.',
        11: '\nGesamt: %d Einträge.',
    },
    'help': {
        0:  "ℹ️ Befehl '%s' stammt aus der Expansion: %s",
        1:  "ℹ️ Befehl '%s' erfordert Zugriff: %d",
        2:  '%s\n%s',
        3:  'Verwendung:',
        4:  '❌ Keine Hilfedatei gefunden.',
        5:  "Befehlsliste — benutze 'commands'.",
        6:  "📋 Befehle (Präfix '%s'):",
        7:  "'%s'",
        8:  '\n👑 [8/God+] (%d): %s',
        9:  '\n🧑 [7/Chief] (%d): %s',
        10: '\n💎 [6] (%d): %s',
        11: '\n🗢 [5] (%d): %s',
        12: '\n🔨 [4] (%d): %s',
        13: '\n👤 [3] (%d): %s',
        14: '\n⚖ [2] (%d): %s',
        15: '\n✅ [1/Alle] (%d): %s',
        16: '\nDein Zugriff: %s',
        17: '❌ Formatfehler in der Hilfedatei.',
    },
    'info': {
        0:  "📋 heutige Besucher (%s):\n%s\n(online: %s)",
        1:  '❌ Heute keine Besucher.',
        2:  '📋 Liste (%s):\n%s',
        3:  '📋 Offline (%s):\n%s\n(online: %s)',
        4:  '❌ Keine Offline-Benutzer.',
        5:  '📋 Räume:',
        6:  '❌ Keine Räume.',
        7:  '📋 Dispatcher:',
        8:  '📋 Online:',
        9:  '📋 Suchergebnisse (%s):\n%s',
        10: '❌ Nicht gefunden.',
    },
    'lang': {
        0:  '📋 Aktuelle Sprache: %s\n📄 Verwendet: %s\n🔍 Codes: %s\n💡auch der Name kann verwendet werden: %s',
        1:  '✅ Deine Sprache ist jetzt: %s.',
        2:  '❌ Unbekannter Sprachcode: %s.\n🔍 Codes: %s',
        3:  '❌ Speichern der Sprachauswahl fehlgeschlagen.',
        4:  "ℹ️ Vollständig: ':lang auto' bringt die automatische Erkennung zurück.",
        5:  '📋 Sprachen in diesem Raum:\n%s',
        6:  'ℹ️ Hier hat noch niemand eine Sprache gewählt.',
        7:  '❌ Sprachdatenbank konnte nicht gelesen werden.',
    },
    'note': {
        0:  '❌ Notizblock ist leer.',
        1:  '❌ Notiz zu lang (max. 512).',
        2:  '❌ Ungültiges Argument.',
        3:  '❌ Notizblock ist voll (16 Zeilen).',
        4:  '✅ Erledigt.',
        5:  '❌ Zeile ist leer.',
        6:  '📋 Deine Notizen:\n',
        7:  '✅ In Zeile %s gespeichert.',
        8:  '❌ Zeile ist bereits leer.',
    },
    'sconf_attrs': {
        0:  "❌ '%s' ist offline.",
        1:  "'%s' wird bereits verwendet.",
        2:  "❌ Unbekannter Dispatcher: '%s'.",
        3:  '✅ Betreten erneut...',
        4:  '✅ Nick gesetzt auf: %s',
        5:  '❌ Nick zu lang (max. 16).',
        6:  'Präfix entfernt.',
        7:  '❌ Kein Präfix gesetzt.',
        8:  "✅ Präfix gesetzt auf: '%s'",
        9:  "Präfix '%s' ist bereits gesetzt.",
        10: "Verfügbare Präfixe: '%s'",
        11: "Aktuelles Präfix: '%s'",
        12: '❌ Kein Präfix.',
        13: "❌ Unbekannter Zustand: '%s'",
    },
    'sheriff': {
        4:  '❌ Werbung ist hier nicht erlaubt.',
        8:  '❌ Obszöne Sprache ist hier nicht erlaubt.',
        9:  '❌ Presence/Status ist zu lang.',
        10: '❌ %s: Automatisch gesperrt nach %d Kicks.',
        11: '❌ %s: Du bist stummgeschaltet, warte.',
        12: '⚠️ %s: Anti-Wipe ausgelöst.',
        13: '❌ Flood erkannt.',
        14: '❌ Du bist stummgeschaltet. Warte: %s',
        17: '❌ %s: Bitte verifiziere dich.',
        18: 'ℹ️ %s: Beantworte diese Frage, um beizutreten: %s',
        19: 'Was ist 2+2?|4\nWelche Farbe hat der Himmel?|blau',
        24: '\nAnti-Leerzeichen: ',
        25: '[AN]\n',
        26: '[AUS]\n',
        27: 'Max. Nicklänge: %d\nAnti-Wipe: ',
        28: 'Automatische Sperre nach: %d Kicks\nVerifizierung: ',
        29: 'Loyalität: %d\nAnti-Werbung: ',
        30: '❌ Stummschaltdauer: %d Sek.\nAnti-Obszönität: ',
        31: 'Max. Nachrichtenlänge: %d\nAnti-Caps: ',
        32: 'Max. Presence-Länge: %d\nSPARTA: ',
        34: '❌ Server steht bereits in der Liste.',
        35: '❌ Server steht nicht in der Liste.',
        36: '❌ Ungültiger Server (muss einen Punkt enthalten).',
    },
    'talkers': {
        0:  '📋 Top-Chatter:',
        1:  '❌ Keine Daten.',
        2:  'Nachrichten: %d\nWörter: %d\nWörter/Nachr.: %s',
        3:  '\n(zeigt Teilergebnisse)',
    },
    'user_stats': {
        0:  'ℹ️ Beigetreten: %s\nDatum: %s\nRolle: %s',
        1:  '\nZuletzt gesehen: %s\nVerlassen: %s',
        2:  '\nNicks: %s',
        3:  '❌ Keine Daten.',
        4:  'ℹ️ %s war %s hier.',
        5:  'Du warst %s hier.',
        6:  '❌ Nicht hier.',
    },
    'wtf': {
        0:  '📋 Globale Definitionen (%d):\n%s',
        1:  '📋 Lokale Definitionen (%d) [%s]:\n%s',
        2:  '❌ Keine Definitionen gefunden.',
        3:  '%s — %d Erwähnungen',
        4:  '❌ Nicht gefunden.',
        5:  '%s:\n%s\n— Hinzugefügt von %s (%s)',
        6:  "❌ '%s' nicht gefunden.",
        7:  'Global: %d Definitionen.',
        8:  'Lokal: %d Definitionen [%s].',
        9:  "'%s' existiert global, kann nicht überschrieben werden.",
        10: 'Kein Raumkontext.',
        11: '\n',
    },
}


def ansbase(exp):
    path = os.path.join(BASE, 'expansions', exp, 'code.py')
    for node in ast.walk(ast.parse(open(path, encoding='utf-8').read())):
        if isinstance(node, ast.Assign) and getattr(node.targets[0], 'id', '') == 'AnsBase':
            return ast.literal_eval(node.value)
    raise RuntimeError('AnsBase not found in %s' % path)


def main():
    total = 0
    for exp in EXPS:
        table = DE[exp]
        base = ansbase(exp)
        wanted = {i for i, x in enumerate(base) if x and x.strip()}
        stray = sorted(set(table) - wanted)
        if stray:
            raise RuntimeError('%s: stray keys %s' % (exp, stray))
        missing = sorted(wanted - set(table))
        if missing:
            raise RuntimeError('%s: missing keys %s' % (exp, missing))
        for i, v in table.items():
            if not isinstance(v, str):
                raise RuntimeError('%s: %s not a str' % (exp, i))
            if '\\n' in v:
                raise RuntimeError('%s: %s contains literal backslash-n' % (exp, i))
        out = {str(i): table[i] for i in sorted(table)}
        path = os.path.join(BASE, 'expansions', exp, 'ans.de.json')
        with open(path, 'w', encoding='utf-8') as fh:
            json.dump(out, fh, ensure_ascii=False, indent=2,
                      sort_keys=lambda s: int(s))
            fh.write('\n')
        total += len(out)
        print('%-14s %2d entries -> %s' % (exp, len(out), path))
    print('TOTAL', total)


main()