import networkx as nx
import numpy as np
import matplotlib.pyplot as plt
import xml.etree.ElementTree as ET

#Generate the two graphs
connect_G = nx.Graph()
conflict_G = nx.Graph()

#These must be global because of what depends on them
global nodeNames, nodeXCoor, nodeYCoor
nodeNames = []
nodeXCoor = []
nodeYCoor = []

#Read in the text file with nodes and XY coordinates
f = open('data.txt','r')
for line in f:
    lineArray = line.split(' ')
    nodeNames.append(int(lineArray[0]))
    nodeXCoor.append(float(lineArray[1]))
    nodeYCoor.append(float(lineArray[2]))

#A distance function
def euclid_dist(u,v):
    return np.power(np.power((nodeXCoor[u]-nodeXCoor[v]),2) + np.power((nodeYCoor[u]-nodeYCoor[v]),2),0.5)

#The isotropic channel gain function
def channel_gain(x,y,d,n):
    return np.power(euclid_dist(x,y)/d,-n)

#Creating the Connectivity Graph
for nodeIndex in range(len(nodeNames)):
    connect_G.add_node(nodeNames[nodeIndex], idd=nodeNames[nodeIndex], coor=(nodeXCoor[nodeIndex],nodeYCoor[nodeIndex]))

#Reading in the XML file
tree = ET.parse('model.xml')
root = tree.getroot()
for child in root:
    #ADDITIVE
    if str(child.attrib['name']).lower() == 'additive':
        #Gathering initial values from the XML file: eta = channel exponent, d0 = channel denominator, etc.
        #This is the same "block" for all models.
        eta = float(root[0][1].text)
        d0 = float(root[0][2].text)
        SINRthresh = float(root[0][5].text)
        thermal_noise_power = float(root[0][4].text)
        transmit_power = float(root[0][3].text)
        csThresh = float(root[0][6].text)

        #Generate the edges of the Connectivity Graph. After establishing a link between two nodes u and v,
        #we must then consider all other nodes w that connect to v to see if they interfere or don't with
        #a possible connection based on the equations provided. If not, a possible connection exists, and
        #we add an edge to the graph.
        #This is the same block for all models.
        for u in connect_G.nodes():
            SUM = 0.0
            for v in connect_G.nodes():
                if v != u:
                    numerator = transmit_power*channel_gain(u,v,d0,eta)
                    SUM = 0.0
                    for w in connect_G.nodes():
                        if w != v and w != u:
                            SUM = SUM + channel_gain(w,v,d0,eta)
                    denominator = thermal_noise_power + SUM
                    SINR = numerator/denominator
                    if SINR >= SINRthresh:
                        connect_G.add_edge(u,v,dist=euclid_dist(u,v))

        #Begin creating the nodes of the Conflict Graph based on edges of the Connectivity Graph
        #This is the same for all models.
        newIndex = 0
        for edge in connect_G.edges():
            edist = nx.get_edge_attributes(connect_G,'dist')
            conflict_G.add_node(newIndex, reference=(edge[0],edge[1]), radius=euclid_dist(edge[0],edge[1]))
            newIndex += 1

        #In adding edges to the Conflict Graph, we need to consider the source of the current node
        #and its destination, namely the first two "parts" of nodes u and v.
        #After, we then consider all the other possible connections based on the destination.
        #For example, if (1,2) and (1,3) are conflict nodes, then we need to examine
        #all other links involving nodes 2 and 3 to see if they interfere with the link.
        #This is the same block for all models.
        for u in conflict_G.nodes():
            nodesource_u = conflict_G.node[u]['reference'][0]
            nodelink_out_u = conflict_G.node[u]['reference'][1]
            SUM = 0.0
            for v in conflict_G.nodes():
                if v != u:
                    nodesource_v = conflict_G.node[v]['reference'][0]
                    nodelink_out_v = conflict_G.node[v]['reference'][1]
                    if nodesource_u == nodesource_v:
                        SUM = 0.0
                        for w in conflict_G.nodes():
                            if w != v and w != u:
                                nodesource_w = conflict_G.node[w]['reference'][0]
                                nodelink_out_w = conflict_G.node[w]['reference'][1]
                                if nodelink_out_u == nodelink_out_w or nodelink_out_u == nodesource_w:
                                    SUM += transmit_power*channel_gain(nodesource_u,nodesource_w,d0,eta)
                        if SUM + thermal_noise_power >= csThresh:
                            conflict_G.add_edge(u,v,reference=(conflict_G.node[u]['reference'][0],conflict_G.node[u]['reference'][1]))                
        
    #PROTOCOL
    elif str(child.attrib['name']).lower() == 'protocol':
        delta = float(root[0][0].text)
        comm_range = float(root[0][1].text)
        for u in connect_G.nodes():
            for v in connect_G.nodes():
                if v != u:
                    radmomd = euclid_dist(u,v)
                    success = 0
                    for w in connect_G.nodes():
                        if w != v and w != u:
                            radlm = euclid_dist(u,v)
                            if radlm >= (1.0+delta)*radmomd:
                                success += 1
                            if success == len(nodeNames) - 2 and radmomd <= comm_range:
                                connect_G.add_edge(u,v,dist=euclid_dist(u,v))
        newIndex = 0
        for edge in connect_G.edges():
            edist = nx.get_edge_attributes(connect_G,'dist')
            conflict_G.add_node(newIndex, reference=(edge[0],edge[1]), radius=euclid_dist(edge[0],edge[1]))
            newIndex += 1
        for u in conflict_G.nodes():
            nodesource_u = conflict_G.node[u]['reference'][0]
            nodelink_out_u = conflict_G.node[u]['reference'][1]
            for v in conflict_G.nodes():
                if v != u:
                    nodesource_v = conflict_G.node[v]['reference'][0]
                    nodelink_out_v = conflict_G.node[v]['reference'][1]
                    if nodesource_u == nodesource_v:
                        success = 0
                        for w in conflict_G.nodes():
                            if w != v and w != u:
                                nodesource_w = conflict_G.node[w]['reference'][0]
                                nodelink_out_w = conflict_G.node[w]['reference'][1]
                                if nodelink_out_u == nodelink_out_w or nodelink_out_u == nodesource_w:
                                    if transmit_power*channel_gain(nodesource_u,nodesource_w,d0,eta) >= csThresh:
                                        success += 1
                            if success > 0:
                                conflict_G.add_edge(u,v,reference=(conflict_G.node[u]['reference'][0],conflict_G.node[u]['reference'][1]))
                                
