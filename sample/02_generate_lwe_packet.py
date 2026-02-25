import pynmea2
import pyais
from pylwe import generate

def main():
    print("--- Example 1: Generating NMEA 0183 LWE Packet ---")
    tags = {
        "s": "GP0001",
        "c": "Nav"
    }
    
    # 1. Provide an NMEA string directly
    nmea_str_payload = "$GPGGA,123519,4807.038,N,01131.000,E,1,08,0.9,545.4,M,46.9,M,,*47"
    packet_from_string = generate(tags, nmea_str_payload)
    print(f"From string: {packet_from_string}")

    # 2. Provide a pynmea2 sentence object
    nmea_obj_payload = pynmea2.parse(nmea_str_payload)
    packet_from_obj = generate(tags, nmea_obj_payload)
    print(f"From pynmea2 object: {packet_from_obj}")


    print("\n--- Example 2: Generating AIS LWE Packet ---")
    ais_tags = {
        "s": "AI0001",
        "c": "Nav"
    }
    
    # 1. Provide an AIS sentence string directly
    ais_str_payload = "!AIVDM,1,1,,A,14eG;o@034o8sd<L9i:a;WG>0000,0*7D"
    packet_ais_str = generate(ais_tags, ais_str_payload)
    print(f"From AIS string: {packet_ais_str}")
    
    # 2. Provide a pyais payload directly (maintaining formatting)
    # The talker_id and radio_channel can be preserved if they are set on the object
    ais_obj_payload = pyais.decode(ais_str_payload)
    
    # Simulate the attributes that `pylwe.parse` attaches to the pyais message
    ais_obj_payload.talker_id = "AIVDM"
    ais_obj_payload.radio_channel = "A"
    
    packet_ais_obj = generate(ais_tags, ais_obj_payload)
    print(f"From pyais object: {packet_ais_obj}")


if __name__ == "__main__":
    main()
