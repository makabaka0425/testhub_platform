"""
Core 应用视图
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters

from .models import UnifiedNotificationConfig
from .serializers import UnifiedNotificationConfigSerializer

import logging
logger = logging.getLogger(__name__)


class UnifiedNotificationConfigViewSet(viewsets.ModelViewSet):
    """统一通知配置视图集"""
    queryset = UnifiedNotificationConfig.objects.all()
    serializer_class = UnifiedNotificationConfigSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['config_type', 'is_default', 'is_active']
    search_fields = ['name']
    ordering_fields = ['created_at']
    ordering = ['-created_at']

    def perform_create(self, serializer):
        """创建通知配置"""
        instance = serializer.save(created_by=self.request.user)
        logger.info(f"创建统一通知配置: {instance.name}")

    def perform_update(self, serializer):
        """更新通知配置"""
        instance = serializer.save()
        logger.info(f"更新统一通知配置: {instance.name}")

    def perform_destroy(self, instance):
        """删除通知配置"""
        logger.info(f"删除统一通知配置: {instance.name}")
        instance.delete()

    @action(detail=True, methods=['post'])
    def set_default(self, request, pk=None):
        """设置为默认配置"""
        config = self.get_object()
        # 取消其他默认配置
        UnifiedNotificationConfig.objects.filter(is_default=True).update(is_default=False)
        # 设置当前为默认
        config.is_default = True
        config.save()
        return Response({'message': '已设置为默认配置'})

    @action(detail=False, methods=['get'])
    def active_configs(self, request):
        """获取所有启用的配置"""
        configs = UnifiedNotificationConfig.objects.filter(is_active=True)
        serializer = self.get_serializer(configs, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def test_email(self, request, pk=None):
        """测试邮箱配置是否可用"""
        config = self.get_object()
        if config.config_type != 'email':
            return Response({'error': '该配置不是邮箱类型'}, status=status.HTTP_400_BAD_REQUEST)

        if not config.email_smtp_host or not config.email_host_user:
            return Response({'error': 'SMTP服务器或发件邮箱未配置'}, status=status.HTTP_400_BAD_REQUEST)

        test_recipient = request.data.get('email') or config.email_host_user
        try:
            import smtplib
            from email.mime.text import MIMEText

            msg = MIMEText('这是一封测试邮件，用于验证邮箱SMTP配置是否正确。', 'plain', 'utf-8')
            msg['From'] = config.email_from or config.email_host_user
            msg['To'] = test_recipient
            msg['Subject'] = '测试邮件 - 灵动平台邮箱配置验证'

            if config.email_use_ssl:
                server = smtplib.SMTP_SSL(config.email_smtp_host, config.email_smtp_port or 465, timeout=30)
            else:
                server = smtplib.SMTP(config.email_smtp_host, config.email_smtp_port or 587, timeout=30)
                if config.email_use_tls:
                    server.starttls()

            if config.email_host_user and config.email_host_password:
                server.login(config.email_host_user, config.email_host_password)

            server.sendmail(msg['From'], [test_recipient], msg.as_string())
            server.quit()

            return Response({'message': f'测试邮件已发送至 {test_recipient}'})
        except Exception as e:
            return Response({'error': f'发送失败: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
