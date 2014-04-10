'''
return data format:
{'date': 'collect time', 'content': content,
'name': 'data name', 'id': 'the md5 of the collected data',
'storage_driver': 'The store plug-in.'
}
'''

from collector.utils import util


@util.send_data
def collect_file_content(**kwargs):
    """
    files: The files which content will be collected.
        type: list
    """
    files = kwargs.pop('files')
    data_names = kwargs['data_names']
    if len(files) != len(data_names):
        raise
    contents = []
    for f in files:
        content = ''
        try:
            with open(f, 'r') as tmp_file:
                con = tmp_file.readline()
                while con:
                    content = content + con
                    con = tmp_file.readline()
                contents.append(content)
        except:
            raise
    return contents
