use data_structures::config::GenerateSummaryConfig;
use futures::future::join_all;
use reqwest_middleware::ClientWithMiddleware;
use std::time::Duration;
use tokio::time::sleep;
use tools::html_extractor::HtmlExtractor;
use tracing::{info, warn};

use super::{bigmodel, gemini, siliconflow};

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

    /// 生成单个摘要（核心逻辑）
    async fn generate_single_summary(
        &self,
        client: &ClientWithMiddleware,
        content: &str,
    ) -> Result<SummaryResult, Box<dyn std::error::Error>> {
        match self.config.provider.as_str() {
            "gemini" => self.try_gemini_models(client, content).await,
            "siliconflow" => self.try_siliconflow_models(client, content).await,
            "bigmodel" => self.try_bigmodel_models(client, content).await,
            "all" => self.try_all_providers(client, content).await,
            _ => Err(format!("不支持的提供商: {}", self.config.provider).into()),
        }
    }

    async fn try_gemini_models(
        &self,
        client: &ClientWithMiddleware,
        content: &str,
    ) -> Result<SummaryResult, Box<dyn std::error::Error>> {
        let gemini_config = self.config.gemini.as_ref().ok_or("Gemini配置缺失")?;

        let mut last_error = None;

        for model in &gemini_config.models {
            info!("尝试使用Gemini模型: {}", model);

            match gemini::generate_content(client, content).await {
                Ok(summary) => {
                    info!("Gemini模型 {} 成功生成摘要", model);
                    return Ok(SummaryResult {
                        summary,
                        model: format!("gemini-{model}"),
                    });
                }
                Err(e) => {
                    warn!("Gemini模型 {} 失败: {}", model, e);
                    last_error = Some(e);
                }
            }
        }

        Err(last_error.unwrap_or_else(|| "所有Gemini模型都失败了".into()))
    }

    async fn try_siliconflow_models(
        &self,
        client: &ClientWithMiddleware,
        content: &str,
    ) -> Result<SummaryResult, Box<dyn std::error::Error>> {
        let siliconflow_config = self
            .config
            .siliconflow
            .as_ref()
            .ok_or("SiliconFlow配置缺失")?;

        let mut last_error = None;

        for model in &siliconflow_config.models {
            info!("尝试使用SiliconFlow模型: {}", model);

            match siliconflow::generate_content(client, model, content).await {
                Ok(summary) => {
                    info!("SiliconFlow模型 {} 成功生成摘要", model);
                    return Ok(SummaryResult {
                        summary,
                        model: format!("siliconflow-{model}"),
                    });
                }
                Err(e) => {
                    warn!("SiliconFlow模型 {} 失败: {}", model, e);
                    last_error = Some(e);
                }
            }
        }

        Err(last_error.unwrap_or_else(|| "所有SiliconFlow模型都失败了".into()))
    }

    async fn try_bigmodel_models(
        &self,
        client: &ClientWithMiddleware,
        content: &str,
    ) -> Result<SummaryResult, Box<dyn std::error::Error>> {
        let bigmodel_config = self.config.bigmodel.as_ref().ok_or("BigModel配置缺失")?;

        let mut last_error = None;

        for model in &bigmodel_config.models {
            info!("尝试使用BigModel模型: {}", model);

            match bigmodel::generate_content(client, model, content).await {
                Ok(summary) => {
                    info!("BigModel模型 {} 成功生成摘要", model);
                    return Ok(SummaryResult {
                        summary,
                        model: format!("bigmodel-{model}"),
                    });
                }
                Err(e) => {
                    warn!("BigModel模型 {} 失败: {}", model, e);
                    last_error = Some(e);
                }
            }
        }

        Err(last_error.unwrap_or_else(|| "所有BigModel模型都失败了".into()))
    }

    async fn try_all_providers(
        &self,
        client: &ClientWithMiddleware,
        content: &str,
    ) -> Result<SummaryResult, Box<dyn std::error::Error>> {
        info!("尝试所有配置的AI提供商");

        // 首先尝试BigModel
        if self.config.bigmodel.is_some() {
            info!("尝试BigModel提供商");
            match self.try_bigmodel_models(client, content).await {
                Ok(summary_result) => {
                    info!("BigModel提供商成功生成摘要");
                    return Ok(summary_result);
                }
                Err(e) => {
                    warn!("BigModel提供商失败: {}", e);
                }
            }
        }

        // 其次尝试SiliconFlow
        if self.config.siliconflow.is_some() {
            info!("尝试SiliconFlow提供商");
            match self.try_siliconflow_models(client, content).await {
                Ok(summary_result) => {
                    info!("SiliconFlow提供商成功生成摘要");
                    return Ok(summary_result);
                }
                Err(e) => {
                    warn!("SiliconFlow提供商失败: {}", e);
                }
            }
        }

        // 然后尝试Gemini作为备选
        if self.config.gemini.is_some() {
            info!("尝试Gemini提供商");
            match self.try_gemini_models(client, content).await {
                Ok(summary_result) => {
                    info!("Gemini提供商成功生成摘要");
                    return Ok(summary_result);
                }
                Err(e) => {
                    warn!("Gemini提供商失败: {}", e);
                }
            }
        }

        Err("所有配置的AI提供商都失败了".into())
    }

    /// 验证配置的有效性
    pub fn validate_config(&self) -> Result<(), String> {
        if !self.config.enabled {
            return Ok(());
        }

        // 验证提供商配置
        match self.config.provider.as_str() {
            "gemini" => {
                if let Some(gemini_config) = &self.config.gemini {
                    if gemini_config.models.is_empty() {
                        return Err("Gemini模型列表不能为空".to_string());
                    }
                } else {
                    return Err("选择了Gemini提供商但缺少Gemini配置".to_string());
                }
            }
            "siliconflow" => {
                if let Some(siliconflow_config) = &self.config.siliconflow {
                    if siliconflow_config.models.is_empty() {
                        return Err("SiliconFlow模型列表不能为空".to_string());
                    }
                } else {
                    return Err("选择了SiliconFlow提供商但缺少SiliconFlow配置".to_string());
                }
            }
            "bigmodel" => {
                if let Some(bigmodel_config) = &self.config.bigmodel {
                    if bigmodel_config.models.is_empty() {
                        return Err("BigModel模型列表不能为空".to_string());
                    }
                } else {
                    return Err("选择了BigModel提供商但缺少BigModel配置".to_string());
                }
            }
            "all" => {
                let has_gemini = self
                    .config
                    .gemini
                    .as_ref()
                    .is_some_and(|g| !g.models.is_empty());
                let has_siliconflow = self
                    .config
                    .siliconflow
                    .as_ref()
                    .is_some_and(|s| !s.models.is_empty());

                if !has_gemini && !has_siliconflow {
                    return Err("选择了'all'提供商但没有配置任何有效的提供商".to_string());
                }
            }
            _ => return Err(format!("不支持的提供商: {}", self.config.provider)),
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
    use data_structures::config::ModelConfig;

    fn create_test_config() -> GenerateSummaryConfig {
        GenerateSummaryConfig {
            enabled: true,
            provider: "siliconflow".to_string(),
            max_concurrent: 3,        // 使用默认值
            wait_on_rate_limit: true, // 使用默认值
            max_chars: 8000,          // 使用默认值
            gemini: None,
            siliconflow: Some(ModelConfig {
                models: vec!["THUDM/GLM-4.1V-9B-Thinking".to_string()],
            }),
            bigmodel: None,
        }
    }

    #[test]
    fn test_validate_config_valid() {
        let provider = EnhancedSummaryProvider::new(create_test_config());
        assert!(provider.validate_config().is_ok());
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
