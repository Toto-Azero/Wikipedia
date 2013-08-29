#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
** (fr) **
Ce bot met à jour les modèles {{Articles récents}} sur fr.wikipedia.

** (en) **
This bot updates the {{Articles récents}} templates on fr.wikipedia.

Dernières modifications :
*
"""
#
# (C) Toto Azéro, 2011-2012
#
# Distribué sous licence GNU GPLv3
# Distributed under the terms of the GNU GPLv3 license
# http://www.gnu.org/licenses/gpl.html
#
__version__ = '$Id: maj_articles_recents.py 1589+ 2013-05-01 16:35:52 (CEST) Toto Azéro $'
#
import almalog2
import pywikibot
from pywikibot import catlib, pagegenerators
import re, time
from datetime import datetime

def main():
	dry = False # À activer seulement pour les tests
	test = False # À activer seulement pour tester le script sur une seule page
	ns_test = False
	recurse_test = False
	for arg in pywikibot.handleArgs():
		if arg == "-dry":
			dry = True
			pywikibot.output(u'(dry is ON)')
			
		elif arg[0:6] == "-test:":
			test = True
			titre_page_test = arg[6:]
			
		elif arg[0:4] == "-ns:":
			ns_test = True
			namespaces_test_value = [int(i) for i in arg[4:].split(',')]
			
		elif arg[0:9] == "-recurse:":
			recurse_test = True
			recurse_test_value = bool(arg[9:])
	
	comment_modele = u"%(nombre_articles)i articles) (Bot: Mise à jour de la liste des articles récents (%(precision_pages)s)"
	site = pywikibot.getSite()
	titre_modele = u"Articles récents"
	modele = pywikibot.Page(site, titre_modele, ns = 10)
	gen = pagegenerators.ReferringPageGenerator(modele, onlyTemplateInclusion = True)
	
	matchDebut1 = u"<!-- Ce tableau est créé automatiquement par un robot. Articles Récents DEBUT -->"
	matchFin1 = u"\n<!-- Ce tableau est créé automatiquement par un robot. Articles Récents FIN -->"
	
	matchDebut2 = u"<!-- Ce tableau est créé automatiquement par un robot. Articles Récents Liste DEBUT -->"
	matchFin2 = u"\n<!-- Ce tableau est créé automatiquement par un robot. Articles Récents Liste FIN -->"

	if test:
		pywikibot.output(u'(test is ON)')
		gen = [pywikibot.Page(site, titre_page_test)]
	#gen = [pywikibot.Page(site, u"Projet:Sport automobile/Articles récents")]
	
	for main_page in gen:
		comment = comment_modele
		pywikibot.output(u"\n========================\nTraitement de %s\n========================" % main_page.title())
		text = main_page.get()
		
		#####################
		### Récupération des informations sur la page
		#####################
		m = re.search(re.compile(ur"{ *{ *[aA]rticles récents.*\| *pageportail *= *(?P<pageportail>[^\n]*).*\| *catégorie *= *(?P<categorie>[^\n]*)", re.S), text)
		m2 = re.search("\| *nbMax *= *(?P<nbMax>[^\n]+)", text)
		m3 = re.search("\| *namespaces *= *(?P<namespaces>[^\n]+)", text)
		m4 = re.search("\| *recurse *= *(?P<recurse>[^\n]+)", text)
		if m:
			pywikibot.output(u'* résultat de la recherche = %s' % m.group())

			pageportail = m.group('pageportail')
			pywikibot.output(u'* pageportail = %s' % pageportail)
			titre_categorie = m.group('categorie')
			pywikibot.output(u'* titre_categorie = %s' % titre_categorie)
			
			nbMax = 10
			if m2:
				nbMax = int(m2.group('nbMax'))
			pywikibot.output(u'* nbMax = %i' % nbMax)
			
			namespaces = [0]
			if m3:
				namespaces_early = m3.group('namespaces').split(',')
				try:
					namespaces = [int(i) for i in namespaces_early]
				except:
					pywikibot.output(u'Erreur : des namespaces spécifiés ne sont pas des entiers')
			if ns_test:
				pywikibot.output(u'(ns_test is ON)')
				namespaces = namespaces_test_value
			pywikibot.output(u'* namespaces = %s' % namespaces)
			
			recurse = False
			if m4:
				recurse_string = m4.group('recurse')
				if recurse_string == 'oui' or recurse_string == '1':
					recurse = True
			if recurse_test:
				pywikibot.output(u'(recurse_test is ON)')
				recurse = recurse_test_value
			pywikibot.output(u'* recurse = %s' % recurse)
				
		else: #Si le modèle n'a pas été trouvé sur la page examinée
			pywikibot.output(u"aucun modèle {{Articles récents}} détecté sur la page %s" % main_page.title())
			continue
		
		listeRecents = text[(text.index(matchDebut1)+len(matchDebut1)):text.index(matchFin1)]
		
		# Permet d'enlever le premier élément (vide) de la liste
		listeRecents = listeRecents.split('\n# ')[1:]
		
		text = re.sub(re.compile(u"%s.*%s" % (matchDebut2, matchFin2), re.S), u"%s%s" % (matchDebut2, matchFin2), text)
		#####################
		
		# Au cas où il n'y aurait aucune nouvelle page mais
		# une ou des pages ayant été supprimée(s)
		exception_maj = False
		
		# Pour préciser le résumé d'édition
		precisions_comment = u""
		
		#####################
		### Vérification des pages récentes actuelles (en cas de suppression)
		#####################
		for titre_article in listeRecents:
			#print re.sub(u"\[\[(.*)\]\]", "\\1", titre_article)
			page = pywikibot.Page(site, re.sub(u"\[\[(.*)\]\]", "\\1", titre_article)) # Pour enlever les crochets : [[…]].
			#print page
			try:
				# Si la page existe toujours et n'est pas une
				# redirection, on la laisse dans la liste…
				page.get()
			except pywikibot.NoPage:
				pywikibot.output(u"La page %s n'existe plus." % page.title(asLink=True))
				
				pywikibot.output(u"Suppression de la page %s de la liste listeRecents" % page.title(asLink=True))
				precisions_comment += (u"; - %s" % titre_article)
				listeRecents.remove(titre_article)
			except pywikibot.IsRedirectPage:
				pywikibot.output(u"La page %s n'est plus qu'une redirection."  % page.title(asLink=True))
				
				nouvelle_page = page.getRedirectTarget()
				pywikibot.output(u"Modification du titre la page %s (renommée en %s) de la liste listeRecents" % (page.title(asLink=True), nouvelle_page.title(asLink=True)))
				precisions_comment += (u"; - %s ; + %s" % (titre_article, nouvelle_page.title(asLink=True)))
				listeRecents[listeRecents.index(titre_article)] = nouvelle_page.title(asLink=True)
			except:
				pywikibot.output(u"Erreur inconnue lors du traitement de la page %s"  % page.title(asLink=True))
			else:
				# Si pas d'erreur : on passe à la page suivante
				continue
			
			# Si on arrive ici, c'est qu'il y a eu une erreur
			# (pywikibot.NoPage ou pywikibot.IsRedirectPage)
			# On force la mise à jour de la page, même si aucun nouvel article
			# récent n'est trouvé.
			exception_maj = True
		
		if precisions_comment:
			precisions_comment = precisions_comment[2:] # Pour supprimer le '; '
		#####################
		
		#####################
		### Recherches des articles nouveaux
		#####################
		precisions_comment2 = u""
		
		list_new = list()
		
		cat = pywikibot.Category(site, titre_categorie)
		
		# Permet de récupérer un pywikibot.Timestamp de la dernière
		# modification de la page
		timestamp = main_page.editTime()
		pywikibot.output(timestamp)
		
		# Permet de ne générer que la liste des articles ajoutés à la
		# catégorie après la dernière modification de la page
		# contenant le modèle {{Articles récents}}.
		#list_new.extend([page for page in site.categorymembers(cat, starttime=timestamp, sortby='timestamp', namespaces=[0])])
		#pywikibot.output(str([page for page in cat.articles(starttime=timestamp, sortby='timestamp', namespaces=namespaces, recurse=recurse)]))
		list_new.extend([page for page in cat.articles(starttime=timestamp, sortby='timestamp', namespaces=namespaces, recurse=recurse)])
		#print list_new
		
		# NB : exception_maj peut être passer à True si un article
		# a été supprimé de la catégorie. 
		if len(list_new) == 0 and not exception_maj:
			# Inutile d'aller plus loin s'il n'y a aucun nouvel article.
			continue
		
		# Permet de mettre les nouvelles pages comme des titres : 
		# nécessaires plus loin !
		list_new = [page.title(asLink = True) for page in list_new]
		
		# Permet de récupérer des infos sur la catégorie.
		# NB : Si ralentit le script, l'item cat_info['pages']
		#      correspondant au nombre de pages contenues
		#      dans la catégorie doit pouvoir être remplacé
		#      par len(listeCategorie) + len(list_new).
		cat_info = site.categoryinfo(cat)
		pywikibot.output(cat_info)
		
		for titre_page in list_new:
			# NB : titre_page est du type [[Nom de la page]]
			pywikibot.output(u"Nouvelle page : %s" % titre_page)
			if not titre_page in listeRecents:
				pywikibot.output("phase 1")
				precisions_comment2 += (u"; + %s" % titre_page)
			else:
				# Si l'article se trouve déjà dans la liste listeRecents
				# il est inutile de le rajouter à nouveau.
				list_new.remove(titre_page)
				
				# Re-vérification pour voir si list_new contient toujours
				# au moins une page.
				if len(list_new) == 0 and not exception_maj:
					# Inutile d'aller plus loin s'il n'y a aucun nouvel article.
					continue
		
		if precisions_comment: # Si precisions_comment contient déjà des infos (suppression de pages)
			precisions_comment += precisions_comment2
		else:			
			precisions_comment = precisions_comment2[2:] # Pour supprimer le '; '
		
		
		# Pour compléter le résumé d'édition
		comment = comment % {'nombre_articles': cat_info['pages'], 'precision_pages': precisions_comment}
		#####################
		
		#list_new.sort()
		
		#####################
		### Création de la liste des articles récents
		#####################
		liste_nouveaux_recents = list()
		liste_nouveaux_recents.extend(list_new)
		# Si le nombre d'articles nouveaux est strictement au nombre maximum
		# d'articles récents qui doivent figurer.
		if len(liste_nouveaux_recents) < nbMax:
			i = 0
			while len(liste_nouveaux_recents) != nbMax:
				if len(listeRecents) < i + 1:
					# Dans le cas où la liste listeRecents ne contiendrait pas
					# assez d'éléments.
					break
				liste_nouveaux_recents.append(listeRecents[i])
				i += 1
				if i == len(listeRecents): # Pourrait provoquer une erreur de longueur
					break
		elif len(liste_nouveaux_recents) > nbMax:
			liste_nouveaux_recents = liste_nouveaux_recents[0:(nbMax-1)]
		
		# La liste liste_nouveaux_recents contient désormais
		# nbMax articles récents exactement
		
		liste_nouveaux_recents_string = u"<!-- Ce tableau est créé automatiquement par un robot. Articles Récents DEBUT -->"
		for titre_article in liste_nouveaux_recents:
			liste_nouveaux_recents_string += u'\n# %s' % titre_article
		
		liste_nouveaux_recents_string += u"\n<!-- Ce tableau est créé automatiquement par un robot. Articles Récents FIN -->"
		#####################
		
		#####################
		### Mise à jour du contenu de la page
		#####################		
		new_text = text
		
		# Mise à jour de la liste des articles récents (listeRecents)
		new_text = re.sub(re.compile(u'%s.*%s' % (matchDebut1, matchFin1), re.S), liste_nouveaux_recents_string, new_text)
		
		# Mise à jour de la liste des articles de la catégorie (listeCategorie)
		#new_text = re.sub(re.compile(u'%s.*%s' % (matchDebut2, matchFin2), re.S), listeCategorie_string_new, new_text)
		
		pywikibot.output(new_text)
		
		#pywikibot.showDiff(main_page.get(), new_text)
		pywikibot.output(u'Commentaire: %s' % comment)
		
		#choice = pywikibot.inputChoice(u'Do you want to accept these changes?', ['Yes', 'No'], ['y', 'N'], 'N')
		#if choice == 'y':
		#	main_page.put(new_text, comment = comment)
		if not dry:
			main_page.put(new_text, comment = comment)
		else:
			pywikibot.showDiff(main_page.get(), new_text)
		#####################


if __name__ == '__main__':
    try:
        main()
    except Exception, myexception:
        almalog2.error(u'maj_articles_recents', u'%s %s'% (type(myexception), myexception.args))
        raise
    finally:
        pywikibot.stopme()
