import re
import typing

import pyais
import pynmea2
from pynmea2 import NMEASentence

from .exceptions import LweParseError, LweTagError, LweChecksumError

_TAG_BLOCK_RE = re.compile(r'\\([^\\]+)\\')

def verify_checksum(tag_str: str) -> bool:
    """Verifies the checksum of a tag block string.
    
    The tag block string format is typically `s:somedev,c:1234*1A` 
    where `1A` is the HEX checksum of the content before `*`.
    
    Args:
        tag_str: The tag block string without the surrounding backslashes.
    """
    if '*' not in tag_str:
        return True  # No checksum provided, valid by default (or maybe invalid for strict mode)
    
    content, checksum_hex = tag_str.rsplit('*', 1)
    
    calculated_checksum = 0
    for char in content:
        calculated_checksum ^= ord(char)
        
    try:
        expected_checksum = int(checksum_hex, 16)
    except ValueError:
        return False
        
    return calculated_checksum == expected_checksum

def parse_tags(tag_str: str) -> typing.Dict[str, str]:
    """Parses a tag block string into a dictionary.
    
    Args:
        tag_str: The tag block string, e.g. "s:VD01,d:ST0000*2A".
                 Doesn't include the enclosing backslashes.
                 
    Returns:
        A dictionary of tag keys to values.
        
    Raises:
        LweChecksumError: If the checksum is invalid.
    """
    if not verify_checksum(tag_str):
        raise LweChecksumError("Invalid tag block checksum")
        
    if '*' in tag_str:
        content = tag_str.rsplit('*', 1)[0]
    else:
        content = tag_str
        
    tags = {}
    if not content:
        return tags
        
    for param in content.split(','):
        if ':' in param:
            k, v = param.split(':', 1)
            tags[k] = v
            
    return tags

def parse(data: bytes) -> typing.Tuple[typing.Dict[str, str], typing.Union[NMEASentence, typing.Any, str]]:
    """Parses an IEC 61162-450 LWE packet.
    
    Args:
        data: The raw packet bytes (specifically the UDP payload).
        
    Returns:
        A tuple containing:
        - A dictionary of tags parsed from the tag block.
        - The payload, parsed as a pynmea2.NMEASentence object if applicable,
          or the original string if it cannot be parsed by pynmea2.
          
    Raises:
        LweParseError: If the packet is malformed.
        LweTagError: If the tags block is too long or violates specs.
        LweChecksumError: If the tag block checksum is invalid.
    """
    try:
        text = data.decode('ascii', errors='replace')
    except UnicodeDecodeError:
        raise LweParseError("Packet is not valid ASCII")

    if not text.startswith("UdPbC\x00"):
        raise LweParseError("Missing or invalid UdPbC token")
        
    # Remove the token
    content = text[6:]
    
    tags = {}
    
    # Check for tag block
    tag_match = _TAG_BLOCK_RE.match(content)
    if tag_match:
        tag_block_with_slashes = tag_match.group(0)
        tag_str = tag_match.group(1)
        
        # In IEC 61162-450, total length of tag block (including slashes) must not exceed 82 bytes (or 80 based on standard version, usually 80+2). Let's use 82 max length for strictness, but standard IEC 61162-450 typically restricts individual tags block to maximum sizes.
        # we will use limit of 82.
        if len(tag_block_with_slashes) > 82:
             raise LweTagError(f"Tag block length exceeds 80 bytes: {len(tag_block_with_slashes)}")
             
        tags = parse_tags(tag_str)
        content = content[len(tag_block_with_slashes):]
        
    # The rest should be the NMEA sentence optionally followed by \r\n
    sentence_str = content.strip()
    
    if not sentence_str:
        raise LweParseError("Missing NMEA sentence")
        
    try:
        if sentence_str.startswith('!'):
            try:
                from pyais.messages import NMEAMessage
                nmea_info = NMEAMessage(sentence_str.encode("ascii"))
                
                # pyais uses decode() instead of parse()
                sentence = pyais.decode(sentence_str)
                
                # Attach NMEA information onto the object so it can be re-encoded exactly later
                sentence.talker_id = getattr(nmea_info, "talker", "AI") + getattr(nmea_info, "type", "VDO")
                sentence.radio_channel = getattr(nmea_info, "channel", "A")
                sentence.seq_id = getattr(nmea_info, "seq_id", None)
            except Exception:
                sentence = sentence_str
        else:
            sentence = pynmea2.parse(sentence_str)
    except pynmea2.ParseError:
        sentence = sentence_str
        
    return tags, sentence
