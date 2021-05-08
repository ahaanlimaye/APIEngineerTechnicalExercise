# Imports
import xml.etree.ElementTree as ET
import argparse
import json
from pathlib import Path

# Main Function
def main():
    parser = argparse.ArgumentParser(description="Convert Seat Map XML to JSON")
    parser.add_argument("filepath", type=dir_path, nargs="+", help="Filepath for XML File")

    args = parser.parse_args()
    filepath = args.filepath[0]
    path = Path(filepath)
    res = {}
    if (filepath[-5 : ] == "1.xml"):
        res = seatmap1_to_json(path)
    elif (filepath[-5 : ] == "2.xml"):
        res = seatmap2_to_json(path)
    else:
        raise argparse.ArgumentTypeError(f"readable_dir:{filepath} is not a valid path, must have \"1\" or \"2\" suffix (depending on xml format)")

    new_path = Path(str(path.parent) + "/" + str(path.stem) + "_parsed.json")
    with open(new_path, 'w+') as f:
        json.dump(res, f, indent=4)
    
    print(f"Successfully created JSON of {filepath} in new file: {new_path}")

# XML File Datatype
def dir_path(path):
    if (Path(path) and path[-4 : ] == ".xml"):
        return path
    else:
        raise argparse.ArgumentTypeError(f"readable_dir:{path} is not a valid path, must be an XML file")  


def seatmap1_to_json(xml):

    # Layout of Response JSON
    res = {
        "departureAirport": "",
        "arrivalAirport": "",
        "departureDateTime": "",
        "flightNumber": "",
        "cabins": []
    }

    # Namespaces JSON
    ns = {
        "soapenc": "http://schemas.xmlsoap.org/soap/encoding/",
        "soapenv": "http://schemas.xmlsoap.org/soap/envelope/",
        "xsd": "http://www.w3.org/2001/XMLSchema",
        "xsi": "http://www.w3.org/2001/XMLSchema-instance",
        "ns":"http://www.opentravel.org/OTA/2003/05/common/"
    }
    
    
    tree = ET.parse(xml) # Parses XML File
    
    # Sets Flight Details in Response JSON
    flight = tree.getroot()[0][0][1][0]
    flight_info = flight.find("ns:FlightSegmentInfo", ns)
    res["departureDateTime"] = flight_info.attrib["DepartureDateTime"]
    res["flightNumber"] = flight_info.attrib["FlightNumber"]
    res["departureAirport"] = flight_info.find("ns:DepartureAirport", ns).attrib["LocationCode"]
    res["arrivalAirport"] = flight_info.find("ns:ArrivalAirport", ns).attrib["LocationCode"]

    # Iterates through the cabins of the Flight
    for cabin in flight.find("ns:SeatMapDetails", ns):

        # Layout of Cabin JSON
        cabinJSON = {
            "class": cabin[0].attrib["CabinType"],
            "layout": cabin.attrib["Layout"],
            "numCols": len(cabin.attrib["Layout"].replace(" ", "")),
            "numRows": 0,
            "seats": []
        }

        # Adds Seat Objects to Cabin
        for row in cabin:
            rowList = []
            for seat in row:
                summary = seat.find("ns:Summary", ns)
                service = seat.find("ns:Service", ns)
                fee = service.find("ns:Fee", ns) if service != None else None
                tax = fee.find("ns:Taxes", ns) if fee != None else None
                tags = []
                for feature in seat.findall("ns:Features", ns):
                    if feature.attrib == {}:
                        tags.append(feature.text)

                # Layout of Seat JSON
                seatJSON = {
                    "id": summary.attrib["SeatNumber"] if summary != None else "N/A",
                    "available": summary.attrib["AvailableInd"] if summary != None else "N/A",
                    "tags": tags,
                    "fee": {
                        "price": fee.attrib["Amount"] if fee != None else "N/A",
                        "currencyCode": fee.attrib["CurrencyCode"] if fee != None else "N/A",
                        "tax": tax.attrib["Amount"] if tax != None else "N/A"
                    }
                }

                # Adds Seat Object to Row List
                rowList.append(seatJSON)
            
            # Adds Row to Cabin List
            cabinJSON["seats"].append(rowList)
        
            cabinJSON["numRows"] += 1 #Increments numRows of Cabin

        # Adds Cabin JSON to Cabin List
        res["cabins"].append(cabinJSON)

    return res # Returns Response JSON

