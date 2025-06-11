"""
Embedded Python Blocks:

Each time this file is saved, GRC will instantiate the first class it finds
to get ports and parameters of your block. The arguments to __init__  will
be the parameters. All of them are required to have default values!
"""

import numpy as np
import pywt
from gnuradio import gr


class idwt_pywavelets(gr.sync_block):
    """
    Inverse Discrete Wavelet Transform block using PyWavelets.
    Input: concatenated DWT coefficients (float)
    Output: reconstructed signal (float)
    """

    def __init__(self, wavelet_name='db1', level=1, block_size=128):
        gr.sync_block.__init__(
            self,
            name='IDWT PyWavelets',
            in_sig=[np.float32],
            out_sig=[np.float32]
        )
        self.wavelet_name = wavelet_name
        self.level = level
        self.block_size = block_size
        self.coeff_lengths = self._calc_coeff_lengths()
        self.input_block_len = sum(self.coeff_lengths)
        self.buffer = np.array([], dtype=np.float32)
        
    def _calc_coeff_lengths(self):
        # calculate the elngths of each coefficient array for given block_size, wavelet, and level
        dummy = np.zeros(self.block_size, dtype=np.float32)
        coeffs = pywt.waverec(dummy, self.wavelet_name, level=self.level)
        return [len(c) for c in coeffs]

    def work(self, input_items, output_items):
        in0 = input_items[0]
        out = output_items[0]
        
        # Buffer input until we have enough for a block
        self.buffer = np.concatenate((self.buffer, in0))
        n_blocks = len(self.buffer) // self.input_block_len
        
        if n_blocks == 0:
            return 0 # Not enough data yet
        
        n_out = 0
        for i in range(n_blocks):
            block = self.buffer[i*self.input_block_len:(i+1)*self.input_block_len]
            # split block into coeffs
            coeffs = []
            idx = 0
            for clen in self.coeff_lengths:
                coeffs.append(block[idx:idx+clen])
                idx += clen
            # inverse DWT
            rec = pywt.waverec(coeffs, self.wavelet_name)
            rec = rec[:self.block_size] # truncate to original block size
            out_len = len(rec)
            if n_out + out_len > len(out):
                break # output buffer full
            out[n_out:n_out+out_len] = rec.astype(np.float32)
            n_out += out_len
        
        # remove processed samples from buffer
        self.buffer = self.buffer[n_blocks*self.input_block_len:]
        
        return n_out
