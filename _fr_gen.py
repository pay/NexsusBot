# -*- coding: utf-8 -*-
"""Generate ans.fr.json for each expansion from hand-written French translations."""
import json, os, collections

os.chdir('/data/data/com.termux/files/home/NexsusBot')

FR = {}

FR['access'] = {
    0: "ℹ️ Ton accès : %s",
    1: "❌ Accès de %s : %s",
    2: "❌ %s introuvable.",
    3: "❌ La liste d'accès globale est vide.",
    4: "❌ La liste d'accès locale est vide.",
    5: "📋 Liste d'accès :\n",
    6: "❌ %s n'est pas dans la liste d'accès.",
    7: "❌ Le niveau d'accès doit être compris entre -1 et 8.",
    8: "❌ Le niveau d'accès doit être compris entre 0 et 6.",
    9: "Cet utilisateur est dans la liste globale, utilise gaccess.",
    10: "❌ Utilisateur %s introuvable.",
}

FR['basic_control'] = {
    0: "❌ [join] %s (%s) a demandé à rejoindre %s",
    1: " (raison : %s)",
    2: "❌ %s rejoint avec succès.",
    3: "❌ Échec de l'ajout à %s.",
    4: "✅ Terminé.",
    5: "❌ Déjà dans ce salon.",
    6: "❌ JID de salon invalide : %s",
    7: "ℹ️ Bonjour ! Je suis %s, invité par %s.",
    8: "ℹ️ Sortie sur demande de %s.",
    9: "✅ %s quitté.",
    10: "✅ %s quitté.",
    11: "ℹ️ Rechargement sur demande de %s...",
    12: "ℹ️ Arrêt sur demande de %s...",
    13: " (minuteur de reconnexion actif)",
    14: "❌ Dispatcher hors ligne.",
    15: "❌ Impossible de créer le répertoire pour %s.",
    16: "❌ Erreur du thread du dispatcher.",
    17: "❌ Dispatcher inconnu : %s",
}

FR['bot_sends'] = {
    0: "ℹ️ Nettoyage en cours...",
    1: "✅ Tous les systèmes sont opérationnels.",
    2: "❌ %s, %d erreurs détectées",
    3: "❌ Erreurs : %d",
    5: "%s : %s",
    6: "Déjà ici.",
    7: "❌ Utilisateur introuvable.",
    8: "Délai d'attente : %s",
    9: "❌ Rien à nettoyer.",
}

FR['config'] = {
    0: "✅ Mis à jour : %s",
    1: "Rien à mettre à jour.",
    2: "Configuration actuelle :\n",
    3: "❌ Aucun client supplémentaire configuré.",
    4: "ℹ️ Sortie des salons...",
    5: "ℹ️ Déconnexion...",
    6: "Nouveau dispatcher principal : %s",
    7: "❌ Impossible de supprimer le seul client.",
    8: "❌ Erreur de thread.",
    9: "Connexion échouée.",
    10: "Déjà connecté.",
    11: "❌ Client introuvable : %s",
    12: "Client hors ligne : %s",
}

FR['cron'] = {
    0: "ℹ️ Exécution du cron : %s",
    1: "❌ Aucun cron avec l'id %d.",
    2: "❌ Intervalle trop court ou trop peu de répétitions.",
    3: " (+%d répétitions supplémentaires masquées)",
    4: "📋 Planification :\n%s",
    5: "❌ Corps trop long.",
    6: "✅ Planifié : %s",
    7: "❌ Aucune tâche cron.",
    8: "Tâches cron :\n%s",
    9: "❌ Date invalide.",
}

FR['exp_control'] = {
    0: "📋 Infos sur l'expansion :",
    1: "existe",
    2: "❌ manquante",
    3: "chargée",
    4: "✅ Terminé.",
    5: " gestionnaires : %s",
    6: "❌ non chargée",
    7: "❌ Introuvable.",
    8: "📋 Expansions :",
    9: "\nNon chargées (%d) :\n%s",
    10: "Expansion '%s' chargée.",
    11: "❌ Échec du chargement de '%s' : %s",
    13: "✅  Version précédente restaurée.",
    14: "Gestionnaires disponibles : %s",
    15: "❌ Aucun gestionnaire dans '%s'.",
    16: "❌ La commande '%s' est déjà activée.",
    17: "❌ La commande '%s' est déjà désactivée.",
    18: "✅ Toutes les commandes sont activées.",
}

