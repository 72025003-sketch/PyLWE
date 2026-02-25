import json
from pylwe import parse, LweParseError

def main():
    # Example 1: Parsing an NMEA 0183 Packet
    print("--- Example 1: NMEA 0183 Packet ---")
    nmea_data = b"UdPbC\x00\\s:GP0001,c:Nav*73\\$GPGGA,123519,4807.038,N,01131.000,E,1,08,0.9,545.4,M,46.9,M,,*47\r\n"
    print(f"Original Data: {nmea_data}")
    
    try:
        tags, sentence = parse(nmea_data)
        print(f"Tags: {json.dumps(tags, indent=2)}")
        
        # `sentence` will be a pynmea2 object
        print(f"Talker ID: {sentence.talker}")
        print(f"Sentence Type: {sentence.sentence_type}")
        print(f"Latitude: {sentence.lat} {sentence.lat_dir}")
        print(f"Longitude: {sentence.lon} {sentence.lon_dir}")
    except LweParseError as e:
        print(f"Failed to parse NMEA: {e}")

    print("\n--- Example 2: AIS Packet ---")
    # Example 2: Parsing an AIS Packet
    ais_data = b"UdPbC\x00\\s:AI0001,c:Nav*6C\\!AIVDM,1,1,,A,14eG;o@034o8sd<L9i:a;WG>0000,0*7D\r\n"
    print(f"Original Data: {ais_data}")
    
    try:
        tags, ais_msg = parse(ais_data)
        print(f"Tags: {json.dumps(tags, indent=2)}")
        
        # `ais_msg` will be a pyais message object
        print(f"MMSI: {ais_msg.mmsi}")
        print(f"Speed: {ais_msg.speed} knots")
        print(f"Course: {ais_msg.course} degrees")
        print(f"Latitude: {ais_msg.lat}")
        print(f"Longitude: {ais_msg.lon}")
        print(f"Original Talker ID: {getattr(ais_msg, 'talker_id', 'Unknown')}")
    except LweParseError as e:
        print(f"Failed to parse AIS: {e}")

if __name__ == "__main__":
    main()
