# Refactor LoginConfig to use test case instead of hardcoded elements

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('ui_automation', '0003_remove_uiproject_login_button_selector_and_more'),
    ]

    operations = [
        # Remove old element FK fields
        migrations.RemoveField(
            model_name='loginconfig',
            name='username_element',
        ),
        migrations.RemoveField(
            model_name='loginconfig',
            name='password_element',
        ),
        migrations.RemoveField(
            model_name='loginconfig',
            name='login_button_element',
        ),
        migrations.RemoveField(
            model_name='loginconfig',
            name='verify_element',
        ),
        # Remove old non-FK fields
        migrations.RemoveField(
            model_name='loginconfig',
            name='username_value',
        ),
        migrations.RemoveField(
            model_name='loginconfig',
            name='password_value',
        ),
        migrations.RemoveField(
            model_name='loginconfig',
            name='verify_type',
        ),
        migrations.RemoveField(
            model_name='loginconfig',
            name='verify_value',
        ),
        migrations.RemoveField(
            model_name='loginconfig',
            name='verify_wait_time',
        ),
        migrations.RemoveField(
            model_name='loginconfig',
            name='pre_login_steps',
        ),
        # Change login_url from required to optional
        migrations.AlterField(
            model_name='loginconfig',
            name='login_url',
            field=models.URLField(blank=True, default='', verbose_name='登录页URL',
                                  help_text='可选，留空则使用项目基础URL'),
        ),
        # Add new login_test_case FK field
        migrations.AddField(
            model_name='loginconfig',
            name='login_test_case',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name='login_configs',
                to='ui_automation.testcase',
                verbose_name='登录测试用例',
                help_text='定义登录操作步骤的测试用例',
            ),
        ),
    ]
