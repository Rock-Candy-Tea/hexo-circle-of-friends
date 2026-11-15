use data_structures::config::{GenerateSummaryConfig, ProviderConfig};
use futures::future::join_all;
use reqwest_middleware::ClientWithMiddleware;
use std::time::Duration;
use tokio::time::sleep;
use tools::html_extractor::HtmlExtractor;
use tracing::{info, warn};

use super::openai;

/// AI摘要生成结果，包含摘要内容和使用的模型信息
#[derive(Debug, Clone)]
pub struct SummaryResult {
    pub summary: String,
    pub model: String,
}

/// 增强的摘要提供商，支持并发、限速和内容分块
pub struct EnhancedSummaryProvider {
    config: GenerateSummaryConfig,
    html_extractor: HtmlExtractor,
}

impl EnhancedSummaryProvider {
    pub fn new(config: GenerateSummaryConfig) -> Self {
        let max_chars = config.get_max_chars();
        let chunk_size = config.get_chunk_size();

        let html_extractor = HtmlExtractor::new(max_chars, chunk_size);

        Self {
            config,
            html_extractor,
        }
    }

    /// 生成单个文章的摘要
    pub async fn generate_summary(
        &self,
        client: &ClientWithMiddleware,
        html_content: &str,
    ) -> Result<SummaryResult, Box<dyn std::error::Error>> {
        if !self.config.enabled {
            return Err("摘要生成功能已禁用".into());
        }

        // 1. 提取和精简HTML内容
        info!("开始提取HTML内容");
        let extracted_content = self.html_extractor.extract_article_content(html_content);
        info!("提取的内容长度: {} 字符", extracted_content.len());

        // 2. 检查是否需要分块处理 (总是启用，智能自适应)
        if extracted_content.len() > self.html_extractor.get_chunk_size() {
            info!("内容过长，启用分块处理");
            self.generate_summary_with_chunks(client, &extracted_content)
                .await
        } else {
            info!("内容长度适中，直接处理");
            self.generate_single_summary(client, &extracted_content)
                .await
        }
    }

    /// 批量生成多个文章的摘要（支持并发）
    pub async fn generate_summaries_batch(
        &self,
        client: &ClientWithMiddleware,
        html_contents: Vec<(String, String)>, // (link, html_content)
    ) -> Vec<(String, Result<SummaryResult, Box<dyn std::error::Error>>)> {
        let max_concurrent = self.config.get_max_concurrent();

        info!(
            "开始批量生成摘要，文章数量: {}, 最大并发: {}",
            html_contents.len(),
            max_concurrent
        );

        // 将任务分批处理
        let mut results = Vec::new();
        let chunks: Vec<_> = html_contents.chunks(max_concurrent).collect();

        for (batch_idx, batch) in chunks.iter().enumerate() {
            info!("处理第 {} 批，包含 {} 个任务", batch_idx + 1, batch.len());

            // 并发处理当前批次
            let batch_futures: Vec<_> = batch
                .iter()
                .map(|(link, html)| {
                    let link = link.clone();
                    async move {
                        let result = self.generate_summary_with_retry(client, html).await;
                        (link, result)
                    }
                })
                .collect();

            let batch_results = join_all(batch_futures).await;
            results.extend(batch_results);

            // 批次间的延迟，避免过于频繁的请求
            if batch_idx < chunks.len() - 1 {
                let delay = 2; // 固定2秒批次间延迟，简单有效
                info!("批次间延迟 {} 秒", delay);
                sleep(Duration::from_secs(delay)).await;
            }
        }

        results
    }

