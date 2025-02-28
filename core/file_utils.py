import os
import chardet
from datetime import datetime
import re

class FileUtils:
    """文件处理工具类"""
    def __init__(self):
        self.current_encoding = 'utf-8'
        self.fallback_encodings = ['gb18030', 'gbk', 'big5']
        self.time_pattern = re.compile(r'^(\d{4}/\d{1,2}/\d{1,2} \d{1,2}:\d{1,2}:\d{1,2})')
        
    def detect_encoding(self, file_path):
        """检测文件编码"""
        try:
            with open(file_path, 'rb') as f:
                rawdata = f.read(10000)
                result = chardet.detect(rawdata)
                
                if result['encoding'] and 'gb' in result['encoding'].lower():
                    self.current_encoding = result['encoding']
                else:
                    for enc in ['utf-8-sig', 'gb18030', 'gbk', 'big5']:
                        try:
                            rawdata.decode(enc)
                            self.current_encoding = enc
                            break
                        except:
                            continue
                
                # 验证编码有效性
                test_str = rawdata[:100].decode(self.current_encoding, errors='replace')
                if '' in test_str:
                    raise UnicodeDecodeError("检测到替换字符，编码可能不正确")
                
                return True, f"文件编码检测为: {self.current_encoding}"
        except Exception as e:
            self.current_encoding = 'gb18030'  # 中文最通用编码
            return False, f"编码检测失败: {str(e)}，使用备选编码"

    def decode_content(self, content):
        """解码内容"""
        try:
            return content.decode(self.current_encoding)
        except UnicodeDecodeError:
            for enc in self.fallback_encodings:
                try:
                    return content.decode(enc)
                except:
                    continue
            return content.decode(self.current_encoding, errors='replace')

    def parse_timestamp(self, line):
        """解析时间戳"""
        match = self.time_pattern.match(line)
        if match:
            try:
                return datetime.strptime(match.group(1), '%Y/%m/%d %H:%M:%S')
            except:
                return None
        return None

    def get_last_timestamp(self, file_path):
        """获取文件的最后有效时间戳"""
        try:
            with open(file_path, 'rb') as f:
                f.seek(-10240, os.SEEK_END)  # 读取最后10KB内容
                content = f.read().decode(self.current_encoding, errors='ignore')
                for line in reversed(content.splitlines()):
                    ts = self.parse_timestamp(line)
                    if ts:
                        return ts
        except:
            pass
        return None

    def extract_content(self, line):
        """提取内容"""
        markers = ['@來自', '@来自']  # 支持简繁体
        for marker in markers:
            index = line.find(marker)
            if index != -1:
                # 提取冒号后的内容（如果存在）
                colon_index = line.find(':', index)
                if colon_index != -1:
                    return line[colon_index+1:].strip()
                # 如果没有冒号，直接取标记后的内容
                return line[index + len(marker):].strip()
        return line
