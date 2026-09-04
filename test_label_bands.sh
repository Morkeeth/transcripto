#!/usr/bin/env bash
# Overlapping habits are descriptive only. No causal or significance-based ranking.
cd "$(dirname "$0")"
python3 -m unittest discover -s tests -p test_replay.py -k StatisticsTests