    /// 带重试机制的摘要生成
    async fn generate_summary_with_retry(
        &self,
        client: &ClientWithMiddleware,
        html_content: &str,
    ) -> Result<SummaryResult, Box<dyn std::error::Error>> {
        let retry_attempts = self.config.get_retry_attempts();
        let wait_on_rate_limit = self.config.get_wait_on_rate_limit();
        let rate_limit_delay = self.config.get_rate_limit_delay();

        for attempt in 0..retry_attempts {
            match self.generate_summary(client, html_content).await {
                Ok(summary_result) => return Ok(summary_result),
                Err(e) => {
                    let error_msg = e.to_string().to_lowercase();

                    // 检查是否是限速错误
                    if error_msg.contains("rate limit")
                        || error_msg.contains("too many requests")
                        || error_msg.contains("429")
                    {
                        if wait_on_rate_limit && attempt < retry_attempts - 1 {
                            warn!(
                                "遇到限速，等待 {} 秒后重试 (尝试 {}/{})",
                                rate_limit_delay,
                                attempt + 1,
                                retry_attempts
                            );
                            sleep(Duration::from_secs(rate_limit_delay)).await;
                            continue;
                        } else {
                            return Err(format!("达到最大重试次数，限速错误: {e}").into());
                        }
                    }

                    // 其他错误，短暂延迟后重试
                    if attempt < retry_attempts - 1 {
                        warn!(
                            "生成摘要失败，2秒后重试 (尝试 {}/{}): {}",
                            attempt + 1,
                            retry_attempts,
                            e
                        );
                        sleep(Duration::from_secs(2)).await;
                    } else {
                        return Err(e);
                    }
                }
            }
        }

        Err("达到最大重试次数".into())
    }

    /// 分块处理长内容
    async fn generate_summary_with_chunks(
        &self,
        client: &ClientWithMiddleware,
        content: &str,
    ) -> Result<SummaryResult, Box<dyn std::error::Error>> {
        let chunks = self.html_extractor.chunk_content(content);
        info!("内容分为 {} 块", chunks.len());

        let mut summaries = Vec::new();
        let mut used_models = Vec::new();

        for (idx, chunk) in chunks.iter().enumerate() {
            info!("处理第 {} 块内容 (长度: {} 字符)", idx + 1, chunk.len());

            match self.generate_single_summary(client, chunk).await {
                Ok(summary_result) => {
                    summaries.push(summary_result.summary);
                    used_models.push(summary_result.model);
                }
                Err(e) => {
                    warn!("第 {} 块处理失败: {}", idx + 1, e);
                    // 继续处理其他块，不因一个块失败而中断整个过程
                }
            }

            // 块间延迟，避免过于频繁的API调用
            if idx < chunks.len() - 1 {
                sleep(Duration::from_secs(1)).await;
            }
        }

        if summaries.is_empty() {
            return Err("所有内容块处理都失败了".into());
        }

        // 如果有多个摘要，合并它们
        if summaries.len() > 1 {
            info!("合并 {} 个分块摘要", summaries.len());
            let combined_summary = summaries.join(" ");
            let combined_models = used_models.join(", ");

            // 如果合并后的摘要过长，再次总结
            if combined_summary.len() > 1000 {
                info!("合并摘要过长，进行二次总结");
                let prompt = format!(
                    "请将以下分段摘要合并为一个完整的文章摘要（不超过500字符）：\n\n{combined_summary}"
                );
                match self.generate_single_summary(client, &prompt).await {
                    Ok(final_result) => Ok(SummaryResult {
                        summary: final_result.summary,
                        model: format!("chunks-{}", final_result.model),
                    }),
                    Err(e) => Err(e),
                }
            } else {
                Ok(SummaryResult {
                    summary: combined_summary,
                    model: format!("chunks-{combined_models}"),
                })
            }
        } else {
            Ok(SummaryResult {
                summary: summaries.into_iter().next().unwrap(),
                model: used_models.into_iter().next().unwrap(),
            })
        }
    }

    /// 生成单个摘要（核心逻辑）：按配置顺序遍历所有提供商，前面的优先，全部失败则报错
    async fn generate_single_summary(
        &self,
        client: &ClientWithMiddleware,
        content: &str,
    ) -> Result<SummaryResult, Box<dyn std::error::Error>> {
        let mut last_error = None;

        for provider in &self.config.providers {
            match self.try_provider_models(client, provider, content).await {
                Ok(summary_result) => return Ok(summary_result),
                Err(e) => {
                    warn!("提供商 {} 失败: {}", provider.name, e);
                    last_error = Some(e);
                }
            }
        }

        Err(last_error.unwrap_or_else(|| "没有配置任何可用的 AI 提供商".to_string().into()))
    }

