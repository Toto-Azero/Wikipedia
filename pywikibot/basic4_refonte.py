#!/usr/bin/python
# -*- coding: utf-8  -*-
"""
** (fr) **
Ce bot extrait l'infobox d'un article et effectue certaines modifications
dessus.

Support des modifications mineures et majeures (la page ne sera mise à jour
uniquement lorsqu'au moins une modification majeure aura été effectuée,
et, dans ce cas seulement, les modifications mineures seront prises
en compte).

Les paramètres optionneles suivants sont supportés :

-dry			  N'autorise aucune modification réelle, mais montre
				  seulement ce qui aurait été modifié.

-reprise:		  Permet de reprendre le traitement à une page donnée.

-debug			  Passe en mode debug.

-async			  Active la publication asynchrone des pages : leur
				  publication sera faite durant un laps de temps libre
				  afin de permettre une meilleure optimisation du temps.

TODO/À faire :
	- introduction des arguments avec la commande pywikibot.handleArgs()
		✓ fait pour le(s) paramètre(s) suivant(s):
			* -reprise:
		➙ reste d'autres paramètres à introduire
	- gestion automatique de la variable titreModeleOldRe en prenant
	  les titres des pages de redirection du modèle
	  (i.e. titreModeleOldRe = u'titre modele|redirection 1|redirection 2')
		✓ fait : en phase de test (cf. ƒ2)
	- passage sur pywikibot rewrite
		✓ fait
	- commenter les différents remplacements effectués pour éviter
	  les erreurs (cf. ƒ4)
	  	✗ pas fait

** (en) **
(NB: Maybe this version is less developped than the French one.
	 So if you speak French, please read the version above)

This bot extracts the infobox of an article and do some changes on it.

Support of minor and major modifications (the page will be updated
only when at least one major change will have be done, and, in this case
only, minor changes are so taken into account).


The following optional parameters are supported:

-dry			  Doesn't do any real changes, but only shows what
				  would have been changed.

-reprise:		  Allows to restart the treatment from a given page.

-debug			  Go in the debug mode.

-async			  Put the pages asynchronously.
"""
#
# (C) Pywikipedia bot team, 2006-2010
# (C) Toto Azéro, 2010, 2011
#
# Distribué sous licence MIT.
# Distributed under the terms of the MIT license.
#
__version__ = '$Id: basic4_refonte.py 1005 $'

import pywikibot
from pywikibot import pagegenerators, catlib
import re

class InfoboxBot:
	def __init__(self, dry, reprise, titreReprise, debug, async):
		"""
		Constructor. Parameters:
			* generator - The page generator that determines on which pages
						  to work on.
			* dry	   - If True, doesn't do any real changes, but only shows
						 what would have been changed.
		"""
