"""
状态栏应用配置文件
管理应用的各种设置和错误处理配置
"""

import os
from typing import Dict, Any


class AppConfig:
    """应用配置类"""

    # 默认配置
    DEFAULT_CONFIG = {
        # 更新设置
        "update_interval": 1,  # 默认1秒更新一次
        "min_update_interval": 1,  # 最小更新间隔
        "max_update_interval": 600,  # 最大更新间隔（10分钟）
        # 错误处理设置
        "max_error_count": 3,  # 最大连续错误次数
        "error_retry_delay": 5,  # 错误重试延迟（秒）
        "network_timeout": 10,  # 网络请求超时时间
        # 显示设置
        "show_notifications": True,  # 是否显示通知
        "show_price_change_alerts": True,  # 是否显示价格变化提醒
        "price_change_threshold": 0.5,  # 价格变化提醒阈值（百分比）
        # 界面设置
        "menu_max_items": 10,  # 菜单最大项目数
        "title_max_length": 20,  # 标题最大长度
        # 日志设置
        "enable_logging": True,  # 是否启用日志
        "log_level": "INFO",  # 日志级别
        "log_file_path": None,  # 日志文件路径（None表示不写文件）
    }

    def __init__(self):
        self.config = self.DEFAULT_CONFIG.copy()
        self.load_config()

    def load_config(self):
        """加载配置（可以从文件或环境变量加载）"""
        # 从环境变量加载配置
        env_mappings = {
            "GOLD_UPDATE_INTERVAL": "update_interval",
            "GOLD_MAX_ERRORS": "max_error_count",
            "GOLD_RETRY_DELAY": "error_retry_delay",
            "GOLD_TIMEOUT": "network_timeout",
            "GOLD_NOTIFICATIONS": "show_notifications",
            "GOLD_PRICE_ALERTS": "show_price_change_alerts",
            "GOLD_ALERT_THRESHOLD": "price_change_threshold",
            "GOLD_LOG_LEVEL": "log_level",
        }

        for env_key, config_key in env_mappings.items():
            env_value = os.getenv(env_key)
            if env_value is not None:
                # 类型转换
                if config_key in [
                    "update_interval",
                    "max_error_count",
                    "error_retry_delay",
                    "network_timeout",
                    "menu_max_items",
                    "title_max_length",
                ]:
                    try:
                        self.config[config_key] = int(env_value)
                    except ValueError:
                        pass
                elif config_key in ["price_change_threshold"]:
                    try:
                        self.config[config_key] = float(env_value)
                    except ValueError:
                        pass
                elif config_key in [
                    "show_notifications",
                    "show_price_change_alerts",
                    "enable_logging",
                ]:
                    self.config[config_key] = env_value.lower() in (
                        "true",
                        "1",
                        "yes",
                        "on",
                    )
                else:
                    self.config[config_key] = env_value

    def get(self, key: str, default=None) -> Any:
        """获取配置值"""
        return self.config.get(key, default)

    def set(self, key: str, value: Any):
        """设置配置值"""
        self.config[key] = value

    def get_update_intervals(self) -> Dict[str, int]:
        """获取可选的更新间隔"""
        return {
            "1秒": 1,
            "10秒": 10,
            "15秒": 15,
            "30秒": 30,
            "1分钟": 60,
            "2分钟": 120,
            "5分钟": 300,
            "10分钟": 600,
        }

    def validate_update_interval(self, interval: int) -> int:
        """验证并调整更新间隔"""
        min_interval = self.get("min_update_interval")
        max_interval = self.get("max_update_interval")

        if interval < min_interval:
            return min_interval
        elif interval > max_interval:
            return max_interval
        else:
            return interval


class ErrorHandler:
    """错误处理类"""

    def __init__(self, config: AppConfig):
        self.config = config
        self.error_count = 0
        self.last_error_time = None
        self.error_history = []

    def handle_error(self, error: Exception, context: str = "") -> bool:
        """
        处理错误

        Args:
            error: 异常对象
            context: 错误上下文

        Returns:
            bool: 是否应该继续重试
        """
        import time
        from datetime import datetime

        self.error_count += 1
        self.last_error_time = time.time()

        # 记录错误历史
        error_record = {
            "time": datetime.now(),
            "error": str(error),
            "context": context,
            "count": self.error_count,
        }
        self.error_history.append(error_record)

        # 保持错误历史记录不超过100条
        if len(self.error_history) > 100:
            self.error_history = self.error_history[-100:]

        # 打印错误信息
        if self.config.get("enable_logging"):
            print(f"[ERROR] {context}: {error} (错误次数: {self.error_count})")

        # 判断是否超过最大错误次数
        max_errors = self.config.get("max_error_count")
        return self.error_count < max_errors

    def reset_error_count(self):
        """重置错误计数"""
        self.error_count = 0
        self.last_error_time = None

    def get_retry_delay(self) -> int:
        """获取重试延迟时间"""
        base_delay = self.config.get("error_retry_delay")
        # 根据错误次数增加延迟时间
        return min(base_delay * (2 ** min(self.error_count - 1, 3)), 60)

    def is_service_healthy(self) -> bool:
        """检查服务是否健康"""
        max_errors = self.config.get("max_error_count")
        return self.error_count < max_errors

    def get_error_summary(self) -> str:
        """获取错误摘要"""
        if not self.error_history:
            return "无错误记录"

        recent_errors = self.error_history[-5:]  # 最近5个错误
        summary = f"总错误次数: {len(self.error_history)}\n"
        summary += f"当前连续错误: {self.error_count}\n\n"
        summary += "最近错误:\n"

        for i, error_record in enumerate(recent_errors, 1):
            time_str = error_record["time"].strftime("%H:%M:%S")
            summary += f"{i}. [{time_str}] {error_record['context']}: {error_record['error']}\n"

        return summary


# 创建全局配置实例
app_config = AppConfig()
error_handler = ErrorHandler(app_config)


def get_app_config() -> AppConfig:
    """获取应用配置实例"""
    return app_config


def get_error_handler() -> ErrorHandler:
    """获取错误处理实例"""
    return error_handler
