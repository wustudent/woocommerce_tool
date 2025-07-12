import streamlit as st
from woocommerce import API
from dotenv import load_dotenv
import os
import requests
from loguru import logger
import sys

from requests.auth import HTTPBasicAuth

# 初始化日志
logger.remove()
logger.add(sys.stdout, level="DEBUG")  # 控制台输出
logger.add("app.log", rotation="1 MB", level="DEBUG")  # 保存到文件

# 加载环境变量
load_dotenv()
WC_URL = os.getenv("WC_URL")
WC_CONSUMER_KEY = os.getenv("WC_CONSUMER_KEY")
WC_CONSUMER_SECRET = os.getenv("WC_CONSUMER_SECRET")
WP_USERNAME = os.getenv("WP_USERNAME")
WP_APPLICATION_PASSWORD = os.getenv("WP_APPLICATION_PASSWORD")

logger.debug(f"Loaded WC_URL: {WC_URL}")

if not all([WC_URL, WC_CONSUMER_KEY, WC_CONSUMER_SECRET, WP_USERNAME, WP_APPLICATION_PASSWORD]):
    st.error("❌ Missing WooCommerce credentials in .env")
    logger.error("Missing credentials in .env")
    st.stop()

# 初始化 WooCommerce API
logger.info("Initializing WooCommerce API")
wcapi = API(
    url=WC_URL,
    consumer_key=WC_CONSUMER_KEY,
    consumer_secret=WC_CONSUMER_SECRET,
    version="wc/v3"
)

st.title("🛍 添加产品到 WooCommerce")

debug_mode = st.sidebar.checkbox("🧪 开启调试信息")

with st.form("product_form"):
    name = st.text_input("产品名称")
    type_ = st.selectbox("产品类型", ["simple", "grouped", "external", "variable"])
    regular_price = st.text_input("原价", placeholder="例如：19.99")
    sale_price = st.text_input("促销价（可选）", "")
    description = st.text_area("产品描述", "")
    short_description = st.text_area("简要描述", "")
    sku = st.text_input("SKU（可选）", "")
    stock_quantity = st.number_input("库存数量", min_value=0, value=10)
    manage_stock = st.checkbox("是否管理库存？", value=True)
    in_stock = st.checkbox("是否有货？", value=True)
    image_file = st.file_uploader("上传产品图片", type=["jpg", "jpeg", "png"])

    submit = st.form_submit_button("提交")

def upload_image_to_wp(filename, filecontent):
    """
    使用 WordPress 应用密码通过 REST API 上传媒体文件
    """
    url = f"{WC_URL}/wp-json/wp/v2/media"
    headers = {
        'Content-Disposition': f'attachment; filename={filename}',
        # 这里简单判断图片类型，实际可根据文件后缀做更精准判断
        'Content-Type': 'image/jpeg' if filename.lower().endswith(('.jpg', '.jpeg')) else 'image/png'
    }

    if not WP_USERNAME or not WP_APPLICATION_PASSWORD:
        logger.error("WP_USERNAME 或 WP_APPLICATION_PASSWORD 未设置，无法上传图片")
        return None

    try:
        auth = HTTPBasicAuth(WP_USERNAME, WP_APPLICATION_PASSWORD)
        response = requests.post(url, headers=headers, data=filecontent, auth=auth)
        logger.debug(f"Image upload response status: {response.status_code}")
        logger.debug(f"Image upload response body: {response.text}")

        if response.status_code in (200, 201):
            json_resp = response.json()
            return json_resp.get('source_url')
        else:
            logger.error(f"图片上传失败，状态码: {response.status_code}")
            return None
    except Exception as e:
        logger.exception(f"上传图片异常: {e}")
        return None

def create_product(name, type_, regular_price, sale_price, description,
                   short_description, sku, stock_quantity, manage_stock,
                   in_stock, image_file=None):
    """
    创建 WooCommerce 产品
    """
    data = {
        "name": name,
        "type": type_,
        "regular_price": regular_price,
        "description": description,
        "short_description": short_description,
        "sku": sku,
        "manage_stock": manage_stock,
        "stock_quantity": stock_quantity,
        "in_stock": in_stock
    }

    # 去除为空字段
    data = {k: v for k, v in data.items() if v not in ("", None)}

    # 加促销价
    if sale_price:
        data["sale_price"] = sale_price

    # 上传图片
    if image_file:
        image_url = upload_image_to_wp(image_file.name, image_file.read())
        if image_url:
            data["images"] = [{"src": image_url}]
            logger.info(f"图片上传成功: {image_url}")
        else:
            logger.warning("⚠️ 图片上传失败，跳过图片设置")

    logger.debug(f"创建产品请求数据: {data}")

    try:
        response = wcapi.post("products", data)
        logger.debug(f"响应状态: {response.status_code}")
        logger.debug(f"响应内容: {response.text}")
        return response
    except Exception as e:
        logger.exception("创建产品请求异常")
        return None

if submit:
    if not name or not regular_price:
        st.error("❌ 产品名称和原价为必填项")
    else:
        response = create_product(
            name, type_, regular_price, sale_price, description,
            short_description, sku, stock_quantity, manage_stock,
            in_stock, image_file
        )

        if response is None:
            st.error("❌ 创建失败：请求异常")
        elif response.status_code in (200, 201):
            product = response.json()
            st.success(f"✅ 产品创建成功！ID: {product.get('id')}")
            st.json(product)
        else:
            st.error(f"❌ 创建产品失败: {response.status_code}")
            st.text(response.text)

    