#		self.generator = generator
		self.dry = dry
		self.reprise = reprise
		self.titreReprise = titreReprise
		self.debug = debug
		self.async = async
		self.site = pywikibot.getSite()

		# (fr) : Résumé de modification
		# (en) : Edit summary
		self.summary = u"[[WP:RBOT]]) (Bot: Correction typographique dans l'[[Modèle:Infobox Footballeur|Infobox Footballeur]]"

	def debugMode(self):
		print u'dry = %r' % self.dry
		print u'reprise = %r' % self.reprise
		print u'titreReprise = %s' % self.titreReprise

	def run(self):
		#############################################
		##### (fr) : Paramètres modifiables
		##### (en) : Modifiable parameters
		#############################################

		exceptions = []

		titreModeleOld = u'Infobox Stade'

		## Obsolète : cf. ƒ2 plus bas
		# ‹!› Ne pas mettre de parenthèses !
		#titreModeleOldRe = u'[iI]nfobox Émission de télévision|[iI]nfobox [Tt]élévision|[Ii]nfobox Télévision nouveau|[Ii]nfobox TV émission'

		modeleOld = pywikibot.Page(self.site, u'Modèle:%s' % titreModeleOld)
		modeleNew = u'\\1Infobox Stade'

		checkNamespace = True
		checkNumberNamespace = 0
		onlySaveIfMajorChange = True
		ajoutParametresAbsents = False
		alignementSignesEgal = True

		useCategories = False
		listeTitresCategories = [u"Détection temporaire paramètre float Infobox ville"]

		#### Expérimental : ƒ2 ####
		"""
		Recherche automatique des redirections afin de remplir la
		variable titreModeleOldRe avec une expression régulière.
		‹!› La variable titreModeleOldRe ne doit pas contenir de
			parenthèses codantes, auquel cas les expressions régulières
			utilisant la variable seraient faussées.
		"""
		premiereLettreMinuscule = titreModeleOld[0:1].lower()
		premiereLettreMajuscule = titreModeleOld[0:1].upper()
		resteTitre = titreModeleOld[1:]
		titreModeleOldRe = u'[%s%s]%s' % (premiereLettreMinuscule, premiereLettreMajuscule, resteTitre)

		for page in modeleOld.getReferences(redirectsOnly = True):
			premiereLettreMinuscule = page.title(asLink = False)[0:1].lower()
			premiereLettreMajuscule = page.title(asLink = False)[0:1].upper()
			resteTitre = titreModeleOld[1:]
			titreModeleOldRe += u'|[%s%s]%s' % (premiereLettreMinuscule, premiereLettreMajuscule, resteTitre)
		############################

		## Obsolète : Remplacé par la détection de l'argument
		## '-reprise:' (voir fonction main()).
		# (fr) : Activer ce paramètre permet de reprendre le
		# 		 traitement à partir de la page donnée
		# (en) : Enable this parameter allows restarting the treatment
		# 		 form the page given
		#reprise = True
		#titreReprise = u"La Folle Route"

		##### (fr) : Modifications majeures #####
		##### (en) : Major changes #####

		## (fr) : Liste de recherches ##
		## (en) : Find list ##
		listeRechercheElements = {
		#1 : u'\n? *\| *surnom *= *.*'
		#1 : u'(\n? *\| *département *= [^\n]*\[ *\[ *[hH]autes[ -][pP]yrénées *\] *\](\n.*)*géoloc-département) *= *(\n|\})',
		#5 : u'(\n? *\| *département *= [^\n]*\[ *\[ *[hH]auts[ -][dD]e[ -][sS]eine]**\] *\](\n.*)*géoloc-département) *= *(\n|\})',
		#6 : u'(\n? *\| *département *= [^\n]*\[ *\[ *[sS]eine[ -][sS]aint[ -][dD]enis *\] *\](\n.*)*géoloc-département) *= *(\n|\})',
		#7 : u'(\n? *\| *département *= [^\n]*\[ *\[ *[Vv]al[ -][Dd]e[ -][mM]arne *\] *\](\n.*)*géoloc-département) *= *(\n|\})'
		#8 : u'(\n? *\| *département *= [^\n]*\[ *\[ *[sS]eine *\] *\](\n.*)*géoloc-département) *= *(\n|\})',
		#9 : u'(\n? *\| *département *= [^\n]*\[ *\[ *[sS]eine *\] *\](\n.*)*géoloc-département) *= *(\n|\})'
		#1 : u'(\n? *\| *)site production( *= *.*)',
		#2 : u"(\n? *\| *(précédé|suivi) *par *= *)''(.*)''"
		#3 : u'(\n? *\| *)carte2( *= *.*)',
		#4 : u'(\n? *\| *taille-logo *= *.*) *(px|cm|mm) *'
		#1 : re.compile(u'(alt moy *= *[0-9]*) *m *'),
		#2 : re.compile(u'(\| *)arrondissement( *= *)(.*)')
		#6 : u'(\n *\|.*) *= *\{ *\{ *[Ff][Oo][Rr][Mm][Aa][Tt][Nn][Uu][Mm] *: *([0-9]*) *\} *\}',
		#7 : u'(\n? *\| *région) *= *\[ *\[ *Région (.*)',
		#8 : u'(\n? *\| *région) *= *\[ *\[.*\| *([bB]retagne|[cC]entre).*\] *\]',
		#9 : u'(\n? *\| *région) *= *\[ *\[.*\| *[Rr]éunion.*\] *\]',
		#10: u'(.*) *= *[Nn]\.? *[Cc]\.? *',
		#1 : u'(\n? *\| *(longitude|latitude)) *= *([0-9]*)[°\'‘’" ]*([0-9]*)[°\'‘’" ]*([0-9]*)[°\'‘’" ]*[Ee](st)?',
		#2 : u'(\n? *\| *(longitude|latitude)) *= *([0-9]*)[°\'‘’" ]*([0-9]*)[°\'‘’" ]*([0-9]*)[°\'‘’" ]*([Oo](uest)?|[Ww](est)?)',
		#3 : u'(\n? *\| *(longitude|latitude)) *= *([0-9]*)[°\'‘’" ]*([0-9]*)[°\'‘’" ]*([0-9]*)[°\'‘’" ]*[Nn](ord)?',
		#4 : u'(\n? *\| *(longitude|latitude)) *= *([0-9]*)[°\'‘’" ]*([0-9]*)[°\'‘’" ]*([0-9]*)[°\'‘’" ]*[Ss](ud)?'
		#6 : u'(\n? *\| *(longitude|latitude) *= .*)//',
		#1 : u'\n? *\| *(float) *= *.*', ## Paramètres à supprimer
		#8 : re.compile(u'(\n?) *\| *Région *= *(.*)'),
		#1 : re.compile(ur'\| *coordonnées *=.*(.*\| *latitude *= *[^\n]+.*\| *longitude *= *[^\n]+\n|.*\| *longitude *= *[^\n]+.*\| *latitude *= *[^\n]+\n)', re.DOTALL),
		#2 : re.compile(ur'(\| *latitude *= *[^\n]+.*\| *longitude *= *[^\n]+.*|\| *longitude *= *[^\n]+.*\| *latitude *= *[^\n]+.*)\| *coordonnées *=[^\n]*\n?', re.DOTALL),
		#3 : u'(\n?) *\| *coordonnées *= *\{ *\{ *[Cc]oord *\| *([0-9\.-]+) *\| *([0-9\.]+) *\| *([0-9\.]+) *\| *([NS]) *\| *([0-9\.-]+) *\| *([0-9\.]+) *\| *([0-9\.]+) *\| *([EW])[^.\}]*\} *\}',
		#4 : u'(\n?) *\| *coordonnées *= *\{ *\{ *[Cc]oord *\| *([0-9\.-]+) *\| *([NS]) *\| *([0-9\.-]+) *\| *([EW])[^.\}]*\} *\}',
		#5 : u'(\n?) *\| *coordonnées *= *\{ *\{ *[Cc]oord *\| *([0-9\.-]+) *\| *([0-9\.-]+)[^.\}]*\} *\}',
		#6 : u'(\n?) *\| *coordonnées *= *[^0-9\n]*'
		#5 : re.compile(ur'\{ *\{ *[Cc]oord[\n]*\} *\}(.*\| *latitude *= *[^\n]+.*\| *longitude *= *[^\n]+.*|.*\| *longitude *= *[^\n]+.*\| *latitude *= *[^\n]+)', re.DOTALL)
		#13 : u'(\n? *\| *(longitude|latitude)) *= *([0-9\.]*) *[Ee](st)?'
		#1 : u"((\n? *\| *)image *=.*) ((\$®\$|\|)[0-9]+px *)",
		#2 : u"(\n? *\| *)image *= *\[ *\[ *([iI]mage|[Ff]ichier|[Ff]ile) *: *([^\|]+) *(((\||\$®\$)[^\|]*)?) *\] *\]"
		1 : u"→"
		}

		## (fr) : Liste de remplacements ##
		## (en) : Replace list ##
		listeRemplacementsElements = {
		1 : u" {{info|→|prêt}}"
		#2 : u"\\1image = \\3\\1légende = \\4"
		#2 : u"\\1\\3"
		#1 : u'\\1 = Hautes-Pyrénées\\3',
		#3 : u'\\1 | latitude = \\2/\\3/\\4/\\5\n | longitude = \\6/\\7/\\8/\\9',
		#4 : u'\\1 | latitude = \\2/\\3\n | longitude = \\4/\\5',
		#5 : u'\\1 | latitude = \\2\n | longitude = \\3',
		#6 : u'\\1 | latitude = \n | longitude = '
		#1 : u'|nom de division = [[Départements d\'Haïti|Département]]\n|division =\\3',
		#2 : u'|nom de division2 = Arrondissement\n|division2 = \\3'
		#7 : u'\\1 = [[\\2',
		#8 : u'\\1 = [[Région \\2|\\2]]',
		#9 : u'\\1 = [[La Réunion|Réunion]]',
		#10 : u'\\1 = ',
		#1 : u'\\1 = \\3/\\4/\\5/E',
		#2 : u'\\1 = \\3/\\4/\\5/W',
		#3 : u'\\1 = \\3/\\4/\\5/N',
		#4 : u'\\1 = \\3/\\4/\\5/S'
		}

		## (fr) : Liste d'ajouts ##
		## (en) : Adds list ##


		##### (fr) : Modifications mineures #####
		##### (en) : Minor changes #####
		listeConditionsPositivesAjouts = {
		#1 : u""
		}

		listeConditionsNegativesAjouts = {
		#1 : u"\| *carte *= *[EÉée]tats-Unis/[fF]loride"
		}

		listeElementsAAjouter = {
		#1 : u"| carte=États-Unis/Floride"
		}

		## (fr) : Liste de recherches ##
		## (en) : Find list ##
		listeRechercheElementsMineure = {
		#1 : u'(\| *image *=.*\n) *\| *([^=]*\n)',
		#2 : u'(\n? *\| *(longueur|largeur) *= *[0-9]*),'
		}

		## (fr) : Liste de remplacements ##
		## (en) : Replace list ##
		listeRemplacementsElementsMineure = {
		#1 : u'\\1 | légende = \\2',
		#2 : u'\\1.'
		}

		#############################################
		#### (fr) : Début du traitement
		#### (en) : Beginning of the treatment
		#############################################
		if not self.debug:
			if not useCategories:
				listePages = [page for page in modeleOld.getReferences(follow_redirects=False, withTemplateInclusion=True,
							  onlyTemplateInclusion=True, redirectsOnly=False)]
			else:
				listePages = []
				for titreCategorie in listeTitresCategories:
					cat = pywikibot.Category(self.site, titreCategorie)
					listePages.extend(list(cat.articles()))
			pywikibot.output(u'Taille de la liste = %i' % len(listePages))
			listePagesARetirer = []

			if self.reprise:
				for page in listePages:
					if page.title() == self.titreReprise:
						break
					listePagesARetirer.append(page)

			if checkNamespace:
				for page in listePages:
					if page.namespace() != checkNumberNamespace and not page in listePagesARetirer:
						listePagesARetirer.append(page)

			for page in listePagesARetirer:
				listePages.remove(page)
		elif self.debug:
			listePages = [pywikibot.Page(self.site, u'User:Toto Azéro/Bac à sable')]

		pywikibot.output(u"Nombre de pages à traiter : %i" % len(listePages))

		for page in listePages:
			if onlySaveIfMajorChange:
				possibiliteSauvegarder = False
			else:
				possibiliteSauvegarder = True
			text = self.load(page)
			pywikibot.output(u"\n> \03{lightblue}Traitement de %s\03{default} <" % page.title())

			############
			### À utiliser uniquement dans les cas exceptionnels :
			### permet d'autoriser la sauvegarde dans un cas précis
			global exception_possibiliteSauvegarder
			exception_possibiliteSauvegarder = False
			#textOld = text

			#text = re.sub(u'(\n? *\| *date-sans *=[^\n]*) *\} *\} *(([\n]+.*)*géoloc-département *= *)', u'\\1\\2}}', text)
			#if text != textOld:
			#	exception_possibiliteSauvegarder = True
			#############

			#################################################################
			############ TRAVAIL SUR L'INFOBOX EXTRAITE DU TEXTE ############
			#################################################################
			##### Délimiter le début de l'infobox
			try:
				matchDebut = re.search(u'\{ *\{ *(%s)' % titreModeleOldRe, text).group(0)
			except:
				pywikibot.output(u"\03{lightred}Absence du modèle %s sur la page %s\03{default}" % (titreModeleOld, page.title()))
				continue
			positionMatchDebut = text.index(matchDebut)
			extraitText = text[positionMatchDebut:]

			#### Délimiter la fin possible de l'infobox
			#### (i.e. les premiers u'}}' trouvés)
			# ‹!› Le résultat n'est pas forcément la fin réelle
			# 	 de l'infobox : en effet, cet ordre ne tient pas
			# 	 compte de probables modèles présents dans l'infobox
			# 	 et s'arrêtera aux premiers u'}}' trouvés, quels
			# 	 qu'ils soient !

			matchFin = re.search(u' *\} *\}', extraitText).group(0)
			positionMatchFin = extraitText.index(matchFin)
			extraitText = extraitText[0:(positionMatchFin + len(matchFin))]
			# NB : dans extraitText[0:(positionMatchFin + len(matchFin))],
			# on ajoute la longueur des u'}}' pour qu'ils se
			# trouvent bien dans l'extrait traité

			# Principe de la boucle : tant que le nombre de u'{'
			# et celui de u'}' ne sont pas équibilibrés, la variable
			# extraitText est agrandie jusqu'au u'}}' suivants trouvés
			# dans le texte.
			positionMatchFin = text.index(extraitText)
			resteText = text[positionMatchFin + len(extraitText):]
			while extraitText.count('{') != extraitText.count('}'):
				matchFin = re.search(u'([^\{\}]* *\} *\}|(\{ *\{[^\{\}]*\} *\})+[^\{\}]* *\} *\})', resteText).group(0)
				positionMatchFin = resteText.index(matchFin)
				extraitTextOld = extraitText
				extraitText = extraitText + resteText[0:(positionMatchFin + len(matchFin))]
				resteText = resteText[positionMatchFin + len(matchFin):]

			### On travaille sur cet extrait puis on effectuera
			### les remplacements sur le texte à la fin
			extraitTextNew = extraitText

			##### Normalisation de l'infobox pour éviter des problèmes dans son traitement #####
			## Enlever les u'|' inutiles et les placer au début du paramètre suivant ##
			# ex : |cp=66360| \n maire=Gérard Rabat
			#	→ |cp=66360\n | maire=Gérard Rabat
			extraitTextNew = pywikibot.replaceExcept(extraitTextNew, re.compile(u'(\|[^\[\]\{\}]*=.*)\|\n'), u'\\1\n |', exceptions)
			extraitTextNew = pywikibot.replaceExcept(extraitTextNew, re.compile(u'\|? *([^\[\]\{\}]*=.*)\| *\n *\|'), u'| \\1\n |', exceptions)

			####
			### Ce qui suit est spécifique
			### à l'infobox {{Infobox Commune de France}}
			## Déplacement d'une image mise à côté du nom de la commune (le blason) dans le paramètre 'armoiries' ##
			# ex : |nomcommune = Saint-Didier-en-Velay [[Image:Blason_Saint-Didier-en-Velay_43.svg|80 px]]
			#	→ |nomcommune = Saint-Didier-en-Velay […] |armoiries = Blason_Saint-Didier-en-Velay_43.svg
			extraitTextNew = pywikibot.replaceExcept(extraitTextNew, re.compile(u'(\| *nomcommune *= *[^\|]*\n?)\[ *\[ *([fF]ichier|[Ii]mage|[Ff]ile) *: *([^\|]*)\|? *([Cc]enter|[Cc]entre|[Ll]eft|[Rr]ight)?[^\]]*\] *\]'), u'\\1|armoiries = \\3', exceptions)

			## On fait passer les u'}}' à la ligne s'ils sont en bout de ligne d'un paramètre ##
			# ex : u'| géoloc-département = | }}'
			#	→ u'| géoloc-département = \n}}' #
			extraitTextNew = pywikibot.replaceExcept(extraitTextNew, re.compile(u'(\n *\|? *.*=.*) *\|+ *\} *\}$'), u'\\1\n}}', exceptions)
			# ex : u'| géoloc-département = }}'
			#	→ u'| géoloc-département = \n}}' #
			extraitTextNew = pywikibot.replaceExcept(extraitTextNew, re.compile(u'(\n *\|? *.*=.*) *\} *\}$'), u'\\1\n}}', exceptions)
			####

			## On fait passer un éventuel u'|' présent en bout de ligne du début de l'infobox ##
			# ex : u'{{Infobox Commune de France|\n\|'
			#	→ u'{{Infobox Commune de France\n|'
			extraitTextNew = pywikibot.replaceExcept(extraitTextNew, re.compile(u'\{ *\{ *(%s[^\n]*) *\| *\n+ *\|' % titreModeleOldRe), u'{{\\1\n | ', exceptions)
			# ex : u'{{Infobox Commune de France|'
			#	→ u'{{Infobox Commune de France\n|'
			extraitTextNew = pywikibot.replaceExcept(extraitTextNew, re.compile(u'\{ *\{ *(%s[^\n]*) *\| *\n' % titreModeleOldRe), u'{{\\1\n | ', exceptions)

			## Suppression de plusieurs u'|' successifs ##
			# ex : {{Infobox Commune de France||nomcommune=Baudrecourt
			#	→ {{Infobox Commune de France|nomcommune=Baudrecourt
			extraitTextNew = pywikibot.replaceExcept(extraitTextNew, re.compile(u'(\{ *\{ *(%s.*)) *(\| *){2,}' % titreModeleOldRe), u'\\1|', exceptions)

			#print u'0-5\n' + extraitTextNew
			## Faire passer les u'|' présents en fin de ligne en début de ligne suivante ##
			extraitTextNew = pywikibot.replaceExcept(extraitTextNew, re.compile(u'(\n?[^\[\]\{\}\n]*=[^=\n]*) *\| *\n'), u'\\1\n | ', exceptions)
			#extraitTextNew = pywikibot.replaceExcept(extraitTextNew, re.compile(u'(\n?[^=]*=[^=]*) *\| *\n'), u'\\1\n | ', exceptions)

			#print u'1\n' + extraitTextNew
			extraitTextNewOld = extraitTextNew

	 ###################################################
	 ###### Modifications pour éviter des erreurs ######
	 ###################################################
	 ## TODO/À faire (ƒ4) : commenter les différents remplacements
			re1 = re.compile(u'(\| *[^\[\]\{\}]*= *\[ *\[ *([fF]ichier|[Ff]ile|[Ii]mage) *:[^=\]]*\|[^=\]]*)=')
			re2 = re.compile(u'(\| *[^\[\]\{\}]*= *[^\[\]\{\}]*\[ *\[[^\[\]\{\}]*)=([^\[\]\{\}]*\] *\])')
			re3 = re.compile(u'(\| *[^\[\]\{\}]*= *[^\[\]\{\}]*\{ *\{[^\[\]\{\}]*)=([^\[\]\{\}]*\} *\})')
			re4 = re.compile(u'(\| *[^\[\]\{\}]*=.*\{ *\{.*)\|(.*\} *\})')
			re5 = re.compile(u'\|([^\[\]\{\}\|\n]*=) *')
			#re5 = re.compile(u'(\| *[^\[\]\{\}]*=.*\{ *\{[^\}\|]*(\n+[^\}]*)+)\|([^\}]*(\n*[^\}]*)+\} *\})')

			while re.search(re1, extraitTextNew):
				extraitTextNew = pywikibot.replaceExcept(extraitTextNew, re1, u'\\1$±$', exceptions)

			while re.search(re2, extraitTextNew):
				extraitTextNew = pywikibot.replaceExcept(extraitTextNew, re2, u'\\1$±$\\2', exceptions)

			while re.search(re3, extraitTextNew):
				extraitTextNew = pywikibot.replaceExcept(extraitTextNew, re3, u'\\1$±$\\2', exceptions)

			while re.search(re4, extraitTextNew):
				extraitTextNew = pywikibot.replaceExcept(extraitTextNew, re4, u'\\1$®$\\2', exceptions)

			while re.search(re5, extraitTextNew):
				extraitTextNew = pywikibot.replaceExcept(extraitTextNew, re5, u'$¡$\\1 ', exceptions)
			extraitTextNew = extraitTextNew.replace(u'|', u'$®$')
			extraitTextNew = extraitTextNew.replace(u'$¡$', u'|')
	 ###################################################

			#print u'2\n' + extraitTextNew
			#pywikibot.showDiff(extraitTextNewOld, extraitTextNew)


			## Séparer tous les paramètres présents sur une même ligne ##
			# ex : u'|nomcommune = Saint-Félix-de-Sorgues|région = [[Midi-Pyrénées]]'
			#	→ u'|nomcommune = Saint-Félix-de-Sorgues
			#		|région = [[Midi-Pyrénées]]'

			verificationStop = re.compile(u'(\| *[^\[\]\{\}]*=[^\n]*)(\| *[^\[\]\{\}]*=[^\n]*)')
			#print extraitTextNew
			while re.search(verificationStop, extraitTextNew):
				extraitTextNew = pywikibot.replaceExcept(extraitTextNew, re.compile(u'(\| *[^\[\]\{\}]*=[^\n]*)(\| *[^\[\]\{\}]*=[^\n]*)'), u'\\1\n\\2', exceptions)

			#print u'3\n' + extraitTextNew
			verificationStop = re.compile(u'(\| *[^\[\{]+=.*\[ *\[(.*\|)+.*\] *\][^\[\n]*)(\| *[^\[\{]+=.*)')
			while re.search(verificationStop, extraitTextNew):
				##PROBLEME ICI (RESOlU ?)
				extraitTextNew = pywikibot.replaceExcept(extraitTextNew, re.compile(u'(\| *[^\[\{]+=.*\[ *\[(.*\|)+.*\] *\][^\[\n]*)(\| *[^\[\{]+=.*)'), u'\\1\n\\2', exceptions)

			#print u'4\n' + extraitTextNew
			#print extraitTextNew
			## Fait passer les parmètre en bout d'annonce du modèle à la ligne
			# ex : {{Infobox Commune de France|nomcommune=Baudrecourt
			#	→ {{Infobox Commune de France
			#	  | nomcommune=Baudrecourt
			extraitTextNew = pywikibot.replaceExcept(extraitTextNew, re.compile(u'\{ *\{ *(%s) *\| *(.*)\n' % titreModeleOldRe), u'{{\\1\n | \\2\n', exceptions)

			#print extraitTextNew
			## Suppression d'un '|' inutile (ex : '| }}')
			# ex : | }}
			#	→ }}
			extraitTextNew = pywikibot.replaceExcept(extraitTextNew, re.compile(u'\n *\|+ *\} *\}'), u'\n}}', exceptions)
			extraitTextNew = pywikibot.replaceExcept(extraitTextNew, re.compile(u'\n *(\|?.*=.*) *\| *\} *\}'), u'\n\\1}}', exceptions)

			#print u'5\n' + extraitTextNew
			extraitTextNewOld = extraitTextNew

			## Modifications majeures ##
			for x in listeRechercheElements:
				elementAChercher = listeRechercheElements[x]
				print 'x = %i' % x
				print elementAChercher
				print re.search(elementAChercher, extraitTextNew)
				print listeRemplacementsElements[x]
				print re.sub(elementAChercher, listeRemplacementsElements[x], extraitTextNew)
				extraitTextNew = pywikibot.replaceExcept(extraitTextNew, elementAChercher, listeRemplacementsElements[x], exceptions)
				#extraitTextNew = re.sub(elementAChercher, listeRemplacementsElements[x], extraitTextNew)
				#print extraitTextNew

			#print extraitTextNew
			## Ajouts majeurs ##
			for x in listeElementsAAjouter:
				elementAAjouter = listeElementsAAjouter[x]
				conditionNegative = listeConditionsNegativesAjouts[x]
				conditionPositive = listeConditionsPositivesAjouts[x]
				#print elementAAjouter

				if not re.search(conditionNegative, extraitTextNew) and re.search(conditionPositive, extraitTextNew):
					positionFin = extraitTextNew.rindex('\n}}')
					#print positionFin
					#print extraitTextNew[0:positionFin]
					extraitTextNew = extraitTextNew[0:positionFin] + u"\n" + elementAAjouter + extraitTextNew[positionFin:]

			#print u'5-5\n' + extraitTextNew
			### Enlever les séparateurs des milliers dans certains paramètres donnés
			listeElements = []
			for element in listeElements:
				m = re.search(u'(%s *= *)([0-9]* [0-9]* *)' % element, extraitTextNew)
				if m != None:
					new = m.group(1) + m.group(2).replace(u' ', u'')
					#print u'1-1 : %s — %s' % (m.group(0), new)
					extraitTextNew = extraitTextNew.replace(m.group(0), new)

			#print extraitTextNew
			## Vérifier si une modification majeure a eu lieu
			if (extraitTextNew != extraitTextNewOld and onlySaveIfMajorChange) or exception_possibiliteSauvegarder:
				possibiliteSauvegarder = True
				#pywikibot.showDiff(extraitTextNewOld, extraitTextNew)
				for x in listeRechercheElementsMineure: # Modifications mineures
					elementAChercher = listeRechercheElementsMineure[x]
					#print 'x = %i' % x
					#print elementAChercher
					extraitTextNew = pywikibot.replaceExcept(extraitTextNew, elementAChercher, listeRemplacementsElementsMineure[x], exceptions)
					#print extraitTextNew
			else:
				continue
			#listeElements = [u'longitude', u'latitude']
			#for element in listeElements:
			#	m = re.search(u'\n? *\| *%s *= *([-—–]?[0-9\.]+)' % element, extraitTextNew)
			#	m2 = re.search(u'\n? *\| *%s *= *[0-9]+\.[0-9]{4,}' % element, extraitTextNew)
			#	if m != None and m2 != None:
			#		extraitTextNew = extraitTextNew.replace(m.group(1), (u'%.4f' % float(m.group(1))))

			extraitTextNew = pywikibot.replaceExcept(extraitTextNew, re.compile(u'\n *\| *'), u'\n | ', exceptions)
			extraitTextNew = pywikibot.replaceExcept(extraitTextNew, re.compile(u'(\| *[a-zé²\- _]{2,17}) *= *'), u'\\1 = ', exceptions)

			extraitTextNew = pywikibot.replaceExcept(extraitTextNew, re.compile(u'(\|.*=.*)\| *$'), u'\\1', exceptions)


	 ### Fin modification pour éviter des erreurs (1/2)
			extraitTextNew = extraitTextNew.replace(u'$±$', u'=')
			##### Ajouts de tous les paramètres absents #####
			listeParametresActuelsAvecValeurs = extraitTextNew.split(u'\n | ')[1:]

			listeParametres = [u'nomcommune', u'image', u'image-desc', u'armoiries',
							  u'armoiries-desc', u'armoiries-taille', u'logo', u'logo-desc', u'logo-taille', #u'collectivité',
							  u'région', u'canton', u'arrondissement', u'insee', u'cp', u'maire', u'mandat', u'intercomm',
							  u'latitude', u'longitude', u'alt mini', u'alt maxi', u'km²', u'sans', u'date-sans',
							  u'aire-urbaine', u'date-aire-urbaine', u'nomhab', u'siteweb', u'géoloc-département']

			if ajoutParametresAbsents:
				for parametre in listeParametres:
					if not parametre in extraitTextNew:
						parametrePrecedent = listeParametres[listeParametres.index(parametre) - 1]
						old = re.compile(u'(\n? *\| *%s *= *.*)' % parametrePrecedent)
						new = u'\\1\n | %s = ' % parametre
						extraitTextNew = pywikibot.replaceExcept(extraitTextNew, old, new, exceptions)

			#print '6\n' + extraitTextNew
			##### Alignement des signes u'=' #####
			listeParametresAvecValeurs = extraitTextNew.split(u'\n | ')[1:]
			tailleMaxParametre = 0
			for parametreAvecValeur in listeParametresAvecValeurs:
				#print parametreAvecValeur
				match = re.search(u' *=', parametreAvecValeur).group(0)
				positionSigneEgal = parametreAvecValeur.index(match)
				partieParametre = parametreAvecValeur[0:positionSigneEgal]
				#print 'partieParametre = %s ; taille = %s' % (partieParametre, len(partieParametre))
				if len(partieParametre) > tailleMaxParametre:
					tailleMaxParametre = len(partieParametre)

			tailleMaxParametre = tailleMaxParametre + 1 # Permet de laisser un espace avant le plus long paramètre…
			#print '\ntailleMaxParametre = %i' % tailleMaxParametre
			if not alignementSignesEgal:
				listeParametresAvecValeurs = []
			#print listeParametresAvecValeurs

			for parametreAvecValeur in listeParametresAvecValeurs:
				#print parametreAvecValeur
				positionSigneEgal = parametreAvecValeur.index(u'=')
				partieParametre = parametreAvecValeur[0:positionSigneEgal]
				partieParametreNew = partieParametre
				while len(partieParametreNew) < tailleMaxParametre:
					partieParametreNew = partieParametreNew + u' '

				while len(partieParametreNew) > tailleMaxParametre:
					partieParametreNew = partieParametreNew[0:-1]

				#print str(len(partieParametreNew)) + partieParametreNew
				#print 'partieParametre = ' + partieParametre
				parametreAvecValeurNew = pywikibot.replaceExcept(parametreAvecValeur, u'^%s' % partieParametre, partieParametreNew, exceptions)
				#parametreAvecValeurNew = parametreAvecValeur.replace(u' | ' + partieParametre, u' | ' + partieParametreNew)
				#print 'partieParametreNew = ' + partieParametreNew
				extraitTextNew = extraitTextNew.replace(u'\n | ' + parametreAvecValeur, u'\n | ' + parametreAvecValeurNew)

	 ### Fin modification pour éviter des erreurs (2/2)
			extraitTextNew = extraitTextNew.replace(u'$®$', u'|')

			#print extraitTextNew
			###### Mettre à jour le texte grâce à l'extrait modifié et le publier ######
			#print extraitTextNew
			text = text.replace(extraitText, extraitTextNew)
			resume = self.summary
			#if re.search(u'longitude *= *[^\n]+.*', text) and re.search(u'latitude *= *[^\n]+.*', text):
			#	resume = u'[[WP:RBOT]] : Suppression du paramètre \'coordonnées\' dans le [[modèle:Infobox Pont]] au profit des paramètres \'latitude\' et \'longitude\''
			#if re.search(u'\{ *\{ *[Cc]oord *\|.*\} *\}', text) and re.search(u'\| *latitude *= *.+', text) and re.search(u'\| *longitude *= *.+', text):
			#	text = pywikibot.replaceExcept(text, re.compile(u'\{ *\{ *[Cc]oord *\|.*\} *\}\n?'), u'', exceptions)
			#	resume = resume + u' ; suppression du modèle {{coord}} faisant doublon avec ces paramètres'
			#print extraitTextNew
			print u"‹!› Modifications ‹!›"
			pywikibot.showDiff(page.get(), text)
			#if checkNamespace and page.namespace() == checkNumberNamespace:
			#print possibiliteSauvegarder
			if possibiliteSauvegarder:
				if not self.save(text, page, resume):
					pywikibot.output(u'La page %s n\'a pas été sauvegardée' % page.title(asLink=True))
			#else:
			#	pywikibot.output(u'\03{lightred}La page %s ne sera pas sauvegardée car elle n\'est pas dans le namespace 0\03{default}' % page.title(asLink=True))

	def load(self, page):
		"""
		Retourne le contenu d'une page donnée.
		En cas d'erreur, retourne None en précisant l'erreur rencontrée.
		"""
		try:
			text = page.get()
		except pywikibot.NoPage:
			pywikibot.output(u"La page %s n'existe pas."
							 % page.title(asLink=True))
		except pywikibot.IsRedirectPage:
			pywikibot.output(u"La page %s est une redirection."
							 % page.title(asLink=True))
		else:
			return text
		return None

	def save(self, text, page, comment, minorEdit=True, botflag=True):
		# Ne sauvegarder que si quelque chose a été modifié.
		if text != page.get():
			arretdurgence()
			pywikibot.output(u"\n\n>>> \03{lightpurple}%s\03{default} <<<"
							 % page.title())

			# Diff montrant ce qui a été modifié
			pywikibot.showDiff(page.get(), text)
			# Commentaire d'édition du bot
			pywikibot.output(u"Commentaire d'édition : %s" %comment)

			# Pour plus d'info sur le paramètre dry, voir explications
			# dans l'en-tête du script
			if not self.dry:
				#choice = 'y'
				choice = pywikibot.inputChoice(u'Do you want to accept these changes?', ['Yes', 'No'], ['y', 'N'], 'N')
				if choice == 'y':
					try:
						if self.async:
							page.put_async(text, comment=comment, minorEdit=minorEdit)
						else:
							page.put(text, comment=comment, minorEdit=minorEdit)#, botflag=botflag)
					except pywikibot.EditConflict:
						pywikibot.output(
							u"Saute la page %s à cause d'un conflit d'édition."
							% (page.title(asLink = True)))
					except pywikibot.LockedPage:
						pywikibot.output(u"La page %s est protégée."
							% page.title(asLink = True))
					except pywikibot.SpamblacklistError, error:
						pywikibot.output(
u'Impossible de publier la page %s à cause du filtre anti-erreur n°%s'
							% (page.title(asLink = True), error.url))
					else:
						return True
		return False

