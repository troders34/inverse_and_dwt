clc;
clear;

% MODULATION ------------------------------
%input
textID = fopen('send.txt', 'r', 'b', 'US-ASCII');  % each character in the source text will represent to ASCII characters.
intSource = fread(textID, 'char*1');  % read text file and interpret the source or output as 8-bit characters.
fclose(textID);
source2Bin = dec2bin(intSource, 8);    % convert each character to 8-bit binary row
bitStreamSource = reshape(source2Bin', 1, []);  % reshape into binary row-vector
%properties
M = 16;
k = log2(M);
n = 30000;  % number of symbols per frame
sps = 1;  % number of samples per symbol (oversampling factor)
numBits_source = length(bitStreamSource);  
modulo_bits = mod(numBits_source, k);      % remainder after division
if modulo_bits ~= 0
    pad_bits = k - modulo_bits;
    bitStreamSource = [bitStreamSource, repmat('0', 1, pad_bits)];
end
new_bitstream_structure = reshape(bitStreamSource, k, []).';  % PERLU?
sourceSymbols = bin2dec(new_bitstream_structure);  % PERLU?
% plot to show binary values in specific range number of bits
stem(intSource(1:24), 'filled');
title('First 20-bits of the converted source binary data');
xlabel('Bit Index');
ylabel('Binary Value');
%modulating
modulatedSource = qammod(sourceSymbols, M, 'UnitAveragePower', true, 'InputType', 'integer');
%plot on constellation
constDiagram = comm.ConstellationDiagram( ...
    'Title', 'Modulated 256-QAM', ...
    'ReferenceConstellation', qammod(0:M-1, M, 'UnitAveragePower', true), ...
    'ReferenceColor', [1 1 0]);
constDiagram(modulatedSource);

% DEMODULATION ------------------------------
demodulatedSource = qamdemod(modulatedSource, M, 'UnitAveragePower', true, 'OutputType', 'integer', 'OutputDataType', 'double');
receivedSymbols = dec2bin(demodulatedSource, k);
receivedBits = reshape(receivedSymbols.', [], 1);
disp('16-QAM Demodulated Bits');
disp(receivedBits(1:20).');  % showing 20 binary digits of demodulated bits
disp('End');

%clear y Fs
%[y, Fs] = audioread('catchyRNBpopLOOP_44100hz_16bit_stereo.wav', [1, 5*44100]);
%sound(y, Fs);
%display result by a text file
%resultID = fopen('demodulated_source.txt', 'w');
%fprintf(resultID, '%d', receivedBits);
%fclose(resultID);
