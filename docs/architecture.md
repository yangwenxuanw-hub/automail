# AutoMail 架构说明

## 目标

这个原型用于处理金融客户入金、出金、SI FOP/DVP 指令的审批邮件编排，重点覆盖以下能力：

- 按交易金额与账户类型自动判断最低授权人员
- 自动生成初始审批邮件
- 收集授权人员回信并判断是否全部批准
- 在全部批准后提醒操作人员
- 自动把初始邮件和全部授权回信整理成附件
- 自动生成下一步操作邮件草稿
- 预留 Outlook、Microsoft Graph、数据库、通知中心等接口

## 模块划分

- `automail.models`
  - 定义交易请求、审批要求、审批动作、邮件对象、工作流 Case
- `automail.rules`
  - 审批门槛规则引擎
- `automail.services`
  - 工作流编排，负责启动 Case、刷新审批状态、生成下一步邮件
- `automail.interfaces`
  - 定义邮件网关、通知器、仓储、附件打包器的抽象接口
- `automail.adapters.memory`
  - 内存版示例适配器，便于本地演示和单元测试
- `automail.adapters.stubs`
  - 未来接 Outlook COM / Microsoft Graph 的占位实现

## 审批规则

### 1. 客户提款或提仓（相同受益人），包括 SI FOP/DVP

- `个人或联名账户`
  - `<= HKD 5M`: `CO Maker + Checker`
  - `<= HKD 10M`: `HCO + HF`
  - `> HKD 10M`: `HCO + HF + RO 或主管`
- `其他账户，包括公司或机构账户`
  - `<= HKD 10M`: `CO Maker + Checker`
  - `<= HKD 50M`: `HCO + HF`
  - `> HKD 50M`: `HCO + HF + RO 或主管`
- 额外风险审批
  - 如提款前后存在 `debit cash` 或 `debit stock balance`
  - 或保证金账户存在 `debit balance`
  - 则额外需要 `Risk Management`
- 对 SI 指令
  - 取 `market value` 和 `settlement amount` 较高者作为审批金额

### 2. 客户存款或存仓（相同受益人），包括 SI FOP/DVP

- `个人或联名账户`
  - `<= HKD 10M`: `CO Maker + Checker`
  - `<= HKD 50M`: `HCO + HF`
  - `> HKD 50M`: `HCO + HF + RO 或主管`
- `其他账户，包括公司或机构账户`
  - `<= HKD 50M`: `CO Maker + Checker`
  - `<= HKD 100M`: `HCO + HF`
  - `> HKD 100M`: `HCO + HF + RO 或主管`
- 对 SI 指令
  - 取 `market value` 和 `settlement amount` 较高者作为审批金额

## 建议的下一阶段扩展

- Outlook 集成
  - Windows 环境下用 `win32com` 直接创建草稿、读取会话、导出 `.msg`
- Microsoft 365 集成
  - 用 Microsoft Graph 发送邮件、读取回信、做 webhook 订阅
- 审批识别增强
  - 支持从回信正文解析 `APPROVED` / `REJECTED`
  - 支持同一角色多人候补、最少一人批准即满足
- 持久化
  - 把 Case、邮件线程、审批记录存入数据库
- 提醒能力
  - 接 Teams、企业微信、短信、桌面通知
- 审计能力
  - 全链路留痕、审批时间线、审批超时告警、导出审计报表
