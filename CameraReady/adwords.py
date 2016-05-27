
################################################################################################
# PLEASE README!
################################################################################################

# The Code for project 07.Topic-7.Project-7.AdWordsPlacement.BipartiteGraphMatching 2
# CSC 591: Algorithms for Data Guided Business Intelligence.
# Student name : Himangshu Ranjan Borah
# Unity Id: hborah
# Student Id: 200105222
# The code assumes that the bidder_dataset.csv and the queries.txt resides in the same
# directory where the code is placed and run from.
# It takes around 4 seconds to calculate one pass of all the queries and get the revenue values. 
# Around 400 seconds to calcluate the average over 100 cycles and get the competitive ratio estimate.


################################################################################################
################################################################################################

import sys
import collections
import random
import time
import numpy as np
import pandas as pd
import igraph as gp
random.seed(0)

# Input parsing
if len(sys.argv) != 2:
	print "The input format is not proper ! Please enter in the following format."
	print "python adwords.py <greedy | balance | msvv>"    
	exit(1)
suggested_algorithm = sys.argv[1]


def main():	
	if suggested_algorithm == "greedy":
		#print "GREEDY"
		greedy_matching()
	elif suggested_algorithm == "balance":
		#print "BALANCE"
		balance_matching()
	elif suggested_algorithm == "msvv":
		#print "MSVV"
		msvv_matching()
	else:
		print "The input format is not proper ! Please enter in the following format."
		print "python adwords.py <greedy | balance | msvv>"

# Code to load the test queries.
def load_queries():
	queries =[]
	fp = open("queries.txt","r")
	for line in fp:
		queries.append(line.strip('\n'))
	fp.close()
	return queries


# Code to build the Graph from the Data in the CSV file.
def load_data_to_graph():
	my_df = pd.read_csv("bidder_dataset.csv")

	# Find the unique advertisers and the Keywords
	advertisers = pd.unique(my_df.Advertiser.ravel())
	keywords = pd.unique(my_df.Keyword.ravel()) 

	# Create A graph for the adverrisers and keywords
	adwords_graph = gp.Graph(len(advertisers) + len(keywords))
	vertex_names = list(map(str, list(advertisers))) + list(keywords)
	adwords_graph.vs['name'] = vertex_names

	# Drop the NaN values of the my_df's Budget column
	budget_slice = my_df.dropna(axis = 0, subset=["Budget"])

	# Walk through the budget slice and update the budget attributes of the advertisers
	for i, row_index in budget_slice.iterrows():
		curr_advtertiser = row_index.Advertiser
		curr_budget = row_index.Budget
		adwords_graph.vs.find(str(curr_advtertiser))['budget'] = curr_budget
	
	# Walk through the original DataFrame and add the corresponding edges with the bidding values
	# as the cell entries.
	for i, item in my_df.iterrows():
		# Add edge
		adwords_graph.add_edge(item.Keyword, item.Advertiser, weight = item['Bid Value'])

	OPT_estimate = my_df.Budget.sum(axis = 0)	

	return adwords_graph, OPT_estimate



################################################################################################
# GREEDY!
################################################################################################	


def get_greedy_revenue(query_list, adwords_graph):
	rev_count = 0
	for item in query_list:
		# Get the column of the query
		
		candidates = []
		
		curr_source = adwords_graph.vs.find(item)

		curr_neighbors = adwords_graph.vs.find(item).neighbors()
		for neigh in curr_neighbors:
			neigh_weight = adwords_graph.es.find(_between=((curr_source.index,), (neigh.index,)))['weight']
			if neigh['budget'] >= neigh_weight:
				candidates.append((int(neigh['name']), neigh_weight))

		# Now we have cancdidates ready for selecting.
		if(len(candidates) == 0):
			continue
		
		winner = max(candidates, key = lambda x: x[1])
		# tie breaker, automatically happening
		
		# add to revenue
		rev_count = rev_count + winner[1]
		winner_vertex = adwords_graph.vs.find(str(winner[0]))
		# Budget reduction
		winner_vertex['budget'] = winner_vertex['budget'] - winner[1]
	return rev_count	



def greedy_matching():
	query_list = load_queries()
	[adwords_graph, OPT_estimate] = load_data_to_graph()
	

	# Calculate revenue on the original sequence.
	curr_adwords_graph = adwords_graph.copy()

	revenue_org = get_greedy_revenue(query_list, curr_adwords_graph)
	print "Revenue = " + str(revenue_org) # Necessary print statement.
	
	# iterate 100 times with random suffling of the queries to find the mean revenue.
	revenue_count = 0
	temp_query_list = query_list
	for i in range(0,100):
		random.shuffle(temp_query_list)
		curr_adwords_graph = adwords_graph.copy()
		revenue_count = revenue_count + get_greedy_revenue(temp_query_list, curr_adwords_graph)

	ALG_estimate = revenue_count / 100 # Check for floating point errors
	compet_ratio = ALG_estimate / OPT_estimate

	print "Competitive Ratio = " + str(compet_ratio) # Necessary print



