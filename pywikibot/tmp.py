#!/usr/bin/python
# -*- coding: utf-8  -*-
import sys
import pywikibot
import difflib
import re
site = pywikibot.Site()

modeles = [u"À sourcer", u"Admissibilité à vérifier", u"À wikifier", \
                        u"Article sans source", u"Vérifiabilité", u"Orphelin", u"Guide pratique", u"Section guide pratique", \
                        u"Section guide pratique", u"Section à wikifier", u"Section à sourcer", u"Section à délister", \
                        u"BPV à sourcer", u"À illustrer", u"Section à sourcer", u"Sources secondaires", u"Sources à lier", \
                        u"Internationaliser", u"À mettre à jour", u"À recycler", u"Source unique", \
                        u"Traduction à revoir", u"Travail inédit", u"Style non encyclopédique", u"Style non encyclopédique section", \
                        u"Trop d'ouvrages", u"Résumé introductif", u"Désaccord de neutralité", u"Traduction incomplète", \
                        u"Rédaction", u"Anecdotes", u"Trop de liens", u"À dater", u"À délister", u"Désaccord de neutralité", \
                        u"Pertinence section", u"À vérifier", u"Section non neutre", u"Rédaction", u"Trop d'ouvrages", \
                        u"À déjargoniser", u"Promotionnel", u"Article incomplet", u"À vérifier/architecture", u"Trop long", \
                        u"Article non neutre", u"Conventions bibliographiques", u"Section trop longue", u"À recycler/droit", \
                        u"Section à recycler", u"À recycler/biographie", u"À recycler/catch", u"À recycler/géographie", \
                        u"À recycler/histoire militaire", u"À recycler/judaïsme", u"À recycler/mathématiques", \
                        u"À recycler/récompenses", u"À recycler/zoologie", \
                        u"À vérifier/alimentation", u"À vérifier/anthropologie", u"À vérifier/architecture", \
                        u"À vérifier/association", u"À vérifier/astronomie", u"À vérifier/biographie", u"À vérifier/biologie", \
                        u"À vérifier/botanique", u"À vérifier/chimie", u"À vérifier/cinéma", u"À vérifier/criminologie", \
                        u"À vérifier/culture", u"À vérifier/danse", u"À vérifier/droit", u"À vérifier/entreprise", \
                        u"À vérifier/environnement", u"À vérifier/généalogie", u"À vérifier/géographie", u"À vérifier/géologie", \
                        u"À vérifier/hip-hop", u"À vérifier/histoire", u"À vérifier/histoire militaire", u"À vérifier/informatique", \
                        u"À vérifier/jeu vidéo", u"À vérifier/linguistique", u"À vérifier/littérature", u"À vérifier/mathématiques", \
                        u"À vérifier/mode", u"À vérifier/musique", u"À vérifier/mythologie", u"À vérifier/médecine", \
                        u"À vérifier/média", u"À vérifier/paléontologie", u"À vérifier/peinture", u"À vérifier/philosophie", \
                        u"À vérifier/physique", u"À vérifier/politique", u"À vérifier/psychologie", u"À vérifier/religion", \
                        u"À vérifier/sciences", u"À vérifier/sociologie", u"À vérifier/sport", u"À vérifier/transports", \
                        u"À vérifier/télévision", u"À vérifier/zoologie", u"À vérifier/économie", u"À vérifier/éducation", \
                        u"Plan", u"Sources obsolètes", u"Typographie", u"Catalogue de vente", u"Hagiographique", u"CV", \
                        u"À prouver", u"À désacadémiser", u"Pertinence", u"Copyvio", u"À délister", u"Section à recycler", \
                        u"Résumé introductif trop long", u"Vie privée", u"à recycler/histoire militaire", u"pour wikiquote", \
                        u"trop de citations", u"Anthropocentrisme", u"Résumé introductif trop court"]

#liste_titres = []
#for titre_modele in modeles:
#        page = pywikibot.Page(site, titre_modele, ns=10)
#        while page.isRedirectPage():
#                page = page.getRedirectTarget()
#        liste_titres.append(page)
#        liste_titres_redirect = [p for p in page.backlinks(filterRedirects=True)]
#        # ex : liste_titres_redirect =
#        #                       [u'Sources', u'A sourcer', u'Source ?']
#        liste_titres.extend(liste_titres_redirect)

bot = pywikibot.User(site, u"ZéroBot")
gen = bot.contributions(namespaces=0, total=30000)


def analyse(page):
    history = page.revisions(total=100)
    found = False
    old_text = None
    new_text = None
    
    for k in history:
        if found:
            old_text = page.getOldVersion(k.revid)
            break
        if k.user != u"ZéroBot":
            continue
        else:
            new_text = page.getOldVersion(k.revid)
            found = True
                

    #pattern = "\{\{(.+?)\|.*date=.+"
    #template_name = re.search(pattern, new_text).group(1)
    #new_text = re.sub(pattern, "", new_text)
    #old_text = re.sub("\{\{%s.+" % template_name, "", old_text)
    
    if not old_text or not new_text:
        print "\tERROR could not check %s" % page
        return

    diff = difflib.ndiff(old_text.splitlines(1), new_text.splitlines(1))
    pattern = re.compile("(- +\{\{.+|\+ +\{\{.+?\|.*date=)")
    count_m = 0
    count_p = 0
    for line in diff:
        if line.startswith(" ") or line.startswith("?"):
            continue
        #print line
	if not pattern.search(line):
	    print "\tERROR 0 with page %s" % page
            return
        if line.startswith("-"):
            count_m += 1
        elif line.startswith("+"):
            count_p += 1

    if count_m != count_p:
        print "\tERROR 1 with page %s" % page

count = 0
start = False
for contrib in gen:
    page = contrib[0]
    #page = pywikibot.Page(pywikibot.Site(), u"Andriy Chevtchenko")
    #page = pywikibot.Page(pywikibot.Site(), u"Peintres en Bretagne")
    pywikibot.output("Doing %s (%s) (%i)" % (page, contrib[2], count))
    if page.title() == "Jean-Paul Jacquier":
	print "starting now"
        start = True
    if start:
	analyse(page)
    count += 1
    #break