FR['game'] = {
    0: "🎲 Égalité !",
    1: "🎲 Tu gagnes ! %s.",
    2: "🎲 Je gagne ! %s.",
}

FR['get_iq'] = {
    0: "ℹ️ Pong ! %.3f s",
    1: "ℹ️ Pong ! %s — %.3f s",
    2: "❌ Aucune réponse.",
    3: "Statistiques de ping pour %s :\n count : %s\n min : %s\n max : %s\n moy : %s",
    4: "❌ Aucune donnée.",
    5: "❌ %s n'est pas dans le salon.",
    6: "❌ Erreur ou pas de réponse.",
    7: "ℹ️ Inactif : %s — %s",
    8: "ℹ️ Inactif : %s — %s",
    9: "❌ Aucune correspondance trouvée.",
    10: "vCard vide.",
    11: "\nTotal : %d élément(s).",
}

FR['help'] = {
    0: "ℹ️ La commande '%s' provient de l'expansion : %s",
    1: "ℹ️ La commande '%s' nécessite un accès : %d",
    2: "%s\n%s",
    3: "Utilisation :",
    4: "❌ Aucun fichier d'aide trouvé.",
    5: "Liste des commandes — utilise 'commands'.",
    6: "📋 Commandes (préfixe '%s') :",
    7: "'%s'",
    8: "\n👑 [8/Dieu+] (%d) : %s",
    9: "\n🧑 [7/Chef] (%d) : %s",
    10: "\n💎 [6] (%d) : %s",
    11: "\n🗢 [5] (%d) : %s",
    12: "\n🔨 [4] (%d) : %s",
    13: "\n👤 [3] (%d) : %s",
    14: "\n⚖ [2] (%d) : %s",
    15: "\n✅ [1/Tous] (%d) : %s",
    16: "\nTon accès : %s",
    17: "❌ Erreur de format du fichier d'aide.",
}

FR['info'] = {
    0: "📋 Visiteurs du jour (%s) :\n%s\n(en ligne : %s)",
    1: "❌ Aucun visiteur aujourd'hui.",
    2: "📋 Liste (%s) :\n%s",
    3: "📋 Hors ligne (%s) :\n%s\n(en ligne : %s)",
    4: "❌ Aucun utilisateur hors ligne.",
    5: "📋 Salons :",
    6: "❌ Aucun salon.",
    7: "📋 Dispatchers :",
    8: "📋 En ligne :",
    9: "📋 Résultats de recherche (%s) :\n%s",
    10: "❌ Introuvable.",
}

FR['lang'] = {
    0: "📋 Langue actuelle : %s\n📄 Utilisée : %s\n🔍 Codes : %s\n💡 le nom est aussi accepté : %s",
    1: "✅ Ta langue est maintenant : %s.",
    2: "❌ Code de langue inconnu : %s.\n🔍 Codes : %s",
    3: "❌ Impossible d'enregistrer le choix de langue.",
    4: "ℹ️ Pour boucler la boucle : ':lang auto' permet de revenir à la détection automatique.",
    5: "📋 Langue dans ce salon :\n%s",
    6: "ℹ️ Personne n'a encore choisi de langue ici.",
    7: "❌ Impossible de lire la base de données des langues.",
}

FR['note'] = {
    0: "❌ Le bloc-notes est vide.",
    1: "❌ Note trop longue (512 max).",
    2: "❌ Argument invalide.",
    3: "❌ Le bloc-notes est plein (16 lignes).",
    4: "✅ Terminé.",
    5: "❌ La ligne est vide.",
    6: "📋 Tes notes :\n",
    7: "✅ Enregistré à la ligne %s.",
    8: "❌ La ligne est déjà vide.",
}