#CAPTURE
    elif str(child.attrib['name']).lower() == 'capture':
        eta = float(root[0][1].text)
        d0 = float(root[0][2].text)
        csThresh = float(root[0][5].text)
        rxThresh = float(root[0][6].text)
        cpThresh = float(root[0][7].text)
        thermal_noise_power = float(root[0][4].text)
        transmit_power = float(root[0][3].text)
        for u in connect_G.nodes():
            for v in connect_G.nodes():
                if v != u:
                    numerator = transmit_power*channel_gain(u,v,d0,eta)
                    success = 0
                    for w in connect_G.nodes():
                        if w != v and w != u:
                            denominator = thermal_noise_power*channel_gain(w,v,d0,eta)
                            if numerator/denominator >= cpThresh:
                                success += 1
                    if numerator >= rxThresh and success == len(nodeNames) - 2:
                        connect_G.add_edge(u,v,dist=euclid_dist(u,v))                       
        newIndex = 0
        for edge in connect_G.edges():
            edist = nx.get_edge_attributes(connect_G,'dist')
            conflict_G.add_node(newIndex, reference=(edge[0],edge[1]), radius=euclid_dist(edge[0],edge[1]))
            newIndex += 1
        for u in conflict_G.nodes():
            nodesource_u = conflict_G.node[u]['reference'][0]
            nodelink_out_u = conflict_G.node[u]['reference'][1]
            for v in conflict_G.nodes():
                if v != u:
                    nodesource_v = conflict_G.node[v]['reference'][0]
                    nodelink_out_v = conflict_G.node[v]['reference'][1]
                    if nodesource_u == nodesource_v:
                        success = 0
                        for w in conflict_G.nodes():
                            if w != v and w != u:
                                nodesource_w = conflict_G.node[w]['reference'][0]
                                nodelink_out_w = conflict_G.node[w]['reference'][1]
                                if nodelink_out_u == nodelink_out_w or nodelink_out_u == nodesource_w:
                                    if transmit_power*channel_gain(nodesource_u,nodesource_w,d0,eta) >= csThresh:
                                        success += 1
                            if success > 0:
                                conflict_G.add_edge(u,v,reference=(conflict_G.node[u]['reference'][0],conflict_G.node[u]['reference'][1]))
    #INF RANGE
    else:
        csThresh = float(root[0][1].text)
        eta = float(root[0][2].text)
        d0 = float(root[0][3].text)
        transmit_power = float(root[0][4].text)
        if str(root[0][0].text).lower() == 'a':
            comm_range = float(root[0][5].text)
            interf_range = float(root[0][6].text)
            for u in connect_G.nodes():
                for v in connect_G.nodes():
                    if v != u:
                        momd = euclid_dist(u,v)
                        success = 0
                        for w in connect_G.nodes():
                            if w != v and w != u:
                                lomd = euclid_dist(w,v)
                                if lomd >= interf_range:
                                    success += 1
                        if momd <= comm_range and success == len(nodeNames) - 2:
                            connect_G.add_edge(u,v,dist=euclid_dist(u,v))
        else:
            cpThresh = float(root[0][5].text)
            rxThresh = float(root[0][6].text)
            irThresh = rxThresh/cpThresh
            for u in connect_G.nodes():
                for v in connect_G.nodes():
                    if v != u:
                        rx = transmit_power*channel_gain(u,v,d0,eta)
                        success = 0
                        for w in connect_G.nodes():
                            if w != v and w != u:
                                ir = transmit_power*channel_gain(w,v,d0,eta)
                                if ir <= irThresh:
                                    success += 1
                        if rx >= rxThresh and success == len(nodeNames) - 2:
                            connect_G.add_edge(u,v,dist=euclid_dist(u,v))
        newIndex = 0
        for edge in connect_G.edges():
            edist = nx.get_edge_attributes(connect_G,'d ist')
            conflict_G.add_node(newIndex, reference=(edge[0],edge[1]), radius=euclid_dist(edge[0],edge[1]))
            newIndex += 1
        for u in conflict_G.nodes():
            nodesource_u = conflict_G.node[u]['reference'][0]
            nodelink_out_u = conflict_G.node[u]['reference'][1]
            for v in conflict_G.nodes():
                if v != u:
                    nodesource_v = conflict_G.node[v]['reference'][0]
                    nodelink_out_v = conflict_G.node[v]['reference'][1]
                    if nodesource_u == nodesource_v:
                        success = 0
                        for w in conflict_G.nodes():
                            if w != v and w != u:
                                nodesource_w = conflict_G.node[w]['reference'][0]
                                nodelink_out_w = conflict_G.node[w]['reference'][1]
                                if nodelink_out_u == nodelink_out_w or nodelink_out_u == nodesource_w:
                                    if transmit_power*channel_gain(nodesource_u,nodesource_w,d0,eta) >= csThresh:
                                        success += 1
                            if success > 0:
                                conflict_G.add_edge(u,v,reference=(conflict_G.node[u]['reference'][0],conflict_G.node[u]['reference'][1]))

plt.subplot(221)
nx.draw(connect_G)
#plt.axis([min(nodeXCoor),max(nodeXCoor),min(nodeYCoor),max(nodeYCoor)])
plt.title('Connectivity Graph')
plt.subplot(222)
nx.draw(conflict_G)
#plt.axis([min(nodeXCoor),max(nodeXCoor),min(nodeYCoor),max(nodeYCoor)])
plt.title('Conflict Graph')
plt.savefig('Graphs.png')
plt.show()

print("Connectivity Graph Nodes:\n")
print(connect_G.nodes(data=True))
print("\nConnectivity Graph Edges:\n")
print(connect_G.edges(data=True))
print("\n\nConflict Graph Nodes:\n")
print(conflict_G.nodes(data=True))
print("\nConflict Graph Edges:\n")
print(conflict_G.edges(data=True))
