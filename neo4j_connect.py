from py2neo import Graph
import firebase_admin
from firebase_admin import credentials
from firebase_admin import db

graph = Graph("http://localhost:7474/db/data")
graph.begin()
cred = credentials.Certificate('google-services.json')
firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://orendaa-2-0.firebaseio.com/'
})

def gen_shortest_route(source , destination , graph):
    query_string = "MATCH (start:Loc{name:'#"+source+"'}), (end:Loc{name:'#"+destination+"'}) CALL algo.shortestPath.stream(start, end, 'dist') YIELD nodeId, cost RETURN algo.asNode(nodeId).name AS name, cost"
    result = graph.run(query_string)
    record = []
    short_path = []
    for r in result:
        record += r
    i = 0
    while i < (len(record) - 1):
        short_path.append(record[i][1:])
        i = i + 2
    return short_path

def bus_route(source, destination,graph):
    query = "MATCH ({name : \"" + str(source) + "\"})-[r]->({name : \"" + str(
        destination) + "\"}) RETURN type(r) as type"
    bus = graph.run(query)
    bus_list = []
    record = []
    for b in bus:
        record += b
    for i in range(len(record)):
        bus_list.append(record[i])
    return bus_list

def intersection(li1, li2):
    return (list)(set(li1) & set(li2))

def generate_route(source ,destination):
    short_path = gen_shortest_route(source,destination,graph)
    Route = []
    break_point=[]
    route = []
    for i in range(len(short_path) - 1):
        if i == 0:
            route = (bus_route(short_path[0], short_path[1], graph)) + bus_route(short_path[1], short_path[0], graph)
            print(route)
            break_point.append(short_path[0])
            continue
        r = bus_route(short_path[i], short_path[i + 1], graph) + bus_route(short_path[i + 1], short_path[i], graph)
        if len(intersection(route, r)) == 0:
            Route.append(route)
            route = r[:]
            break_point.append(short_path[i])
        else:
            route = intersection(route, r)
    break_point.append(short_path[-1])
    Route.append(route)
    print(Route)
    print(break_point)
    dict_route={}
    for i in range(len(break_point)-1):
        src = str(i) + ":" + str(break_point[i]) + ":" + str(break_point[i+1])
        s=" "
        for x in Route[i]:
            s = s + str(x)
            s = s + " "
        dict_route.update({src:s})
    print(dict_route)
    return dict_route

def listener(event):
    # print(event.event_type)  # can be 'put' or 'patch'
    key = event.path  # relative to the reference, it seems
    key = key.strip('/')
    data = event.data
    print(data)  # new data at /reference/event.path. None if deleted
    if data is None:
        return
    if(type(data) is dict):
        key = list(data.keys())
        key = key[0]
        data = data[key]
    source, destination = data.strip(' ').split(':')
    source = source.strip(' ')
    destination = destination.strip(' ')
    print(source +" "+ destination)
    res = generate_route(source, destination)
    print(res)
    ref = db.reference('/route_result')
    ref.child(key).update(res)
    db.reference('/route_query').child(key).delete()


firebase_admin.db.reference('/route_query').listen(listener)