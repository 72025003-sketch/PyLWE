import typing
from dataclasses import dataclass
from typing import TypeGuard

from pynmea2 import NMEASentence

PayloadKind = typing.Literal["nmea", "ais", "raw"]

TDecoded = typing.TypeVar("TDecoded")


@dataclass(frozen=True, slots=True)
class AisMeta:
    talker_id: str          # e.g. "AI"
    formatter: str          # e.g. "VDM" / "VDO"
    radio_channel: str      # e.g. "A" / "B" / ""
    seq_id: str | None


@dataclass(frozen=True, slots=True)
class ParsedPacket(typing.Generic[TDecoded]):
    tags: dict[str, str]
    kind: PayloadKind
    raw_sentence: str | bytes
    decoded: TDecoded | None = None
    ais_meta: AisMeta | None = None


def is_nmea(packet: "ParsedPacket[object]") -> TypeGuard["ParsedPacket[NMEASentence]"]:
    return packet.kind == "nmea" and isinstance(packet.decoded, NMEASentence)


def is_ais(packet: "ParsedPacket[object]") -> TypeGuard["ParsedPacket[object]"]:
    return packet.kind == "ais" and packet.decoded is not None


def is_raw_bytes(packet: "ParsedPacket[object]") -> TypeGuard["ParsedPacket[object]"]:
    return packet.kind == "raw" and isinstance(packet.raw_sentence, bytes)