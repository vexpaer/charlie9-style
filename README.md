<div align="center">

# Charlie9 Style

**把少年冒险插画的线条、人物与叙事空间，变成可复用的创作参考。**

从 27 册《查理九世》扫描资料中整理出的视觉参考集与 Codex Skill。<br>
黑白叙事插画 · 人物设计 · 环境构图 · 照片转插画

**简体中文** · [English](README.en.md)

[快速使用](#快速使用) · [生成示例](#生成示例) · [参考图集](references/gallery.html) · [风格指南](SKILL.md)

</div>

## 仓库宣传图

<p align="center">
  <a href="promo/charlie9-style_skill_promo_poster.png"><img src="promo/charlie9-style_skill_promo_poster.png" height="560" alt="查理九世插画 Skill 宣传图"></a>
  &nbsp;&nbsp;
  <a href="promo/charlie9-style_skill_promo_02_repo_intro.png"><img src="promo/charlie9-style_skill_promo_02_repo_intro.png" height="560" alt="仓库介绍：27 册原作样本、141 张参考插画、10 份专题分析及 GitHub 链接"></a>
</p>

## 生成示例

<p align="center">
  <a href="examples/gallery.jpg"><img src="examples/gallery.jpg" height="560" alt="两行错位拼图：上排为人物插图与生物遭遇，下排为湖边场景与篮球场照片转插画对比"></a>
</p>

<p align="center"><sub>上排：人物插图 · 生物遭遇　／　下排：湖边场景 · 照片转插画</sub></p>

四张示例保留完整画面，按原始比例拼成两行。展示高度设为 560 px，宽度随比例计算；点击拼图查看大图。

[人物插图](examples/characters.png) · [生物遭遇](examples/creature-encounter.png) · [湖边场景](examples/lakeside.png) · [篮球场对比](examples/basketball-court-comparison.png)

## 这个项目能做什么

- **辅助画新图**：把少年冒险、悬疑场景、人物小图和环境插画的视觉特点转成可执行的创作方向。
- **用图片理解风格**：141 张有来源记录的代表裁图，配合线稿、明暗、构图等 10 份专题分析。
- **把照片转为插画**：保留场景的透视和主体位置，用黑白轮廓、排线与阴影重新表达。
- **追溯参考来源**：通过册数、书名和 PDF 页码，连接参考图与原始扫描页。

Skill 提供指令和参考图片；实际绘图由图像生成工具完成。项目不包含训练权重或独立的图像生成服务。

## 快速使用

给你的 Agent 发送：

```text
使用 https://github.com/vexpaer/charlie9-style，生成 xxx 图片。
```

例如：

```text
使用 https://github.com/vexpaer/charlie9-style，生成三名少年在雾中湖边发现微光的黑白插画。
```

照片转插画时，附上照片并发送：

```text
使用 https://github.com/vexpaer/charlie9-style，根据这张照片生成黑白插画，保留原构图和人物位置。
```

Agent 需能读取仓库内容，并具备图像生成能力。

## 风格指南

| 方向 | 创作重点 | 详细说明 |
| --- | --- | --- |
| 人物 | 易读的表情、动作与不同体型轮廓 | [人物设计](analysis/character-design.md) |
| 线条与明暗 | 粗细变化、局部排线、明确的黑白块面 | [线稿](analysis/linework.md) · [明暗](analysis/shading.md) |
| 场景 | 前中后景、透视、自然与建筑细节 | [构图](analysis/composition.md) · [透视](analysis/perspective.md) · [环境](analysis/environment.md) |
| 冒险与悬疑 | 尺度反差、遮挡、剪影与异常形态 | [怪物设计](analysis/creature-design.md) · [悬疑表达](analysis/horror-language.md) |
| 色彩 | 根据具体参考选择处理方式 | [色彩](analysis/color.md) |

先读 [核心风格与证据范围](analysis/style-core.md)，再按任务选择专题。

## Skill 内容

| 内容 | 用途 |
| --- | --- |
| [SKILL.md](SKILL.md) | 创作方向与参考阅读入口 |
| [风格专题](analysis/) | 10 份人物、线稿、明暗、环境等指南 |
| [参考图集](references/gallery.html) | 141 张代表参考图 |
| [来源说明](references/sources.md) | 参考图对应的册数、书名与 PDF 页码 |
| [展示示例](examples/) | README 使用的四个示例与拼图 |

```text
charlie9-style/
├── SKILL.md
├── analysis/
├── references/
│   ├── representative/
│   ├── gallery.html
│   └── sources.md
├── examples/
├── README.md
├── README.en.md
├── LICENSE
└── THIRD_PARTY_NOTICES.md
```

下载后可在浏览器中打开 HTML 参考图集。仓库只保留 Skill、必要参考资源和展示文档。

## 参与贡献

欢迎提交可复现的问题、参考来源纠错、风格分析补充和示例改进。问题报告请附文件路径、来源册与 PDF 页码。较大的结构调整建议先讨论。

新增参考图请保留来源记录，新增生成示例请标明使用的参考和生成方式。修改文档时同步更新中英文页面。

## 来源与许可

本项目基于《查理九世》扫描样本研究可见的插画特征，未验证具体插画作者归属，也不代表官方项目或所有卷册的统一风格。

代码与原创文档采用 [MIT 许可](LICENSE)。扫描参考图、照片与生成示例不属于该软件许可范围；扫描页和参考裁图的版权属于各自权利人。详见 [第三方资料说明](THIRD_PARTY_NOTICES.md)。
