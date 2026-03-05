import socket
import struct
from pylwe import parse, LweParseError
from pylwe.types import is_nmea, is_ais, is_raw_bytes  # TypeGuardをインポート

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
                # strict=False (デフォルト) でパース。壊れたデータもアプリを落とさず raw で返す。
                packet = parse(data)
                
                print(f"[{addr[0]}:{addr[1]}] Tags: {packet.tags}")
                
                # 新設計の TypeGuard を使ったスマートな分岐
                if is_ais(packet):
                    # ここに入った時点で packet.decoded は None ではないと保証される
                    # pyaisオブジェクトの属性に直接安全にアクセス可能
                    mmsi = getattr(packet.decoded, 'mmsi', 'Unknown')
                    print(f"  -> AIS Message: Formatter={packet.ais_meta.formatter}, MMSI={mmsi}")
                    
                elif is_nmea(packet):
                    # ここに入った時点で packet.decoded は完全に NMEASentence 型として認識される
                    # getattr は不要！
                    sentence = packet.decoded
                    print(f"  -> NMEA Sentence: {sentence.talker}{sentence.sentence_type}")
                    
                elif is_raw_bytes(packet):
                    # ASCIIデコードすらできなかった完全なバイナリ破損データ
                    print(f"  -> Unparseable Binary Data: {packet.raw_sentence.hex()[:20]}...")
                    
                else:
                    # ASCII文字列ではあるが、LWEの文法エラーや未知のフォーマット
                    print(f"  -> Raw/Unknown payload: {packet.raw_sentence[:30]}")
            
            except LweParseError as e:
                # 致命的なエラー（UdPbCトークン欠落など）の場合のみここに来る
                print(f"[{addr[0]}:{addr[1]}] Ignored non-LWE traffic: {e}")
            
    except KeyboardInterrupt:
        print("\nStopping UDP Receiver.")
    finally:
        sock.close()

if __name__ == "__main__":
    main()