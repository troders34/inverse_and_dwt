#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2025 ubtandika84.
#
# SPDX-License-Identifier: GPL-3.0-or-later
#


import numpy as np
from gnuradio import gr

def _periodic_pad(x, n):
    if n <= 0:
        return x
    return np.concatenate([x[-n:], x, x[:n]])

def _upsample(x):
    y = np.zeros(2 * len(x), dtype=x.dtype)
    y[::2] = x
    return y

def _downsample(x):
    return x[::2].copy()

def _conv_periodic(x, h):
    N = len(x)
    L = len(h)
    pad = L - 1
    xp = _periodic_pad(x, pad // 2)
    y = np.convolve(xp, h, mode='valid')
    if len(y) == N:
        return y
    # wrap-ke-N untuk keamanan
    out = y[:N].copy()
    if len(y) > N:
        out += np.roll(y, -N)[:N]
    return out

def db4_taps():
    # decimation taps
    h0 = np.array([
        -0.0105974017850021,  0.0328830116668852,  0.0308413818359869, -0.1870348117188811,
        -0.0279837694168599,  0.6308807679298589,  0.7148465705525415,  0.2303778133088552
    ], dtype=np.float32)
    h1 = np.array([
        -0.2303778133088552,  0.7148465705525415, -0.6308807679298589, -0.0279837694168599,
         0.1870348117188811,  0.0308413818359869, -0.0328830116668852, -0.0105974017850021
    ], dtype=np.float32)
    # reconstruction taps
    g0 = h0[::-1].copy()
    g1 = (-h1[::-1]).copy()
    return h0, h1, g0, g1

class wavelet_db4_tsb(gr.tagged_stream_block):
    def __init__(self, N=2048, L=8, mode="DWT", pack_order="A|D", len_tag_key="packet_len"):
        gr.tagged_stream_block.__init__(
            self,
            name="Wavelet db4 TSB",
            in_sig=[np.complex64],
            out_sig=[np.complex64],
            length_tag_key=len_tag_key,
        )
        self.N = int(N)
        self.L = int(L)
        self.mode = str(mode).upper()
        self.pack_order = str(pack_order)
        if self.N & (self.N - 1) != 0:
            raise ValueError("N must be power of two.")
        if self.L < 1 or self.L > int(np.log2(self.N)):
            raise ValueError("L out of range.")
        if self.pack_order != "A|D":
            raise ValueError("Only pack_order 'A|D' supported.")
        if self.mode not in ("DWT", "IDWT"):
            raise ValueError("mode must be 'DWT' or 'IDWT'.")
        h0, h1, g0, g1 = db4_taps()
        self.h0 = h0
        self.h1 = h1
        self.g0 = g0
        self.g1 = g1

    def _dwt_multilevel(self, x):
        a = x
        details = []
        for _ in range(self.L):
            lo = _conv_periodic(a, self.h0.astype(a.real.dtype))
            hi = _conv_periodic(a, self.h1.astype(a.real.dtype))
            a = _downsample(lo)
            d = _downsample(hi)
            details.append(d)
        cA = a
        out = [cA]
        out.extend(details[::-1])
        return np.concatenate(out)

    def _idwt_multilevel(self, coeffs):
        nA = self.N >> self.L
        cA = coeffs[:nA]
        Ds = []
        idx = nA
        for k in range(self.L, 0, -1):
            nD = self.N >> k
            Ds.append(coeffs[idx:idx + nD])
            idx += nD
        a = cA
        for d in Ds:
            a_up = _upsample(a)
            d_up = _upsample(d)
            lo = _conv_periodic(a_up, self.g0.astype(a.real.dtype))
            hi = _conv_periodic(d_up, self.g1.astype(a.real.dtype))
            a = lo + hi
        return a

    def work(self, input_items, output_items):
        x = input_items[0]
        n = len(x)
        if n != self.N:
            raise RuntimeError(f"Expected frame of {self.N}, got {n}")
        if self.mode == "DWT":
            y = self._dwt_multilevel(x.astype(np.complex64))
        else:
            y = self._idwt_multilevel(x.astype(np.complex64))
        output_items[0][:self.N] = y.astype(np.complex64)
        return self.N
