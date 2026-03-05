import json
from pylwe import parse, LweParseError
from pylwe.types import is_nmea, is_ais

def main():
    # Example 1: Parsing an NMEA 0183 Packet
    print("--- Example 1: NMEA 0183 Packet ---")
    nmea_data = b"UdPbC\x00\\s:GP0001,c:Nav*73\\$GPGGA,123519,4807.038,N,01131.000,E,1,08,0.9,545.4,M,46.9,M,,*47\r\n"
    print(f"Original Data: {nmea_data}")
    
    try:
        packet = parse(nmea_data)
        print(f"Tags: {json.dumps(packet.tags, indent=2)}")
        
        if is_nmea(packet):
            sentence = packet.decoded
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
        packet = parse(ais_data)
        print(f"Tags: {json.dumps(packet.tags, indent=2)}")

        if is_ais(packet):
            ais_msg = packet.decoded
            print(f"MMSI: {ais_msg.mmsi}")
            print(f"Speed: {getattr(ais_msg, 'speed', 'N/A')} knots")
            print(f"Course: {getattr(ais_msg, 'course', 'N/A')} degrees")
            print(f"Latitude: {getattr(ais_msg, 'lat', 'N/A')}")
            print(f"Longitude: {getattr(ais_msg, 'lon', 'N/A')}")
            
            if packet.ais_meta:
                 print(f"Original Talker ID: {packet.ais_meta.talker_id}")
                 print(f"Formatter: {packet.ais_meta.formatter}")
                 print(f"Radio Channel: {packet.ais_meta.radio_channel}")
    except LweParseError as e:
        print(f"Failed to parse AIS: {e}")

if __name__ == "__main__":
    main()