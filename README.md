# inverse_and_dwt
Inverse-DWT and DWT Python code used on GNU Radio Companion

Evaluasi:
@64qam_text

line#7: intSource akan mengubah setiap karakter pada send.text ke dalam bentuk karakter ASCII. Contoh: G=71; n=110; e=101
line#9: source2Bin mengubah representasi karakter pada ASCII ke dalam bentuk 8-bit biner. Contoh: 71=01000111; 110=01101110; 101=01100101
line#10: bitStreamSource mengubah bentuk penyajian yang semula 8-bit biner column-vector (source2Bin) menjadi row-vector. Bentuk permisalan: 011010101010...
line#15~19: padding, yaitu penambahan 1 digit bit dengan nilai '0' agar 1 simbol genap 8-bit
line#20: new_bitstream_structure mengubah lagi semula sudah row-vector menjadi 8-bit column-vector.

Pertanyaan: 
#1 apakah line#20 perlu dan sesuai dengan modulasi 256-QAM? (digunakan order 256 agar tidak perlu lagi terjadi pemotongan biner dari 8-bit menjadi 8-bit per simbol).
#2 
