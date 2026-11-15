pub mod enhanced_provider;
pub mod openai;

pub use enhanced_provider::EnhancedSummaryProvider;
pub use enhanced_provider::SummaryResult;

pub(crate) const SUMMARY_MAX_OUTPUT_TOKENS: u64 = 1024;
pub(crate) const SUMMARY_SYSTEM_PROMPT: &str = r#"你是一个文本和文章分析专家。请根据提供的博客文章正文生成摘要。

你必须严格遵循以下回复规则：
1. 摘要必须使用简体中文；如果原文不是简体中文，请翻译为简体中文。
2. 摘要不得超过500个字符，并在信息充分的前提下尽量简洁。
3. 仅输出摘要正文，不要添加标题、前缀、字符数或解释。"#;
