import pytest
import pynmea2

from pylwe import generate, LweTagError

def test_generate_packet_with_tags():
    tags = {"s": "VD01", "c": "1234"}
    sentence_str = "$GPGGA,123519,4807.038,N,01131.000,E,1,08,0.9,545.4,M,46.9,M,,*47"
    sentence = pynmea2.parse(sentence_str)
    
    packet_bytes = generate(sentence, tags=tags)
    
    expected_content = b"UdPbC\x00\\c:1234,s:VD01*2B\\$GPGGA,123519,4807.038,N,01131.000,E,1,08,0.9,545.4,M,46.9,M,,*47\r\n"
    assert packet_bytes == expected_content

def test_generate_packet_without_tags():
    tags = {}
    sentence_str = "$GPGGA,123519,4807.038,N,01131.000,E,1,08,0.9,545.4,M,46.9,M,,*47"
    
    # Test with string this time
    packet_bytes = generate(sentence_str, tags=tags)
    
    expected_content = b"UdPbC\x00$GPGGA,123519,4807.038,N,01131.000,E,1,08,0.9,545.4,M,46.9,M,,*47\r\n"
    assert packet_bytes == expected_content

def test_generate_packet_tag_too_long():
    tags = {"a": "x" * 80}
    sentence_str = "$GPGGA,123519,4807.038,N,01131.000,E,1,08,0.9,545.4,M,46.9,M,,*47"
    
    with pytest.raises(LweTagError, match="Generated tag block length exceeds 82 bytes"):
        generate(sentence_str, tags=tags)

def test_generate_ais_packet():
    import pyais
    from pylwe import generate_ais
    from pylwe import AisMeta
    tags = {"s": "VD01", "c": "1234"}
    # Decode a sentence to get a pyais message object
    original_sentence = "!AIVDM,1,1,,A,14eG;o@034o8sd<L9i:a;WG>0000,0*0C"
    
    # the decoded message should have the talker_id and radio_channel from parser.py
    from pylwe import parse
    full_packet = b"UdPbC\x00\\s:VD01,c:1234*2B\\" + original_sentence.encode('ascii') + b"\r\n"
    packet = parse(full_packet)
    
    # We create a new valid AisMeta with AIVDM for pyais, since the parser splits it.
    meta = AisMeta(talker_id="AIVDM", formatter="", radio_channel="A", seq_id=None)
    
    packet_bytes = generate_ais(packet.decoded, tags=tags, ais_meta=meta)
    
    expected_content = b"UdPbC\x00\\c:1234,s:VD01*2B\\!AIVDM,1,1,,A,14eG;o@034o8sd<L9i:a;WG>0000,0*0C\r\n"
    assert packet_bytes == [expected_content]
