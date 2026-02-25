import typing

import pynmea2
from pynmea2 import NMEASentence

from .exceptions import LweTagError

def _calculate_checksum(content: str) -> str:
    """Calculates the XOR checksum of a string, returning a 2-character hex string."""
    checksum = 0
    for char in content:
        checksum ^= ord(char)
    return f"{checksum:02X}"

def generate_tag_block(tags: typing.Dict[str, str]) -> str:
    """Generates a tag block string from a dictionary of tags.
    
    Args:
        tags: A dictionary of tags, e.g. {'s': 'VD01', 'c': '12345678'}.
        
    Returns:
        The formatted tag block including checksum and enclosing backslashes.
        e.g., "\\s:VD01,c:12345678*2C\\"
    """
    if not tags:
        return ""
        
    # Build comma-separated key:value pairs
    pairs = []
    for k, v in tags.items():
        pairs.append(f"{k}:{v}")
        
    content = ",".join(pairs)
    
    # Calculate checksum
    checksum_hex = _calculate_checksum(content)
    
    tag_block = f"\\{content}*{checksum_hex}\\"
    
    # The specification says tag block string length should not exceed 80 or 82 chars. (Usually 80)
    # 82 with the slashes.
    if len(tag_block) > 82:
        raise LweTagError(f"Generated tag block exceeds length limit: {len(tag_block)}")
        
    return tag_block

def generate(tags: typing.Dict[str, str], sentence: typing.Union[NMEASentence, typing.Any, str]) -> bytes:
    """Generates an IEC 61162-450 LWE packet.
    
    Args:
        tags: A dictionary of tags to include in the tag block.
        sentence: A pynmea2.NMEASentence object or a raw NMEA string.
        
    Returns:
        The raw packet bytes (ready for UDP transmission).
        
    Raises:
        LweTagError: If the tags block is too long.
    """
    # Token
    packet_str = "UdPbC\0"
    
    # Tags
    packet_str += generate_tag_block(tags)
    
    # Sentence
    if isinstance(sentence, NMEASentence):
        sentence_str = str(sentence)
    elif type(sentence).__module__.startswith("pyais"):
        import pyais
        talker_id = getattr(sentence, "talker_id", "AIVDO")
        radio_channel = getattr(sentence, "radio_channel", "A")
        seq_id = getattr(sentence, "seq_id", None)
        encoded = pyais.encode_msg(
            sentence, 
            talker_id=talker_id, 
            radio_channel=radio_channel, 
            seq_id=seq_id
        )
        sentence_str = "\r\n".join(encoded)
    else:
        sentence_str = str(sentence)
        
    # Ensure standard NMEA line ending
    if not sentence_str.endswith("\r\n"):
        sentence_str += "\r\n"
        
    packet_str += sentence_str
    
    # UDP payload is encoded as ASCII (or utf-8, but ASCII is safe for NMEA)
    return packet_str.encode('ascii')