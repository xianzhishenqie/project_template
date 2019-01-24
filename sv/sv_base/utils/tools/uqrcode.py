import qrcode
import qrtools


def make_qrcode(qrcode_str, filepath):
    img = qrcode.make(qrcode_str)
    img.save(filepath)



def parse_qrcode(qrcode_file):
    qr = qrtools.QR()
    qr.decode(qrcode_file)
    return qr.data

