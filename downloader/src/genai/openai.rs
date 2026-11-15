use reqwest_middleware::ClientWithMiddleware;
use serde_json::json;
use tracing::info;

use super::{SUMMARY_MAX_OUTPUT_TOKENS, SUMMARY_SYSTEM_PROMPT};

/// 通用 OpenAI 兼容客户端
///
/// 只要供应商提供 OpenAI 兼容的 `chat/completions` 端点（SiliconFlow、智谱、
/// DeepSeek、Moonshot、OpenRouter、本地 ollama、甚至 Gemini 的 OpenAI 兼容层等），
/// 都能通过本函数调用，无需为每个供应商单独编写代码。
pub async fn generate_content(
    client: &ClientWithMiddleware,
    base_url: &str,
    api_key: &str,
    model: &str,
    content: &str,
) -> Result<String, Box<dyn std::error::Error>> {
    let body = json!({
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": SUMMARY_SYSTEM_PROMPT
            },
            {
                "role": "user",
                "content": content
            }
        ],
        "temperature": 0.3,
        "max_tokens": SUMMARY_MAX_OUTPUT_TOKENS
    });

    // 拼接完整端点，兼容 base_url 末尾是否带 "/"
    let url = format!("{}/chat/completions", base_url.trim_end_matches('/'));

    let response = client
        .post(&url)
        .header("Authorization", format!("Bearer {api_key}"))
        .header("Content-Type", "application/json")
        .body(body.to_string())
        .send()
        .await?;

    let response_text = response.text().await?;
    info!("OpenAI-compatible [{model}] ({url}) API response: {response_text}");

    let response_json: serde_json::Value = serde_json::from_str(&response_text)?;

    if let Some(choices) = response_json["choices"].as_array()
        && let Some(first_choice) = choices.first()
        && let Some(message) = first_choice["message"].as_object()
        && let Some(content) = message["content"].as_str()
    {
        return Ok(content.trim().to_string());
    }

    Err(
        format!("Failed to extract summary from OpenAI-compatible response for model: {model}")
            .into(),
    )
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_request_body_structure() {
        // 验证请求 body 结构符合 OpenAI chat/completions 格式
        let html_content = r#"<html><body><h1>测试文章</h1><p>内容。</p></body></html>"#;

        let body = json!({
            "model": "test-model",
            "messages": [
                { "role": "system", "content": SUMMARY_SYSTEM_PROMPT },
                { "role": "user", "content": html_content }
            ],
            "temperature": 0.3,
            "max_tokens": SUMMARY_MAX_OUTPUT_TOKENS
        });

        assert_eq!(body["model"], "test-model");
        let messages = body["messages"].as_array().unwrap();
        assert_eq!(messages.len(), 2);
        assert_eq!(messages[0]["role"], "system");
        assert_eq!(messages[1]["role"], "user");
        assert_eq!(messages[1]["content"], html_content);
        assert_eq!(body["temperature"], 0.3);
        assert_eq!(body["max_tokens"], SUMMARY_MAX_OUTPUT_TOKENS);
    }

    #[test]
    fn test_endpoint_url_join() {
        // 验证端点拼接对 base_url 末尾斜杠的容错
        assert_eq!(
            format!(
                "{}/chat/completions",
                "https://api.siliconflow.cn/v1".trim_end_matches('/')
            ),
            "https://api.siliconflow.cn/v1/chat/completions"
        );
        assert_eq!(
            format!(
                "{}/chat/completions",
                "https://api.siliconflow.cn/v1/".trim_end_matches('/')
            ),
            "https://api.siliconflow.cn/v1/chat/completions"
        );
    }

    #[test]
    fn test_response_parsing() {
        let mock_response = r#"{
            "id": "chatcmpl-test",
            "choices": [
                {
                    "message": {
                        "role": "assistant",
                        "content": "这是一篇测试文章的摘要。"
                    },
                    "finish_reason": "stop"
                }
            ],
            "usage": {
                "prompt_tokens": 100,
                "completion_tokens": 50,
                "total_tokens": 150
            }
        }"#;

        let response_json: serde_json::Value = serde_json::from_str(mock_response).unwrap();

        if let Some(choices) = response_json["choices"].as_array()
            && let Some(first_choice) = choices.first()
            && let Some(message) = first_choice["message"].as_object()
            && let Some(content) = message["content"].as_str()
        {
            assert_eq!(content.trim(), "这是一篇测试文章的摘要。");
        } else {
            panic!("响应解析失败");
        }
    }
}