    /// 依次尝试某个提供商下的所有模型（OpenAI 兼容格式）
    async fn try_provider_models(
        &self,
        client: &ClientWithMiddleware,
        provider: &ProviderConfig,
        content: &str,
    ) -> Result<SummaryResult, Box<dyn std::error::Error>> {
        // 读取该提供商配置的 API key；未配置则直接失败，由上层降级到下一个提供商
        let api_key = tools::get_env_var(&provider.api_key_env)?;

        let mut last_error = None;

        for model in &provider.models {
            info!("尝试使用 {} 模型: {}", provider.name, model);

            match openai::generate_content(client, &provider.base_url, &api_key, model, content)
                .await
            {
                Ok(summary) => {
                    info!("{} 模型 {} 成功生成摘要", provider.name, model);
                    return Ok(SummaryResult {
                        summary,
                        model: format!("{}-{}", provider.name, model),
                    });
                }
                Err(e) => {
                    warn!("{} 模型 {} 失败: {}", provider.name, model, e);
                    last_error = Some(e);
                }
            }
        }

        Err(last_error.unwrap_or_else(|| format!("{} 的所有模型都失败了", provider.name).into()))
    }

    /// 验证配置的有效性
    pub fn validate_config(&self) -> Result<(), String> {
        if !self.config.enabled {
            return Ok(());
        }

        if self.config.providers.is_empty() {
            return Err("未配置任何 AI 提供商（providers 为空）".to_string());
        }

        for provider in &self.config.providers {
            if provider.name.is_empty() {
                return Err("提供商 name 不能为空".to_string());
            }
            if provider.base_url.is_empty() {
                return Err(format!("提供商 {} 的 base_url 不能为空", provider.name));
            }
            if provider.api_key_env.is_empty() {
                return Err(format!("提供商 {} 的 api_key_env 不能为空", provider.name));
            }
            if provider.models.is_empty() {
                return Err(format!("提供商 {} 的模型列表不能为空", provider.name));
            }
        }

        // 验证配置参数 (使用智能默认值，简化验证)
        if self.config.get_max_concurrent() == 0 {
            return Err("最大并发数不能为0".to_string());
        }
        if self.config.get_max_chars() == 0 {
            return Err("最大字符数不能为0".to_string());
        }

        Ok(())
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use data_structures::config::ProviderConfig;

    fn create_test_config() -> GenerateSummaryConfig {
        GenerateSummaryConfig {
            enabled: true,
            max_concurrent: 3,
            wait_on_rate_limit: true,
            max_chars: 8000,
            providers: vec![ProviderConfig {
                name: "siliconflow".to_string(),
                base_url: "https://api.siliconflow.cn/v1".to_string(),
                api_key_env: "SILICONFLOW_API_KEY".to_string(),
                models: vec!["deepseek-ai/DeepSeek-V3.2".to_string()],
            }],
        }
    }

    #[test]
    fn test_validate_config_valid() {
        let provider = EnhancedSummaryProvider::new(create_test_config());
        assert!(provider.validate_config().is_ok());
    }

    #[test]
    fn test_validate_config_no_providers() {
        let mut config = create_test_config();
        config.providers = vec![];

        let provider = EnhancedSummaryProvider::new(config);
        assert!(provider.validate_config().is_err());
    }

    #[test]
    fn test_validate_config_empty_models() {
        let mut config = create_test_config();
        config.providers[0].models = vec![];

        let provider = EnhancedSummaryProvider::new(config);
        assert!(provider.validate_config().is_err());
    }

    #[test]
    fn test_validate_config_invalid_concurrent() {
        let mut config = create_test_config();
        config.max_concurrent = 0;

        let provider = EnhancedSummaryProvider::new(config);
        assert!(provider.validate_config().is_err());
    }

    #[test]
    fn test_validate_config_invalid_content() {
        let mut config = create_test_config();
        config.max_chars = 0;

        let provider = EnhancedSummaryProvider::new(config);
        assert!(provider.validate_config().is_err());
    }

    #[test]
    fn test_default_values() {
        let config = create_test_config();

        // 测试默认值
        assert_eq!(config.get_max_concurrent(), 3);
        assert!(config.get_wait_on_rate_limit());
        assert_eq!(config.get_max_chars(), 8000);
        assert_eq!(config.get_chunk_size(), 4000);
        assert_eq!(config.get_retry_attempts(), 3);
        assert_eq!(config.get_rate_limit_delay(), 60);
    }
}
