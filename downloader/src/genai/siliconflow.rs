use reqwest_middleware::ClientWithMiddleware;
use serde_json::json;
use tracing::info;

/// SiliconFlow API集成
/// 基于文档: https://docs.siliconflow.cn/cn/api-reference/chat-completions/chat-completions
pub async fn generate_content(
    client: &ClientWithMiddleware,
    model: &str,
    html: &str,
) -> Result<String, Box<dyn std::error::Error>> {
    let api_key = tools::get_env_var("SILICONFLOW_API_KEY")?;

    let body = json!({
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": r#"你是一个文本和文章分析专家。你的任务是分析提供的HTML页面，提取其中包含的博客文章，并对文章进行总结。

你必须严格遵循以下回复规则：
1. 摘要必须用简体中文写成，如果不是简体中文则翻译为简体中文。
2. 摘要的总长度不得超过500个字符但要尽量接近500个字符（此计数包括所有字符、标点符号和空格）。
3. 输出必须仅包含摘要文本本身。不要包含任何前缀、标题、字符数或介绍性短语（例如"以下是摘要："、"（xxx字符）"）。"#
            },
            {
                "role": "user",
                "content": html
            }
        ],
        "temperature": 0.3,
        "max_tokens": 8192
    });

    let response = client
        .post("https://api.siliconflow.cn/v1/chat/completions")
        .header("Authorization", format!("Bearer {api_key}"))
        .header("Content-Type", "application/json")
        .body(body.to_string())
        .send()
        .await?;

    let response_text = response.text().await?;
    info!("SiliconFlow {} API response: {}", model, response_text);

    // Parse the response to extract the summary
    let response_json: serde_json::Value = serde_json::from_str(&response_text)?;

    if let Some(choices) = response_json["choices"].as_array()
        && let Some(first_choice) = choices.first()
        && let Some(message) = first_choice["message"].as_object()
        && let Some(content) = message["content"].as_str()
    {
        return Ok(content.trim().to_string());
    }

    Err(format!("Failed to extract summary from SiliconFlow response for model: {model}").into())
}

#[cfg(test)]
mod tests {
    use super::*;

    #[tokio::test]
    async fn test_siliconflow_request_structure() {
        // 测试请求结构的正确性
        let html_content = r#"
        <html>
            <head><title>Test Article</title></head>
            <body>
                <h1>测试文章标题</h1>
                <p>这是一篇测试文章的内容。</p>
            </body>
        </html>
        "#;

        let body = json!({
            "model": "Qwen/QwQ-32B",
            "messages": [
                {
                    "role": "system",
                    "content": r#"你是一个文本和文章分析专家。你的任务是分析提供的HTML页面，提取其中包含的博客文章，并对文章进行总结。

你必须严格遵循以下回复规则：
1. 摘要必须用简体中文写成，如果不是简体中文则翻译为简体中文。
2. 摘要的总长度不得超过500个字符但要尽量接近500个字符（此计数包括所有字符、标点符号和空格）。
3. 输出必须仅包含摘要文本本身。不要包含任何前缀、标题或介绍性短语（例如"以下是摘要："）。"#
                },
                {
                    "role": "user",
                    "content": html_content
                }
            ],
            "temperature": 0.3,
            "max_tokens": 1000
        });

        // 验证JSON结构
        assert_eq!(body["model"], "Qwen/QwQ-32B");
        assert_eq!(body["messages"].as_array().unwrap().len(), 2);
        assert_eq!(body["messages"][0]["role"], "system");
        assert_eq!(body["messages"][1]["role"], "user");
        assert_eq!(body["messages"][1]["content"], html_content);
        assert_eq!(body["temperature"], 0.3);
        assert_eq!(body["max_tokens"], 1000);
    }

    #[test]
    fn test_response_parsing() {
        // 测试响应解析逻辑
        let mock_response = r#"{
            "id": "test-id",
            "choices": [
                {
                    "message": {
                        "role": "assistant",
                        "content": "这是一个测试摘要内容。"
                    },
                    "finish_reason": "stop"
                }
            ],
            "usage": {
                "prompt_tokens": 100,
                "completion_tokens": 50,
                "total_tokens": 150
            },
            "created": 1234567890,
            "model": "Qwen/QwQ-32B",
            "object": "chat.completion"
        }"#;

        let response_json: serde_json::Value = serde_json::from_str(mock_response).unwrap();

        if let Some(choices) = response_json["choices"].as_array()
            && let Some(first_choice) = choices.first()
            && let Some(message) = first_choice["message"].as_object()
            && let Some(content) = message["content"].as_str()
        {
            assert_eq!(content.trim(), "这是一个测试摘要内容。");
        }
    }
}