def arretdurgence():
	"""
	Fonction d'arrêt d'urgence : recupère le contenu de la page
	de discussion du bot et arrête le script en demandant une confirmation
	lorsque la page contient autre chose que le modèle {{/Stop}}
	(i.e. lorsqu'un message a été laissé sur la page de discussion)
	"""
	global arret
	arretpage = pywikibot.Page(pywikibot.Site('fr','wikipedia'), u"Discussion utilisateur:ZéroBot")
	arret = arretpage.get()
	if arret != u"{{/Stop}}":
		pywikibot.inputChoice(u"\03{lightred}Demande d'arrêt d'urgence\03{default}",['vu'],['v'],'')

def main():
	dry = False
	reprise = False
	titreReprise = None
	debug = False
	async = False

	for arg in pywikibot.handleArgs():
		if arg.startswith("-dry"):
			dry = True
		elif arg.startswith("-reprise:"):
			reprise = True
			titreReprise = arg[len('-reprise:'):].replace('_', ' ')
			if titreReprise == '':
				pywikibot.output(u'Syntax: basic4_refonte.py [-reprise:|-dry|-debug]')
				exit()
		elif arg.startswith("-debug"):
			debug = True
		elif arg.startswith("-async"):
			async = True
		else:
			pywikibot.output(u'Syntax: basic4_refonte.py [-reprise:|-dry|-debug|-async]')
			exit()

	bot = InfoboxBot(dry, reprise, titreReprise, debug, async)
	bot.debugMode()
	bot.run()

if __name__ == "__main__":
	try:
		main()
	finally:
		pywikibot.stopme()
