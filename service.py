"""
金价获取服务模块
集成现有的金价数据源，为状态栏应用提供数据支持
"""

from typing import Optional, Dict, Any
from datetime import datetime

from client import client
from config import get_app_config


class GoldPriceService:
    """金价服务类"""

    def __init__(self):
        self.last_price = None
        self.last_update_time = None
        self.error_count = 0
        self.max_error_count = 3
        # 读取网络超时/重试配置并应用到 JD 客户端
        try:
            config = get_app_config()
            client.api_client.timeout = int(config.get("network_timeout") or 10)
        except Exception:
            pass

    def _format_price_to_decimal(self, price_str: str) -> str:
        """
        将价格字符串格式化为2位小数

        Args:
            price_str: 价格字符串

        Returns:
            str: 格式化后的价格字符串，保持2位小数
        """
        try:
            price_float = float(price_str)
            return f"{price_float:.2f}"
        except (ValueError, TypeError):
            return "0.00"

    def get_latest_gold_price(self) -> Optional[Dict[str, Any]]:
        """
        获取最新金价信息

        Returns:
            Dict: 包含金价信息的字典，失败时返回 None
        """
        try:
            # 调用现有的金价获取接口
            gold_data = client.get_latest_gold_price()

            if gold_data:
                price_info = {
                    "price": str(gold_data.price),
                    "yesterday_price": str(gold_data.yesterdayPrice),
                    "up_and_down_rate": str(gold_data.upAndDownRate),
                    "up_and_down_amt": str(gold_data.upAndDownAmt),
                    "time": str(gold_data.time),
                    "product_sku": str(gold_data.productSku),
                    "update_time": datetime.now().strftime("%H:%M:%S"),
                }

                # 更新缓存
                self.last_price = price_info
                self.last_update_time = datetime.now()
                self.error_count = 0  # 重置错误计数

                return price_info
            else:
                self.error_count += 1
                return None

        except Exception as e:
            print(f"获取金价失败: {e}")
            self.error_count += 1
            return None

    def get_cached_price(self) -> Optional[Dict[str, Any]]:
        """
        获取缓存的金价信息

        Returns:
            Dict: 缓存的金价信息，如果没有缓存则返回 None
        """
        return self.last_price

    def is_service_healthy(self) -> bool:
        """
        检查服务是否健康

        Returns:
            bool: 服务是否健康
        """
        return self.error_count < self.max_error_count

    def format_price_display(self, price_info: Dict[str, Any]) -> str:
        """
        格式化金价显示文本

        Args:
            price_info: 金价信息字典

        Returns:
            str: 格式化后的显示文本
        """
        if not price_info:
            return "金价获取失败"

        try:
            price = price_info.get("price", "0")
            rate = price_info.get("up_and_down_rate", "0%")
            price_info.get("up_and_down_amt", "0")

            # 确保金价保持2位小数
            formatted_price = self._format_price_to_decimal(price)

            # 判断涨跌
            if rate.startswith("+") or (
                rate.replace("%", "").replace(".", "").replace("-", "").isdigit()
                and float(rate.replace("%", "")) > 0
            ):
                trend_icon = "📈"
            elif rate.startswith("-") or (
                rate.replace("%", "").replace(".", "").replace("-", "").isdigit()
                and float(rate.replace("%", "")) < 0
            ):
                trend_icon = "📉"
            else:
                trend_icon = "➖"

            return f"{trend_icon} {formatted_price}"

        except Exception as e:
            print(f"格式化金价显示失败: {e}")
            return "金价格式错误"

    def get_detailed_info(self, price_info: Dict[str, Any]) -> str:
        """
        获取详细的金价信息

        Args:
            price_info: 金价信息字典

        Returns:
            str: 详细信息文本
        """
        if not price_info:
            return "暂无金价数据"

        try:
            price = price_info.get("price", "0")
            yesterday_price = price_info.get("yesterday_price", "0")
            rate = price_info.get("up_and_down_rate", "0%")
            amt = price_info.get("up_and_down_amt", "0")
            update_time = price_info.get("update_time", "")

            # 确保所有金价相关数值保持2位小数
            formatted_price = self._format_price_to_decimal(price)
            formatted_yesterday_price = self._format_price_to_decimal(yesterday_price)
            formatted_amt = self._format_price_to_decimal(amt)

            detail_text = f"""当前金价: ¥{formatted_price}
昨日收盘: ¥{formatted_yesterday_price}
涨跌幅: {rate}
涨跌额: ¥{formatted_amt}
更新时间: {update_time}"""

            return detail_text

        except Exception as e:
            print(f"获取详细信息失败: {e}")
            return "详细信息获取失败"

    def reset_error_count(self):
        """重置错误计数"""
        self.error_count = 0


# 创建全局服务实例
gold_price_service = GoldPriceService()


def get_gold_price_service() -> GoldPriceService:
    """
    获取金价服务实例

    Returns:
        GoldPriceService: 金价服务实例
    """
    return gold_price_service


if __name__ == "__main__":
    # 测试代码
    service = get_gold_price_service()
    price_info = service.get_latest_gold_price()

    if price_info:
        print("金价获取成功:")
        print(service.format_price_display(price_info))
        print("\n详细信息:")
        print(service.get_detailed_info(price_info))
    else:
        print("金价获取失败")
