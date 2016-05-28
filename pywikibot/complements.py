#!/usr/bin/python
# -*- coding: utf-8  -*-

"""
Some useful complements.

Last changes :
* 0042 : Answer to Life, the Universe and Everything
"""

#
# (C) Toto Azéro, 2012-2013
#
# Distribué sous licence GNU GPLv3
# Distributed under the terms of the GNU GPLv3 license
# http://www.gnu.org/licenses/gpl.html
#
__version__ = '0042'
__date__ = '2013-10-18 21:34:51 (CEST)'
#

# TODO : utiliser la fonction re.split afin de découper le texte en sections
# sans titre puis de récupérer les titres.
# Avantage : peut peut-être permettre d'éviter certains problèmes en cas de
# doublons de titres.

import re

def extract_titles(text, beginning, match_title):
	"""
	Extracts all the titles of a text, starting at 'beginning'
	Setting beginning to '' or None will start at the beginning of the text
	[‹!› Not working] Setting beginning to anything else (but only unicode) will start ignore all the titles
	before the first occurrence of the phrase given.
	
	match_title should be a regular expression (use re.compile).
	
	Returns a list of unicode strings.
	"""
	titles = {
	-1: beginning
	}
	i = 0
	#print text
	if not text:
		return None
	while re.search(match_title, text):
		titles[i] = re.search(match_title, text).group(0)
		
		if titles[i][0] == '\n':
			titles[i] = titles[i][1:]
		
		#print titles[i]
		text = text[text.index(titles[i]) + len(titles[i]):]
		i += 1
	
	del titles[-1]
	
	return titles

def extract_sections(text, titles):
	"""
	Extracts all the sections of a text, based on a list of titles.
	You can use extract_titles() to be given this list.
	
	Returns a dictionnary as following :
		section_number (int): section_value (unicode)	
	NB: section_value includes the section's title.
	"""
	if not titles:
		return None
		
	sections = {}
	
	for setion_number in titles:
		# Si jamais le titre est celui de la dernière section, on procède
		# sans rechercher le titre de la section suivante, puisqu'elle
		# n'existe pas.
		if (setion_number + 1) != len(titles):
			sections[setion_number] = text[text.index(titles[setion_number]):text.index(titles[setion_number + 1])]
			text = text[text.index(sections[setion_number]) + len(sections[setion_number]):]
		else:
			sections[setion_number] = text[text.index(titles[setion_number]):]
	
	return sections
	

def extract_sections_with_titles(text, beginning, match_title):
	"""
	Extracts all the titles and sections of a text, starting at 'beginning'.
	
	match_title should be a regular expression (use re.compile).
	
	Returns a dictionnary as following :
		section_title (unicode): section_value (unicode)	
	NB: section_value includes the section's title.
	"""
	
	titles = extract_titles(text, beginning, match_title)
	if not titles:
		return None
	
	sections = {}
	
	for setion_number in titles:
		# Si jamais le titre est celui de la dernière section, on procède
		# sans rechercher le titre de la section suivante, puisqu'elle
		# n'existe pas.
		current_title = titles[setion_number]
		if (setion_number + 1) != len(titles):
			sections[current_title] = text[text.index(titles[setion_number]):text.index(titles[setion_number + 1])]
			text = text[text.index(sections[current_title]) + len(sections[current_title]):]
		else:
			sections[current_title] = text[text.index(titles[setion_number]):]
		
	
	return sections

def date_creation_page(page):
	"""
	Returns the creation's date of a page.
	
	@ type page : pywikibot.Page
	"""
	date_creation = page.getVersionHistory()[-1][1]
	return date_creation_page