################################################################################################
# MSVV!
################################################################################################



def chi_x(x_u):
	return 1 - np.exp(x_u - 1)


def get_msvv_revenue(query_list, adwords_graph):
	rev_count = 0
	# add attribute to all the vertices named 'used_budget'
	adwords_graph.vs['used_budget'] = 0.0

	
	for item in query_list:
		# Get the column of the query
		candidates = []
		curr_source = adwords_graph.vs.find(item)

		curr_neighbors = adwords_graph.vs.find(item).neighbors()
		for neigh in curr_neighbors:
			neigh_weight = adwords_graph.es.find(_between=((curr_source.index,), (neigh.index,)))['weight']
			if neigh['budget'] >= neigh_weight:
				x_u = neigh['used_budget'] / neigh['budget']
				candidates.append((int(neigh['name']), neigh_weight * chi_x(x_u), neigh_weight))

		
		# Now we have cancdidates ready for selecting.
		if(len(candidates) == 0):
			continue
		
		winner = max(candidates, key = lambda x: x[1])
		# tie breaker, automatically happening.
		
		# add to revenue
		rev_count = rev_count + winner[2]
		winner_vertex = adwords_graph.vs.find(str(winner[0]))
		# Budget reduction
		winner_vertex['used_budget'] = winner_vertex['used_budget'] + winner[2]
	return rev_count	



def msvv_matching():
	query_list = load_queries()
	[adwords_graph, OPT_estimate] = load_data_to_graph()
	

	# Calculate revenue on the original sequence.
	curr_adwords_graph = adwords_graph.copy()


	revenue_org = get_msvv_revenue(query_list, curr_adwords_graph)
	print "Revenue = " + str(revenue_org) # Necessary print statement.
	

	# iterate 100 times with random suffling of the queries to find the mean revenue.
	revenue_count = 0
	temp_query_list = query_list
	for i in range(0,100):
		random.shuffle(temp_query_list)
		curr_adwords_graph = adwords_graph.copy()
		revenue_count = revenue_count + get_msvv_revenue(temp_query_list, curr_adwords_graph)

	ALG_estimate = revenue_count / 100 # Check for floating point errors
	compet_ratio = ALG_estimate / OPT_estimate

	print "Competitive Ratio = " + str(compet_ratio) # Necessary print



################################################################################################
# BALANCE!
################################################################################################



def get_balance_revenue(query_list, adwords_graph):
	rev_count = 0	
	for item in query_list:
		# Get the column of the query
		candidates = []
		curr_source = adwords_graph.vs.find(item)

		curr_neighbors = adwords_graph.vs.find(item).neighbors()
		for neigh in curr_neighbors:
			neigh_weight = adwords_graph.es.find(_between=((curr_source.index,), (neigh.index,)))['weight']
			if neigh['budget'] >= neigh_weight:
				candidates.append((int(neigh['name']), neigh['budget'], neigh_weight))

		
		# Now we have cancdidates ready for selecting.
		if(len(candidates) == 0):
			continue
		
		winner = max(candidates, key = lambda x: x[1])
		# tie breaker, automatically happening.
		
		# add to revenue
		rev_count = rev_count + winner[2]
		winner_vertex = adwords_graph.vs.find(str(winner[0]))
		# Budget reduction
		winner_vertex['budget'] = winner_vertex['budget'] - winner[2]
	return rev_count	



def balance_matching():
	query_list = load_queries()
	[adwords_graph, OPT_estimate] = load_data_to_graph()
	

	# Calculate revenue on the original sequence.
	curr_adwords_graph = adwords_graph.copy()

	revenue_org = get_balance_revenue(query_list, curr_adwords_graph)
	print "Revenue = " + str(revenue_org) # Necessary print statement.
	
	# iterate 100 times with random suffling of the queries to find the mean revenue.
	revenue_count = 0
	temp_query_list = query_list
	for i in range(0,100):
		random.shuffle(temp_query_list)
		curr_adwords_graph = adwords_graph.copy()
		revenue_count = revenue_count + get_balance_revenue(temp_query_list, curr_adwords_graph)

	ALG_estimate = revenue_count / 100 # Check for floating point errors
	compet_ratio = ALG_estimate / OPT_estimate

	print "Competitive Ratio = " + str(compet_ratio) # Necessary print





# Call the main. Entry point.

if __name__ == "__main__":
	main()