FR['sconf_attrs'] = {
    0: "❌ '%s' est hors ligne.",
    1: "Utilise déjà '%s'.",
    2: "❌ Dispatcher inconnu : '%s'.",
    3: "✅ Réintégration...",
    4: "✅ Nick défini sur : %s",
    5: "❌ Nick trop long (16 max).",
    6: "Préfixe supprimé.",
    7: "❌ Aucun préfixe défini.",
    8: "✅ Préfixe défini sur : '%s'",
    9: "Le préfixe '%s' est déjà défini.",
    10: "Préfixes disponibles : '%s'",
    11: "Préfixe actuel : '%s'",
    12: "❌ Aucun préfixe.",
    13: "❌ État inconnu : '%s'",
}

FR['sheriff'] = {
    4: "❌ La publicité n'est pas autorisée ici.",
    8: "❌ Le langage obscène n'est pas autorisé ici.",
    9: "❌ Le statut est trop long.",
    10: "❌ %s : auto-ban après %d kicks.",
    11: "❌ %s : tu as perdu le droit de parler, attends.",
    12: "⚠️ %s : anti-wipe déclenché.",
    13: "❌ Flood détecté.",
    14: "❌ Tu as perdu le droit de parler. Attends : %s",
    17: "❌ %s : merci de te vérifier.",
    18: "ℹ️ %s : réponds à cette question pour entrer : %s",
    19: "Combien font 2+2 ?|4\nDe quelle couleur est le ciel ?|bleu",
    24: "\nAnti-espace : ",
    25: "[ACTIVÉ]\n",
    26: "[DÉSACTIVÉ]\n",
    27: "Nick max len : %d\nAnti-wipe : ",
    28: "Auto-ban après %d kicks\nVérif : ",
    29: "Fidélité : %d\nAnti-tiser : ",
    30: "❌ Retrait de voix : %d s\nAnti-obscène : ",
    31: "Msg max len : %d\nAnti-caps : ",
    32: "Presence max len : %d\nSPARTA : ",
    34: "❌ Serveur déjà dans la liste.",
    35: "❌ Serveur absent de la liste.",
    36: "❌ Serveur invalide (doit contenir un point).",
}

FR['talkers'] = {
    0: "📋 Grands parlants :",
    1: "❌ Aucune donnée.",
    2: "Messages : %d\nMots : %d\nMots/msg : %s",
    3: "\n(résultats partiels)",
}

FR['user_stats'] = {
    0: "ℹ️ Arrivée : %s\nDate : %s\nRôle : %s",
    1: "\nVu la dernière fois : %s\nParti : %s",
    2: "\nNicks : %s",
    3: "❌ Aucune donnée.",
    4: "ℹ️ %s est ici depuis %s.",
    5: "Tu es ici depuis %s.",
    6: "❌ Pas ici.",
}

FR['wtf'] = {
    0: "📋 Définitions globales (%d) :\n%s",
    1: "📋 Définitions locales (%d) [%s] :\n%s",
    2: "❌ Aucune définition trouvée.",
    3: "%s — %d mentions",
    4: "❌ Introuvable.",
    5: "%s :\n%s\n— Ajouté par %s (%s)",
    6: "❌ '%s' introuvable.",
    7: "Global : %d définitions.",
    8: "Local : %d définitions [%s].",
    9: "'%s' existe globalement, impossible d'écraser.",
    10: "Aucun contexte de salon.",
}

EXPS = ('access basic_control bot_sends config cron exp_control game get_iq help '
        'info lang note sconf_attrs sheriff talkers user_stats wtf').split()

assert set(EXPS) == set(FR), set(EXPS) ^ set(FR)

for exp in EXPS:
    path = 'expansions/%s/ans.fr.json' % exp
    data = collections.OrderedDict(
        (str(k), v) for k, v in sorted(FR[exp].items()))
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write('\n')
    print('%-14s %d entries -> %s' % (exp, len(data), path))
