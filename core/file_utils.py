import os
import chardet
from datetime import datetime
import re

class FileUtils:
    """文件处理工具类"""
    def __init__(self, log_callback=None):
        self.current_encoding = 'utf-8'
        self.log_callback = log_callback or (lambda msg, level: None)
        # 添加更多常用编码作为备选
        self.fallback_encodings = [
            'utf-8', 'utf-8-sig',  # UTF-8变体
            'utf-16', 'utf-16le', 'utf-16be',  # UTF-16变体
            'ascii',  # ASCII
            'gb18030', 'gbk', 'gb2312', 'big5',  # 中文编码
            'shift-jis', 'iso-2022-jp', 'euc-jp',  # 日语编码
            'euc-kr', 'iso-2022-kr',  # 韩语编码
            'koi8-r', 'iso-8859-5',  # 俄语编码
            'iso-8859-1', 'windows-1252'  # 西欧语言编码
        ]
        self.time_pattern = re.compile(r'^(\d{4}/\d{1,2}/\d{1,2} \d{1,2}:\d{1,2}:\d{1,2})')
        
    def detect_encoding(self, file_path):
        """检测文件编码"""
        try:
            with open(file_path, 'rb') as f:
                rawdata = f.read(10000)
                result = chardet.detect(rawdata)
                
                if result['encoding'] and result['confidence'] >= 0.7:
                    detected_encoding = result['encoding'].lower()
                    # 使用chardet检测到的编码
                    try:
                        rawdata.decode(detected_encoding)
                        self.current_encoding = detected_encoding
                    except UnicodeDecodeError:
                        pass

                # 如果chardet检测失败或置信度低，尝试其他编码
                if not self.current_encoding or self.current_encoding == 'ascii':
                    for enc in self.fallback_encodings:
                        try:
                            rawdata.decode(enc)
                            self.current_encoding = enc
                            break
                        except UnicodeDecodeError:
                            continue

                # 如果所有尝试都失败，使用utf-8并忽略错误
                if not self.current_encoding:
                    self.current_encoding = 'utf-8'
                
                # 验证编码有效性
                test_str = rawdata[:100].decode(self.current_encoding, errors='replace')
                if '�' in test_str:  # 使用实际的替换字符而不是空字符串
                    self.log_callback(f"警告：使用 {self.current_encoding} 编码时存在替换字符", "WARN")

                is_utf8 = self.current_encoding.lower().startswith('utf-8')
                return True, is_utf8, f"文件编码检测为: {self.current_encoding}"
                
        except Exception as e:
            self.current_encoding = 'utf-8'  # 默认使用utf-8
            return False, False, f"编码检测失败: {str(e)}，使用默认UTF-8编码"

    def convert_to_utf8(self, file_path):
        """将文件转换为UTF-8编码"""
        try:
            # 先检测文件编码
            success, is_utf8, msg = self.detect_encoding(file_path)
            if not success:
                return False, msg
            
            if is_utf8:
                return True, "文件已经是UTF-8编码"
            
            # 读取文件内容
            with open(file_path, 'rb') as f:
                content = f.read()
            
            # 使用检测到的编码解码内容
            text = content.decode(self.current_encoding)
            
            # 创建备份文件
            backup_path = file_path + '.bak'
            os.rename(file_path, backup_path)
            
            # 以UTF-8编码写入新文件
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(text)
            
            return True, "文件已成功转换为UTF-8编码"
            
        except Exception as e:
            # 如果发生错误且备份文件存在，恢复原文件
            if os.path.exists(backup_path):
                os.replace(backup_path, file_path)
            return False, f"转换失败: {str(e)}"

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

    def get_encoding_info(self):
        """获取当前编码信息"""
        return self.current_encoding.upper()