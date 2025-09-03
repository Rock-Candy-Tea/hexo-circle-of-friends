use reqwest_middleware::ClientWithMiddleware;
use serde_json::json;
use tracing::info;

/// BigModel API集成
/// 基于文档: https://docs.bigmodel.cn/api-reference/%E6%A8%A1%E5%9E%8B-api/%E5%AF%B9%E8%AF%9D%E8%A1%A5%E5%85%A8
pub async fn generate_content(
    client: &ClientWithMiddleware,
    model: &str,
    html: &str,
) -> Result<String, Box<dyn std::error::Error>> {
    let api_key = tools::get_env_var("BIGMODEL_API_KEY")?;

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
        "do_sample":false,
        "max_tokens": 16384
    });

    let response = client
        .post("https://open.bigmodel.cn/api/paas/v4/chat/completions")
        .header("Authorization", format!("Bearer {api_key}"))
        .header("Content-Type", "application/json")
        .body(body.to_string())
        .send()
        .await?;

    let response_text = response.text().await?;
    info!("BigModel {} API response: {}", model, response_text);

    // Parse the response to extract the summary
    let response_json: serde_json::Value = serde_json::from_str(&response_text)?;

    if let Some(choices) = response_json["choices"].as_array()
        && let Some(first_choice) = choices.first()
        && let Some(message) = first_choice["message"].as_object()
        && let Some(content) = message["content"].as_str()
    {
        return Ok(content.trim().to_string());
    }

    Err(format!("Failed to extract summary from BigModel response for model: {model}").into())
}
