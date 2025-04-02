#!/usr/bin/env python

import matplotlib.pyplot as plt
import numpy as np
import os
import sys

hamBands_MHz = {
    160: np.array([1.81,    2]),
    80: np.array([3.5,      3.8]),
    60: np.array([5.3515,   5.3665]),
    40: np.array([7,        7.2]),
    30: np.array([10.1,     10.15]),
    20: np.array([14,       14.35]),
    17: np.array([18.068,   18.168]),
    15: np.array([21,       21.45]),
    12: np.array([24.89,    24.99]),
    11: np.array([26.965,   27.405]),
    10: np.array([28,       29.7]),
    6: np.array([50,        52])
}


def cli(argv):
    prog = os.path.basename(argv[0])
    argv = argv[1:]
    fullwave = False
    metric = True
    bands = []
    i = 0
    while i < len(argv):
        if argv[i] == '-f':
            fullwave = True
        elif argv[i] == '-i':
            metric = False
        else:
            try:
                b = int(argv[i])
            except ValueError:
                usage(prog)
            bands.append(b)
        i += 1
    bands.sort(reverse=True)
    if len(bands) == 0:
        usage(prog)
    return prog, bands, metric, fullwave


def edges_MHz(prog, bands_MHz):
    e_MHz = []
    for b in bands_MHz:
        if b in hamBands_MHz:
            e_MHz.append(hamBands_MHz[b])
        else:
            usage(prog)
    return e_MHz


def graph(title, edges_ft, safe_ranges, unknown_ranges, metric, lenQtr_ft):
    plt.figure(figsize=(12, 3), dpi=300)
    plt.title(title, fontsize=12)
    plt.xlabel('Wire Length in %s' % ('m' if metric else 'ft'))
    plt.yticks([])
    plt.ylim(0, 1)
    plt.grid(True)

    ft_to_m = 0.3048
    conv = ft_to_m if metric else 1.0

    xMax = 0
    # Resonant (red)
    for e in edges_ft:
        e_m = e * conv
        plt.fill([e_m[0], e_m[0], e_m[1], e_m[1]],
                 [0, 1, 1, 0], 'red', alpha=0.75)
        mid = (e_m[0] + e_m[1]) / 2
        # label = "%.1f–%.1f %s" % (e_m[0], e_m[1], 'm' if metric else 'ft')
        # plt.text(mid, 0.5, label, ha='center', va='center',
        #          fontsize=8, color='black', rotation=90)
        xMax = max(xMax, e_m[1])

    # Safe (green)
    for safe in safe_ranges:
        safe_m = [s * conv for s in safe]
        mid = (safe_m[0] + safe_m[1]) / 2
        plt.fill([safe_m[0], safe_m[0], safe_m[1], safe_m[1]],
                 [0, 1, 1, 0], 'green', alpha=0.75)
        label = "%.1f–%.1f %s\n(Center: %.1f %s)" % (
            safe_m[0], safe_m[1], 'm' if metric else 'ft',
            mid, 'm' if metric else 'ft'
        )
        plt.text(mid, 0.5, label, ha='center', va='center',
                 fontsize=8, color='black', rotation=90)
        xMax = max(xMax, safe_m[1])

    # Unknown (gray)
    for unknown in unknown_ranges:
        unknown_m = [s * conv for s in unknown]
        plt.fill([unknown_m[0], unknown_m[0], unknown_m[1], unknown_m[1]], [
                 0, 1, 1, 0], color='gray', alpha=0.75)
        mid = (unknown_m[0] + unknown_m[1]) / 2
        # label = "%.1f–%.1f %s" % (
        #     unknown_m[0], unknown_m[1], 'm' if metric else 'ft')
        # plt.text(mid, 0.5, label, ha='center', va='center',
        #          fontsize=8, color='black', rotation=90)

    plt.xlim(0, xMax * 1.05)  # Skala beginnt bei 0
    plt.tight_layout()
    plt.savefig('resonant_frequencies.png')  # Kein bbox_inches='tight'
    print("Saved as 'resonant_frequencies.png'")


def high_V(band_MHz, lenMax_ft):
    len1_ft, len0_ft = 468 / band_MHz
    multiples = int(lenMax_ft / len0_ft)
    res_ft = np.zeros((multiples, 2))
    res_ft[:, 0] = (1 + np.arange(multiples)) * len0_ft
    res_ft[:, 1] = (1 + np.arange(multiples)) * len1_ft
    return res_ft


def usage(prog):
    print('Usage: %s [-f] [-m] band(s)' % prog)
    print('       -f for full wave, default: quarter wave')
    print('       -i for lengths in feet instead of meters')
    print('       Bands by name 160, 80, 60, 40, 30, 20, 17, 15, 12, 11, 10, 6 m')
    print('       Example: %s -f -i 40 20 15 10' % prog)
    print('       Happy calculating & 73 de Ralph HB3XCO')
    sys.exit(1)


def find_safe_lengths(resonant_ranges, min_gap_ft=3):
    resonant_ranges = sorted(resonant_ranges, key=lambda r: r[0])
    safe_ranges = []
    if resonant_ranges[0][0] > min_gap_ft:
        safe_ranges.append((0, resonant_ranges[0][0]))
    for i in range(len(resonant_ranges) - 1):
        end = resonant_ranges[i][1]
        start_next = resonant_ranges[i + 1][0]
        if start_next - end >= min_gap_ft:
            safe_ranges.append((end, start_next))
    return safe_ranges


def find_unknown_ranges(resonant_ranges, safe_ranges):
    all_blocks = sorted(resonant_ranges + safe_ranges, key=lambda r: r[0])
    unknowns = []
    for i in range(len(all_blocks) - 1):
        gap_start = all_blocks[i][1]
        gap_end = all_blocks[i + 1][0]
        if gap_end - gap_start > 0:
            unknowns.append((gap_start, gap_end))
    return unknowns


def main(argv):
    prog, bands_m, metric, fullwave = cli(argv)
    bands_MHz = edges_MHz(prog, bands_m)

    lenQtr_ft = 234 / bands_MHz[0][0]
    lenMax_ft = 2 * 468 / \
        bands_MHz[0][0] if fullwave else 468 / bands_MHz[0][0]

    all_ft = [np.array([0, lenQtr_ft])]
    for band_MHz in bands_MHz:
        res_ft = high_V(band_MHz, lenMax_ft)
        all_ft.extend(res_ft)

    safe_ranges = find_safe_lengths(all_ft)
    unknown_ranges = find_unknown_ranges(all_ft, safe_ranges)

    s = str(bands_m)
    graph('Wire Lenghts for %s m' %
          s[1:-1], all_ft, safe_ranges, unknown_ranges, metric, lenQtr_ft)

    conv = 0.3048 if metric else 1.0
    unit = 'm' if metric else 'ft'

    print("\n🔴 Don't use these lengths:")
    for r in all_ft:
        print("  %.1f–%.1f %s" % (r[0] * conv, r[1] * conv, unit))

    print("\n🟢 Recommended wire lengths:")
    for r in safe_ranges:
        print("  %.1f–%.1f %s" % (r[0] * conv, r[1] * conv, unit))

    print("\n⚪ Irrelevant wire lengths:")
    for r in unknown_ranges:
        print("  %.1f–%.1f %s" % (r[0] * conv, r[1] * conv, unit))


if __name__ == '__main__':
    main(sys.argv)
