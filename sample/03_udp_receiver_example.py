import socket
import struct
from pylwe import parse, LweParseError

def main(ip="0.0.0.0", port=60001, multicast_group="239.192.0.1"):
    """
    A simple UDP receiver that listens for incoming LWE packets
    and prints the parsed tags and sentences.
    """
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    
    # Allow multiple sockets to use the same port number
    try:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
    except AttributeError:
        # SO_REUSEPORT is not available on all platforms (like Windows)
        pass
        
    sock.bind((ip, port))
    
    # Join the multicast group for IEC 61162-450 (e.g., 239.192.0.1 for MISC)
    if multicast_group:
        mreq = struct.pack("4sl", socket.inet_aton(multicast_group), socket.INADDR_ANY)
        sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
        print(f"Joined multicast group: {multicast_group}")
    
    print(f"Listening for IEC61162-450 LWE packets on UDP {ip}:{port}...")
    
    try:
        while True:
            data, addr = sock.recvfrom(4096)
            
            try:
                # Parse the raw bytes
                tags, sentence = parse(data)
                
                print(f"[{addr[0]}:{addr[1]}] Tags: {tags}")
                
                # Check what type of sentence we received
                if type(sentence).__module__.startswith("pyais"):
                    print(f"  -> AIS Message: MMSI={getattr(sentence, 'mmsi', 'Unknown')}")
                    # You can access properties like sentence.lat, sentence.lon, etc.
                else:
                    print(f"  -> NMEA Sentence: {getattr(sentence, 'talker', '')}{getattr(sentence, 'sentence_type', '')}")
                    # You can access properties like sentence.data
            
            except LweParseError:
                # In a real application, you might just log this or ignore non-LWE traffic on the port
                print(f"[{addr[0]}:{addr[1]}] Received non-LWE or malformed data: {data[:20]}...")
            
    except KeyboardInterrupt:
        print("\nStopping UDP Receiver.")
    finally:
        sock.close()

if __name__ == "__main__":
    main()
