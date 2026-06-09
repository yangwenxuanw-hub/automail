# AutoMail

面向金融业务审批邮件场景的 Outlook 自动化原型。

当前原型已经实现：

- 按金额、账户类型、交易类型自动匹配最低授权人员
- 生成初始审批邮件草稿
- 汇总授权人员回信并判断是否全部批准
- 在全部批准后触发提醒
- 自动把初始信息和全部授权回信整理为附件文件
- 自动生成下一步邮件草稿
- 预留 Outlook / Microsoft Graph / 数据库 / 通知扩展接口

## 目录

- `automail/models.py`
  - 核心数据模型
- `automail/rules.py`
  - 审批规则引擎
- `automail/services.py`
  - 工作流编排服务
- `automail/interfaces.py`
  - 扩展接口定义
- `automail/adapters/memory.py`
  - 可运行的内存版演示适配器
- `automail/adapters/stubs.py`
  - Outlook COM / Microsoft Graph 预留适配器
- `docs/architecture.md`
  - 架构和规则说明

## 运行演示

需要 Python 3.11+。

```bash
cd /workspace
python -m automail.cli --demo
```

运行后会看到：

- 自动生成审批邮件草稿
- 自动收集示例审批回信
- 当全部授权完成后输出提醒
- 在 `outbox/<case_id>/` 下生成附件材料

## 当前限制

- 当前仓库提供的是可扩展原型，默认使用内存适配器演示流程
- 未直接连接真实 Outlook，因为真实 Outlook 自动化通常需要 Windows + Outlook 客户端，或改为 Microsoft Graph
- 如果你准备在公司环境落地，建议下一步接入：
  - Windows Outlook COM
  - Microsoft Graph API
  - 数据库存储
  - 审批超时提醒
  - 邮件正文审批关键字识别
