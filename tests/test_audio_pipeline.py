#!/usr/bin/env python3
"""
test_audio_pipeline.py - Unit Test Suite for Justin's Parametric NAM Audio Pipeline
Justin Muir - 48kHz 24-bit Audio DSP Lab
"""

import os
import sys
import json
import csv
import tempfile
import unittest

# Ensure scripts and firmware are in python path
repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(repo_root, "scripts"))
sys.path.insert(0, os.path.join(repo_root, "firmware"))

from generate_run_sheet import generate_matrix, write_csv, write_data_json, snap_val
from rp2040_pico_pots import EMAPotFilter

class TestParametricNAMPipeline(unittest.TestCase):

    def test_snap_val(self):
        """Verify knob snapping to nearest 0.5 step."""
        self.assertEqual(snap_val(5.23, step=0.5), 5.0)
        self.assertEqual(snap_val(5.35, step=0.5), 5.5)
        self.assertEqual(snap_val(7.76, step=0.5), 8.0)
        self.assertEqual(snap_val(1.0, step=0.5), 1.0)

    def test_matrix_generation_length_and_structure(self):
        """Verify that 40 training takes yields exactly 45 total takes (1 anchor + 40 LHS + 4 edge)."""
        takes = generate_matrix(num_train=40, seed=42, step=0.5)
        self.assertEqual(len(takes), 45)

        # Check take 00 (Anchor take)
        anchor = takes[0]
        self.assertEqual(anchor['take_id'], 'take_00')
        self.assertEqual(anchor['type'], 'Anchor')
        self.assertEqual(anchor['gain'], 5.0)
        self.assertEqual(anchor['bass'], 5.0)
        self.assertEqual(anchor['mid'], 5.0)
        self.assertEqual(anchor['treble'], 5.0)
        self.assertEqual(anchor['master'], 7.0)
        self.assertFalse(anchor['is_validation'])

        # Check validation takes
        val_takes = [t for t in takes if t['is_validation']]
        self.assertEqual(len(val_takes), 2, "There must be exactly 2 holdout validation takes.")
        for vt in val_takes:
            self.assertEqual(vt['type'], 'Holdout Val')

    def test_matrix_bounds(self):
        """Verify all generated knob values fall within safe analog amp bounds (1.0 to 10.0)."""
        takes = generate_matrix(num_train=40, seed=42, step=0.5)
        for t in takes:
            for knob in ['gain', 'bass', 'mid', 'treble', 'master']:
                val = t[knob]
                self.assertGreaterEqual(val, 1.0, f"Knob {knob} is below minimum 1.0: {val}")
                self.assertLessEqual(val, 10.0, f"Knob {knob} is above maximum 10.0: {val}")

    def test_deterministic_generation(self):
        """Verify seeded PRNG produces identical matrix across repeated calls."""
        takes_1 = generate_matrix(num_train=40, seed=42)
        takes_2 = generate_matrix(num_train=40, seed=42)
        self.assertEqual(takes_1, takes_2)

    def test_csv_export_and_readback(self):
        """Verify CSV writer creates valid RFC 4180 CSV with matching rows and headers."""
        takes = generate_matrix(num_train=40, seed=42)
        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as tf:
            temp_csv = tf.name

        try:
            write_csv(takes, temp_csv)
            self.assertTrue(os.path.exists(temp_csv))

            with open(temp_csv, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                rows = list(reader)

            self.assertEqual(len(rows), 45)
            self.assertIn('take_id', rows[0])
            self.assertIn('output_filename', rows[0])
            self.assertEqual(rows[0]['take_id'], 'take_00')
        finally:
            if os.path.exists(temp_csv):
                os.remove(temp_csv)

    def test_data_json_manifest_schema(self):
        """Verify data.json adheres to PyTorch NAM parametric training schema."""
        takes = generate_matrix(num_train=40, seed=42)
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tf:
            temp_json = tf.name

        try:
            write_data_json(takes, temp_json, wav_dir="./takes", input_file="inputTrunc.wav", sample_rate=48000)
            self.assertTrue(os.path.exists(temp_json))

            with open(temp_json, 'r', encoding='utf-8') as f:
                manifest = json.load(f)

            self.assertEqual(manifest['sample_rate'], 48000)
            self.assertEqual(manifest['x'], "./takes/inputTrunc.wav")
            self.assertEqual(len(manifest['y']), 45)

            # Check normalized coordinates
            for entry in manifest['y']:
                self.assertIn('val', entry)
                self.assertIn('path', entry)
                self.assertIn('is_validation', entry)
                coords = entry['val']
                self.assertEqual(len(coords), 5, "Coordinates must have 5 knob dimensions")
                for c in coords:
                    self.assertGreaterEqual(c, 0.0, f"Normalized value {c} must be >= 0.0")
                    self.assertLessEqual(c, 1.0, f"Normalized value {c} must be <= 1.0")

            val_count = sum(1 for e in manifest['y'] if e['is_validation'])
            self.assertEqual(val_count, 2)
        finally:
            if os.path.exists(temp_json):
                os.remove(temp_json)

    def test_ema_filter_smoothing(self):
        """Verify EMA potentiometer filter dampens step noise and clamps to MIDI 0-127."""
        filt = EMAPotFilter(alpha=0.2, deadband=1)
        
        # Test initialization
        mid = filt.update(32768) # ~64 MIDI
        self.assertEqual(mid, 64)

        # Test small jitter below deadband
        jittered = filt.update(32800)
        self.assertEqual(jittered, 64, "Micro jitter below deadband should be rejected")

        # Test full sweep to 0
        for _ in range(30):
            zero_val = filt.update(0)
        self.assertEqual(zero_val, 0)

        # Test full sweep to 65535
        for _ in range(30):
            max_val = filt.update(65535)
        self.assertEqual(max_val, 127)

if __name__ == "__main__":
    unittest.main()
