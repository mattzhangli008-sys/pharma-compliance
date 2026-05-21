# pharma-compliance

医药合规审查技能 — 对文本或文件进行医药行业合规性审查。

## 功能

- 识别岗位描述、制度文件、推广材料中的合规风险
- 基于五大合规逻辑模型 + 黑名单关键词双重校验
- 输出结构化审查报告，每条违规附带原文证据和修改建议
- 支持直接文本输入和文件（docx/pdf/txt）解析

## 适用场景

| 场景 | 示例 |
|------|------|
| 岗位 JD 审查 | "审查这个医药代表的岗位描述是否合规" |
| 制度文件审查 | "检查这份管理办法的合规性" |
| 推广材料审查 | "审查这份学术推广方案" |
| 批量文件审查 | "审查这个目录下所有 docx 文件" |

## 触发关键词

- 合规审查、合规检查、compliance review
- 医药合规、pharma compliance
- JD审查、岗位审查
- 制度审查、文件审查

## 合规规则

| 规则 | 说明 | 严重性 |
|------|------|--------|
| 身份偏移逻辑 | 医药代表不得涉及销售、收款、商业谈判 | 高 |
| 处方干预逻辑 | 严禁收集/追踪处方量 | 高 |
| 利益交换逻辑 | 严禁通过利益手段换取销量 | 高 |
| 非学术化推广逻辑 | 严禁在非学术场景推广 | 中 |
| 科学严谨性逻辑 | 严禁夸大疗效 | 中 |

## 安装

### Codex

```bash
mkdir -p ~/.codex/skills
cp -R skill/pharma-compliance ~/.codex/skills/
```

### Claude Code

```bash
mkdir -p ~/.claude/agents
cp skill/pharma-compliance/SKILL.md ~/.claude/agents/pharma-compliance.md
```

### Kiro

```bash
cp -R skill/pharma-compliance .kiro/skills/
```

### 其他 Agent

将整个 `pharma-compliance/` 目录复制到你的 Agent 的 skills/prompts 目录中，保持 `SKILL.md` 和 `references/` 的相对路径关系。

## 文件结构

```
pharma-compliance/
├── SKILL.md              # 核心技能文件（规则 + 工作流）
├── README.md             # 说明文档
├── references/
│   ├── blacklist.md      # 黑名单关键词详细分类
│   ├── logic-model.md    # 合规逻辑模型详解
│   └── examples.md       # 审查示例
└── scripts/
    ├── extract_file.py   # 文件文本提取（docx/pptx/pdf/txt/doc）
    ├── generate_report.py # HTML 报告生成
    └── requirements.txt  # Python 依赖
```
