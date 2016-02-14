import networkx as nx
from networkx.readwrite import json_graph
from helper_functions import open_db, commit_db
import json

def fill_rep_dict(c):
    rep_dict = {}
    get_rep_codes(c, rep_dict)
    get_rep_bills(c, rep_dict)
    get_rep_weight(rep_dict)
    return rep_dict    

def get_rep_codes(c, rep_dict):
    r = c.execute('SELECT id, first, last, party FROM SENATORS')
    senators = r.fetchall()
    for rep in senators:
        s_id = rep[0]
        first = rep[1]
        last = rep[2]
        party = rep[3]
        name = first + '\n' + last
        rep_dict[s_id] = {}
        rep_dict[s_id]['bills'] = []
        rep_dict[s_id]['name'] = name
        rep_dict[s_id]['party'] = party

def get_rep_bills(c, rep_dict):
    for s_id in rep_dict:
        r = c.execute('SELECT bill_id FROM bills WHERE sponsor_id = ' + str(s_id))
        bills = r.fetchall()
        for bill in bills:
            bill_id = bill[0]
            rep_dict[s_id]['bills'].append(bill_id)

def get_rep_weight(rep_dict):
    for s_id in rep_dict:
        rep_dict[s_id]['relationships'] = {}
        total = 0 
        for bill_id in rep_dict[s_id]['bills']:
            r = c.execute('SELECT cosponsor FROM cosponsorships WHERE bill = ' + str(bill_id))
            cosponsors = r.fetchall()
            for rep in cosponsors:
                rep_id = rep[0]
                if rep_id not in rep_dict[s_id]['relationships']:
                    rep_dict[s_id]['relationships'][rep_id] = 0
                rep_dict[s_id]['relationships'][rep_id] += 1
                total += 1
        rep_dict[s_id]['total_cosponsors'] = total

def graph_nodes(rep_dict):
    graph = nx.Graph()
    
    gop = []
    dems = []
    ind = []

    for rep in rep_dict:
        name = rep_dict[rep]['name']
        cosponsors = rep_dict[rep]['total_cosponsors']
        if rep_dict[rep]['party'] == 'Republican':
            gop.append(rep)
            graph.add_nodes_from([rep], party = 'r', label = name, size = cosponsors)
        elif rep_dict[rep]['party'] == 'Democrat':
            dems.append(rep)
            graph.add_nodes_from([rep], party = 'd', label = name, size = cosponsors)    
        else: 
            ind.append(rep)
            graph.add_nodes_from([rep], party = 'o', label = name, size = cosponsors)        
    pos = nx.random_layout(graph)
    
    return graph,pos
def draw_graph_nodes(graph, pos, gop, dems, ind):
    nx.draw_networkx_nodes(graph, pos, nodelist = gop, node_color = 'r')  
    nx.draw_networkx_nodes(graph, pos, nodelist = dems, node_color = 'b')
    nx.draw_networkx_nodes(graph, pos, nodelist = ind, node_color = 'b')

def graph_edges(rep_dict, graph, pos):
    checked_list = []
    for rep in graph.nodes():
        for cosponsor in rep_dict[rep]['relationships']:
                if (rep, cosponsor) not in checked_list and (cosponsor, rep) not in checked_list:
                    num_sponsorships = rep_dict[rep]['relationships'][cosponsor]
                    if rep in rep_dict[cosponsor]['relationships']:
                        num_sponsorships += rep_dict[cosponsor]['relationships'][rep]
                    checked_list.append((rep, cosponsor))
                    if num_sponsorships >= 1:
                        graph.add_edge(cosponsor, rep, weight = num_sponsorships)

def write_html(graph):
    d = json_graph.node_link_data(graph)
    json.dump(d, open('mysite/gov_data/static/gov_data/force.json','w'))

if __name__ == '__main__':
    c, db = open_db('GovData')
    rep_dict = fill_rep_dict(c)
    graph,pos = graph_nodes(rep_dict)
    graph_edges(rep_dict, graph, pos)
    nx.write_gexf(graph, 'sponsors_graph.gexf')
   
    write_html(graph)

    commit_db(db)