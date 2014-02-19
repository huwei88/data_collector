import datetime
import hashlib;


def get_file_Md5(strFile):
    try:
        dst_file = open(strFile, "rb");
        md5 = hashlib.md5();
        strRead = "";
        
        while True:
            strRead = dst_file.read(8096);
            if not strRead:
                break;
            md5.update(strRead);
        #read file finish
        strMd5 = md5.hexdigest();
    finally:
        if dst_file:
            dst_file.close()
    return strMd5

def get_local_date():
    date_format = '%Y-%m-%d %H:%M:%S'
    return datetime.datetime.now().strftime(date_format)

def get_utc_date():
    date_format = '%Y-%m-%d %H:%M:%S'
    return datetime.datetime.utcnow().strftime(date_format)