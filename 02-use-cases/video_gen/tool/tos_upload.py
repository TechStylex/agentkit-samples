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

"""
TOS 文件上传工具
提供文件上传到火山引擎 TOS 对象存储的功能，并返回带签名的访问 URL
直接使用 tos 库实现
"""

import os
from typing import Optional
from datetime import datetime
import tos
from tos import HttpMethodType
from pathlib import Path
import sys

# 当前目录
sys.path.append(str(Path(__file__).resolve().parent))

# 上层目录
sys.path.append(str(Path(__file__).resolve().parent.parent))

from auth import get_credential_from_vefaas_iam, VEFAAS_IAM_CRIDENTIAL_PATH

# 配置日志（可选）
# tos.set_logger(file_path='tos_upload.log', name='tos', level=tos.log.INFO)

def upload_file_to_tos(
    file_path: str,
    bucket_name: Optional[str] = None,
    object_key: Optional[str] = None,
    region: str = "cn-beijing",
    ak: Optional[str] = None,
    sk: Optional[str] = None,
    session_token: Optional[str] = None,
    expires: int = 604800,  # 7天有效期
) -> Optional[str]:
    f"""
    上传文件到 TOS 对象存储，并返回带签名的可访问 URL
    
    Args:
        file_path: 本地文件路径
        bucket_name: TOS bucket 名称，默认为 "aaa-bbb-ccc-ddd"
        object_key: 对象存储键名，如果为空则使用文件名
        region: TOS 区域，默认为 cn-beijing
        ak: 访问密钥 Access Key，如果为空则从环境变量读取
        sk: 密钥 Secret Key，如果为空则从环境变量读取
        expires: 签名 URL 有效期（秒），默认 7 天（604800 秒）
        
    Returns:
        str: 带签名的 TOS URL，可直接访问
        None: 上传失败时返回 None
        
    环境变量要求:
        VOLCENGINE_ACCESS_KEY: 火山引擎访问密钥
        VOLCENGINE_SECRET_KEY: 火山引擎密钥
        
    使用示例:
        >>> url = upload_file_to_tos("./video.mp4")
        >>> print(url)
        https://bucket.tos-cn-beijing.volces.com/video.mp4?X-Tos-Signature=...
    """
    bucket_name = os.getenv("DATABASE_TOS_BUCKET", "aaa-bbb-ccc-ddd")

    # 检查文件是否存在
    if not os.path.exists(file_path):
        print(f"错误: 文件不存在: {file_path}")
        return None
        
    if not os.path.isfile(file_path):
        print(f"错误: 路径不是文件: {file_path}")
        return None
    
    # Retrieve STS from IAM Role
    if os.path.exists(VEFAAS_IAM_CRIDENTIAL_PATH):
        credential = get_credential_from_vefaas_iam()
        ak = credential.access_key_id
        sk = credential.secret_access_key
        session_token = credential.session_token

    # 从环境变量获取密钥（如果没有显式提供）
    if not ak:
        ak = os.getenv("VOLCENGINE_ACCESS_KEY", "")
    if not sk:
        sk = os.getenv("VOLCENGINE_SECRET_KEY", "")

        
    if not ak or not sk:
        
        print("Error: VOLCENGINE_ACCESS_KEY and VOLCENGINE_SECRET_KEY is not provided or IAM Role is not configured.")
        return None
    
    # 自动生成 object_key（使用文件名）
    if not object_key:
        # 使用时间戳和原始文件名组合，避免覆盖
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = os.path.basename(file_path)
        object_key = f"upload/{timestamp}_{filename}"
    
    # 创建 TOS 客户端
    client = None
    try:
        # 初始化 TOS 客户端
        endpoint = f"tos-{region}.volces.com"
        client = tos.TosClientV2(
            ak=ak,
            sk=sk,
            security_token=session_token,
            endpoint=endpoint,
            region=region
        )
        
        print(f"开始上传文件: {file_path}")
        print(f"目标 Bucket: {bucket_name}")
        print(f"对象键名: {object_key}")
        
        # 确保 bucket 存在（如果不存在则创建）
        try:
            client.head_bucket(bucket_name)
            print(f"Bucket {bucket_name} 已存在")
        except tos.exceptions.TosServerError as e:
            if e.status_code == 404:
                print(f"Bucket {bucket_name} 不存在，正在创建...")
                # client.create_bucket(
                #     bucket=bucket_name,
                #     acl=tos.ACLType.ACL_Public_Read,
                #     storage_class=tos.StorageClassType.Storage_Class_Standard
                # )
                # print(f"Bucket {bucket_name} 创建成功")
            else:
                raise e
        
        # 上传文件
        result = client.put_object_from_file(
            bucket=bucket_name,
            key=object_key,
            file_path=file_path
        )
        
        print(f"文件上传成功!")
        print(f"ETag: {result.etag}")
        print(f"Request ID: {result.request_id}")
        
        # 生成带签名的 URL
        signed_url_output = client.pre_signed_url(
            http_method=HttpMethodType.Http_Method_Get,
            bucket=bucket_name,
            key=object_key,
            expires=expires
        )
        
        signed_url = signed_url_output.signed_url
        print(f"生成签名 URL 成功（有效期 {expires} 秒）")
        print(f"访问 URL: {signed_url}")
        
        return signed_url
        
    except tos.exceptions.TosClientError as e:
        print(f"TOS 客户端错误: {e}")
        return None
    except tos.exceptions.TosServerError as e:
        print(f"TOS 服务器错误: {e}")
        print(f"状态码: {e.status_code}")
        print(f"错误码: {e.code}")
        print(f"错误信息: {e.message}")
        return None
    except Exception as e:
        print(f"上传文件失败: {e}")
        import traceback
        traceback.print_exc()
        return None
    finally:
        # 关闭客户端
        if client:
            client.close()


# 示例用法
if __name__ == "__main__":
    print("=" * 60)
    print("TOS 文件上传测试")
    print("=" * 60)
    
    # 测试文件路径
    test_file = "./hujiahuwei_complete.mp4"
    
    if os.path.exists(test_file):
        print(f"\n找到测试文件: {test_file}")
        file_size = os.path.getsize(test_file) / (1024 * 1024)  # MB
        print(f"文件大小: {file_size:.2f} MB")
        
        print("\n" + "=" * 60)
        print("开始上传...")
        print("=" * 60)
        
        # 调用上传函数
        url = upload_file_to_tos(
            file_path=test_file,
            bucket_name="veadk-default",  # 可以修改为你的 bucket 名称
            # object_key="test_video.mp4",  # 可选：指定对象键名
            region="cn-beijing",  # 可以修改为你的区域
            expires=604800  # 7天有效期
        )
        
        print("\n" + "=" * 60)
        if url:
            print("✅ 上传成功！")
            print(f"📎 访问 URL: {url}")
            print("\n提示: URL 有效期为 7 天，可直接在浏览器中访问")
        else:
            print("❌ 上传失败")
            print("\n请检查:")
            print("1. 环境变量 VOLCENGINE_ACCESS_KEY 和 VOLCENGINE_SECRET_KEY 是否设置")
            print("2. 网络连接是否正常")
            print("3. 账号权限是否足够")
        print("=" * 60)
    else:
        print(f"\n❌ 测试文件不存在: {test_file}")
        print("\n请确保测试文件存在，或修改代码中的 test_file 变量指向一个有效的文件路径")
        print("\n使用方法:")
        print("  from tool.tos_upload import upload_file_to_tos")
        print('  url = upload_file_to_tos("your_file.mp4")')
        print('  print(url)')

