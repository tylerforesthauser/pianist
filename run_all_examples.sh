#!/bin/bash
echo "🎹 Pianist Framework - Running All Examples"
echo "==========================================="
echo ""

cd examples

echo "1️⃣  Simple Melody Example"
python example_01_simple_melody.py
echo ""

echo "2️⃣  Motif Transformations Example"
python example_02_motif_transformations.py
echo ""

echo "3️⃣  AI Parsing Example"
python example_03_ai_parsing.py
echo ""

echo "4️⃣  Chord Progression Example"
python example_04_chords.py
echo ""

echo "5️⃣  Quick Methods Example"
python example_05_quick_methods.py
echo ""

echo "==========================================="
echo "📊 Generated MIDI Files:"
ls -lh *.mid
echo ""
echo "✅ All examples completed successfully!"
