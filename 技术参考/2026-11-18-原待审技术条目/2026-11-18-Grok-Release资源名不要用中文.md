> 技术参考归档，不属待审或正式规则；2026-11-18 从旧待审移入，不代表审核通过或驳回。
> 以下保留原文供定位历史线索，不保证其中推断和绝对化表述成立（如 Release 中文名或所有文本通道必截断）；本轮未核对工具当前行为，不应直接当作通用禁令执行。
> 原文来源：[f5a75e4](https://github.com/cjhkcjgk3-sys/ai-dev-lessons/blob/f5a75e485d4caee8c579b65df7ac591a8095350f/待审/2026-11-18-Grok-Release资源名不要用中文.md)。

提交模型：Grok
来源仓库：character-image-staging（另两个图片仓库同步了这条记录）
建议归类：通用
建议新增或修改：在《检查清单》“收尾”新增一条：上传到 GitHub Releases 的文件名只用英文、数字和连字符；中文名写在 Release 说明或 README 对照表里，发布后打开下载链接核对文件名。
证据：
- 图片仓库问题记录“GitHub Release 把中文资源名改成 default.zip（2026-11-14）”：`gh release create` 上传 `原神.zip` 后资源名变成 `default.zip`，之后改成 `genshin.zip` 等英文名。见 [问题与解决记录](https://github.com/cjhkcjgk3-sys/character-image-staging/blob/main/docs/%E9%97%AE%E9%A2%98%E4%B8%8E%E8%A7%A3%E5%86%B3%E8%AE%B0%E5%BD%95.md)。
- 相关发布功能提交：[0b1ce14](https://github.com/cjhkcjgk3-sys/character-image-staging/commit/0b1ce14)。
