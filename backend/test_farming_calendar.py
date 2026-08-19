# -*- coding: utf-8 -*-
"""江西农事日历测试。"""
import pytest
from datetime import date
from farming_calendar import FarmingCalendar, build_weather_alert_context, ALL_CALENDARS, CROP_ALIASES


class TestFarmingCalendar:
    """FarmingCalendar 测试。"""

    def test_get_current_activities_rice(self):
        # 3月15日应该是早稻播种育秧期
        cal = FarmingCalendar(reference_date=date(2026, 3, 15))
        activities = cal.get_current_activities("早稻")
        assert len(activities) >= 1
        stages = [a["stage"] for a in activities]
        assert "播种育秧" in stages

    def test_get_current_activities_rapeseed(self):
        # 3月20日应该是油菜开花期
        cal = FarmingCalendar(reference_date=date(2026, 3, 20))
        activities = cal.get_current_activities("油菜")
        assert len(activities) >= 1
        stages = [a["stage"] for a in activities]
        assert "开花期" in stages

    def test_get_current_activities_citrus(self):
        # 4月10日应该是柑橘花期
        cal = FarmingCalendar(reference_date=date(2026, 4, 10))
        activities = cal.get_current_activities("柑橘")
        assert len(activities) >= 1
        stages = [a["stage"] for a in activities]
        assert "花期" in stages

    def test_get_current_activities_unknown_crop(self):
        cal = FarmingCalendar()
        activities = cal.get_current_activities("未知作物")
        assert activities == []

    def test_crop_aliases(self):
        cal = FarmingCalendar(reference_date=date(2026, 3, 15))
        # 别名应该能正常工作
        assert cal.get_current_activities("稻") == cal.get_current_activities("水稻")
        assert cal.get_current_activities("菜籽") == cal.get_current_activities("油菜")

    def test_get_upcoming_activities(self):
        cal = FarmingCalendar(reference_date=date(2026, 3, 1))
        # 未来30天应该有多个活动
        activities = cal.get_upcoming_activities("早稻", days=30)
        assert len(activities) >= 2

    def test_get_crop_calendar(self):
        cal = FarmingCalendar()
        result = cal.get_crop_calendar("早稻")
        assert result["ok"] is True
        assert result["crop"] == "早稻"
        assert result["region"] == "江西"
        assert len(result["stages"]) >= 5

    def test_get_crop_calendar_unknown(self):
        cal = FarmingCalendar()
        result = cal.get_crop_calendar("未知作物")
        assert result["ok"] is False

    def test_check_weather_risk_high_temperature(self):
        cal = FarmingCalendar(reference_date=date(2026, 6, 20))
        weather_data = {
            "daily": [
                {"date": "2026-06-20", "temperature_max_c": 38, "temperature_min_c": 28,
                 "precipitation_mm": 0, "weather_code": 0},
            ]
        }
        risks = cal.check_weather_risk("早稻", weather_data)
        # 6月20日应该是早稻孕穗期，高温风险
        temp_risks = [r for r in risks if r["risk_type"] == "high_temperature"]
        assert len(temp_risks) >= 1
        assert temp_risks[0]["severity"] == "critical"  # >= 37°C

    def test_check_weather_risk_frost(self):
        cal = FarmingCalendar(reference_date=date(2026, 3, 10))
        weather_data = {
            "daily": [
                {"date": "2026-03-10", "temperature_max_c": 12, "temperature_min_c": -1,
                 "precipitation_mm": 0, "weather_code": 0},
            ]
        }
        risks = cal.check_weather_risk("早稻", weather_data)
        frost_risks = [r for r in risks if r["risk_type"] == "frost"]
        assert len(frost_risks) >= 1
        assert frost_risks[0]["severity"] == "critical"

    def test_check_weather_risk_no_risk(self):
        cal = FarmingCalendar(reference_date=date(2026, 3, 15))
        weather_data = {
            "daily": [
                {"date": "2026-03-15", "temperature_max_c": 22, "temperature_min_c": 12,
                 "precipitation_mm": 0, "weather_code": 0},
            ]
        }
        risks = cal.check_weather_risk("早稻", weather_data)
        assert len(risks) == 0


class TestWeatherAlertContext:
    """天气预警上下文测试。"""

    def test_build_weather_alert_context(self):
        weather_data = {
            "daily": [
                {"date": "2026-03-15", "temperature_max_c": 22, "temperature_min_c": 12,
                 "precipitation_mm": 0, "weather_code": 0},
            ]
        }
        context = build_weather_alert_context("早稻", weather_data, date(2026, 3, 15))
        assert "天气与农事预警" in context
        assert "当前农事活动" in context

    def test_build_weather_alert_context_with_risk(self):
        weather_data = {
            "daily": [
                {"date": "2026-06-20", "temperature_max_c": 38, "temperature_min_c": 28,
                 "precipitation_mm": 0, "weather_code": 0},
            ]
        }
        context = build_weather_alert_context("早稻", weather_data, date(2026, 6, 20))
        assert "天气风险预警" in context
        assert "高温" in context

    def test_build_weather_alert_context_no_activities(self):
        weather_data = {"daily": []}
        context = build_weather_alert_context("未知作物", weather_data)
        assert context == ""


class TestCalendarData:
    """日历数据完整性测试。"""

    def test_all_calendars_have_required_fields(self):
        for crop, calendar in ALL_CALENDARS.items():
            for stage_name, data in calendar.items():
                assert len(data) == 6, f"{crop}/{stage_name} 字段数不正确"
                start_month, start_day, end_month, end_day, desc, key_ops = data
                assert 1 <= start_month <= 12, f"{crop}/{stage_name} 起始月份无效"
                assert 1 <= start_day <= 31, f"{crop}/{stage_name} 起始日期无效"
                assert 1 <= end_month <= 12, f"{crop}/{stage_name} 结束月份无效"
                assert 1 <= end_day <= 31, f"{crop}/{stage_name} 结束日期无效"
                assert desc, f"{crop}/{stage_name} 描述为空"
                assert key_ops, f"{crop}/{stage_name} 关键操作为空"

    def test_crop_aliases_coverage(self):
        # 关键作物别名应该能正常工作
        key_crops = ["早稻", "晚稻", "中稻", "油菜", "柑橘", "赣南脐橙"]
        for crop in key_crops:
            assert crop in ALL_CALENDARS, f"关键作物 '{crop}' 不在日历中"
        # 别名映射测试
        assert CROP_ALIASES.get("稻") == "水稻"
        assert CROP_ALIASES.get("菜籽") == "油菜"
        assert CROP_ALIASES.get("脐橙") == "赣南脐橙"
