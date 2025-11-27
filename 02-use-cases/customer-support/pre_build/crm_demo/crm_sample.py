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
CRM系统 - 客户关系管理系统
提供客户信息查询、商品信息查询、维修记录管理等功能
"""
import re
from datetime import datetime, date
from enum import Enum
from typing import List, Optional, Dict

import requests
from fastapi import FastAPI, HTTPException, Depends, Header
from pydantic import BaseModel, EmailStr, field_validator


# 数据模型定义
class Customer(BaseModel):
    """客户信息模型"""
    customer_id: str
    name: str
    email: EmailStr
    phone: str
    address: str
    registration_date: date
    date_of_birth: Optional[date] = None
    notes: Optional[str] = None
    total_purchases: int = 0
    lifetime_value: float = 0.0
    support_cases_count: int = 0
    communication_preferences: List[str] = []


class Product(BaseModel):
    """商品信息模型"""
    product_id: str
    serial_number: str
    product_name: str
    customer_id: str
    purchase_date: date
    warranty_end_date: date
    warranty_type: str
    status: str


class ServiceRecord(BaseModel):
    """维修记录模型"""
    record_id: str
    serial_number: str
    customer_id: str
    service_date: datetime
    service_type: str
    description: str
    technician: str
    status: str  # scheduled, completed, cancelled
    estimated_duration: int  # 分钟
    actual_duration: Optional[int] = None
    notes: Optional[str] = None


class ServiceStatus(str, Enum):
    """维修状态枚举"""
    SCHEDULED = "scheduled"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class WarrantyType(str, Enum):
    """保修类型枚举"""
    STANDARD = "standard"
    EXTENDED = "extended"
    PREMIUM = "premium"


# 请求和响应模型
class CustomerQuery(BaseModel):
    """客户查询请求"""
    customer_id: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None


class WarrantyQuery(BaseModel):
    """保修查询请求"""
    serial_number: str
    customer_email: Optional[EmailStr] = None

    @field_validator('serial_number')
    @classmethod
    def validate_serial_number(cls, v):
        if not re.match(r'^[A-Z0-9]{8,20}$', v):
            raise ValueError('Serial number must be 8-20 alphanumeric characters')
        return v


class ServiceRecordCreate(BaseModel):
    """创建维修记录请求"""
    serial_number: str
    service_type: str
    description: str
    technician: str
    service_date: datetime
    estimated_duration: int


class ServiceRecordUpdate(BaseModel):
    """更新维修记录请求"""
    service_date: Optional[datetime] = None
    status: Optional[ServiceStatus] = None
    actual_duration: Optional[int] = None
    notes: Optional[str] = None


class WarrantyResponse(BaseModel):
    """保修查询响应"""
    product_name: str
    serial_number: str
    customer_name: str
    purchase_date: date
    warranty_end_date: date
    warranty_type: str
    status_text: str


# 初始化数据
class CRMData:
    """CRM数据存储类"""

    def __init__(self):
        self.customers: Dict[str, Customer] = {}
        self.products: Dict[str, Product] = {}
        self.service_records: Dict[str, ServiceRecord] = {}
        self._initialize_sample_data()

    def _initialize_sample_data(self):
        """初始化示例数据"""
        # 客户数据
        customers_data = [
            {
                "customer_id": "CUST001",
                "name": "张明",
                "email": "zhang.ming@example.com",
                "phone": "+86-138-0011-2233",
                "address": "北京市朝阳区建国门外大街1号",
                "registration_date": date(2022, 3, 15),
                "date_of_birth": date(1985, 8, 20),
                "notes": "优质客户，经常购买高端产品",
                "total_purchases": 3,
                "lifetime_value": 28500.00,
                "support_cases_count": 2,
                "communication_preferences": ["email", "sms"]
            },
            {
                "customer_id": "CUST002",
                "name": "李华",
                "email": "li.hua@example.com",
                "phone": "+86-139-0022-3344",
                "address": "上海市浦东新区陆家嘴金融中心",
                "registration_date": date(2023, 1, 10),
                "date_of_birth": date(1990, 5, 15),
                "notes": "企业客户，批量采购",
                "total_purchases": 5,
                "lifetime_value": 42000.00,
                "support_cases_count": 1,
                "communication_preferences": ["email", "wechat"]
            },
            {
                "customer_id": "CUST003",
                "name": "王芳",
                "email": "wang.fang@example.com",
                "phone": "+86-137-0033-4455",
                "address": "广州市天河区珠江新城",
                "registration_date": date(2022, 11, 5),
                "date_of_birth": date(1988, 12, 3),
                "notes": "个人用户，偏好智能家居产品",
                "total_purchases": 2,
                "lifetime_value": 12800.00,
                "support_cases_count": 0,
                "communication_preferences": ["sms", "phone"]
            },
            {
                "customer_id": "CUST004",
                "name": "陈强",
                "email": "chen.qiang@example.com",
                "phone": "+86-136-0044-5566",
                "address": "深圳市南山区科技园",
                "registration_date": date(2023, 6, 20),
                "date_of_birth": date(1992, 7, 18),
                "notes": "科技爱好者，喜欢最新产品",
                "total_purchases": 4,
                "lifetime_value": 35600.00,
                "support_cases_count": 3,
                "communication_preferences": ["email", "app"]
            },
            {
                "customer_id": "CUST005",
                "name": "刘婷",
                "email": "liu.ting@example.com",
                "phone": "+86-135-0055-6677",
                "address": "杭州市西湖区文三路",
                "registration_date": date(2022, 8, 12),
                "date_of_birth": date(1987, 3, 25),
                "notes": "电商客户，经常在线购物",
                "total_purchases": 3,
                "lifetime_value": 19200.00,
                "support_cases_count": 1,
                "communication_preferences": ["email", "sms", "wechat"]
            }
        ]

        # 商品数据
        products_data = [
            # 张明的商品
            {
                "product_id": "PROD001",
                "serial_number": "SN20240001",
                "product_name": "智能电视 65寸",
                "customer_id": "CUST001",
                "purchase_date": date(2023, 12, 10),
                "warranty_end_date": date(2025, 12, 10),
                "warranty_type": "standard",
                "status": "active"
            },
            {
                "product_id": "PROD002",
                "serial_number": "SN20240002",
                "product_name": "智能音箱 Pro",
                "customer_id": "CUST001",
                "purchase_date": date(2023, 8, 15),
                "warranty_end_date": date(2024, 8, 15),
                "warranty_type": "extended",
                "status": "active"
            },
            # 李华的商品
            {
                "product_id": "PROD003",
                "serial_number": "SN20240003",
                "product_name": "笔记本电脑 X1",
                "customer_id": "CUST002",
                "purchase_date": date(2024, 1, 20),
                "warranty_end_date": date(2025, 1, 20),
                "warranty_type": "premium",
                "status": "active"
            },
            {
                "product_id": "PROD004",
                "serial_number": "SN20240004",
                "product_name": "平板电脑 T8",
                "customer_id": "CUST002",
                "purchase_date": date(2023, 11, 5),
                "warranty_end_date": date(2024, 11, 5),
                "warranty_type": "standard",
                "status": "active"
            },
            # 王芳的商品
            {
                "product_id": "PROD005",
                "serial_number": "SN20240005",
                "product_name": "智能手表 S3",
                "customer_id": "CUST003",
                "purchase_date": date(2023, 9, 18),
                "warranty_end_date": date(2024, 9, 18),
                "warranty_type": "standard",
                "status": "active"
            },
            {
                "product_id": "PROD006",
                "serial_number": "SN20240006",
                "product_name": "无线耳机 E2",
                "customer_id": "CUST003",
                "purchase_date": date(2023, 6, 22),
                "warranty_end_date": date(2024, 6, 22),
                "warranty_type": "standard",
                "status": "expired"
            },
            # 陈强的商品
            {
                "product_id": "PROD007",
                "serial_number": "SN20240007",
                "product_name": "游戏主机 G5",
                "customer_id": "CUST004",
                "purchase_date": date(2024, 2, 14),
                "warranty_end_date": date(2025, 2, 14),
                "warranty_type": "extended",
                "status": "active"
            },
            {
                "product_id": "PROD008",
                "serial_number": "SN20240008",
                "product_name": "VR头盔 V2",
                "customer_id": "CUST004",
                "purchase_date": date(2023, 10, 30),
                "warranty_end_date": date(2024, 10, 30),
                "warranty_type": "standard",
                "status": "active"
            },
            # 刘婷的商品
            {
                "product_id": "PROD009",
                "serial_number": "SN20240009",
                "product_name": "数码相机 C9",
                "customer_id": "CUST005",
                "purchase_date": date(2023, 7, 8),
                "warranty_end_date": date(2024, 7, 8),
                "warranty_type": "standard",
                "status": "active"
            },
            {
                "product_id": "PROD010",
                "serial_number": "SN20240010",
                "product_name": "打印机 P3",
                "customer_id": "CUST005",
                "purchase_date": date(2023, 4, 12),
                "warranty_end_date": date(2024, 4, 12),
                "warranty_type": "extended",
                "status": "active"
            }
        ]

        # 维修记录数据
        service_records_data = [
            {
                "record_id": "SRV001",
                "serial_number": "SN20240001",
                "customer_id": "CUST001",
                "service_date": datetime(2024, 1, 15, 10, 0),
                "service_type": "屏幕维修",
                "description": "屏幕出现竖线",
                "technician": "王师傅",
                "status": "completed",
                "estimated_duration": 120,
                "actual_duration": 110,
                "notes": "更换屏幕面板，测试正常"
            },
            {
                "record_id": "SRV002",
                "serial_number": "SN20240003",
                "customer_id": "CUST002",
                "service_date": datetime(2024, 3, 20, 14, 30),
                "service_type": "系统升级",
                "description": "操作系统升级服务",
                "technician": "李工程师",
                "status": "scheduled",
                "estimated_duration": 60,
                "actual_duration": None,
                "notes": None
            }
        ]

        # 初始化客户数据
        for customer_data in customers_data:
            self.customers[customer_data["customer_id"]] = Customer(**customer_data)

        # 初始化商品数据
        for product_data in products_data:
            self.products[product_data["serial_number"]] = Product(**product_data)

        # 初始化维修记录数据
        for record_data in service_records_data:
            self.service_records[record_data["record_id"]] = ServiceRecord(**record_data)


# 全局数据存储
crm_data = CRMData()

# 创建FastAPI应用
app = FastAPI()


# 通过Oauth2认证获取当前用户信息
async def get_current_user(authorization: str = Header(...)) -> dict:
    github_user_url = "https://api.github.com/user"
    lark_user_url = "https://fsopen.bytedance.net/open-apis/authen/v1/user_info"
    
    user_response = requests.get(
        lark_user_url,
        headers={"Authorization": f"Bearer {authorization}"}
    )
    if user_response.status_code != 200:
        raise HTTPException(status_code=400, detail="认证失败")
    return user_response.json()


# 根据客户ID查询客户信息
@app.get("/customers/{customer_id}", response_model=Customer, tags=["客户管理"])
async def get_customer_by_id(
        customer_id: str,
        user: dict = Depends(get_current_user)
):
    """根据客户ID查询客户信息"""
    customer = crm_data.customers.get(customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    return customer

# 根据客户ID查询客户的历史购买记录
@app.get("/customers/{customer_id}/purchases", response_model=list[Product], tags=["客户管理"])
async def get_customer_purchases(
        customer_id: str,
        user: dict = Depends(get_current_user)
):
    """根据客户ID查询客户的历史购买记录"""
    purchases = [product for product in crm_data.products.values() if product.customer_id == customer_id]
    if not purchases:
        raise HTTPException(status_code=404, detail="No purchases found for this customer")
    return purchases



@app.post("/warranty/query", response_model=WarrantyResponse, tags=["保修查询"])
async def query_warranty(
        query: WarrantyQuery,
        user: dict = Depends(get_current_user)
):
    """查询商品保修信息"""
    # 查找商品
    product = crm_data.products.get(query.serial_number)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    # 验证客户邮箱（如果提供）
    if query.customer_email:
        customer = crm_data.customers.get(product.customer_id)
        if not customer or customer.email != query.customer_email:
            raise HTTPException(status_code=403, detail="Customer email verification failed")

    # 获取客户信息
    customer = crm_data.customers.get(product.customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")

    # 确定状态文本
    current_date = date.today()
    if product.warranty_end_date < current_date:
        status_text = "保修已过期"
    elif (product.warranty_end_date - current_date).days <= 30:
        status_text = "保修即将到期"
    else:
        status_text = "保修有效"

    return WarrantyResponse(
        product_name=product.product_name,
        serial_number=product.serial_number,
        customer_name=customer.name,
        purchase_date=product.purchase_date,
        warranty_end_date=product.warranty_end_date,
        warranty_type=product.warranty_type,
        status_text=status_text
    )


@app.post("/service/records", response_model=ServiceRecord, tags=["维修管理"])
async def create_service_record(
        record: ServiceRecordCreate,
        user: dict = Depends(get_current_user)
):
    """创建维修记录"""
    # 验证商品是否存在
    product = crm_data.products.get(record.serial_number)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    # 生成记录ID
    record_id = f"SRV{len(crm_data.service_records) + 1:03d}"

    # 创建维修记录
    service_record = ServiceRecord(
        record_id=record_id,
        serial_number=record.serial_number,
        customer_id=product.customer_id,
        service_date=record.service_date,
        service_type=record.service_type,
        description=record.description,
        technician=record.technician,
        status="scheduled",
        estimated_duration=record.estimated_duration
    )

    crm_data.service_records[record_id] = service_record
    return service_record


@app.get("/service/records", response_model=List[ServiceRecord], tags=["维修管理"])
async def get_service_records(
        serial_number: Optional[str] = None,
        customer_id: Optional[str] = None,
        status: Optional[ServiceStatus] = None,
        user: dict = Depends(get_current_user)
):
    """查询维修记录"""
    records = list(crm_data.service_records.values())

    # 应用过滤条件
    filtered_records = []
    for record in records:
        if serial_number and record.serial_number != serial_number:
            continue
        if customer_id and record.customer_id != customer_id:
            continue
        if status and record.status != status:
            continue
        filtered_records.append(record)

    return filtered_records


@app.put("/service/records/{record_id}", response_model=ServiceRecord, tags=["维修管理"])
async def update_service_record(
        record_id: str,
        update: ServiceRecordUpdate,
        user: dict = Depends(get_current_user)
):
    """更新维修记录（支持取消、修改上门维修时间）"""
    record = crm_data.service_records.get(record_id)
    if not record:
        raise HTTPException(status_code=404, detail="Service record not found")

    # 更新字段
    if update.service_date is not None:
        record.service_date = update.service_date
    if update.status is not None:
        record.status = update.status
    if update.actual_duration is not None:
        record.actual_duration = update.actual_duration
    if update.notes is not None:
        record.notes = update.notes

    return record


@app.get('/v1/ping')
async def ping_handler():
    return 'Ping healthcheck'


if __name__ == '__main__':
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8080)
