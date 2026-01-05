#!/bin/bash
echo "🎹 Pianist Framework - Running All Examples"
echo "==========================================="
echo ""

cd examples || { echo "Error: 'examples' directory not found. Exiting."; exit 1; }

echo "1️⃣  Simple Melody Example"
python example_01_simple_melody.py || exit 1
echo ""

echo "2️⃣  Motif Transformations Example"
python example_02_motif_transformations.py || exit 1
echo ""

echo "3️⃣  AI Parsing Example"
python example_03_ai_parsing.py || exit 1
echo ""

echo "4️⃣  Music21 Integration Example"
python example_04_music21_integration.py || exit 1
echo ""

echo "==========================================="
echo "📊 Generated MIDI Files:"
ls -lh *.mid
echo ""
echo "✅ All examples completed successfully!"
