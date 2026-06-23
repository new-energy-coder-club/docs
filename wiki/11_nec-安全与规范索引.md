# NEC 安全与规范索引

> 实验室安全 · 代码规范 · 文档规范 · 协作流程

---

## 快速入口

<lark-table rows="6" cols="3" header-row="true" column-widths="244,244,244">

  <lark-tr>
    <lark-td>
      规范类型
    </lark-td>
    <lark-td>
      文档
    </lark-td>
    <lark-td>
      适用对象
    </lark-td>
  </lark-tr>
  <lark-tr>
    <lark-td>
      **项目管理**
    </lark-td>
    <lark-td>
      [NEC ROBOCON 2026 项目管理指南](https://scn0bdoc8zxg.feishu.cn/docx/VZF7dgkiKouP4fx46Q5cQdkUnzf)
    </lark-td>
    <lark-td>
      全体成员
    </lark-td>
  </lark-tr>
  <lark-tr>
    <lark-td>
      **代码提交**
    </lark-td>
    <lark-td>
      [基于仓库提交的自动化日报与总结生成指南](https://scn0bdoc8zxg.feishu.cn/docx/CEALdxroboMukexx2T6cJGUyn1o)
    </lark-td>
    <lark-td>
      技术组成员
    </lark-td>
  </lark-tr>
  <lark-tr>
    <lark-td>
      **协作流程**
    </lark-td>
    <lark-td>
      [④ Contribute · 参与协作](https://scn0bdoc8zxg.feishu.cn/wiki/Jrk5w2K4riyS5SkSLqScqtNjnPb)
    </lark-td>
    <lark-td>
      全体成员
    </lark-td>
  </lark-tr>
  <lark-tr>
    <lark-td>
      **成员管理**
    </lark-td>
    <lark-td>
      [NEC核心预备机制 · 数字化评估](https://scn0bdoc8zxg.feishu.cn/docx/IYrCdXEnGoYAcMxXD0gcTV8fn2g)
    </lark-td>
    <lark-td>
      核心/预备成员
    </lark-td>
  </lark-tr>
  <lark-tr>
    <lark-td>
      **实验室申请**
    </lark-td>
    <lark-td>
      [非正常时间工作申请表模板](https://scn0bdoc8zxg.feishu.cn/docx/Q6mEdBc7eo8jhexU7uxcR6U8nlV)
    </lark-td>
    <lark-td>
      全体技术组
    </lark-td>
  </lark-tr>
</lark-table>

---

## 一、实验室与场地安全

### 3D打印区

- **设备**: K1 打印机 × N台、Creality Print / BanbuLab 切片软件
- **安全须知**:
	- 换料后必须重新进料
	- PLA/PETG/ASA 材料特性差异巨大，参数不可混用
	- 高温部件（>200°C）运行时勿触碰
	- 堵头处理参考 [K1 使用说明书](https://scn0bdoc8zxg.feishu.cn/wiki/ICwXwiTE9iJ676kzwPUcvAmqnSd)
- **耗材采购**: 见 [NEC 新人 Quickstart](https://scn0bdoc8zxg.feishu.cn/wiki/QAtNwr244ir8ZekITEZcwpOZnkg) 耗材采购章节

### 机械加工区

- **设备**: 雕刻机
- **培训要求**: 必须通过 [雕刻机培训](https://scn0bdoc8zxg.feishu.cn/docx/GeZFdb8Qqovh5cx18ktcoauTnnd) 方可独立操作
- **安全须知**:
	- 佩戴护目镜
	- 长发束起
	- 设备运行时勿离开

### 电控调试区

- **设备**: DM-MC02 电控板、M3508/N630/8010 电机
- **安全须知**:
	- 上电前检查接线（8010 注意红黑线顺序）
	- 电池规格匹配（当前需6S规格）
	- 短接 CAN/RS485 端子前确认断电

### 视觉实验区

- **设备**: K230 / Odin1 / 树莓派
- **安全须知**:
	- K230 功耗较大，建议使用 USB3.0 或 5V2A+ 供电
	- TF 卡操作前先安全弹出

---

## 二、代码提交规范

### Git Workflow
> 详细流程见 [Gitee 仓库培训](https://scn0bdoc8zxg.feishu.cn/docx/QkkYdBJE0o2Q9Xx9O5ocIoWZnde)

1. **分支命名**: `feature/xxx`, `fix/xxx`, `docs/xxx`
1. **提交信息**: 中英文均可，需说明做了什么
1. **PR 要求**: 必须关联 Issue，需 Review 通过
1. **日报格式**: `YYYYMMDD @姓名: 工作内容`（见日报指南）

### 代码风格

- C/C++: 遵循团队统一风格
- Python: PEP8 为基础
- 嵌入式: 参考 [中科大 RM 进阶课](https://gitee.com/kit-miao/dm-mc02) 风格

---

## 三、文档命名规范

### 飞书文档

- **知识库文档**: `{ NEC }` 前缀或分类前缀
- **会议纪要**: `智能纪要：主题 YYYY年MM月DD日`
- **培训记录**: `【培训记录提交】主题 — YYYY-MM-DD`
- **项目文档**: `项目名称 + 版本/日期`

### 仓库文档

- README: 中英双语优先
- 架构图: `architecture-vX.Y.png`
- 数据手册: `datasheet_型号_厂商.pdf`

---

## 四、协作流程规范

### 任务流转

1. **需求/任务** → 录入 [项目管理 Base](https://scn0bdoc8zxg.feishu.cn/base/OCEebf0Pkazhn0s29HmcAsuHnQg)
1. **分配** → 负责人确认，设置截止日期
1. **执行** → 在对应群聊同步进度
1. **完成** → 更新 Base 状态 + 代码提交 + 积分同步

### 会议规范

- **例会**: 每周固定时间，提前发布议程
- **纪要**: 飞书智能纪要自动生成，提取待办事项
- **待办跟踪**: 纪要中的 action items 需在一周内闭环

### 请假/缺席

- 非正常时间实验室工作需填写 [申请表](https://scn0bdoc8zxg.feishu.cn/docx/Q6mEdBc7eo8jhexU7uxcR6U8nlV)
- 例会缺席需提前在群聊告知

---

## 五、经费与采购

### 采购流程

1. 需求提出 → 组长审核
1. 经费审批 → DarrenPig/财务负责人
1. 采购执行 → 指定采购人
1. 入库登记 → 在项目管理 Base 中记录

### 供应商清单

见 [往届经验速查 - 供应商资源备忘](https://www.feishu.cn/wiki/EPwVwQipgiWJ05kXJojcO8wCnZb)

---

## 六、待完善规范

- [ ] **实验室安全手册**（完整版）— 负责人：待指定
- [ ] **设备使用登记制度** — 负责人：待指定
- [ ] **耗材领用规范** — 负责人：待指定
- [ ] **外协加工流程** — 负责人：待指定
- [ ] **知识产权与开源协议指南** — 负责人：待指定

---

*本文档为规范索引，具体执行细则由各组组长制定。**最后更新：2026-04-29 | 由 NEC-Claw 创建*