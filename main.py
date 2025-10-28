#!/usr/bin/env python3
"""
macOS 状态栏金价监控应用
使用 rumps 库实现状态栏显示和交互功能
"""

import rumps
import threading
import time
import queue
from typing import Dict, Any

from service import get_gold_price_service
from config import get_app_config, get_error_handler


class GoldPriceStatusBarApp(rumps.App):
    """金价状态栏应用"""

    def __init__(self):
        super(GoldPriceStatusBarApp, self).__init__(
            "💰",  # 默认图标
            title="金价监控",
            quit_button="退出",
        )

        # 初始化配置和服务
        self.config = get_app_config()
        self.error_handler = get_error_handler()
        self.gold_service = get_gold_price_service()

        self.current_price_info = None
        self.last_price = None  # 用于价格变化检测
        self.update_interval = self.config.get("update_interval")
        self.is_running = True

        # 刷新状态和看门狗
        self.refreshing = False
        self.refresh_watchdog = None

        # 主线程 UI 任务队列与定时处理
        self.ui_queue = queue.Queue()
        self.ui_timer = rumps.Timer(self._drain_ui_queue, 0.05)
        self.ui_timer.start()

        # 创建菜单项
        self.setup_menu()

        # 启动后台更新线程
        self.start_background_update()

        # 立即获取一次金价
        self.update_gold_price()

    def setup_menu(self):
        """设置菜单项"""
        # 金价详情菜单项
        self.price_detail_item = rumps.MenuItem("获取金价中...")
        self.menu.add(self.price_detail_item)

        # 分隔线
        self.menu.add(rumps.separator)

        # 刷新按钮
        refresh_item = rumps.MenuItem("立即刷新", callback=self.refresh_price)
        self.menu.add(refresh_item)

        # 设置菜单
        settings_item = rumps.MenuItem("设置")

        # 更新间隔子菜单
        interval_menu = rumps.MenuItem("更新间隔")
        intervals = self.config.get_update_intervals()
        for label, seconds in intervals.items():
            interval_menu.add(
                rumps.MenuItem(
                    label, callback=lambda _, s=seconds: self.set_update_interval(s)
                )
            )

        settings_item.add(interval_menu)
        self.menu.add(settings_item)

        # 分隔线
        self.menu.add(rumps.separator)

        # 错误状态菜单项
        self.error_status_item = rumps.MenuItem("服务状态: 正常")
        self.menu.add(self.error_status_item)

        # 分隔线
        self.menu.add(rumps.separator)

        # 关于菜单
        about_item = rumps.MenuItem("关于", callback=self.show_about)
        self.menu.add(about_item)

    def update_gold_price(self):
        """更新金价信息（后台线程获取，主线程更新UI）"""
        import threading

        def _fetch():
            try:
                print("[DEBUG] 开始获取金价...")
                price_info = self.gold_service.get_latest_gold_price()
                if price_info:

                    def _apply():
                        try:
                            print("[DEBUG] 获取金价成功，更新UI")
                            # 检查价格变化
                            self.check_price_change(price_info)
                            self.current_price_info = price_info
                            # 更新状态栏标题
                            display_text = self.gold_service.format_price_display(
                                price_info
                            )
                            self.title = display_text
                            # 更新详情菜单项
                            detail_text = self.gold_service.get_detailed_info(
                                price_info
                            )
                            self.price_detail_item.title = detail_text.replace(
                                "\n", " | "
                            )
                            # 重置错误计数
                            self.error_handler.reset_error_count()
                            self.update_error_status()
                            # 完成刷新，清理看门狗
                            self.refreshing = False
                            watchdog = getattr(self, "refresh_watchdog", None)
                            if watchdog is not None:
                                try:
                                    watchdog.stop()
                                except Exception:
                                    pass
                                self.refresh_watchdog = None
                        except Exception as e:
                            self.handle_update_error(e)

                    # 将 UI 更新调度到主线程队列中
                    self.schedule_on_main(_apply)
                else:
                    print("[DEBUG] 金价数据为空，触发错误处理")
                    self.schedule_on_main(
                        lambda: self.handle_update_error(Exception("获取金价数据失败"))
                    )
            except Exception as e:
                print(f"[DEBUG] 获取金价异常: {e}")
                self.schedule_on_main(lambda e=e: self.handle_update_error(e))

        threading.Thread(target=_fetch, daemon=True).start()

    def update_detail_with_cached(self):
        """在错误时使用缓存数据更新详情显示"""
        try:
            cached = self.gold_service.get_cached_price()
            if cached:
                detail_text = self.gold_service.get_detailed_info(cached)
                self.price_detail_item.title = "使用缓存 | " + detail_text.replace(
                    "\n", " | "
                )
        except Exception:
            pass

    def schedule_on_main(self, fn):
        """将函数调度到主线程 UI 队列执行"""
        try:
            self.ui_queue.put(fn)
        except Exception:
            pass

    def _drain_ui_queue(self, timer):
        """主线程定时处理 UI 队列中的任务"""
        try:
            while not self.ui_queue.empty():
                fn = self.ui_queue.get_nowait()
                try:
                    fn()
                except Exception as e:
                    self.handle_update_error(e)
        except Exception:
            # 避免 UI 队列处理异常影响主循环
            pass

    def check_price_change(self, new_price_info: Dict[str, Any]):
        """检查价格变化并发送通知"""
        if not self.config.get("show_price_change_alerts") or not self.last_price:
            self.last_price = new_price_info.get("price")
            return

        try:
            current_price = float(new_price_info.get("price", 0))
            last_price = float(self.last_price or 0)

            if last_price > 0:
                change_percent = abs((current_price - last_price) / last_price * 100)
                threshold = self.config.get("price_change_threshold")

                if change_percent >= threshold:
                    trend = "上涨" if current_price > last_price else "下跌"
                    change_amount = abs(current_price - last_price)

                    if self.config.get("show_notifications"):
                        rumps.notification(
                            title="金价变化提醒",
                            subtitle=f"价格{trend} {change_percent:.2f}%",
                            message=f"当前价格: ¥{current_price:.2f} (变化: ¥{change_amount:.2f})",
                        )

            self.last_price = current_price

        except (ValueError, TypeError) as e:
            print(f"价格变化检查失败: {e}")

    def handle_update_error(self, error: Exception):
        """处理更新错误"""
        # 结束刷新状态并清理看门狗
        self.refreshing = False
        watchdog = getattr(self, "refresh_watchdog", None)
        if watchdog is not None:
            try:
                watchdog.stop()
            except Exception:
                pass
            self.refresh_watchdog = None

        should_retry = self.error_handler.handle_error(error, "金价更新")

        if should_retry:
            if self.error_handler.is_service_healthy():
                self.title = "⚠️ 获取中..."
                self.price_detail_item.title = "正在重试获取金价..."
            else:
                self.title = "❌ 连接失败"
                self.price_detail_item.title = "金价服务连接失败，请检查网络"
        else:
            self.title = "❌ 服务异常"
            self.price_detail_item.title = "服务异常，已停止自动更新"

        # 尝试展示缓存详情，给用户参考
        self.update_detail_with_cached()

        self.update_error_status()

    def update_error_status(self):
        """更新错误状态显示"""
        if self.error_handler.is_service_healthy():
            self.error_status_item.title = "服务状态: 正常"
        else:
            error_count = self.error_handler.error_count
            self.error_status_item.title = f"服务状态: 异常 (错误: {error_count})"

    def start_background_update(self):
        """启动后台更新线程"""

        def update_loop():
            while self.is_running:
                try:
                    # 使用配置的更新间隔
                    time.sleep(self.update_interval)
                    if (
                        self.is_running
                        and self.error_handler.is_service_healthy()
                        and not self.refreshing
                    ):
                        self.update_gold_price()
                    elif not self.error_handler.is_service_healthy():
                        # 服务不健康时使用更长的重试间隔
                        retry_delay = self.error_handler.get_retry_delay()
                        print(f"服务不健康，等待 {retry_delay} 秒后重试")
                        time.sleep(
                            max(retry_delay - self.update_interval, 0)
                        )  # 补充等待时间
                        if self.is_running and not self.refreshing:
                            self.update_gold_price()
                except Exception as e:
                    self.error_handler.handle_error(e, "后台更新线程")
                    time.sleep(5)  # 线程错误时等待5秒再重试

        update_thread = threading.Thread(target=update_loop, daemon=True)
        update_thread.start()

    @rumps.clicked("立即刷新")
    def refresh_price(self, sender):
        """手动刷新金价（在主线程调度，避免子线程更新UI导致闪退）"""
        self.title = "🔄 刷新中..."
        self.price_detail_item.title = "正在获取最新金价..."
        self.refreshing = True

        # 使用 rumps.Timer 在主线程事件循环中调度一次更新
        def run_update(timer):
            try:
                timer.stop()
                self.update_gold_price()
            except Exception as e:
                self.handle_update_error(e)

        rumps.Timer(run_update, 0.05).start()

        # 启动看门狗：超过网络超时时间仍未完成，则提示超时错误
        def watchdog(timer):
            try:
                timer.stop()
                if self.refreshing:
                    from builtins import TimeoutError

                    self.handle_update_error(TimeoutError("刷新超时"))
            except Exception as e:
                self.handle_update_error(e)

        timeout_seconds = int(self.config.get("network_timeout") or 10)
        self.refresh_watchdog = rumps.Timer(watchdog, timeout_seconds)
        self.refresh_watchdog.start()

    def set_update_interval(self, interval: int):
        """设置更新间隔"""
        # 验证间隔值
        validated_interval = self.config.validate_update_interval(interval)
        self.update_interval = validated_interval
        self.config.set("update_interval", validated_interval)

        print(f"更新间隔已设置为 {validated_interval} 秒")

        # 显示通知
        if self.config.get("show_notifications"):
            rumps.notification(
                title="设置已更新",
                subtitle=f"更新间隔: {validated_interval}秒",
                message="新的更新间隔将在下次更新时生效",
            )

    @rumps.clicked("关于")
    def show_about(self, sender):
        """显示关于信息"""
        # 获取错误摘要
        error_summary = self.error_handler.get_error_summary()
        service_status = "正常" if self.error_handler.is_service_healthy() else "异常"

        about_text = f"""金价监控 v1.0

实时监控黄金价格变化
数据来源：京东金融

功能特性：
• 实时金价显示
• 涨跌趋势指示  
• 自定义更新间隔
• 详细价格信息
• 价格变化提醒
• 智能错误处理

当前状态：
• 服务状态: {service_status}
• 更新间隔: {self.update_interval}秒
• 通知功能: {"开启" if self.config.get("show_notifications") else "关闭"}

错误统计：
{error_summary}

开发：MicLon"""

        rumps.alert(title="关于金价监控", message=about_text, ok="确定")

    def clean_up(self):
        """清理资源"""
        self.is_running = False
        print("应用正在退出...")


def main():
    """主函数"""
    try:
        # 创建并运行应用
        app = GoldPriceStatusBarApp()

        print("金价状态栏应用启动成功")
        print("按 Ctrl+C 退出应用")

        # 运行应用
        app.run()

    except KeyboardInterrupt:
        print("\n应用被用户中断")
    except Exception as e:
        print(f"应用运行错误: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
