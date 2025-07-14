clc;
clear;

% REED-SOLOMON ENCODING
%properties
mRS = 3;          % number of bits per symbol;
nRS = 2^mRS - 1;  % codeword length
kRS = 3;          % message length, so the parity=3 and coderate=4/7
%input and conversion
sourceID = fopen('send.txt', 'r', 'b', 'US-ASCII');
sourceChar = fread(sourceID, 'uint8=>uint8');
fclose(sourceID);
char2Binary = dec2bin(sourceChar, 8);
bitStream = reshape(char2Binary', 1, []);
numBits = numel(bitStream);
rem_bits = mod(numBits, mRS);
if rem_bits ~= 0
    padSize = mRS - rem_bits;
    bitStream = [bitStream, repmat('0', 1, padSize)];
end
symbols_3bit = bin2dec(reshape(bitStream, mRS, [])');
numSymbols = numel(symbols_3bit);
remSymbols = mod(numSymbols, kRS);
if remSymbols ~= 0
    padSize = kRS - remSymbols;
    symbols_3bit = [symbols_3bit; zeros(padSize, 1)];
end
msg = reshape(symbols_3bit, kRS, []).';
msgGF = gf(msg, mRS);
code = rsenc(msgGF, nRS, kRS);
disp('Encoding Successful!');
disp('Size of the output codeword length');
disp(size(code.x));
