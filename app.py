import collections
import itertools

from flask import Flask, request, json
from flask_cors import CORS
from Graph import Graph

app = Flask(__name__)
cors = CORS(app, resources={r"/*": {"origins": "*"}})


@app.route("/search", methods=['POST'])
def search():
    # Reading request variables
    origin_iata = request.form['origin_iata']
    destination_iata = request.form['destination_iata']
    depart_date = request.form['depart_date']
    trip_class = request.form['trip_class']
    adults = request.form['adults']
    children = request.form['children']
    infants = request.form['infants']
    display_option = request.form['displayOption']

    # Load flight data from json repo
    flight_data = load_flights_data()

    # Load airport data from json repo
    airport_data = load_airport_data()

    graph = Graph(load_graph(load_airport_data(), display_option))
    path_list = graph.dijkstra(origin_iata, destination_iata)
    sliceable_path_list = sliceable_deque(path_list)

    #print(sliceable_path_list)

    route_path = []
    total_distance = 0
    total_duration = 0
    for previous, current in zip(sliceable_path_list, sliceable_path_list[1:]):
        distance = get_distance(airport_data, previous, current)
        duration = get_duration(airport_data, previous, current)
        route = {"origin": previous, "destination": current, "distance": distance}
        total_distance = total_distance + int(distance)
        total_duration = total_duration + float(duration)
        route_path.append(route)
    route_object = {"total_duration": total_duration, "total_distance": total_distance, "route_path": route_path}
    print("**")
    print(route_object)

    # Finding the flights based on search criteria
    flights = find_match(flight_data, origin_iata, destination_iata, depart_date, route_object)

    # print(flights)
    flights.sort(key=lambda x: x['price'], reverse=False)

    # Sorting the results based on display options

    response_object = {
                            'status': 'OK',
                            'payload': {

                                'origin_iata': origin_iata,
                                'destination_iata': destination_iata,
                                'depart_date': depart_date,
                                'trip_class': trip_class,
                                'adults': adults,
                                'children': children,
                                'infants': infants
                            },
                            'flights': flights
                    }

    print(response_object)
    # return response
    return json.dumps(response_object)


class sliceable_deque(collections.deque):
    def __getitem__(self, index):
        if isinstance(index, slice):
            return type(self)(itertools.islice(self, index.start,index.stop, index.step))
        return collections.deque.__getitem__(self, index)


def load_graph(nodes, key):
    edges = []
    for node in nodes:
        edge = (node["origin"], node["destination"], int(node[key]))
        edges.append(edge)
    # print("Edges:")
    # print(edges)
    return edges


def load_json(file_name):
    with open(file_name) as f:
        data = json.load(f)
    return data


def load_flights_data():
    return load_json('flightsData.json')


def load_airport_data():
    return load_json('airportData.json')


def get_distance(parent_json, oc, dc):
    for airport in parent_json:
        if (airport["origin"] == oc) and (airport["destination"] == dc):
            return airport["distance"]
    return 0


def get_duration(parent_json, oc, dc):
    for airport in parent_json:
        if (airport["origin"] == oc) and (airport["destination"] == dc):
            return airport["duration"]
    return 0


def find_match(parent_json, oc, dc, dt, route_object):
    json_data_list = []
    print("fm")
    for leg in route_object["route_path"]:
        for flight in parent_json:
            if (flight["date"] == dt) and (flight["oc"] == leg["origin"]) and (flight["dc"] == leg["destination"]):
                price = float(flight["price"]) * int(leg["distance"])
                route_flight = {"price": int(price), "route_path": route_object, "flight": flight}
                json_data_list.append(route_flight)

    return json_data_list




def find_match_old(parent_json, oc, dc, dt, route_object):
    json_data_list = []
    print("fm")
    for flight in parent_json:
        if (flight["date"] == dt) and (flight["oc"] == oc) and (flight["dc"] == dc):
            price = float(flight["price"]) * int(route_object["total_distance"])
            route_flight = {"price": int(price), "route_path": route_object, "flight": flight}
            json_data_list.append(route_flight)
    # print(json_data_list)
    return json_data_list


if __name__ == "__main__":
    app.run()
