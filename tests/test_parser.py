import pytest
import pynmea2

from pylwe import parse, LweParseError, LweTagError, LweChecksumError

def test_parse_valid_packet():
    data = b"UdPbC\x00\\s:VD01,c:1234*2B\\$GPGGA,123519,4807.038,N,01131.000,E,1,08,0.9,545.4,M,46.9,M,,*47\r\n"
    packet = parse(data)
    
    assert packet.tags == {"s": "VD01", "c": "1234"}
    assert packet.kind == "nmea"
    assert isinstance(packet.decoded, pynmea2.NMEASentence)
    assert packet.decoded.sentence_type == "GGA"
    assert packet.decoded.data[0] == "123519"
    
def test_parse_packet_no_tags():
    data = b"UdPbC\x00$GPGGA,123519,4807.038,N,01131.000,E,1,08,0.9,545.4,M,46.9,M,,*47\r\n"
    packet = parse(data)
    
    assert packet.tags == {}
    assert packet.kind == "nmea"
    assert isinstance(packet.decoded, pynmea2.NMEASentence)
    assert packet.decoded.sentence_type == "GGA"

def test_parse_invalid_token():
    data = b"Wrong\x00\\s:VD01,c:1234*2B\\$GPGGA,123519,4807.038,N,01131.000,E,1,08,0.9,545.4,M,46.9,M,,*47\r\n"
    with pytest.raises(LweParseError, match="Missing or invalid UdPbC token"):
        parse(data)

def test_parse_invalid_tag_checksum():
    data = b"UdPbC\x00\\s:VD01,c:1234*99\\$GPGGA,4807.038,N,01131.000,E,1,08,0.9,545.4,M,46.9,M,,*4A\r\n"
    with pytest.raises(LweChecksumError, match="Invalid tag block checksum"):
        parse(data)
        
def test_parse_too_long_tag_block():
    long_tag = "a:" + "x" * 80
    data = f"UdPbC\x00\\{long_tag}*00\\$GPGGA,123519,4807.038,N\r\n".encode("ascii")
    with pytest.raises(LweTagError, match="Tag block length exceeds"):
        parse(data)

def test_parse_ais_packet():
    data = b"UdPbC\x00\\s:VD01,c:1234*2B\\!AIVDM,1,1,,A,14eG;o@034o8sd<L9i:a;WG>0000,0*7D\r\n"
    packet = parse(data)
    
    assert packet.tags == {"s": "VD01", "c": "1234"}
    assert packet.kind == "ais"
    assert hasattr(packet.decoded, "mmsi")
    assert packet.decoded.mmsi == 316001245
    assert packet.ais_meta is not None
    assert packet.ais_meta.talker_id == "AI"
    assert packet.ais_meta.formatter == "VDM"
    assert packet.ais_meta.radio_channel == "A"
