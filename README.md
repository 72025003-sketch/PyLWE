# PyLWE

A Python library for parsing and generating IEC 61162-450 (Lightweight Ethernet) packets.
It delegates NMEA 0183 parsing to `pynmea2` and AIS parsing to `pyais`.

> **Note:** This library is not intended to be published on PyPI.

## Installation

You can install this library directly from the Git repository:

```bash
pip install git+https://github.com/72025003-sketch/PyLWE.git
```

## Usage & Examples

Please check the `sample/` directory for example scripts on how to use `PyLWE`:
- **Parsing**: `sample/01_parse_nmea_and_ais.py`
- **Generating**: `sample/02_generate_lwe_packet.py`
- **UDP Receiver**: `sample/03_udp_receiver_example.py`