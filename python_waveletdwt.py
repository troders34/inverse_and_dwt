#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2025 ubtandika84.
#
# SPDX-License-Identifier: GPL-3.0-or-later
#


import numpy as np
from gnuradio import gr
import pwt
try:
    import pywt
except Exception:
    pywt = None

def _check_params(nsc, level):
    if nsc <= 0 or (nsc & (nsc - 1)) != 0:
        raise ValueError("nsc must be power of two and > 0")
    if level <= 0 or (2 ** level) > nsc:
        raise ValueError("level must satisfy 2^level <= nsc")


def _bandsizes(nsc, level):
    sizes = [nsc // (2 ** level)]
    sizes += [nsc // (2 ** k) for k in range(level, 0, -1)]
    return sizes  # [|cA_L|, |cD_L|, ..., |cD_1|], sum == nsc


def _wavedec_complex(x, wavelet, level, mode):
    # PyWavelets tidak mendukung kompleks langsung. Pisahkan real-imag.
    cR = pywt.wavedec(x.real.astype(np.float64), wavelet, level=level, mode=mode)
    cI = pywt.wavedec(x.imag.astype(np.float64), wavelet, level=level, mode=mode)
    coeffs = [cR[0] + 1j * cI[0]]
    for i in range(1, len(cR)):
        coeffs.append(cR[i] + 1j * cI[i])
    return coeffs  # [cA_L, cD_L, ..., cD_1]


def _pack(coeffs, pack_order):
    # Only support "A|D" => [cA_L | cD_L | cD_{L-1} | ... | cD_1]
    if pack_order != "A|D":
        raise ValueError("Unsupported pack_order. Use 'A|D'.")
    return np.concatenate([coeffs[0]] + coeffs[1:]).astype(np.complex64)


class wavelet_dwt_gen(gr.basic_block):
    """
    Stream-in, stream-out general block.
    """
    def __init__(self,
                 nsc=128, level=4,
                 wavelet='db4', mode='periodization', pack_order='A|D',
                 packet_len_key='packet_len', align_to_tag=True,
                 use_pywt=True, debug=False):
        gr.basic_block.__init__(self,
                                name="wavelet_dwt_gen",
                                in_sig=[np.complex64],
                                out_sig=[np.complex64])
        _check_params(int(nsc), int(level))
        self.nsc = int(nsc)
        self.level = int(level)
        self.wavelet = str(wavelet)
        self.mode = str(mode)
        self.pack_order = str(pack_order)
        self.packet_len_key = str(packet_len_key)
        self.align_to_tag = bool(align_to_tag)
        self.use_pywt = bool(use_pywt) and (pywt is not None)
        self.debug = bool(debug)

        if not self.use_pywt:
            raise RuntimeError("PyWavelets not available. Install pywt or set use_pywt=False and add fallback.")

        self.set_output_multiple(self.nsc)
        self._buf = np.zeros(0, dtype=np.complex64)
        self._sizes = _bandsizes(self.nsc, self.level)
        self._await_sync = self.align_to_tag  # menunggu tag start saat align_to_tag=True

    def forecast(self, noutput_items, ninputs):
        # Need minimal input nsc to produce multiplied nsc output
        nreq = max(self.nsc, int(np.ceil(noutput_items / self.nsc)) * self.nsc)
        self.set_input_required_itemsets([nreq])

    def _maybe_realign_to_tag(self, in0):
        # Realign to tag packet_len if necessary
        if not self.align_to_tag:
            return
        nread = int(self.nitems_read(0))
        tags = []
        self.get_tags_in_range(tags, 0, nread, nread + len(in0))
        # Finding first tag with corresponding packet_len_key
        for t in tags:
            if pmt.symbol_to_string(t.key) == self.packet_len_key:
                pos = int(t.offset - nread)
                if 0 <= pos < len(in0):
                    self._buf = np.array([], dtype=np.complex64)
                    tail = in0[pos:].astype(np.complex64, copy=False)
                    if tail.size:
                        self._buf = np.concatenate([self._buf, tail])
                    self._await_sync = False
                    return

    def general_work(self, input_items, output_items):
        in0 = input_items[0]
        out0 = output_items[0]
        n_in = len(in0)
        if n_in == 0:
            return 0

        if self._await_sync:
            self._maybe_realign_to_tag(in0)
        else:
            self._buf = np.concatenate([self._buf, in0.astype(np.complex64, copy=False)])

        produced = 0
        frames = []

        # synchronization
        if self.align_to_tag and self._await_sync:
            self.consume(0, n_in)
            return 0

        while self._buf.size >= self.nsc:
            frame = self._buf[:self.nsc]
            self._buf = self._buf[self.nsc:]
            frames.append(frame)

        for x in frames:
            coeffs = _wavedec_complex(x, self.wavelet, self.level, self.mode)
            y = _pack(coeffs, self.pack_order)
            n = min(y.size, out0.size - produced)
            out0[produced:produced + n] = y[:n]
            produced += n
            if produced + self.nsc > out0.size:
                break

        self.consume(0, n_in)
        return produced