def seatmap2_to_json(xml):

    # Layout of Response JSON
    res = {
        "departureAirport": "",
        "arrivalAirport": "",
        "departureDateTime": "",
        "flightNumber": "",
        "cabins": []
    }

    # Namespaces JSON
    ns = {
        "ns": "http://www.iata.org/IATA/EDIST/2017.2", 
        "ns2": "http://www.iata.org/IATA/EDIST/2017.2/CR129"
    }


    tree = ET.parse(xml) # Parses XML File

    # Sets Flight Details in Response JSON
    flight = tree.getroot()
    data_lists = flight.find("ns:DataLists", ns)
    flight_info = data_lists.find("ns:FlightSegmentList", ns).find("ns:FlightSegment", ns)
    departure = flight_info.find("ns:Departure", ns)
    arrival = flight_info.find("ns:Arrival", ns)
    marketing_carrier = flight_info.find("ns:MarketingCarrier", ns)
    res["departureAirport"] = departure.find("ns:AirportCode", ns).text
    res["arrivalAirport"] = arrival.find("ns:AirportCode", ns).text
    res["departureDateTime"] = departure.find("ns:Date", ns).text + "T" + departure.find("ns:Time", ns).text
    res["flightNumber"] = marketing_carrier.find("ns:FlightNumber", ns).text

    # Defines Seat Definitions
    seat_definitions = {}
    for seat_def in data_lists.find("ns:SeatDefinitionList", ns):
        seat_definitions[seat_def.attrib["SeatDefinitionID"]] = seat_def.find("ns:Description/ns:Text", ns).text.replace("_", " ").title()

    # Defines Offers
    seat_offers = {}
    for offers in flight.findall("ns:ALaCarteOffer", ns):
        for offer in offers:
            offer_id = offer.attrib["OfferItemID"]
            simple_currency_price = offer.find("ns:UnitPriceDetail/ns:TotalAmount/ns:SimpleCurrencyPrice", ns)
            currency_code = simple_currency_price.attrib["Code"]
            price = simple_currency_price.text
            offerJSON = {
                "currencyCode": currency_code,
                "price": price,
            }
            seat_offers[offer_id] = offerJSON

    # Iterates through the cabins of the Flight
    for seatmap in flight.findall("ns:SeatMap", ns):
        
        #Layout of CabinJSON
        cabinJSON = {
            "class": "",
            "layout": "",
            "numCols": "0",
            "numRows": "0",
            "seats": []
        }

        # Defines Cabin
        cabin = seatmap[1]

        # Sets numRows and numCols of Cabin
        cabin_layout = cabin.find("ns:CabinLayout", ns)
        layout = ""
        for col in cabin_layout.findall("ns:Columns", ns):
            layout += col.attrib["Position"]
            prev_index = len(layout)-2
            if col.text == "AISLE" and prev_index >= 0 and layout[prev_index] != " ":
                layout += " "
            cabinJSON["numCols"] = str(int(cabinJSON["numCols"]) + 1)
        cabinJSON["layout"] = layout
        rows = cabin_layout.find("ns:Rows", ns)
        cabinJSON["numRows"] = str(int(rows.find("ns:Last", ns).text) - int(rows.find("ns:First", ns).text) + 1)

        # Adds Seat Objects to Cabin
        for row in cabin.findall("ns:Row", ns):
            rowList = []
            row_num = row.find("ns:Number", ns).text
            for seat in row.findall("ns:Seat", ns):
                col_num = seat.find("ns:Column", ns).text
                tags = []
                available = False
                for seat_ref in seat.findall("ns:SeatDefinitionRef", ns):
                    if (seat_ref == "SD4"):
                        available = True
                    else:
                        tags.append(seat_definitions[seat_ref.text])
                offer = seat.find("ns:OfferItemRefs", ns)
                offer_id = offer.text if offer != None else None

                # Layout of Seat JSON
                seatJSON = {
                    "id": row_num + col_num,
                    "available": "true" if available else "false",
                    "tags": tags,
                    "fee": seat_offers[offer_id] if offer != None else {"currencyCode": "N/A", "price": "N/A"}
                }

                # Adds Seat Object to Row List
                rowList.append(seatJSON)
            
            # Adds Row to Cabin List
            cabinJSON["seats"].append(rowList)

        # Adds Cabin JSON to Cabin List
        res["cabins"].append(cabinJSON)

    return res # Returns Resopnse JSON

# Runs Main Funciton
if __name__ == "__main__":
    main()