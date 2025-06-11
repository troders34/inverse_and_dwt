"""
Embedded Python Blocks:

Each time this file is saved, GRC will instantiate the first class it finds
to get ports and parameters of your block. The arguments to __init__  will
be the parameters. All of them are required to have default values!
"""

import numpy as np
import pywt
from gnuradio import gr


class dwt_pywavelets(gr.sync_block):
    """
    Discrete Wavelet Transform block using PyWavelets.
    Input: stream of floats (or complex)
    Output: concatenated approximation and detail coefficients
    """

    def __init__(self, wavelet_name='db1', level=1, block_size=128):
        """arguments to this function show up as parameters in GRC"""
        gr.sync_block.__init__(
            self,
            name='DWT PyWavelets',
            in_sig=[np.float32],
            out_sig=[np.float32]
        )
        self.wavelet_name = wavelet_name
        self.level = level
        self.block_size = block_size
        self.buffer = np.array([], dtype=np.float32)

    def work(self, input_items, output_items):
        in0 = input_items[0]
        out = output_items[0]
        
        # Buffer input until having enough for a block
        self.buffer = np.concatenate((self.buffer, in0))
        n_blocks = len(self.buffer) // self.block_size
        
        if n_blocks == 0:
            return 0 # Not enough data yet
        
        n_out = 0
        for i in range(n_blocks):
            block = self.buffer[i*self.block_size:(i+1)*self.block_size]
            # Apply DWT
            coeffs = pywt.wavedec(block, self.wavelet_name, level=self.level)
            # Concatenate all coefficients
            dwt_out = np.concatenate(coeffs).astype(np.float32)
            out_len = len(dwt_out)
            if n_out + out_len > len(out):
                break # Output buffer full
            out[n_out:n_out+out_len] = dwt_out
            n_out += out_len
            
        # Remove processed samples from buffer
        self.buffer = self.buffer[n_blocks*self.block_size:]
        
        
        return n_out
