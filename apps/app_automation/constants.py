# -*- coding: utf-8 -*-
"""
APP自动化测试常量定义
"""


class DeviceStatus:
    """设备状态"""
    AVAILABLE = 'available'
    LOCKED = 'locked'
    OFFLINE = 'offline'
    ONLINE = 'online'


class ExecutionStatus:
    """执行状态"""
    PENDING = 'pending'
    RUNNING = 'running'
    SUCCESS = 'success'
    FAILED = 'failed'
    STOPPED = 'stopped'


class ElementType:
    """元素类型"""
    IMAGE = 'image'      # 图片元素
    POS = 'pos'          # 坐标元素
    REGION = 'region'    # 区域元素
