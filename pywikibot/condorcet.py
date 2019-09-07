#!/usr/bin/python
# -*- coding: utf-8  -*-
import re

#text = u""""""
	
def winners(list_candidates, ballots, return_matrix = False):
	text = ballots
	matrix = {}
	win_matrix = {}
	dict_victories = {}
	nb_of_candidates = len(list_candidates)
	print nb_of_candidates
	print list_candidates
	
	#list_candidates = ['A', 'B', 'C', 'D', 'E', 'F']
	#if 'E' in text:
	#	nb_of_candidates = 5
	#else:
	#	nb_of_candidates = 4
	#list_candidates = list_candidates[0:nb_of_candidates]
	
	for i in range(nb_of_candidates):
		matrix[list_candidates[i]] = {}
		win_matrix[list_candidates[i]] = {}
		dict_victories[list_candidates[i]] = 0
		for j in range(nb_of_candidates):
			matrix[list_candidates[i]][list_candidates[j]] = 0
			win_matrix[list_candidates[i]][list_candidates[j]] = 0
			
	li = list()
	li.extend(text.split(u'\n'))
	while '' in li:
		li.remove('')
	
	for ballot in li:
		ballot = re.sub(u" *", "", ballot)
		ballot_elements = ballot.split('>')
		# On obtient une liste des candidats classée par ordre de préférence
		#   ex : A>C>B -> ['A', 'C', 'B']
		# NB : en cas de mise à égalité pour plusieurs candidats, on aura :
		#   A>C=B -> ['A', 'C=B']
		
		print u'ballot_elements = %s' % ballot_elements
		list_candidates_remaining = list()
		list_candidates_remaining.extend(list_candidates)
		#print 'list_candidates_remaining ='
		#print list_candidates_remaining
		# list_candidates_remaining correspond aux candidats qui n'ont pas été
		# analysé pour chaque ballot.
		#   ex : ['A', 'C', 'B'] 
		#	-> première boucle : list_candidates_remaining = ['C', 'B']
		#   -> deuxième boucle : list_candidates_remaining = ['B']
		
		for item in ballot_elements:
			if not '=' in item: # Cas 1 : pas de mise à égalité entre candidats
				print u'Case 1 : no "=" in item'
				list_candidates_remaining.remove(item)
				
				# Mise à jour de la matrice des préférences.
				for candidate_less_preferred in list_candidates_remaining:
					matrix[item][candidate_less_preferred] +=1
			else: # Cas 2 : mise(s) à égalité entre plusieurs candidats
				print u'Case 2 : one or more "=" in item'
				list_items = item.split('=')
				
				# On supprime donc chaque candidat mis à égalité de la
				# liste list_candidates_remaining.
				for item in list_items:
					print item
					list_candidates_remaining.remove(item)
					
				# Puis, pour chaque candidat, on met à jour la matrice des
				# préférences.
				for item in list_items:
					for candidate_less_preferred in list_candidates_remaining:
						matrix[item][candidate_less_preferred] +=1
	
	print matrix
	# NB : les variables win_matrix et dict_victories ont été définies avant.
	#print win_matrix
	#print dict_victories
	winners = []
	maxVictories = 0
	
	for candidate1 in list_candidates:
		for candidate2 in list_candidates:
			if matrix[candidate1][candidate2] > matrix[candidate2][candidate1]:
				win_matrix[candidate1][candidate2] += 1
				dict_victories[candidate1] += 1
		if dict_victories[candidate1] > maxVictories:
			winners = [candidate1]
			maxVictories = dict_victories[candidate1]
		elif dict_victories[candidate1] == maxVictories:
			winners.append(candidate1)
			maxVictories = dict_victories[candidate1]
	
	#print win_matrix
	#print dict_victories
	#print winners
	if return_matrix:
		return {'winners':winners, 'matrix':matrix}
	else:
		return winners