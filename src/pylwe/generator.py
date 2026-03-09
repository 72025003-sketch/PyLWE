import time
import typing

import pyais
from pynmea2 import NMEASentence

from .exceptions import LweTagError, LweGenerateError
from .types import AisMeta


def _calculate_checksum(content: str) -> str:
    checksum = 0
    for char in content:
        checksum ^= ord(char)
    return f"{checksum:02X}"


def generate_tag_block(
    tags: typing.Optional[typing.Mapping[str, str]] = None,
    strict_tags: bool = False,
) -> str:
    if not tags:
        return ""

    if strict_tags and "s" not in tags:
        raise LweTagError("Mandatory tag 's' (Source ID) is missing in strict mode.")

    content = ",".join(f"{k}:{v}" for k, v in sorted(tags.items()))
    checksum_hex = _calculate_checksum(content)
    tag_block = f"\\{content}*{checksum_hex}\\"

    if len(tag_block) > 82:
        raise LweTagError(f"Generated tag block length exceeds 82 bytes (including slashes): {len(tag_block)}")

    return tag_block


def generate(
    payload: str | NMEASentence,
    tags: typing.Optional[typing.Mapping[str, str]] = None,
    strict: bool = True,
    strict_tags: bool = False,
) -> bytes:
    sentence_str = str(payload).rstrip("\r\n")

    if ("\n" in sentence_str) or ("\r" in sentence_str):
        if strict:
            raise LweGenerateError(
                "Multiple sentences detected. In strict mode, 1 datagram must contain exactly 1 sentence. "
                "For AIS multi-sentence messages, use generate_ais()."
            )

    tag_str = generate_tag_block(tags, strict_tags=strict_tags)
    packet_str = f"UdPbC\x00{tag_str}{sentence_str}\r\n"
    return packet_str.encode("ascii", errors="strict")


def generate_ais(
    payload: typing.Any,
    tags: typing.Optional[typing.Mapping[str, str]] = None,
    ais_meta: AisMeta | None = None,
    strict_tags: bool = False,
) -> list[bytes]:
    tags_dict = dict(tags) if tags else {}

    encode_kwargs: dict[str, typing.Any] = {}
    if ais_meta:
        if ais_meta.talker_id:
            talker_id = ais_meta.talker_id
            if isinstance(talker_id, str) and ais_meta.formatter and len(talker_id) == 2:
                talker_id = f"{talker_id}{ais_meta.formatter}"
            encode_kwargs["talker_id"] = talker_id
        if ais_meta.radio_channel:
            encode_kwargs["radio_channel"] = ais_meta.radio_channel
        if ais_meta.seq_id:
            encode_kwargs["seq_id"] = ais_meta.seq_id

    try:
        encoded_sentences = pyais.encode_msg(payload, **encode_kwargs)
    except Exception as e:
        raise LweGenerateError(f"Failed to encode AIS payload: {e}")

    if isinstance(encoded_sentences, str):
        encoded_sentences = [encoded_sentences]

    total = len(encoded_sentences)
    group_msg_id = str(int(time.time() * 1000))[-4:] if total > 1 else ""

    packets: list[bytes] = []
    for i, sentence in enumerate(encoded_sentences, start=1):
        sentence_str = str(sentence).rstrip("\r\n")
        if not sentence_str:
            continue

        current_tags = dict(tags_dict)
        if total > 1:
            current_tags["g"] = f"{i}-{total}-{group_msg_id}"

        tag_str = generate_tag_block(current_tags, strict_tags=strict_tags)
        packet_str = f"UdPbC\x00{tag_str}{sentence_str}\r\n"
        packets.append(packet_str.encode("ascii", errors="strict"))

    return packets
