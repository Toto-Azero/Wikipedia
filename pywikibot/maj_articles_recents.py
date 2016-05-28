#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
** (fr) **
Ce bot met à jour les modèles {{Articles récents}} sur fr.wikipedia.

** (en) **
This bot updates the {{Articles récents}} templates on fr.wikipedia.


TODO: cf. rev 2055 & 2056
Dernières modifications :
* 2058 : introduction du paramètre strip dans la fonction  check_and_return_parameter
         (fonction partagée avec d'autres scripts)
* 2057 : correction problème doublon en cas de fusion de deux pages présentes
         dans la liste en une seule page
* 2056 : rétablissement comportement précédent pour suppression à tort (bug doublon),
         à corriger
* 2055 : problème encodage + suppression à tort des articles rajoutés sur la page
        lorsque entre deux mises à jour du bot.
* 2052 : résolution problème encodage
* 2050 : ajout de la date rétroactif
* 2002 : correction encodage
* 2001 : correction date
* 2000 : gestion date
* 1900 : gestion SQL
* 1754 : ajout du paramètre 'delai'
"""
#
# (C) Toto Azéro, 2011-2016
#
# Distribué sous licence GNU GPLv3
# Distributed under the terms of the GNU GPLv3 license
# http://www.gnu.org/licenses/gpl.html
#
__version__ = '$Id: maj_articles_recents.py 2057 2016-02-07 17:40:07 (CET) Toto Azéro $'
#
import almalog2
import pywikibot
from pywikibot import pagegenerators, config, textlib
import re, time, datetime, _mysql
import locale

def end_page(main_page, date_debut_traitement, first_passage):
	db=_mysql.connect(host='tools-db', db='s51245__totoazero', read_default_file="/data/project/totoazero/replica.my.cnf")
	if not first_passage:
		db.query('UPDATE maj_articles_recents SET last="%s" WHERE page="%s"' % (date_debut_traitement.strftime("%Y-%m-%d %H:%M:%S"), main_page.title().replace('"', '\\"').encode('utf-8')))
	else:
		db.query('INSERT INTO maj_articles_recents VALUES("%s","%s")' % (main_page.title().replace('"', '\\"').encode('utf-8'), date_debut_traitement.strftime("%Y-%m-%d %H:%M:%S")))

# TODO: à mutualiser
def check_and_return_parameter(template, parameter, default_value=None, strip=True):
	if template.has_key(parameter):
		value = template[parameter]
		value = re.sub("<!-- .* -->", "", value) # Suppression d'éventuels commentaires
		if strip:
			value = value.strip()
		pywikibot.output(u'* %s = %s' % (parameter, value))
		if value:
			return value
		else:
			pywikibot.output(u"* %s missing : %s was taken instead" % (parameter, default_value))
			return default_value
	else:
		if default_value != None:
			pywikibot.output(u"* %s missing : %s was taken instead" % (parameter, default_value))
			return default_value
		else:
			pywikibot.output(u"* %s missing" % parameter)
			return None

def find_date(article, category):
	"""
	article is pywikibot.Page
	category is pywikibot.Category
	"""
	try:
		namespace_id = article.namespace().id
	except:
		namespace_id = int(article.namespace())
		
	title = article.title(asLink=False, withNamespace=False, underscore = True)
	
	frwiki_p = _mysql.connect(host='frwiki.labsdb', db='frwiki_p', read_default_file="/data/project/totoazero/replica.my.cnf")
	pywikibot.output('SELECT page_title, page_id FROM page where page_title = "%s" AND page_namespace=%i' % (title.replace('"', '\\"').encode('utf-8'), namespace_id))
	results=frwiki_p.query('SELECT page_title, page_id FROM page where page_title = "%s" AND page_namespace=%i' % (title.replace('"', '\\"').encode('utf-8'), namespace_id))
	results=frwiki_p.store_result()
	result=results.fetch_row(maxrows=0)
	pywikibot.output(result)
	
	if result:
		id = result[0][1]
	else:
		pywikibot.output(u"article %s introuvable" % title.decode('utf-8'))
		return None
	pywikibot.output('SELECT cl_from, cl_timestamp FROM categorylinks WHERE cl_from = %s AND cl_to = "%s"' % (id.encode('utf-8'), category.title(asLink = False, underscore = True, withNamespace = False).encode('utf-8')))
	results=frwiki_p.query('SELECT cl_from, cl_timestamp FROM categorylinks WHERE cl_from = %s AND cl_to = "%s"' % (id.encode('utf-8'), category.title(asLink = False, underscore = True, withNamespace = False).encode('utf-8')))
	results=frwiki_p.store_result()
	result=results.fetch_row(maxrows=0)
	if result:
		timestamp = pywikibot.Timestamp.strptime(result[0][1], "%Y-%m-%d %H:%M:%S")
		pywikibot.output(u"Found: %s" % timestamp)
		return timestamp
	else:
		pywikibot.output(u"pas de date trouvée pour %s" % title.decode('utf-8'))
		return None

def main():
	config.use_mwparserfromhell = False
	locale.setlocale(locale.LC_ALL, 'fr_FR.utf-8')

	db = False

	global test
	global dry
		
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
	site = pywikibot.Site()
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

	if ns_test:
		pywikibot.output(u'(ns_test is ON)')

	
	for main_page in gen:
		try:
			comment = comment_modele
			pywikibot.output(u"\n========================\nTraitement de %s\n========================" % main_page.title())
			text = main_page.get()

			#####################
			### Récupération des informations sur la page
			#####################
			templates = textlib.extract_templates_and_params(text)
			template_in_use = None
			for tuple in templates:
				if tuple[0] != u'Articles récents':
					continue
				else:
					template_in_use = tuple[1]
					break

			if not template_in_use:
				pywikibot.output(u"Aucun modèle {{Articles récents}} détecté sur la page %s" % main_page.title())
				continue

			titre_categorie = check_and_return_parameter(template_in_use, u'catégorie')
			if not titre_categorie:
				continue
			cat = pywikibot.Category(site, titre_categorie)
	
			nbMax = check_and_return_parameter(template_in_use, 'nbMax', 10)
			try:
				nbMax = int(nbMax)
			except:
				pywikibot.output(u'Erreur : nbMax incorrect')
				continue
		
			namespaces = check_and_return_parameter(template_in_use, 'namespaces', '0')
			namespaces = namespaces.split(',')
			try:
				namespaces = [int(k) for k in namespaces]
			except:
				pywikibot.output(u'Erreur : des namespaces spécifiés ne sont pas des entiers')
				continue

			recurse = check_and_return_parameter(template_in_use, 'recurse', '0')
			if recurse.lower().strip() in ('oui', '1'):
				recurse = True
			else:
				recurse = False

			delai_creation = check_and_return_parameter(template_in_use, 'delai', '0')
			try:
				delai_creation = int(delai_creation)
			except:
				pywikibot.output(u'Erreur : delai incorrect')
				continue

			format_date = check_and_return_parameter(template_in_use, u'date') or None
			if format_date:
				try:
					test_date = datetime.datetime.now()
					test_date.strftime(format_date)
				except:
					format_date = None
					pywikibot.output(u'Erreur : format de date incorrect')

			puce = check_and_return_parameter(template_in_use, 'puces', '#')
			
			listeRecents = text[(text.index(matchDebut1)+len(matchDebut1)):text.index(matchFin1)]

			# Permet d'enlever le premier élément (vide) de la liste
			listeRecents = listeRecents.split('\n%s ' % puce)[1:]

			listeRecents_old = [page for page in listeRecents]
			listeRecents = list()
			dico_dates_presentes = {}
			
			for recent in listeRecents_old:
				r = re.search(u"(\[\[.*\]\]) ?(\(.+\))?", recent)
				if r:
					listeRecents.append(r.group(1))
					if r.group(2):
						dico_dates_presentes[r.group(1)] = r.group(2)[1:-1]
				else:
					pass

			text = re.sub(re.compile(u"%s.*%s" % (matchDebut2, matchFin2), re.S), u"%s%s" % (matchDebut2, matchFin2), text)
			#####################

			# Au cas où il n'y aurait aucune nouvelle page mais
			# une ou des pages ayant été supprimée(s)
			exception_maj = False

			# Pour préciser le résumé d'édition
			precisions_comment = u""
			
			pywikibot.output('stade 0')
			#####################
			### Vérification des pages récentes actuelles (en cas de suppression)
			#####################
			for titre_article in listeRecents:
				try:
					page = pywikibot.Page(site, re.sub(u"\[\[(.*)\]\]", "\\1", titre_article)) # Pour enlever les crochets : [[…]].
					# Si la page existe toujours et n'est pas une
					# redirection, on la laisse dans la liste…
					page.get()
					
					if format_date and not dico_dates_presentes.has_key(titre_article) and find_date(page, cat):
						# Date trouvée alors qu'elle n'y était pas.
						exception_maj = True
						dico_dates_presentes[titre_article] = find_date(page, cat).strftime(format_date)
						
				except pywikibot.NoPage:
					pywikibot.output(u"La page %s n'existe plus." % page.title(asLink=True))
		
					pywikibot.output(u"Suppression de la page %s de la liste listeRecents" % page.title(asLink=True))
					precisions_comment += (u"; - %s" % titre_article)
					listeRecents.remove(titre_article)
		
					# On force la mise à jour de la page, même si aucun nouvel article
					# récent n'est trouvé.
					exception_maj = True
				except pywikibot.IsRedirectPage:
					pywikibot.output(u"La page %s n'est plus qu'une redirection."  % page.title(asLink=True))
		
					try:
						nouvelle_page = page.getRedirectTarget()
						pywikibot.output(u"Modification du titre la page %s (renommée en %s)" % (page.title(asLink=True), nouvelle_page.title(asLink=True, withSection=False)))
						precisions_comment += (u"; - %s ; + %s" % (titre_article, nouvelle_page.title(asLink=True, withSection=False)))
						
						if not nouvelle_page.title(asLink=True, withSection=False) in listeRecents:
							listeRecents[listeRecents.index(titre_article)] = nouvelle_page.title(asLink=True, withSection=False)
						else:
							pywikibot.output(u"La page destination était déjà présente dans la liste")
							listeRecents.pop(listeRecents.index(titre_article))
						
						# On force la mise à jour de la page, même si aucun nouvel article
						# récent n'est trouvé.
						exception_maj = True
							
					except:
						pywikibot.output(u"an error occured (CircularRedirect?)")
				#except KeyboardInterrupt:
				#	pywikibot.stopme()
				except:
					try:
						pywikibot.output(u"Erreur inconnue lors du traitement de la page %s"  % page.title(asLink=True))
					except:
						pywikibot.output(u"Erreur inconnue lors du traitement d'une page")
				else:
					# Si pas d'erreur : on passe à la page suivante
					continue
	

			if precisions_comment:
				precisions_comment = precisions_comment[2:] # Pour supprimer le '; '
			#####################

			#####################
			### Recherches des articles nouveaux
			#####################
			precisions_comment2 = u""

			# Récupération de la dernière mise à jour de la page par le bot		
			db=_mysql.connect(host='tools-db', db='s51245__totoazero', read_default_file="/data/project/totoazero/replica.my.cnf")
			results=db.query('SELECT last FROM maj_articles_recents WHERE page="%s"' % main_page.title().replace('"', '\\"').encode('utf-8'))
			results=db.store_result()
			result=results.fetch_row(maxrows=0)
			pywikibot.output(("last check was " + str(result)))
			if result:
				first_passage = False
				t = result[0][0]
				timestamp = pywikibot.Timestamp.strptime(t, "%Y-%m-%d %H:%M:%S")

				# Permet de ne générer que la liste des articles ajoutés à la
				# catégorie après la dernière modification de la page
				# contenant le modèle {{Articles récents}}.
				#list_new.extend([page for page in site.categorymembers(cat, starttime=timestamp, sortby='timestamp', namespaces=[0])])
				list_new = [page for page in cat.articles(starttime=timestamp, sortby='timestamp', namespaces=namespaces, recurse=recurse)]
				list_new.reverse()
	
			else: # nouvelle page, premier passage du bot
				first_passage = True
	
				timestamp = main_page.editTime()
				if delai_creation > 0:
					timestamp -= datetime.timedelta(hours = delai_creation)
	
				# Génération de la première liste, pour éviter si possible de
				# laisser la page vide.	
				list_new = [page for page in cat.newest_pages(total=nbMax)]
				
				# TODO : mieux ?
				#list_new = [page for page in cat.articles(sortby='timestamp', namespaces=namespaces, recurse=recurse)]

			pywikibot.output('stade 2')
			now = datetime.datetime.now()

			# NB : exception_maj peut être passer à True si un article
			# a été supprimé de la catégorie. 
			if len(list_new) == 0 and not exception_maj:
				# Inutile d'aller plus loin s'il n'y a aucun nouvel article.
				end_page(main_page, now, first_passage)
				continue

			# Liste des pages pour requête SQL sur base frwiki_p
			list_new_str = '("'
			list_new_str += '", "'.join([page.title(asLink = False, underscore = True).replace('"', '\\"') for page in list_new])
			list_new_str += '")'
			pywikibot.output(list_new_str)

			# Fonctionne uniquement avec les pages du ns 0 pour le moment
			frwiki_p = _mysql.connect(host='frwiki.labsdb', db='frwiki_p', read_default_file="/data/project/totoazero/replica.my.cnf")
			pywikibot.output('SELECT page_title, page_id FROM page where page_title IN %s AND page_namespace=0' % list_new_str.encode('utf-8'))
			results=frwiki_p.query('SELECT page_title, page_id FROM page where page_title IN %s AND page_namespace=0' % list_new_str.encode('utf-8'))
			results=frwiki_p.store_result()
			result=results.fetch_row(maxrows=0)
			pywikibot.output(result)

			dico_result = {}
			for tuple in result:
				title = tuple[0]
				id = tuple[1]
				dico_result[title] = id
			pywikibot.output(dico_result)

			dico_timestamp = {}

			pywikibot.output('stade 3')
			frwiki_p = _mysql.connect(host='frwiki.labsdb', db='frwiki_p', read_default_file="/data/project/totoazero/replica.my.cnf")
			for key in dico_result:
				id = dico_result[key]
	
				pywikibot.output('SELECT cl_from, cl_timestamp FROM categorylinks WHERE cl_from = %s AND cl_to = "%s"' % (id.encode('utf-8'), cat.title(asLink = False, underscore = True, withNamespace = False).encode('utf-8')))
				results=frwiki_p.query('SELECT cl_from, cl_timestamp FROM categorylinks WHERE cl_from = %s AND cl_to = "%s"' % (id.encode('utf-8'), cat.title(asLink = False, underscore = True, withNamespace = False).encode('utf-8')))
				results=frwiki_p.store_result()
				result=results.fetch_row(maxrows=0)
				if result:
					dico_timestamp[key.decode('utf-8')] = pywikibot.Timestamp.strptime(result[0][1], "%Y-%m-%d %H:%M:%S")
				else:
					pywikibot.output(u"pas de date trouvée pour %s" % key.decode('utf-8'))

			pywikibot.output(dico_timestamp)

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

			pywikibot.output('stade 4')
			list_new_old = list()
			list_new_old.extend(list_new)
			
			pywikibot.output('delai_creation is %s' % delai_creation)
			#for titre_page in list_new_old:
			#	print titre_page

			for titre_page in list_new_old:
				# NB : titre_page est du type [[Nom de la page]]
				pywikibot.output("----------")
				pywikibot.output(u"Page récemment ajoutée : %s" % titre_page)
				if not titre_page in listeRecents:
					if delai_creation:
						# Délai imposé (en heures) depuis la création de l'article,
						# au-delà duquel l'article récemment ajouté à la catégorie
						# ne doit pas figurer dans la liste.
						# Exemple :  delai_creation = 24
						# 	 => le bot liste uniquement les articles créés il y
						# 		a moins de 24h.
						page = pywikibot.Page(site, titre_page[2:-2])
			
						# NB : date_creation et date_plus_petite_requise
						#      sont du type pywikibot.Timestamp
						date_creation = page.getVersionHistory()[-1][1]
						pywikibot.output(date_creation)
			
						if delai_creation > 0:
							date_plus_petite_requise = pywikibot.Timestamp.now() - datetime.timedelta(hours=delai_creation)
						elif delai_creation == -1:
							# 'timestamp' a été défini plus haut comme étant la date de dernière
							# édition du bot sur la page.
							date_plus_petite_requise = timestamp
			
						pywikibot.output(date_plus_petite_requise)
			
						if date_plus_petite_requise > date_creation:
							pywikibot.output(u"Vérification du délai : Non")	
							pywikibot.output(u"La page ne satisfait pas le délai depuis la création imposé.")
							list_new.remove(titre_page)
							continue
						else:
							pywikibot.output(u"Vérification du délai : OK")
		
					precisions_comment2 += (u"; + %s" % titre_page)
				else:
					# Si l'article se trouve déjà dans la liste listeRecents
					# il est inutile de le rajouter à nouveau.
					list_new.remove(titre_page)
					
					pywikibot.output(u"L'article était déjà présent sur la page.")
		
					# Re-vérification pour voir si list_new contient toujours
					# au moins une page.
					if len(list_new) == 0 and not exception_maj:
						# Inutile d'aller plus loin s'il n'y a aucun nouvel article.
						pywikibot.output('Nothing left.')
						continue
		
			# Re-vérification pour voir si list_new contient toujours
			# au moins une page.
			if len(list_new) == 0 and not exception_maj:
				# Inutile d'aller plus loin s'il n'y a aucun nouvel article.
				end_page(main_page, now, first_passage)
				continue

			if precisions_comment: # Si precisions_comment contient déjà des infos (suppression de pages)
				precisions_comment += precisions_comment2
			else:			
				precisions_comment = precisions_comment2[2:] # Pour supprimer le '; '

			pywikibot.output('stade 5')

			# Pour compléter le résumé d'édition
			comment = comment % {'nombre_articles': cat_info['pages'], 'precision_pages': precisions_comment}

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

			pywikibot.output('stade 6')
			liste_nouveaux_recents_string = u"<!-- Ce tableau est créé automatiquement par un robot. Articles Récents DEBUT -->"
			for titre_article in liste_nouveaux_recents:
				liste_nouveaux_recents_string += u'\n%s %s' % (puce, titre_article)
				if format_date and dico_timestamp.has_key(titre_article[2:-2].replace(' ', '_')):
					pywikibot.output('stade 6-1')
					pywikibot.output(dico_timestamp[titre_article[2:-2].replace(' ', '_')].strftime(format_date))
					try:
						liste_nouveaux_recents_string += (' (' + dico_timestamp[titre_article[2:-2].replace(' ', '_')].strftime(format_date).decode('utf-8') + ')')
					except:
						try:
							liste_nouveaux_recents_string += (' (' + dico_timestamp[titre_article[2:-2].replace(' ', '_')].strftime(format_date) + ')')
						except:
							raise "erreur au stade 6-1"
					
				elif dico_dates_presentes.has_key(titre_article):
					pywikibot.output('stade 6-2')
					pywikibot.output(dico_dates_presentes[titre_article])
					try:
						liste_nouveaux_recents_string += (' (' + dico_dates_presentes[titre_article] + ')')
					except:# UnicodeEncodeError:
						try:
							liste_nouveaux_recents_string += (' (' + dico_dates_presentes[titre_article].decode('utf-8') + ')')
						except:
							raise "erreur au stade 6-2"

			liste_nouveaux_recents_string += u"\n<!-- Ce tableau est créé automatiquement par un robot. Articles Récents FIN -->"
			#####################

			#####################
			### Mise à jour du contenu de la page
			#####################		
			new_text = text
			
			pywikibot.output('stade 7')
			# Mise à jour de la liste des articles récents (listeRecents)
			new_text = re.sub(re.compile(u'%s.*%s' % (matchDebut1, matchFin1), re.S), liste_nouveaux_recents_string, new_text)
		
			pywikibot.output(new_text)

			pywikibot.output(u'Commentaire: %s' % comment)
		
			if not dry:
				main_page.put(new_text, comment = comment)
				end_page(main_page, now, first_passage)
			else:
				pywikibot.showDiff(main_page.get(), new_text)
			#####################
		except Exception, myexception:
			pywikibot.output("Erreur lors du traitement de la page %s" % main_page.title(asLink=True))
			almalog2.error(u'maj_articles_recents', u'traitement de %s : %s %s'% (main_page.title(asLink=True), type(myexception), myexception.args))

if __name__ == '__main__':
	try:
		main()
	except Exception, myexception:
		if not (test or dry):
			almalog2.error(u'maj_articles_recents', u'%s %s'% (type(myexception), myexception.args))
		raise
	finally:
		pywikibot.stopme()