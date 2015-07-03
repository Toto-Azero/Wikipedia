#!/usr/bin/python
# -*- coding: utf-8  -*-
"""

Dernières modifications :
* 0165 : espace de noms principal seulement, gestion de nouveaux modèles
* 0162 : gestion du modèle {{Vérifiabilité}}
* 0161 : gestion du modèle {{Vérifiabilité}}
* 0160 : gestion du modèle {{Article sans source}}
* 0159 : correction erreur unicode + adaptation aux Labs
"""
#
# (C) Toto Azéro, 2013-2015
#
# Distribué sous licence GNU GPLv3
# Distributed under the terms of the GNU GPLv3 license
# http://www.gnu.org/licenses/gpl.html
#
__version__ = '$Id: modeles_sans_dates.py 0165 2015-07-03 14:31:40 (CEST) Toto Azéro $'
#

import pywikibot
import almalog2
import re, time, datetime
import locale

class BotPrecisionModele:
	def __init__(self):
		self.summary = u"Bot: Précision du paramètre 'date' %s dans le modèle {{%s}}"
		self.titres_modeles_initiaux = [u"À sourcer", u"Admissibilité à vérifier", u"À wikifier", \
			u"Article sans source", u"Vérifiabilité", u"Orphelin", u"Guide pratique", u"Section guide pratique", \
			u"Section guide pratique", u"Section à wikifier", u"Section à sourcer" ]
		self.site = pywikibot.Site()
		self.liste_titres_cats = [u"Admissibilité à vérifier, date manquante", u"Article à wikifier, date manquante", \
			u"Article sans source, date manquante", u"Article non vérifiable, date manquante", \
			u"Article orphelin, date manquante", u"Guide pratique, date manquante", \
			u"Article manquant de référence depuis date inconnue" ]
		#u"Article avec section à wikifier, date manquante"
		
	def generate_liste_pages_modele(self, modeles):
		# Génère la liste complète des modèles utilisables (redirections comprises)
		liste_titres = []
		for titre_modele in modeles:
			page = pywikibot.Page(self.site, titre_modele, ns=10)
			liste_titres.append(page)
			liste_titres_redirect = [p for p in page.backlinks(filterRedirects=True)]
			# ex : liste_titres_redirect =
			#			[u'Sources', u'A sourcer', u'Source ?']
			liste_titres.extend(liste_titres_redirect)
		
		return liste_titres
	
	def operate(self, page, liste_modeles):
		dict = {}
		modeles_modifies_str = u""
		count_modeles_modifies = 0
		add_date = False
		
		text = None
		
		for couple in page.templatesWithParams():
			for modele in liste_modeles:
				if couple[0]==modele:
					dict[modele] = couple[1]
		
		for modele in dict:
		# NB : modele est de type pywikibot.Page
			add_date = True
			re_params = u""
			pywikibot.output(u"modele : %s" % modele.title(withNamespace=False))
			if dict[modele]:
				for param in dict[modele]:
					re_params += (u" *\| *%s" % param) # Paramètres allant avec le modèle
					if re.search(u"^date *=.+", param):
						param_date = re.search(u"^date *=.+", param)
						add_date = False
						break
			
			pywikibot.output("add_date = %s" % unicode(add_date))
			pywikibot.output("re_params = %s" % unicode(re_params))
			
			if add_date == True:
				titre_modele = modele.title(withNamespace=False)
				
				# Permet de rechercher le modèle (avec ses paramètres) dans le texte
				pywikibot.output(u"{ *{ *([%s%s]%s%s)*} *}" % (titre_modele[0].lower(), titre_modele[0].upper(), titre_modele[1:], re_params))
				re_titre_modele = re.compile(u"{ *{ *([%s%s]%s%s)*} *}" % (titre_modele[0].lower(), titre_modele[0].upper(), titre_modele[1:], re_params))
				
				now = datetime.datetime.now()
				date = now.strftime(u"%B %Y")
				
				# Permet de ne charger le texte de la page qu'une seule fois
				# Mis ici et non au début de la fonction car permet de ne pas charger
				# le texte si aucune modification n'est nécessaire.
				if not text:
					text = page.get()
	
				match_modele = re_titre_modele.search(text)
				pywikibot.output(match_modele.group(1))
				new = u"{{%s|date=%s}}" % (match_modele.group(1), date.decode('utf-8'))
				pywikibot.output(new)
				
				text = text.replace(match_modele.group(0), new)
				modeles_modifies_str += u"[[Modèle:%(modele)s|{{%(modele)s}}]], " % {'modele':titre_modele}
				count_modeles_modifies += 1
		
		modeles_modifies_str = modeles_modifies_str[0:-2] # Enlever le ', ' en trop
		if count_modeles_modifies == 1:
			comment = u"Bot: Ajout du paramètre 'date' dans le modèle %s" % modeles_modifies_str
			page.put(text, comment = comment)
		else:
			comment = u"Bot: Ajout du paramètre 'date' dans les modèles %s" % modeles_modifies_str
			page.put(text, comment = comment)
					
	def run(self):
		pywikibot.output(u"Initialisation en cours… date : %s" % datetime.datetime.now())
		t1 = time.time()
		
		# Génère la liste des pages à traiter
		liste_pages_a_traiter = []
		for titre_cat in self.liste_titres_cats:
			cat = pywikibot.Category(self.site, titre_cat)
			liste_pages_a_traiter.extend([page for page in cat.articles(content=True, namespaces=[0])])
		
		if not liste_pages_a_traiter:
			pywikibot.output(u"Aucune page à traiter")
			return
		
		# Génère la liste complète des modèles utilisables (redirections comprises)
		self.liste_pages_modeles = self.generate_liste_pages_modele(self.titres_modeles_initiaux)
		
		for modele in self.liste_pages_modeles: pywikibot.output(modele)
		
		t2 = time.time()
		pywikibot.output(u"Initialisation terminée. Temps mis : %i secondes" % int(t2-t1))
		
		#liste_pages_a_traiter.append(pywikibot.Page(self.site, u'Utilisateur:Toto Azéro/Bac à sable 5'))
		
		# Analyse page par page
		for page in liste_pages_a_traiter:
			pywikibot.output(page)
			liste_pages_modeles = [couple[0] for couple in page.templatesWithParams()]
			
			# Intersection entre les listes self.liste_pages_modeles et liste_pages_modeles
			modeles_recherches_presents = list(set(self.liste_pages_modeles) & set(liste_pages_modeles))
			
			if modeles_recherches_presents:
				self.operate(page, modeles_recherches_presents)
		
def main():
	bot = BotPrecisionModele()
	bot.run()

if __name__ == "__main__":
	locale.setlocale(locale.LC_ALL, 'fr_FR.utf8')
	
	try:
		main()
	except Exception, myexception:
		almalog2.error(u'modeles_sans_dates.py', u'%s %s'% (type(myexception), myexception.args))
		raise
	finally:
		pywikibot.stopme()