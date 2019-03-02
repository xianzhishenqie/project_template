import qrcode
import qrtools


def make_qrcode(qrcode_str: str, filepath: str) -> None:
    """生成二维码

    :param qrcode_str: 二维码内容
    :param filepath: 输出路径
    """
    img = qrcode.make(qrcode_str)
    img.save(filepath)



def parse_qrcode(qrcode_file: object) -> str:
    """解析二维码

    :param qrcode_file: 二维码文件
    :return: 二维码内容
    """
    qr = qrtools.QR()
    qr.decode(qrcode_file)
    return qr.data

