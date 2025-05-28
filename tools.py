from typing import List, Dict, Callable, Optional
from dataclasses import asdict, is_dataclass
import os

def load_prompt(filename:str,file=None)->str:
    base_dir = os.path.dirname(__file__)
    file_path = os.path.join(base_dir,"my_prompt",filename)
    my_prompt = ""

    try:
        with open(file_path,"r",encoding="utf-8") as f:
            my_prompt = f.read()
            #print("my_prompt:",my_prompt)
        
        print(f'✅ prompt文件加载成功！({file_path})')
    except FileNotFoundError:
        print(f'❌ 文件不存在: {file_path}')
    except IOError as e:
        print(f'⛔ 文件读取失败: {str(e)}')
    
    return my_prompt

def save_to_file(filename: str, content: str,writeType:str="w") -> None:
    """
    将内容保存到指定文件中。
    :param filename: 文件路径
    :param content: 要保存的内容
    """
    base_dir = os.path.dirname(__file__)
    file_path = os.path.join(base_dir, "my_output", filename)  # 假设保存到 "output" 文件夹中

    try:
        
        with open(file_path, writeType, encoding="utf-8") as f:
            f.write(content)
        print(f'✅ 文件保存成功！({file_path})')
    except IOError as e:
        print(f'⛔ 文件保存失败: {str(e)}')

#将对象列表转换为可读字符串
class ListString:
    def list_to_string(items: List[object],separator: str = ", ",format_func: Optional[Callable[[object], str]] = None) -> str:
        """
        :param items: 需要转换的对象列表
        :param separator: 分隔符，默认为", "
        :param format_func: 自定义格式化函数
        """
        if items is None:
            return "null"
        
        if not items:
            return "[]"

        formatted = []
        for item in items:
            if format_func:
                formatted.append(format_func(item))
            else:
                formatted.append(ListString._convert_object(item))

        return f"[{separator.join(formatted)}]"

    #递归转换对象为字符串
    def _convert_object(obj: object, indent: int = 0) -> str:
        if obj is None:
            return "null"
        
        # 处理基础类型
        if isinstance(obj, (int, float, str, bool)):
            return f'"{obj}"' if isinstance(obj, str) else str(obj)
        
        # 处理数据类
        if is_dataclass(obj):
            return ListString._format_dataclass(obj, indent)
        
        # 处理字典
        if isinstance(obj, dict):
            return ListString._format_dict(obj, indent)
        
        # 处理可迭代对象
        if isinstance(obj, (list, tuple, set)):
            return ListString._format_iterable(obj, indent)
        
        # 其他对象类型
        return ListString._format_generic_object(obj, indent)

    def _format_dataclass(obj: object, indent: int) -> str:
        """格式化数据类对象"""
        data = asdict(obj)
        return ListString._format_dict(data, indent)

    def _format_dict(data: dict, indent: int) -> str:
        """格式化字典类型"""
        entries = []
        for k, v in data.items():
            entry = f'{"  " * indent}"{k}": {ListString._convert_object(v, indent + 1)}'
            entries.append(entry)
        return "{\n" + ",\n".join(entries) + "\n" + "  " * (indent - 1) + "}"
    
    def _format_iterable(items: iter, indent: int) -> str:
        """格式化可迭代对象"""
        elements = [ListString._convert_object(item, indent + 1) for item in items]
        return "[\n" + ",\n".join(elements) + "\n" + "  " * (indent - 1) + "]"

    def _format_generic_object(obj: object, indent: int) -> str:
        """处理普通对象"""
        try:
            # 尝试获取字典表示
            return ListString._format_dict(obj.__dict__, indent)
        except AttributeError:
            # 最后保底处理
            return str(obj)
