import re

import pyais
import pyais.exceptions
import pynmea2
from pynmea2 import NMEASentence

from .exceptions import LweParseError, LweTagError, LweChecksumError
from .types import AisMeta, ParsedPacket

# UdPbC\x00 の直後に来るタグブロックを抽出（内部に \ が含まれない前提）
_TAG_BLOCK_RE = re.compile(r"^\\([^\\]+)\\")


def verify_checksum(tag_str: str, strict: bool = False) -> bool:
    if "*" not in tag_str:
        return not strict

    content, checksum_hex = tag_str.rsplit("*", 1)

    calculated_checksum = 0
    for char in content:
        calculated_checksum ^= ord(char)

    try:
        expected_checksum = int(checksum_hex, 16)
    except ValueError:
        return False

    return calculated_checksum == expected_checksum


def parse_tags(tag_str: str, strict: bool = False) -> dict[str, str]:
    if not verify_checksum(tag_str, strict=strict):
        raise LweChecksumError("Invalid tag block checksum or missing checksum in strict mode")

    content = tag_str.rsplit("*", 1)[0] if "*" in tag_str else tag_str

    tags: dict[str, str] = {}
    if not content:
        return tags

    for param in content.split(","):
        if ":" in param:
            k, v = param.split(":", 1)
            tags[k] = v

    return tags


def parse(data: bytes, strict: bool = False) -> ParsedPacket[object]:
    # データ保全: strictでなければASCII decode失敗は raw(bytes) として返す
    try:
        text = data.decode("ascii")
    except UnicodeDecodeError as e:
        if strict:
            raise LweParseError(f"Packet is not valid ASCII: {e}")
        return ParsedPacket(tags={}, kind="raw", raw_sentence=data, decoded=None, ais_meta=None)

    if not text.startswith("UdPbC\x00"):
        raise LweParseError("Missing or invalid UdPbC token")

    content = text[6:]
    tags: dict[str, str] = {}

    # タグブロック
    tag_match = _TAG_BLOCK_RE.match(content)
    if tag_match:
        tag_block_with_slashes = tag_match.group(0)
        tag_str = tag_match.group(1)

        if len(tag_block_with_slashes) > 82:
            raise LweTagError(
                f"Tag block length exceeds 82 bytes (including slashes): {len(tag_block_with_slashes)}"
            )

        tags = parse_tags(tag_str, strict=strict)
        content = content[len(tag_block_with_slashes) :]

    # 改行だけ落とす（stripしすぎない）
    sentence_str = content.rstrip("\r\n")

    if not sentence_str:
        raise LweParseError("Missing NMEA sentence")

    # 1 datagram = 1 sentence（strict時）
    if ("\n" in sentence_str) or ("\r" in sentence_str):
        if strict:
            raise LweParseError("Multiple sentences in a single datagram are not allowed in strict mode.")
        sentence_str = sentence_str.splitlines()[0]

    # AIS
    if sentence_str.startswith(("!AIVDM", "!AIVDO", "!BSVDM", "!BSVDO", "!ABVDM", "!ABVDO")):
        parts = sentence_str.split(",")
        ais_meta = None
        if len(parts) >= 5:
            header = parts[0][1:]  # e.g. "AIVDM"
            talker_id = header[:2]
            formatter = header[2:]
            seq_id = parts[3] if parts[3] else None
            radio_ch = parts[4] if parts[4] else ""
            ais_meta = AisMeta(talker_id=talker_id, formatter=formatter, radio_channel=radio_ch, seq_id=seq_id)

        try:
            decoded = pyais.decode(sentence_str)
            return ParsedPacket(tags=tags, kind="ais", raw_sentence=sentence_str, decoded=decoded, ais_meta=ais_meta)
        except (pyais.exceptions.PyAISException, ValueError) as e:
            if strict:
                raise LweParseError(f"AIS parse failed: {e}")
            return ParsedPacket(tags=tags, kind="raw", raw_sentence=sentence_str, decoded=None, ais_meta=ais_meta)

    # NMEA
    if sentence_str.startswith("$"):
        try:
            decoded = pynmea2.parse(sentence_str)
            return ParsedPacket(tags=tags, kind="nmea", raw_sentence=sentence_str, decoded=decoded, ais_meta=None)
        except pynmea2.ParseError as e:
            if strict:
                raise LweParseError(f"NMEA parse failed: {e}")
            return ParsedPacket(tags=tags, kind="raw", raw_sentence=sentence_str, decoded=None, ais_meta=None)

    # Unknown
    if strict:
        raise LweParseError(f"Unrecognized sentence start character: {sentence_str[:1]}")
    return ParsedPacket(tags=tags, kind="raw", raw_sentence=sentence_str, decoded=None, ais_meta=None)