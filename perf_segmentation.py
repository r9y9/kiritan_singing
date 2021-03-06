import os
import numpy as np
from glob import glob
from os.path import join, basename, splitext
from nnmnkwii.io import hts
import sys
from util import segment_labels, trim_sil_and_pau, compute_nosil_duration
import config


# copy mono alignments to full
mono_files = sorted(glob(join(config.out_dir, "mono_dtw", "*.lab")))
full_files = sorted(glob(join(config.out_dir, "sinsy_full_round", "*.lab")))
dst_dir = join(config.out_dir, "full_dtw")
os.makedirs(dst_dir, exist_ok=True)

for mono, full in zip(mono_files, full_files):
    m, f = hts.load(mono), hts.load(full)
    assert len(m) == len(f)
    f.start_times = m.start_times
    f.end_times = m.end_times
    name = basename(mono)
    with open(join(dst_dir, name), "w") as of:
        of.write(str(f))


# segmentation
base_files = sorted(glob(join(config.out_dir, "mono_dtw", "*.lab")))
base_files = base_files[:config.num_annotated_files]

lengths = {}

for name in ["full_dtw", "sinsy_full_round", "sinsy_mono_round"]:
    files = sorted(glob(join(config.out_dir, name, "*.lab")))
    files = files[:config.num_annotated_files]
    for idx, base in enumerate(base_files):
        utt_id = splitext(basename(base))[0]
        if utt_id != "05" and False:
            continue
        base_lab = hts.load(base)
        base_segments, start_indices, end_indices = segment_labels(
            base_lab, True, config.segmentation_threshold,
            min_duration=config.segment_min_duration,
            force_split_threshold=config.force_split_threshold)
        if name == "full_dtw":
            d = []
            for seg in base_segments:
              d.append((seg.end_times[-1] - seg.start_times[0]) * 1e-7)
            lengths[utt_id] = d

        lab = hts.load(files[idx])
        assert len(lab) == len(base_lab)
        segments = []
        for s,e in zip(start_indices, end_indices):
            segments.append(lab[s:e+1])

        dst_dir = join(config.out_dir, f"{name}_seg")
        os.makedirs(dst_dir, exist_ok=True)
        for idx, seg in enumerate(segments):
            with open(join(dst_dir, f"{utt_id}_seg{idx}.lab"), "w") as of:
                of.write(str(seg))

        base_dst_dir = join(config.out_dir, "mono_dtw_seg")
        os.makedirs(base_dst_dir, exist_ok=True)
        for idx, seg in enumerate(base_segments):
            with open(join(base_dst_dir, f"{utt_id}_seg{idx}.lab"), "w") as of:
                of.write(str(seg))


for ls in [lengths]:
    for k, v in ls.items():
        print("{}.lab: segment duration min {:.02f}, max {:.02f}, mean {:.02f}".format(
            k, np.min(v), np.max(v), np.mean(v)))

    flatten_lengths = []
    for k, v in ls.items():
        sys.stdout.write(f"{k}.lab: segment lengths: ")
        for d in v:
            sys.stdout.write("{:.02f}, ".format(d))
            flatten_lengths.append(d)
        sys.stdout.write("\n")

    print("Segmentation stats: min {:.02f}, max {:.02f}, mean {:.02f}".format(
        np.min(flatten_lengths), np.max(flatten_lengths), np.mean(flatten_lengths)))

    print("Total number of segments: {}".format(len(flatten_lengths)))

sys.exit(0)