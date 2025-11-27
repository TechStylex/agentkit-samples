# Copyright (c) 2025 Beijing Volcano Engine Technology Co., Ltd. and/or its affiliates.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import requests
from pathlib import Path
from typing import Optional, List
from urllib.parse import urlparse, unquote


def file_download(
    url: List[str], 
    save_dir: Optional[str] = None, 
    filename: Optional[List[str]] = None
) -> List[str]:
    """
    从互联网批量下载文件到本地，支持同时下载多个URL，避免agent循环调用
    
    Args:
        url: 文件的URL地址列表（可以传入单个URL的列表或多个URL的列表）
        save_dir: 保存目录，默认/tmp目录
        filename: 保存的文件名列表，默认为None时会从URL中提取文件名
        
    Returns:
        List[str]: 下载文件保存的完整路径列表
        
    Raises:
        requests.exceptions.RequestException: 网络请求失败
        IOError: 文件写入失败
        ValueError: 参数错误
        
    Examples:
        # 下载单个文件
        paths = file_download(["https://example.com/file.pdf"])
        
        # 批量下载多个文件
        paths = file_download([
            "https://example.com/file1.pdf",
            "https://example.com/file2.jpg",
            "https://example.com/file3.json"
        ])
    """
    # 确保url是列表
    if not isinstance(url, list):
        raise ValueError("url参数必须是列表类型")
    
    urls = url
    if save_dir is None:
        # 优先使用环境变量
        save_dir = os.getenv('DOWNLOAD_DIR', "/tmp")
    
    # 处理filename参数
    if filename is None:
        filenames = [None] * len(urls)
    elif isinstance(filename, list):
        if len(filename) != len(urls):
            raise ValueError(f"filename列表长度({len(filename)})必须与url列表长度({len(urls)})相同")
        filenames = filename
    else:
        raise ValueError("filename必须是列表或None")
    
    # 下载所有文件
    downloaded_paths = []
    for url_item, filename_item in zip(urls, filenames):
        path = _download_single_file(url_item, save_dir, filename_item)
        downloaded_paths.append(path)
    
    return downloaded_paths


def _download_single_file(url: str, save_dir: Optional[str] = None, filename: Optional[str] = None) -> str:
    """
    下载单个文件（内部辅助函数）
    
    Args:
        url: 文件的URL地址
        save_dir: 保存目录，默认/tmp目录
        filename: 保存的文件名
        
    Returns:
        str: 下载文件保存的完整路径
        
    Raises:
        requests.exceptions.RequestException: 网络请求失败
        IOError: 文件写入失败
    """
    # 确定保存目录
    if save_dir is None:
        # 优先使用环境变量
        save_dir = os.getenv('DOWNLOAD_DIR', "/tmp")
        if save_dir is None:
            # 获取项目根目录（假设当前文件在 tool 子目录下）
            current_file = Path(__file__)
            project_root = current_file.parent.parent
            save_dir = str(project_root)
    
    # 确保保存目录存在
    save_path = Path(save_dir)
    save_path.mkdir(parents=True, exist_ok=True)
    
    # 确定文件名
    if filename is None:
        # 从URL中提取文件名
        parsed_url = urlparse(url)
        filename = unquote(os.path.basename(parsed_url.path))
        
        # 如果URL中没有文件名，使用默认名称
        if not filename or filename == '/':
            filename = 'downloaded_file'
    
    # 完整的文件路径
    full_path = save_path / filename
    
    # 如果文件已存在，添加序号避免覆盖
    counter = 1
    original_stem = full_path.stem
    original_suffix = full_path.suffix
    while full_path.exists():
        filename = f"{original_stem}_{counter}{original_suffix}"
        full_path = save_path / filename
        counter += 1
    
    # 下载文件
    try:
        response = requests.get(url, stream=True, timeout=30)
        response.raise_for_status()
        
        # 写入文件
        with open(full_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        
        return str(full_path.absolute())
    
    except requests.exceptions.RequestException as e:
        raise requests.exceptions.RequestException(f"下载文件失败: {str(e)}")
    except IOError as e:
        raise IOError(f"写入文件失败: {str(e)}")


# 示例使用
if __name__ == "__main__":
    # 示例1: 下载单个文件（使用默认目录）
    try:
        file_paths = file_download(["https://example.com/sample.pdf"])
        print(f"文件下载成功: {file_paths[0]}")
    except Exception as e:
        print(f"下载失败: {e}")
    
    # 示例2: 下载单个文件（指定保存目录）
    try:
        file_paths = file_download(["https://example.com/image.jpg"], save_dir="/tmp")
        print(f"文件下载成功: {file_paths[0]}")
    except Exception as e:
        print(f"下载失败: {e}")
    
    # 示例3: 批量下载多个文件（避免agent循环调用）
    try:
        urls = [
            "https://example.com/file1.pdf",
            "https://example.com/file2.jpg",
            "https://example.com/file3.json"
        ]
        file_paths = file_download(urls)
        print(f"批量下载成功，共 {len(file_paths)} 个文件:")
        for i, path in enumerate(file_paths, 1):
            print(f"  {i}. {path}")
    except Exception as e:
        print(f"下载失败: {e}")
    
    # 示例4: 批量下载多个文件并指定文件名
    try:
        urls = [
            "https://example.com/file1.pdf",
            "https://example.com/file2.jpg"
        ]
        filenames = ["my_document.pdf", "my_image.jpg"]
        file_paths = file_download(urls, filename=filenames)
        print(f"批量下载成功:")
        for path in file_paths:
            print(f"  {path}")
    except Exception as e:
        print(f"下载失败: {e}")
    
    # 示例5: 使用环境变量配置目录
    # 在运行前设置: export DOWNLOAD_DIR=/path/to/downloads
    try:
        file_paths = file_download(["https://example.com/data.json"])
        print(f"文件下载成功: {file_paths[0]}")
    except Exception as e:
        print(f"下载失败: {e}")

